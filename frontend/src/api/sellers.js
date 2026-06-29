import client from './client'

export const getSellers         = (params) => client.get('/sellers', { params })
export const getSeller          = (id)     => client.get(`/sellers/${id}`)
// Same fix as stocks.js: let axios set its own multipart boundary instead
// of overriding Content-Type with a boundary-less value the server can't
// parse (this was silently breaking brand_logo uploads on profile saves).
export const updateProfile      = (data)   => client.put('/seller/profile', data)
