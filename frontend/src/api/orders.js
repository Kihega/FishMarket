import client from './client'

export const getOrders        = ()   => client.get('/orders')
export const placeOrder       = (data) => client.post('/orders', data)
export const payOrder         = (id) => client.post(`/orders/${id}/pay`)
export const confirmOrder     = (id) => client.post(`/orders/${id}/confirm`)
// Buyer-only actions
export const cancelOrder      = (id) => client.post(`/orders/${id}/cancel`)
export const confirmDelivery  = (id) => client.post(`/orders/${id}/confirm-delivery`)
