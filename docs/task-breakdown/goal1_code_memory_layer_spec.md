# Goal 1 – Code Memory Layer 📚

> **Objective:** implement an end-to-end, self-maintaining knowledge system for a *polyglot* codebase so that **client-side AI agents never hallucinate**, always see the freshest structure, and can reason about impact & policy.

---

## 1  Desired Outcomes

| 🏆  | Outcome |
|-----|---------|
| 1 | Every file, function, class, block in the repo is represented as a `(:CodeChunk)` vector in **Weaviate** and a typed node in **Neo4j**. |
| 2 | Structural, semantic, historical & domain relationships are queryable in Cypher (`CALLS`, `IMPORTS`, `TAGGED_AS`, `SIMILAR_TO`, `MODIFIED`) |
| 3 | Incremental watcher keeps graph + vectors in sync < 2 sec after a save. |
| 4 | Retrieval API returns a *layered* context bundle (graph slice + top-k chunks + external docs) with one call. |
| 5 | Novice developer can ask “change X” and agent reliably generates a correct diff with zero prompt engineering. |

---

## 2  Indexing Blueprint (as per user template)

### 2.1  Domain Enumeration
We will maintain a static `domains.yml` (future: auto-learn) containing all domains in §1 of the pattern. During ingestion we match path + heuristics to domain tags and store
```
(:Domain {name})
(:File)-[:TAGGED_AS]->(:Domain)
```

### 2.2  Metadata extracted per **File**
```
{
  language,           # py, ts, java…
  domains,            # ["backend","auth"]
  frameworks,         # ["FastAPI"]
  dependencies,       # pip/npm names
  role,               # entrypoint, test, config…
  git_commit, branch, rel_path,
  loc                 # lines-of-code
}
```

### 2.3  Multi-granular Chunking
| Level | Node label | Vector? | Stored in |
|-------|------------|---------|-----------|
| File          | `:File`      | ✔ | Weaviate / Neo4j |
| Class / Module| `:Class`     | ✔ | ↗ |
| Function      | `:Function`  | ✔ | ↗ |
| Block (>N)    | `:Block`     | ✔ | ↗ |

All chunks keep `source_id` (original id) + `uuid` (Weaviate).

### 2.4  Neo4j Schema (initial)
```
(:File)-[:CONTAINS]->(:Class|Function|Block)
(:Function)-[:CALLS]->(:Function)
(:File)-[:IMPORTS]->(:Library)
(:File)-[:TAGGED_AS]->(:Domain)
(:Commit)-[:MODIFIED]->(:File)
(:CodeChunk)-[:EMBEDS]->(:WeaviateObject)   # virtual link via uuid
```

### 2.5  Weaviate Classes
```
CodeChunk {
  uuid,                # PK
  source_id,           # sync w/ Neo4j node.id
  file_path,
  node_type,           # FILE/CLASS/…
  name,
  start_line, end_line,
  content,             # raw code
  domains[],           # same tags
  vector               # text2vec-ollama or Gemini
}
```

> **Hybrid Search:** vector + BM25 + metadata filter (file_path / domains).

---

## 3  Pipeline Stages

1. **Discovery** – FileWatcher emits path.
2. **Parsing** – ParserRegistry picks language parser → `CodeNode[]`, `CodeRelationship[]`.
3. **Graph Persist** – Upsert nodes & relationships to Neo4j.
4. **Chunk Embed** – Generate embeddings (Gemini) for embed-worthy nodes; insert into Weaviate.
5. **Health Hook** – Increment counters & expose `/metrics`.

All stages idempotent (MERGE + upsert).

---

## 4  Remaining Tasks Checklist

### 4.1  Critical Fixes
- [ ] **Weaviate UUID** – generate valid UUID4, store `source_id`.
- [ ] Ensure `CodeChunk` collection exists with correct schema (string PK).
- [ ] Replace remaining `.dict()` calls.

### 4.2  Feature Work
- [ ] Block-level splitter (AST + heuristics > N lines).
- [ ] Commit-diff ingester – hook via `git fsmonitor` or CI event.
- [ ] `Library` node extraction from `requirements.txt` & `package.json`.
- [ ] Implement JS/TS parser (tree-sitter).
- [ ] Domain auto-tagger.
- [ ] Retrieval API `/context?file=…`.
- [ ] Prometheus metrics.

### 4.3  Stretch
- [ ] Runtime call-graph (coverage or OpenTelemetry).
- [ ] SIMILAR_TO link based on embedding cosine.

---

## 5  Novice-Friendly Interaction Flow
1. **User** saves file / asks question in IDE.
2. **Client agent** → `/context` → receives rich bundle.
3. Agent calls LLM with bundle → presents diff or answer.
4. If user accepts change, agent triggers `/apply_diff` endpoint (future).

No prompt engineering needed—the agent & server negotiate queries.

---

## 6  References & Inspiration
- Neo4j Graph Academy call-graph demo (2025-05)
- Weaviate Hybrid Search white-paper 2025-02
- Google Gemini “embed_content” best-practices 2025-03

---

*Last updated 22 Jun 2025 by Cascade.*
