<template>
  <div class="chart-frame" :style="{ minHeight: height }">
    <div v-if="isEmpty" class="chart-empty">{{ emptyText }}</div>
    <div v-show="!isEmpty" ref="chartElement" class="chart-canvas" :style="{ height }"></div>
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
  if (isEmpty.value) {
    disposeChart()
    return
  }
  if (!chartElement.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartElement.value)
  }
  chartInstance.setOption(props.option, true)
}

function disposeChart() {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

function resize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(async () => {
  await nextTick()
  renderChart()
  if (chartElement.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(chartElement.value)
  }
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
  disposeChart()
})
</script>
