const { faker } = require('@faker-js/faker');
const getClient = require('./db');

const ORDER_COUNT = 10000;

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log("Connected. Seeding orders + order_items...");

  // 1. user_id 목록
  const userRes = await client.query(`SELECT user_id FROM users`);
  const userIds = userRes.rows.map(row => row.user_id);

  // 2. sku + product 생성일 정보
  const skuRes = await client.query(`
    SELECT s.sku_id, s.price, p.created_at AS product_created_at
    FROM sku s
    JOIN products p ON s.product_id = p.product_id
  `);
  const skus = skuRes.rows;

  for (let i = 0; i < ORDER_COUNT; i++) {
    const orderId = faker.string.uuid();
    const userId = faker.helpers.arrayElement(userIds);
    const itemCount = faker.number.int({ min: 1, max: 5 });

    // 주문할 SKU 선택
    const selectedSkus = faker.helpers.arrayElements(skus, itemCount);

    // 주문 가능한 최소 시점은 가장 오래된 product_created_at 이후
    const earliestProductCreated = selectedSkus.reduce((earliest, sku) => {
      return new Date(sku.product_created_at) > earliest
        ? new Date(sku.product_created_at)
        : earliest;
    }, new Date(selectedSkus[0].product_created_at));

    const orderCreatedAt = faker.date.between({
      from: earliestProductCreated,
      to: new Date()
    });

    const orderItems = [];
    let totalAmount = 0;

    for (const sku of selectedSkus) {
      const quantity = faker.number.int({ min: 1, max: 3 });
      const unitPrice = parseFloat(sku.price);
      const itemTotal = unitPrice * quantity;

      totalAmount += itemTotal;

      orderItems.push({
        order_item_id: faker.string.uuid(),
        sku_id: sku.sku_id,
        quantity,
        unit_price: unitPrice
      });
    }

    try {
      // 주문 테이블
      await client.query(`
        INSERT INTO orders (
          order_id, user_id, order_status, total_amount,
          discount_amount, point_used, created_at, updated_at
        ) VALUES (
          $1, $2, 'PLACED', $3, 0, 0, $4, $4
        )
      `, [orderId, userId, totalAmount, orderCreatedAt]);

      // 주문 아이템
      for (const item of orderItems) {
        await client.query(`
          INSERT INTO order_items (
            order_item_id, order_id, quantity,
            unit_price, created_at, updated_at, sku_id
          ) VALUES (
            $1, $2, $3, $4, $5, $5, $6
          )
        `, [
          item.order_item_id,
          orderId,
          item.quantity,
          item.unit_price,
          orderCreatedAt,
          item.sku_id
        ]);
      }

    } catch (err) {
      console.error(`❌ Error at order ${i}: ${err.message}`);
    }

    if (i % 500 === 0) console.log(`Inserted ${i} orders...`);
  }

  console.log("✅ All orders + order_items inserted!");
  await client.end();
};
