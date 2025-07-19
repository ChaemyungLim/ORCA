const { faker } = require('@faker-js/faker');
const getClient = require('./db');
const { v4: uuidv4 } = require('uuid');

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log("Connected. Seeding user_coupons...");

  // 유저 목록 + is_active 조회
  const resUsers = await client.query('SELECT user_id, is_active FROM users');
  const userMap = {};
  resUsers.rows.forEach(row => {
    userMap[row.user_id] = row.is_active;
  });
  const users = Object.keys(userMap);

  // 쿠폰 + 프로모션 매핑
  const resCoupons = await client.query(`
    SELECT coupon_id, promo_id FROM coupon
  `);

  const couponMap = {}; // coupon_id → { start_at, end_at }

  for (const row of resCoupons.rows) {
    if (!row.promo_id) continue;

    const promoRes = await client.query(`
      SELECT start_at, end_at FROM promotion
      WHERE promo_id = $1
    `, [row.promo_id]);

    const promo = promoRes.rows[0];
    if (!promo) continue;

    couponMap[row.coupon_id] = {
      start_at: promo.start_at,
      end_at: promo.end_at
    };
  }

  const assignments = [];

  for (const coupon_id of Object.keys(couponMap)) {
    const { start_at, end_at } = couponMap[coupon_id];

    // 유효한 범위일 경우에만 진행
    if (new Date(start_at) >= new Date(end_at)) {
      console.warn(`⏭️ Skipping coupon ${coupon_id} (invalid promotion date range)`);
      continue;
    }

    const sampledUsers = faker.helpers.arrayElements(users, 100); // 쿠폰당 100명

    for (const user_id of sampledUsers) {
      const assignedAt = faker.date.between({
        from: start_at,
        to: end_at
      });

      const is_active = userMap[user_id];
      const is_used = Math.random() < (is_active ? 0.6 : 0.2); // 활성 유저일수록 쿠폰 사용 확률 높음

      assignments.push({
        id: uuidv4(),
        user_id,
        coupon_id,
        assigned_at: assignedAt,
        is_used: false,
      });
    }
  }

  // DB insert
  for (const u of assignments) {
    await client.query(`
      INSERT INTO user_coupons (
        id, user_id, coupon_id, assigned_at, is_used
      ) VALUES ($1, $2, $3, $4, $5)
    `, [
      u.id,
      u.user_id,
      u.coupon_id,
      u.assigned_at,
      u.is_used
    ]);
  }

  console.log(`✅ ${assignments.length} user_coupons inserted!`);
  await client.end();
};
