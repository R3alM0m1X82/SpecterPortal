<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/50" @click="close"></div>
    
    <!-- Modal -->
    <div :class="['relative w-full max-w-lg mx-4 rounded-lg shadow-xl', isDark ? 'bg-gray-800' : 'bg-white']">
      <!-- Header -->
      <div :class="['flex items-center justify-between p-4 border-b', isDark ? 'border-gray-700' : 'border-gray-200']">
        <h2 :class="['text-xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">
          🔐 Authenticate
        </h2>
        <button @click="close" :class="['text-2xl leading-none', isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700']">
          ×
        </button>
      </div>
      
      <!-- Tab Navigation -->
      <div :class="['flex border-b', isDark ? 'border-gray-700' : 'border-gray-200']">
        <button
          @click="activeTab = 'device'"
          :class="[
            'flex-1 py-3 px-4 text-sm font-medium transition-colors',
            activeTab === 'device'
              ? 'border-b-2 border-blue-500 text-blue-500'
              : isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          📱 Device Code
        </button>
        <button
          @click="activeTab = 'ropc'"
          :class="[
            'flex-1 py-3 px-4 text-sm font-medium transition-colors',
            activeTab === 'ropc'
              ? 'border-b-2 border-orange-500 text-orange-500'
              : isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          🔑 User/Pass
        </button>
        <button
          @click="activeTab = 'sp'"
          :class="[
            'flex-1 py-3 px-4 text-sm font-medium transition-colors',
            activeTab === 'sp'
              ? 'border-b-2 border-purple-500 text-purple-500'
              : isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          <!-- Service Principal Icon (Entra ID) -->
          <svg class="inline-block w-4 h-4 mr-1" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L4 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V13H5V7.3l7-3.11v8.8z"/>
          </svg>
          Service Principal
        </button>
      </div>
      
      <!-- Content -->
      <div class="p-4">
        <!-- Client ID Selection (Common for Device/ROPC) -->
        <div v-if="activeTab !== 'sp'" class="mb-4">
          <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
            Client Application
          </label>
          
          <!-- Autocomplete Dropdown -->
          <div class="relative">
            <!-- Selected Application Display -->
            <button
              type="button"
              @click="dropdownOpen = !dropdownOpen"
              :class="[
                'w-full px-3 py-2 rounded-lg border text-left flex items-center justify-between',
                isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300 text-gray-900'
              ]"
            >
              <span>{{ selectedAppName }}</span>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </button>
            
            <!-- Dropdown Menu -->
            <div
              v-if="dropdownOpen"
              :class="[
                'absolute z-50 w-full mt-1 rounded-lg border shadow-lg max-h-96 overflow-hidden',
                isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'
              ]"
            >
              <!-- Search Box -->
              <div class="p-2 border-b" :class="isDark ? 'border-gray-600' : 'border-gray-200'">
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="🔍 Search applications..."
                  :class="[
                    'w-full px-3 py-2 rounded border text-sm',
                    isDark ? 'bg-gray-800 border-gray-600 text-gray-100 placeholder-gray-500' : 'bg-gray-50 border-gray-300 text-gray-900'
                  ]"
                  @click.stop
                />
              </div>
              
              <!-- Applications List -->
              <div class="overflow-y-auto max-h-80">
                <!-- Popular Applications -->
                <div v-if="popularApplications.length > 0">
                  <div 
                    :class="['px-3 py-2 text-xs font-semibold uppercase tracking-wider', isDark ? 'text-gray-400 bg-gray-800' : 'text-gray-600 bg-gray-50']"
                  >
                    📌 Popular ({{ popularApplications.length }})
                  </div>
                  <button
                    v-for="app in popularApplications"
                    :key="app.id"
                    type="button"
                    @click="selectApplication(app.id)"
                    :class="[
                      'w-full px-4 py-2 text-left text-sm hover:bg-opacity-80 transition-colors',
                      selectedClientId === app.id 
                        ? (isDark ? 'bg-blue-900 text-blue-200' : 'bg-blue-100 text-blue-800')
                        : (isDark ? 'hover:bg-gray-600 text-gray-200' : 'hover:bg-gray-100 text-gray-800')
                    ]"
                  >
                    {{ app.name }}
                  </button>
                </div>
                
                <!-- All Other Applications -->
                <div v-if="otherApplications.length > 0">
                  <div 
                    :class="['px-3 py-2 text-xs font-semibold uppercase tracking-wider', isDark ? 'text-gray-400 bg-gray-800' : 'text-gray-600 bg-gray-50']"
                  >
                    📋 All Applications ({{ otherApplications.length }})
                  </div>
                  <button
                    v-for="app in otherApplications"
                    :key="app.id"
                    type="button"
                    @click="selectApplication(app.id)"
                    :class="[
                      'w-full px-4 py-2 text-left text-sm hover:bg-opacity-80 transition-colors',
                      selectedClientId === app.id 
                        ? (isDark ? 'bg-blue-900 text-blue-200' : 'bg-blue-100 text-blue-800')
                        : (isDark ? 'hover:bg-gray-600 text-gray-200' : 'hover:bg-gray-100 text-gray-800')
                    ]"
                  >
                    {{ app.name }}
                  </button>
                </div>
                
                <!-- No Results -->
                <div 
                  v-if="filteredApplications.length === 0"
                  :class="['px-4 py-8 text-center text-sm', isDark ? 'text-gray-400' : 'text-gray-500']"
                >
                  No applications found matching "{{ searchQuery }}"
                </div>
                
                <!-- Custom Client ID Option -->
                <div :class="['border-t', isDark ? 'border-gray-600' : 'border-gray-200']">
                  <button
                    type="button"
                    @click="selectApplication('custom')"
                    :class="[
                      'w-full px-4 py-2 text-left text-sm hover:bg-opacity-80 transition-colors',
                      selectedClientId === 'custom'
                        ? (isDark ? 'bg-purple-900 text-purple-200' : 'bg-purple-100 text-purple-800')
                        : (isDark ? 'hover:bg-gray-600 text-gray-300' : 'hover:bg-gray-100 text-gray-700')
                    ]"
                  >
                    ⚙️ Custom Client ID...
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Custom Client ID Input -->
          <input
            v-if="selectedClientId === 'custom'"
            v-model="customClientId"
            type="text"
            placeholder="Enter custom Client ID (GUID)"
            :class="[
              'w-full mt-2 px-3 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500',
              isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900'
            ]"
          />
        </div>
        
        <!-- Device Code Flow Tab -->
        <div v-if="activeTab === 'device'">
          <!-- State: Not Started -->
          <div v-if="deviceState === 'idle'">
            <p :class="['text-sm mb-4', isDark ? 'text-gray-400' : 'text-gray-600']">
              Device Code Flow works like PowerShell authentication. You'll get a code to enter in your browser.
            </p>
            <button
              @click="startDeviceCode"
              :disabled="loading"
              class="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
            >
              {{ loading ? 'Starting...' : '🚀 Start Authentication' }}
            </button>
          </div>
          
          <!-- State: Code Received -->
          <div v-else-if="deviceState === 'code_received'">
            <div :class="['p-4 rounded-lg mb-4 text-center', isDark ? 'bg-gray-700' : 'bg-blue-50']">
              <p :class="['text-sm mb-2', isDark ? 'text-gray-300' : 'text-gray-600']">
                Go to this URL and enter the code:
              </p>
              <a
                :href="deviceData.verification_uri"
                target="_blank"
                class="text-blue-500 hover:text-blue-600 font-medium block mb-3"
              >
                {{ deviceData.verification_uri }}
              </a>
              <div :class="['text-3xl font-mono font-bold tracking-widest py-3 px-4 rounded', isDark ? 'bg-gray-600 text-white' : 'bg-white text-gray-900']">
                {{ deviceData.user_code }}
              </div>
              <button
                @click="copyCode"
                :class="['mt-2 text-sm', codeCopied ? 'text-green-500' : isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500']"
              >
                {{ codeCopied ? '✓ Copied!' : '📋 Copy Code' }}
              </button>
            </div>
            
            <!-- Polling Status -->
            <div class="text-center">
              <div class="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
              <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                {{ pollingMessage }}
              </p>
              <p :class="['text-xs mt-1', isDark ? 'text-gray-500' : 'text-gray-400']">
                Expires in {{ remainingTime }}s
              </p>
            </div>
            
            <button
              @click="cancelDeviceCode"
              :class="['w-full mt-4 py-2 px-4 rounded-lg font-medium', isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300']"
            >
              Cancel
            </button>
          </div>
          
          <!-- State: Success -->
          <div v-else-if="deviceState === 'success'">
            <div class="text-center py-4">
              <div class="text-5xl mb-3">✅</div>
              <h3 :class="['text-lg font-semibold mb-2', isDark ? 'text-gray-100' : 'text-gray-800']">
                Authentication Successful!
              </h3>
              <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                Token for {{ successData?.upn || successData?.app_name || 'user' }} has been added.
              </p>
            </div>
            <button
              @click="close"
              class="w-full py-2 px-4 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700"
            >
              Done
            </button>
          </div>
        </div>
        
        <!-- ROPC Tab -->
        <div v-else-if="activeTab === 'ropc'">
          <!-- Warning -->
          <div :class="['p-3 rounded-lg mb-4 text-sm', isDark ? 'bg-orange-900/30 text-orange-300' : 'bg-orange-50 text-orange-700']">
            ⚠️ <strong>Lab Use Only!</strong> ROPC doesn't work with MFA-enabled accounts.
          </div>
          
          <div class="space-y-4">
            <div>
              <label :class="['block text-sm font-medium mb-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                Username (UPN)
              </label>
              <input
                v-model="ropcUsername"
                type="email"
                placeholder="user@domain.com"
                :class="[
                  'w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-orange-500',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900'
                ]"
              />
            </div>
            
            <div>
              <label :class="['block text-sm font-medium mb-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                Password
              </label>
              <input
                v-model="ropcPassword"
                type="password"
                placeholder="••••••••"
                :class="[
                  'w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-orange-500',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900'
                ]"
                @keyup.enter="authenticateRopc"
              />
            </div>
            
            <!-- Tenant ID Field (Optional) -->
            <div>
              <label :class="['block text-sm font-medium mb-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                Tenant ID <span :class="['text-xs font-normal', isDark ? 'text-gray-500' : 'text-gray-400']">(Optional)</span>
              </label>
              <input
                v-model="ropcTenantId"
                type="text"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                :class="[
                  'w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-orange-500',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900'
                ]"
              />
              <p :class="['text-xs mt-1', isDark ? 'text-gray-500' : 'text-gray-400']">
                💡 Leave empty to use default. Specify tenant GUID if user is synced to multiple tenants.
              </p>
            </div>
            
            <button
              @click="authenticateRopc"
              :disabled="loading || !ropcUsername || !ropcPassword"
              class="w-full py-3 px-4 bg-orange-600 text-white rounded-lg font-semibold hover:bg-orange-700 disabled:opacity-50"
            >
              {{ loading ? 'Authenticating...' : '🔑 Authenticate' }}
            </button>
          </div>
        </div>
        
        <!-- Service Principal Tab -->
        <div v-else-if="activeTab === 'sp'">
          <!-- Info -->
          <div :class="['p-3 rounded-lg mb-4 text-sm', isDark ? 'bg-purple-900/30 text-purple-300' : 'bg-purple-50 text-purple-700']">
            🔐 Authenticate as Service Principal using Client Credentials flow
          </div>
          
          <div class="space-y-4">
            <div>
              <label :class="['block text-sm font-medium mb-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                Client ID (Application ID)
              </label>
              <input
                v-model="spClientId"
                type="text"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                :class="[
                  'w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-purple-500',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900'
                ]"
              />
            </div>
            
            <div>
              <label :class="['block text-sm font-medium mb-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                Client Secret
              </label>
              <input
                v-model="spClientSecret"
                type="password"
                placeholder="Enter application secret"
                :class="[
                  'w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-purple-500',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900'
                ]"
                @keyup.enter="authenticateSP"
              />
            </div>
            
            <div>
              <label :class="['block text-sm font-medium mb-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                Tenant ID
              </label>
              <input
                v-model="spTenantId"
                type="text"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                :class="[
                  'w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-purple-500',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900'
                ]"
              />
              <p :class="['text-xs mt-1', isDark ? 'text-gray-500' : 'text-gray-400']">
                💡 The Azure AD tenant where the Service Principal is registered
              </p>
            </div>
            
            <div>
              <label :class="['block text-sm font-medium mb-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                Scope/Resource
              </label>
              <select
                v-model="spScope"
                :class="[
                  'w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-purple-500',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300 text-gray-900'
                ]"
              >
                <option value="https://graph.microsoft.com/.default">Microsoft Graph API</option>
                <option value="https://management.azure.com/.default">Azure Management (ARM)</option>
                <option value="https://vault.azure.net/.default">Azure Key Vault</option>
                <option value="https://storage.azure.com/.default">Azure Storage</option>
              </select>
            </div>
            
            <button
              @click="authenticateSP"
              :disabled="loading || !spClientId || !spClientSecret || !spTenantId"
              class="w-full py-3 px-4 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50"
            >
              {{ loading ? 'Authenticating...' : '🔐 Authenticate as SP' }}
            </button>
          </div>
        </div>
        
        <!-- Error Display -->
        <div v-if="error" :class="['mt-4 p-3 rounded-lg text-sm', isDark ? 'bg-red-900/30 text-red-300' : 'bg-red-50 text-red-700']">
          ❌ {{ error }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:5000/api'

const props = defineProps({
  isOpen: Boolean,
  isDark: Boolean
})

const emit = defineEmits(['close', 'success'])

// State
const activeTab = ref('device')
const selectedClientId = ref('14d82eec-204b-4c2f-b7e8-296a70dab67e')
const customClientId = ref('')
const loading = ref(false)
const error = ref('')

// Device Code Flow state
const deviceState = ref('idle') // idle, code_received, success
const deviceData = ref(null)
const pollingInterval = ref(null)
const pollingMessage = ref('Waiting for authentication...')
const remainingTime = ref(0)
const countdownInterval = ref(null)
const successData = ref(null)
const codeCopied = ref(false)
const pollAttempts = ref(0) // Track polling attempts for timeout (max 60 = 5 minutes)

// ROPC state
const ropcUsername = ref('')
const ropcPassword = ref('')
const ropcTenantId = ref('')

// Service Principal state
const spClientId = ref('')
const spClientSecret = ref('')
const spTenantId = ref('')
const spScope = ref('https://graph.microsoft.com/.default')

// Computed
const effectiveClientId = computed(() => {
  return selectedClientId.value === 'custom' ? customClientId.value : selectedClientId.value
})

// Client Applications (138 apps with Device Code Flow support)
const clientApplications = [
  // Popular applications (most powerful scopes)
  { id: '14d82eec-204b-4c2f-b7e8-296a70dab67e', name: 'Microsoft Graph PowerShell', popular: true },
  { id: '1950a258-227b-4e31-a9cf-717495945fc2', name: 'Microsoft Azure PowerShell', popular: true },
  { id: 'd3590ed6-52b3-4102-aeff-aad2292ab01c', name: 'Microsoft Office', popular: true },
  { id: '1fec8e78-bce4-4aaf-ab1b-5451cc387264', name: 'Microsoft Teams', popular: true },
  { id: '04b07795-8ddb-461a-bbee-02f9e1bf7b46', name: 'Microsoft Azure CLI', popular: true },
  { id: '0b107b34-72a8-4081-a8ca-f3ecb0937531', name: 'Microsoft Azure', popular: true },
  { id: '2e307cd5-5d2d-4499-b656-a97de9f52708', name: 'Modern Workplace Customer API Native', popular: true },
  { id: '00b41c95-dab0-4487-9791-b9d2c32c80f2', name: 'Office 365 Management', popular: true },
  
  // All other applications (alphabetically)
  { id: '90f610bf-206d-4950-b61d-37fa6fd1b224', name: 'Aadrm Admin Powershell', popular: false },
  { id: 'b90d5b8f-5503-4153-b545-b31cecfaece2', name: 'AADJ CSP', popular: false },
  { id: '1b730954-1685-4b74-9bfd-dac224a7b894', name: 'Azure Active Directory PowerShell', popular: false },
  { id: 'cb1056e2-e479-49de-ae31-7812af012ed8', name: 'Microsoft Azure Active Directory Connect', popular: false },
  { id: 'bb301b1f-c8f3-473a-9ff5-7ad970c639c2', name: 'Azure Analysis Services User Picker', popular: false },
  { id: 'cf6d7e68-f018-4e0a-a7b3-126e053fb88d', name: 'Azure AD Connect Health Agent', popular: false },
  { id: '55747057-9b5d-4bd4-b387-abf52a8bd489', name: 'Azure AD Application Proxy Connector', popular: false },
  { id: 'c00e9d32-3c8d-4a7d-832b-029040e7db99', name: 'Microsoft Azure Information Protection', popular: false },
  { id: 'a69788c6-1d43-44ed-9ca3-b83e194da255', name: 'Azure Data Studio', popular: false },
  { id: 'a94f9c62-97fe-4d19-b06d-472bed8d2bcf', name: 'Azure SQL Database and Data Warehouse', popular: false },
  { id: '5217e4ff-9fc6-4207-ac4e-d1cb98e21d6e', name: 'ContainerInsightsExt 1st Party AAD App', popular: false },
  { id: 'd0df5b7c-9183-4f34-89de-c64ef4a5e1f3', name: 'CortanaUWPClient', popular: false },
  { id: 'de50c81f-5f80-4771-b66b-cebd28ccdfc1', name: 'Device Management Client', popular: false },
  { id: 'db662dc1-0cfe-4e1c-a843-19a68e65be58', name: 'KustoClient', popular: false },
  { id: '2ad88395-b77d-4561-9441-d0e40824f9bc', name: 'Dynamics 365 Development Tools', popular: false },
  { id: '51f81489-12ee-4a9e-aaae-a2591f45987d', name: 'Dynamics 365 Example Client Application', popular: false },
  { id: '67ae0dc4-5f97-4c38-b132-65d38bbab8d1', name: 'Dynamics AX Workflow Editor', popular: false },
  { id: '4906f920-9f94-4f14-98aa-8456dd5f78a8', name: 'Dynamics CRM Unified Service Desk', popular: false },
  { id: 'ce9f9f18-dd0c-473e-b9b2-47812435e20d', name: 'Microsoft Dynamics CRM for tablets and phones', popular: false },
  { id: 'd5527362-3bc8-4e63-b5b3-606dc14747e9', name: 'Dynamics Retail Cloud POS', popular: false },
  { id: 'd6b5a0bd-bf3f-4a8c-b370-619fb3d0e1cc', name: 'Dynamics Retail Modern POS', popular: false },
  { id: '2f3b013e-5dc4-4b2a-831f-47ba08353237', name: 'Microsoft Dynamics 365 Project Service Automation Add-in for Microsoft Project', popular: false },
  { id: '1a20851a-696e-4c7e-96f4-c282dfe48872', name: 'Editor Browser Extension', popular: false },
  { id: '60c8bde5-3167-4f92-8fdb-059f6176dc0f', name: 'Enterprise Roaming and Backup', popular: false },
  { id: '0973ecd5-7828-4430-9548-bb2331536767', name: 'Feedback Hub', popular: false },
  { id: '0922ef46-e1b9-4f7e-9134-9ad00547eb41', name: 'Loop', popular: false },
  { id: '3b68e96c-82d3-41b3-99b8-56c260cf38d8', name: 'Managed Home Screen', popular: false },
  { id: '1f7f6f43-2f81-429c-8499-293566d0ab0c', name: 'Get Help', popular: false },
  { id: '52c2e0b5-c7b6-4d11-a89c-21e42bcec444', name: 'Graph Files Manager', popular: false },
  { id: '6af07558-09e0-40fd-8af6-7759d010cf82', name: 'HDIUX_APP', popular: false },
  { id: '6b11041d-54a2-4c4f-96a2-6053efe46d8b', name: 'HoloLens Camera Roll Upload', popular: false },
  { id: 'f36c30df-d241-4c14-a0ee-752c71e4d3da', name: 'IDS-PROD', popular: false },
  { id: '3dd3a51e-8d76-4cca-ac35-5537c1319211', name: 'Windows App - iOS', popular: false },
  { id: '4ec7f63c-188f-4433-9253-ccbe3021125f', name: 'IntuneBMR1PApp', popular: false },
  { id: '7db04568-724f-4632-be9d-fa6e2d14c2b0', name: 'JDBC Client Driver', popular: false },
  { id: 'cb5b7de5-2ef8-4fb2-9600-9feadb91dc45', name: 'Microsoft Launcher', popular: false },
  { id: '3aa85724-c5ce-42f5-b7f9-36b5a387b7b4', name: 'Windows Admin Center', popular: false },
  { id: '3d5cffa9-04da-4657-8cab-c7f074657cad', name: 'M365 Commerce Client', popular: false },
  { id: 'f448d7e5-e313-4f90-a3eb-5dbb3277e4b3', name: 'Media Recording for Dynamics 365 Sales', popular: false },
  { id: 'eea619ad-603a-4b03-a386-860fcc7410d1', name: 'Microsoft Mesh', popular: false },
  { id: '655db33f-4580-4e63-bad1-4618764badb9', name: 'MicrosoftDynamics365MRGuidesCoreClient', popular: false },
  { id: 'aaa651fc-734c-48a1-8c37-ad1724b2088c', name: 'Microsoft Nonprofit Portal', popular: false },
  { id: 'a2a1fecc-b06e-4a1e-95c1-2afd94bcadff', name: 'Microsoft People', popular: false },
  { id: '5c17a0cf-5493-4b86-b23d-dabc1cc46f5a', name: 'Minit Desktop for Windows', popular: false },
  { id: '2e246ed0-1ec0-4526-a2de-9e9ff9468494', name: 'Microsoft Power Automate SDX Plugin', popular: false },
  { id: '2e307cd5-5d2d-4499-b656-a97de9f52708', name: 'Modern Workplace Customer API Native', popular: false },
  { id: '18fbca16-2224-45f6-85b0-f7bf2b39b3f3', name: 'Microsoft Docs', popular: false },
  { id: '4813382a-8fa7-425e-ab75-3b753aab3abb', name: 'Microsoft Authenticator App', popular: false },
  { id: '29d9ed98-a469-4536-ade2-f981bc1d605e', name: 'Microsoft Authentication Broker', popular: false },
  { id: 'cf36b471-5b44-428c-9ce7-313bf84528de', name: 'Microsoft Bing Search', popular: false },
  { id: 'cab96880-db5b-4e15-90a7-f3f1d62ffe39', name: 'Microsoft Defender Platform', popular: false },
  { id: 'dd47d17a-3194-4d86-bfd5-c6ae6f5651e3', name: 'Microsoft Defender for Mobile', popular: false },
  { id: 'dd762716-544d-4aeb-a526-687b73838a22', name: 'Microsoft Device Registration Client', popular: false },
  { id: 'e9c51622-460d-4d3d-952d-966a5b1da34c', name: 'Microsoft Edge', popular: false },
  { id: 'ecd6b820-32c2-49b6-98a6-444530e5a77a', name: 'Microsoft Edge', popular: false },
  { id: 'f44b1140-bc5e-48c6-8dc0-5cf5a53c0e34', name: 'Microsoft Edge', popular: false },
  { id: 'd7b530a4-7680-4c23-a8bf-c52c121d2e87', name: 'Microsoft Edge Enterprise New Tab Page', popular: false },
  { id: '82864fa0-ed49-4711-8395-a0e6003dca1f', name: 'Microsoft Edge MSAv2', popular: false },
  { id: 'fb78d390-0c51-40cd-8e17-fdbfab77341b', name: 'Microsoft Exchange REST API Based Powershell', popular: false },
  { id: '4d097d71-f71f-450b-8b44-f638d5d1b5d6', name: 'PhysOps.Clients.Worker', popular: false },
  { id: '4d2f5175-f06b-49e2-9f4a-8e614a8abc03', name: 'Microsoft Exchange Hybrid Wizard', popular: false },
  { id: '9bc3ab49-b65d-410a-85ad-de819febfddc', name: 'Microsoft SharePoint Online Management Shell', popular: false },
  { id: 'fc0f3af4-6835-4174-b806-f7db311fd2f3', name: 'Microsoft Intune Windows Agent', popular: false },
  { id: '9ba1a5c7-f17a-4de9-a1f1-6178c8d51223', name: 'Microsoft Intune Company Portal', popular: false },
  { id: 'b743a22d-6705-4147-8670-d92fa515ee2b', name: 'Microsoft Intune Company Portal for Linux', popular: false },
  { id: 'a670efe7-64b6-454f-9ae9-4f1cf27aba58', name: 'Microsoft Lists App on Android', popular: false },
  { id: '5d661950-3475-41cd-a2c3-d671a3162bc1', name: 'Microsoft Outlook', popular: false },
  { id: 'c0d2a505-13b8-4ae0-aa9e-cddd5eab0b12', name: 'Microsoft Power BI', popular: false },
  { id: '66375f6b-983f-4c2c-9701-d680650f588f', name: 'Microsoft Planner', popular: false },
  { id: 'a672d62c-fc7b-4e81-a576-e60dc46e951d', name: 'Microsoft Power Query for Excel', popular: false },
  { id: 'fca5a20d-55aa-4395-9c2f-c6147f3c9ffa', name: 'Microsoft Remote Assist', popular: false },
  { id: 'aba285d5-d9f3-427b-a994-e9deb4567639', name: 'Microsoft SQL Server', popular: false },
  { id: '22098786-6e16-43cc-a27d-191a01a1e3b5', name: 'Microsoft To-Do client', popular: false },
  { id: '57336123-6e14-4acc-8dcf-287b6088aa28', name: 'Microsoft Whiteboard Client', popular: false },
  { id: 'd7813711-9094-4ad3-a062-cac3ec74ebe8', name: 'Microsoft.Azure.Services.AppAuthentication', popular: false },
  { id: '12128f48-ec9e-42f0-b203-ea49fb6af367', name: 'MS Teams Powershell Cmdlets', popular: false },
  { id: '540d4ff4-b4c0-44c1-bd06-cab1782d582a', name: 'ODSP Mobile Lists App', popular: false },
  { id: '2c1229aa-16c5-4ff5-b46b-4f7fe2a2a9c8', name: 'ODBC Client Driver', popular: false },
  { id: 'e28ff72c-58a5-49ba-8125-42ec264d7cd0', name: 'Office Browser Extension', popular: false },
  { id: '0ec893e0-5785-4de6-99da-4ed124e5296c', name: 'Office UWP PWA', popular: false },
  { id: 'd2eb9fef-f34c-40ec-b6a3-4bf524065158', name: 'Office voice transcript generator AAD', popular: false },
  { id: 'af124e86-4e96-495a-b70a-90f90ab96707', name: 'OneDrive iOS App', popular: false },
  { id: 'b26aadf8-566f-4478-926f-589f601d9c74', name: 'OneDrive', popular: false },
  { id: 'ab9b8c07-8f02-4f72-87fa-80105867a763', name: 'OneDrive SyncEngine', popular: false },
  { id: '27922004-5251-4030-b22d-91ecd9a37ea4', name: 'Outlook Mobile', popular: false },
  { id: 'e9b154d0-7658-433b-bb25-6b8e0a8a7c59', name: 'Outlook Lite', popular: false },
  { id: '9cee029c-6210-4654-90bb-17e6e9d36617', name: 'Power Platform CLI - pac', popular: false },
  { id: '386ce8c0-7421-48c9-a1df-2a532400339f', name: 'Power Automate Desktop For Windows', popular: false },
  { id: 'ee90a17f-1cb7-4909-be27-dfc2dcc4dc15', name: 'Power Automate Desktop', popular: false },
  { id: '041e4c2d-ba3e-46a1-9347-5bc4054c8af4', name: 'Power Automate Desktop GCC', popular: false },
  { id: '4e291c71-d680-4d0e-9640-0a3358e31177', name: 'PowerApps', popular: false },
  { id: '3e62f81e-590b-425b-9531-cad6683656cf', name: 'PowerApps - apps.powerapps.com', popular: false },
  { id: '7f67af8a-fedc-4b08-8b4e-37c4d127b6cf', name: 'Power BI Desktop', popular: false },
  { id: 'ea0616ba-638b-4df5-95b9-636659ae5121', name: 'Power BI Gateway', popular: false },
  { id: 'd326c1ce-6cc6-4de2-bebc-4591e5e13ef0', name: 'SharePoint', popular: false },
  { id: 'c58637bb-e2e1-4312-8a00-04b5ffcd3403', name: 'SharePoint Online Client Extensibility', popular: false },
  { id: 'f05ff7c9-f75a-4acd-a3b5-f4b6a870245d', name: 'SharePoint Android', popular: false },
  { id: 'fdd7719f-d61e-4592-b501-793734eb8a0e', name: 'SharePointMigrationTool', popular: false },
  { id: '4d079b4c-cab7-4b7c-a115-8fd51b6f8239', name: 'SQL DotNet Client', popular: false },
  { id: '7fba38f4-ec1f-458d-906c-f4e3c4f41335', name: 'Sticky Notes Client', popular: false },
  { id: '507a7586-da5c-4e86-80f2-2bc2e55ae394', name: 'Surface Dashboard', popular: false },
  { id: '47a4f6b2-25dc-4851-8524-fffe7360e8d4', name: 'Surface App', popular: false },
  { id: '60dd25e4-9d08-44fa-9b18-280cff19b15b', name: 'Surface Hub and Microsoft Teams Room Device Management', popular: false },
  { id: '8ec6bc83-69c8-4392-8f08-b3c986009232', name: 'Microsoft Teams-T4L', popular: false },
  { id: '61c8fd69-c13e-4ee6-aaa6-24ff71c09bca', name: 'Teams SIP Gateway', popular: false },
  { id: '7ea7c24c-b1f6-4a20-9d11-9ae12e9e7ac0', name: 'Teams-Toolkit', popular: false },
  { id: '74374a04-182f-444f-9dad-3978d27aad44', name: 'O365 Network Onboarding Tool', popular: false },
  { id: 'aad98258-6bb0-44ed-a095-21506dfb68fe', name: 'Universal Print PS Module', popular: false },
  { id: 'dae89220-69ba-4957-a77a-47b78695e883', name: 'Universal Print Native Client', popular: false },
  { id: '706247ff-cdd6-4957-8377-c65e91c8d532', name: 'Universal Print Mac Client', popular: false },
  { id: '268761a2-03f3-40df-8a8b-c3db24145b6b', name: 'Universal Store Native Client', popular: false },
  { id: 'aebc6443-996d-45c2-90f0-388ff96faa56', name: 'Visual Studio Code', popular: false },
  { id: '04f0c124-f2bc-4f59-8241-bf6df9866bbd', name: 'Visual Studio', popular: false },
  { id: '872cd9fa-d31f-45e0-9eab-6e460a02d1f1', name: 'Visual Studio - Legacy', popular: false },
  { id: '63896e48-3d27-4ce2-9968-610b4af62c5d', name: 'Windows App - macOS', popular: false },
  { id: 'cbf8c392-4ffb-4d85-9d4a-f7678d381a1f', name: 'Windows App - Android', popular: false },
  { id: '4fb5cc57-dbbc-4cdc-9595-748adff5f414', name: 'Windows 365 Client', popular: false },
  { id: 'ebde7daf-df42-4ade-81a4-d67b339b49e9', name: 'Windows Clock', popular: false },
  { id: '1b3c667f-cde3-4090-b60b-3d2abd0117f0', name: 'Windows Spotlight', popular: false },
  { id: '26a7ee05-5602-4d76-a7ba-eae8b7b67941', name: 'Windows Search', popular: false },
  { id: 'a8759234-4b8b-4d94-8c0a-ee1ab73af270', name: 'WindowsShareExperienceProd', popular: false },
  { id: '0dc2408a-bbc0-4238-871e-13b372f0200f', name: 'Windows Insider Program', popular: false },
  { id: '61ae9cd9-7bca-458c-affc-861e2f24ba3b', name: 'Windows Update for Business Deployment Service', popular: false },
  { id: 'a569458c-7f2b-45cb-bab9-b7dee514d112', name: 'Yammer iPhone', popular: false },
  { id: '038ddad9-5bbe-4f64-b0cd-12434d1e633b', name: 'ZTNA Network Access Client', popular: false },
  { id: 'd5e23a82-d7e1-4886-af25-27037a0fdc2a', name: 'ZTNA Network Access Client -- M365', popular: false },
  { id: '57fcbcfa-7cee-4eb1-8b25-12d2030b4ee0', name: 'Microsoft Flow', popular: false },
  { id: '0c1307d4-29d6-4389-a11c-5cbe7f65d7fa', name: 'Microsoft Azure', popular: false }
]

// Autocomplete state
const searchQuery = ref('')
const dropdownOpen = ref(false)

// Filtered applications
const filteredApplications = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  
  if (!query) {
    return clientApplications
  }
  
  return clientApplications.filter(app => 
    app.name.toLowerCase().includes(query)
  )
})

