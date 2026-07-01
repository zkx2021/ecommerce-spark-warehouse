<template>
  <main class="dashboard">
    <header class="dashboard__header">
      <p class="eyebrow">Ecommerce Spark Warehouse</p>
      <h1>电商经营分析大屏</h1>
      <p class="subtitle">Spark + HDFS + Hive 离线数仓指标展示</p>
    </header>

    <section class="kpi-grid" aria-label="核心指标">
      <article v-for="item in kpis" :key="item.label" class="kpi-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>
  </main>
</template>

<script setup>
const kpis = [
  { label: '销售额', value: '0.00' },
  { label: '订单数', value: '0' },
  { label: '支付用户', value: '0' },
  { label: '转化率', value: '0%' }
]
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  padding: 32px;
  background: #07111f;
  color: #eef5ff;
  font-family: "Microsoft YaHei", system-ui, sans-serif;
}

.dashboard__header {
  margin-bottom: 28px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #26d9c7;
  font-size: 14px;
}

h1 {
  margin: 0;
  font-size: 32px;
}

.subtitle {
  margin: 10px 0 0;
  color: #9fb1c9;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.kpi-card {
  border: 1px solid #2b4262;
  border-radius: 8px;
  padding: 18px;
  background: #101b2e;
}

.kpi-card span {
  display: block;
  color: #9fb1c9;
  font-size: 14px;
}

.kpi-card strong {
  display: block;
  margin-top: 10px;
  font-size: 28px;
}

@media (max-width: 860px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .dashboard {
    padding: 20px;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
