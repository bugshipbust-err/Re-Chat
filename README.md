## Re-Chat

**Re-Chat** is a fully local, personal AI assistant built to avoid reliance on online LLM services while still providing a highly personalized conversational experience.

It uses **Retrieval-Augmented Generation (RAG)** to store, retrieve, and reason over long-term user information, making interactions more contextual and tailored over time. While the architecture is intentionally simple, it has proven to be reliable, fast, and practical for daily use.

This is the project I consider my **cleanest work**.

---

### Motivation

The primary goals behind Re-Chat were to:
- Avoid using online or proprietary LLM APIs
- Maintain full control over personal data
- Experiment with long-term memory and personalization via RAG
- Build something genuinely useful enough to use every day

This project also marks my **first hands-on experience with LangChain**.

---

### High-Level Design

Re-Chat consists of three main components:

1. **Local LLM Inference**
   - Uses Ollama-hosted models (e.g. `llama3.1`, `gpt-oss`)
   - No external API calls

2. **User-Centric RAG System**
   - Stores distilled user information rather than raw conversations
   - Retrieves relevant personal context during inference
   - Avoids unnecessary duplication in memory

3. **Interactive Chat Interface**
   - Terminal-based UI (TUI)
   - Persistent conversational state

---

### Core Ideas

- **Memory as distilled facts, not transcripts**  
  Conversations are summarized into meaningful user-related statements before ingestion.

- **Controlled ingestion**  
  New information is compared against existing memory using an LLM-based decision step to determine whether it should be added or skipped.

- **Query decomposition**  
  User queries are broken into sub-queries to improve retrieval quality from the vector database.

---

### Key Components

#### `UserRAG`
A custom RAG pipeline responsible for:
- Extracting user-relevant facts from conversations
- Generating retrieval queries
- Performing similarity search over stored memories
- Ingesting new information selectively

Internally, it uses:
- **Chroma** for vector storage
- **Ollama embeddings**
- **LLM agents with structured outputs** for decision-making

#### Agents
- **Query generation agent** – expands user queries into multiple retrieval queries
- **Summarization agent** – extracts long-term user information from conversations
- **Decision agent** – decides whether new information replaces or complements existing memory

---

### Tech Stack

- Python
- LangChain
- ChromaDB
- Ollama
- Pydantic
- Terminal-based UI (TUI)

---
