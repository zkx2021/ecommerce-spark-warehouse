<template>
  <main class="dashboard-shell">
    <header class="dashboard-header">
      <div>
        <p class="dashboard-eyebrow">Spark + HDFS + Hive 离线数仓</p>
        <h1>电商经营分析大屏</h1>
      </div>

      <form class="dashboard-controls" @submit.prevent="refreshDashboard">
        <label class="control-field">
          <span>业务日期</span>
          <input v-model="selectedDate" type="date" />
        </label>
        <button type="submit" :disabled="isLoading">
          {{ isLoading ? '加载中' : '刷新' }}
        </button>
        <label class="auto-refresh">
          <input v-model="autoRefresh" type="checkbox" />
          <span>自动刷新</span>
        </label>
        <StatusBadge :status="sourceStatus" />
      </form>
    </header>

    <section class="status-strip">
      <span>数据日期：{{ overview.date_id }}</span>
      <span>最近刷新：{{ lastRefreshLabel }}</span>
      <span v-if="lastError" class="status-strip__warning">{{ lastError }}</span>
    </section>

    <section class="kpi-grid" aria-label="核心指标">
      <KpiCard v-for="item in kpiCards" :key="item.label" v-bind="item" />
    </section>

    <section class="dashboard-grid" aria-label="经营分析图表">
      <div class="dashboard-column dashboard-column--side">
        <DashboardPanel title="品类销售占比" meta="按销售额">
          <BaseChart :option="categoryShareOption" height="250px" />
        </DashboardPanel>
        <DashboardPanel title="用户画像" meta="人群维度">
          <BaseChart :option="userProfileOption" height="250px" />
        </DashboardPanel>
      </div>

      <DashboardPanel title="销售趋势" meta="近 7 个周期" class="dashboard-panel--hero">
        <BaseChart :option="trendOption" height="560px" />
      </DashboardPanel>

      <div class="dashboard-column dashboard-column--side">
        <DashboardPanel title="商品销售排行" meta="TOP 5">
          <BaseChart :option="productRankOption" height="250px" />
        </DashboardPanel>
        <DashboardPanel title="转化漏斗" meta="曝光到支付">
          <BaseChart :option="funnelOption" height="250px" />
        </DashboardPanel>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import BaseChart from './components/BaseChart.vue'
import DashboardPanel from './components/DashboardPanel.vue'
import KpiCard from './components/KpiCard.vue'
import StatusBadge from './components/StatusBadge.vue'
import { mockAdsOverview } from './data/mockAds'
import { fetchAdsOverview } from './services/adsApi'
import { formatCount, formatDateTime, formatMoney, formatPercent } from './utils/formatters'

const selectedDate = ref('')
const overview = ref(mockAdsOverview)
const isLoading = ref(false)
const sourceStatus = ref('mock')
const lastError = ref('')
const lastRefreshAt = ref(new Date())
const autoRefresh = ref(false)
let refreshTimer = null
let refreshRequestId = 0

const chartTextColor = '#d7e2f2'
const mutedTextColor = '#8ea3bf'
const axisLineColor = '#25364f'
const palette = ['#2dd4bf', '#60a5fa', '#f59e0b', '#a78bfa', '#fb7185']

async function refreshDashboard() {
  const requestId = ++refreshRequestId
  isLoading.value = true
  try {
    const data = await fetchAdsOverview(selectedDate.value)
    if (requestId !== refreshRequestId) return
    overview.value = data
    sourceStatus.value = 'api'
    lastError.value = ''
    lastRefreshAt.value = new Date()
  } catch (error) {
    if (requestId !== refreshRequestId) return
    overview.value = mockAdsOverview
    sourceStatus.value = 'mock'
    lastError.value = '接口暂不可用，已切换为 Mock 数据'
    lastRefreshAt.value = new Date()
  } finally {
    if (requestId === refreshRequestId) {
      isLoading.value = false
    }
  }
}

watch(autoRefresh, (enabled) => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  if (enabled) {
    refreshTimer = setInterval(refreshDashboard, 60000)
  }
})

onMounted(refreshDashboard)

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})

const lastRefreshLabel = computed(() => formatDateTime(lastRefreshAt.value))

const kpiCards = computed(() => {
  const kpi = overview.value.kpi
  return [
    {
      label: '销售额',
      value: formatMoney(kpi.total_sales_amount),
      hint: `客单价 ${formatMoney(kpi.avg_order_amount)}`
    },
    {
      label: '订单数',
      value: formatCount(kpi.total_order_count),
      hint: `支付用户 ${formatCount(kpi.paid_user_count)}`
    },
    {
      label: '支付用户',
      value: formatCount(kpi.paid_user_count),
      hint: `转化率 ${formatPercent(kpi.payment_conversion_rate)}`
    },
    {
      label: '支付转化率',
      value: formatPercent(kpi.payment_conversion_rate),
      hint: `数据日期 ${overview.value.date_id}`
    }
  ]
})

