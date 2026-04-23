import os
import sys
import json
from neo4j import GraphDatabase

# Thêm đường dẫn project vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.append(project_dir)

from app.core.config import Config
from app.core.logger import logger

KG_DATA_PATH = os.path.join(project_dir, "data", "kg_data.json")

def migrate_to_neo4j():
    """Đọc dữ liệu từ file JSON và ghi vào Neo4j."""
    
    if not os.path.exists(KG_DATA_PATH):
        logger.warning(f"Không tìm thấy file dữ liệu Graph tại {KG_DATA_PATH}")
        logger.info("Đang tạo file mẫu kg_data.json...")
        sample_data = {
            "entities": [
                {"entity_id": "dieu_1", "name": "Điều 1", "description": "Phạm vi điều chỉnh", "entity_type": "DIEU_LUAT"},
                {"entity_id": "luat_cntt", "name": "Luật CNTT 2006", "description": "Luật Công nghệ thông tin", "entity_type": "VAN_BAN"}
            ],
            "relationships": [
                {"source_entity_id": "dieu_1", "target_entity_id": "luat_cntt", "relationship_type": "THUOC", "description": "Thuộc văn bản", "weight": 1.0}
            ]
        }
        os.makedirs(os.path.dirname(KG_DATA_PATH), exist_ok=True)
        with open(KG_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã tạo file mẫu. Hãy cập nhật dữ liệu vào {KG_DATA_PATH} rồi chạy lại script.")
        return

    with open(KG_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    
    logger.info(f"Đã tải {len(entities)} entities và {len(relationships)} relationships từ JSON.")

    logger.info(f"Đang kết nối đến Neo4j tại {Config.NEO4J_URI}...")
    try:
        driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)
        )
    except Exception as e:
        logger.error(f"Lỗi kết nối Neo4j: {e}")
        return

    with driver.session() as session:
        # Xóa dữ liệu cũ
        logger.info("Đang xóa dữ liệu cũ trong Neo4j...")
        session.run("MATCH (n) DETACH DELETE n")
        
        # Thêm Entities (Nodes)
        logger.info("Đang tạo Nodes...")
        for entity in entities:
            label = entity["entity_type"]
            query = f"""
            MERGE (n:`{label}` {{entity_id: $entity_id}})
            SET n.name = $name,
                n.description = $description,
                n:Entity
            """
            session.run(query, {
                "entity_id": entity["entity_id"],
                "name": entity["name"],
                "description": entity.get("description", "")
            })
            
        # Thêm Relationships (Edges)
        logger.info("Đang tạo Relationships...")
        for rel in relationships:
            rel_type = rel["relationship_type"].replace(" ", "_").upper()
            query = f"""
            MATCH (source {{entity_id: $source_id}})
            MATCH (target {{entity_id: $target_id}})
            MERGE (source)-[r:`{rel_type}`]->(target)
            SET r.description = $description,
                r.weight = $weight
            """
            session.run(query, {
                "source_id": rel["source_entity_id"],
                "target_id": rel["target_entity_id"],
                "description": rel.get("description", ""),
                "weight": rel.get("weight", 1.0)
            })

        logger.info("Đang tạo indexes...")
        try:
            session.run("CREATE TEXT INDEX entity_name_idx IF NOT EXISTS FOR (n:Entity) ON (n.name)")
        except Exception as e:
            logger.warning(f"Lưu ý khi tạo index: {e}")

    driver.close()
    logger.info("Đồng bộ Neo4j hoàn tất thành công!")

if __name__ == "__main__":
    migrate_to_neo4j()
