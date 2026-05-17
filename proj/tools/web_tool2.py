import os
import requests
import xml.etree.ElementTree as ET
import json
from dotenv import load_dotenv
from groq import Groq

# ---------------------------
# 🔑 ENV
# ---------------------------
load_dotenv("../.env")

LANGSEARCH_API_KEY = os.getenv("LANGSEARCH_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

LANGSEARCH_URL = "https://api.langsearch.com/v1/web-search"


# =========================================================
# 🌐 1. LANGSEARCH WEB SEARCH (NEW PRIMARY WEB LAYER)
# =========================================================
def fetch_langsearch(query):
    headers = {
        "Authorization": f"Bearer {LANGSEARCH_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "limit": 10
    }

    try:
        res = requests.post(LANGSEARCH_URL, json=payload, headers=headers)

        if res.status_code != 200:
            return []

        data = res.json()
        pages = data.get("data", {}).get("webPages", {}).get("value", [])

        results = []
        for item in pages[:5]:
            results.append({
                "title": item.get("name", ""),
                "summary": item.get("snippet", "")[:300],
                "link": item.get("url", ""),
                "source": "langsearch"
            })

        return results

    except Exception as e:
        print("LangSearch error:", e)
        return []


# =========================================================
# 📄 2. ARXIV SEARCH
# =========================================================
def search_arxiv(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query"

    search_query = f"(all:{query})"

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }

    try:
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        results = []

        for entry in root.findall("atom:entry", ns):
            results.append({
                "title": entry.find("atom:title", ns).text.strip(),
                "summary": entry.find("atom:summary", ns).text.strip()[:300],
                "link": entry.find("atom:id", ns).text.strip(),
                "source": "arxiv"
            })

        return results

    except Exception as e:
        print("arXiv error:", e)
        return []


# =========================================================
# 🧬 3. PUBMED SEARCH
# =========================================================
def search_pubmed(query, max_results=5):
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }

    try:
        search_res = requests.get(search_url, params=params).json()
        ids = search_res.get("esearchresult", {}).get("idlist", [])

        if not ids:
            return []

        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml"
        }

        fetch_res = requests.get(fetch_url, params=fetch_params)
        root = ET.fromstring(fetch_res.content)

        results = []

        for article in root.findall(".//PubmedArticle"):
            title = article.find(".//ArticleTitle")
            abstract = article.find(".//Abstract/AbstractText")
            pmid = article.find(".//PMID")

            results.append({
                "title": title.text if title is not None else "No title",
                "summary": abstract.text[:300] if abstract is not None else "No abstract",
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid.text}/" if pmid is not None else "",
                "source": "pubmed"
            })

        return results

    except Exception as e:
        print("PubMed error:", e)
        return []


# =========================================================
# 🚀 4. UNIFIED TOOL (SINGLE QUERY → ALL SOURCES)
# =========================================================
def research_web_tool(query):
    return {
        "query": query,
        "langsearch": fetch_langsearch(query),
        "arxiv": search_arxiv(query),
        "pubmed": search_pubmed(query)
    }


# =========================================================
# 🧠 5. OPTIONAL LLM SUMMARY (GROQ)
# =========================================================
def summarize_with_llm(query, results):
    prompt = f"""
You are a research assistant.

User Query:
{query}

Sources:
{json.dumps(results, indent=2)}

Instructions:
- Combine all sources
- Remove duplicates
- Prefer scientific sources when available
- Be concise and factual

Final Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


# =========================================================
# 🧪 TEST
# =========================================================
if __name__ == "__main__":
    q = input("Enter query: ")

    results = research_web_tool(q)

    print("\n📦 RAW RESULTS:\n")
    print(json.dumps(results, indent=2))

    print("\n🧠 LLM SUMMARY:\n")
    print(summarize_with_llm(q, results))
