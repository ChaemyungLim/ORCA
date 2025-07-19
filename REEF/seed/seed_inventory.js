const { faker } = require('@faker-js/faker');
const getClient = require('./db');

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log("Connected. Seeding inventory...");

  // sku_id와 available_from을 같이 가져옴
  const result = await client.query(`
    SELECT sku_id, available_from
    FROM sku
  `);
  const skus = result.rows;

  for (const s of skus) {
    // available_from 이후 1~5일 이내 날짜 생성
    let lastUpdated = s.available_from;
    if (new Date(s.available_from) < new Date('2024-12-31')) {
      lastUpdated = faker.date.between({
        from: s.available_from,
        to: new Date('2024-12-31')
      });
}

    await client.query(`
      INSERT INTO inventory (inventory_id, sku_id, quantity, last_updated)
      VALUES ($1, $2, $3, $4)
    `, [
      faker.string.uuid(),
      s.sku_id,
      faker.number.int({ min: 0, max: 1000 }),
      lastUpdated
    ]);
  }

  console.log("✅ Inventory seeded successfully.");
  await client.end();
};
