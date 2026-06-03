/**
 * Recipe: JSON Document Store
 * Database: LowDB
 * Description: Demonstrates core CRUD operations using LowDB's plain JavaScript
 *              API -- insert, read, filter, update, upsert, and delete documents
 *              in a single JSON file. Uses a temporary file so no artifacts
 *              remain on disk.
 *
 * Usage: node src/recipe_json_store.js
 */

import { JSONFilePreset } from 'lowdb/node'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { unlinkSync } from 'node:fs'

// Generate a temp file path unique to this run
const dbPath = join(tmpdir(), `lowdb-recipe-${Date.now()}.json`)

async function main() {
  // 1. Setup -- create or open the JSON file with default structure
  const defaultData = { users: [] }
  const db = await JSONFilePreset(dbPath, defaultData)

  // 2. Insert documents -- push to the plain array and write
  db.data.users.push(
    { id: 1, name: 'Alice', age: 30, city: 'London' },
    { id: 2, name: 'Bob', age: 25, city: 'Paris' },
    { id: 3, name: 'Charlie', age: 35, city: 'London' },
    { id: 4, name: 'Diana', age: 28, city: 'Berlin' },
    { id: 5, name: 'Eve', age: 22, city: 'Paris' }
  )
  await db.write()

  console.log(`Inserted ${db.data.users.length} users.`)

  // 3. Search and filter -- use plain JavaScript Array methods
  const { users } = db.data

  // Find one by field
  const alice = users.find(u => u.name === 'Alice')
  console.log(`Found Alice: ${JSON.stringify(alice)}`)

  // Filter with conditions
  const young = users.filter(u => u.age < 30)
  console.log(`Users under 30: ${young.map(u => u.name).join(', ')}`)

  // Combined conditions
  const londonAdults = users.filter(u => u.city === 'London' && u.age >= 30)
  console.log(`London adults: ${londonAdults.map(u => u.name).join(', ')}`)

  // Check existence
  const hasBob = users.some(u => u.name === 'Bob')
  console.log(`Contains Bob: ${hasBob}`)
  const hasZelda = users.some(u => u.name === 'Zelda')
  console.log(`Contains Zelda: ${hasZelda}`)

  // 4. Update documents -- mutate in place and write
  const aliceRecord = db.data.users.find(u => u.name === 'Alice')
  if (aliceRecord) {
    aliceRecord.age = 31
  }
  await db.write()
  const updatedAlice = db.data.users.find(u => u.name === 'Alice')
  console.log(`Updated Alice: ${JSON.stringify(updatedAlice)}`)

  // 5. Upsert -- insert if not found, update if found
  await db.update(({ users }) => {
    // Upsert Frank (new)
    const francisIdx = users.findIndex(u => u.name === 'Frank')
    if (francisIdx >= 0) {
      users[francisIdx] = { ...users[francisIdx], age: 40, city: 'Tokyo' }
    } else {
      users.push({ id: 6, name: 'Frank', age: 40, city: 'Tokyo' })
    }

    // Upsert Bob (existing)
    const bobIdx = users.findIndex(u => u.name === 'Bob')
    if (bobIdx >= 0) {
      users[bobIdx] = { ...users[bobIdx], age: 26 }
    }
  })

  const bob = db.data.users.find(u => u.name === 'Bob')
  console.log(`Bob after upsert: ${JSON.stringify(bob)}`)
  console.log(`User count after upserts: ${db.data.users.length}`)

  // 6. Count with conditions
  const parisCount = db.data.users.filter(u => u.city === 'Paris').length
  console.log(`Users in Paris: ${parisCount}`)

  // 7. Delete documents
  await db.update(({ users }) => {
    const eveIdx = users.findIndex(u => u.name === 'Eve')
    if (eveIdx >= 0) {
      users.splice(eveIdx, 1)
    }
  })

  console.log(`User count after removing Eve: ${db.data.users.length}`)

  // 8. List all remaining documents
  console.log(`\nAll users (${db.data.users.length}):`)
  for (const user of db.data.users) {
    console.log(`  ${JSON.stringify(user)}`)
  }

  // 9. Cleanup -- remove the temporary file
  unlinkSync(dbPath)
}

main().catch(err => {
  // Clean up temp file even on error
  try { unlinkSync(dbPath) } catch (_) { /* ignore */ }
  console.error('Error:', err.message)
  process.exit(1)
})
