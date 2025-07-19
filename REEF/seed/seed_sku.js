const { faker } = require('@faker-js/faker');
const getClient = require('./db');
const { v4: uuidv4 } = require('uuid');

const COLORS = ['Black', 'White', 'Red', 'Blue', 'Green', 'Gray'];
const OPTIONS = ['64GB', '128GB', '256GB', 'Small', 'Medium', 'Large'];
const VARIANT_NAMES = ['Standard', 'Pro', 'Lite', 'Plus'];

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log('Connected. Seeding skus...');

  const resProducts = await client.query('SELECT product_id FROM products');
  const products = resProducts.rows;

  if (products.length === 0) {
    console.error('🚨 No products found. Please seed products first.');
    await client.end();
    return;
  }

  const usedSkuCodes = new Set();
  let count = 0;

  while (count < 1000) {
    const product = faker.helpers.arrayElement(products);
    const brand = faker.string.alpha(4).toUpperCase();
    const prod = faker.string.alpha(4).toUpperCase();
    const color = faker.string.alpha(4).toUpperCase();
    const option = faker.string.alpha(4).toUpperCase();

    const skuCode = `${brand}-${prod}-${color}-${option}`;
    if (usedSkuCodes.has(skuCode)) continue;
    usedSkuCodes.add(skuCode);

    const variant = faker.helpers.arrayElement(VARIANT_NAMES) + ' ' + option;

    await client.query(`
        INSERT INTO sku (sku_id, product_id, sku_code, variant_name, color, option, price)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
      `, [
        uuidv4(),
        product.product_id,
        skuCode,
        variant,
        color,
        option,
        faker.number.float({ min: 10, max: 500, precision: 0.01 })
      ]);

    count++;
  }

  console.log('✅ 1000 skus inserted!');
  await client.end();
};
