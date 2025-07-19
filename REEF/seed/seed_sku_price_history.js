const { faker } = require('@faker-js/faker');
const getClient = require('./db');

const ENTRY_COUNT = 500;

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log('Connected. Seeding sku_price_history...');

  // 1. 프로모션 목록 가져오기
  const promoRes = await client.query(`SELECT promo_id, discount_value, discount_type, start_at, end_at FROM promotion`);
  const promotions = promoRes.rows;

  // 2. SKU 목록 가져오기
  const skuRes = await client.query(`SELECT sku_id, price FROM sku`);
  const skus = skuRes.rows;

  if (promotions.length === 0 || skus.length === 0) {
    console.error('🚨 프로모션 또는 SKU가 없습니다. 먼저 시드해주세요.');
    await client.end();
    return;
  }

  const usedPairs = new Set();

  let count = 0;
  while (count < ENTRY_COUNT) {
    const promo = faker.helpers.arrayElement(promotions);
    const sku = faker.helpers.arrayElement(skus);

    const key = `${promo.promo_id}-${sku.sku_id}`;
    if (usedPairs.has(key)) continue;
    usedPairs.add(key);

    const originalPrice = parseFloat(sku.price);

    // 할인 계산
    let discountPrice = originalPrice;
    if (promo.discount_type === 'percentage') {
      discountPrice = originalPrice * (1 - parseFloat(promo.discount_value) / 100);
    } else {
      discountPrice = originalPrice - parseFloat(promo.discount_value);
    }

    // 최소 가격 보장
    discountPrice = Math.max(discountPrice, 0);

    await client.query(`
      INSERT INTO sku_price_history (
        promo_id, sku_id, price, discount_price,
        start_at, end_at, is_stackable, created_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8
      )
    `, [
      promo.promo_id,
      sku.sku_id,
      originalPrice,
      discountPrice.toFixed(2),
      promo.start_at,
      promo.end_at,
      faker.datatype.boolean(),
      promo.start_at
    ]);

    count++;
  }

  console.log(`✅ ${ENTRY_COUNT} sku_price_history records inserted!`);
  await client.end();
};
