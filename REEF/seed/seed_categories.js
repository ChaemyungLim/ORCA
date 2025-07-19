const { faker } = require('@faker-js/faker');
const getClient = require('./db'); 

const categoryNames = [
  'Electronics',
  'Fashion',
  'Home Appliances',
  'Books',
  'Toys',
  'Beauty',
  'Groceries',
  'Furniture',
  'Sports',
  'Automotive'
];

module.exports = async function () {
  const client = getClient();       // new client per file
  await client.connect();
  console.log(`Connected. Inserting ${categoryNames.length} categories...`);

  for (const name of categoryNames) {
    const categoryId = faker.string.uuid(); // UUID
    const description = faker.commerce.productDescription();

    try {
      await client.query(`
        INSERT INTO categories (
          category_id, name, description, created_at, updated_at
        ) VALUES ($1, $2, $3, NOW(), NOW())
      `, [categoryId, name, description]);
    } catch (err) {
      console.error(`Error inserting category "${name}": ${err.message}`);
    }
  }

  console.log("All categories inserted!");
  await client.end();
};