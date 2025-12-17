<template>
  <div :class="['key-vaults-view', isDark ? 'dark-theme' : '']">
    <div class="header">
      <div>
        <h1>Key Vaults</h1>
        <p class="subtitle">Azure Key Vaults enumeration and management</p>
      </div>
      <div class="header-actions">
        <!-- Subscription Selector -->
        <select 
          v-model="selectedSubscription" 
          @change="fetchKeyVaults(true)"
          :class="['subscription-select', { 'dark': isDark }]"
        >
          <option value="">Select Subscription</option>
          <option v-for="sub in subscriptions" :key="sub.subscriptionId" :value="sub.subscriptionId">
            {{ sub.displayName }}
          </option>
        </select>
        
        <!-- Refresh Button -->
        <button 
          @click="fetchKeyVaults(true)" 
          class="refresh-btn" 
          :disabled="loading"
        >
          <svg class="w-5 h-5" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>{{ loading ? 'Loading...' : 'Refresh' }}</span>
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" :class="[isDark ? 'bg-red-900/50 border-red-700 text-red-200' : 'bg-red-100 border-red-300 text-red-800', 'border px-4 py-3 rounded-lg mb-4']">
      <div class="flex items-center">
        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <span>{{ error }}</span>
      </div>
    </div>

    <!-- No Subscription Selected -->
    <div v-if="!selectedSubscription && keyVaults.length === 0" class="text-center py-12">
      <svg :class="['w-16 h-16 mx-auto mb-4', isDark ? 'text-gray-600' : 'text-gray-400']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
      </svg>
      <h3 :class="['text-lg font-semibold mb-2', isDark ? 'text-gray-400' : 'text-gray-600']">Select a Subscription</h3>
      <p :class="[isDark ? 'text-gray-500' : 'text-gray-500']">Choose a subscription from the dropdown to view Key Vaults</p>
    </div>

    <div v-if="!selectedVault && keyVaults.length > 0" class="vaults-grid">
      <div 
        v-for="vault in keyVaults" 
        :key="vault.id"
        class="vault-card"
        @click="selectVault(vault)"
      >
        <div class="vault-header">
          <span class="vault-icon">🔐</span>
          <h3>{{ vault.name }}</h3>
        </div>
        <div class="vault-details">
          <p><strong>Subscription:</strong> {{ vault.subscription }}</p>
          <p><strong>Location:</strong> {{ vault.location }}</p>
          <p><strong>SKU:</strong> {{ vault.sku }}</p>
          <p>
            <strong>Auth Model:</strong> 
            <span :class="vault.enableRbacAuthorization ? 'badge-rbac' : 'badge-policies'">
              {{ vault.enableRbacAuthorization ? 'Azure RBAC' : 'Access Policies' }}
            </span>
          </p>
        </div>
      </div>
    </div>

    <!-- Vault Details View (4 Tabs) -->
    <div v-if="selectedVault" class="vault-details-view">
      <div class="details-header">
        <button @click="selectedVault = null" class="back-btn">← Back to List</button>
        <h2>{{ selectedVault.name }}</h2>
      </div>

      <!-- Tabs Navigation -->
      <div class="tabs">
        <button 
          :class="['tab-btn', { active: activeTab === 'properties' }]"
          @click="activeTab = 'properties'"
        >
          📋 Properties
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'secrets' }]"
          @click="activeTab = 'secrets'"
        >
          🔑 Secrets
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'certificates' }]"
          @click="activeTab = 'certificates'"
        >
          📜 Certificates
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'access-policies' }]"
          @click="switchToAccessPolicies"
        >
          👥 Access Policies
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- TAB 1: Properties -->
        <div v-if="activeTab === 'properties'" class="properties-tab">
          <div class="property-group">
            <h3>General Information</h3>
            <div class="property-grid">
              <div class="property-item">
                <span class="property-label">Name:</span>
                <span class="property-value">{{ selectedVault.name }}</span>
              </div>
              <div class="property-item">
                <span class="property-label">Location:</span>
                <span class="property-value">{{ selectedVault.location }}</span>
              </div>
              <div class="property-item">
                <span class="property-label">Subscription:</span>
                <span class="property-value">{{ selectedVault.subscription }}</span>
              </div>
              <div class="property-item">
                <span class="property-label">SKU:</span>
                <span class="property-value">{{ selectedVault.sku }}</span>
              </div>
              <div class="property-item wide">
                <span class="property-label">Vault URI:</span>
                <span class="property-value code">{{ selectedVault.vaultUri }}</span>
              </div>
              <div class="property-item wide">
                <span class="property-label">Tenant ID:</span>
                <span class="property-value code">{{ selectedVault.tenantId }}</span>
              </div>
              <div class="property-item">
                <span class="property-label">Authorization Model:</span>
                <span :class="['badge', selectedVault.enableRbacAuthorization ? 'badge-rbac' : 'badge-policies']">
                  {{ selectedVault.enableRbacAuthorization ? 'Azure RBAC' : 'Access Policies' }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="Object.keys(selectedVault.tags || {}).length > 0" class="property-group">
            <h3>Tags</h3>
            <div class="tags-grid">
              <div v-for="(value, key) in selectedVault.tags" :key="key" class="tag-item">
                <span class="tag-key">{{ key }}:</span>
                <span class="tag-value">{{ value }}</span>
              </div>
            </div>
          </div>

          <div class="property-group">
            <h3>Resource ID</h3>
            <div class="code-block">{{ selectedVault.id }}</div>
          </div>
        </div>

        <!-- TAB 2: Secrets -->
        <div v-if="activeTab === 'secrets'" class="secrets-tab">
          <div class="tab-actions">
            <button @click="listSecrets" class="action-btn" :disabled="secretsLoading">
              {{ secretsLoading ? 'Loading...' : '🔍 List Secrets' }}
            </button>
            <span v-if="secrets.length > 0" class="count-badge">{{ secrets.length }} secrets</span>
          </div>

          <div v-if="secretsError" class="error">
            {{ secretsError }}
            <p v-if="secretsError.includes('403') || secretsError.includes('permission')" class="hint">
              💡 Try clicking "Grant Self Access" in the Access Policies tab
            </p>
          </div>

          <div v-if="!dataPlaneTokenAvailable && !secretsError" class="warning">
            ⚠️ No data plane token available. Acquire token with audience: <code>https://vault.azure.net</code>
          </div>

          <div v-if="secrets.length > 0" class="secrets-table">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Content Type</th>
                  <th>Enabled</th>
                  <th>Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="secret in secrets" :key="secret.id">
                  <td class="secret-name">{{ secret.name }}</td>
                  <td>{{ secret.contentType || 'N/A' }}</td>
                  <td>
                    <span :class="['status-badge', secret.enabled ? 'enabled' : 'disabled']">
                      {{ secret.enabled ? 'Enabled' : 'Disabled' }}
                    </span>
                  </td>
                  <td>{{ formatTimestamp(secret.updated) }}</td>
                  <td>
                    <button 
                      @click="revealSecret(secret.name)" 
                      class="reveal-btn"
                      :disabled="revealingSecret === secret.name"
                    >
                      {{ revealingSecret === secret.name ? '🔄 Revealing...' : '👁️ Reveal' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Secret Value Modal -->
          <div v-if="revealedSecret" class="modal-overlay" @click="revealedSecret = null">
            <div class="modal-content" @click.stop>
              <div class="modal-header">
                <h3>🔓 Secret Value</h3>
                <button @click="revealedSecret = null" class="close-btn">×</button>
              </div>
              <div class="modal-body">
                <p><strong>Name:</strong> {{ revealedSecret.name }}</p>
                <div class="secret-value-container">
                  <label>Plaintext Value:</label>
                  <div class="secret-value">{{ revealedSecret.value }}</div>
                  <button @click="copyToClipboard(revealedSecret.value)" class="copy-btn">
                    📋 Copy
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB 3: Certificates -->
        <div v-if="activeTab === 'certificates'" class="certificates-tab">
          <div class="tab-actions">
            <button @click="listCertificates" class="action-btn" :disabled="certsLoading">
              {{ certsLoading ? 'Loading...' : '📜 List Certificates' }}
            </button>
            <span v-if="certificates.length > 0" class="count-badge">{{ certificates.length }} certificates</span>
          </div>

          <div v-if="certsError" class="error">
            {{ certsError }}
            <p v-if="certsError.includes('403') || certsError.includes('permission')" class="hint">
              💡 Try clicking "Grant Self Access" in the Access Policies tab
            </p>
          </div>

          <div v-if="!dataPlaneTokenAvailable && !certsError" class="warning">
            ⚠️ No data plane token available. Acquire token with audience: <code>https://vault.azure.net</code>
          </div>

          <div v-if="certificates.length > 0" class="certificates-table">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Thumbprint</th>
                  <th>Enabled</th>
                  <th>Created</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="cert in certificates" :key="cert.id">
                  <td class="cert-name">{{ cert.name }}</td>
                  <td class="thumbprint">{{ cert.x509Thumbprint || 'N/A' }}</td>
                  <td>
                    <span :class="['status-badge', cert.enabled ? 'enabled' : 'disabled']">
                      {{ cert.enabled ? 'Enabled' : 'Disabled' }}
                    </span>
                  </td>
                  <td>{{ formatTimestamp(cert.created) }}</td>
                  <td>{{ formatTimestamp(cert.updated) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- TAB 4: Access Policies -->
        <div v-if="activeTab === 'access-policies'" class="access-policies-tab">
          <div class="tab-actions">
            <button @click="fetchAccessPolicies" class="action-btn" :disabled="policiesLoading">
              {{ policiesLoading ? 'Loading...' : '🔄 Refresh Policies' }}
            </button>
            <button 
              @click="grantSelfAccess" 
              class="grant-access-btn" 
              :disabled="grantingAccess || (vaultDetails && vaultDetails.enableRbacAuthorization)"
            >
              {{ grantingAccess ? 'Granting...' : '🎯 Grant Self Access' }}
            </button>
          </div>

          <div v-if="vaultDetails && vaultDetails.enableRbacAuthorization" class="info-box">
            ℹ️ This Key Vault uses <strong>Azure RBAC</strong> for authorization. Access policies are disabled.
            Use Azure role assignments instead (e.g., "Key Vault Secrets User" role).
          </div>

          <div v-if="policiesError" class="error">{{ policiesError }}</div>
          <div v-if="grantAccessSuccess" class="success">
            ✅ {{ grantAccessSuccess }}
          </div>

          <div v-if="accessPolicies.length > 0" class="policies-container">
            <h3>Current Access Policies ({{ accessPolicies.length }})</h3>
            <div class="policies-grid">
              <div v-for="(policy, index) in accessPolicies" :key="index" class="policy-card">
                <div class="policy-header">
                  <span class="policy-icon">👤</span>
                  <div class="principal-info">
                    <span v-if="principalInfo[policy.objectId]" class="principal-name">
                      {{ principalInfo[policy.objectId] }}
                    </span>
                    <span v-else-if="resolvingPrincipals" class="resolving">Resolving...</span>
                    <span v-else class="object-id">{{ policy.objectId }}</span>
                  </div>
                </div>
                <div class="policy-permissions">
                  <div v-if="policy.permissions.secrets.length > 0" class="perm-group">
                    <strong>Secrets:</strong> {{ policy.permissions.secrets.join(', ') }}
                  </div>
                  <div v-if="policy.permissions.certificates.length > 0" class="perm-group">
                    <strong>Certificates:</strong> {{ policy.permissions.certificates.join(', ') }}
                  </div>
                  <div v-if="policy.permissions.keys.length > 0" class="perm-group">
                    <strong>Keys:</strong> {{ policy.permissions.keys.join(', ') }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="!policiesLoading && !vaultDetails?.enableRbacAuthorization" class="empty-state">
            No access policies configured. Click "Grant Self Access" to add permissions.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'KeyVaultsView',
  props: {
    isDark: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      // Subscriptions
      subscriptions: [],
      selectedSubscription: '',
      
      keyVaults: [],
      selectedVault: null,
      loading: false,
      error: null,
      activeTab: 'properties',
      
      // Cache management (5 minutes TTL)
      lastFetchTime: null,
      cacheValidityMinutes: 5,
      
      // Secrets
      secrets: [],
      secretsLoading: false,
      secretsError: null,
      revealedSecret: null,
      revealingSecret: null,
      dataPlaneTokenAvailable: true,
      
      // Certificates
      certificates: [],
      certsLoading: false,
      certsError: null,
      
      // Access Policies
      accessPolicies: [],
      vaultDetails: null,
      policiesLoading: false,
      policiesError: null,
      grantingAccess: false,
      grantAccessSuccess: null,
      
      // Sprint 13: UPN Resolution
      principalInfo: {},
      resolvingPrincipals: false
    }
  },
  methods: {
    async fetchKeyVaults(forceRefresh = false) {
      // Check cache validity (5 minutes)
      if (!forceRefresh && this.lastFetchTime && this.keyVaults.length > 0) {
        const now = new Date()
        const timeDiff = (now - this.lastFetchTime) / 1000 / 60 // minutes
        
        if (timeDiff < this.cacheValidityMinutes) {
          console.log(`Using cached Key Vaults data (${timeDiff.toFixed(1)} min old, cache valid for ${this.cacheValidityMinutes} min)`)
          return
        }
      }
      
      this.loading = true
      this.error = null
      
      try {
        // If subscription selected, filter by it; otherwise enumerate ALL
        const url = this.selectedSubscription 
          ? `http://localhost:5000/api/azure/keyvaults?subscription_id=${this.selectedSubscription}`
          : 'http://localhost:5000/api/azure/keyvaults'
        
        const response = await axios.get(url, {
          withCredentials: true
        })
        
        if (response.data.success) {
          this.keyVaults = response.data.key_vaults || []
          this.lastFetchTime = new Date() // Update cache timestamp
          console.log(`Key Vaults data refreshed, cache valid for ${this.cacheValidityMinutes} minutes`)
        } else {
          this.error = response.data.error || 'Failed to fetch key vaults'
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message
      } finally {
        this.loading = false
      }
    },
    
    async loadSubscriptions() {
      try {
        const response = await axios.get('http://localhost:5000/api/azure/subscriptions', {
          withCredentials: true
        })
        
        if (response.data.success) {
          this.subscriptions = response.data.subscriptions
          // Check if no subscriptions - likely no ARM token
          if (this.subscriptions.length === 0) {
            this.error = 'No valid ARM token found'
          } else {
            this.error = null
            // Auto-select if only one subscription (but don't fetch - let user decide)
            if (this.subscriptions.length === 1) {
              this.selectedSubscription = this.subscriptions[0].subscriptionId
            }
          }
        } else {
          this.error = response.data.error || 'Failed to load subscriptions'
        }
      } catch (err) {
        console.error('Failed to load subscriptions:', err)
        this.error = err.response?.data?.error || 'Network error loading subscriptions'
      }
    },
    
    selectVault(vault) {
      this.selectedVault = vault
      this.activeTab = 'properties'
      this.resetTabData()
    },
    
    resetTabData() {
      this.secrets = []
      this.secretsError = null
      this.revealedSecret = null
      this.certificates = []
      this.certsError = null
      this.accessPolicies = []
      this.vaultDetails = null
      this.policiesError = null
      this.grantAccessSuccess = null
      this.principalInfo = {}
    },
    
    getVaultIdB64() {
      if (!this.selectedVault) return null
      return btoa(this.selectedVault.id).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
    },
    
    // ==================== SECRETS ====================
    
    async listSecrets() {
      this.secretsLoading = true
      this.secretsError = null
      this.secrets = []
      
      try {
        const vaultIdB64 = this.getVaultIdB64()
        const response = await axios.get(
          `http://localhost:5000/api/azure/keyvaults/${vaultIdB64}/secrets`,
          { withCredentials: true }
        )
        
        if (response.data.success) {
          this.secrets = response.data.secrets || []
          this.dataPlaneTokenAvailable = true
        } else {
          this.secretsError = response.data.error || 'Failed to list secrets'
          if (response.data.needs_token) {
            this.dataPlaneTokenAvailable = false
          }
        }
      } catch (err) {
        this.secretsError = err.response?.data?.error || err.message
        if (err.response?.status === 403) {
          this.secretsError += ' (Permission denied)'
        }
      } finally {
        this.secretsLoading = false
      }
    },
    
    async revealSecret(secretName) {
      this.revealingSecret = secretName
      
      try {
        const vaultIdB64 = this.getVaultIdB64()
        const response = await axios.get(
          `http://localhost:5000/api/azure/keyvaults/${vaultIdB64}/secrets/${secretName}`,
          { withCredentials: true }
        )
        
        if (response.data.success) {
          this.revealedSecret = response.data.secret
        } else {
          alert('Failed to reveal secret: ' + (response.data.error || 'Unknown error'))
        }
      } catch (err) {
        alert('Error: ' + (err.response?.data?.error || err.message))
      } finally {
        this.revealingSecret = null
      }
    },
    
    // ==================== CERTIFICATES ====================
    
    async listCertificates() {
      this.certsLoading = true
      this.certsError = null
      this.certificates = []
      
      try {
        const vaultIdB64 = this.getVaultIdB64()
        const response = await axios.get(
          `http://localhost:5000/api/azure/keyvaults/${vaultIdB64}/certificates`,
          { withCredentials: true }
        )
        
        if (response.data.success) {
          this.certificates = response.data.certificates || []
          this.dataPlaneTokenAvailable = true
        } else {
          this.certsError = response.data.error || 'Failed to list certificates'
          if (response.data.needs_token) {
            this.dataPlaneTokenAvailable = false
          }
        }
      } catch (err) {
        this.certsError = err.response?.data?.error || err.message
        if (err.response?.status === 403) {
          this.certsError += ' (Permission denied)'
        }
      } finally {
        this.certsLoading = false
      }
    },
    
    // ==================== ACCESS POLICIES ====================
    
    async switchToAccessPolicies() {
      this.activeTab = 'access-policies'
      if (this.accessPolicies.length === 0 && !this.vaultDetails) {
        await this.fetchAccessPolicies()
      }
    },
    
    async fetchAccessPolicies() {
      this.policiesLoading = true
      this.policiesError = null
      this.grantAccessSuccess = null
      
      try {
        const vaultIdB64 = this.getVaultIdB64()
        const response = await axios.get(
          `http://localhost:5000/api/azure/keyvaults/${vaultIdB64}/access-policies`,
          { withCredentials: true }
        )
        
        if (response.data.success) {
          this.accessPolicies = response.data.access_policies || []
          this.vaultDetails = {
            name: response.data.vault_name,
            enableRbacAuthorization: response.data.enableRbacAuthorization
          }
          
          // Sprint 13: Resolve objectId → UPN
          await this.resolvePrincipals()
        } else {
          this.policiesError = response.data.error || 'Failed to fetch access policies'
        }
      } catch (err) {
        this.policiesError = err.response?.data?.error || err.message
      } finally {
        this.policiesLoading = false
      }
    },
    
    async grantSelfAccess() {
      if (!confirm('Grant yourself FULL ACCESS to this Key Vault?\n\nThis will add an access policy with all permissions for secrets, certificates, and keys.')) {
        return
      }
      
      this.grantingAccess = true
      this.policiesError = null
      this.grantAccessSuccess = null
      
      try {
        const vaultIdB64 = this.getVaultIdB64()
        const response = await axios.post(
          `http://localhost:5000/api/azure/keyvaults/${vaultIdB64}/access-policies/grant`,
          {},
          { withCredentials: true }
        )
        
        if (response.data.success) {
          this.grantAccessSuccess = response.data.message || 'Access granted successfully!'
          // Refresh access policies
          await this.fetchAccessPolicies()
        } else {
          this.policiesError = response.data.error || 'Failed to grant access'
        }
      } catch (err) {
        this.policiesError = err.response?.data?.error || err.message
      } finally {
        this.grantingAccess = false
      }
    },
    
    async resolvePrincipals() {
      if (this.accessPolicies.length === 0) return
      
      this.resolvingPrincipals = true
      
      try {
        const objectIds = [...new Set(this.accessPolicies.map(p => p.objectId))]
        
        for (const objectId of objectIds) {
          try {
            const response = await axios.get(
              `http://localhost:5000/api/azure/permissions/resolve-principal/${objectId}`,
              { withCredentials: true }
            )
            
            if (response.data.success) {
              const principal = response.data.principal
              this.principalInfo[objectId] = principal.userPrincipalName || principal.displayName || objectId
            }
          } catch (err) {
            console.log(`[UPN Resolution] Failed for ${objectId}`)
          }
        }
      } finally {
        this.resolvingPrincipals = false
      }
    },
    
    // ==================== HELPERS ====================
    
    formatTimestamp(timestamp) {
      if (!timestamp) return 'N/A'
      const date = new Date(timestamp * 1000)
      return date.toLocaleString()
    },
    
    copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!')
      })
    }
  },
  mounted() {
    this.loadSubscriptions()
    // Enumerate ALL Key Vaults by default (red team scenario: may have resource-level access without subscription role)
    this.fetchKeyVaults()
  }
}
</script>

<style scoped>
.key-vaults-view {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 30px;
  font-weight: bold;
  color: #2c3e50;
  margin: 0;
}

.subtitle {
  font-size: 14px;
  color: #7f8c8d;
  margin: 5px 0 0 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.subscription-select {
  padding: 10px 15px;
  background: white;
  color: #2c3e50;
  border: 1px solid #ddd;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  min-width: 250px;
}

.subscription-select:focus {
  outline: none;
  border-color: #3498db;
}

.subscription-select.dark {
  background: #2d3748;
  color: #f3f4f6;
  border-color: #4a5568;
}

.refresh-btn {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #2980b9;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  background: #fee;
  border: 1px solid #fcc;
  padding: 15px;
  border-radius: 5px;
  color: #c33;
  margin-bottom: 20px;
}

.error .hint {
  margin-top: 10px;
  font-size: 14px;
  color: #666;
}

.warning {
  background: #fff8dc;
  border: 1px solid #ffa500;
  padding: 15px;
  border-radius: 5px;
  color: #856404;
  margin-bottom: 20px;
}

.success {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  padding: 15px;
  border-radius: 5px;
  color: #155724;
  margin-bottom: 20px;
}

.info-box {
  background: #e7f3ff;
  border: 1px solid #b3d9ff;
  padding: 15px;
  border-radius: 5px;
  color: #004085;
  margin-bottom: 20px;
}

/* Vaults Grid */
.vaults-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.vault-card {
  background: white;
  border: 2px solid #3498db;
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
}

.vault-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(52, 152, 219, 0.3);
  border-color: #2980b9;
  background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
}

.vault-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.vault-icon {
  font-size: 32px;
  filter: drop-shadow(0 2px 4px rgba(52, 152, 219, 0.3));
}

.vault-header h3 {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #3498db 0%, #2c3e50 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.vault-details p {
  margin: 10px 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
  display: flex;
  align-items: center;
  gap: 6px;
}

.vault-details p strong {
  color: #1f2937;
  font-weight: 600;
  min-width: 100px;
}

.badge-rbac, .badge-policies {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid;
}

.badge-rbac {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-color: #059669;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);
}

.badge-policies {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border-color: #d97706;
  box-shadow: 0 2px 6px rgba(245, 158, 11, 0.3);
}

/* Vault Details View */
.vault-details-view {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
}

.details-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
  padding: 20px;
  background: #3498db;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

.back-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.6);
  transform: translateX(-4px);
}

