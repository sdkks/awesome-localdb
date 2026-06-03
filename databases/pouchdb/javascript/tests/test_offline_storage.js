/**
 * Tests for recipe_offline_storage.js
 *
 * Run: node --test tests/test_offline_storage.js
 */
const test = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const path = require('node:path');

test('recipe_offline_storage runs without error', () => {
  const scriptPath = path.resolve(__dirname, '../src/recipe_offline_storage.js');

  // Run the recipe as a subprocess so deprecation warnings don't
  // interfere with the test runner's output capture.
  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 10000
  });

  assert.ok(result.includes('Done.'), 'Recipe should complete with Done.');
});

test('recipe_offline_storage produces expected output', () => {
  const scriptPath = path.resolve(__dirname, '../src/recipe_offline_storage.js');

  const result = execSync(`node "${scriptPath}"`, {
    encoding: 'utf-8',
    timeout: 10000
  });

  // Verify section headers
  assert.ok(result.includes('Mexican Recipes'), 'Should have Mexican Recipes section');
  assert.ok(result.includes('Recipes by Cuisine'), 'Should have Recipes by Cuisine section');
  assert.ok(result.includes('Quick Meals'), 'Should have Quick Meals section');

  // Verify data presence
  assert.ok(result.includes('Chili con Carne'), 'Should include Chili con Carne');
  assert.ok(result.includes('Pad Thai'), 'Should include Pad Thai');
  assert.ok(result.includes('Green Curry'), 'Should include Green Curry');
});
