import client from './client'

export const getSellers         = (params) => client.get('/sellers', { params })
export const getSeller          = (id)     => client.get(`/sellers/${id}`)
export const updateProfile      = (data)   => client.put('/seller/profile', data, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
