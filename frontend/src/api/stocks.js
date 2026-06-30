import client from './client'

export const getStocks    = (params) => client.get('/stocks', { params })
// Seller dashboard's own scoped stock list — NOT the public feed.
// Using the public /stocks endpoint here was the bug that leaked every
// seller's stock into every other seller's "Manage Stocks" screen.
export const getMyStocks  = ()       => client.get('/seller/stocks')
// Sends a plain JSON object — the Add Stock form no longer uploads an
// image (that was crashing the form), so there's no FormData/file
// involved here anymore. If a file upload is ever reintroduced
// elsewhere, remember: do NOT set Content-Type manually for FormData —
// axios needs to generate its own boundary string, and a hardcoded
// 'multipart/form-data' with no boundary produces a body the server
// can't parse at all (this broke stock creation entirely before).
export const createStock  = (data)   => client.post('/stocks', data)
export const updateStock  = (id, data) => client.put(`/stocks/${id}`, data)
export const deleteStock  = (id)       => client.delete(`/stocks/${id}`)
