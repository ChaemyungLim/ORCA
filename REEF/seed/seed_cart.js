const { faker } = require('@faker-js/faker');
const getClient = require('./db');

module.exports = async function () {
  const client = getClient();       // new client per file
  await client.connect();
  console.log("Connected. Seeding cart...");

  // 1. 유저 및 SKU 목록 불러오기 (user의 가입일 포함)
  const userRes = await client.query('SELECT user_id, created_at FROM users');
  const skuRes = await client.query('SELECT sku_id FROM sku');

  const users = userRes.rows;
  const sku = skuRes.rows;

  // 2. 전체 유저 중 90% 선택
  const sampledUsers = faker.helpers.arrayElements(users, Math.floor(users.length * 0.9));

  for (const user of sampledUsers) {
    const productCount = faker.number.int({ min: 1, max: 5 });
    const sampledSkus = faker.helpers.arrayElements(sku, productCount);

    for (const s of sampledSkus) {
      // 생성일: 가입일 기준 30일 내
      const createdAt = faker.date.between({
        from: user.created_at,
        to: new Date(new Date(user.created_at).getTime() + 30 * 24 * 60 * 60 * 1000)
      });

      // 수정일: 생성일 이후
      const updatedAt = faker.date.between({
        from: createdAt,
        to: new Date(createdAt.getTime() + 5 * 24 * 60 * 60 * 1000)
      });

      await client.query(`
        INSERT INTO cart (cart_id, user_id, sku_id, quantity, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6)
      `, [
        faker.string.uuid(),
        user.user_id,
        s.sku_id,
        faker.number.int({ min: 1, max: 10 }),
        createdAt,
        updatedAt
      ]);
    }
  }

  console.log("✅ Cart seeded successfully.");
  await client.end();
};
