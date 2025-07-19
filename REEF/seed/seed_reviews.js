const { faker } = require('@faker-js/faker');
const getClient = require('./db');
const { v4: uuidv4 } = require('uuid');

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log("Connected. Seeding reviews...");

  // 1. 유저 활동성 맵 조회
  const userRes = await client.query('SELECT user_id, is_active FROM users');
  const userMap = {};
  for (const row of userRes.rows) userMap[row.user_id] = row.is_active;

  // 2. 주문 + 상품 정보 기반 리뷰 생성
  const orderItemRes = await client.query(`
    SELECT o.user_id, oi.sku_id, oi.unit_price, oi.quantity, s.product_id
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN sku s ON oi.sku_id = s.sku_id
  `);

  const usedPairs = new Set();
  let count = 0;

  function sigmoid(x) {
    return 1 / (1 + Math.exp(-x));
  }

  for (const row of orderItemRes.rows) {
    const { user_id, unit_price, quantity, product_id } = row;
    const key = `${user_id}-${product_id}`;
    if (usedPairs.has(key)) continue;
    usedPairs.add(key);

    const is_active = userMap[user_id];
    const order_total = unit_price * quantity;
    const log_total = Math.log(order_total + 1); // scale

    // 리뷰 생성 확률 = sigmoid(0.5 * is_active + 0.1 * log(order_total))
    const reviewProb = sigmoid((is_active ? 0.5 : -0.5) + 0.1 * log_total);
    if (Math.random() > reviewProb) continue;

    // 점수 생성 (활성 유저 + 고액 구매일수록 점수 높음)
    let score = Math.round(sigmoid((is_active ? 1 : 0) + 0.05 * log_total + faker.number.float({ min: -1, max: 1 })) * 5);
    score = Math.max(1, Math.min(5, score));

    await client.query(`
      INSERT INTO review (review_id, product_id, user_id, title, content, score)
      VALUES ($1, $2, $3, $4, $5, $6)
    `, [
      uuidv4(),
      product_id,
      user_id,
      faker.lorem.sentence(5),
      faker.lorem.paragraph(),
      score
    ]);

    count++;
    if (count >= 3000) break;
  }

  console.log(`✅ ${count} reviews inserted based on activity and order amount.`);
  await client.end();
};