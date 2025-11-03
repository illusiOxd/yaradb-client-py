# 🐍 YaraDB Python Client

> Official Python client for YaraDB - the intelligent in-memory Document Database

[![PyPI version](https://badge.fury.io/py/yaradb-client.svg)](https://pypi.org/project/yaradb-client/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[📖 **Full Documentation**](https://github.com/illusiOxd/yaradb-client-py/wiki) | 
[🚀 YaraDB Server](https://github.com/illusiOxd/yaradb)

---

## 📦 Installation

```bash
pip install yaradb-client
```

---

## 🚀 Quick Start

### 1. Start YaraDB Server

**Linux / macOS:**
```bash
docker run -d -p 8000:8000 \
  -v $(pwd)/yaradb_data:/data \
  -e DATA_DIR=/data \
  --name yaradb_server \
  ashfromsky/yaradb:latest
```

**Windows (PowerShell):**
```powershell
docker run -d -p 8000:8000 -v ${PWD}/yaradb_data:/data -e DATA_DIR=/data --name yaradb_server ashfromsky/yaradb:latest
```

**Windows (CMD):**
```cmd
docker run -d -p 8000:8000 -v %cd%/yaradb_data:/data -e DATA_DIR=/data --name yaradb_server ashfromsky/yaradb:latest
```

### 2. Use the Python Client

```python
from yaradb_client import YaraClient

# Connect to server
client = YaraClient("http://localhost:8000")

# Check connection
if not client.ping():
    print("Server is offline!")
    exit()

# Create a document
doc = client.create(
    name="user_account",
    body={
        "username": "alice",
        "email": "alice@example.com",
        "level": 1
    }
)

print(f"Created document: {doc['_id']}")
print(f"Version: {doc['version']}")

# Get document
doc = client.get(doc["_id"])
print(f"Username: {doc['body']['username']}")

# Update document (with optimistic locking)
updated = client.update(
    doc_id=doc["_id"],
    version=doc["version"],  # Must match current version
    body={
        "username": "alice",
        "email": "alice@example.com",
        "level": 2  # Leveled up!
    }
)

# Find documents
users = client.find({"level": 2})
print(f"Found {len(users)} level 2 users")

# Archive (soft delete)
archived = client.archive(doc["_id"])
print(f"Archived at: {archived['archived_at']}")
```

---

## ✨ Features

- 🔄 **Full CRUD Operations** - Create, Read, Update, Archive
- 🔒 **Optimistic Locking** - Version-based conflict detection
- 🔍 **Flexible Search** - Filter documents by any field
- 🗑️ **Soft Deletes** - Archive without data loss
- 🎯 **Type Hints** - Full IDE autocomplete support
- 🐍 **Pythonic API** - Clean and intuitive interface
- ⚡ **Fast** - Direct HTTP communication with YaraDB

---

## 📖 API Reference

### Client Initialization

```python
from yaradb_client import YaraClient

client = YaraClient(base_url="http://localhost:8000")
```

### Methods

#### `ping() -> bool`
Check if server is alive.

```python
if client.ping():
    print("Server is online!")
```

#### `create(name: str, body: dict) -> dict`
Create a new document.

```python
doc = client.create(
    name="user",
    body={"username": "bob", "age": 25}
)
```

#### `get(doc_id: str) -> dict | None`
Get document by ID.

```python
doc = client.get("550e8400-e29b-41d4-a716-446655440000")
```

#### `find(filter_body: dict, include_archived: bool = False) -> list[dict]`
Search documents.

```python
# Find all users aged 25
users = client.find({"age": 25})

# Include archived documents
all_users = client.find({"username": "bob"}, include_archived=True)
```

#### `update(doc_id: str, version: int, body: dict) -> dict`
Update document with optimistic locking.

```python
updated = client.update(
    doc_id=doc["_id"],
    version=doc["version"],  # Must match!
    body={"username": "bob", "age": 26}
)
```

#### `archive(doc_id: str) -> dict`
Archive (soft delete) document.

```python
archived = client.archive(doc["_id"])
```

---

## 🛡️ Error Handling

```python
from yaradb_client import YaraClient, YaraDBError, ConflictError

client = YaraClient("http://localhost:8000")

try:
    # Try to update with wrong version
    client.update(
        doc_id="some-id",
        version=1,  # But server has version 5
        body={"data": "new"}
    )
except ConflictError as e:
    print(f"Version conflict: {e}")
except YaraDBError as e:
    print(f"Database error: {e}")
```

---

## 🔥 Advanced Usage

### Batch Operations

```python
# Create multiple documents
users = [
    {"username": "alice", "level": 1},
    {"username": "bob", "level": 2},
    {"username": "charlie", "level": 3}
]

for user_data in users:
    client.create(name="user", body=user_data)

# Find all level > 1
high_level_users = [
    doc for doc in client.find({})
    if doc["body"].get("level", 0) > 1
]
```

### Optimistic Concurrency Pattern

```python
def safe_increment_counter(client, doc_id):
    """Safely increment a counter with retry logic"""
    max_retries = 5
    
    for attempt in range(max_retries):
        # Get current state
        doc = client.get(doc_id)
        if not doc:
            raise ValueError("Document not found")
        
        # Increment counter
        new_body = doc["body"].copy()
        new_body["counter"] = new_body.get("counter", 0) + 1
        
        try:
            # Try to update
            return client.update(
                doc_id=doc_id,
                version=doc["version"],
                body=new_body
            )
        except ConflictError:
            # Someone else updated, retry
            if attempt == max_retries - 1:
                raise
            continue
```

---

## 🧪 Testing

```python
import pytest
from yaradb_client import YaraClient

@pytest.fixture
def client():
    return YaraClient("http://localhost:8000")

def test_create_and_get(client):
    # Create
    doc = client.create(name="test", body={"value": 42})
    
    # Get
    retrieved = client.get(doc["_id"])
    assert retrieved["body"]["value"] == 42
    
    # Archive
    client.archive(doc["_id"])
    
    # Should not find archived
    assert client.get(doc["_id"]) is None
```

---

## 🌐 Multi-Platform Support

This client works on:
- ✅ Linux
- ✅ macOS  
- ✅ Windows
- ✅ Docker containers
- ✅ CI/CD pipelines

---

## 📚 Resources

- [YaraDB Server GitHub](https://github.com/illusiOxd/yaradb)
- [YaraDB Documentation](https://github.com/illusiOxd/yaradb/wiki)
- [Docker Hub](https://hub.docker.com/r/ashfromsky/yaradb)
- [Report Issues](https://github.com/illusiOxd/yaradb-client-py/issues)

---

## 🤝 Contributing

Contributions welcome! Please read the [Contributing Guide](CONTRIBUTING.md).

---

## 📄 License

MIT © 2025 Tymofii Shchur Viktorovych

---

## 🔗 Links

- **Client Repository:** https://github.com/illusiOxd/yaradb-client-py
- **Server Repository:** https://github.com/illusiOxd/yaradb
- **PyPI Package:** https://pypi.org/project/yaradb-client/
