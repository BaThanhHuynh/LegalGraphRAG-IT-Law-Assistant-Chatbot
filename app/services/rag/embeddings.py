import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import Config

_model = None


def get_model():
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        print(f"[Embeddings] Loading model: {Config.EMBEDDING_MODEL}...")
        _model = SentenceTransformer(Config.EMBEDDING_MODEL)
        print("[Embeddings] Model loaded successfully.")
    return _model


def get_embedding(text: str) -> np.ndarray:
    """Generate embedding vector for a text string."""
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return np.array(embedding, dtype=np.float32)


def get_embeddings_batch(texts: list) -> list:
    """Generate embeddings for a batch of texts."""
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    return [np.array(e, dtype=np.float32) for e in embeddings]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def serialize_embedding(embedding: np.ndarray) -> bytes:
    """Serialize numpy array to bytes for MySQL BLOB storage."""
    return embedding.tobytes()


def deserialize_embedding(blob: bytes) -> np.ndarray:
    """Deserialize bytes from MySQL BLOB to numpy array."""
    return np.frombuffer(blob, dtype=np.float32)
