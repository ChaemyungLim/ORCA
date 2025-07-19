const { faker } = require('@faker-js/faker');
const getClient = require('./db');
const { v4: uuidv4 } = require('uuid');

const TRANSACTION_COUNT = 2000;

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log('Connected. Seeding point transactions...');

  // 유저 목록 가져오기
  const userRes = await client.query(`SELECT user_id FROM users`);
  const users = userRes.rows;

  if (users.length === 0) {
    console.error('🚨 No users found. Please seed them first.');
    await client.end();
    return;
  }

  // 2. payment 기반 earn 포인트 적립
  const paymentRes = await client.query(`
    SELECT p.order_id, p.amount, o.user_id, p.payment_date
    FROM payment p
    JOIN orders o ON p.order_id = o.order_id
    WHERE p.payment_status = 'COMPLETED'
  `);
  const payments = paymentRes.rows;

  let count = 0;

  const REASONS = {
    earn: ['회원가입 적립', '리뷰 작성 보상', '구매 적립', '이벤트 참여'],
    spend: ['주문 사용', '쿠폰 교환', '배송비 차감']
  };

  let paymentCount = 0;
  for (const p of payments) {
    const point = Math.floor(p.amount * 0.01); // 1% 적립
    if (point <= 0) continue;

    await client.query(`
      INSERT INTO point_transaction (
        transaction_id, user_id, point_change,
        reason, transaction_at, type
      ) VALUES ($1, $2, $3, $4, $5, 'earn')
    `, [
      uuidv4(),
      p.user_id,
      point,
      '구매 적립',
      p.payment_date
    ]);

    paymentCount++;
  }

  console.log(`✅ ${paymentCount} earned transactions inserted from payment.`);

  for (let i = 0; i < TRANSACTION_COUNT; i++) {
    const user = faker.helpers.arrayElement(users);
    const isEarn = faker.datatype.boolean();
    const type = isEarn ? 'earn' : 'spend';

    const pointChange = faker.number.float({
      min: 100,
      max: 10000,
      precision: 1
    });

    const amount = isEarn ? pointChange : -pointChange;

    await client.query(`
      INSERT INTO point_transaction (
        transaction_id, user_id, point_change,
        reason, transaction_at, type
      ) VALUES ($1, $2, $3, $4, $5, $6)
    `, [
      uuidv4(),
      user.user_id,
      amount,
      faker.helpers.arrayElement(REASONS[type]),
      faker.date.between({ from: '2023-01-01', to: '2025-01-01' }),
      type
    ]);

    if (i % 500 === 0) console.log(`Inserted ${i} transactions...`);
  }

  console.log(`✅ ${TRANSACTION_COUNT} point transactions inserted!`);
  await client.end();
};
