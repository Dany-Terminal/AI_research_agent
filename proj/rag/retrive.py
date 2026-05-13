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

# 🔹 Load embedding model (same as before)
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
    
    return results


def generate_answer(query, retrieved_chunks):
    """Send context + query to LLM"""
    
    context = "\n\n".join([chunk["text"] for chunk in retrieved_chunks])
    
    prompt = f"""
You are a research assistant.

You MUST answer ONLY using the provided context.

If the answer is not in the context:
say: "Not found in provided documents."

Do NOT use external knowledge.

Context:
{context}

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


# 🔽 RUN LOOP
if __name__ == "__main__":
    
    while True:
        query = input("\n🔍 Ask something (or type 'exit'): ")
        
        if query.lower() == "exit":
            break
        
        retrieved = retrieve(query, k=5)
        
        print("\n📄 Retrieved chunks:")
        for r in retrieved:
            print(f"- {r['paper_id']} | Page {r['page_number']}")
        
        answer = generate_answer(query, retrieved)
        
        print("\n🤖 Answer:\n")
        print(answer)
