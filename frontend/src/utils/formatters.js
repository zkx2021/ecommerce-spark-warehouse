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
