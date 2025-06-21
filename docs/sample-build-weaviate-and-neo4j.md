
---

## 1. Quick AST→Graph Example

Take this tiny Python file, `greet.py`:

```python
# greet.py
def greet(name):
    print("Hello, " + name)
```

AST hierarchy:  
• Module  
  → FunctionDef(name=“greet”)  
    → arguments(arg=“name”)  
    → Expr  
      → Call(func=Name(id=“print”))  
        → BinOp(left=Constant("Hello, "), op=Add, right=Name("name"))

We want Neo4j nodes like `(Module)`, `(Func:greet)`, `(Arg:name)`, `(Call:print)`, and relationships like `(:Func)-[:HAS_ARG]->(:Arg)` or `(:Call)-[:CALLS]->(:Func)`.

---

## 2. Prerequisites

```bash
pip install neo4j weaviate-client gitpython
# plus your FastAPI, pydantic-graph, etc.
```

Ensure Neo4j is running (bolt://localhost:7687) and Weaviate is up with your API key.

---

## 3. AST → Neo4j Script

```python
# code_graph.py
import ast, uuid
from neo4j import GraphDatabase

class AST2Neo4j(ast.NodeVisitor):
    def __init__(self, tx):
        self.tx = tx
        self.stack = []  # parent node IDs

    def _create_node(self, label, props):
        node_id = str(uuid.uuid4())
        props["id"] = node_id
        self.tx.run(
            f"CREATE (n:{label} $props)",
            props=props
        )
        return node_id

    def _link(self, parent_id, child_id, rel):
        self.tx.run(
            """
            MATCH (a {id:$p}), (b {id:$c})
            CREATE (a)-[r:%s]->(b)
            """ % rel,
            p=parent_id, c=child_id
        )

    def generic_visit(self, node):
        label = node.__class__.__name__
        props = {}
        # capture relevant props:
        for field in ("name","id","arg","attr","n"):
            if hasattr(node, field):
                props[field] = getattr(node, field)
        curr_id = self._create_node(label, props)
        if self.stack:
            self._link(self.stack[-1], curr_id, "CHILD_OF")
        self.stack.append(curr_id)
        super().generic_visit(node)
        self.stack.pop()

def ingest_file_to_neo4j(filepath, neo4j_uri, auth):
    driver = GraphDatabase.driver(neo4j_uri, auth=auth)
    source = open(filepath).read()
    tree = ast.parse(source, filepath)
    with driver.session() as sess:
        sess.write_transaction(lambda tx: AST2Neo4j(tx).visit(tree))
    driver.close()

if __name__ == "__main__":
    ingest_file_to_neo4j(
      "greet.py",
      "bolt://localhost:7687", ("neo4j","password")
    )
```

What happens:  
1) We parse `greet.py` into an `ast.Module`.  
2) We walk every AST node, create a Neo4j node labeled by its class (`FunctionDef`, `Call`, …) with minimal properties.  
3) We link each node back to its parent via `CHILD_OF`.

---

## 4. Integrate into Your FastAPI MCP Server

```python
# services/code_graph_service.py
from fastapi import APIRouter
from pydantic import BaseModel
from .code_graph import ingest_file_to_neo4j
import git  # GitPython

router = APIRouter()

class RepoIn(BaseModel):
    url: str

@router.post("/ingest_repository")
async def ingest_repository(config: RepoIn):
    # 1. Clone
    repo = git.Repo.clone_from(config.url, "/tmp/mcp_repo", depth=1)
    # 2. Iterate .py files
    for path in repo.working_tree_dir.glob("**/*.py"):
        ingest_file_to_neo4j(
            str(path),
            "bolt://neo4j:7687", ("neo4j","password")
        )
    return {"status":"ok","files":len(list(repo.working_tree_dir.glob("**/*.py")))}
```

Plug that router into your main FastAPI app. Now your MCP client can call `mcp_call_tool("ingest_repository",{"url":…})`.

---

## 5. Adding Weaviate for Hybrid Search

Once code is in Neo4j, you may want semantic search over function bodies. Let’s push each function’s source code snippet into Weaviate:

