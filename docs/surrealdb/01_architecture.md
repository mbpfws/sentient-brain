# Sentient-Brain SurrealDB Architecture (Draft v0.1)

> This document outlines the new single-DB design that replaces Neo4j + Weaviate with SurrealDB and introduces a multi-agent workflow powered by LangGraph / CrewAI.

## 1. Rationale
* One dependency instead of two → less memory, simpler ops.
* Native vector & graph support in the same query layer (SurrealQL).
* Built-in pub/sub enables decoupled agent messaging.

## 2. Services (Docker Compose)
| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| surrealdb | `surrealdb/surrealdb:latest` | 8001(http) / 8002(ws) | Graph+Vector store |
| server | `sentient-brain-py-server` | 8000 | FastAPI + agents |
| ollama | `ollama/ollama:latest` | 11434 | Local fallback LLM |

Groq & Gemini calls are outbound HTTPS (no containers).

## 3. Memory Layers → SurrealDB Tables
| Layer | Table | Key Fields |
|-------|-------|-----------|
| Code   | `code_chunk` | `id`, `file_path`, `content`, `vector`, `meta` |
| Docs   | `document_chunk` | `id`, `source_uri`, `content`, `vector`, `meta` |
| Tasks  | `task` | `id`, `title`, `status`, `parent`, `vec_summary` |
| Chat   | `chat_message` | `id`, `role`, `content`, `vector`, `thread_id` |
| Concept | `knowledge_concept` | `id`, `title`, `summary`, `vector`, `rel` |

> All tables share `ts` timestamp + `vector` column with KNN index `search::knn(distance: cosine, dims: 384)`.

## 4. Agents & Roles
* **UltraOrchestrator** (root FSM; spawns others)
* ArchitectAgent (green-field or enhancement mode)
* CodeIndexerAgent (file watcher → SurrealDB)
* DocsCrawlerAgent (scrape docs → chunks)
* RefactorAgent (post-run improvements)

Agents are implemented with LangGraph; each edge is a SurrealDB pub/sub channel (`notify agent_x topic_y payload`).

## 5. LLM / Embedding Stack
* Primary chat: **meta-llama/llama-4-scout-17b-16e-instruct** via Groq API.
* Fallbacks: `gemini-2.5-flash` (fast) & `gemini-2.5-pro` (accurate).
* Embeddings: `text-embedding-3-small` (OpenAI) or local MiniLM.

## 6. External Integrations
* Coral Protocol: store DID creds in table `credential`.
* Fetch.ai: pluggable AEAs launched by Orchestrator.

## 7. Next Steps
1. Finalise SurrealDB schema (`02_schema.sql`).
2. Build Surreal client wrapper.
3. Create Ultra Orchestrator prompt templates (`03_agent_templates.md`).
4. Remove Neo4j / Weaviate services.
5. Migrate existing ingestion tests.
