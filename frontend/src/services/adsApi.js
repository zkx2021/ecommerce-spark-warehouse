const ADS_OVERVIEW_PATH = '/api/ads/overview'

export async function fetchAdsOverview(date) {
  const params = new URLSearchParams()
  if (date) {
    params.set('date', date)
  }

  const query = params.toString()
  const url = `${ADS_OVERVIEW_PATH}${query ? `?${query}` : ''}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`ADS overview request failed with status ${response.status}`)
  }

  return response.json()
}
