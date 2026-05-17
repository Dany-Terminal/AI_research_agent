import os
import json
import faiss
import numpy as np
import pdfplumber
import re
import tiktoken
from sentence_transformers import SentenceTransformer


# =========================================================
# CONFIG
# =========================================================

OUTPUT_DIR = "../rag"
CHUNKS_FILE = "chunks.json"
INDEX_FILE = "faiss_index.index"
META_FILE = "indexed_files.json"

tokenizer = tiktoken.get_encoding("cl100k_base")
model = SentenceTransformer("all-MiniLM-L6-v2")


# =========================================================
# 📄 PDF TEXT EXTRACTION
# =========================================================

def extract_text_from_pdf(pdf_path):
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n{page_text}\n"

    return text


# =========================================================
# ✂️ CHUNKING
# =========================================================

def count_tokens(text):
    return len(tokenizer.encode(text))


def split_text(text, chunk_size=500, overlap=100):
    paragraphs = text.split("\n\n")

    chunks = []
    current = ""

    for para in paragraphs:
        if count_tokens(current + para) <= chunk_size:
            current += para + "\n\n"
        else:
            if current:
                chunks.append(current.strip())

            sentences = re.split(r'(?<=[.!?]) +', para)
            temp = ""

            for s in sentences:
                if count_tokens(temp + s) <= chunk_size:
                    temp += s + " "
                else:
                    if temp:
                        chunks.append(temp.strip())
                    temp = s + " "

            if temp:
                chunks.append(temp.strip())

            current = ""

    if current:
        chunks.append(current.strip())

    # overlap
    final_chunks = []
    for i, ch in enumerate(chunks):
        if i > 0:
            ch = chunks[i - 1][-overlap:] + ch
        final_chunks.append(ch)

    return final_chunks


# =========================================================
# 🧠 EMBEDDING
# =========================================================

def embed_texts(texts):
    embeddings = model.encode(texts, show_progress_bar=True)
    return np.array(embeddings).astype("float32")


# =========================================================
# 🗂️ LOAD / SAVE HELPERS
# =========================================================

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_faiss_index(dim):
    index_path = os.path.join(OUTPUT_DIR, INDEX_FILE)

    if os.path.exists(index_path):
        return faiss.read_index(index_path)

    return faiss.IndexFlatL2(dim)


# =========================================================
# 🚀 CORE FUNCTION: INGEST SINGLE PDF
# =========================================================

def ingest_pdf(pdf_path):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    indexed_files_path = os.path.join(OUTPUT_DIR, META_FILE)
    chunks_path = os.path.join(OUTPUT_DIR, CHUNKS_FILE)
    index_path = os.path.join(OUTPUT_DIR, INDEX_FILE)

    indexed_files = load_json(indexed_files_path, [])

    file_name = os.path.basename(pdf_path)

    # 🚨 Skip if already indexed
    if file_name in indexed_files:
        print(f"⚠️ Already indexed: {file_name}")
        return None

    print(f"\n📄 Ingesting: {file_name}")

    # 1. extract
    text = extract_text_from_pdf(pdf_path)

    # 2. chunk
    chunks_text = split_text(text)

    chunks = [
        {
            "paper_id": file_name,
            "chunk_id": i,
            "text": c
        }
        for i, c in enumerate(chunks_text)
    ]

    # 3. load existing chunks
    all_chunks = load_json(chunks_path, [])
    all_chunks.extend(chunks)

    # 4. embeddings
    embeddings = embed_texts([c["text"] for c in chunks])

    # 5. FAISS index
    dim = embeddings.shape[1]
    index = load_faiss_index(dim)

    index.add(embeddings)

    # 6. save everything
    save_json(chunks_path, all_chunks)
    faiss.write_index(index, index_path)

    indexed_files.append(file_name)
    save_json(indexed_files_path, indexed_files)

    print(f"✅ Indexed: {file_name}")

    return {
        "file": file_name,
        "chunks": len(chunks)
    }


# =========================================================
# 🧪 OPTIONAL BATCH MODE
# =========================================================

def ingest_folder(folder_path):
    results = []

    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            result = ingest_pdf(os.path.join(folder_path, file))
            if result:
                results.append(result)

    return results


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":
    folder = "./"
    print(ingest_folder(folder))
