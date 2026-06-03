/**
 * Tests for recipe_document_store.js
 *
 * Run: node --test tests/test_recipe_document_store.js
 */
const test = require('node:test')
const assert = require('node:assert')
const { execSync } = require('node:child_process')
const { resolve } = require('node:path')

const scriptPath = resolve(__dirname, '../src/recipe_document_store.js')

test('recipe_document_store runs without error', () => {
  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 10000
  })

  assert.ok(result.includes('All users'), 'Recipe should complete with user listing')
})

test('recipe_document_store produces expected output', () => {
  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 10000
  })

  // Verify insertions
  assert.ok(result.includes('Inserted 5 users'), 'Should confirm 5 users inserted')

  // Verify find
  assert.ok(result.includes('Found Alice'), 'Should find Alice by name')
  assert.ok(result.includes('Londoners:'), 'Should find Londoners')
  assert.ok(result.includes('Alice') && result.includes('Charlie'), 'Alice and Charlie should be Londoners')

  // Verify regex find
  assert.ok(result.includes('Names with A/a'), 'Should find names with regex')

  // Verify where
  assert.ok(result.includes('Users under 30'), 'Should list users under 30')
  assert.ok(result.includes('Bob') && result.includes('Diana') && result.includes('Eve'), 'Bob, Diana, and Eve should be under 30')

  // Verify chain
  assert.ok(result.includes('London adults'), 'Should show London adults')
  assert.ok(result.includes('Alice') && result.includes('Charlie'), 'Alice and Charlie should be in chain results')

  // Verify contains check
  assert.ok(result.includes('Contains Bob: true'), 'Should confirm Bob exists')
  assert.ok(result.includes('Contains Zelda: false'), 'Should confirm Zelda does not exist')

  // Verify update
  assert.ok(result.includes('Updated Alice'), 'Should show updated Alice')
  assert.ok(result.includes('"age":31'), 'Alice age should be 31')

  // Verify upsert
  assert.ok(result.includes('Bob after upsert'), 'Should show Bob after upsert')
  assert.ok(result.includes('"age":26'), 'Bob age should be 26 after upsert')

  // Verify paris count
  assert.ok(result.includes('Users in Paris: 2'), 'Should count 2 users in Paris')

  // Verify delete
  assert.ok(result.includes('User count after removing Eve: 5'), 'Should have 5 users after removing Eve')

  // Verify DynamicView sorting
  assert.ok(result.includes('Users sorted by age (desc)'), 'Should show sorted users')

  // Verify final listing
  assert.ok(result.includes('All users (6):'), 'Should show final user count of 6')
  assert.ok(result.includes('"name":"Grace"'), 'Grace should be in final listing')
})
