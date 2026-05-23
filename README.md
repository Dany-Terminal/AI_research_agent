
### Note: The System Architecture Diagram is given in *==Sys_Design.pdf==* 


```markdown
# 🧠 DSL-Based Multi-Tool AI Router with Memory

A modular AI system that intelligently routes user queries across multiple tools (RAG, Web, PDF, Research) using an LLM-based planner — enhanced with **context-aware memory** and **query rewriting**.

---

## ✨ Features

- 🧠 **LLM-Based Tool Routing**
  - Uses a DSL (Domain-Specific Language) instead of JSON for robust parsing
  - Dynamically selects one or more tools per query

- 🔍 **RAG Integration (FAISS)**
  - Semantic similarity search
  - Automatically triggered for knowledge-based queries

- 🌐 **Web Search Tool**
  - Handles real-time / latest information queries

- 📄 **PDF Query System**
  - Extracts and answers questions from local PDFs

- 📚 **Research Paper Tool**
  - Fetches and processes academic content

- 🧠 **Short-Term Memory System**
  - Maintains conversation context
  - Stores last 4 interactions + rolling summary

- 🔁 **Query Rewriting**
  - Resolves references like:
    - "it"
    - "that"
    - "previous one"

- ⚡ **Multi-Tool Execution**
  - Supports chaining tools
  - Merges outputs using LLM

---

## 🏗️ Architecture

```

User Query  
↓  
Memory Context (summary + recent)  
↓  
Query Rewriting (LLM)  
↓  
Tool Planner (DSL via LLM)  
↓  
Tool Execution (RAG / Web / PDF / Research)  
↓  
Final Answer Generator (LLM)  
↓  
Memory Update

````

---

## 📂 Project Structure

```
.
├── router.py              # Main orchestration logic
├── memory/
│   └── memory.py         # Context + summarization system
├── tools/
│   ├── pdf_tool.py
│   ├── web_tool.py
├── rag/
│   └── rag_retrival.py   # FAISS-based retrieval
├── .env                  # API keys
└── README.md
````

---

## ⚙️ Setup

### 1. Clone repo

```bash
git clone https://github.com/Dany-Terminal/AI_research_agent.git
cd AI_research_agent
```

---

### 2. Create virtual environment

```bash
python -m venv <name of env>

source <name of env>/bin/activate   # Linux/Mac
<name of env>\Scripts\activate      # Windows
```

---

### 3. Install dependencies

```bash
pip install groq python-dotenv faiss-cpu numpy requests beautifulsoup4 PyPDF2 tiktoken
```

---

### 4. Setup environment variables

Create `.env` file (inside proj directory):

```env
GROQ_API_KEY=your_api_key_here
LANGSEARCH_API_KEY=your_api_key_here
```

---

## ▶️ Run the CLI

```bash
python router.py
```

Example:

```
🔍 You: What is the latest Python version?
🤖 Answer: ...

🔍 You: What about its release date?
🤖 Answer: ...
```

---

## 🧠 Memory System

- Stores last 4 interactions
    
- Older interactions are summarized
    
- Maintains:
    
    - topic continuity
        
    - entity tracking
        
    - comparison context
        

---

## 🔁 Query Rewriting Example

|User Input|Rewritten Query|
|---|---|
|"What about it?"|"What about Python latest version?"|

---

## 🔌 Supported Tools

|Tool|Purpose|
|---|---|
|`rag`|Semantic retrieval from vector DB|
|`web`|Latest information|
|`pdf`|Local document QA|
|`research`|Academic search|

---

## 📌 Future Improvements

- 🔮 Long-term memory using vector DB
    
- 🎯 Intent classification before routing
    
- ⚡ Tool result caching
    
- 🌍 API deployment (FastAPI)
    
- 🧠 Memory-aware tool prioritization
    

---

## 🧑‍💻 Author

Built with ❤️ by _[Danyal Ahmad]_

---

## ⭐ If you like this project

Give it a star ⭐ — it helps a lot!
