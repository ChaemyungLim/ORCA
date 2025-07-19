const { faker } = require('@faker-js/faker');
const getClient = require('./db');
const { v4: uuidv4 } = require('uuid');

const USER_COUNT = 10000;
const usernameSet = new Set();
const emailSet = new Set();
// const phonePool = [];  

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log(`Connected. Seeding ${USER_COUNT} users...`);

  const emailsUsed = new Set();
  const usernamesUsed = new Set();

  const today = new Date();

  function sigmoid(x) {
    return 1 / (1 + Math.exp(-x));
  }

  for (let i = 0; i < 1000; i++) {
    const user_id = uuidv4();

    // 1%는 email/username 중복 허용
    const useDuplicate = Math.random() < 0.01;

    const email = useDuplicate
      ? faker.helpers.arrayElement([...emailsUsed])
      : faker.internet.email();
    const username = useDuplicate
      ? faker.helpers.arrayElement([...usernamesUsed])
      : faker.internet.username();

    emailsUsed.add(email);
    usernamesUsed.add(username);

    // 10%는 일부 NULL 값 포함
    const name = Math.random() < 0.1 ? null : faker.person.fullName();
    const address = Math.random() < 0.1 ? null : faker.location.streetAddress();
    const phone = Math.random() < 0.1 ? null : faker.phone.number();

    // 인과 구조 기반 생성
    const signup_days_ago = faker.number.int({ min: 0, max: 3 * 365 });
    const created_at = new Date(today.getTime() - signup_days_ago * 24 * 60 * 60 * 1000);

    const age = Math.round(faker.number.float({
      min: 20,
      max: 60,
      mean: 30 + 0.01 * signup_days_ago,
      stddev: 5
    }));

    const birth = new Date(
      today.getFullYear() - age,
      faker.number.int({ min: 0, max: 11 }),  // 수정된 부분: month는 0~11 정수
      faker.number.int({ min: 1, max: 28 })
);

    const is_active = Math.random() < sigmoid(-0.01 * signup_days_ago + faker.number.float({ min: -0.5, max: 0.5 }));

    await client.query(`
      INSERT INTO users (
        user_id, username, password, name, email, phone,
        birth, gender, address, is_active, created_at, updated_at, point_balance
      ) VALUES ($1, $2, $3, $4, $5, $6,
                $7, $8, $9, $10, $11, $12, $13)
    `, [
      user_id,
      username,
      'hashed-password',
      name,
      email,
      phone,
      birth,
      faker.helpers.arrayElement(['M', 'F', null]),
      address,
      is_active,
      created_at,
      created_at,
      0.0
    ]);
  }

  console.log("All users inserted!");
  await client.end();
};