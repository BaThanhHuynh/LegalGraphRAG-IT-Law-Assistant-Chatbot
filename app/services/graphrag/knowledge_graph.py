"""
Knowledge Graph engine for hybrid search (vector + graph traversal).
Uses LangChain Neo4jGraph and Cypher queries.
"""
from app.core.config import Config
from app.services.rag.retriever import vector_search
from langchain_neo4j import Neo4jGraph
from neo4j import GraphDatabase

class KnowledgeGraph:
    """Knowledge graph loaded from Neo4j."""

    def __init__(self):
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            self._graph = Neo4jGraph(
                url=Config.NEO4J_URI,
                username=Config.NEO4J_USERNAME,
                password=Config.NEO4J_PASSWORD,
                enhanced_schema=False,
                refresh_schema=False
            )
        return self._graph

    def search_entities(self, query: str, top_k: int = 5) -> list:
        """Search entities by name/description using full-text index or CONTAINS."""
        # Split query into words to match
        words = [w.lower() for w in query.split() if len(w) >= 2]
        if not words:
            return []

        # A basic keyword match Cypher query
        cypher = """
        MATCH (n:Entity)
        WHERE any(word in $words WHERE toLower(n.name) CONTAINS word OR toLower(n.description) CONTAINS word)
        RETURN n.entity_id AS entity_id, n.name AS name, n.description AS description, labels(n) AS labels
        LIMIT $top_k
        """
        
        results = self.graph.query(cypher, params={"words": words, "top_k": top_k})
        
        scored = []
        for r in results:
            labels = [l for l in r.get("labels", []) if l != "Entity"]
            entity_type = labels[0] if labels else "UNKNOWN"
            
            # Recompute a basic score for ranking
            score = 0
            name_lower = r.get("name", "").lower()
            desc_lower = r.get("description", "").lower()
            for w in words:
                if w in name_lower: score += 3
                if w in desc_lower: score += 1
                
            scored.append({
                "entity": {
                    "entity_id": r["entity_id"],
                    "name": r["name"],
                    "description": r["description"],
                    "entity_type": entity_type
                },
                "score": score
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def get_graph_context(self, entity_ids: list, depth: int = 1) -> str:
        """
        Build context string from graph traversal starting from given entities.
        """
        if not entity_ids:
            return ""

        # Query up to 2 hops from the starting entities
        # Note: Cypher paths length can be dynamic but for simple RAG, depth 1-2 is enough.
        cypher = f"""
        MATCH (start:Entity)-[r*1..{depth}]-(target:Entity)
        WHERE start.entity_id IN $entity_ids
        RETURN start.name AS start_name, 
               [l IN labels(start) WHERE l <> 'Entity'][0] AS start_type,
               start.description AS start_desc,
               target.name AS target_name, 
               [l IN labels(target) WHERE l <> 'Entity'][0] AS target_type,
               type(r[-1]) AS rel_type
        LIMIT 50
        """
        
        results = self.graph.query(cypher, params={"entity_ids": entity_ids})
        
        if not results:
            # Maybe just fetch the nodes themselves if no relationships
            cypher_nodes = """
            MATCH (n:Entity) WHERE n.entity_id IN $entity_ids
            RETURN n.name AS name, [l IN labels(n) WHERE l <> 'Entity'][0] AS type, n.description AS desc
            """
            nodes = self.graph.query(cypher_nodes, params={"entity_ids": entity_ids})
            context = ""
            for n in nodes:
                context += f"[Entity: {n.get('name')}] (Loại: {n.get('type')})\n  {n.get('desc', '')[:200]}\n"
            return context

        context_parts = []
        seen_starts = set()
        seen_edges = set()

        for r in results:
            start_name = r["start_name"]
            if start_name not in seen_starts:
                seen_starts.add(start_name)
                context_parts.append(
                    f"[Entity: {start_name}] (Loại: {r['start_type']})\n"
                    f"  {r.get('start_desc', '')[:200]}"
                )
            
            edge_key = f"{start_name}-{r['rel_type']}-{r['target_name']}"
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                context_parts.append(
                    f"  → [{r['rel_type']}] {r['target_name']} (Loại: {r['target_type']})"
                )

        return "\n".join(context_parts)

    def get_graph_data_for_visualization(self, entity_ids: list = None, depth: int = 1) -> dict:
        """
        Get graph data (nodes + edges) for frontend visualization.
        """
        nodes_dict = {}
        edges_list = []

        if not entity_ids:
            # Default visualization: Fetch a subset of the graph
            cypher = """
            MATCH (n)-[r]->(m)
            WHERE ('VAN_BAN' IN labels(n) OR 'DIEU_LUAT' IN labels(n) OR 'CHUONG' IN labels(n))
            RETURN n.entity_id AS source_id, n.name AS source_name, [l IN labels(n) WHERE l <> 'Entity'][0] AS source_type,
                   m.entity_id AS target_id, m.name AS target_name, [l IN labels(m) WHERE l <> 'Entity'][0] AS target_type,
                   type(r) AS rel_type, r.description AS rel_desc
            LIMIT 50
            """
            results = self.graph.query(cypher)
        else:
            cypher = f"""
            MATCH (n)-[r*1..{depth}]-(m)
            WHERE n.entity_id IN $entity_ids
            WITH n, r[-1] as last_rel, m
            RETURN n.entity_id AS source_id, n.name AS source_name, [l IN labels(n) WHERE l <> 'Entity'][0] AS source_type,
                   m.entity_id AS target_id, m.name AS target_name, [l IN labels(m) WHERE l <> 'Entity'][0] AS target_type,
                   type(last_rel) AS rel_type, last_rel.description AS rel_desc
            LIMIT 100
            """
            results = self.graph.query(cypher, params={"entity_ids": entity_ids})

        for r in results:
            sid = r["source_id"]
            if sid not in nodes_dict:
                nodes_dict[sid] = {"id": sid, "label": r.get("source_name", "")[:50], "type": r.get("source_type")}
                
            tid = r["target_id"]
            if tid not in nodes_dict:
                nodes_dict[tid] = {"id": tid, "label": r.get("target_name", "")[:50], "type": r.get("target_type")}
                
            edges_list.append({
                "source": sid,
                "target": tid,
                "type": r["rel_type"],
                "label": r.get("rel_desc", "")[:30]
            })

        return {"nodes": list(nodes_dict.values()), "edges": edges_list}

# Singleton instance
_kg_instance = None

def get_knowledge_graph() -> KnowledgeGraph:
    """Get singleton KnowledgeGraph instance."""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraph()
    return _kg_instance


def hybrid_search(query: str, top_k: int = 5) -> dict:
    """
    Hybrid search: combine vector search + knowledge graph traversal.
    Returns both RAG chunks and graph context.
    """
    # 1. Vector search for relevant chunks
    vector_results = vector_search(query, top_k=top_k)

    # 2. Knowledge graph search for related entities
    kg = get_knowledge_graph()
    try:
        kg_results = kg.search_entities(query, top_k=3)
    except Exception as e:
        print(f"[KG Error] Failed to search entities: {e}")
        kg_results = []

    # 3. Expand graph context from matched entities
    matched_entity_ids = [r["entity"]["entity_id"] for r in kg_results]

    # Also find entities linked to vector search results
    for vr in vector_results[:3]:
        article = vr.get("article", "")
        if article:
            import re
            art_match = re.search(r'(\d+)', article)
            if art_match:
                article_entity_id = f"dieu_{art_match.group(1)}"
                if article_entity_id not in matched_entity_ids:
                    matched_entity_ids.append(article_entity_id)

    try:
        if matched_entity_ids:
            graph_context = kg.get_graph_context(matched_entity_ids, depth=2)
            graph_data = kg.get_graph_data_for_visualization(matched_entity_ids, depth=1)
        else:
            graph_context = ""
            graph_data = {"nodes": [], "edges": []}
    except Exception as e:
        print(f"[KG Error] Failed to get graph context: {e}")
        graph_context = ""
        graph_data = {"nodes": [], "edges": []}

    return {
        "vector_results": vector_results,
        "graph_context": graph_context,
        "graph_data": graph_data,
        "matched_entities": kg_results,
    }
