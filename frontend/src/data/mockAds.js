export const mockAdsOverview = {
  date_id: '2026-07-01',
  kpi: {
    date_id: '2026-07-01',
    total_sales_amount: 1234567.89,
    total_order_count: 3420,
    paid_user_count: 1280,
    avg_order_amount: 361.0,
    payment_conversion_rate: 0.374
  },
  trend: [
    { sales_amount: 196000, order_count: 510, paid_user_count: 201 },
    { sales_amount: 238000, order_count: 620, paid_user_count: 244 },
    { sales_amount: 286000, order_count: 745, paid_user_count: 293 },
    { sales_amount: 324000, order_count: 830, paid_user_count: 336 },
    { sales_amount: 402000, order_count: 1010, paid_user_count: 410 },
    { sales_amount: 388000, order_count: 970, paid_user_count: 392 },
    { sales_amount: 456000, order_count: 1120, paid_user_count: 448 }
  ],
  product_rank: [
    { rank_no: 1, product_id: 1001, product_name: '无线机械键盘', category: '数码配件', sales_quantity: 920, sales_amount: 276000 },
    { rank_no: 2, product_id: 1002, product_name: '智能运动手表', category: '智能设备', sales_quantity: 760, sales_amount: 228000 },
    { rank_no: 3, product_id: 1003, product_name: '降噪蓝牙耳机', category: '影音娱乐', sales_quantity: 680, sales_amount: 204000 },
    { rank_no: 4, product_id: 1004, product_name: '便携咖啡机', category: '生活电器', sales_quantity: 540, sales_amount: 162000 },
    { rank_no: 5, product_id: 1005, product_name: '人体工学椅', category: '办公家居', sales_quantity: 390, sales_amount: 156000 }
  ],
  category_share: [
    { category: '数码配件', sales_amount: 356000, sales_quantity: 1320, sales_share: 0.288 },
    { category: '智能设备', sales_amount: 286000, sales_quantity: 940, sales_share: 0.232 },
    { category: '影音娱乐', sales_amount: 238000, sales_quantity: 880, sales_share: 0.193 },
    { category: '生活电器', sales_amount: 198000, sales_quantity: 650, sales_share: 0.16 },
    { category: '办公家居', sales_amount: 156567.89, sales_quantity: 420, sales_share: 0.127 }
  ],
  user_profile: [
    { dimension_type: 'age', dimension_value: '18-24', user_count: 420, buyer_count: 168, sales_amount: 160000 },
    { dimension_type: 'age', dimension_value: '25-34', user_count: 860, buyer_count: 412, sales_amount: 398000 },
    { dimension_type: 'age', dimension_value: '35-44', user_count: 610, buyer_count: 290, sales_amount: 286000 },
    { dimension_type: 'gender', dimension_value: 'female', user_count: 980, buyer_count: 462, sales_amount: 452000 },
    { dimension_type: 'gender', dimension_value: 'male', user_count: 910, buyer_count: 408, sales_amount: 398000 }
  ],
  funnel: [
    { stage_name: '曝光', stage_order: 1, stage_count: 12000, conversion_rate: 1 },
    { stage_name: '访问', stage_order: 2, stage_count: 6850, conversion_rate: 0.571 },
    { stage_name: '加购', stage_order: 3, stage_count: 2840, conversion_rate: 0.415 },
    { stage_name: '下单', stage_order: 4, stage_count: 1680, conversion_rate: 0.592 },
    { stage_name: '支付', stage_order: 5, stage_count: 1280, conversion_rate: 0.762 }
  ]
}