.details-header h2 {
  font-size: 28px;
  color: white;
  margin: 0;
  font-weight: 700;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* Tabs */
.tabs {
  display: flex;
  gap: 8px;
  background: #f8fafc;
  padding: 8px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.tab-btn {
  padding: 12px 24px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  color: #64748b;
  transition: all 0.3s ease;
  position: relative;
}

.tab-btn:hover {
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
}

.tab-btn.active {
  color: white;
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.4);
}

/* Tab Content */
.tab-content {
  min-height: 400px;
}

/* Properties Tab */
.properties-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.property-group h3 {
  font-size: 16px;
  font-weight: 700;
  color: white;
  background: #3498db;
  margin: 0;
  padding: 16px 20px;
  border-radius: 12px 12px 0 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.property-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  background: white;
  padding: 24px;
  border: 2px solid #e5e7eb;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* Property items larghi per URI e ID lunghi */
.property-item.wide {
  grid-column: span 2;
}

.property-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border-left: 4px solid #3498db;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.property-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
  border-left-color: #2980b9;
}

.property-label {
  font-weight: 700;
  color: #3498db;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.property-value {
  color: #1f2937;
  font-size: 15px;
  font-weight: 500;
}

.property-value.code {
  font-family: 'Courier New', monospace;
  background: #f1f5f9;
  padding: 8px 12px;
  border-radius: 3px;
  font-size: 13px;
  word-break: break-all;
  overflow-wrap: break-word;
  white-space: normal;
}

.code-block {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 5px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  word-break: break-all;
  color: #333;
}

.tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.tag-item {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 5px;
  font-size: 14px;
}

.tag-key {
  font-weight: 600;
  color: #555;
  margin-right: 5px;
}

.tag-value {
  color: #2c3e50;
}

/* Secrets & Certificates Tabs */
.tab-actions {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 20px;
}

.action-btn {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 600;
}

.action-btn:hover:not(:disabled) {
  background: #2980b9;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.grant-access-btn {
  padding: 10px 20px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 600;
}

.grant-access-btn:hover:not(:disabled) {
  background: #c0392b;
}

.grant-access-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.count-badge {
  background: #ecf0f1;
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 14px;
  color: #555;
  font-weight: 600;
}

.secrets-table, .certificates-table {
  overflow-x: auto;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

th {
  background: #3498db;
  padding: 16px;
  text-align: left;
  font-weight: 700;
  font-size: 13px;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: none;
}

td {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  color: #4b5563;
  font-size: 14px;
}

tr:last-child td {
  border-bottom: none;
}

/* HOVER RIMOSSO - Causava illeggibilità */

.secret-name, .cert-name {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  color: #1f2937;
  font-size: 14px;
}

.thumbprint {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #6b7280;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: inline-block;
}

.status-badge.enabled {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);
}

.status-badge.disabled {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.3);
}

