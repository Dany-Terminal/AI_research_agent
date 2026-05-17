import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from rag.ingest import ingest_pdf

# Load stored chunks
CHUNKS_PATH = "../rag/chunks.json"
INDEX_PATH = "../rag/faiss_index.index"

model = SentenceTransformer("all-MiniLM-L6-v2")


# =========================================================
# 📦 Load data
# =========================================================

def load_chunks():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_index():
    return faiss.read_index(INDEX_PATH)


# =========================================================
# 🔍 Retrieve ONLY from one PDF
# =========================================================

def retrieve_pdf_chunks(query, pdf_name, top_k=5):
    chunks = load_chunks()
    index = load_index()

    query_embedding = model.encode([query]).astype("float32")

    _, indices = index.search(query_embedding, top_k * 5)

    results = []

    for i in indices[0]:
        if i >= len(chunks):
            continue

        chunk = chunks[i]

        # 🔥 IMPORTANT FILTER
        if chunk["paper_id"] == pdf_name:
            results.append(chunk["text"])

        if len(results) >= top_k:
            break

    return "\n\n".join(results)


# =========================================================
# 🧠 MAIN TOOL
# =========================================================

def pdf_tool(pdf_path, query, llm_client):
    pdf_name = os.path.basename(pdf_path)

    # 1. INGEST FIRST (incremental safe)
    ingest_pdf(pdf_path)

    # 2. RETRIEVE ONLY THIS PDF
    context = retrieve_pdf_chunks(query, pdf_name)

    if not context.strip():
        return "No relevant content found in this PDF."

    # 3. LLM PROMPT (IMPORTANT PART)
    prompt = f"""
You are a strict research assistant.

You must answer ONLY using the provided PDF context.

If answer is not in context, say: "Not found in document."

---

PDF CONTEXT:
{context}

---

QUESTION:
{query}

---

Answer clearly and accurately:
"""

    response = llm_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
