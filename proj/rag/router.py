import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# 🔹 Load embedding model (same as retrieval)
model = SentenceTransformer("all-MiniLM-L6-v2")

# 🔹 Load FAISS index
index = faiss.read_index("faiss_index.index")


def check_rag_confidence(query):
    """
    Returns similarity score (higher = better match)
    """
    query_embedding = model.encode([query]).astype("float32")

    distances, indices = index.search(query_embedding, k=1)

    score = distances[0][0]

    return score


def route(query):
    """
    Decide whether to use RAG or Web
    """

    query_lower = query.lower()

    # 🔹 Step 1: Keyword rules (fast)
    if any(word in query_lower for word in ["latest", "news", "2024", "2025","2026", "recent"]):
        return "web"

    if any(word in query_lower for word in ["file", ".txt", ".pdf"]):
        return "file"   # for future use

    # 🔹 Step 2: FAISS similarity check
    score = check_rag_confidence(query)
    print(score)

    # ⚠️ IMPORTANT: Tune this threshold
    THRESHOLD = 0.95

    if score <= THRESHOLD:
        return "rag"
    else:
        return "web"
