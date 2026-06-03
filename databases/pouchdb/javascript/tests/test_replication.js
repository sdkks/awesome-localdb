/**
 * Tests for recipe_replication.js
 *
 * Run: node --test tests/test_replication.js
 */
const test = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const path = require('node:path');

test('recipe_replication runs without error', () => {
  const scriptPath = path.resolve(__dirname, '../src/recipe_replication.js');

  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 15000
  });

  assert.ok(result.includes('Done.'), 'Recipe should complete with Done.');
});

test('recipe_replication syncs data bidirectionally', () => {
  const scriptPath = path.resolve(__dirname, '../src/recipe_replication.js');

  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 15000
  });

  // Verify sync headers
  assert.ok(result.includes('Push complete'), 'Should show push completion');
  assert.ok(result.includes('Remote Database'), 'Should show remote database section');
  assert.ok(result.includes('Local Database'), 'Should show local database section');

  // After sync, both databases should have all 5 recipes
  assert.ok(result.includes('Margherita Pizza'), 'Should include Margherita Pizza after sync');
  assert.ok(result.includes('Carbonara'), 'Should include Carbonara after sync');
  assert.ok(result.includes('Minestrone'), 'Should include Minestrone after sync');
  assert.ok(result.includes('Focaccia'), 'Should include Focaccia after sync');

  // Live sync section
  assert.ok(result.includes('Starting live sync'), 'Should start live sync');
  assert.ok(result.includes('Tiramisu'), 'Should add Tiramisu during live sync');
  assert.ok(result.includes('Live sync cancelled'), 'Should cancel live sync');
});
