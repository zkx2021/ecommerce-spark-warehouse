import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const projectRoot = path.resolve(root, '..')

function read(relativePath) {
  return fs.readFileSync(path.resolve(projectRoot, relativePath), 'utf8')
}

function assertFile(relativePath) {
  assert.ok(fs.existsSync(path.resolve(projectRoot, relativePath)), `${relativePath} should exist`)
}

const packageJson = JSON.parse(read('frontend/package.json'))

assert.equal(packageJson.dependencies.vue, '3.4.29')
assert.equal(packageJson.dependencies.echarts, '5.5.0')
assert.equal(packageJson.scripts['test:assets'], 'node tests/dashboard-assets.test.mjs')

assertFile('frontend/src/data/mockAds.js')
assertFile('frontend/src/services/adsApi.js')
assertFile('frontend/src/utils/formatters.js')

const mockAds = read('frontend/src/data/mockAds.js')
for (const section of ['kpi', 'trend', 'product_rank', 'category_share', 'user_profile', 'funnel']) {
  assert.match(mockAds, new RegExp(`${section}:`))
}
for (const field of [
  'rank_no',
  'product_id',
  'sales_quantity',
  'sales_share',
  'dimension_type',
  'dimension_value',
  'buyer_count',
  'stage_name',
  'stage_order',
  'stage_count'
]) {
  assert.match(mockAds, new RegExp(`${field}:`))
}

const adsApi = read('frontend/src/services/adsApi.js')
assert.match(adsApi, /\/api\/ads\/overview/)
assert.match(adsApi, /URLSearchParams/)
assert.match(adsApi, /throw new Error/)

const viteConfigSource = read('frontend/vite.config.js')
assert.match(viteConfigSource, /server\s*:/)
assert.match(viteConfigSource, /proxy\s*:/)
assert.match(viteConfigSource, /['"]\/api['"]/)
assert.match(viteConfigSource, /http:\/\/127\.0\.0\.1:8000/)

const formatters = read('frontend/src/utils/formatters.js')
for (const formatter of ['formatMoney', 'formatCount', 'formatPercent', 'formatDateTime']) {
  assert.match(formatters, new RegExp(`export function ${formatter}`))
}

const { mockAdsOverview } = await import('../src/data/mockAds.js')
const { fetchAdsOverview } = await import('../src/services/adsApi.js')
const {
  formatMoney,
  formatCount,
  formatPercent,
  formatDateTime
} = await import('../src/utils/formatters.js')

for (const section of ['trend', 'product_rank', 'category_share', 'user_profile', 'funnel']) {
  assert.ok(Array.isArray(mockAdsOverview[section]), `${section} should be an array`)
  assert.ok(mockAdsOverview[section].length > 0, `${section} should not be empty`)
}

assert.deepEqual(Object.keys(mockAdsOverview.trend[0]), [
  'sales_amount',
  'order_count',
  'paid_user_count'
])
assert.deepEqual(Object.keys(mockAdsOverview.product_rank[0]), [
  'rank_no',
  'product_id',
  'product_name',
  'category',
  'sales_quantity',
  'sales_amount'
])
assert.deepEqual(Object.keys(mockAdsOverview.category_share[0]), [
  'category',
  'sales_amount',
  'sales_quantity',
  'sales_share'
])
assert.deepEqual(Object.keys(mockAdsOverview.user_profile[0]), [
  'dimension_type',
  'dimension_value',
  'user_count',
  'buyer_count',
  'sales_amount'
])
assert.deepEqual(Object.keys(mockAdsOverview.funnel[0]), [
  'stage_name',
  'stage_order',
  'stage_count',
  'conversion_rate'
])

const originalFetch = global.fetch
try {
  let capturedUrl
  global.fetch = async (url) => {
    capturedUrl = url
    return {
      ok: true,
      json: async () => ({ ok: true })
    }
  }

  const result = await fetchAdsOverview('2026-07-01')
  assert.equal(capturedUrl, '/api/ads/overview?date=2026-07-01')
  assert.deepEqual(result, { ok: true })

  global.fetch = async () => ({
    ok: false,
    status: 503
  })
  await assert.rejects(() => fetchAdsOverview(), /503/)
} finally {
  if (originalFetch === undefined) {
    delete global.fetch
  } else {
    global.fetch = originalFetch
  }
}

assert.equal(formatMoney(1234567.89), '123.46 万')
assert.equal(formatCount(3420), '3,420')
assert.equal(formatPercent(0.374), '37.4%')
const formattedDateTime = formatDateTime(new Date('2026-07-01T12:34:56+08:00'))
assert.equal(typeof formattedDateTime, 'string')
assert.ok(formattedDateTime.length > 0)

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
assert.match(baseChartSource, /v-show="!isEmpty"/)
assert.match(baseChartSource, /if \(isEmpty\.value\)/)
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
assert.match(appSource, /refreshRequestId/)
assert.match(appSource, /requestId !== refreshRequestId/)
assert.match(appSource, /productRankLabelWidth/)
assert.match(appSource, /containLabel:\s*true/)
assert.match(appSource, /overflow:\s*'break'/)
assert.match(appSource, /formatter: \(params\) =>/)
assert.match(appSource, /销售额：/)
assert.match(appSource, /销量：/)
assert.match(appSource, /formatProfileAxisLabel/)
assert.match(appSource, /interval:\s*0/)
assert.match(appSource, /电商数据经营看板/)
assert.doesNotMatch(appSource, /Spark \+ HDFS \+ Hive/)
for (const pattern of [
  /catch/,
  /finally/,
  /clearInterval/,
  /onBeforeUnmount/,
  /type: 'line'/,
  /type: 'bar'/,
  /type: 'pie'/,
  /type: 'funnel'/
]) {
  assert.match(appSource, pattern)
}

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

assert.match(cssSource, /repeat\(4,\s*minmax\(0,\s*1fr\)\)/)
assert.match(cssSource, /repeat\(2,\s*minmax\(0,\s*1fr\)\)/)
assert.match(cssSource, /flex-wrap:\s*wrap/)
assert.match(cssSource, /overflow-wrap:\s*anywhere/)
assert.doesNotMatch(cssSource, /radial-gradient/)

assert.doesNotMatch(appSource, /<style scoped>/)

const readmeSource = read('README.md')
assert.match(readmeSource, /Vue\/ECharts dashboard/)
assert.match(readmeSource, /FastAPI ADS API/)
assert.match(readmeSource, /Dashboard: Vue 3 \+ ECharts dashboard/)
assert.match(readmeSource, /FastAPI ADS API -> Vue\/ECharts dashboard/)
assert.match(readmeSource, /Current Data Flow/)
assert.doesNotMatch(readmeSource, /planned Vue/i)
assert.doesNotMatch(readmeSource, /future Vue/i)

const foundationCheckSource = read('deploy/scripts/check.ps1')
for (const file of [
  'frontend/src/App.vue',
  'frontend/src/main.js',
  'frontend/src/components/BaseChart.vue',
  'frontend/src/components/KpiCard.vue',
  'frontend/src/components/StatusBadge.vue',
  'frontend/src/components/DashboardPanel.vue',
  'frontend/src/data/mockAds.js',
  'frontend/src/services/adsApi.js',
  'frontend/src/utils/formatters.js',
  'frontend/src/styles/dashboard.css',
  'frontend/tests/dashboard-assets.test.mjs'
]) {
  assert.match(foundationCheckSource, new RegExp(file.replaceAll('/', '\\\\')))
}

console.log('Dashboard asset checks passed.')
