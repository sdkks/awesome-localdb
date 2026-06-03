# PouchDB

> **Category:** Document | **License:** Apache-2.0 | **Stars:** ~17,000

## Overview

PouchDB is a browser-native JavaScript database that stores JSON documents locally using IndexedDB and syncs bidirectionally with any CouchDB-compatible server. It brings offline-first architecture to web apps: users interact with local data instantly, and PouchDB handles replication and conflict resolution behind the scenes when connectivity returns. Lightweight enough to drop into any web page with a single script tag.

## Quick Start

### JavaScript

```js
// Install: npm install pouchdb
const PouchDB = require('pouchdb');

// Create or open a local database (IndexedDB in browser, LevelDB in Node.js)
const db = new PouchDB('my_app');

// Create a document
db.put({
  _id: 'user_1',
  name: 'Ada Lovelace',
  email: 'ada@example.com',
  role: 'engineer'
}).then(response => {
  console.log('Document created:', response.id);
});

// Retrieve a document
db.get('user_1').then(doc => {
  console.log('Retrieved:', doc.name); // "Ada Lovelace"
});

// Query with MapReduce
const designDoc = {
  _id: '_design/engineers',
  views: {
    by_role: {
      map: function (doc) { if (doc.role === 'engineer') emit(doc.name); }.toString()
    }
  }
};

db.put(designDoc).then(() => {
  return db.query('engineers/by_role');
}).then(result => {
  console.log('Engineers:', result.rows.map(r => r.key));
});

// Sync with a remote CouchDB
const remote = new PouchDB('https://example.com/my_remote_db');
db.replicate.to(remote).on('complete', () => {
  console.log('Sync complete');
}).on('error', err => {
  console.error('Sync error:', err);
});
```

## On-Disk Format

IndexedDB (browser) / LevelDB (Node.js)

## Core Strengths

- Runs natively in every browser using IndexedDB with zero native dependencies
- Seamless bidirectional sync with Apache CouchDB and compatible servers
- Offline-first design with automatic conflict detection and resolution
- Lightweight -- just a script tag or npm install, 46KB gzipped in the browser
- MVCC concurrency control keeps reads consistent during writes
- Full CRUD API for JSON documents with attachments, MapReduce views, and secondary indexes

## Best Use Cases

1. **Offline-First Web Apps** -- Users save data locally even without internet. PouchDB persists to IndexedDB and syncs when back online.
2. **Progressive Web Apps (PWAs)** -- Service workers and local storage combine for app-like reliability with real sync.
3. **Mobile Web Applications** -- Build web apps that withstand flaky cellular connections and seamlessly merge data later.
4. **Multi-Device Sync** -- One user on phone and laptop stays in sync through a central CouchDB server.
5. **Node.js Embedded Document Store** -- Use PouchDB in Node.js scripts as a lightweight, promise-based document store with optional replication.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| JavaScript | [`recipe_offline_storage.js`](javascript/src/recipe_offline_storage.js) | Create, read, update, delete JSON documents with MapReduce views |
| JavaScript | [`recipe_replication.js`](javascript/src/recipe_replication.js) | Set up bidirectional sync between two local databases simulating remote replication |

## Limitations & Caveats

- Automatic sync between browser and server requires a remote CouchDB-compatible endpoint (CouchDB, Cloudant, Couchbase).
- PouchDB is AP from a CAP perspective -- favors availability and partition tolerance, not strong consistency.
- The Node.js LevelDB adapter requires native compilation; pure-JavaScript alternatives like MemDOWN work but are slower.
- Secondary indexes (via `pouchdb-find`) must be deliberately set up; ad-hoc queries over large datasets are slow without them.
- Document conflicts during multi-master replication require application-level resolution logic.

## Further Reading

- [Official Documentation](https://pouchdb.com/guides/)
- [Source Repository](https://github.com/pouchdb/pouchdb)
- [PouchDB API Reference](https://pouchdb.com/api.html)
- [CouchDB Replication Protocol](https://docs.couchdb.org/en/stable/replication/protocol.html)
- [Database of Databases -- PouchDB](https://dbdb.io/db/pouchdb)
