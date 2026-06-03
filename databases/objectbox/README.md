# ObjectBox

> **Category:** Vector | **License:** Apache-2.0 | **Stars:** ~4.6k

## Overview

ObjectBox is a high-performance on-device database for objects and vectors, purpose-built for mobile, edge, and IoT applications. It uses FlatBuffers for zero-copy serialization and stores data in a single file with ACID transactions. ObjectBox supports vector similarity search for on-device AI workloads alongside traditional object persistence with relations, type-safe queries, and automatic schema migrations. It is available across C/C++, Go, Java/Kotlin, Swift, Dart/Flutter, and Python, running fully embedded with no server required.

## Quick Start

### Python

```python
# Install: pip install objectbox
from objectbox import Entity, Id, Store, String

@Entity()
class Person:
    id = Id
    name = String

store = Store()

# Get a box for the Person entity
box = store.box(Person)

# CRUD operations
person = Person(name="Joe Green")
id = box.put(person)          # Create
person = box.get(id)          # Read
person.name = "Joe Black"
box.put(person)               # Update
box.remove(person)            # Delete
```

### Go

```go
// Install: bash <(curl -s https://raw.githubusercontent.com/objectbox/objectbox-go/main/install.sh)
package main

import (
    "fmt"
    "github.com/objectbox/objectbox-go/objectbox"
)

//go:generate go run github.com/objectbox/objectbox-go/cmd/objectbox-gogen

type Task struct {
    Id   uint64 `objectbox:"id"`
    Text string
}

func main() {
    ob := objectbox.NewBuilder().Model(ObjectBoxModel()).Build()
    defer ob.Close()

    box := BoxForTask(ob)
    id, _ := box.Put(&Task{Text: "Buy milk"})
    task, _ := box.Get(id)
    fmt.Printf("Task: %s\n", task.Text)
}
```

## On-Disk Format

FlatBuffers-based (single file)

## Core Strengths

- On-device vector search for local AI, RAG, and semantic similarity
- FlatBuffers-based zero-copy serialization with no parsing overhead
- ACID transactions with automatic schema migrations and no manual scripts
- Embedded-only with no server required, runs in-process on constrained devices
- Multi-platform: Android, iOS, Linux, macOS, Windows, and embedded ARM
- Object persistence with built-in relations, indexes, and type-safe queries

## Best Use Cases

1. **On-Device AI** -- Run vector similarity search and RAG pipelines locally on mobile, desktop, or edge devices.
2. **Mobile & IoT Apps** -- Fast local storage with minimal CPU, memory, and power footprint for constrained devices.
3. **Offline-First** -- Reliable local persistence with optional ObjectBox Sync for multi-device data coordination.
4. **High-Performance Object Storage** -- Replace SQLite when you need 10x faster CRUD with native object mapping.
5. **Edge Computing** -- Deploy on ARM-based gateways and embedded Linux for local data processing.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_vector_search.py`](python/src/recipe_vector_search.py) | Define entities with embeddings, insert objects, perform vector similarity search |
| Go | [`recipe_vector_search`](go/cmd/recipe_vector_search/main.go) | Create store, persist objects with vector properties, run vector queries |

## Limitations & Caveats

- ObjectBox is a multi-repo project; vector search API availability varies by language binding (first-class in Python, C/C++, Java/Kotlin, Swift; object-focused in Go).
- Go and Dart/Flutter require a code generation step (`go generate` / `build_runner`) for entity bindings.
- Python vector search is in alpha (v4.0.0); API surface may change in future releases.
- The native C/C++ library must be installed for all language bindings. Python and Java bundle it automatically; Go requires running the install script.
- ObjectBox Sync is a commercial add-on for multi-device synchronization.

## Further Reading

- [Official Documentation](https://docs.objectbox.io)
- [ObjectBox Java/Kotlin (Main Repo)](https://github.com/objectbox/objectbox-java)
- [ObjectBox Go Repository](https://github.com/objectbox/objectbox-go)
- [ObjectBox Python Repository](https://github.com/objectbox/objectbox-python)
- [Go Package Documentation](https://pkg.go.dev/github.com/objectbox/objectbox-go/objectbox)
- [On-Device Vector Search Docs](https://docs.objectbox.io/on-device-vector-search)
