/**
 * Recipe: Realtime Document Store
 * Database: AceBase
 * Description: Demonstrates core AceBase operations -- set, update, get, query,
 *              realtime subscriptions (child_added, child_changed, value),
 *              transactions, and indexes. Uses local binary storage with a
 *              temp database path.
 *
 * Usage: node src/recipe_realtime_store.js
 */

const { AceBase } = require('acebase')
const path = require('path')
const fs = require('fs')

const DB_DIR = path.join(__dirname, '..', '.acebase-temp')
const DB_NAME = 'recipe'

// Clean up any previous run and ensure temp directory exists
if (fs.existsSync(DB_DIR)) {
  fs.rmSync(DB_DIR, { recursive: true, force: true })
}
fs.mkdirSync(DB_DIR, { recursive: true })

async function main() {
  // 1. Setup -- create local database
  const db = new AceBase(DB_NAME, {
    logLevel: 'error',
    storage: { path: DB_DIR }
  })

  await db.ready()

  const usersRef = db.ref('users')

  // 2. Store documents with auto-generated keys via push
  console.log('--- Inserting users ---')
  const aliceRef = await usersRef.push({ name: 'Alice', age: 30, city: 'London', score: 100 })
  console.log(`Pushed Alice: ${aliceRef.key}`)
  const bobRef = await usersRef.push({ name: 'Bob', age: 25, city: 'Paris', score: 200 })
  console.log(`Pushed Bob: ${bobRef.key}`)
  const charlieRef = await usersRef.push({ name: 'Charlie', age: 35, city: 'London', score: 150 })
  console.log(`Pushed Charlie: ${charlieRef.key}`)
  const dianaRef = await usersRef.push({ name: 'Diana', age: 28, city: 'Berlin', score: 175 })
  console.log(`Pushed Diana: ${dianaRef.key}`)
  const eveRef = await usersRef.push({ name: 'Eve', age: 22, city: 'Paris', score: 125 })
  console.log(`Pushed Eve: ${eveRef.key}`)

  // 3. Get a specific document
  console.log('\n--- Reading Alice ---')
  const aliceSnap = await db.ref(`users/${aliceRef.key}`).get()
  console.log(`Alice: ${JSON.stringify(aliceSnap.val())}`)

  // 4. Update a document (merge)
  console.log('\n--- Updating Alice ---')
  await db.ref(`users/${aliceRef.key}`).update({ age: 31, score: 110 })
  const updatedSnap = await db.ref(`users/${aliceRef.key}`).get()
  console.log(`Updated Alice: ${JSON.stringify(updatedSnap.val())}`)

  // 5. Query with filter, sort, and limit
  console.log('\n--- Query: score >= 100, sorted by name ---')
  const querySnap = await usersRef.query()
    .filter('score', '>=', 100)
    .sort('name')
    .take(10)
    .get()
  const results = querySnap.getValues()
  results.forEach(user => console.log(`  ${user.name}: ${user.score}`))

  // 6. Count children
  const totalUsers = await usersRef.count()
  console.log(`\nTotal users: ${totalUsers}`)

  // 7. Realtime subscriptions
  console.log('\n--- Realtime subscriptions ---')
  const events = []

  usersRef.on('child_added', child => {
    events.push(`child_added: ${child.val().name}`)
  })

  // Add a new user after subscriber is registered
  const frankRef = await usersRef.push({ name: 'Frank', age: 40, city: 'Tokyo', score: 300 })
  console.log(`Frank added, events captured: ${events.length}`)

  // Subscribe to child_changed
  usersRef.on('child_changed', child => {
    events.push(`child_changed: ${child.val().name} (score: ${child.val().score})`)
  })

  // Update Frank's score to trigger child_changed
  await db.ref(`users/${frankRef.key}`).update({ score: 320 })

  // Value subscription for the whole path
  db.ref(`users/${frankRef.key}`).on('value', snap => {
    const val = snap.val()
    if (val) {
      events.push(`value: ${val.name} -> score=${val.score}`)
    }
  })

  // Another update to trigger value event
  await db.ref(`users/${frankRef.key}`).update({ score: 340 })

  // Give AceBase a moment to deliver value event before printing
  await new Promise(resolve => setTimeout(resolve, 100))

  console.log('Events received:')
  events.forEach(e => console.log(`  ${e}`))

  // 8. Transaction -- atomic get-and-set
  console.log('\n--- Transaction ---')
  await db.ref(`users/${aliceRef.key}/score`).transaction(snap => {
    const current = snap.val() || 0
    return current + 50 // Add 50 points
  })

  const afterTxSnap = await db.ref(`users/${aliceRef.key}/score`).get()
  console.log(`Alice score after transaction: ${afterTxSnap.val()}`)

  // 9. Indexes
  console.log('\n--- Indexes ---')
  await db.indexes.create('users', 'score')
  await db.indexes.create('users', 'city')
  console.log('Indexes created on score and city')

  // Query using the index
  const indexedQuery = await usersRef.query()
    .filter('city', '==', 'Paris')
    .get()
  console.log(`Users in Paris: ${indexedQuery.getValues().map(u => u.name).join(', ')}`)

  // 10. Remove a document
  console.log('\n--- Removing Eve ---')
  await db.ref(`users/${eveRef.key}`).remove()
  const afterRemoveCount = await usersRef.count()
  console.log(`Users after removing Eve: ${afterRemoveCount}`)

  // 11. Final listing
  console.log('\n--- Final listing ---')
  const finalCount = await usersRef.count()
  const allSnap = await usersRef.get()
  console.log(`All users (${finalCount}):`)
  Object.entries(allSnap.val()).forEach(([key, child]) => {
    console.log(`  ${child.name}: score=${child.score}, city=${child.city}`)
  })

  // Close the database to release file locks
  await db.close()

  // Cleanup
  if (fs.existsSync(DB_DIR)) {
    fs.rmSync(DB_DIR, { recursive: true, force: true })
  }

  console.log('\nRecipe completed successfully.')
}

main().catch(err => {
  console.error('Recipe failed:', err)
  // Cleanup even on failure
  if (fs.existsSync(DB_DIR)) {
    fs.rmSync(DB_DIR, { recursive: true, force: true })
  }
  process.exit(1)
})
