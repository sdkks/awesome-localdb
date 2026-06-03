/**
 * Tests for recipe_replication.js
 *
 * Run: node --test tests/test_replication.js
 */
const test = require('node:test');
const assert = require('node:assert');

test('recipe_replication runs without error', async () => {
  const { main } = require('../src/recipe_replication');

  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error('Recipe timed out')), 20000)
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

test('recipe_replication syncs data bidirectionally', async () => {
  const { main } = require('../src/recipe_replication');

  const outputs = [];
  const origLog = console.log;

  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      console.log = origLog;
      reject(new Error('Recipe timed out waiting for output'));
    }, 20000);

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

  // Verify seed messages
  assert.ok(fullOutput.includes('Remote seeded'), 'Should show remote seed');
  assert.ok(fullOutput.includes('Local seeded'), 'Should show local seed');

  // Verify replication
  assert.ok(fullOutput.includes('Replicating'), 'Should show replication start');
  assert.ok(fullOutput.includes('Initial replication complete'), 'Should complete initial replication');

  // After sync, both databases should have all recipes
  // (3 from remote seed + 2 from local seed)
  assert.ok(fullOutput.includes('Margherita Pizza'), 'Should include Margherita Pizza after sync');
  assert.ok(fullOutput.includes('Carbonara'), 'Should include Carbonara after sync');
  assert.ok(fullOutput.includes('Caprese Salad'), 'Should include Caprese Salad after sync');
  assert.ok(fullOutput.includes('Minestrone'), 'Should include Minestrone after sync');
  assert.ok(fullOutput.includes('Focaccia'), 'Should include Focaccia after sync');

  // Verify sections
  assert.ok(fullOutput.includes('Remote Database'), 'Should show remote database section');
  assert.ok(fullOutput.includes('Local Database'), 'Should show local database section');

  // Verify live change propagation
  assert.ok(fullOutput.includes('Tiramisu'), 'Should include Tiramisu during replication');
});
