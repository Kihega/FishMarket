import client from './client'

export const createSubscription = (data) => client.post('/seller/subscription', data)
export const getMySubscriptions = () => client.get('/seller/subscription')