const baseAxis = {
  axisLine: { lineStyle: { color: axisLineColor } },
  axisTick: { show: false },
  axisLabel: { color: mutedTextColor }
}

const baseGrid = {
  left: 42,
  right: 24,
  top: 42,
  bottom: 34,
  containLabel: true
}

const trendOption = computed(() => {
  const rows = overview.value.trend
  return {
    color: ['#2dd4bf', '#60a5fa', '#f59e0b'],
    tooltip: { trigger: 'axis' },
    legend: {
      top: 0,
      textStyle: { color: chartTextColor }
    },
    grid: baseGrid,
    xAxis: {
      type: 'category',
      data: rows.map((_, index) => `周期 ${index + 1}`),
      ...baseAxis
    },
    yAxis: [
      {
        type: 'value',
        name: '销售额',
        ...baseAxis,
        splitLine: { lineStyle: { color: 'rgba(142, 163, 191, 0.16)' } }
      },
      {
        type: 'value',
        name: '订单/用户',
        ...baseAxis,
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '销售额',
        type: 'line',
        smooth: true,
        data: rows.map((item) => item.sales_amount),
        areaStyle: { opacity: 0.12 }
      },
      {
        name: '订单数',
        type: 'bar',
        yAxisIndex: 1,
        data: rows.map((item) => item.order_count)
      },
      {
        name: '支付用户',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: rows.map((item) => item.paid_user_count)
      }
    ]
  }
})

const productRankOption = computed(() => {
  const rows = [...overview.value.product_rank].sort((a, b) => a.rank_no - b.rank_no)
  return {
    color: ['#60a5fa'],
    tooltip: { trigger: 'axis' },
    grid: { left: 92, right: 20, top: 18, bottom: 20 },
    xAxis: {
      type: 'value',
      ...baseAxis,
      splitLine: { lineStyle: { color: 'rgba(142, 163, 191, 0.14)' } }
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: rows.map((item) => item.product_name),
      ...baseAxis
    },
    series: [
      {
        name: '销售额',
        type: 'bar',
        data: rows.map((item) => item.sales_amount),
        barWidth: 14,
        label: {
          show: true,
          position: 'right',
          color: chartTextColor,
          formatter: ({ dataIndex }) => formatCount(rows[dataIndex].sales_quantity)
        }
      }
    ]
  }
})

const categoryShareOption = computed(() => ({
  color: palette,
  tooltip: {
    trigger: 'item',
    formatter: ({ data }) => `${data.name}<br/>销售额：${formatMoney(data.value)}<br/>占比：${formatPercent(data.salesShare)}`
  },
  legend: {
    bottom: 0,
    textStyle: { color: chartTextColor }
  },
  series: [
    {
      name: '品类销售占比',
      type: 'pie',
      radius: ['46%', '70%'],
      center: ['50%', '44%'],
      avoidLabelOverlap: true,
      label: {
        color: chartTextColor,
        formatter: ({ data }) => `${data.name}\n${formatPercent(data.salesShare)}`
      },
      data: overview.value.category_share.map((item) => ({
        name: item.category,
        value: item.sales_amount,
        salesShare: item.sales_share
      }))
    }
  ]
}))

const userProfileOption = computed(() => {
  const rows = overview.value.user_profile
  return {
    color: ['#a78bfa', '#2dd4bf'],
    tooltip: { trigger: 'axis' },
    legend: {
      top: 0,
      textStyle: { color: chartTextColor }
    },
    grid: { left: 42, right: 18, top: 42, bottom: 30, containLabel: true },
    xAxis: {
      type: 'category',
      data: rows.map((item) => `${item.dimension_type}:${item.dimension_value}`),
      ...baseAxis
    },
    yAxis: {
      type: 'value',
      ...baseAxis,
      splitLine: { lineStyle: { color: 'rgba(142, 163, 191, 0.14)' } }
    },
    series: [
      {
        name: '访问用户',
        type: 'bar',
        data: rows.map((item) => item.user_count)
      },
      {
        name: '购买用户',
        type: 'bar',
        data: rows.map((item) => item.buyer_count)
      }
    ]
  }
})

const funnelOption = computed(() => {
  const rows = [...overview.value.funnel].sort((a, b) => a.stage_order - b.stage_order)
  return {
    color: palette,
    tooltip: {
      trigger: 'item',
      formatter: ({ data }) => `${data.name}<br/>人数：${formatCount(data.value)}<br/>转化率：${formatPercent(data.conversionRate)}`
    },
    series: [
      {
        name: '转化漏斗',
        type: 'funnel',
        left: '8%',
        top: 12,
        bottom: 8,
        width: '84%',
        minSize: '28%',
        maxSize: '94%',
        sort: 'none',
        gap: 4,
        label: {
          color: chartTextColor,
          formatter: ({ data }) => `${data.name} ${formatPercent(data.conversionRate)}`
        },
        data: rows.map((item) => ({
          name: item.stage_name,
          value: item.stage_count,
          conversionRate: item.conversion_rate
        }))
      }
    ]
  }
})
</script>
