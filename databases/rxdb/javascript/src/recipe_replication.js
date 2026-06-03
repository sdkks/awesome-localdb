/**
 * Recipe: Replication
 * Database: RxDB
 * Description: Demonstrate bidirectional sync between two local RxDB databases,
 *              simulating the offline-first replication flow. Uses the in-memory
 *              storage adapter for clean Node.js execution.
 *
 * Usage: node src/recipe_replication.js
 */

const { createRxDatabase } = require('rxdb/plugins/core');
const { getRxStorageMemory } = require('rxdb/plugins/storage-memory');
const { replicateRxCollection } = require('rxdb/plugins/replication');

// Define a shared schema for both databases
const RECIPE_SCHEMA = {
  version: 0,
  primaryKey: 'id',
  type: 'object',
  properties: {
    id: { type: 'string', maxLength: 100 },
    name: { type: 'string' },
    chef: { type: 'string' },
    prep_time: { type: 'number' }
  },
  required: ['id', 'name', 'chef']
};

async function main() {
  // 1. Create two independent databases (simulating local and remote)
  const localDb = await createRxDatabase({
    name: 'local_kitchen',
    storage: getRxStorageMemory(),
  });
  const remoteDb = await createRxDatabase({
    name: 'remote_kitchen',
    storage: getRxStorageMemory(),
  });

  await localDb.addCollections({
    recipes: { schema: RECIPE_SCHEMA }
  });
  await remoteDb.addCollections({
    recipes: { schema: RECIPE_SCHEMA }
  });

  // 2. Seed the remote with existing data
  await remoteDb.recipes.bulkInsert([
    { id: 'recipe_pizza', name: 'Margherita Pizza', chef: 'Mario', prep_time: 60 },
    { id: 'recipe_pasta', name: 'Carbonara', chef: 'Luigi', prep_time: 25 },
    { id: 'recipe_salad', name: 'Caprese Salad', chef: 'Mario', prep_time: 10 },
  ]);
  console.log(`Remote seeded with ${await remoteDb.recipes.count().exec()} recipes.`);

  // 3. Seed the local with offline-only data
  await localDb.recipes.bulkInsert([
    { id: 'recipe_soup', name: 'Minestrone', chef: 'Anna', prep_time: 45 },
    { id: 'recipe_bread', name: 'Focaccia', chef: 'Anna', prep_time: 55 },
  ]);
  console.log(`Local seeded with ${await localDb.recipes.count().exec()} recipes.`);

  // 4. Set up bidirectional replication between local and remote
  const replication = replicateRxCollection({
    collection: localDb.recipes,
    replicationIdentifier: 'my-recipes-replication',
    pull: {
      async handler(lastCheckpoint, batchSize) {
        const docs = await remoteDb.recipes.find().exec();
        const checkpoint = docs.length > 0 ? docs[docs.length - 1].id : null;
        return {
          documents: docs.map(doc => {
            const { _rev, ...rest } = doc.toJSON();
            return rest;
          }),
          checkpoint: checkpoint,
        };
      },
    },
    push: {
      async handler(changeRows) {
        for (const row of changeRows) {
          const { _rev, ...doc } = row.newDocumentState;
          const existing = await remoteDb.recipes.findOne({ selector: { id: { $eq: doc.id } } }).exec();
          if (existing) {
            await existing.patch(doc);
          } else {
            await remoteDb.recipes.insert(doc);
          }
        }
        return [];
      },
    },
  });

  // Wait for initial replication to settle
  console.log('\nReplicating...');
  await replication.awaitInitialReplication();
  console.log('Initial replication complete.');

  // 5. Show merged state on remote
  const remoteAll = await remoteDb.recipes.find().exec();
  console.log('\n=== Remote Database (after sync) ===');
  remoteAll.forEach(r => {
    console.log(`  [${r.id}] ${r.name} — chef: ${r.chef}`);
  });

  // 6. Show merged state locally
  const localAll = await localDb.recipes.find().exec();
  console.log('\n=== Local Database (after sync) ===');
  localAll.forEach(r => {
    console.log(`  [${r.id}] ${r.name} — chef: ${r.chef}`);
  });

  // 7. Demonstrate a change that propagates via replication
  console.log('\n=== Adding Tiramisu to local during replication ===');
  await localDb.recipes.insert({ id: 'recipe_tiramisu', name: 'Tiramisu', chef: 'Sofia', prep_time: 30 });

  // Wait for replication to push to remote
  await new Promise(resolve => setTimeout(resolve, 200));

  const tiramisuRemote = await remoteDb.recipes.findOne({ selector: { name: { $eq: 'Tiramisu' } } }).exec();
  console.log(`Tiramisu in remote: ${tiramisuRemote ? tiramisuRemote.name : 'NOT FOUND'}`);

  // 8. Clean up
  await replication.cancel();
  await localDb.remove();
  await remoteDb.remove();
  console.log('\nDone.');
}

if (require.main === module) {
  main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
}

module.exports = { main };
