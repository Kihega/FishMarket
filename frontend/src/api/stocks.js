import client from './client'

export const getStocks    = (params) => client.get('/stocks', { params })
// IMPORTANT: do NOT set Content-Type manually for FormData uploads.
// Axios (and the browser) need to generate their own boundary string and
// put it in the Content-Type header automatically. A hardcoded
// 'multipart/form-data' with no boundary produces a body the server
// cannot parse at all — every field, including the file, arrives empty —
// which is why stock creation was failing silently.
export const createStock  = (data)   => client.post('/stocks', data)
export const updateStock  = (id, data) => client.put(`/stocks/${id}`, data)
export const deleteStock  = (id)       => client.delete(`/stocks/${id}`)
