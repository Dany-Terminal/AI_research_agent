import os
from dotenv import load_dotenv
from groq import Groq

# ---------------------------
# Load ENV (ONLY ONCE)
# ---------------------------
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ---------------------------
# Tools
# ---------------------------
from tools.pdf_tool import pdf_tool
from tools.web_tool import web_search_tool, research_paper_tool
from rag.rag_retrival import rag_tool, retrieve

#memory
from memory.memory import get_context, add_interaction
# =========================================================
# 📊 FAISS SCORE
# =========================================================
def get_rag_score(query: str) -> float:
    _, distances = retrieve(query, k=1)
    return float(distances[0]) if distances else 0.0

#Deterministic PDF path detector
def extract_pdf_path(query: str):
    words = query.split()
    for w in words:
        if w.endswith(".pdf"):
            return w
    return None

# =========================================================
# 🧠 DSL TOOL PLANNER (NO JSON)
# =========================================================
def plan_tools(query: str, rag_score: float):
    prompt = f"""
You are a tool routing system.

Return ONLY tool calls in DSL format.

DO NOT explain.
DO NOT use JSON.
DO NOT use markdown.
DO NOT add any extra text.

FORMAT:
TOOL:<tool_name>|<input>

AVAILABLE TOOLS:
- rag
- pdf
- web
- research

RULES:
- You MAY use multiple tools
- One tool per line
- Maintain correct execution order

User Query:
{query}

FAISS Score:
{rag_score}
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return parse_dsl(res.choices[0].message.content)


# =========================================================
# ⚙️ DSL PARSER (ROBUST)
# =========================================================
def parse_dsl(text: str):
    tools = []

    if not text:
        return {"tools": []}

    for line in text.strip().split("\n"):
        line = line.strip()

        if line.startswith("TOOL:"):
            try:
                body = line.replace("TOOL:", "", 1)
                name, inp = body.split("|", 1)

                tools.append({
                    "name": name.strip(),
                    "input": inp.strip()
                })

            except Exception:
                continue

    return {"tools": tools}


# =========================================================
# ⚙️ TOOL EXECUTION ENGINE
# =========================================================
def execute_tools(plan, query):
    outputs = []

    for tool in plan.get("tools", []):

        name = tool.get("name")
        inp = tool.get("input", query)

        # ---------------- RAG ----------------
        if name == "rag":
            outputs.append({
                "tool": "rag",
                "output": rag_tool(query)
            })

        # ---------------- PDF ----------------
        elif name == "pdf":
            if isinstance(inp, str) and os.path.exists(inp):
                outputs.append({
                    "tool": "pdf",
                    "output": pdf_tool(inp, query, client)
                })

        # ---------------- WEB ----------------
        elif name == "web":
            outputs.append({
                "tool": "web",
                "output": web_search_tool(query)
            })

        # ---------------- RESEARCH ----------------
        elif name == "research":
            outputs.append({
                "tool": "research",
                "output": research_paper_tool(query)
            })

    return outputs


# =========================================================
# 🧠 FINAL ANSWER GENERATOR
# =========================================================
def generate_final_answer(query, tool_outputs):
    prompt = f"""
You are a final answer system.

User Query:
{query}

Tool Outputs:
{tool_outputs}

INSTRUCTIONS:
- Combine all tool outputs
- Remove repetition
- Prefer factual accuracy
- Be concise and structured

FINAL ANSWER:
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return res.choices[0].message.content

def rewrite_query(query, context):
    prompt = f"""
Rewrite the query using context if needed.

RULES:
- Resolve references like "it", "that", "previous"
- Keep original intent
- If no rewrite needed, return original query

Context:
{context}

Query:
{query}

Rewritten Query:
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    return res.choices[0].message.content.strip()
# =========================================================
# 🚀 MAIN ROUTER
# =========================================================
def run_router(query: str):

    # ---------------- PDF DIRECT ----------------
    pdf_path = extract_pdf_path(query)
    if pdf_path and os.path.exists(pdf_path):
        result = pdf_tool(pdf_path, query, client)
        add_interaction(query, str(result))
        return result

    # ---------------- 🧠 MEMORY ----------------
    context = get_context()

    # ---------------- 🧠 QUERY REWRITE ----------------
    rewritten_query = rewrite_query(query, context)

    print(f"\n🧠 Rewritten Query: {rewritten_query}\n")  # optional debug

    # ---------------- 🧠 ENHANCED QUERY ----------------
    enhanced_query = f"""
Conversation Context:
{context}

User Query:
{rewritten_query}
"""

    # ---------------- 📊 RAG SCORE ----------------
    rag_score = get_rag_score(enhanced_query)

    # ---------------- 🧠 PLAN ----------------
    plan = plan_tools(enhanced_query, rag_score)

    # ---------------- ⚙️ EXECUTE ----------------
    tool_outputs = execute_tools(plan, enhanced_query)

    # ---------------- ✅ SINGLE TOOL ----------------
    if len(tool_outputs) == 1:
        result = tool_outputs[0]["output"]
        add_interaction(query, str(result))
        return result

    # ---------------- ❌ NO TOOL ----------------
    if len(tool_outputs) == 0:
        final_answer = "No tools were triggered for this query."
        add_interaction(query, final_answer)
        return final_answer

    # ---------------- 🧠 FINAL ANSWER ----------------
    final_answer = generate_final_answer(enhanced_query, tool_outputs)

    add_interaction(query, final_answer)

    return final_answer
#clean print result
def pretty_print(result):
    import json

    print("\n" + "─" * 60)

    if isinstance(result, dict):

        tool = result.get("tool", "unknown")
        print(f"🧠 Tool Used: {tool.upper()}")

        if tool == "pdf" and "pdf_name" in result:
            print(f"📄 Source: {result['pdf_name']}")

        print("\n📖 Answer:\n")
        print(result.get("answer") or result.get("content") or json.dumps(result, indent=2))

    else:
        print("\n📖 Answer:\n")
        print(result)

    print("\n" + "─" * 60 + "\n")
# =========================================================
# 🧪 CLI
# =========================================================
if __name__ == "__main__":

    print("\n🧠 DSL Multi-Tool AI Router Started (type 'exit' to quit)\n")

    while True:
        query = input("🔍 You: ")

        if query.lower() == "exit":
            break

        result = run_router(query)

        print("\n🤖 Answer:\n")
        pretty_print(result)
        print("\n" + "-" * 60 + "\n")
