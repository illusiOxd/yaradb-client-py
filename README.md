# 📦 YaraDB

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/illusiOxd/yaradb)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg?logo=docker)](https://hub.docker.com/)

**YaraDB is an intelligent, in-memory-first Document Database with crash-safe WAL persistence and schema enforcement, built on FastAPI.**

It bridges the gap between the flexibility of NoSQL and the reliability of schema-enforced databases, providing modern data integrity guarantees like **Optimistic Concurrency Control (OCC)**, **unique constraints**, and **atomic transactions** right out of the box.

---

## ⚡ Core Features (v3.0)

YaraDB v3.0 introduces **Structured Tables** and powerful data validation mechanisms while maintaining blazing-fast in-memory performance.

* **🗂️ Structured Table Management:** Organize documents into logical tables with configurable modes:
  * **Free Mode** (Default): Schemaless, on-the-fly table creation for rapid prototyping
  * **Strict Mode**: Enforce JSON Schema validation on all write operations
  * **Read-Only Mode**: Archive historical data with write protection

* **🛡️ Crash-Safe Persistence (WAL):** All write operations are logged to a **Write-Ahead Log** before being applied to memory. The database state is fully recoverable on restart, with table metadata and schemas preserved.

* **🔒 Unique Constraints:** Enforce field-level uniqueness (e.g., email addresses, usernames) atomically during create and update operations. Violations return immediate errors.

* **🔄 Optimistic Concurrency Control (OCC):** Every document has a `version` field. Updates require version matching to prevent "lost update" race conditions. Mismatches return `409 Conflict`.

* **🔐 Data Integrity:** Automatic `body_hash` generation for every document, allowing you to verify data hasn't been corrupted.

* **🗑️ Soft Deletes:** Archive documents instead of destroying them, preserving data history for recovery or auditing.

* **🚀 Fast In-Memory Indexing:** O(1) read performance with UUID-based document indexing.

---

## 🚀 Quick Start (Docker)

The easiest way to run YaraDB v3.0 as a persistent service.

### Option 1: Docker Compose

**Save the `docker-compose.yml` file:**
```yaml
version: '3.8'

services:
  yaradb:
    image: ghcr.io/illusioxd/yaradb:v3
    container_name: yaradb_server
    ports:
      - "8000:8000"
    volumes:
      - ./yaradb_data:/data
    environment:
      - DATA_DIR=/data
    restart: always

volumes:
  yaradb_data:
```

**Run the service:**
```bash
docker-compose up -d
```

### Option 2: Docker Run

```bash
docker run -d -p 8000:8000 \
  -v $(pwd)/yaradb_data:/data \
  -e DATA_DIR=/data \
  --name yaradb_server \
  ghcr.io/illusioxd/yaradb:v3
```

The server is now running on **http://127.0.0.1:8000**. Your database files will be safely stored in the `yaradb_data` folder.

---

## 🐍 Python Client

Install the official Python client:
```bash
pip install yaradb-client
```

### Basic Usage (v3.0)

```python
from yaradb_client import YaraClient, YaraConflictError, YaraBadRequestError

client = YaraClient()

if not client.ping():
    print("Server is offline!")
    exit()

# 1. Create a strict table with schema and unique constraints
client.create_table(
    name="users",
    mode="strict",
    unique_fields=["email"],
    schema={
        "type": "object",
        "required": ["email", "age", "username"],
        "properties": {
            "email": {"type": "string"},
            "age": {"type": "integer"},
            "username": {"type": "string"}
        }
    }
)

# 2. Create a valid document
doc = client.create(
    table_name="users",
    name="alice_user",
    body={
        "username": "alice",
        "email": "alice@example.com",
        "age": 25
    }
)
doc_id = doc["_id"]
doc_version = doc["version"]

# 3. Try to create a duplicate (this will fail due to unique constraint)
try:
    client.create(
        table_name="users",
        name="bob_user",
        body={
            "username": "bob",
            "email": "alice@example.com",  # Same email!
            "age": 30
        }
    )
except YaraBadRequestError as e:
    print(f"Expected error: {e}")  # Unique constraint violation

# 4. Update with version control
updated_doc = client.update(
    doc_id=doc_id,
    version=doc_version,
    body={
        "username": "alice_updated",
        "email": "alice@example.com",
        "age": 26
    }
)

# 5. Try to update with old version (this will fail)
try:
    client.update(
        doc_id=doc_id,
        version=doc_version,  # Old version
        body={
            "username": "alice_wrong",
            "email": "alice@example.com",
            "age": 27
        }
    )
except YaraConflictError as e:
    print(f"Expected conflict: {e}")
```

### Table Management

```python
# List all tables
tables = client.list_tables()
print(tables)

# Get table details
table_info = client.get_table("users")
print(f"Mode: {table_info['mode']}, Documents: {table_info['documents_count']}")

# Get all documents in a table
docs = client.get_table_documents("users")

# Delete a table
client.delete_table("users")
```

---

## 📖 API Reference

### Table Operations (New in v3.0)

#### POST /table/create

Creates a new table with specific configuration.

**Request Body:**
```json
{
  "name": "users",
  "mode": "strict",
  "read_only": false,
  "unique_fields": ["email"],
  "schema_definition": {
    "type": "object",
    "required": ["email", "age"],
    "properties": {
      "email": {"type": "string"},
      "age": {"type": "integer"}
    }
  }
}
```

**Response (200 OK):**
```json
{
  "name": "users",
  "mode": "strict",
  "read_only": false,
  "unique_fields": ["email"],
  "schema_definition": {...},
  "created_at": "2025-11-23T12:00:00Z",
  "documents_count": 0
}
```

#### GET /table/list

Returns a list of all tables.

#### GET /table/{name}

Retrieves table metadata and statistics.

#### DELETE /table/{name}

Deletes a table and all its documents.

#### GET /table/{name}/documents

Returns all documents in a specific table.

---

### Document Operations

#### POST /document/create

Creates a new document in a specified table.

**Request Body (v3.0 - table_name is now mandatory):**
```json
{
  "table_name": "users",
  "name": "user_account",
  "body": {
    "username": "alice",
    "email": "alice@example.com",
    "age": 25
  }
}
```

**Response (200 OK):**
```json
{
  "_id": "a1b2c3d4-...",
  "name": "user_account",
  "table_name": "users",
  "body": {
    "username": "alice",
    "email": "alice@example.com",
    "age": 25
  },
  "body_hash": "a9f8b...",
  "created_at": "2025-11-23T12:00:00Z",
  "updated_at": null,
  "version": 1,
  "archived_at": null
}
```

**Error (400 Bad Request) - Schema Validation:**
```json
{
  "detail": "Schema validation failed: 'age' is a required property"
}
```

**Error (400 Bad Request) - Unique Constraint:**
```json
{
  "detail": "Unique constraint violation on field 'email'"
}
```

#### GET /document/get/{doc_id}

Retrieves a single document by ID (O(1) lookup).

#### PUT /document/update/{doc_id}

Updates a document with optimistic concurrency control.

**Request Body:**
```json
{
  "version": 1,
  "body": {
    "username": "alice_updated",
    "email": "alice@example.com",
    "age": 26
  }
}
```

**Response (409 Conflict) - Version Mismatch:**
```json
{
  "detail": "Conflict: Document version mismatch. DB is at 2, you sent 1"
}
```

#### POST /document/find

Finds documents using a filter on body fields.

**Request Body:**
```json
{
  "username": "alice_updated"
}
```

**Query Parameters:**
- `include_archived` (bool): Include archived documents in results

#### PUT /document/archive/{doc_id}

Performs a soft delete on a document.

#### POST /document/combine

Combines multiple documents into a single new document.

**Request Body:**
```json
{
  "name": "combined_doc",
  "document_ids": ["doc-id-1", "doc-id-2"],
  "merge_strategy": "overwrite"
}
```

---

### System Operations

#### DELETE /system/self-destruct

**⚠️ DANGER: Wipes all data from the database. USE WITH EXTREME CAUTION.**

**Request Body:**
```json
{
  "verification_phrase": "BDaray",
  "safety_pin": 2026,
  "confirm": true
}
```

---

## 🔄 Migration from v2.x to v3.0

### Breaking Changes

1. **Mandatory table_name in document creation:**
   ```python
   # OLD (v2.x)
   client.create(name="doc1", body={"val": 1})
   
   # NEW (v3.0)
   client.create(table_name="default", name="doc1", body={"val": 1})
   ```

2. **Storage format change:**
   - Recommended: Delete existing `yaradb_storage.json` and `yaradb_wal` files
   - The database will automatically migrate to the new format

### Updated Python Client

Update to the latest client version:
```bash
pip install --upgrade yaradb-client
```

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI**: Modern, high-performance API framework
- **Pydantic**: Data modeling and validation
- **Uvicorn**: ASGI server
- **Docker**: Containerization and deployment

---

## 🎯 Use Cases

- **Rapid Prototyping**: Start schemaless, enforce structure later
- **Configuration Management**: Store validated config with unique keys
- **User Management**: Enforce unique emails/usernames with schema validation
- **Audit Logs**: Write-once tables with read-only mode
- **Session Storage**: Fast in-memory lookups with persistence

---

## 🤝 Contributing

Contributions are welcome! Please read our CONTRIBUTING.md to understand the process and our Contributor License Agreement (CLA).

Feel free to open issues for bugs, feature requests, or questions.

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **GitHub Repository**: [github.com/illusiOxd/yaradb](https://github.com/illusiOxd/yaradb)
- **Python Client**: [github.com/illusiOxd/yaradb-client-py](https://github.com/illusiOxd/yaradb-client-py)
- **Docker Hub**: Coming soon
- **Documentation**: Coming soon

---

**Made with ❤️ by [Tymofii Shchur](https://github.com/illusiOxd)**