/**
 * API Service - Axios client for backend communication
 */
import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Token API
export const tokenAPI = {
  // Get all tokens
  getAll: () => api.get('/tokens'),
  
  // Get specific token
  getById: (id) => api.get(`/tokens/${id}`),
  
  // Get active token
  getActive: () => api.get('/tokens/active'),
  
  // Import tokens from JSON
  import: (data, filename) => api.post('/tokens/import', { data, filename }),
  
  // Activate token
  activate: (id) => api.post(`/tokens/${id}/activate`),
  
  //Delete Expired token
  deleteExpired: () => api.delete('/tokens/expired'),
  
  // Delete token
  delete: (id) => api.delete(`/tokens/${id}`),
  
  // Quick Actions Utils - Sprint 14
  generateCurl: (accessToken, endpoint = null, method = 'GET') => 
    api.post('/utils/generate-curl', {
      access_token: accessToken,
      endpoint: endpoint,
      method: method
    }),
  
  exportJson: (tokenId) => 
    api.post('/utils/export-json', {
      token_id: tokenId
    }),
  
  // Token Analysis - Sprint 14
  decodeJwt: (accessToken = null) => 
    api.post('/utils/decode-jwt', {
      access_token: accessToken
    }),
  
  analyzeScope: (scope = null) => 
    api.post('/utils/analyze-scope', {
      scope: scope
    }),
  
  validateToken: (accessToken = null) => 
    api.post('/utils/validate-token', {
      access_token: accessToken
    })
}

// Graph API
export const graphAPI = {
  // Get user profile
  getUserProfile: () => api.get('/graph/me'),
  
  // Get user photo
  getUserPhoto: () => api.get('/graph/me/photo')
}

// System API
export const systemAPI = {
  // Health check
  health: () => api.get('/health'),
  
  // Get stats
  getStats: () => api.get('/stats')
}

// Roles & Licenses API
export const rolesAPI = {
  // Get all directory roles
  getDirectoryRoles: () => api.get('/roles/directory-roles'),
  
  // Get members of a specific role
  getRoleMembers: (roleId) => api.get(`/roles/directory-roles/${roleId}/members`),
  
  // Get AU-scoped roles (delegated admin in Administrative Units)
  getAUScopedRoles: () => api.get('/roles/au-scoped'),
  
  // Get all licenses
  getLicenses: () => api.get('/roles/licenses'),
  
  // Get users with a specific license
  getLicenseUsers: (skuId) => api.get(`/roles/licenses/${skuId}/users`),
  
  // Get privileged roles
  getPrivilegedRoles: () => api.get('/roles/privileged'),
  
  // Get security summary
  getSecuritySummary: () => api.get('/roles/security-summary')
}

// ========================================
// ADMIN ACTIONS API
// ========================================
export const adminAPI = {
  // -- Capability Check (NEW) --
  
  // Check if token has admin role + required scopes
  checkCapabilities: (accessToken, actionType = null) => {
    const payload = { access_token: accessToken }
    if (actionType) {
      payload.action_type = actionType
    }
    return api.post('/admin/check-capabilities', payload)
  },
  
  // Perform FOCI exchange to get Azure PowerShell token
  fociExchange: (accessToken) => 
    api.post('/admin/foci-exchange', { 
      access_token: accessToken 
    }),
  
  // Auto-acquire token for specific action type (FOCI or Device Code)
  autoAcquireToken: (accessToken, actionType, deviceCodeData = null) => {
    const payload = {
      access_token: accessToken,
      action_type: actionType
    }
    if (deviceCodeData) {
      payload.device_code_data = deviceCodeData
    }
    return api.post('/admin/auto-acquire-token', payload)
  },
  
  // Start device code flow
  startDeviceCode: (clientId, scope) => 
    api.post('/auth/device-code/start', {
      client_id: clientId,
      scope: scope
    }),
  
  // Poll device code for token
  pollDeviceCode: (clientId, deviceCode) => 
    api.post('/auth/device-code/poll', {
      client_id: clientId,
      device_code: deviceCode
    }),
  
  // -- User Management (4.2) --
  
  // Create new user
  createUser: (accessToken, userData) => 
    api.post('/admin/create-user', {
      access_token: accessToken,
      user_data: userData
    }),
  
  // -- Password Reset  --
  
  // Reset user password
  resetPassword: (accessToken, userId, newPassword, forceChange = true) => 
    api.post('/admin/reset-password', {
      access_token: accessToken,
      user_id: userId,
      new_password: newPassword,
      force_change: forceChange
    }),
  
  // -- TAP Management  --
  
  // List TAP for user
  listTap: (accessToken, userId) => 
    api.post('/admin/tap/list', {
      access_token: accessToken,
      user_id: userId
    }),
  
  // Create TAP for user
  createTap: (accessToken, userId, options = {}) => 
    api.post('/admin/tap/create', {
      access_token: accessToken,
      user_id: userId,
      lifetime_minutes: options.lifetimeInMinutes || 60,
      is_usable_once: options.isUsableOnce || false
    }),
  
  // Delete TAP
  deleteTap: (accessToken, userId, tapId) => 
    api.post('/admin/tap/delete', {
      access_token: accessToken,
      user_id: userId,
      tap_id: tapId
    }),
  
  // -- MFA Management --
  
  // List all auth methods for user
  listAuthMethods: (accessToken, userId) => 
    api.post('/admin/auth-methods/list', {
      access_token: accessToken,
      user_id: userId
    }),
  
  // Delete auth method
  deleteAuthMethod: (accessToken, userId, methodType, methodId) => 
    api.post('/admin/auth-methods/delete', {
      access_token: accessToken,
      user_id: userId,
      method_type: methodType,
      method_id: methodId
    }),
  
  // Add phone method
  addPhoneMethod: (accessToken, userId, phoneNumber, phoneType = 'mobile') => 
    api.post('/admin/auth-methods/add-phone', {
      access_token: accessToken,
      user_id: userId,
      phone_number: phoneNumber,
      phone_type: phoneType
    }),
  
  // Add email method
  addEmailMethod: (accessToken, userId, emailAddress) => 
    api.post('/admin/auth-methods/add-email', {
      access_token: accessToken,
      user_id: userId,
      email_address: emailAddress
    })
}

export default api
