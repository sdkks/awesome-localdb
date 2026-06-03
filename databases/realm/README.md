# Realm

> **Category:** Mobile | **License:** Apache-2.0 | **Stars:** ~16,600

## Overview

Realm is an offline-first mobile object database that runs directly inside phones, tablets, wearables, and desktop apps. It stores typed objects with automatic indexing and provides real-time reactive queries — views update automatically when underlying data changes. Supporting Swift, Kotlin, Java, JavaScript/TypeScript, C#, and .NET, Realm offers zero-copy reads, ACID transactions, and schema migration with minimal boilerplate. It is designed as a complete replacement for SQLite and Core Data in mobile applications.

## Quick Start

### JavaScript

```js
// Install: npm install realm
const Realm = require('realm');

// Define object schemas
const ProductSchema = {
  name: 'Product',
  primaryKey: 'id',
  properties: {
    id: 'int',
    name: 'string',
    price: 'double',
    inStock: 'bool',
    category: 'string'
  }
};

// Open a Realm with the schema
const realm = new Realm({ schema: [ProductSchema] });

// Write objects inside a transaction
realm.write(() => {
  realm.create('Product', { id: 1, name: 'Widget', price: 9.99, inStock: true, category: 'Gadgets' });
  realm.create('Product', { id: 2, name: 'Gizmo', price: 14.50, inStock: false, category: 'Gadgets' });
});

// Query objects — results are live and auto-update
const gadgets = realm.objects('Product').filtered('category == $0', 'Gadgets');
console.log(`Gadgets in stock: ${gadgets.filtered('inStock == true').length}`);

// Add a change listener for reactive updates
gadgets.addListener((products, changes) => {
  console.log(`Gadgets changed! New count: ${products.length}`);
});

// Update inside a transaction
realm.write(() => {
  realm.create('Product', { id: 2, name: 'Gizmo', price: 12.99, inStock: true, category: 'Gadgets' }, 'modified');
});

// Clean up
gadgets.removeAllListeners();
realm.close();
```

## On-Disk Format

B+ Tree memory-mapped files (single-file per Realm, optional encryption)

## Core Strengths

- Real-time reactive queries with live objects that auto-update on data changes
- Zero-copy reads via memory-mapped storage — no deserialization overhead
- ACID transactions with schema migration support and low boilerplate
- Offline-first design: all data lives locally, sync is optional and additive
- Cross-platform: iOS, Android, .NET, JavaScript/RN, with a unified data model
- Single-file storage with built-in encryption, compaction, and notifications

## Best Use Cases

1. **Mobile Apps** -- Use Realm as the primary local database in iOS (Swift), Android (Kotlin), or React Native apps for offline-first persistence.
2. **React Native** -- Native-speed object storage with live queries; the JavaScript API mirrors the native SDKs for a consistent experience.
3. **Cross-Platform Data Layer** -- Define your data model once and share it across iOS, Android, and .NET targets.
4. **SQLite Replacement** -- Replace SQLite and Core Data with a simpler object API, automatic indexing, and reactive queries.
5. **Optional Cloud Sync** -- Add device sync to your app without rearchitecting the local data layer.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| JavaScript | [`recipe_mobile_store.js`](javascript/src/recipe_mobile_store.js) | Define schemas, insert products and orders, run filtered queries, observe live changes |

## Limitations & Caveats

- MongoDB announced deprecation of Atlas Device Sync + Realm SDKs in September 2024. The database remains open-source but official maintenance has slowed significantly.
- The JavaScript SDK (realm@20.x) requires native module compilation (`node-gyp`) and has known compatibility issues with newer Node.js versions.
- Realm requires a schema definition upfront — fields not in the schema cannot be stored, unlike schemaless document databases.
- Object models are tied to the Realm instance; objects queried from one Realm cannot be written to another without manual copying.
- All writes must happen inside `realm.write()` transaction blocks; this adds ceremony compared to auto-commit databases.
- The Node.js SDK is primarily intended for testing and server-side use; production mobile apps should use the React Native binding.

## Further Reading

- [Official Documentation](https://www.mongodb.com/docs/realm/)
- [Realm Swift (Main Repo)](https://github.com/realm/realm-swift)
- [Realm JavaScript/TypeScript](https://github.com/realm/realm-js)
- [Realm Kotlin (Android)](https://github.com/realm/realm-kotlin)
- [Realm .NET](https://github.com/realm/realm-dotnet)
- [NPM Package](https://www.npmjs.com/package/realm)