.reveal-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.3);
}

.reveal-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.reveal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 900px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: #3498db;
  border-radius: 12px 12px 0 0;
}

.modal-header h3 {
  margin: 0;
  color: white;
  font-weight: 700;
  font-size: 20px;
}

.close-btn {
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  color: white;
  padding: 0;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: bold;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: scale(1.05);
}

.modal-body {
  padding: 20px;
}

.modal-body p {
  margin-bottom: 15px;
}

.secret-value-container {
  margin-top: 20px;
}

.secret-value-container label {
  display: block;
  font-weight: 700;
  font-size: 15px;
  margin-bottom: 12px;
  color: #3498db;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.secret-value {
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-all;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  color: #c0392b;
  border: 2px solid #e5e7eb;
  margin-bottom: 16px;
  max-height: 300px;
  overflow-y: auto;
  font-weight: 600;
}

.copy-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.3);
}

.copy-btn:hover {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

/* Access Policies Tab */
.policies-container h3 {
  font-size: 18px;
  color: #2c3e50;
  margin-bottom: 15px;
}

.policies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 15px;
}

.policy-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 2px solid #3498db;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.15);
  transition: all 0.3s ease;
}

.policy-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(52, 152, 219, 0.25);
  border-color: #2980b9;
}

.policy-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.policy-icon {
  font-size: 28px;
  filter: drop-shadow(0 2px 4px rgba(52, 152, 219, 0.3));
}