```python
# services/code_weaviate.py
from weaviate import Client
import ast, inspect

weaviate_client = Client("http://localhost:8080")

# Ensure class exists
weaviate_client.schema.create_class({
  "class": "FunctionSnippet",
  "vectorizer": "none",
  "properties": [
    {"name":"func_name","dataType":["string"]},
    {"name":"code","dataType":["text"]}
  ]
})

def ingest_functions_to_weaviate(filepath):
    source = open(filepath).read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            src = inspect.getsource(node)
            weaviate_client.data_object.create(
                {
                  "func_name": node.name,
                  "code": src
                },
                "FunctionSnippet"
            )
```

Combine this in your same `/ingest_repository` loop, so every Python function is both graph-modeled in Neo4j _and_ text-indexed in Weaviate.

---

## 6. Refactoring & Queries

Now you can write:

• Cypher to find all callers of `greet`:
```cypher
MATCH (f:FunctionDef {name:"greet"})<-[:CALLS]-(caller)
RETURN caller.name;
```

• Weaviate to semantically search for functions containing “hello world”:
```python
res = weaviate_client.query\
  .get("FunctionSnippet", ["func_name","code"])\
  .with_near_text({"concepts":["print hello"]})\
  .with_limit(5)\
  .do()
```

• Or hybrid: find functions that call `greet` (structural filter) _and_ whose implementation mentions “log” (semantic filter).

---

## 7. Next Steps & Tips

1. **Indexing Performance**: Batch your Neo4j writes (UNWIND) and Weaviate creates to speed up large repos.  
2. **Schema Tuning**: Add indexes in Neo4j on `:FunctionDef(name)` & Weaviate filters on `func_name`.  
3. **Cross-Language**: Swap Python’s `ast` for JS’s `@babel/parser`, same pattern.  
4. **Refactor Pipelines**: Use your `pydantic-graph` flows to orchestrate ingestion, syncing, error-retry.  
5. **Visualization**: Hook Neo4j Bloom or the built-in browser to explore your code graph interactively.

With this in place, your MCP server can both _understand_ code structure deeply and _search_ it semantically—powering next-gen AI coding assistants.

Here’s how you can get Neo4j and Weaviate talking to each other in your MCP server so you get lightning-fast structural queries and rich semantic search over the same codebase.

---

## 1. Why integrate Neo4j + Weaviate?

- Neo4j = perfect for “who-calls-who,” inheritance hierarchies, dependency graphs.  
- Weaviate = perfect for “find me functions that look like…”, semantic similarity, natural-language filters.  
- Together you can do powerful two-step queries, e.g.:  
  1. Neo4j: find all methods overriding `Foo.do()` in your graph  
  2. Weaviate: among those, rank by “closest to ‘database migration’”  

---

## 2. Overall architecture patterns

1. **Dual-writes at ingest**  
   - Your AST parser writes each node into Neo4j.  
   - In the same loop you also push that node’s snippet+metadata into Weaviate.  
   - Pros: simple, zero lag.  
   - Cons: coupling, back-pressure if one DB falls over.

2. **Event-driven sync**  
   - Parser → Kafka/RabbitMQ publishes “FunctionParsed” events.  
   - Neo4j consumer picks them up, writes graph nodes/rels.  
   - Weaviate consumer picks them up, writes vector objects.  
   - Pros: decoupled, resilient.  
   - Cons: added infra and latency.

3. **Batch ETL**  
   - Periodic job:  
     • Pull changed AST nodes from Neo4j (e.g. `updated_at` index)  
     • Push to Weaviate.  
   - Pros: simple if code rarely changes.  
   - Cons: stale search index between runs.

---

## 3. Data-model linking

In Neo4j you might have:
```cypher
(:FunctionDef {id:"UUID", name:"greet", file:"greet.py", weaviateRef:"<obj_id>"})
```
– `weaviateRef` stores that function’s Weaviate object-ID.  

