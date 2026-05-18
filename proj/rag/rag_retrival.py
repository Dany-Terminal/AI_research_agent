import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
import os

# 🔹 Load environment variables
load_dotenv("../.env")
groq_api_key = os.getenv("GROQ_API_KEY")

# 🔹 Initialize Groq client
client = Groq(api_key=groq_api_key)

# 🔹 Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 🔹 Load FAISS index
#index = faiss.read_index("faiss_index.index")
BASE_DIR = os.path.dirname(__file__)

index_path = os.path.join(BASE_DIR, "faiss_index.index")
index = faiss.read_index(index_path)

# 🔹 Load metadata

chunks_path = os.path.join(BASE_DIR, "chunks.json")

with open(chunks_path, "r", encoding="utf-8") as f:
    chunks = json.load(f)


# -------------------------------
# 🔹 Core RAG Functions
# -------------------------------

def retrieve(query, k=5):
    """Search FAISS and return top-k chunks"""

    query_embedding = model.encode([query]).astype("float32")
    distances, indices = index.search(query_embedding, k)

    results = []
    for i in indices[0]:
        results.append(chunks[i])

    return results, distances[0]


def build_context(rag_chunks=None):
    """Build structured context"""

    context = ""

    if rag_chunks:
        context += "RAG Context:\n"
        context += "\n\n".join([chunk["text"] for chunk in rag_chunks])

    return context


def generate_answer(query, context):
    """Send context + query to LLM"""

    prompt = f"""
You are an intelligent research assistant.

Use the information provided below.

If answer is not present, you may continue with your answer however do specify:
"The following question is generic and will be answered as per LLM"
before giving your own answer.

---

{context}

---

Question:
{query}

Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


# -------------------------------
# ✅ MAIN TOOL FUNCTION
# -------------------------------

def rag_tool(query: str, k: int = 5, threshold: float = 0.5):
    """
    RAG Tool function to be called by router/agent

    Returns:
        dict: {
            "answer": str,
            "sources": list,
            "confidence": float,
            "fallback": bool
        }
    """

    # 🔹 Step 1: Retrieve
    retrieved, distances = retrieve(query, k=k)

    best_score = float(distances[0])

    # 🔹 Step 2: Confidence check
    fallback = best_score < threshold

    # 🔹 Step 3: Build context
    context = build_context(retrieved if not fallback else None)

    # 🔹 Step 4: Generate answer
    answer = generate_answer(query, context)

    # 🔹 Step 5: Format sources
    sources = [
        {
            "paper_id": r["paper_id"],
            "page_number": r["page_number"]
        }
        for r in retrieved
    ]

    return {
        "answer": answer,
        "sources": sources,
        "confidence": best_score,
        "fallback": fallback
    }
