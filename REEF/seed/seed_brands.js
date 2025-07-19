const { faker } = require('@faker-js/faker');
const getClient = require('./db');

const brandMap = {
  'Electronics': ['삼성전자', 'LG전자', '애플', '소니', '샤오미'],
  'Fashion': ['나이키', '아디다스', '뉴발란스', '푸마', '리복'],
  'Home Appliances': ['쿠쿠', '다이슨', '발뮤다', '필립스', '일렉트로룩스'],
  'Books': ['문학동네', '민음사', '위즈덤하우스', '한겨레출판', '창비'],
  'Toys': ['레고', '영실업', '반다이', '타카라토미', '미미월드'],
  'Beauty': ['설화수', '라네즈', '이니스프리', '클리오', '미샤'],
  'Groceries': ['오뚜기', '농심', 'CJ', '풀무원', '동원'],
  'Furniture': ['한샘', '이케아', '일룸', '동서가구', '에이스침대'],
  'Sports': ['휠라', '데상트', '언더아머', '나이키', '캘러웨이'],
  'Automotive': ['불스원', '카렉스', '아이나비', '카템']
};

module.exports = async function () {
  const client = getClient();       // new client per file
  await client.connect();
  console.log("Connected to DB. Inserting brands...");

  const res = await client.query(`SELECT category_id, name FROM categories`);
  const categoryMap = {};
  res.rows.forEach(row => {
    categoryMap[row.name] = row.category_id;
  });

  for (const [categoryName, brandList] of Object.entries(brandMap)) {
    const categoryId = categoryMap[categoryName];
    for (const brand of brandList) {
      const brandId = faker.string.uuid();
      await client.query(`
        INSERT INTO brands (brand_id, category_id, brand_name, created_at, updated_at)
        VALUES ($1, $2, $3, NOW(), NOW())
      `, [brandId, categoryId, brand]);
    }
  }

  console.log("All brands inserted!");
  await client.end();
};