# Vue ECharts Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Vue 3 and ECharts ecommerce operations dashboard that reads `/api/ads/overview`, falls back to mock ADS data when the API is unavailable, and presents a polished classic three-column cockpit screen.

**Architecture:** Keep the frontend layered and small: `App.vue` owns page state and layout, `services/adsApi.js` owns API calls, `data/mockAds.js` owns fallback data, `components/*` owns reusable visual pieces, `utils/formatters.js` owns display formatting, and `styles/dashboard.css` owns the screen styling. ECharts lifecycle is isolated in `BaseChart.vue`.

**Tech Stack:** Vue 3, Vite, ECharts 5, Node asset checks, existing Python backend asset checks.

---

## File Structure

- Modify `frontend/package.json`: add `test:assets` script.
- Create `frontend/tests/dashboard-assets.test.mjs`: lightweight Node asset/contract checks.
- Create `frontend/src/data/mockAds.js`: complete mock `OverviewResponse`.
- Create `frontend/src/services/adsApi.js`: API request helper for `/api/ads/overview`.
- Create `frontend/src/utils/formatters.js`: money, count, percent, and timestamp formatting.
- Create `frontend/src/components/BaseChart.vue`: ECharts lifecycle wrapper.
- Create `frontend/src/components/KpiCard.vue`: KPI display card.
- Create `frontend/src/components/StatusBadge.vue`: data-source and loading state badge.
- Create `frontend/src/components/DashboardPanel.vue`: reusable chart panel shell.
- Modify `frontend/src/App.vue`: dashboard composition, data loading, fallback, auto refresh, chart option builders.
- Create `frontend/src/styles/dashboard.css`: full dashboard visual and responsive styling.
- Modify `frontend/src/main.js`: import dashboard CSS.
- Modify `deploy/scripts/check.ps1`: include new frontend dashboard files.
- Modify `README.md`: describe active Vue/ECharts dashboard.

## Task 1: Frontend Data Contracts, Mock Data, API Service, and Formatters

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/tests/dashboard-assets.test.mjs`
- Create: `frontend/src/data/mockAds.js`
- Create: `frontend/src/services/adsApi.js`
- Create: `frontend/src/utils/formatters.js`

- [ ] **Step 1: Write failing asset tests**

Create `frontend/tests/dashboard-assets.test.mjs`:

```javascript
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const projectRoot = path.resolve(root, '..')

function read(relativePath) {
  return fs.readFileSync(path.join(projectRoot, relativePath), 'utf8')
}

function assertFile(relativePath) {
  assert.ok(fs.existsSync(path.join(projectRoot, relativePath)), `${relativePath} should exist`)
}

const packageJson = JSON.parse(read('frontend/package.json'))
assert.equal(packageJson.dependencies.vue, '3.4.29')
assert.equal(packageJson.dependencies.echarts, '5.5.0')
assert.equal(packageJson.scripts['test:assets'], 'node tests/dashboard-assets.test.mjs')

for (const file of [
  'frontend/src/data/mockAds.js',
  'frontend/src/services/adsApi.js',
  'frontend/src/utils/formatters.js'
]) {
  assertFile(file)
}

const mockSource = read('frontend/src/data/mockAds.js')
for (const section of ['kpi', 'trend', 'product_rank', 'category_share', 'user_profile', 'funnel']) {
  assert.match(mockSource, new RegExp(`${section}:`), `mock data should include ${section}`)
}

const apiSource = read('frontend/src/services/adsApi.js')
assert.match(apiSource, /\/api\/ads\/overview/)
assert.match(apiSource, /URLSearchParams/)
assert.match(apiSource, /throw new Error/)

const formatterSource = read('frontend/src/utils/formatters.js')
for (const exportName of ['formatMoney', 'formatCount', 'formatPercent', 'formatDateTime']) {
  assert.match(formatterSource, new RegExp(`export function ${exportName}`), `${exportName} should be exported`)
}

