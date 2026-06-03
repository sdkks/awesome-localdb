/**
 * Recipe: Reactive Store
 * Database: RxDB
 * Description: Demonstrates insert, query, reactive observe, update, and delete
 *              of JSON documents using RxDB with schema validation. Uses the
 *              in-memory storage adapter for clean Node.js execution.
 *
 * Usage: node src/recipe_reactive_store.js
 */

const { createRxDatabase } = require('rxdb/plugins/core');
const { getRxStorageMemory } = require('rxdb/plugins/storage-memory');

async function main() {
  // 1. Create a database with the in-memory storage adapter
  const db = await createRxDatabase({
    name: 'cookbook',
    storage: getRxStorageMemory(),
  });

  // 2. Add a collection with JSON Schema validation
  await db.addCollections({
    recipes: {
      schema: {
        version: 0,
        primaryKey: 'id',
        type: 'object',
        properties: {
          id: { type: 'string', maxLength: 100 },
          name: { type: 'string' },
          cuisine: { type: 'string' },
          prep_time: { type: 'number' },
          servings: { type: 'number' },
          vegetarian: { type: 'boolean' }
        },
        required: ['id', 'name', 'cuisine', 'prep_time', 'servings']
      }
    }
  });

  // 3. Insert documents
  await db.recipes.bulkInsert([
    { id: 'recipe_chili', name: 'Chili con Carne', cuisine: 'Mexican', prep_time: 45, servings: 4, vegetarian: false },
    { id: 'recipe_padthai', name: 'Pad Thai', cuisine: 'Thai', prep_time: 30, servings: 2, vegetarian: false },
    { id: 'recipe_ratatouille', name: 'Ratatouille', cuisine: 'French', prep_time: 60, servings: 6, vegetarian: true },
    { id: 'recipe_tacos', name: 'Tacos al Pastor', cuisine: 'Mexican', prep_time: 40, servings: 5, vegetarian: false },
    { id: 'recipe_curry', name: 'Green Curry', cuisine: 'Thai', prep_time: 35, servings: 3, vegetarian: true },
  ]);

  console.log(`Inserted ${await db.recipes.count().exec()} documents.`);

  // 4. Query: find all Mexican recipes
  const mexicanRecipes = await db.recipes.find({
    selector: { cuisine: { $eq: 'Mexican' } }
  }).exec();
  console.log(`Mexican recipes: ${mexicanRecipes.map(r => r.name).join(', ')}`);

  // 5. Query: find quick recipes (under 35 minutes)
  const quickRecipes = await db.recipes.find({
    selector: { prep_time: { $lt: 35 } }
  }).exec();
  console.log(`Quick recipes (under 35 min): ${quickRecipes.map(r => r.name).join(', ')}`);

  // 6. Reactive query: subscribe to vegetarian recipes (auto-updates on changes)
  console.log('\n=== Reactive Query: Vegetarian Recipes ===');
  const sub = db.recipes.find({
    selector: { vegetarian: { $eq: true } }
  }).$.subscribe(docs => {
    console.log(`  Vegetarian recipes: [${docs.map(r => `${r.name} (${r.cuisine})`).join(', ')}]`);
  });

  // Allow the subscription to emit its initial value before we make changes
  await new Promise(resolve => setTimeout(resolve, 100));

  // 7. Update a document via patch
  const padThai = await db.recipes.findOne({
    selector: { name: { $eq: 'Pad Thai' } }
  }).exec();
  await padThai.patch({ prep_time: 25, vegetarian: true });
  console.log('\nUpdated Pad Thai (vegetarian, 25 min)');

  // Allow the subscription to emit the updated value
  await new Promise(resolve => setTimeout(resolve, 100));

  // 8. Upsert: insert or update
  const frankDoc = await db.recipes.findOne({
    selector: { name: { $eq: 'Focaccia' } }
  }).exec();
  if (frankDoc) {
    await frankDoc.patch({ prep_time: 55 });
  } else {
    await db.recipes.insert({ id: 'recipe_focaccia', name: 'Focaccia', cuisine: 'Italian', prep_time: 55, servings: 4, vegetarian: true });
  }
  console.log('Upserted Focaccia');

  // Allow reactive query to catch up
  await new Promise(resolve => setTimeout(resolve, 100));

  // 9. Delete a document
  const ratatouille = await db.recipes.findOne({
    selector: { name: { $eq: 'Ratatouille' } }
  }).exec();
  await ratatouille.remove();
  console.log('Removed Ratatouille');

  // Allow reactive query to catch up
  await new Promise(resolve => setTimeout(resolve, 100));

  // 10. Show all remaining documents
  const allDocs = await db.recipes.find().exec();
  console.log(`\nTotal documents after operations: ${allDocs.length}`);
  allDocs.forEach(r => {
    console.log(`  [${r.id}] ${r.name} — ${r.cuisine}, ${r.prep_time} min${r.vegetarian ? ', vegetarian' : ''}`);
  });

  // 11. Clean up
  sub.unsubscribe();
  await db.remove();
  console.log('\nDone.');
}

if (require.main === module) {
  main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
}

module.exports = { main };
