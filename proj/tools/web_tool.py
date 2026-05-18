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
# 🌐 LANGSEARCH (GENERAL WEB)
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
                "link": item.get("url", "")
            })

        return results

    except Exception:
        return []


# =========================================================
# 📄 ARXIV
# =========================================================
def search_arxiv(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query"

    params = {
        "search_query": f"(all:{query})",
        "start": 0,
        "max_results": max_results
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
                "link": entry.find("atom:id", ns).text.strip()
            })

        return results

    except Exception:
        return []


# =========================================================
# 🧬 PUBMED
# =========================================================
def search_pubmed(query, max_results=5):
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

        search_res = requests.get(search_url, params={
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json"
        }).json()

        ids = search_res.get("esearchresult", {}).get("idlist", [])

        if not ids:
            return []

        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

        fetch_res = requests.get(fetch_url, params={
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml"
        })

        root = ET.fromstring(fetch_res.content)

        results = []
        for article in root.findall(".//PubmedArticle"):
            title = article.find(".//ArticleTitle")
            abstract = article.find(".//Abstract/AbstractText")
            pmid = article.find(".//PMID")

            results.append({
                "title": title.text if title is not None else "",
                "summary": abstract.text[:300] if abstract is not None else "",
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid.text}/" if pmid is not None else ""
            })

        return results

    except Exception:
        return []


# =========================================================
# 🧠 TOOL 1: RESEARCH PAPER TOOL
# =========================================================
def research_paper_tool(query: str) -> dict:
    """
    arXiv + PubMed combined tool
    """

    arxiv_results = search_arxiv(query)
    pubmed_results = search_pubmed(query)

    combined = arxiv_results + pubmed_results

    return {
        "tool": "research_paper",
        "query": query,
        "results": combined,
        "found": len(combined) > 0
    }


# =========================================================
# 🧠 TOOL 2: WEB SEARCH TOOL (WITH LLM)
# =========================================================
def web_search_tool(query: str) -> dict:
    """
    General web search + LLM summary
    """

    results = fetch_langsearch(query)

    if not results:
        return {
            "tool": "web",
            "answer": "No web results found.",
            "found": False
        }

    prompt = f"""
You are a research assistant.

User Query:
{query}

Sources:
{json.dumps(results, indent=2)}

Instructions:
- Summarize clearly
- Remove duplicates
- Keep it concise

Final Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return {
        "tool": "web",
        "answer": response.choices[0].message.content,
        "sources": results,
        "found": True
    }
