const { faker } = require('@faker-js/faker');
const getClient = require('./db');

module.exports = async function () {
  const client = getClient();  
  await client.connect();
  console.log("Connected. Generating payment & shipping for orders...");

  // 주문 목록 가져오기 → created_at 포함
  const ordersRes = await client.query(`
  SELECT o.order_id, o.total_amount, o.created_at,
         c.discount_amount, c.discount_rate
  FROM orders o
  LEFT JOIN coupon_usage u ON o.order_id = u.order_id
  LEFT JOIN coupon c ON u.coupon_id = c.coupon_id
`);
  const orders = ordersRes.rows;

  for (let i = 0; i < orders.length; i++) {
    const order = orders[i];

    // 쿠폰 적용 금액 계산
    let discount = 0;
    if (order.discount_amount != null && order.discount_amount > 0) {
      discount = parseFloat(order.discount_amount);
    } else if (order.discount_rate && order.discount_rate > 0) {
      discount = order.total_amount * (order.discount_rate / 100);
    }
    const finalAmount = Math.max(0, order.total_amount - discount);
    
    // 1. 결제일 생성 (주문일 이후)
    const isFastPayment = Math.random() < 0.9;
    const paymentDate = faker.date.between({
      from: order.created_at,
      to: new Date(new Date(order.created_at).getTime() + (isFastPayment ? 1 : 3) * 24 * 60 * 60 * 1000)
    });

    // 2. 결제 상태 설정
    let paymentStatus = 'COMPLETED';
    if (!isFastPayment) {
      paymentStatus = faker.helpers.arrayElement(['COMPLETED', 'PENDING']);
    }
    const now = new Date();
    const daysSincePayment = (now - paymentDate) / (1000 * 60 * 60 * 24);
    if (paymentStatus === 'PENDING' && daysSincePayment > 7) {
      paymentStatus = 'FAILED';
    }

    // 3. 주문 상태 설정
    let orderStatus = 'PLACED';
    if (paymentStatus === 'FAILED') orderStatus = 'CANCELLED';

    // 4. 배송 정보 (COMPLETED만)
    let shippingInsert = false;
    let shippingData = null;

    if (paymentStatus === 'COMPLETED') {
      shippingInsert = true;
      const shippingId = faker.string.uuid();
      const carrier = faker.helpers.arrayElement(['CJ대한통운', '한진택배', '롯데택배', '우체국택배']);
      const status = faker.helpers.arrayElement(['SHIPPED', 'DELIVERED']);
      const trackingNumber = faker.string.alphanumeric({ length: 12 });

      const isFastShipping = Math.random() < 0.9;
      const shippedAt = faker.date.between({
        from: paymentDate,
        to: new Date(paymentDate.getTime() + (isFastShipping ? 2 : 14) * 24 * 60 * 60 * 1000)
      });

      let deliveredAt = null;
      if (status === 'DELIVERED') {
        const isFastDelivery = Math.random() < 0.9;
        deliveredAt = faker.date.between({
          from: shippedAt,
          to: new Date(shippedAt.getTime() + (isFastDelivery ? 2 : 5) * 24 * 60 * 60 * 1000)
        });
      }

      shippingData = {
        shippingId,
        carrier,
        status,
        shippedAt,
        deliveredAt,
        trackingNumber
      };
    }

    try {
      // 주문 상태 업데이트
      await client.query(`
        UPDATE orders
        SET order_status = $1, discount_amount = $2, updated_at = NOW()
        WHERE order_id = $3
      `, [orderStatus, discount, order.order_id]);

      // 결제 insert
      await client.query(`
        INSERT INTO payment (
          payment_id, order_id, payment_method, payment_status, amount, payment_date
        ) VALUES ($1, $2, $3, $4, $5, $6)
      `, [
        faker.string.uuid(),
        order.order_id,
        faker.helpers.arrayElement(['CARD', 'BANK', 'KAKAO', 'NAVER']),
        paymentStatus,
        finalAmount,
        paymentDate
      ]);

      // 배송 insert
      if (shippingInsert && shippingData) {
        await client.query(`
          INSERT INTO shipping (
            shipping_id, order_id, tracking_number, carrier, status,
            shipped_at, delivered_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [
          shippingData.shippingId,
          order.order_id,
          shippingData.trackingNumber,
          shippingData.carrier,
          shippingData.status,
          shippingData.shippedAt,
          shippingData.deliveredAt
        ]);
      }

    } catch (err) {
      console.error(`Error processing order ${order.order_id}: ${err.message}`);
    }

    if (i % 500 === 0) {
      console.log(`Processed ${i} orders...`);
    }
  }

  console.log("✅ All payment & shipping records inserted!");
  await client.end();
};
