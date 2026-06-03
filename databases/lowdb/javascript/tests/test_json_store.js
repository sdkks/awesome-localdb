/**
 * Tests for recipe_json_store.js
 *
 * Run: node --test tests/test_json_store.js
 */
import test from 'node:test'
import assert from 'node:assert'
import { execSync } from 'node:child_process'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const scriptPath = resolve(__dirname, '../src/recipe_json_store.js')

test('recipe_json_store runs without error', () => {
  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 10000
  })

  assert.ok(result.includes('All users'), 'Recipe should complete with user listing')
})

test('recipe_json_store produces expected output', () => {
  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 10000
  })

  // Verify insertions
  assert.ok(result.includes('Inserted 5 users'), 'Should confirm 5 users inserted')

  // Verify search
  assert.ok(result.includes('Found Alice'), 'Should find Alice')
  assert.ok(result.includes('Users under 30'), 'Should list users under 30')
  assert.ok(result.includes('Bob, Diana, Eve'), 'Bob, Diana, and Eve should be under 30')
  assert.ok(result.includes('London adults'), 'Should list London adults')
  assert.ok(result.includes('Alice, Charlie'), 'Alice and Charlie should be London adults')

  // Verify contains check
  assert.ok(result.includes('Contains Bob: true'), 'Should confirm Bob exists')
  assert.ok(result.includes('Contains Zelda: false'), 'Should confirm Zelda does not exist')

  // Verify update
  assert.ok(result.includes('Updated Alice'), 'Should show updated Alice')
  assert.ok(result.includes('"age":31'), 'Alice age should be 31')

  // Verify upsert
  assert.ok(result.includes('Bob after upsert'), 'Should show Bob after upsert')
  assert.ok(result.includes('"age":26'), 'Bob age should be 26 after upsert')
  assert.ok(result.includes('User count after upserts: 6'), 'Should have 6 users after adding Frank')

  // Verify count
  assert.ok(result.includes('Users in Paris: 2'), 'Should count 2 users in Paris')

  // Verify delete
  assert.ok(result.includes('User count after removing Eve: 5'), 'Should have 5 users after removing Eve')

  // Verify final listing
  assert.ok(result.includes('All users (5):'), 'Should show final user count of 5')
})
