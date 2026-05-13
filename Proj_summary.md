**Agentic AI Research Assistant with RAG and MCP Integration**

**1. Problem Statement**

Modern users (students, researchers, professionals) deal with:

- Large volumes of documents (PDFs, reports, notes)
- Scattered external information (web, APIs)

### ❌ Current Problems:

- Hard to extract relevant insights quickly
- LLMs alone → hallucinate
- Tools exist but are not integrated intelligently

Design a system that:

**Understands user queries, retrieves relevant document information, and dynamically uses external tools via a modular protocol (MCP) to generate accurate, context-aware responses.**

# 2. Objectives

- Build a **RAG-based QA system**
- Extend it into an **agentic system**
- Integrate external tools via
   Model Context Protocol
- Ensure:
  - accuracy
  - modularity
  - scalability

#  3. Expected User Inputs

### 🔹 Input Types:

#### 1. Document Upload

- PDF / text files

#### 2. Natural Language Queries

Examples:

"What is the main contribution of this paper?"
"Summarize section 3"
"Compare this with current industry trends"

#  4. System Requirements

------

## 🔹 Functional Requirements

### 📄 Document Processing

- Extract text from PDF
- Chunking (fixed / semantic)
- Store embeddings

------

### 🔍 Retrieval (RAG)

- Query → embedding
- Similarity search (top-k chunks)
- Context injection into LLM

------

### 🤖 Agent System

- Decide:
  - Use RAG?
  - Call tool?
- Multi-step reasoning

------

### 🔌 MCP Integration

- Tools exposed via protocol:
  - Web search
  - Calculator
  - File tools
- Communication:
  - JSON-RPC style request/response

------

### 🧠 Memory

- Maintain chat history
- Context-aware responses

# 5. Expected Output

------

## 🔹 Output Format

### 1. Answer (Natural Language)

```
"This paper proposes a transformer-based approach..."
```

------

### 2. Citations (VERY IMPORTANT)

```
Source:
- Page 3: "Transformer improves efficiency..."
```

------

### 3. Tool Usage (if used)

```
[Used Tool: Web Search]
"Recent trends show..."
```

------

### 4. Structured Output (Optional)

```
{
  "summary": "...",
  "key_points": ["...", "..."],
  "external_insights": ["..."]
}
```

------

# 🔄 6. System Workflow (End-to-End)

------

## 🧭 Step-by-Step Flow

```
1. User uploads document
2. System preprocesses:
   → chunking
   → embeddings stored (FAISS)

3. User asks query

4. Agent receives query

5. Decision:
   IF doc-related → use RAG
   IF external info needed → call MCP tool

6. MCP tool executes:
   → returns data

7. LLM combines:
   → retrieved chunks
   → tool output

8. Final response generated

9. Memory updated
```

------

# 🏗️ 7. Architecture Overview

```
User
  ↓
Frontend (Streamlit)
  ↓
Agent (LangGraph)
  ↓
 ┌──────────────┬──────────────┐
 ↓              ↓              ↓
RAG Engine     MCP Tools      Memory
(FAISS)        (Server)       (Chat History)
```

------

# 🧰 8. Tech Stack

- LangGraph
- LangChain
- FAISS
- Streamlit

------

# 🎯 9. Key Features (Highlight These in Resume)

- Hybrid **RAG + Agent system**
- **MCP-based modular tool integration**
- Dynamic decision making
- Context-aware memory
- Source-grounded responses