const popularApplications = computed(() => 
  filteredApplications.value.filter(app => app.popular)
)

const otherApplications = computed(() => 
  filteredApplications.value.filter(app => !app.popular)
)

const selectApplication = (appId) => {
  selectedClientId.value = appId
  dropdownOpen.value = false
  searchQuery.value = ''
}

const selectedAppName = computed(() => {
  if (selectedClientId.value === 'custom') {
    return 'Custom Client ID...'
  }
  const app = clientApplications.find(a => a.id === selectedClientId.value)
  return app ? app.name : 'Unknown Application'
})


// Methods
const close = () => {
  cancelDeviceCode()
  resetState()
  emit('close')
}

const resetState = () => {
  deviceState.value = 'idle'
  deviceData.value = null
  error.value = ''
  successData.value = null
  ropcUsername.value = ''
  ropcPassword.value = ''
  ropcTenantId.value = ''
  spClientId.value = ''
  spClientSecret.value = ''
  spTenantId.value = ''
  codeCopied.value = false
  dropdownOpen.value = false
  searchQuery.value = ''
}

const copyCode = async () => {
  if (deviceData.value?.user_code) {
    try {
      await navigator.clipboard.writeText(deviceData.value.user_code)
      codeCopied.value = true
      setTimeout(() => {
        codeCopied.value = false
      }, 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }
}

// Device Code Flow
const startDeviceCode = async () => {
  if (!effectiveClientId.value) {
    error.value = 'Please select or enter a Client ID'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.post(`${API_BASE}/auth/device-code/start`, {
      client_id: effectiveClientId.value,
      scope: 'https://graph.microsoft.com/.default offline_access'
    })
    
    if (response.data.success) {
      deviceData.value = response.data
      deviceState.value = 'code_received'
      remainingTime.value = response.data.expires_in || 900
      
      // Start polling
      startPolling(response.data.interval || 5)
      
      // Start countdown
      countdownInterval.value = setInterval(() => {
        remainingTime.value--
        if (remainingTime.value <= 0) {
          cancelDeviceCode()
          error.value = 'Device code expired. Please try again.'
        }
      }, 1000)
    } else {
      error.value = response.data.error || 'Failed to start device code flow'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message || 'Network error'
  } finally {
    loading.value = false
  }
}

const startPolling = (interval) => {
  // Reset attempts counter
  pollAttempts.value = 0
  const MAX_ATTEMPTS = 60 // 60 attempts * 5s = 5 minutes
  
  pollingInterval.value = setInterval(async () => {
    // Increment attempts counter
    pollAttempts.value++
    
    // Check timeout (60 attempts = 5 minutes with 5s interval)
    if (pollAttempts.value >= MAX_ATTEMPTS) {
      cancelDeviceCode()
      error.value = '⏱️ Authentication timeout (5 minutes). Please restart the authentication process.'
      console.warn('[DEVICE-CODE] Frontend timeout after', pollAttempts.value, 'attempts')
      return
    }
    
    try {
      const response = await axios.post(`${API_BASE}/auth/device-code/poll`, {
        client_id: effectiveClientId.value,
        device_code: deviceData.value.device_code
      })
      
      if (response.data.success) {
        // Got token!
        cancelPolling()
        successData.value = response.data
        deviceState.value = 'success'
        emit('success', response.data)
      } else if (response.data.status === 'expired') {
        // Backend timeout (5 minutes)
        cancelDeviceCode()
        error.value = '⏱️ Device code expired. Please restart the authentication process.'
        console.warn('[DEVICE-CODE] Backend timeout - device code expired')
      } else if (response.data.status === 'pending') {
        pollingMessage.value = `Waiting for authentication... (${pollAttempts.value}/${MAX_ATTEMPTS})`
      } else if (response.data.status === 'slow_down') {
        pollingMessage.value = 'Slowing down...'
      } else {
        // Error
        cancelDeviceCode()
        error.value = response.data.error || 'Authentication failed'
      }
    } catch (err) {
      // Network error during polling - continue
      console.warn('Polling error:', err.message)
    }
  }, interval * 1000)
}

const cancelPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
    countdownInterval.value = null
  }
}

const cancelDeviceCode = () => {
  cancelPolling()
  deviceState.value = 'idle'
  deviceData.value = null
  pollAttempts.value = 0 // Reset attempts counter
}

// ROPC Flow
const authenticateRopc = async () => {
  if (!effectiveClientId.value) {
    error.value = 'Please select or enter a Client ID'
    return
  }
  
  if (!ropcUsername.value || !ropcPassword.value) {
    error.value = 'Username and password are required'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const payload = {
      username: ropcUsername.value,
      password: ropcPassword.value,
      client_id: effectiveClientId.value,
      scope: 'https://graph.microsoft.com/.default offline_access'
    }
    
    // Add tenant_id only if provided
    if (ropcTenantId.value && ropcTenantId.value.trim()) {
      payload.tenant_id = ropcTenantId.value.trim()
    }
    
    const response = await axios.post(`${API_BASE}/auth/ropc`, payload)
    
    if (response.data.success) {
      successData.value = response.data
      activeTab.value = 'device' // Switch to device tab to show success
      deviceState.value = 'success'
      emit('success', response.data)
    } else {
      error.value = response.data.error || 'Authentication failed'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message || 'Authentication failed'
  } finally {
    loading.value = false
  }
}

// Service Principal Flow
const authenticateSP = async () => {
  if (!spClientId.value || !spClientSecret.value || !spTenantId.value) {
    error.value = 'Client ID, Secret and Tenant ID are required'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.post(`${API_BASE}/auth/service-principal`, {
      client_id: spClientId.value,
      client_secret: spClientSecret.value,
      tenant_id: spTenantId.value,
      scope: spScope.value
    })
    
    if (response.data.success) {
      successData.value = response.data
      activeTab.value = 'device' // Switch to device tab to show success
      deviceState.value = 'success'
      emit('success', response.data)
    } else {
      error.value = response.data.error || 'Authentication failed'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message || 'Authentication failed'
  } finally {
    loading.value = false
  }
}

// Cleanup on unmount
onUnmounted(() => {
  cancelPolling()
})

// Reset when modal closes
watch(() => props.isOpen, (newVal) => {
  if (!newVal) {
    cancelDeviceCode()
    resetState()
  }
})
</script>
