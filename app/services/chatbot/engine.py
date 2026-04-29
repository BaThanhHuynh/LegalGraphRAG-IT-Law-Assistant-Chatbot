import json
import uuid
import os
from datetime import datetime
import google.generativeai as genai

from app.core.config import Config
from app.core.logger import logger
from app.services.rag.retriever import get_context_from_results
from app.services.graphrag.knowledge_graph import hybrid_search
from app.services.chatbot.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE, TITLE_PROMPT

# Configure Gemini
_model = None

def get_llm():
    """Get or initialize Gemini model."""
    global _model
    if _model is None:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        _model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
        logger.info("[LLM] Gemini model initialized.")
    return _model


def _load_history():
    if not os.path.exists(Config.CHAT_HISTORY_PATH):
        return {"conversations": {}, "messages": []}
    with open(Config.CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"conversations": {}, "messages": []}

def _save_history(data):
    os.makedirs(os.path.dirname(Config.CHAT_HISTORY_PATH), exist_ok=True)
    with open(Config.CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_response(query: str, conversation_id: str = None) -> dict:
    """
    Main chatbot pipeline:
    1. Hybrid retrieval (vector + graph)
    2. Build prompt with context
    3. Call Gemini API
    4. Save to conversation history
    5. Return response with sources
    """
    # 1. Create conversation if needed
    if not conversation_id:
        conversation_id = create_conversation(query)

    # 2. Save user message
    save_message(conversation_id, "user", query)

    # 3. Hybrid search (vector + knowledge graph)
    try:
        search_results = hybrid_search(query, top_k=5)
        rag_context = get_context_from_results(search_results["vector_results"])
        graph_context = search_results.get("graph_context", "Không có thông tin từ Knowledge Graph.")
        graph_data = search_results.get("graph_data", {"nodes": [], "edges": []})
    except Exception as e:
        logger.error(f"[Error] Search failed: {e}")
        rag_context = "Không thể truy xuất dữ liệu."
        graph_context = ""
        graph_data = {"nodes": [], "edges": []}
        search_results = {"vector_results": []}

    # 4. Build prompt
    prompt = RAG_PROMPT_TEMPLATE.format(
        rag_context=rag_context,
        graph_context=graph_context,
        query=query,
    )

    # 5. Get conversation history for context
    history = get_conversation_history(conversation_id, limit=6)
    chat_history = []
    for msg in history[:-1]:  # Exclude the current user message
        chat_history.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [msg["content"]],
        })

    # 6. Generate Response using Gemini API
    try:
        # Check for MOCK mode
        if query.strip().lower().startswith("/mock"):
            logger.info("MOCK mode activated. Bypassing Gemini API.")
            answer = "Dữ liệu tìm thấy từ CSDL (Mock Mode):\n\n" + rag_context
        else:
            model = get_llm()
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(
                f"{SYSTEM_PROMPT}\n\n{prompt}",
            )
            answer = response.text
    except Exception as e:
        logger.error(f"[Error] LLM generation failed: {e}")
        answer = f"Lỗi API key Gemini"

    # 7. Build sources list
    sources = []
    for r in search_results.get("vector_results", [])[:3]:
        sources.append({
            "article": r.get("article", ""),
            "content": r.get("content", "")[:200],
            "score": round(r.get("score", 0), 3),
            "doc_title": r.get("doc_title", ""),
        })

    # 8. Save assistant message
    save_message(conversation_id, "assistant", answer, sources)

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": sources,
        "graph_data": graph_data,
    }


def create_conversation(first_query: str = "") -> str:
    """Create a new conversation and return its ID."""
    conv_id = str(uuid.uuid4())
    title = "Cuộc hội thoại mới"

    # Try to generate a smart title
    if first_query:
        try:
            model = get_llm()
            title_prompt = TITLE_PROMPT.format(query=first_query)
            response = model.generate_content(title_prompt)
            title = response.text.strip()[:100]
        except Exception:
            title = first_query[:50] + "..." if len(first_query) > 50 else first_query

    data = _load_history()
    now = datetime.now().isoformat()
    data["conversations"][conv_id] = {
        "id": conv_id,
        "title": title,
        "created_at": now,
        "updated_at": now
    }
    _save_history(data)
    return conv_id


def save_message(conversation_id: str, role: str, content: str, sources: list = None):
    """Save a message to the conversation history."""
    data = _load_history()
    now = datetime.now().isoformat()
    
    data["messages"].append({
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "sources": sources,
        "created_at": now
    })
    
    if conversation_id in data["conversations"]:
        data["conversations"][conversation_id]["updated_at"] = now
        
    _save_history(data)


def get_conversation_history(conversation_id: str, limit: int = 20) -> list:
    """Get conversation messages."""
    data = _load_history()
    msgs = [m for m in data["messages"] if m["conversation_id"] == conversation_id]
    msgs.sort(key=lambda x: x["created_at"])
    return msgs[-limit:] if limit else msgs


def get_all_conversations() -> list:
    """Get all conversations sorted by recent."""
    data = _load_history()
    convs = list(data["conversations"].values())
    convs.sort(key=lambda x: x["updated_at"], reverse=True)
    return convs
