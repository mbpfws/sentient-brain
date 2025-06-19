# **MCP Server RESTful API Specification v1.0**

This document provides a complete specification for the Model Context Protocol (MCP) server's RESTful API. The API is organized around the four core memory layers defined in the database architecture.

**Base URL:** `/api/v1`

---

### **1. Common Objects & Conventions**

#### **1.1. Standard Error Response**

Used for `4xx` and `5xx` status codes.

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "optional string or object with more info"
  }
}
```

#### **1.2. Pagination Object**

Included in list responses that support pagination.

```json
{
  "pagination": {
    "total_items": 100,
    "total_pages": 10,
    "current_page": 1,
    "page_size": 10
  }
}
```

---

## **Code Memory API**

Endpoints for managing repositories, code files, summaries, and intra-code dependencies.

### **2.1. Code Repositories**

**Resource URL:** `/code/repositories`

| Endpoint | Description |
| :--- | :--- |
| `POST /code/repositories` | Creates a new code repository record. |
| `GET /code/repositories` | Lists all code repositories. |
| `GET /code/repositories/{repoId}` | Retrieves a single repository by its ID. |
| `PUT /code/repositories/{repoId}` | Updates an existing repository. |
| `DELETE /code/repositories/{repoId}` | Deletes a repository and all its associated files. |

---

#### **`POST /code/repositories`**
*   **Description:** Creates a new code repository entry.
*   **Request Body:**
    ```json
    {
      "name": "string",
      "local_path": "string"
    }
    ```
*   **Success Response:** `201 Created`
    ```json
    {
      "id": "uuid",
      "name": "string",
      "local_path": "string",
      "created_at": "timestamp with timezone",
      "updated_at": "timestamp with timezone"
    }
    ```

---

### **2.2. Code Files & Directories**

**Resource URL:** `/code/repositories/{repoId}/files`

| Endpoint | Description |
| :--- | :--- |
| `POST /code/repositories/{repoId}/files` | Creates a new file or directory within a repository. |
| `GET /code/repositories/{repoId}/tree` | Retrieves the entire file/directory hierarchy for a repository. |
| `GET /code/files/{fileId}` | Retrieves details for a specific file or directory. |
| `PUT /code/files/{fileId}` | Updates the properties of a file or directory. |
| `DELETE /code/files/{fileId}` | Deletes a file or directory. |
| `POST /code/files/{fileId}/sync` | Triggers a sync and analysis for a specific file. |

---

#### **`POST /code/repositories/{repoId}/files`**
*   **Description:** Creates a new file or directory. The server is responsible for calculating `content_hash` if content is provided.
*   **Request Body:**
    ```json
    {
      "parent_id": "uuid, optional, null for root items",
      "is_directory": "boolean",
      "file_path": "string, full path relative to repo root",
      "content": "string, optional, base64 encoded file content"
    }
    ```
*   **Success Response:** `201 Created`
    ```json
    {
      "id": "uuid",
      "repository_id": "uuid",
      "parent_id": "uuid or null",
      "is_directory": "boolean",
      "file_path": "string",
      "content_hash": "string (sha-256) or null",
      "status": "string, one of ['pending', 'synced', 'error', 'stale']",
      "last_analyzed_at": "timestamp with timezone or null",
      "created_at": "timestamp with timezone",
      "updated_at": "timestamp with timezone"
    }
    ```
---
#### **`GET /code/repositories/{repoId}/tree`**
*   **Description:** Returns the complete, nested file and directory structure for a repository.
*   **Success Response:** `200 OK`
    ```json
    [
      {
        "id": "uuid",
        "file_path": "src/",
        "is_directory": true,
        "status": "synced",
        "children": [
          {
            "id": "uuid",
            "file_path": "src/index.js",
            "is_directory": false,
            "status": "synced",
            "children": []
          }
        ]
      }
    ]
    ```

---

### **2.3. Code Summaries & Dependencies**

| Endpoint | Description |
| :--- | :--- |
| `POST /code/files/{fileId}/summaries` | Creates an AI-generated summary for a file. |
| `GET /code/files/{fileId}/summaries` | Lists all summaries for a file. |
| `POST /code/files/{fileId}/dependencies` | Links a source file to a target dependency file. |
| `GET /code/files/{fileId}/dependencies` | Lists all files that this file depends on. |
| `GET /code/files/{fileId}/dependents` | Lists all files that depend on this file. |

---

#### **`POST /code/files/{fileId}/dependencies`**
*   **Description:** Creates a dependency link from the file specified in the path to the file specified in the body.
*   **Request Body:**
    ```json
    {
      "target_file_id": "uuid"
    }
    ```
*   **Success Response:** `201 Created`
    ```json
    {
        "source_file_id": "uuid",
        "target_file_id": "uuid"
    }
    ```

---

## **Guides & Implementation Memory API**

Endpoints for managing source documents, knowledge chunks, and synthesized guides. This includes semantic search capabilities.

### **3.1. Source Documents & Chunks**

| Endpoint | Description |
| :--- | :--- |
| `POST /guides/sources` | Creates a new source document record. |
| `GET /guides/sources` | Lists all source documents. |
| `GET /guides/sources/{sourceId}` | Retrieves a single source document. |
| `POST /guides/sources/{sourceId}/ingest` | Ingests and chunks a document, creating `document_chunks` and embedding them in ChromaDB. |
| `GET /guides/chunks/{chunkId}` | Retrieves a specific document chunk. |

---

#### **`POST /guides/sources/{sourceId}/ingest`**
*   **Description:** A high-level action that fetches content from the `source_url`, splits it into manageable chunks, creates corresponding `document_chunks` records in PostgreSQL, and generates/stores their vector embeddings in the `guides_and_chunks_collection` in ChromaDB.
*   **Request Body:** (Empty)
*   **Success Response:** `202 Accepted`
    ```json
    {
      "status": "Ingestion process started.",
      "source_document_id": "uuid",
      "job_id": "string"
    }
    ```

---

### **3.2. Synthesized Guides**

**Resource URL:** `/guides/synthesized`

| Endpoint | Description |
| :--- | :--- |
| `POST /guides/synthesized` | Creates a new synthesized guide from document chunks. |
| `GET /guides/synthesized` | Lists all synthesized guides. |
| `GET /guides/synthesized/{guideId}` | Retrieves a single guide and its source chunks. |
| `PUT /guides/synthesized/{guideId}` | Updates a synthesized guide. |
| `DELETE /guides/synthesized/{guideId}` | Deletes a synthesized guide. |

---

#### **`POST /guides/synthesized`**
*   **Description:** Creates a new guide. This single transaction creates the `synthesized_guides` record, its ChromaDB vector embedding, and the `guide_chunk_map` associations.
*   **Request Body:**
    ```json
    {
      "task_id": "uuid, optional",
      "title": "string",
      "content": "string, the synthesized actionable guide",
      "source_chunk_ids": ["uuid", "uuid", ...]
    }
    ```
*   **Success Response:** `201 Created`
    ```json
    {
      "id": "uuid",
      "task_id": "uuid or null",
      "title": "string",
      "content": "string",
      "created_at": "timestamp with timezone",
      "updated_at": "timestamp with timezone",
      "source_chunks": [
        {
            "id": "uuid",
            "source_document_id": "uuid",
            "metadata": {}
        }
      ]
    }
    ```

---

### **3.3. Semantic Search**

#### **`GET /guides/search`**
*   **Description:** Performs a semantic search across both raw document chunks and synthesized guides in ChromaDB.
*   **Query Parameters:**
    | Parameter | Type | Description |
    | :--- | :--- | :--- |
    | `q` | string | **Required.** The natural language query string. |
    | `type` | string | Optional. Filter by `'chunk'` or `'guide'`. |
    | `limit` | integer | Optional. Number of results to return. Defaults to 10. |
    | `task_id`| string (uuid) | Optional. Filter guides associated with a specific task. |
*   **Success Response:** `200 OK`
    ```json
    {
      "results": [
        {
          "score": 0.987,
          "type": "guide",
          "data": {
            "id": "uuid",
            "title": "How to implement OAuth 2.0 flow",
            "content_preview": "First, redirect the user to the authorization server...",
            "task_id": "uuid"
          }
        },
        {
          "score": 0.954,
          "type": "chunk",
          "data": {
            "id": "uuid",
            "chunk_text": "The client_id is a public identifier for apps...",
            "source_document_id": "uuid",
            "metadata": { "page": 42 }
          }
        }
      ]
    }
    ```

---

## **Task Memory API**

Endpoints for managing grand plans, hierarchical tasks, and build conflicts.

### **4.1. Grand Plans & Tasks**

| Endpoint | Description |
| :--- | :--- |
| `POST /tasks/plans` | Creates a new grand plan. |
| `GET /tasks/plans` | Lists all grand plans. |
| `GET /tasks/plans/{planId}` | Retrieves a grand plan and its top-level tasks. |
| `POST /tasks` | Creates a new task, possibly as a sub-task. |
| `GET /tasks` | Lists tasks with filtering and sorting. |
| `GET /tasks/{taskId}` | Retrieves a single task, including its sub-tasks and dependencies. |
| `PATCH /tasks/{taskId}` | Partially updates a task (e.g., changing its status or priority). |
| `DELETE /tasks/{taskId}` | Deletes a task. |

---

#### **`GET /tasks`**
*   **Description:** Retrieves a list of tasks with powerful filtering.
*   **Query Parameters:**
    | Parameter | Type | Description |
    | :--- | :--- | :--- |
    | `grand_plan_id` | string (uuid) | Filter by a specific plan. |
    | `parent_task_id`| string (uuid) | Get direct children of a task. |
    | `status` | string | Filter by status (`pending`, `in_progress`, etc.). |
    | `classification`| string | Filter by feature classification. |
    | `priority` | integer | Filter by priority level. |
*   **Success Response:** `200 OK`
    ```json
    {
      "pagination": { /* ... */ },
      "data": [
        {
          "id": "uuid",
          "grand_plan_id": "uuid",
          "parent_task_id": "uuid or null",
          "title": "Setup user authentication module",
          "description": "...",
          "status": "in_progress",
          "priority": 1,
          "feature_classification": "backend"
        }
      ]
    }
    ```

---

### **4.2. Task Relations & Conflicts**

| Endpoint | Description |
| :--- | :--- |
| `POST /tasks/{taskId}/dependencies` | Defines a dependency where the current task depends on another. |
| `GET /tasks/{taskId}/dependencies` | Lists tasks that `{taskId}` depends on. |
| `POST /tasks/{taskId}/associations/code` | Associates a task with a code file. |
| `GET /tasks/{taskId}/associations/code` | Lists code files associated with a task. |
| `POST /tasks/{taskId}/conflicts` | Logs a new build conflict related to a task. |
| `GET /conflicts` | Lists all build conflicts, filterable by `is_resolved` or `task_id`. |

---

## **Dependency Memory API**

Endpoints for managing external project dependencies and their documentation.

### **5.1. Project Dependencies (PostgreSQL)**

**Resource URL:** `/dependencies`

| Endpoint | Description |
| :--- | :--- |
| `POST /dependencies` | Adds a new project dependency to the catalog. |
| `GET /dependencies` | Lists all tracked project dependencies. |
| `GET /dependencies/{dependencyId}` | Retrieves a specific project dependency. |
| `POST /dependencies/{dependencyId}/ingest-docs` | Triggers ingestion of the dependency's documentation into ChromaDB. |

---

#### **`POST /dependencies`**
*   **Description:** Registers a new external library or framework.
*   **Request Body:**
    ```json
    {
      "name": "string",
      "version": "string",
      "manager": "string, one of ['npm', 'pip', 'maven', 'go', 'cargo', 'other']",
      "documentation_url": "string, optional"
    }
    ```
*   **Success Response:** `201 Created`
    ```json
    {
      "id": "uuid",
      "name": "string",
      "version": "string",
      "manager": "string",
      "documentation_url": "string or null",
      "created_at": "timestamp with timezone"
    }
    ```
---

### **5.2. Dependency Documentation Search (ChromaDB)**

#### **`GET /dependencies/docs/search`**
*   **Description:** Performs a semantic search on the ingested documentation for all dependencies.
*   **Query Parameters:**
    | Parameter | Type | Description |
    | :--- | :--- | :--- |
    | `q` | string | **Required.** The natural language query string. |
    | `dependency_id` | string (uuid)| Optional. Scope search to a specific dependency. |
    | `feature_relation`| string | Optional. Find docs related to a feature like `user-authentication`. |
    | `limit` | integer | Optional. Number of results to return. Defaults to 10. |
*   **Success Response:** `200 OK`
    ```json
    {
      "results": [
        {
          "score": 0.975,
          "dependency_name": "react-router-dom",
          "dependency_id": "uuid",
          "feature_relation": "routing",
          "source_section": "Hooks API: useLoaderData",
          "text_preview": "The useLoaderData hook provides the value returned from your route loader..."
        }
      ]
    }
    ```