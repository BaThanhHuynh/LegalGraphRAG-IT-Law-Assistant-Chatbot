"""
Seed data script: Load law data from law_crawler's law_chunks.jsonl,
generate embeddings, and upload to Qdrant vector database.

Run: python database/seed_data.py
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import Config
from app.services.rag.embeddings import get_embeddings_batch
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Path to law_chunks.jsonl
JSONL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "law_crawler", "data", "law_chunks.jsonl"
)

def load_jsonl(path: str) -> list:
    """Load law_chunks.jsonl into list of dicts."""
    print(f"[Load] Reading {path}...")
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    print(f"[Load] Loaded {len(chunks):,} chunks")
    return chunks

def seed_qdrant():
    """Main seeding function for Qdrant."""
    if not os.path.exists(JSONL_PATH):
        print(f"[ERROR] File not found: {JSONL_PATH}")
        print("  Please ensure law_crawler/data/law_chunks.jsonl exists.")
        sys.exit(1)

    # Load chunks from JSONL
    chunks = load_jsonl(JSONL_PATH)

    # Filter out repealed chunks
    active_chunks = [c for c in chunks if not c.get("payload", {}).get("is_repealed", False)]
    print(f"[Filter] {len(active_chunks):,} active chunks (excluded {len(chunks) - len(active_chunks)} repealed)")

    # Ensure DB directory exists
    os.makedirs(os.path.dirname(Config.QDRANT_PATH), exist_ok=True)

    # Connect to local Qdrant
    client = QdrantClient(path=Config.QDRANT_PATH)

    print(f"[Qdrant] Recreating collection '{Config.QDRANT_COLLECTION}'...")
    client.recreate_collection(
        collection_name=Config.QDRANT_COLLECTION,
        vectors_config=models.VectorParams(
            size=Config.EMBEDDING_DIM,
            distance=models.Distance.COSINE
        )
    )

    BATCH_SIZE = 256
    total_batches = (len(active_chunks) + BATCH_SIZE - 1) // BATCH_SIZE

    print("[Qdrant] Generating embeddings and uploading points...")
    for batch_idx in range(total_batches):
        start = batch_idx * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(active_chunks))
        batch_chunks = active_chunks[start:end]

        # Extract text for embeddings
        texts = [c.get("text", "") for c in batch_chunks]
        embeddings = get_embeddings_batch(texts)

        points = []
        for i, chunk in enumerate(batch_chunks):
            payload = chunk.get("payload", {})
            # Flatten metadata for payload
            point_payload = {
                "chunk_id": chunk.get("id", ""),
                "content": payload.get("noi_dung_chunk", ""),
                "context_text": chunk.get("text", ""),
                "chuong_so": payload.get("chuong_so", ""),
                "chuong_ten": payload.get("chuong_ten", ""),
                "muc_so": payload.get("muc_so", ""),
                "muc_ten": payload.get("muc_ten", ""),
                "dieu_so": payload.get("dieu_so", ""),
                "dieu_ten": payload.get("dieu_ten", ""),
                "is_repealed": payload.get("is_repealed", False),
                "is_truncated": payload.get("is_truncated", False),
                "ten_van_ban": payload.get("ten_van_ban", ""),
                "so_hieu": payload.get("so_hieu", ""),
                "loai_van_ban": payload.get("loai_van_ban", ""),
                "trang_thai": payload.get("trang_thai", ""),
                "nhom": payload.get("nhom", "")
            }

            points.append(
                models.PointStruct(
                    id=start + i + 1,  # Qdrant integer ID
                    vector=embeddings[i].tolist(),
                    payload=point_payload
                )
            )

        # Upload batch
        client.upload_points(
            collection_name=Config.QDRANT_COLLECTION,
            points=points
        )
        print(f"  ... batch {batch_idx + 1}/{total_batches} uploaded ({end:,}/{len(active_chunks):,})")

    print(f"\n{'='*60}")
    print(f"  ✅ Seed data to Qdrant completed!")
    print(f"  🔢 Total chunks uploaded: {len(active_chunks):,}")
    print(f"  📂 Qdrant storage path:   {Config.QDRANT_PATH}")
    print(f"{'='*60}")

if __name__ == "__main__":
    seed_qdrant()
