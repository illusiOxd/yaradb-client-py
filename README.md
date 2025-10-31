# 📦 YaraDB

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/illusiOxd/yaradb)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg?logo=docker)](https://hub.docker.com/)

**YaraDB is an intelligent, in-memory-first Document DB with crash-safe WAL persistence, built on FastAPI.**

It's designed for projects that need the flexibility of a NoSQL document store but require modern data integrity guarantees like **Optimistic Concurrency Control (OCC)** and **atomic transactions** right out of the box.

---

## ⚡ Core Features (v2.0)

YaraDB isn't just another key-value store. It's a "smart" database that provides critical features at the document level.

* **🛡️ Crash-Safe Persistence (WAL):** All write operations (`create`, `update`, `archive`) are first written to a **Write-Ahead Log (WAL)** before being applied to memory. This guarantees that no data is lost even if the server crashes. The database state is recovered from the WAL on restart.

* **🔄 Optimistic Concurrency Control (OCC):** Every document has a `version` field. The update endpoint requires this version, preventing "lost update" race conditions. If versions mismatch, the API returns a `409 Conflict`.

* **🔐 Data Integrity:** Every document's `body` is automatically hashed into a `body_hash` field. This allows you to verify that data hasn't been corrupted.

* **🗑️ Soft Deletes:** Deleting a document (via `archive`) doesn't destroy it. It just sets an `archived_at` flag, preserving data history for recovery or auditing.

* **⛓️ Atomic Transactions:** (Coming Soon) Batch multiple update/archive operations into a single request. The server will validate all operations first, ensuring the transaction is "all-or-nothing".

* **🚀 Fast In-Memory Indexing:** All documents are indexed in memory by their `_id` (a UUID) for O(1) read performance.

---

## 🚀 Quick Start (Docker Compose)

This is the easiest and recommended way to run YaraDB as a persistent service.

1.  **Save the `docker-compose.yml` file:**
```yaml
    version: '3.8'

    services:
      yaradb:
        image: ghcr.io/illusioxd/yaradb:latest  # (Use the official image once published)
        # build: .  # (Or build locally if you cloned the repo)
        container_name: yaradb_server
        ports:
          - "8000:8000"
        volumes:
          - ./yaradb_data:/app # Mounts a local folder for persistence
        restart: always

    volumes:
      yaradb_data:
```
    *(Note: You'll need to publish your image to `ghcr.io` or Docker Hub for the `image:` tag to work)*

2.  **Run the service:**
```bash
    docker-compose up -d
```

The server is now running on **http://127.0.0.1:8000**. Your database files (snapshot and WAL) will be safely stored in a `yaradb_data` folder in your current directory.

---

## 🐍 Python Client

While you can use any HTTP client, the easiest way to interact with YaraDB from Python is with the official `pip` package.
```bash
pip install yaradb-client
```
```python
from yaradb_client import YaraClient, YaraConflictError

client = YaraClient()

if not client.ping():
    print("Server is offline!")
    exit()
    
# 1. Create a document
doc = client.create(
    name="user", 
    body={"username": "alice", "level": 10}
)
doc_id = doc["_id"]
doc_version = doc["version"]

# 2. Update it (this will work)
updated_doc = client.update(
    doc_id=doc_id,
    version=doc_version,
    body={"username": "alice", "level": 11}
)

# 3. Try to update again with the *old* version (this will fail)
try:
    client.update(
        doc_id=doc_id,
        version=doc_version, # Sending version 1, but DB is at 2
        body={"username": "alice", "level": 12}
    )
except YaraConflictError as e:
    print(f"Success! Caught expected error: {e}")
```

---

## 📖 API Reference

### POST /document/create

Creates a new document.

**Request Body:**
```json
{
  "name": "user_account",
  "body": {
    "username": "alice",
    "email": "alice@example.com"
  }
}
```

**Response (200 OK):** The full StandardDocument object.
```json
{
  "_id": "a1b2c3d4-...",
  "name": "user_account",
  "body": { "username": "alice", "email": "alice@example.com" },
  "body_hash": "a9f8b...",
  "created_at": "2025-10-31T12:00:00Z",
  "updated_at": null,
  "version": 1,
  "archived_at": null
}
```

### GET /document/get/{doc_id}

Retrieves a single document by its ID (fast, O(1) read).

**Response (200 OK):** The StandardDocument object.

**Response (404 Not Found):** If the document does not exist or has been archived.
```json
{
  "detail": "Document not found"
}
```

### PUT /document/update/{doc_id}

Updates a document only if the provided version matches the one in the database.

**Request Body:**
```json
{
  "version": 1, 
  "body": {
    "username": "alice_updated",
    "email": "alice@example.com"
  }
}
```

**Response (200 OK):** The updated StandardDocument with version incremented.

**Response (409 Conflict):** If the provided version does not match the database.
```json
{
  "detail": "Conflict: Document version mismatch. DB is at 2, you sent 1"
}
```

### POST /document/find

Finds documents using a filter on the body fields.

**Request Body:**
```json
{
  "username": "alice_updated"
}
```

**Query Params:**

- `include_archived` (bool, optional): Set to true to include archived documents in the search.

**Response (200 OK):** A list of matching StandardDocument objects.
```json
[
  { ...StandardDocument... }
]
```

### PUT /document/archive/{doc_id}

Performs a "soft delete" on a document by setting its `archived_at` timestamp.

**Response (200 OK):** The archived StandardDocument object.

**Response (400 Bad Request):** If the document is already archived.
```json
{
  "detail": "Document already archived"
}
```

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI**: For the modern, high-performance API
- **Pydantic**: For data modeling and validation (StandardDocument)
- **Uvicorn**: As the ASGI server
- **Docker**: For containerization and easy deployment

---

## 🤝 Contributing

Contributions are welcome! Please read our CONTRIBUTING.md to understand the process and our Contributor License Agreement (CLA).

Feel free to open issues for bugs, feature requests, or questions.

---

## 📝 License

This project is licensed under the MIT License. See the file for details.