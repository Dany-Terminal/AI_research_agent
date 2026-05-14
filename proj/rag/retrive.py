import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
import os

# 🔹 Import router
from router import route, check_rag_confidence

# 🔹 Load environment variables
load_dotenv("../.env")
groq_api_key = os.getenv("GROQ_API_KEY")

# 🔹 Initialize Groq client
client = Groq(api_key=groq_api_key)

# 🔹 Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 🔹 Load FAISS index
index = faiss.read_index("faiss_index.index")

# 🔹 Load metadata
with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)


def retrieve(query, k=5):
    """Search FAISS and return top-k chunks"""

    query_embedding = model.encode([query]).astype("float32")

    distances, indices = index.search(query_embedding, k)

    results = []

    for i in indices[0]:
        results.append(chunks[i])

    return results, distances[0]


def generate_answer(query, context):
    """Send context + query to LLM"""

    prompt = f"""
You are an intelligent research assistant.

Use the information provided below.

If answer is not present, u may continue with your answer how ever do specify "The following question is generic and will be answerd as per LLM". This statement must be written before You give your own answer.

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


def build_context(rag_chunks=None):
    """Build structured context"""

    context = ""

    if rag_chunks:
        context += "RAG Context:\n"
        context += "\n\n".join([chunk["text"] for chunk in rag_chunks])

    return context


# 🔽 RUN LOOP
if __name__ == "__main__":

    while True:
        query = input("\n🔍 Ask something (or type 'exit'): ")

        if query.lower() == "exit":
            break

        # 🔹 Step 1: Route decision
        decision = route(query)
        print(f"\n🧠 Router Decision: {decision}")

        # 🔹 Step 2: Execute based on decision

        if decision == "rag":

            retrieved, distances = retrieve(query, k=5)

            print("\n📄 Retrieved chunks:")
            for r in retrieved:
                print(f"- {r['paper_id']} | Page {r['page_number']}")

            # 🔥 Step 3: Fallback check (IMPORTANT)
            best_score = distances[0]

            if best_score < 0.5:
                print("\n⚠️ Low confidence in RAG → (would switch to web in future)")

            context = build_context(retrieved)

        elif decision == "web":
            print("\n🌐 Web search not implemented yet.")
            context = "No data available."

        elif decision == "file":
            print("\n📂 File tool not implemented yet.")
            context = "No data available."

        else:
            context = "No data available."

        # 🔹 Step 4: Generate Answer
        answer = generate_answer(query, context)

        print("\n🤖 Answer:\n")
        print(answer)