.object-id {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #6b7280;
  background: #f1f5f9;
  padding: 6px 10px;
  border-radius: 6px;
  word-break: break-all;
  border-left: 3px solid #3498db;
}

.policy-permissions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.perm-group {
  font-size: 13px;
  color: #4b5563;
  padding: 10px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 3px solid #10b981;
}

.perm-group strong {
  color: #1f2937;
  font-weight: 700;
  display: inline-block;
  margin-right: 8px;
}

.empty-state {
  text-align: center;
  padding: 60px 40px;
  color: #9ca3af;
  font-size: 16px;
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
  border-radius: 12px;
  border: 2px dashed #d1d5db;
}

/* Sprint 13: Principal Info */
.principal-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.principal-name {
  font-weight: 700;
  font-size: 15px;
  background: linear-gradient(135deg, #3498db 0%, #2c3e50 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.resolving {
  font-size: 12px;
  color: #9ca3af;
  font-style: italic;
}

/* Dark Theme Support - Tailwind Colors */
.key-vaults-view.dark-theme {
  background-color: #111827 !important;
}

.key-vaults-view.dark-theme .header h1,
.key-vaults-view.dark-theme .details-header h2,
.key-vaults-view.dark-theme .property-group h3,
.key-vaults-view.dark-theme .policies-container h3,
.key-vaults-view.dark-theme .vault-header h3,
.key-vaults-view.dark-theme .principal-name,
.key-vaults-view.dark-theme .property-value,
.key-vaults-view.dark-theme .secret-name,
.key-vaults-view.dark-theme .cert-name,
.key-vaults-view.dark-theme .tag-value,
.key-vaults-view.dark-theme .perm-group strong,
.key-vaults-view.dark-theme .modal-header h3,
.key-vaults-view.dark-theme .modal-body p {
  color: #f3f4f6 !important;
}

/* Dark Mode - Property Group H3 Background BLU SCURO */
.key-vaults-view.dark-theme .property-group h3 {
  background: #1e3a8a !important;
}

/* Dark Mode - Subtitle senza background, solo colore grigio chiaro */
.key-vaults-view.dark-theme .subtitle {
  color: #9ca3af !important;
  background: transparent !important;
}

.key-vaults-view.dark-theme .property-label,
.key-vaults-view.dark-theme .vault-details p,
.key-vaults-view.dark-theme .object-id,
.key-vaults-view.dark-theme .tag-key,
.key-vaults-view.dark-theme .perm-group,
.key-vaults-view.dark-theme .resolving,
.key-vaults-view.dark-theme .thumbprint,
.key-vaults-view.dark-theme .count-badge,
.key-vaults-view.dark-theme .tabs {
  background: #1f2937 !important;
}

.key-vaults-view.dark-theme .tab-btn {
  color: #9ca3af !important;
}

.key-vaults-view.dark-theme .tab-btn:hover {
  background: rgba(59, 130, 246, 0.2) !important;
  color: #60a5fa !important;
}

.key-vaults-view.dark-theme .tab-btn.active {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  color: white !important;
}

.key-vaults-view.dark-theme td {
  color: #9ca3af !important;
  border-bottom-color: #374151 !important;
}

.key-vaults-view.dark-theme .vault-card,
.key-vaults-view.dark-theme .vault-details-view,
.key-vaults-view.dark-theme table,
.key-vaults-view.dark-theme .policy-card,
.key-vaults-view.dark-theme .modal-content,
.key-vaults-view.dark-theme .tag-item {
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%) !important;
  border-color: #60a5fa !important;
}

