# AceBase

> **Category:** Document | **License:** MIT | **Stars:** ~500

## Overview

AceBase is a fast, low-memory, transaction-capable NoSQL document database for Node.js and the browser with realtime data change notifications. Inspired by the Firebase Realtime Database API, it stores JSON-serializable data in a binary storage engine and supports regular, fulltext, geo, and array indexes. Its realtime subscriptions fire events on data changes, making it ideal for reactive UIs and real-time dashboards. AceBase runs embedded without a server, with optional IndexedDB, SQLite, and MSSQL storage backends.

## Quick Start

### JavaScript

```js
// Install: npm install acebase
const { AceBase } = require('acebase')

const db = new AceBase('myapp', { storage: { path: '.' } })

db.ready(async () => {
  // Store data (auto-creates paths)
  await db.ref('users/alice').set({ name: 'Alice', score: 100, city: 'London' })
  await db.ref('users/bob').set({ name: 'Bob', score: 200, city: 'Paris' })
  await db.ref('users/charlie').set({ name: 'Charlie', score: 150, city: 'London' })

  // Read data
  const snap = await db.ref('users/alice').get()
  console.log('Alice:', snap.val()) // { name: 'Alice', score: 100, city: 'London' }

  // Query with filters
  const results = await db.ref('users').query()
    .filter('score', '>=', 100)
    .sort('name')
    .take(10)
    .get()
  results.forEach(s => console.log(s.val().name))

  // Subscribe to realtime changes
  db.ref('users').on('child_added', child => {
    console.log('New user:', child.val())
  })

  // Transactional update
  await db.ref('users/alice/score').transaction(snap => {
    return (snap.val() || 0) + 10
  })
})
```

## On-Disk Format

Binary storage engine with JSON serialization; optional IndexedDB adapter for browsers and SQLite/MSSQL backends

## Core Strengths

- Firebase-compatible API with realtime subscriptions for child and value events
- Built-in regular, fulltext, geo, and array indexes for fast path queries
- Live data proxies for reactive in-memory objects that auto-sync with the DB
- Transactional updates with atomic get-and-set to prevent race conditions
- Pluggable storage: binary engine, IndexedDB (browser), SQLite, MSSQL, or custom
- Schema validation for enforcing data rules with built-in or custom validators
- Multi-process capable with IPC support and client-server synchronization

## Best Use Cases

1. **Real-Time Web Applications** -- Use live data subscriptions to build dashboards, chat apps, and collaborative tools where UI must react instantly to data changes.
2. **Firebase Replacement** -- Adopt a Firebase-compatible API without vendor lock-in or cloud dependency; self-host on your own infrastructure.
3. **Electron and Desktop Apps** -- Embed AceBase directly in Electron or Node.js desktop applications for fast local NoSQL storage with zero external dependencies.
4. **Browser-Based Local Storage** -- Use the IndexedDB adapter to store data entirely in the browser for SPAs, PWAs, and offline-first web apps.
5. **Multi-Device Synchronization** -- Pair with acebase-server for WebSocket-based real-time sync across browsers, mobile clients, and backend services.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| JavaScript | [`recipe_realtime_store.js`](javascript/src/recipe_realtime_store.js) | CRUD, queries, realtime subscriptions, indexes, transactions |

## Limitations & Caveats

- The binary storage engine is optimized for Node.js; browser usage requires the IndexedDB adapter
- Realtime subscriptions and live data proxies work best in single-process or with acebase-server sync middleware
- Fulltext and geo indexes require explicit creation and are not automatically generated from data
- The acebase-server component is a separate package with its own configuration and auth setup
- For large datasets, be mindful of the transaction locking model -- consider running transactions on subnodes instead of root nodes

## Further Reading

- [Source Repository](https://github.com/appy-one/acebase)
- [AceBase Server](https://github.com/appy-one/acebase-server)
- [AceBase Client](https://github.com/appy-one/acebase-client)
