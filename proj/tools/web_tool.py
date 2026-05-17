import requests
import xml.etree.ElementTree as ET


# ---------------------------
# 🔍 arXiv Search (Filtered)
# ---------------------------
def search_arxiv(query, max_results=10):
    base_url = "http://export.arxiv.org/api/query"

    # Restrict to CS + AI related categories
    search_query = f"(all:{query}) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV)"

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }

    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        return []

    root = ET.fromstring(response.content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    results = []

    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip()
        summary = entry.find("atom:summary", ns).text.strip()
        link = entry.find("atom:id", ns).text.strip()

        results.append({
            "title": title,
            "summary": summary[:500],
            "link": link,
            "source": "arxiv"
        })

    return results


# ---------------------------
# 🔍 PubMed Search
# ---------------------------
def search_pubmed(query, max_results=10):
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }

    search_res = requests.get(search_url, params=search_params).json()
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

    articles = root.findall(".//PubmedArticle")

    results = []

    for article in articles:
        try:
            title = article.find(".//ArticleTitle").text
        except:
            title = "No title"

        try:
            abstract = article.find(".//Abstract/AbstractText").text
        except:
            abstract = "No abstract available"

        try:
            pmid = article.find(".//PMID").text
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        except:
            link = "No link"

        results.append({
            "title": title,
            "summary": abstract[:500],
            "link": link,
            "source": "pubmed"
        })

    return results


# ---------------------------
# 🚀 Combined Tool
# ---------------------------
def research_web_tool(query):
    return {
        "arxiv": search_arxiv(query),
        "pubmed": search_pubmed(query)
    }


# ---------------------------
# 🧪 Test Run
# ---------------------------
if __name__ == "__main__":
    query = input("Enter query: ")
    results = research_web_tool(query)

    import json
    print(json.dumps(results, indent=2))
