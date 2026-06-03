/**
 * Tests for recipe_mobile_store.js
 *
 * Run: node --test tests/test_mobile_store.js
 */
const test = require('node:test');
const assert = require('node:assert');

test('recipe_mobile_store runs without error', async () => {
  const { main } = require('../src/recipe_mobile_store');

  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error('Recipe timed out')), 15000)
  );

  await Promise.race([
    new Promise((resolve, reject) => {
      const origLog = console.log;

      console.log = (...args) => {
        const msg = args.join(' ');
        if (msg === 'Done.' || msg === '\nDone.' || msg.endsWith('Done.')) {
          console.log = origLog;
          resolve();
        } else {
          origLog(...args);
        }
      };

      const origError = console.error;
      console.error = (...args) => {
        console.error = origError;
        console.log = origLog;
        reject(new Error(args.join(' ')));
      };

      main();
    }),
    timeout
  ]);

  assert.ok(true, 'Recipe completed without error');
});

test('recipe_mobile_store produces expected output', async () => {
  const { main } = require('../src/recipe_mobile_store');

  const outputs = [];
  const origLog = console.log;

  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      console.log = origLog;
      reject(new Error('Recipe timed out waiting for output'));
    }, 15000);

    console.log = (...args) => {
      const msg = args.join(' ');
      outputs.push(msg);
      if (msg === 'Done.' || msg === '\nDone.' || msg.endsWith('Done.')) {
        clearTimeout(timeout);
        console.log = origLog;
        resolve();
      } else {
        origLog(...args);
      }
    };

    const origError = console.error;
    console.error = (...args) => {
      clearTimeout(timeout);
      console.error = origError;
      console.log = origLog;
      reject(new Error(args.join(' ')));
    };

    main();
  });

  const fullOutput = outputs.join('\n');

  // Verify initial data
  assert.ok(fullOutput.includes('Inserted'), 'Should have insert message');
  assert.ok(fullOutput.includes('5 products'), 'Should show 5 products');
  assert.ok(fullOutput.includes('Affordable products'), 'Should show affordable products section');
  assert.ok(fullOutput.includes('USB-C Hub'), 'Should include USB-C Hub');
  assert.ok(fullOutput.includes('Yoga Mat'), 'Should include Yoga Mat');

  // Verify electronics query
  assert.ok(fullOutput.includes('Electronics:'), 'Should have Electronics section');
  assert.ok(fullOutput.includes('Wireless Earbuds'), 'Should include Wireless Earbuds');

  // Verify orders
  assert.ok(fullOutput.includes('Placed 2 orders'), 'Should show 2 orders placed');

  // Verify reactive listener
  assert.ok(fullOutput.includes('[Listener]'), 'Should show listener output');
  assert.ok(fullOutput.includes('Listener fired: true'), 'Should confirm listener fired');

  // Verify update
  assert.ok(fullOutput.includes('Updated Order #101'), 'Should show order update');

  // Verify delete
  assert.ok(fullOutput.includes('Deleted confirmed orders'), 'Should show delete message');

  // Verify final state
  assert.ok(fullOutput.includes('Final state:'), 'Should have final state section');
});
