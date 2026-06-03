/**
 * Tests for recipe_realtime_store.js
 *
 * Run: node --test tests/test_recipe_realtime_store.js
 */
const test = require('node:test')
const assert = require('node:assert')
const { execSync } = require('node:child_process')
const { resolve } = require('node:path')

const scriptPath = resolve(__dirname, '../src/recipe_realtime_store.js')

test('recipe_realtime_store runs without error', () => {
  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 15000
  })

  assert.ok(result.includes('Recipe completed successfully'), 'Recipe should complete successfully')
})

test('recipe_realtime_store produces expected output', () => {
  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 15000
  })

  // Verify insertions via push
  assert.ok(result.includes('Pushed Alice'), 'Should push Alice')
  assert.ok(result.includes('Pushed Bob'), 'Should push Bob')
  assert.ok(result.includes('Pushed Charlie'), 'Should push Charlie')
  assert.ok(result.includes('Pushed Diana'), 'Should push Diana')
  assert.ok(result.includes('Pushed Eve'), 'Should push Eve')

  // Verify read
  assert.ok(result.includes('Alice'), 'Should read Alice details')

  // Verify update
  assert.ok(result.includes('Updated Alice'), 'Should show updated Alice')
  assert.ok(result.includes('"age":31'), 'Alice age should be 31')
  assert.ok(result.includes('"score":110'), 'Alice score should be 110')

  // Verify query (runs with 5 initial users, before Frank is added)
  assert.ok(result.includes('Query: score >= 100'), 'Should show query header')
  assert.ok(result.includes('Alice: 110'), 'Alice should appear in query')
  assert.ok(result.includes('Bob: 200'), 'Bob should appear in query')
  assert.ok(result.includes('Charlie: 150'), 'Charlie should appear in query')

  // Verify count
  assert.ok(result.includes('Total users: 5'), 'Should have 5 users initially')

  // Verify realtime subscriptions
  assert.ok(result.includes('child_added: Frank'), 'Should fire child_added for Frank')
  assert.ok(result.includes('child_changed: Frank (score: 320)'), 'Should fire child_changed for Frank')
  assert.ok(result.includes('value: Frank -> score=340'), 'Should fire value event with final score')

  // Verify transaction
  assert.ok(result.includes('Alice score after transaction: 160'), 'Transaction should add 50 points')

  // Verify indexes
  assert.ok(result.includes('Indexes created on score and city'), 'Should create indexes')

  // Verify indexed query (order may vary, check for both expected names)
  assert.ok(result.includes('Users in Paris:'), 'Should show Paris query')
  assert.ok(result.includes('Bob') && result.includes('Eve'), 'Should include Bob and Eve from Paris')

  // Verify remove
  assert.ok(result.includes('Users after removing Eve: 5'), 'Should have 5 users after removing Eve')

  // Verify final listing
  assert.ok(result.includes('All users (5):'), 'Should show final user count of 5')
  assert.ok(result.includes('Frank: score=340, city=Tokyo'), 'Frank should be in final listing with correct data')
  assert.ok(result.includes('Alice: score=160, city=London'), 'Alice should have updated score')

  // Verify completion
  assert.ok(result.includes('Recipe completed successfully'), 'Recipe should complete')
})
