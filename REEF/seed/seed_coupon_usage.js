const { faker } = require('@faker-js/faker');
const getClient = require('./db');

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log("Connected. Seeding coupon_usage...");

  const resUserCoupons = await client.query(`
    SELECT uc.id AS user_coupon_id, uc.user_id, uc.coupon_id
    FROM user_coupons uc
    WHERE is_used = false
  `);

  const resOrders = await client.query('SELECT order_id FROM orders');
  const orders = resOrders.rows.map(row => row.order_id);

  const usageData = [];

  for (let i = 0; i < 300; i++) {
    const uc = faker.helpers.arrayElement(resUserCoupons.rows);
    const order_id = faker.helpers.arrayElement(orders);

    usageData.push({
      usage_id: faker.string.uuid(),
      coupon_id: uc.coupon_id,
      user_id: uc.user_id,
      order_id,
      used_at: faker.date.recent({ days: 20 })
    });

    // user_coupons 테이블에서 is_used true로 설정도 함께 진행
    await client.query(`
      UPDATE user_coupons SET is_used = true WHERE user_id = $1 AND coupon_id = $2
    `, [uc.user_id, uc.coupon_id]);
  }

  for (const usage of usageData) {
    await client.query(`
      INSERT INTO coupon_usage (
        usage_id, coupon_id, user_id, order_id, used_at
      ) VALUES ($1, $2, $3, $4, $5)
    `, [
      usage.usage_id,
      usage.coupon_id,
      usage.user_id,
      usage.order_id,
      usage.used_at
    ]);
  }

  console.log("All coupon_usage inserted!");
  await client.end();
};