.key-vaults-view.dark-theme .vault-card:hover,
.key-vaults-view.dark-theme .policy-card:hover {
  background: linear-gradient(135deg, #1f2937 0%, #1e293b 100%) !important;
  border-color: #3b82f6 !important;
}

.key-vaults-view.dark-theme th {
  background: #1e3a8a !important;
  color: white !important;
  border: none !important;
}

.key-vaults-view.dark-theme .code-block,
.key-vaults-view.dark-theme .property-value.code {
  background: #374151 !important;
  color: #f3f4f6 !important;
  border-color: #4b5563 !important;
}

/* Dark Mode - Secret Value mantiene colore rosso */
.key-vaults-view.dark-theme .secret-value {
  background: #374151 !important;
  color: #ef4444 !important;
  border-color: #ef4444 !important;
}

.key-vaults-view.dark-theme .details-header,
.key-vaults-view.dark-theme .tabs,
.key-vaults-view.dark-theme .policy-header,
.key-vaults-view.dark-theme .modal-header {
  border-bottom-color: #374151 !important;
}

/* Dark Mode - Modal Header BLU SCURO */
.key-vaults-view.dark-theme .modal-header {
  background: #1e3a8a !important;
}

/* Dark Mode - Details Header con BLU SCURO HD */
.key-vaults-view.dark-theme .details-header {
  background: #1e3a8a !important;
  box-shadow: 0 4px 12px rgba(30, 58, 138, 0.5) !important;
}

.key-vaults-view.dark-theme .error .hint {
  color: #9ca3af !important;
}

.key-vaults-view.dark-theme .empty-state {
  color: #6b7280 !important;
}

.key-vaults-view.dark-theme .count-badge {
  background: #374151 !important;
}

.key-vaults-view.dark-theme .close-btn:hover {
  color: #f3f4f6 !important;
}

/* Dark Mode - Secret Value Label BLU CHIARO */
.key-vaults-view.dark-theme .secret-value-container label {
  color: #60a5fa !important;
  background: transparent !important;
}

/* Dark Mode - Miglioramento Contrasto Testi */

/* Vault Card nella lista */
.key-vaults-view.dark-theme .vault-details p {
  color: #d1d5db !important;
}

.key-vaults-view.dark-theme .vault-details p strong {
  color: #f3f4f6 !important;
}

.key-vaults-view.dark-theme .vault-header h3 {
  background: linear-gradient(135deg, #60a5fa 0%, #f3f4f6 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}

/* Properties Tab */
.key-vaults-view.dark-theme .property-label {
  color: #60a5fa !important;
}

.key-vaults-view.dark-theme .property-value {
  color: #f3f4f6 !important;
}

.key-vaults-view.dark-theme .property-item {
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%) !important;
  border-left-color: #60a5fa !important;
}

.key-vaults-view.dark-theme .property-grid {
  background: #1f2937 !important;
  border-color: #374151 !important;
}

/* Access Policies Tab */
.key-vaults-view.dark-theme .principal-name {
  background: linear-gradient(135deg, #60a5fa 0%, #f3f4f6 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}

.key-vaults-view.dark-theme .object-id {
  color: #d1d5db !important;
  background: #374151 !important;
  border-left-color: #60a5fa !important;
}

.key-vaults-view.dark-theme .perm-group {
  color: #d1d5db !important;
  background: #374151 !important;
  border-left-color: #10b981 !important;
}

.key-vaults-view.dark-theme .perm-group strong {
  color: #f3f4f6 !important;
}

/* Secrets/Certificates Tables */
.key-vaults-view.dark-theme .secret-name,
.key-vaults-view.dark-theme .cert-name {
  color: #f3f4f6 !important;
}

.key-vaults-view.dark-theme .thumbprint {
  color: #d1d5db !important;
  background: #374151 !important;
}

/* Resource ID */
.key-vaults-view.dark-theme .code-block {
  color: #f3f4f6 !important;
}
</style>
