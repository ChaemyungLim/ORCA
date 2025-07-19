const { faker } = require('@faker-js/faker');
const getClient = require('./db');
const { v4: uuidv4 } = require('uuid');

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log('Connected. Seeding coupons with promotion linkage...');

  // 1. 프로모션 목록 불러오기
  const promoRes = await client.query(`SELECT promo_id, discount_value, discount_type, start_at, end_at FROM promotion`);
  const promotions = promoRes.rows;

  if (promotions.length === 0) {
    console.error('🚨 No promotions found. Please seed them first.');
    await client.end();
    return;
  }

  const couponList = [];

  for (let i = 0; i < promotions.length; i++) {
    const promo = promotions[i];
    const isPercentage = promo.discount_type === 'PERCENTAGE';

    const discountAmount = isPercentage ? 0 : promo.discount_value;
    const discountRate = isPercentage ? promo.discount_value : 0;

    couponList.push({
      coupon_id: uuidv4(),
      code: `PROMO${i + 1}`,
      description: isPercentage
        ? `${promo.discount_value}% 할인 쿠폰`
        : `₩${promo.discount_value} 할인 쿠폰`,
      discount_amount: discountAmount,
      discount_rate: discountRate,
      min_order_amount: isPercentage
        ? faker.number.int({ min: 10000, max: 50000 })
        : 0,
      expiration_date: promo.end_at,
      promo_id: promo.promo_id
    });
  }

  // 2. DB insert
  for (const c of couponList) {
    await client.query(`
      INSERT INTO coupon (
        coupon_id, code, description,
        discount_amount, discount_rate,
        min_order_amount, expiration_date,
        is_active, promo_id
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, false, $8)
    `, [
      c.coupon_id,
      c.code,
      c.description,
      c.discount_amount,
      c.discount_rate,
      c.min_order_amount,
      c.expiration_date,
      c.promo_id
    ]);
  }

  console.log(`✅ ${couponList.length} coupons inserted and linked with promotions!`);
  await client.end();
};
