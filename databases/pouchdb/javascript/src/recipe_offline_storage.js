/**
 * Recipe: Offline Storage
 * Database: PouchDB
 * Description: Create, read, update, delete JSON documents locally, plus
 *              MapReduce views for querying. Uses in-memory adapter for
 *              clean Node.js execution without native dependencies.
 *
 * Usage: node src/recipe_offline_storage.js
 */

const PouchDB = require('pouchdb');
PouchDB.plugin(require('pouchdb-adapter-memory'));

function main() {
  // 1. Setup — create a local database (in-memory adapter for Node.js)
  //    In the browser this defaults to IndexedDB; Node defaults to LevelDB.
  const db = new PouchDB('cookbook', { adapter: 'memory' });

  // 2. Create documents — offline-first CRUD
  const createRecipes = db.bulkDocs([
    {
      _id: 'recipe_chili',
      name: 'Chili con Carne',
      cuisine: 'Mexican',
      prep_time: 45,
      servings: 4
    },
    {
      _id: 'recipe_padthai',
      name: 'Pad Thai',
      cuisine: 'Thai',
      prep_time: 30,
      servings: 2
    },
    {
      _id: 'recipe_ratatouille',
      name: 'Ratatouille',
      cuisine: 'French',
      prep_time: 60,
      servings: 6
    },
    {
      _id: 'recipe_tacos',
      name: 'Tacos al Pastor',
      cuisine: 'Mexican',
      prep_time: 40,
      servings: 5
    },
    {
      _id: 'recipe_curry',
      name: 'Green Curry',
      cuisine: 'Thai',
      prep_time: 35,
      servings: 3
    }
  ]);

  // 3. Read — retrieve a single document by id
  const readOne = createRecipes.then(() => {
    return db.get('recipe_padthai');
  });

  // 4. Update — modify an existing document
  const updateOne = readOne.then(doc => {
    doc.prep_time = 25; // Faster than we thought
    return db.put(doc);
  });

  // 5. Delete — remove a document
  const deleteOne = db.get('recipe_ratatouille').then(doc => {
    return db.remove(doc);
  });

  // 6. MapReduce view — design documents for querying
  const setupView = Promise.all([updateOne, deleteOne]).then(() => {
    const ddoc = {
      _id: '_design/recipes',
      views: {
        by_cuisine: {
          map: function (doc) {
            if (doc.cuisine) {
              emit(doc.cuisine, doc.name);
            }
          }.toString()
        },
        quick_meals: {
          map: function (doc) {
            if (doc.prep_time && doc.prep_time <= 35) {
              emit(doc.name, doc.prep_time);
            }
          }.toString()
        }
      }
    };
    return db.put(ddoc);
  });

  // 7. Query the views
  const run = setupView.then(() => {
    return Promise.all([
      db.query('recipes/by_cuisine', { key: 'Mexican' }),
      db.query('recipes/by_cuisine', { group: true }),
      db.query('recipes/quick_meals')
    ]);
  });

  run.then(([mexicanResults, cuisineGroups, quickResults]) => {
    console.log('=== Mexican Recipes ===');
    mexicanResults.rows.forEach(row => {
      console.log(`  ${row.value}`);
    });

    console.log('\n=== Recipes by Cuisine (count) ===');
    cuisineGroups.rows.forEach(row => {
      console.log(`  ${row.key}: ${row.value}`);
    });

    console.log('\n=== Quick Meals (under 35 min) ===');
    quickResults.rows.forEach(row => {
      console.log(`  ${row.key} (${row.value} min)`);
    });

    console.log('\nDone.');
  }).catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
}

if (require.main === module) {
  main();
}

module.exports = { main };
