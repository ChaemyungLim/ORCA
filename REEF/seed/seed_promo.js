const { faker } = require('@faker-js/faker');
const getClient = require('./db');
const { v4: uuidv4 } = require('uuid');

const PROMO_COUNT = 100;

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log('Connected. Seeding promotions...');

  for (let i = 0; i < PROMO_COUNT; i++) {
    const promoId = uuidv4();
    const name = faker.company.catchPhrase(); // 랜덤한 프로모션 이름
    const discountType = faker.helpers.arrayElement(['fixed', 'percentage']);
    const discountValue =
      discountType === 'fixed'
        ? faker.number.float({ min: 5, max: 50, precision: 0.01 })
        : faker.number.float({ min: 5, max: 30, precision: 0.01 }); // %

    const startDate = faker.date.between({ from: '2024-01-01', to: '2024-12-01' });
    const endDate = faker.date.soon({ days: 30, refDate: startDate });

    await client.query(`
      INSERT INTO promotion (
        promo_id, name, discount_value, discount_type, start_at, end_at
      ) VALUES ($1, $2, $3, $4, $5, $6)
    `, [
      promoId,
      name,
      discountValue,
      discountType,
      startDate,
      endDate
    ]);
  }

  console.log(`✅ ${PROMO_COUNT} promotions inserted!`);
  await client.end();
};
