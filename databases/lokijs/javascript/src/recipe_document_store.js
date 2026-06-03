/**
 * Recipe: Document Store
 * Database: LokiJS
 * Description: Demonstrates core CRUD operations using LokiJS's MongoDB-like API --
 *              insert, find, where, chain queries, findAndUpdate, findAndRemove,
 *              DynamicView, and compound indexes. Uses in-memory mode with no
 *              persistence to avoid filesystem artifacts.
 *
 * Usage: node src/recipe_document_store.js
 */

const loki = require('lokijs')

function main() {
  // 1. Setup -- create in-memory database (no persistence file)
  const db = new loki('recipe.db')

  // 2. Create collection with compound index
  const users = db.addCollection('users', {
    indices: ['name', 'city', 'age']
  })

  // 3. Insert documents
  users.insert([
    { name: 'Alice', age: 30, city: 'London' },
    { name: 'Bob', age: 25, city: 'Paris' },
    { name: 'Charlie', age: 35, city: 'London' },
    { name: 'Diana', age: 28, city: 'Berlin' },
    { name: 'Eve', age: 22, city: 'Paris' }
  ])

  console.log(`Inserted ${users.count()} users.`)

  // 4. Find -- simple equality queries
  const alice = users.findOne({ name: 'Alice' })
  console.log(`Found Alice: ${JSON.stringify(alice)}`)

  const londoners = users.find({ city: 'London' })
  console.log(`Londoners: ${londoners.map(u => u.name).join(', ')}`)

  // 5. Find with regex
  const namesWithA = users.find({ name: { '$regex': /A|a/ } })
  console.log(`Names with A/a: ${namesWithA.map(u => u.name).join(', ')}`)

  // 6. Where -- function-based filtering
  const young = users.where(u => u.age < 30)
  console.log(`Users under 30: ${young.map(u => u.name).join(', ')}`)

  // 7. Chain queries
  const result = users.chain()
    .find({ city: 'London' })
    .where(u => u.age >= 30)
    .data()
  console.log(`London adults: ${result.map(u => u.name).join(', ')}`)

  // 8. Existence check
  const hasBob = users.findOne({ name: 'Bob' }) !== null
  console.log(`Contains Bob: ${hasBob}`)
  const hasZelda = users.findOne({ name: 'Zelda' }) !== null
  console.log(`Contains Zelda: ${hasZelda}`)

  // 9. Update documents
  users.findAndUpdate({ name: 'Alice' }, function (doc) {
    doc.age = 31
  })
  const updated = users.findOne({ name: 'Alice' })
  console.log(`Updated Alice: ${JSON.stringify(updated)}`)

  // 10. Upsert -- insert if not found, update if found
  let existing = users.findOne({ name: 'Frank' })
  if (existing) {
    existing.age = 40
    existing.city = 'Tokyo'
    users.update(existing)
  } else {
    users.insert({ name: 'Frank', age: 40, city: 'Tokyo' })
  }

  existing = users.findOne({ name: 'Bob' })
  if (existing) {
    existing.age = 26
    users.update(existing)
  }

  const bob = users.findOne({ name: 'Bob' })
  console.log(`Bob after upsert: ${JSON.stringify(bob)}`)
  console.log(`User count after upserts: ${users.count()}`)

  // 11. Count with conditions
  const parisCount = users.chain().find({ city: 'Paris' }).count()
  console.log(`Users in Paris: ${parisCount}`)

  // 12. Remove documents
  users.findAndRemove({ name: 'Eve' })
  console.log(`User count after removing Eve: ${users.count()}`)

  // 13. DynamicView -- live sorted view that updates with the collection
  const byAge = users.addDynamicView('byAge')
  byAge.applySimpleSort('age', { desc: true })
  console.log('Users sorted by age (desc):')
  byAge.data().forEach(u => {
    console.log(`  ${u.name}: ${u.age}`)
  })

  // 14. Add new item and observe DynamicView updates automatically
  users.insert({ name: 'Grace', age: 45, city: 'Oslo' })
  console.log('\nDynamicView after inserting Grace:')
  byAge.data().forEach(u => {
    console.log(`  ${u.name}: ${u.age}`)
  })

  // 15. List all remaining documents
  console.log(`\nAll users (${users.count()}):`)
  users.find().forEach(u => {
    console.log(`  ${JSON.stringify(u)}`)
  })

}

main()