In Weaviate you have a class:
```jsonc
{
  "class": "FunctionSnippet",
  "vectorizer": "text2vec-transformer",
  "properties": [
    { "name":"function_id", "dataType":["string"] },
    { "name":"code",        "dataType":["text"]   }
  ]
}
```
– `function_id` ties back to your Neo4j node’s `id` prop.

---

## 4. Code snippets

### 4.1 Dual-write example (inline AST pipeline)

```python
from weaviate import Client as WaClient
from neo4j import GraphDatabase
import ast, uuid

wa = WaClient("http://localhost:8080")
neo = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j","pw"))

def index_function(node: ast.FunctionDef, source:str):
    func_id = str(uuid.uuid4())
    # 1) write graph
    with neo.session() as s:
        s.run(
          "CREATE (f:FunctionDef {id:$id, name:$n, file:$f, weaviateRef:$w})",
          id=func_id, n=node.name, f=source, w=None
        )
    # 2) write vector
    obj = wa.data_object.create({
      "function_id": func_id,
      "code": ast.get_source_segment(source, node)
    },"FunctionSnippet")
    # 3) store back weaviateRef
    with neo.session() as s:
        s.run(
          "MATCH (f:FunctionDef {id:$id}) SET f.weaviateRef=$w",
          id=func_id, w=obj["id"]
        )

# in your AST2Neo4j visitor:
if isinstance(node, ast.FunctionDef):
    index_function(node, filepath)
```

### 4.2 Event-driven (pydantic-graph flow)

```python
from pydantic_graph import Graph, Node

class ParseAST(Node):
    filepath: str
    def run(self):
        # emit events for each FunctionDef…
        return [dict(name=n.name, src=src) for n in ast.walk(tree)]

class WriteNeo4j(Node):
    events: list
    def run(self):
        # write graph nodes, return list of func_ids
        …

class WriteWeaviate(Node):
    funcs: list
    def run(self):
        # push to weaviate, return mapping {func_id:weav_id}
        …

class LinkRefs(Node):
    mapping: dict
    def run(self):
        # back-populate Neo4j weaviateRef props
        …

flow = Graph(
  ParseAST  >>  WriteNeo4j  >>  WriteWeaviate  >>  LinkRefs
)
flow(filepath="greet.py")
```

---

## 5. Hybrid query patterns

1. **Graph → Semantic**  
   ```cypher
   MATCH (f:FunctionDef)-[:CALLS]->(g:FunctionDef {name:"migrate"})
   RETURN f.id AS func_id;
   ```
   take that list of `func_id` in Python, then:
   ```python
   wa.query.get("FunctionSnippet", ["function_id","code"])\
     .with_where({"path":["function_id"],"operator":"In","valueString":ids})\
     .with_near_text({"concepts":["optimize database"]})\
     .do()
   ```

2. **Semantic → Graph**  
   ```python
   sem_res = wa.query.get("FunctionSnippet", ["function_id"])\
       .with_near_text({"concepts":["unit test framework"]})\
       .with_limit(20)\
       .do()
   ids = [o["function_id"] for o in sem_res["data"]["Get"]["FunctionSnippet"]]
   ```
   ```cypher
   MATCH (f:FunctionDef) WHERE f.id IN $ids
   RETURN f.name, size((f)-[:CALLS]->()) AS fanOut
   ```

---

## 6. Tips & next steps

- **Index tuning**  
  • Neo4j: `CREATE INDEX FOR (f:FunctionDef) ON (f.name);`  
  • Weaviate: pick the right vectorizer, tune `ef`/`efConstruction`.

- **Sync monitoring**  
  • Emit metrics/events when writes succeed/fail.  
  • Build a small dashboard: count mismatch between graph nodes vs Weaviate objects.

- **Cross-language**  
  • Use the same pattern for JavaScript (Babel AST), Java (Eclipse JDT), etc.

- **Advanced: Graph-only vector filters**  
  • Neo4j 5+ supports vector properties—store embeddings in Neo4j and perform `kNN` search purely in graph.

With this in place, your MCP server can fluidly answer both “show me the structural call graph” **and** “find me functions semantically about logging,” all in one unified pipeline.