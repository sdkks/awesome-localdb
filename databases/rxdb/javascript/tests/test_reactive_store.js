/**
 * Tests for recipe_reactive_store.js
 *
 * Run: node --test tests/test_reactive_store.js
 */
const test = require('node:test');
const assert = require('node:assert');

test('recipe_reactive_store runs without error', async () => {
  const { main } = require('../src/recipe_reactive_store');

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

test('recipe_reactive_store produces expected output', async () => {
  const { main } = require('../src/recipe_reactive_store');

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
  assert.ok(fullOutput.includes('Reactive Query'), 'Should have reactive query section');
  assert.ok(fullOutput.includes('Chili con Carne'), 'Should include Chili con Carne');
  assert.ok(fullOutput.includes('Pad Thai'), 'Should include Pad Thai');
  assert.ok(fullOutput.includes('Green Curry'), 'Should include Green Curry');

  // Verify update
  assert.ok(fullOutput.includes('Updated Pad Thai'), 'Should show Pad Thai update');

  // Verify upsert
  assert.ok(fullOutput.includes('Upserted Focaccia'), 'Should show Focaccia upsert');
  assert.ok(fullOutput.includes('Focaccia'), 'Should include Focaccia in output');

  // Verify delete
  assert.ok(fullOutput.includes('Removed Ratatouille'), 'Should show Ratatouille removal');

  // Verify final state section
  assert.ok(fullOutput.includes('Total documents after operations'), 'Should have final count');
});
