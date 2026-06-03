# LowDB

> **Category:** Document | **License:** MIT | **Stars:** ~22,500

## Overview

LowDB is a tiny, type-safe local JSON database for Node.js and the browser. Instead of learning a query language, you use plain JavaScript to read and modify a single JSON file. LowDB wraps `JSON.stringify` and `JSON.parse` with a clean async API and atomic writes, making it perfect for small projects, CLI tools, and prototypes where a full database is overkill.

## Quick Start

### JavaScript

```js
// Install: npm install lowdb
import { JSONFilePreset } from 'lowdb/node'

// Read or create db.json with default data
const defaultData = { users: [] }
const db = await JSONFilePreset('db.json', defaultData)

// Write -- just mutate the plain object, then write
db.data.users.push({ id: 1, name: 'Alice', age: 30 })
await db.write()

// Or use update() to mutate and write atomically
await db.update(({ users }) => {
  users.push({ id: 2, name: 'Bob', age: 25 })
})

// Read -- use plain JavaScript Array methods
const { users } = db.data
const adults = users.filter(u => u.age >= 18)
const alice = users.find(u => u.name === 'Alice')
console.log(alice)  // { id: 1, name: 'Alice', age: 30 }
```

## On-Disk Format

Plain Text JSON File (Single File)

## Core Strengths

- Zero query language -- uses plain JavaScript to read and write data
- Single JSON file with atomic writes for data safety
- TypeScript-first with full type inference on your data shape
- Extremely lightweight and minimal -- no dependencies beyond the Node.js standard library
- Extensible via adapters for custom storage, serialization, and encryption
- Works in Node.js, browser (localStorage/sessionStorage), and in-memory for testing

## Best Use Cases

1. **Configuration Storage** -- Store app settings, user preferences, and runtime state in a structured single file that is easy to inspect and edit by hand.
2. **Prototyping** -- Spin up a data layer in seconds without schemas, migrations, or server processes, then swap to a full database when the design stabilizes.
3. **CLI Tools** -- Persist state between invocations of command-line tools with a single JSON file and a three-line setup.
4. **Small Browser Apps** -- Wrap localStorage with LowDB's browser adapters for a cleaner API and optional TypeScript types.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| JavaScript | [`recipe_json_store.js`](javascript/src/recipe_json_store.js) | CRUD operations, filtering, update, and atomic writes |

## Limitations & Caveats

- Loads the entire JSON file into memory; not suitable for datasets larger than 10-100MB
- No query engine or indexing -- all filtering is done via `Array` methods in user code
- Does not support concurrent access from multiple Node.js processes (cluster mode)
- Pure ESM package; may need `"type": "module"` or `.mjs` extension in CommonJS projects
- Every `db.write()` serializes the full object with `JSON.stringify` -- batch writes when possible

## Further Reading

- [Official Documentation](https://github.com/typicode/lowdb)
- [Source Repository](https://github.com/typicode/lowdb)
