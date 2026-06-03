# LokiJS

> **Category:** Document | **License:** MIT | **Stars:** ~6,800

## Overview

LokiJS is an in-memory, document-oriented JavaScript database with a MongoDB-like API. It stores collections of plain JavaScript objects and provides fast in-memory queries, built-in indexing, and optional persistence adapters for syncing to disk. Its DynamicView feature maintains sorted query result sets that update automatically as documents change, making it great for reactive UIs and live data displays. LokiJS runs in Node.js and browsers with zero dependencies.

## Quick Start

### JavaScript

```js
// Install: npm install lokijs
const loki = require('lokijs')

// Create (or load) a database with persistence adapter
const db = new loki('myapp.db', {
  adapter: new loki.LokiFsAdapter(),
  autoload: true,
  autoloadCallback: databaseInitialize,
  autosave: true,
  autosaveInterval: 4000
})

function databaseInitialize() {
  // Add a collection
  const users = db.addCollection('users', { indices: ['name', 'age'] })

  // Insert documents
  users.insert([
    { name: 'Alice', age: 30, city: 'London' },
    { name: 'Bob', age: 25, city: 'Paris' },
    { name: 'Charlie', age: 35, city: 'London' }
  ])

  // Find with conditions (MongoDB-like)
  const londoners = users.find({ city: 'London' })
  console.log(londoners) // [{name:'Alice',...},{name:'Charlie',...}]

  // Find with filters
  const young = users.where(u => u.age < 30)
  console.log(young) // [{name:'Bob',...}]

  // Chain operations
  const bob = users.chain().find({ name: 'Bob' }).data()
  console.log(bob) // [{name:'Bob',...}]

  // Update a document
  users.findAndUpdate({ name: 'Alice' }, doc => { doc.age = 31 })

  // Remove documents
  users.findAndRemove({ name: 'Charlie' })

  console.log(`Final count: ${users.count()}`) // 2
}
```

## On-Disk Format

In-Memory with optional persistence via JSON file, IndexedDB, WebSQL, or localStorage adapters

## Core Strengths

- MongoDB-like API for document queries with simple find, insert, update, remove
- DynamicView for persistent live query result sets with sorted indexes
- Zero dependencies with single-file embeddable builds for Node.js and browsers
- Optional persistence adapters (IndexedDB, WebSQL, localStorage, JSON file)
- Built-in indexing with compound indexes for fast document lookups
- Small footprint suitable for mobile apps, Electron apps, and SPAs

## Best Use Cases

1. **Client-Side Document Storage** -- Store structured documents in Single-Page Applications and PWAs with an intuitive MongoDB-like API.
2. **Electron and Desktop Apps** -- Embed LokiJS directly in Electron or Node.js desktop applications for fast local document storage with no external database process.
3. **Mobile App Local Storage** -- Use browser-based persistence adapters (IndexedDB, WebSQL) for mobile web and hybrid app data storage.
4. **Prototyping** -- Quick development with a familiar query pattern when the data model is document-shaped and schemaless iteration is needed.
5. **Offline-First Apps** -- Keep the working dataset in-memory for instant reads and periodically flush to a persistence adapter.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| JavaScript | [`recipe_document_store.js`](javascript/src/recipe_document_store.js) | CRUD operations, find, where, chain, DynamicView |

## Limitations & Caveats

- Entire database is held in memory; not suitable for datasets larger than available RAM
- Project is archived (abandoned in 2022) -- no further updates or bug fixes
- Official documentation is no longer available; the site redirects to RxDB
- Persistence adapters must be explicitly wired; in-memory-only is the default
- No built-in encryption, replication, or multi-process concurrency support
- For new projects, consider RxDB as the actively-maintained spiritual successor

## Further Reading

- [Source Repository](https://github.com/techfort/LokiJS)
- [DB-Engines: LokiJS](https://dbdb.io/db/lokijs)
