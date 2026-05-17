import os
import requests
from dotenv import load_dotenv
import json
from groq import Groq

# ---------------------------
# 🔑 LOAD ENV
# ---------------------------
load_dotenv("../.env")

LANGSEARCH_API_KEY = os.getenv("LANGSEARCH_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------------------------
# 🔗 INIT GROQ
# ---------------------------
client = Groq(api_key=GROQ_API_KEY)

URL = "https://api.langsearch.com/v1/web-search"


# ---------------------------
# 🌐 SEARCH FUNCTION
# ---------------------------
def fetch_search_data(query):
    headers = {
        "Authorization": f"Bearer {LANGSEARCH_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "limit": 10  # fetch more → filter later
    }

    try:
        res = requests.post(URL, json=payload, headers=headers)

        if res.status_code != 200:
            print("❌ Search API Error:", res.text)
            return None

        return res.json()

    except Exception as e:
        print("❌ Request failed:", str(e))
        return None


# ---------------------------
# ✂️ CLEAN + EXTRACT RESULTS
# ---------------------------
def extract_top_results(search_data, top_k=5, max_chars=300):
    results = []

    try:
        web_pages = search_data.get("data", {}).get("webPages", {}).get("value", [])

        for item in web_pages[:top_k]:
            title = item.get("name", "").strip()
            snippet = item.get("snippet", "").strip()
            url = item.get("url", "").strip()

            # Basic cleaning
            snippet = snippet.replace("\n", " ").replace("\r", " ")

            # Trim long snippets
            snippet = snippet[:max_chars]

            # Skip garbage
            if not title or not snippet:
                continue

            results.append({
                "title": title,
                "snippet": snippet,
                "url": url
            })

    except Exception as e:
        print("⚠️ Extraction error:", str(e))

    return results


# ---------------------------
# 🧠 LLM PROCESSOR
# ---------------------------
def ask_llm(query, clean_results):
    if not clean_results:
        return "❌ No useful search results found."

    prompt = f"""
You are a precise and intelligent assistant.

User Question:
{query}

Top Search Results:
{json.dumps(clean_results, indent=2)}

Instructions:
- Use ONLY the provided results
- Ignore noise or incomplete data
- Combine multiple sources into one answer
- Keep answer concise but informative
- If factual (like versions), be very clear and structured
- If unsure, say "information is limited"

Final Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


# ---------------------------
# 🧪 MAIN PIPELINE
# ---------------------------
def run(query):
    print("🔍 Query:", query)

    # Step 1: Fetch
    search_data = fetch_search_data(query)
    if not search_data:
        return

    # Step 2: Extract + Clean
    clean_results = extract_top_results(search_data)

    print("\n📦 CLEANED RESULTS:\n")
    print(json.dumps(clean_results, indent=2))

    # Step 3: LLM
    print("\n🧠 Generating final answer...\n")
    final_answer = ask_llm(query, clean_results)

    print("✅ FINAL ANSWER:\n")
    print(final_answer)


# ---------------------------
# ▶️ RUN
# ---------------------------
if __name__ == "__main__":
    q = input("Enter your query: ")
    run(q)
