/**
 * Recipe: Mobile Store
 * Database: Realm
 * Description: Demonstrates schema definition, CRUD operations, filtered queries,
 *              and real-time reactive change listeners for a mobile product store.
 *              Uses an in-memory Realm for clean Node.js execution.
 *
 * Usage: node src/recipe_mobile_store.js
 */

const Realm = require('realm');

// ── Schemas ───────────────────────────────────────────────────────────────

const ProductSchema = {
  name: 'Product',
  primaryKey: 'id',
  properties: {
    id: 'int',
    name: 'string',
    price: 'double',
    inStock: 'bool',
    category: 'string',
    sku: 'string'
  }
};

const OrderSchema = {
  name: 'Order',
  primaryKey: 'id',
  properties: {
    id: 'int',
    productId: 'int',
    quantity: 'int',
    total: 'double',
    placedAt: 'date',
    status: { type: 'string', default: 'pending' }
  }
};

// ── Main ──────────────────────────────────────────────────────────────────

async function main() {
  // 1. Open a Realm (in-memory for clean test runs)
  const realm = new Realm({
    schema: [ProductSchema, OrderSchema],
    inMemory: true
  });

  // 2. Insert products
  realm.write(() => {
    realm.create('Product', { id: 1, name: 'Wireless Earbuds', price: 79.99, inStock: true, category: 'Electronics', sku: 'ELEC-001' });
    realm.create('Product', { id: 2, name: 'Running Shoes', price: 129.50, inStock: true, category: 'Apparel', sku: 'APP-001' });
    realm.create('Product', { id: 3, name: 'Coffee Maker', price: 89.00, inStock: false, category: 'Kitchen', sku: 'KIT-001' });
    realm.create('Product', { id: 4, name: 'USB-C Hub', price: 45.99, inStock: true, category: 'Electronics', sku: 'ELEC-002' });
    realm.create('Product', { id: 5, name: 'Yoga Mat', price: 29.99, inStock: true, category: 'Apparel', sku: 'APP-002' });
  });
  console.log(`Inserted ${realm.objects('Product').length} products.`);

  // 3. Query: find all in-stock products under $50
  const affordableInStock = realm.objects('Product')
    .filtered('inStock == true AND price < 50.0');
  console.log(`Affordable products in stock: ${affordableInStock.map(p => p.name).join(', ')}`);

  // 4. Query: find all Electronics
  const electronics = realm.objects('Product').filtered('category == $0', 'Electronics');
  console.log(`Electronics: ${electronics.map(p => `${p.name} ($${p.price})`).join(', ')}`);

  // 5. Place orders in a write transaction
  realm.write(() => {
    realm.create('Order', {
      id: 100, productId: 1, quantity: 2, total: 159.98,
      placedAt: new Date(), status: 'confirmed'
    });
    realm.create('Order', {
      id: 101, productId: 4, quantity: 1, total: 45.99,
      placedAt: new Date(), status: 'pending'
    });
  });
  console.log(`Placed ${realm.objects('Order').length} orders.`);

  // 6. Reactive change listener on orders
  const allOrders = realm.objects('Order');
  let listenerFired = false;

  allOrders.addListener((orders, changes) => {
    const statuses = orders.map(o => `#${o.id} ${o.status}`).join(', ');
    listenerFired = true;
    console.log(`  [Listener] Orders updated: ${statuses}`);
  });

  // 7. Update order status inside a write transaction
  realm.write(() => {
    const order = realm.objectForPrimaryKey('Order', 101);
    order.status = 'shipped';
  });
  console.log('Updated Order #101 to shipped');

  // 8. Delete completed orders
  realm.write(() => {
    const confirmed = realm.objects('Order').filtered('status == $0', 'confirmed');
    realm.delete(confirmed);
  });
  console.log('Deleted confirmed orders');

  // 9. Show final state
  const remainingOrders = realm.objects('Order');
  console.log(`\nFinal state: ${realm.objects('Product').length} products, ${remainingOrders.length} orders`);
  remainingOrders.forEach(o => {
    const product = realm.objectForPrimaryKey('Product', o.productId);
    console.log(`  Order #${o.id}: ${product.name} x${o.quantity} — ${o.status}`);
  });
  console.log(`Listener fired: ${listenerFired}`);

  // 10. Clean up
  allOrders.removeAllListeners();
  realm.close();
  console.log('Done.');
}

if (require.main === module) {
  main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
}

module.exports = { main };
