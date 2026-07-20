const DEFAULT_CATEGORY_LIMIT = 6
const OTHER_CATEGORY_NAME = '其他'

export function buildCategoryShareSlices(rows, limit = DEFAULT_CATEGORY_LIMIT) {
  if (!Array.isArray(rows) || rows.length <= limit) {
    return Array.isArray(rows) ? rows : []
  }

  const headRows = rows.slice(0, limit)
  const otherRows = rows.slice(limit)
  const otherSlice = otherRows.reduce(
    (summary, row) => ({
      category: OTHER_CATEGORY_NAME,
      sales_amount: summary.sales_amount + Number(row.sales_amount || 0),
      sales_quantity: summary.sales_quantity + Number(row.sales_quantity || 0),
      sales_share: summary.sales_share + Number(row.sales_share || 0)
    }),
    {
      category: OTHER_CATEGORY_NAME,
      sales_amount: 0,
      sales_quantity: 0,
      sales_share: 0
    }
  )

  return [...headRows, otherSlice]
}
