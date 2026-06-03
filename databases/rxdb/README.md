# RxDB

> **Category:** Document | **License:** Apache-2.0 | **Stars:** ~23,200

## Overview

RxDB is a local-first, reactive NoSQL database for JavaScript applications. It stores JSON documents locally with JSON Schema validation and provides real-time reactive queries via RxJS observables — when data changes, every subscribed query updates automatically. RxDB runs in browsers, Node.js, Electron, React Native, and Capacitor with pluggable storage backends, and supports offline-first replication with multiple protocols including HTTP, GraphQL, WebRTC (P2P), CouchDB, WebSocket, Firestore, and NATS.

## Quick Start

### JavaScript

```js
// Install: npm install rxdb rxjs
import { createRxDatabase } from 'rxdb/plugins/core';
import { getRxStorageMemory } from 'rxdb/plugins/storage-memory';

// Create a database with schema-validated collections
const db = await createRxDatabase({
  name: 'myapp',
  storage: getRxStorageMemory()
});

await db.addCollections({
  users: {
    schema: {
      version: 0,
      primaryKey: 'id',
      type: 'object',
      properties: {
        id: { type: 'string', maxLength: 100 },
        name: { type: 'string' },
        email: { type: 'string' },
        age: { type: 'number' }
      },
      required: ['id', 'name', 'email']
    }
  }
});

// Insert documents
await db.users.insert({ id: 'u1', name: 'Ada Lovelace', email: 'ada@example.com', age: 36 });
await db.users.insert({ id: 'u2', name: 'Alan Turing', email: 'alan@example.com', age: 41 });

// Reactive query — updates automatically when data changes
const sub = db.users.find({ selector: { age: { $gt: 30 } } }).$.subscribe(docs => {
  console.log('Users over 30:', docs.map(d => d.name));
});

// Update a document
const alan = await db.users.findOne({ selector: { name: { $eq: 'Alan Turing' } } }).exec();
await alan.patch({ age: 42 }); // triggers the reactive query above

// Delete a document
await alan.remove();

// Clean up
sub.unsubscribe();
```

## On-Disk Format

Pluggable: Dexie.js (default) / IndexedDB / SQLite / LocalStorage / Memory

## Core Strengths

- Reactive queries via RxJS observables -- UI automatically updates on data changes
- JSON Schema-based validation with migration strategies for schema evolution
- Pluggable storage layer -- Dexie.js, IndexedDB, SQLite, LocalStorage, in-memory, and more
- Multi-protocol replication: HTTP, GraphQL, WebRTC (P2P), CouchDB, WebSocket, Firestore, NATS
- Offline-first with automatic sync, conflict detection, and CRDT-based resolution
- Multi-tab support with cross-tab observables via BroadcastChannel
- Encryption plugin for field-level document encryption at rest
- Runs anywhere JavaScript runs -- browser, Node.js, Electron, React Native, Capacitor

## Best Use Cases

1. **Offline-First Web Apps** -- Users work with local data instantly; RxDB persists to IndexedDB/Dexie and syncs when connectivity returns via HTTP or WebSocket replication.
2. **Reactive UIs** -- Frameworks like React, Angular, and Vue integrate with RxDB observables so that every data change propagates instantly to every bound component.
3. **Multi-Device Sync** -- WebRTC replication enables peer-to-peer data sync between browser tabs, devices on the same network, or devices behind NAT.
4. **Electron and React Native Apps** -- Run RxDB with Dexie.js or SQLite storage for a local-first database embedded directly in your desktop or mobile app.
5. **Encrypted Client-Side Storage** -- Use the crypto-js encryption plugin to encrypt individual fields at rest, keeping sensitive data safe even if local storage is compromised.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| JavaScript | [`recipe_reactive_store.js`](javascript/src/recipe_reactive_store.js) | Insert, query, observe, update, and delete JSON documents with reactive queries |
| JavaScript | [`recipe_replication.js`](javascript/src/recipe_replication.js) | Set up bidirectional sync between two local databases simulating remote replication |

## Limitations & Caveats

- Collections are schemaful -- every collection requires a JSON Schema definition; this adds upfront cost compared to schemaless document stores like PouchDB.
- The default storage (Dexie.js) adds overhead compared to raw IndexedDB. For the fastest performance, the premium IndexedDB or SQLite storage plugins are available.
- Some advanced features (SQLite storage, Query Builder, Vector Search) require a paid premium license.
- RxDB has a significant dependency tree due to RxJS, Dexie.js, and optional replication/encryption plugins.
- Schema migrations require explicit versioned migration strategies; the dev-mode plugin will warn about schema mismatches but production use requires migration functions.

## Further Reading

- [Official Documentation](https://rxdb.info/)
- [Source Repository](https://github.com/pubkey/rxdb)
- [RxDB Quickstart](https://rxdb.info/quickstart.html)
- [Replication Protocols](https://rxdb.info/replication.html)
- [Comparison with PouchDB](https://rxdb.info/comparison-pouchdb.html)
- [RxDB vs Other Databases](https://rxdb.info/comparison.html)