console.log('Dashboard asset checks passed.')
```

- [ ] **Step 2: Add the frontend test script**

Modify `frontend/package.json` scripts to:

```json
"scripts": {
  "dev": "vite --host 0.0.0.0",
  "build": "vite build",
  "preview": "vite preview --host 0.0.0.0",
  "test:assets": "node tests/dashboard-assets.test.mjs"
}
```

- [ ] **Step 3: Run the asset test to verify it fails**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
```

Expected: FAIL because `mockAds.js`, `adsApi.js`, and `formatters.js` do not exist yet.

- [ ] **Step 4: Add mock ADS overview data**

Create `frontend/src/data/mockAds.js`:

```javascript
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
```

- [ ] **Step 5: Add API request helper**

Create `frontend/src/services/adsApi.js`:

```javascript
const ADS_BASE_PATH = '/api/ads'

export async function fetchAdsOverview(date) {
  const params = new URLSearchParams()
  if (date) {
    params.set('date', date)
  }

  const query = params.toString()
  const url = `${ADS_BASE_PATH}/overview${query ? `?${query}` : ''}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`ADS overview request failed with status ${response.status}`)
  }

  return response.json()
}
```

- [ ] **Step 6: Add display formatters**

Create `frontend/src/utils/formatters.js`:

```javascript
export function formatMoney(value) {
  const numberValue = Number(value || 0)
  if (Math.abs(numberValue) >= 10000) {
    return `${(numberValue / 10000).toFixed(2)} 万`
  }
  return numberValue.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

export function formatCount(value) {
  return Number(value || 0).toLocaleString('zh-CN')
}

export function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`
}

export function formatDateTime(value = new Date()) {
  const date = value instanceof Date ? value : new Date(value)
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}
```

- [ ] **Step 7: Run data-layer checks**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
```

Expected: PASS with `Dashboard asset checks passed.`

- [ ] **Step 8: Commit**

Run:

```powershell
git add frontend/package.json frontend/tests/dashboard-assets.test.mjs frontend/src/data/mockAds.js frontend/src/services/adsApi.js frontend/src/utils/formatters.js
git commit -m "feat: add dashboard data contracts"
```

## Task 2: Reusable Dashboard Components

**Files:**
- Modify: `frontend/tests/dashboard-assets.test.mjs`
- Create: `frontend/src/components/BaseChart.vue`
- Create: `frontend/src/components/KpiCard.vue`
- Create: `frontend/src/components/StatusBadge.vue`
- Create: `frontend/src/components/DashboardPanel.vue`

- [ ] **Step 1: Extend asset tests for components**

Append this block to `frontend/tests/dashboard-assets.test.mjs` before the final `console.log`:

```javascript
for (const file of [
  'frontend/src/components/BaseChart.vue',
  'frontend/src/components/KpiCard.vue',
  'frontend/src/components/StatusBadge.vue',
  'frontend/src/components/DashboardPanel.vue'
]) {
  assertFile(file)
}

const baseChartSource = read('frontend/src/components/BaseChart.vue')
assert.match(baseChartSource, /echarts\/core/)
assert.match(baseChartSource, /ResizeObserver|resize/)
assert.match(baseChartSource, /dispose/)

const kpiCardSource = read('frontend/src/components/KpiCard.vue')
assert.match(kpiCardSource, /defineProps/)
assert.match(kpiCardSource, /label/)
assert.match(kpiCardSource, /value/)

const statusBadgeSource = read('frontend/src/components/StatusBadge.vue')
assert.match(statusBadgeSource, /API 数据/)
assert.match(statusBadgeSource, /Mock 数据/)

const panelSource = read('frontend/src/components/DashboardPanel.vue')
assert.match(panelSource, /<slot/)
assert.match(panelSource, /panel-title/)
```

Ensure the file still ends with:

```javascript
console.log('Dashboard asset checks passed.')
```

- [ ] **Step 2: Run the component asset test to verify it fails**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
```

Expected: FAIL because the component files do not exist.

- [ ] **Step 3: Add `BaseChart.vue`**

Create `frontend/src/components/BaseChart.vue`:

```vue
<template>
  <div class="chart-frame" :style="{ minHeight: height }">
    <div v-if="isEmpty" class="chart-empty">{{ emptyText }}</div>
    <div ref="chartElement" class="chart-canvas" :style="{ height }"></div>
  </div>
</template>

<script setup>
import { BarChart, FunnelChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent
} from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

echarts.use([
  BarChart,
  FunnelChart,
  GridComponent,
  LegendComponent,
  LineChart,
  PieChart,
  TooltipComponent,
  CanvasRenderer
])

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  height: {
    type: String,
    default: '280px'
  },
  emptyText: {
    type: String,
    default: '暂无数据'
  }
})

const chartElement = ref(null)
let chartInstance = null
let resizeObserver = null

const isEmpty = computed(() => !props.option || Object.keys(props.option).length === 0)

function renderChart() {
  if (!chartElement.value || isEmpty.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartElement.value)
  }
  chartInstance.setOption(props.option, true)
}

function resize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(async () => {
  await nextTick()
  renderChart()
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(chartElement.value)
  window.addEventListener('resize', resize)
})

watch(
  () => props.option,
  async () => {
    await nextTick()
    renderChart()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>
```

- [ ] **Step 4: Add small dashboard components**

Create `frontend/src/components/KpiCard.vue`:

```vue
<template>
  <article class="kpi-card">
    <span class="kpi-card__label">{{ label }}</span>
    <strong class="kpi-card__value">{{ value }}</strong>
    <small class="kpi-card__hint">{{ hint }}</small>
  </article>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  hint: { type: String, default: '' }
})
</script>
```

Create `frontend/src/components/StatusBadge.vue`:

```vue
<template>
  <span class="status-badge" :class="`status-badge--${type}`">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'loading'
  }
})

const type = computed(() => {
  if (props.status === 'api') return 'api'
  if (props.status === 'mock') return 'mock'
  if (props.status === 'error') return 'error'
  return 'loading'
})

const label = computed(() => {
  if (props.status === 'api') return 'API 数据'
  if (props.status === 'mock') return 'Mock 数据'
  if (props.status === 'error') return '异常降级'
  return '加载中'
})
</script>
```

Create `frontend/src/components/DashboardPanel.vue`:

```vue
<template>
  <section class="dashboard-panel">
    <header class="dashboard-panel__header">
      <h2 class="panel-title">{{ title }}</h2>
      <span v-if="meta" class="panel-meta">{{ meta }}</span>
    </header>
    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  meta: { type: String, default: '' }
})
</script>
```

- [ ] **Step 5: Run component checks and build**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
npm.cmd run build --prefix frontend
```

Expected: both PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git add frontend/tests/dashboard-assets.test.mjs frontend/src/components/BaseChart.vue frontend/src/components/KpiCard.vue frontend/src/components/StatusBadge.vue frontend/src/components/DashboardPanel.vue
git commit -m "feat: add dashboard components"
```

## Task 3: Dashboard Page Composition and Chart Options

**Files:**
- Modify: `frontend/tests/dashboard-assets.test.mjs`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Extend tests for page composition**

Append this block to `frontend/tests/dashboard-assets.test.mjs` before the final `console.log`:

```javascript
const appSource = read('frontend/src/App.vue')
for (const token of [
  'fetchAdsOverview',
  'mockAdsOverview',
  'StatusBadge',
  'KpiCard',
  'BaseChart',
  'DashboardPanel',
  'setInterval',
  'sourceStatus',
  'categoryShareOption',
  'productRankOption',
  'funnelOption'
]) {
  assert.match(appSource, new RegExp(token), `App.vue should include ${token}`)
}
```

- [ ] **Step 2: Run the asset test to verify it fails**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
```

Expected: FAIL because `App.vue` is still the placeholder dashboard.

- [ ] **Step 3: Replace `App.vue` with dashboard composition**

Modify `frontend/src/App.vue` to include:

```vue
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
```

Use a `<script setup>` section that imports the new modules and implements:

```javascript
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
```

Implement `refreshDashboard()` so API success sets `sourceStatus.value = 'api'`, API failure sets `overview.value = mockAdsOverview`, `sourceStatus.value = 'mock'`, and stores a short error message.

Implement `watch(autoRefresh, ...)` so enabling auto refresh starts a `setInterval(refreshDashboard, 60000)` and disabling it clears the timer.

Build chart computed properties with these names:

- `trendOption`
- `productRankOption`
- `categoryShareOption`
- `userProfileOption`
- `funnelOption`

Keep chart options in `App.vue` for this first version. Use Chinese labels and the existing ADS payload fields.

- [ ] **Step 4: Run page checks and build**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
npm.cmd run build --prefix frontend
```

Expected: both PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add frontend/tests/dashboard-assets.test.mjs frontend/src/App.vue
git commit -m "feat: compose vue ads dashboard"
```

## Task 4: Dashboard Styling and Responsive Layout

**Files:**
- Modify: `frontend/tests/dashboard-assets.test.mjs`
- Create: `frontend/src/styles/dashboard.css`
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/App.vue` if needed to remove scoped CSS

- [ ] **Step 1: Extend tests for styling integration**

Append this block to `frontend/tests/dashboard-assets.test.mjs` before the final `console.log`:

```javascript
assertFile('frontend/src/styles/dashboard.css')

const mainSource = read('frontend/src/main.js')
assert.match(mainSource, /styles\/dashboard\.css/)

const cssSource = read('frontend/src/styles/dashboard.css')
for (const token of [
  'dashboard-shell',
  'dashboard-grid',
  'dashboard-panel',
  'status-badge--api',
  'status-badge--mock',
  '@media'
]) {
  assert.match(cssSource, new RegExp(token), `dashboard.css should include ${token}`)
}
```

- [ ] **Step 2: Run the style asset test to verify it fails**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
```

Expected: FAIL because `frontend/src/styles/dashboard.css` is missing and `main.js` does not import it.

- [ ] **Step 3: Import dashboard CSS**

Modify `frontend/src/main.js`:

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import './styles/dashboard.css'

createApp(App).mount('#app')
```

- [ ] **Step 4: Add dashboard CSS**

Create `frontend/src/styles/dashboard.css` with these required sections:

```css
:root {
  color: #eef5ff;
  background: #070b14;
  font-family: "Microsoft YaHei", system-ui, sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  background: #070b14;
}

button,
input {
  font: inherit;
}

.dashboard-shell {
  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at 16% 8%, rgba(94, 234, 212, 0.16), transparent 28%),
    linear-gradient(135deg, #07111f 0%, #0b1020 48%, #101827 100%);
}

.dashboard-header,
.status-strip,
.kpi-grid,
.dashboard-grid {
  width: min(1680px, 100%);
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 14px;
}

.dashboard-eyebrow {
  margin: 0 0 8px;
  color: #5eead4;
  font-size: 14px;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 32px;
  letter-spacing: 0;
}

.dashboard-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.control-field,
.auto-refresh {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #bfd3ea;
  font-size: 13px;
}

.control-field input {
  min-height: 36px;
  border: 1px solid #30415f;
  border-radius: 6px;
  padding: 0 10px;
  background: #0f1a2c;
  color: #eef5ff;
}

.dashboard-controls button {
  min-height: 36px;
  border: 0;
  border-radius: 6px;
  padding: 0 14px;
  background: #2dd4bf;
  color: #06111f;
  cursor: pointer;
  font-weight: 700;
}

.dashboard-controls button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  border-radius: 999px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 700;
}

.status-badge--api {
  background: rgba(45, 212, 191, 0.16);
  color: #5eead4;
}

.status-badge--mock,
.status-badge--error {
  background: rgba(251, 191, 36, 0.16);
  color: #fbbf24;
}

.status-badge--loading {
  background: rgba(96, 165, 250, 0.16);
  color: #93c5fd;
}

.status-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  color: #9fb1c9;
  font-size: 13px;
}

.status-strip__warning {
  color: #fbbf24;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.kpi-card,
.dashboard-panel {
  border: 1px solid rgba(96, 165, 250, 0.24);
  border-radius: 8px;
  background: rgba(12, 22, 38, 0.86);
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.18);
}

.kpi-card {
  min-width: 0;
  padding: 16px;
}

.kpi-card__label,
.kpi-card__hint,
.panel-meta {
  color: #9fb1c9;
}

.kpi-card__value {
  display: block;
  margin-top: 8px;
  color: #eef5ff;
  font-size: 26px;
  line-height: 1.15;
  overflow-wrap: anywhere;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(240px, 0.95fr) minmax(420px, 1.7fr) minmax(240px, 0.95fr);
  gap: 14px;
  align-items: stretch;
}

.dashboard-column {
  display: grid;
  gap: 14px;
}

.dashboard-panel {
  min-width: 0;
  padding: 14px;
}

.dashboard-panel--hero {
  min-height: 100%;
}

.dashboard-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.panel-title {
  margin: 0;
  font-size: 16px;
  letter-spacing: 0;
}

.chart-frame,
.chart-canvas {
  width: 100%;
}

.chart-empty {
  display: grid;
  min-height: 120px;
  place-items: center;
  color: #9fb1c9;
}

@media (max-width: 1180px) {
  .dashboard-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .dashboard-controls {
    justify-content: flex-start;
  }

  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .dashboard-shell {
    padding: 16px;
  }

  .dashboard-header h1 {
    font-size: 26px;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-controls,
  .control-field,
  .dashboard-controls button {
    width: 100%;
  }

  .control-field input {
    flex: 1;
  }
}
```

- [ ] **Step 5: Remove obsolete scoped styles from `App.vue`**

If `App.vue` still contains the placeholder `<style scoped>` block, remove it so dashboard styling lives in `frontend/src/styles/dashboard.css`.

- [ ] **Step 6: Run style checks and build**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
npm.cmd run build --prefix frontend
```

Expected: both PASS.

- [ ] **Step 7: Commit**

Run:

```powershell
git add frontend/tests/dashboard-assets.test.mjs frontend/src/styles/dashboard.css frontend/src/main.js frontend/src/App.vue
git commit -m "style: add responsive dashboard layout"
```

## Task 5: Documentation, Foundation Check, and Final Frontend Verification

**Files:**
- Modify: `README.md`
- Modify: `deploy/scripts/check.ps1`
- Modify: `frontend/tests/dashboard-assets.test.mjs`

- [ ] **Step 1: Extend asset test for README and foundation paths**

Append this block to `frontend/tests/dashboard-assets.test.mjs` before the final `console.log`:

```javascript
const readmeSource = read('README.md')
assert.match(readmeSource, /Vue\/ECharts dashboard/)
assert.match(readmeSource, /FastAPI ADS API/)

const checkScript = read('deploy/scripts/check.ps1')
for (const file of [
  'frontend/src/components/BaseChart.vue',
  'frontend/src/data/mockAds.js',
  'frontend/src/services/adsApi.js',
  'frontend/src/styles/dashboard.css'
]) {
  assert.match(checkScript, new RegExp(file.replaceAll('/', '\\\\/')), `check.ps1 should include ${file}`)
}
```

- [ ] **Step 2: Run the asset test to verify it fails**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
```

Expected: FAIL because the README and foundation script do not yet mention the new dashboard files.

- [ ] **Step 3: Update root README**

Modify the root `README.md` tech stack and data flow text so it says the frontend has an active Vue/ECharts dashboard consuming the FastAPI ADS API. Keep the crawler, warehouse, backend, and deployment sections intact.

Expected snippets:

```markdown
- Dashboard: Vue 3 + ECharts dashboard
```

```text
Crawler -> Local raw files -> HDFS -> Hive ODS/DWD/DIM/DWS/ADS
        -> Spark offline jobs -> MySQL ADS result tables
        -> FastAPI ADS API -> Vue/ECharts dashboard
```

- [ ] **Step 4: Update foundation check**

Modify `deploy/scripts/check.ps1` and add these required paths:

```powershell
"frontend/src/components/BaseChart.vue",
"frontend/src/components/KpiCard.vue",
"frontend/src/components/StatusBadge.vue",
"frontend/src/components/DashboardPanel.vue",
"frontend/src/data/mockAds.js",
"frontend/src/services/adsApi.js",
"frontend/src/utils/formatters.js",
"frontend/src/styles/dashboard.css",
"frontend/tests/dashboard-assets.test.mjs",
```

- [ ] **Step 5: Run final local verification**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
npm.cmd run build --prefix frontend
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
python -m pytest backend/tests -q
```

Expected:

- Frontend asset checks pass.
- Vite build passes.
- Foundation check prints `Project foundation check passed.`
- Backend tests pass.

- [ ] **Step 6: Commit**

Run:

```powershell
git add README.md deploy/scripts/check.ps1 frontend/tests/dashboard-assets.test.mjs
git commit -m "docs: register vue dashboard assets"
```

## Task 6: Visual QA, Review, Push, and PR

**Files:**
- No new implementation files unless review finds a blocker.

- [ ] **Step 1: Run full verification**

Run:

```powershell
npm.cmd run test:assets --prefix frontend
npm.cmd run build --prefix frontend
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
python -m pytest backend/tests -q
```

Expected: all commands pass.

- [ ] **Step 2: Start the frontend dev server**

Run:

```powershell
npm.cmd run dev --prefix frontend
```

Expected: Vite starts and prints a local URL. If port 5173 is busy, use the next available Vite port.

- [ ] **Step 3: Inspect in browser**

Use browser automation or the in-app browser to open the Vite URL and verify:

- The first viewport is the dashboard, not a landing page.
- KPI cards render nonblank.
- All five chart panels render.
- Data source status is visible.
- Desktop viewport has no overlapping text or controls.
- Narrow viewport stacks content without incoherent overlap.
- If the backend is not running, mock fallback still renders.

- [ ] **Step 4: Request final code review**

Use a review subagent on `main..HEAD` with this context:

- Description: Vue/ECharts ADS dashboard consuming FastAPI overview data with mock fallback.
- Requirements: `docs/superpowers/specs/2026-07-04-vue-echarts-dashboard-design.md`.
- Verification: all commands from Step 1 plus browser visual QA.

Fix Critical and Important findings before pushing.

- [ ] **Step 5: Push and create PR**

Run:

```powershell
git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push -u origin codex/phase7-vue-echarts-dashboard
```

Create a ready PR against `main` with:

```markdown
## Summary
- add Vue/ECharts ADS dashboard cockpit
- add API-first overview loading with mock fallback
- add reusable dashboard components and frontend asset checks

## Tests
- `npm.cmd run test:assets --prefix frontend`
- `npm.cmd run build --prefix frontend`
- `powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1`
- `python -m pytest backend/tests -q`
```

- [ ] **Step 6: Report completion**

Report:

- PR URL.
- Verification commands and pass counts.
- Visual QA result.
- Any remaining untracked files such as `architecture-options.html`.
- Suggested next phase: deploy integration or richer dashboard interactions.

## Plan Self-Review

- Spec coverage: tasks cover API-first data loading, mock fallback, source status, KPI cards, five ADS visualizations, classic three-column layout, responsive styling, asset checks, build verification, and visual QA.
- Placeholder scan: no placeholder markers remain.
- Type consistency: file names, component names, API endpoint, and ADS section names match the design spec and FastAPI `OverviewResponse`.
- Scope check: the plan stays frontend-focused and does not require backend changes.
