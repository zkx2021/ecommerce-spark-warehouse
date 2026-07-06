# Vue ECharts Dashboard Design

## Goal

Build the first Vue and ECharts dashboard for the ecommerce warehouse project. The dashboard should consume the FastAPI ADS API when available, fall back to mock ADS data when the API is unavailable, and present a polished single-screen ecommerce operations view for demos and local development.

## Scope

This phase implements the frontend dashboard only.

In scope:

- Replace the current placeholder Vue screen with a dashboard.
- Read ADS overview data from `GET /api/ads/overview`.
- Support an optional `date=YYYY-MM-DD` query parameter.
- Fall back to local mock data if the API request fails.
- Show whether data came from API or mock fallback.
- Add ECharts visualizations for ADS sections.
- Keep the page responsive enough for desktop, laptop, and narrow browser widths.
- Add frontend verification for build and required dashboard assets.

Out of scope:

- Backend API changes.
- New ADS metrics or database schema changes.
- Authentication.
- Multi-page navigation.
- Real-time streaming. Auto refresh is timer-based HTTP polling only.
- Production deployment changes beyond documentation or local Vite configuration if needed.

## User Experience

The first version uses a balanced "classic three-column cockpit" layout. It should feel like a data big screen, but not become decorative at the expense of readability.

### Header

The header contains:

- Title: `电商经营分析大屏`
- Subtitle or project label: `Spark + HDFS + Hive 离线数仓`
- Date input using `YYYY-MM-DD`
- Manual refresh button
- Auto-refresh control
- Data source status badge

The data source badge can show:

- `加载中`
- `API 数据`
- `Mock 数据`
- `异常降级`

When mock fallback is active, the page should remain usable and visibly indicate that it is not showing live API data.

### KPI Band

The KPI band shows five metrics:

- Sales amount
- Order count
- Paid user count
- Average order amount
- Payment conversion rate

Values should be formatted for dashboard readability:

- Money uses compact Chinese display such as `12.34 万`.
- Integer counts use separators.
- Rates use percent display.

### Main Dashboard Body

The body uses a three-column layout:

- Left column:
  - Category sales share chart.
  - User profile chart.
- Center column:
  - Sales trend chart as the primary visual.
- Right column:
  - Product sales ranking.
  - Conversion funnel.

The center trend chart should be visually dominant. Side panels should remain dense but readable.

### Responsive Behavior

The primary target is desktop and 16:9 laptop screens.

Responsive rules:

- Wide screens use the three-column cockpit.
- Medium screens stack the side panels under the trend chart or reduce to two columns.
- Small screens stack panels vertically.
- Text and buttons must not overlap or overflow their containers.
- Charts must resize with their containers.

## Data Flow

The dashboard fetches from:

```text
GET /api/ads/overview
GET /api/ads/overview?date=YYYY-MM-DD
```

Successful API response is used directly after frontend normalization.

If the API request fails for network, 404, 503, invalid JSON, or other fetch errors:

1. Load local mock overview data.
2. Set data source status to mock fallback.
3. Store a short error message for the user-facing status area.
4. Keep the dashboard charts rendered with mock data.

The first render should show mock-compatible data structures even before a successful API call, so the screen is never blank for normal local development.

## Frontend Architecture

Use the existing Vite + Vue 3 + ECharts scaffold.

Recommended file boundaries:

```text
frontend/src/App.vue
frontend/src/components/BaseChart.vue
frontend/src/components/KpiCard.vue
frontend/src/components/StatusBadge.vue
frontend/src/components/DashboardPanel.vue
frontend/src/data/mockAds.js
frontend/src/services/adsApi.js
frontend/src/utils/formatters.js
frontend/src/styles/dashboard.css
```

### `App.vue`

Responsibilities:

- Own page-level state:
  - selected date
  - loading state
  - source status
  - last refresh time
  - latest overview data
  - last error message
- Trigger manual refresh.
- Manage auto-refresh timer.
- Compose KPI cards and chart panels.
- Pass prepared chart options to `BaseChart`.

`App.vue` should not contain low-level fetch logic, formatting helpers, or ECharts lifecycle code.

### `services/adsApi.js`

Responsibilities:

- Export `fetchAdsOverview(date)`.
- Build `/api/ads/overview` URL with optional `date`.
- Throw a useful error when the response is not OK.
- Return parsed JSON.

The service should not know about mock fallback. Fallback is a page behavior owned by `App.vue`.

### `data/mockAds.js`

Responsibilities:

- Export one complete overview object matching FastAPI `OverviewResponse`.
- Include realistic demo values for all sections:
  - `kpi`
  - `trend`
  - `product_rank`
  - `category_share`
  - `user_profile`
  - `funnel`

### `components/BaseChart.vue`

Responsibilities:

- Initialize ECharts on mount.
- Update the chart when `option` changes.
- Resize on window resize.
- Dispose the chart on unmount.

This component should accept:

- `option`
- `height`
- optional `emptyText`

### Utility and Style Files

`utils/formatters.js` owns display formatting for money, counts, rates, and date/time strings.

`styles/dashboard.css` owns global dashboard styling. The visual style should avoid a one-note dark blue palette by combining dark neutrals with cyan, blue, amber, and violet accents.

## Chart Mapping

Use ECharts options generated from the overview payload.

| ADS section | Chart |
| --- | --- |
| `kpi` | KPI cards |
| `trend` | Line chart |
| `product_rank` | Horizontal bar chart |
| `category_share` | Donut or pie chart |
| `user_profile` | Grouped or stacked bar chart |
| `funnel` | Funnel chart or staged bar chart |

Chart labels should use Chinese names that match the business meaning.

## Error Handling

The dashboard should handle:

- Loading state while fetching.
- API success.
- API failure with mock fallback.
- Empty arrays in chart data.
- Invalid date input from the browser control.

Invalid date should not crash the page. The date control should use `type="date"` and the frontend should pass the browser-produced value as-is.

## Testing and Verification

Expected local checks:

```powershell
npm.cmd run build --prefix frontend
python -m pytest backend/tests/test_ads_assets.py -q
```

Add a lightweight frontend asset test if useful, for example a Node script or Python test that checks:

- dashboard source files exist
- `package.json` still includes Vue and ECharts
- the app references `/api/ads/overview`
- mock data includes all overview sections

Visual verification should include:

- Desktop viewport.
- Narrow/mobile viewport.
- Page is nonblank.
- KPI cards and charts do not overlap.
- Data source status is visible.

## Implementation Notes

The first implementation should prefer clarity over heavy abstractions. It is acceptable to keep chart option builders in `App.vue` for the first version if they remain readable, but ECharts lifecycle code should be isolated in `BaseChart.vue`.

Do not add a landing page. The dashboard itself should be the first screen.

Do not require a live backend for the frontend build or visual demo. Mock fallback is a core requirement for this phase.

## Spec Self-Review

- Placeholder scan: no placeholder markers remain.
- Scope check: this spec covers one frontend dashboard phase only.
- Consistency check: UX, data flow, file boundaries, and verification all target the same Vue/ECharts dashboard.
- Ambiguity check: data strategy, layout, fallback behavior, and chart mapping are explicitly defined.
