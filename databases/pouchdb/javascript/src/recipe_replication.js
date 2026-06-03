/**
 * Recipe: Replication
 * Database: PouchDB
 * Description: Demonstrate bidirectional sync between two local PouchDB
 *              databases, simulating the offline-first replication flow.
 *              Uses in-memory adapter for clean Node.js execution.
 *
 * Usage: node src/recipe_replication.js
 */

const PouchDB = require('pouchdb');
PouchDB.plugin(require('pouchdb-adapter-memory'));

function main() {
  // 1. Setup — two independent databases (simulating local ↔ remote)
  const localDB = new PouchDB('local_kitchen', { adapter: 'memory' });
  const remoteDB = new PouchDB('server_kitchen', { adapter: 'memory' });

  // 2. Seed the remote with existing data
  const seedRemote = remoteDB.bulkDocs([
    { _id: 'recipe_pizza', name: 'Margherita Pizza', chef: 'Mario' },
    { _id: 'recipe_pasta', name: 'Carbonara', chef: 'Luigi' },
    { _id: 'recipe_salad', name: 'Caprese Salad', chef: 'Mario' }
  ]);

  // 3. Seed the local with offline-only data
  const seedLocal = seedRemote.then(() => {
    return localDB.bulkDocs([
      { _id: 'recipe_soup', name: 'Minestrone', chef: 'Anna' },
      { _id: 'recipe_bread', name: 'Focaccia', chef: 'Anna' }
    ]);
  });

  // 4. Replicate: push local changes to remote
  const push = seedLocal.then(() => {
    console.log('Pushing local changes to remote...');
    return localDB.replicate.to(remoteDB);
  });

  push.then(info => {
    console.log('Push complete.');
    console.log('  Docs written to remote:', info.docs_written);
    return localDB.replicate.from(remoteDB);
  }).then(info => {
    // 5. Replicate: pull remote changes to local
    console.log('\nPulling remote changes to local...');
    console.log('  Docs written to local:', info.docs_written);
    return remoteDB.allDocs({ include_docs: true });
  }).then(remoteAll => {
    // 6. Show the merged state on remote
    console.log('\n=== Remote Database (after sync) ===');
    remoteAll.rows.forEach(row => {
      console.log(`  [${row.id}] ${row.doc.name} — chef: ${row.doc.chef}`);
    });
    return localDB.allDocs({ include_docs: true });
  }).then(localAll => {
    // 7. Show the merged state locally
    console.log('\n=== Local Database (after sync) ===');
    localAll.rows.forEach(row => {
      console.log(`  [${row.id}] ${row.doc.name} — chef: ${row.doc.chef}`);
    });

    // 8. Continuous (live) replication — for long-running processes
    console.log('\n=== Starting live sync (cancelled after 2 seconds) ===');
    const liveSync = localDB.sync(remoteDB, {
      live: true,
      retry: true
    }).on('change', info => {
      console.log('  Live change:', info.direction, info.change.docs.length, 'doc(s)');
    }).on('active', () => {
      console.log('  Live sync active');
    });

    // Demonstrate a change during live sync
    remoteDB.put({ _id: 'recipe_tiramisu', name: 'Tiramisu', chef: 'Sofia' })
      .then(() => {
        console.log('  Added Tiramisu to remote during live sync');
      });

    // Cancel live sync after 2 seconds
    setTimeout(() => {
      liveSync.cancel();
      console.log('\n  Live sync cancelled.');
      console.log('\nDone.');
    }, 2000);
  }).catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
}

if (require.main === module) {
  main();
}

module.exports = { main };
