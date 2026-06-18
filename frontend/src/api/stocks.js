import client from './client'

export const getStocks    = (params) => client.get('/stocks', { params })
export const createStock  = (data)   => client.post('/stocks', data, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const updateStock  = (id, data) => client.put(`/stocks/${id}`, data)
export const deleteStock  = (id)       => client.delete(`/stocks/${id}`)
