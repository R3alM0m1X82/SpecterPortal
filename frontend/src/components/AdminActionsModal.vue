<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/50" @click="close"></div>
    
    <!-- Modal -->
    <div :class="['relative w-full max-w-2xl mx-4 rounded-lg shadow-xl max-h-[90vh] flex flex-col', isDark ? 'bg-gray-800' : 'bg-white']">
      <!-- Header -->
      <div :class="['flex items-center justify-between p-4 border-b', isDark ? 'border-gray-700' : 'border-gray-200']">
        <h2 :class="['text-xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">
          ⚡ Admin Actions - {{ user?.displayName || user?.userPrincipalName }}
        </h2>
        <button @click="close" :class="['text-2xl leading-none', isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700']">
          ×
        </button>
      </div>
      
      <!-- ========== MULTI-TOKEN STATUS BANNER ========== -->
      <div v-if="showMultiTokenStatus" class="px-4 pt-4">
        <div :class="['p-3 rounded-lg text-sm flex items-center gap-2', isDark ? 'bg-green-900/40 text-green-300 border border-green-700' : 'bg-green-50 text-green-700 border border-green-200']">
          <span class="text-lg">✅</span>
          <div class="flex-1">
            <strong>Multi-Token Active:</strong> Original token for TAP/MFA, Azure PowerShell token for Password Reset.
          </div>
        </div>
      </div>
      
      <!-- ========== CAPABILITY BANNER ========== -->
      <div v-if="capabilityBanner" class="px-4 pt-4">
        <!-- No Admin Role -->
        <div v-if="capabilityBanner === 'no_role'" 
             :class="['p-3 rounded-lg text-sm flex items-center gap-2', isDark ? 'bg-red-900/40 text-red-300 border border-red-700' : 'bg-red-50 text-red-700 border border-red-200']">
          <span class="text-lg">❌</span>
          <span>No admin role detected. Cannot perform admin actions.</span>
        </div>
        
        <!-- AU-Scoped Role Warning -->
        <div v-else-if="capabilityBanner === 'au_scoped_warning'"
             :class="['p-3 rounded-lg text-sm flex items-center gap-2', isDark ? 'bg-blue-900/40 text-blue-300 border border-blue-700' : 'bg-blue-50 text-blue-700 border border-blue-200']">
          <span class="text-lg">ℹ️</span>
          <span>Admin role is AU-scoped. Actions may fail for users outside your Administrative Units.</span>
        </div>
        
        <!-- FOCI Auto-Exchange (Password Reset) -->
        <div v-else-if="capabilityBanner === 'foci_auto_exchange'"
             :class="['p-3 rounded-lg text-sm flex items-center gap-2', isDark ? 'bg-blue-900/40 text-blue-300 border border-blue-700' : 'bg-blue-50 text-blue-700 border border-blue-200']">
          <div class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          <span>Auto-acquiring Password Reset token via FOCI exchange...</span>
        </div>
        
        <!-- Device Code Required (TAP/MFA) -->
        <div v-else-if="capabilityBanner === 'device_code_required'"
             :class="['p-3 rounded-lg text-sm', isDark ? 'bg-yellow-900/40 text-yellow-300 border border-yellow-700' : 'bg-yellow-50 text-yellow-700 border border-yellow-200']">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="text-lg">⚠️</span>
              <span>Missing required scope for TAP/MFA. Device Code authentication required.</span>
            </div>
            <button 
              @click="startDeviceCodeFlow"
              :disabled="deviceCodeFlow.active"
              class="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
            >
              {{ deviceCodeFlow.active ? 'Authenticating...' : '🔐 Get Admin Token' }}
            </button>
          </div>
        </div>
        
        <!-- Scope Missing, FOCI Available (Legacy - for manual exchange) -->
        <div v-else-if="capabilityBanner === 'foci_available'"
             :class="['p-3 rounded-lg text-sm', isDark ? 'bg-yellow-900/40 text-yellow-300 border border-yellow-700' : 'bg-yellow-50 text-yellow-700 border border-yellow-200']">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="text-lg">⚠️</span>
              <span>Missing required scope. Token exchange available.</span>
            </div>
            <button 
              @click="performFociExchange"
              :disabled="fociLoading"
              class="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
            >
              {{ fociLoading ? 'Exchanging...' : '🔄 Get Admin Token' }}
            </button>
          </div>
        </div>
        
        <!-- Scope Missing, No FOCI -->
        <div v-else-if="capabilityBanner === 'no_scope_no_foci'"
             :class="['p-3 rounded-lg text-sm', isDark ? 'bg-yellow-900/40 text-yellow-300 border border-yellow-700' : 'bg-yellow-50 text-yellow-700 border border-yellow-200']">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="text-lg">⚠️</span>
              <span>Missing required scope. FOCI exchange not available.</span>
            </div>
            <button 
              @click="startDeviceCodeFlow"
              :disabled="deviceCodeFlow.active"
              class="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
            >
              {{ deviceCodeFlow.active ? 'Authenticating...' : '🔐 Start Device Code' }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- Device Code Flow UI -->
      <div v-if="deviceCodeFlow.active" class="px-4 pt-4">
        <div :class="['p-4 rounded-lg border', isDark ? 'bg-blue-900/20 border-blue-700' : 'bg-blue-50 border-blue-200']">
          <div class="flex items-center justify-between mb-3">
            <h3 :class="['font-semibold', isDark ? 'text-blue-300' : 'text-blue-700']">
              🔐 Device Code Authentication
            </h3>
            <button @click="cancelDeviceCodeFlow" :class="['text-sm', isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-800']">
              ✕ Cancel
            </button>
          </div>
          
          <div :class="['space-y-3 text-sm', isDark ? 'text-blue-200' : 'text-blue-800']">
            <p>1. Go to: <a :href="deviceCodeFlow.verificationUri" target="_blank" class="font-mono underline">{{ deviceCodeFlow.verificationUri }}</a></p>
            
            <div>
              <p class="mb-2">2. Enter code:</p>
              <div class="flex items-center gap-2">
                <span class="font-mono font-bold text-lg px-3 py-2 rounded flex-1 text-center" :class="isDark ? 'bg-blue-800' : 'bg-blue-100'">
                  {{ deviceCodeFlow.userCode }}
                </span>
                <button
                  @click="copyCode"
                  :class="[
                    'px-3 py-2 rounded font-medium transition-colors',
                    codeCopied 
                      ? (isDark ? 'bg-green-700 text-green-100' : 'bg-green-500 text-white')
                      : (isDark ? 'bg-blue-700 hover:bg-blue-600 text-blue-100' : 'bg-blue-500 hover:bg-blue-600 text-white')
                  ]"
                >
                  {{ codeCopied ? '✓ Copied' : '📋 Copy' }}
                </button>
              </div>
            </div>
            
            <div v-if="deviceCodeTimeRemaining > 0" class="flex items-center gap-2">
              <span>⏱️ Expires in: {{ formatTimeRemaining(deviceCodeTimeRemaining) }}</span>
            </div>
            
            <div v-if="deviceCodeFlow.polling" class="flex items-center gap-2 pt-2">
              <div class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              <span>Waiting for authentication...</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Capability Check Loading -->
      <div v-if="checkingCapabilities" class="px-4 pt-4">
        <div :class="['p-3 rounded-lg text-sm flex items-center gap-2', isDark ? 'bg-gray-700' : 'bg-gray-100']">
          <div class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          <span :class="isDark ? 'text-gray-300' : 'text-gray-600'">Checking capabilities...</span>
        </div>
      </div>
      
      <!-- Tab Navigation -->
      <div :class="['flex border-b', isDark ? 'border-gray-700' : 'border-gray-200']">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'flex-1 py-3 px-4 text-sm font-medium transition-colors',
            activeTab === tab.id
              ? `border-b-2 ${tab.borderColor} ${tab.textColor}`
              : isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>
      
      <!-- Content (scrollable) -->
      <div class="p-4 overflow-y-auto flex-1">
        
        <!-- ========== RESET PASSWORD TAB ========== -->
        <div v-if="activeTab === 'password'">
          <div :class="['p-3 rounded-lg mb-4 text-sm', isDark ? 'bg-orange-900/30 text-orange-300' : 'bg-orange-50 text-orange-700']">
            ⚠️ <strong>Warning:</strong> Cannot reset passwords for users with higher privilege roles.
          </div>
          
          <div class="space-y-4">
            <div>
              <label :class="['block text-sm font-medium mb-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                New Password
              </label>
              <div class="relative">
                <input
                  v-model="passwordForm.newPassword"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Enter new password"
                  :class="inputClass"
                />
                <button 
                  type="button"
                  @click="showPassword = !showPassword"
                  :class="['absolute right-3 top-1/2 -translate-y-1/2', isDark ? 'text-gray-400' : 'text-gray-500']"
                >
                  {{ showPassword ? '🙈' : '👁️' }}
                </button>
              </div>
            </div>
            
            <div>
              <button @click="generatePassword" :class="['text-sm', isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500']">
                🎲 Generate Strong Password
              </button>
            </div>
            
            <div class="flex items-center">
              <input 
                type="checkbox" 
                v-model="passwordForm.forceChange"
                id="forceChange"
                class="mr-2"
              />
              <label for="forceChange" :class="['text-sm', isDark ? 'text-gray-300' : 'text-gray-700']">
                Force password change at next sign-in
              </label>
            </div>
            
            <button
              @click="resetPassword"
              :disabled="loading || !passwordForm.newPassword"
              class="w-full py-3 px-4 bg-orange-600 text-white rounded-lg font-semibold hover:bg-orange-700 disabled:opacity-50"
            >
              {{ loading ? 'Resetting...' : '🔑 Reset Password' }}
            </button>
          </div>
        </div>
        
        <!-- ========== TAP TAB ========== -->
        <div v-if="activeTab === 'tap'">
          <div :class="['p-3 rounded-lg mb-4 text-sm', isDark ? 'bg-purple-900/30 text-purple-300' : 'bg-purple-50 text-purple-700']">
            💡 <strong>Temporary Access Pass (TAP)</strong> allows authentication without knowing the password. Useful for onboarding or account recovery.<br/>
            ⚠️ <strong>Note:</strong> TAP authentication method must be enabled for the user in Azure AD Authentication Methods policy.
          </div>
          
          <!-- Existing TAPs -->
          <div v-if="tapList.length > 0" class="mb-4">
            <h4 :class="['font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">Active TAPs</h4>
            <div class="space-y-2">
              <div 
                v-for="tap in tapList" 
                :key="tap.id"
                :class="['p-3 rounded-lg flex items-center justify-between', isDark ? 'bg-gray-700' : 'bg-gray-100']"
              >
                <div>
                  <span :class="['text-sm font-mono', isDark ? 'text-gray-300' : 'text-gray-700']">
                    ID: {{ tap.id.substring(0, 8) }}...
                  </span>
                  <span :class="['ml-2 text-xs', tap.isUsable ? 'text-green-500' : 'text-red-500']">
                    {{ tap.isUsable ? '✓ Usable' : '✗ Not Usable' }}
                  </span>
                  <span :class="['ml-2 text-xs', isDark ? 'text-gray-500' : 'text-gray-400']">
                    ({{ tap.lifetimeInMinutes }} min)
                  </span>
                </div>
                <button 
                  @click="deleteTap(tap.id)"
                  :class="['text-red-500 hover:text-red-400 text-sm']"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          </div>
          
          <!-- Create TAP Form -->
          <div class="space-y-4">
            <div>
              <label :class="['block text-sm font-medium mb-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                Lifetime (minutes)
              </label>
              <select v-model="tapForm.lifetime" :class="selectClass">
                <option :value="10">10 minutes</option>
                <option :value="30">30 minutes</option>
                <option :value="60">1 hour</option>
                <option :value="480">8 hours</option>
                <option :value="1440">24 hours</option>
                <option :value="10080">7 days</option>
              </select>
            </div>
            
            <div class="flex items-center">
              <input 
                type="checkbox" 
                v-model="tapForm.isUsableOnce"
                id="tapOnce"
                class="mr-2"
              />
              <label for="tapOnce" :class="['text-sm', isDark ? 'text-gray-300' : 'text-gray-700']">
                One-time use only
              </label>
            </div>
            
            <button
              @click="createTap"
              :disabled="loading"
              class="w-full py-3 px-4 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50"
            >
              {{ loading ? 'Creating...' : '🎫 Create TAP' }}
            </button>
          </div>
          
          <!-- Created TAP Display -->
          <div v-if="createdTap" :class="['mt-4 p-4 rounded-lg border-2 border-green-500', isDark ? 'bg-green-900/20' : 'bg-green-50']">
            <h4 class="font-bold text-green-500 mb-2">✅ TAP Created Successfully!</h4>
            <div :class="['text-2xl font-mono font-bold tracking-widest py-2 px-3 rounded text-center', isDark ? 'bg-gray-700 text-white' : 'bg-white text-gray-900']">
              {{ createdTap.temporaryAccessPass }}
            </div>
            <button
              @click="copyTap"
              :class="['mt-2 text-sm w-full text-center', tapCopied ? 'text-green-500' : isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500']"
            >
              {{ tapCopied ? '✓ Copied!' : '📋 Copy TAP' }}
            </button>
            <p :class="['mt-2 text-xs text-center', isDark ? 'text-red-400' : 'text-red-600']">
              ⚠️ Store this now - it cannot be retrieved later!
            </p>
          </div>
        </div>
        
        <!-- ========== MFA TAB ========== -->
        <div v-if="activeTab === 'mfa'">
          <div :class="['p-3 rounded-lg mb-4 text-sm', isDark ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-50 text-blue-700']">
            🔐 View and manage authentication methods. Removing MFA methods can weaken account security.
          </div>
          
          <!-- Loading -->
          <div v-if="loadingMfa" class="text-center py-8">
            <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
            <p class="mt-2 text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading auth methods...</p>
          </div>
          
          <!-- Auth Methods List -->
          <div v-else-if="authMethods" class="space-y-4">
            <!-- Summary -->
            <div :class="['p-3 rounded-lg', isDark ? 'bg-gray-700' : 'bg-gray-100']">
              <span :class="['font-medium', isDark ? 'text-gray-200' : 'text-gray-800']">
                {{ authMethods.hasMfa ? '🛡️ MFA Enabled' : '⚠️ No MFA Configured' }}
              </span>
              <span :class="['ml-2 text-sm', isDark ? 'text-gray-400' : 'text-gray-500']">
                ({{ authMethods.mfaMethodCount }} method{{ authMethods.mfaMethodCount !== 1 ? 's' : '' }})
              </span>
            </div>
            
            <!-- Phone Methods -->
            <div v-if="authMethods.methods.phone.length > 0">
              <h4 :class="['font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">📱 Phone Methods</h4>
              <div class="space-y-2">
                <div 
                  v-for="method in authMethods.methods.phone" 
                  :key="method.id"
                  :class="['p-3 rounded-lg flex items-center justify-between', isDark ? 'bg-gray-700' : 'bg-gray-100']"
                >
                  <div>
                    <span :class="['text-sm', isDark ? 'text-gray-300' : 'text-gray-700']">
                      {{ method.phoneNumber }}
                    </span>
                    <span :class="['ml-2 text-xs px-2 py-1 rounded', isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800']">
                      {{ method.phoneType }}
                    </span>
                  </div>
                  <button 
                    @click="deleteMethod('phone', method.id)"
                    :disabled="loading"
                    :class="['text-red-500 hover:text-red-400 text-sm disabled:opacity-50']"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Email Methods -->
            <div v-if="authMethods.methods.email.length > 0">
              <h4 :class="['font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">✉️ Email Methods</h4>
              <div class="space-y-2">
                <div 
                  v-for="method in authMethods.methods.email" 
                  :key="method.id"
                  :class="['p-3 rounded-lg flex items-center justify-between', isDark ? 'bg-gray-700' : 'bg-gray-100']"
                >
                  <span :class="['text-sm', isDark ? 'text-gray-300' : 'text-gray-700']">
                    {{ method.emailAddress }}
                  </span>
                  <button 
                    @click="deleteMethod('email', method.id)"
                    :disabled="loading"
                    :class="['text-red-500 hover:text-red-400 text-sm disabled:opacity-50']"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Authenticator App -->
            <div v-if="authMethods.methods.microsoftAuthenticator.length > 0">
              <h4 :class="['font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">📲 Microsoft Authenticator</h4>
              <div class="space-y-2">
                <div 
                  v-for="method in authMethods.methods.microsoftAuthenticator" 
                  :key="method.id"
                  :class="['p-3 rounded-lg flex items-center justify-between', isDark ? 'bg-gray-700' : 'bg-gray-100']"
                >
                  <div>
                    <span :class="['text-sm', isDark ? 'text-gray-300' : 'text-gray-700']">
                      {{ method.displayName || 'Authenticator App' }}
                    </span>
                    <span v-if="method.deviceTag" :class="['ml-2 text-xs', isDark ? 'text-gray-500' : 'text-gray-400']">
                      {{ method.deviceTag }}
                    </span>
                  </div>
                  <button 
                    @click="deleteMethod('microsoftAuthenticator', method.id)"
                    :disabled="loading"
                    :class="['text-red-500 hover:text-red-400 text-sm disabled:opacity-50']"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
            
            <!-- FIDO2 Keys -->
            <div v-if="authMethods.methods.fido2.length > 0">
              <h4 :class="['font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">🔑 FIDO2 Security Keys</h4>
              <div class="space-y-2">
                <div 
                  v-for="method in authMethods.methods.fido2" 
                  :key="method.id"
                  :class="['p-3 rounded-lg flex items-center justify-between', isDark ? 'bg-gray-700' : 'bg-gray-100']"
                >
                  <div>
                    <span :class="['text-sm', isDark ? 'text-gray-300' : 'text-gray-700']">
                      {{ method.displayName || method.model || 'Security Key' }}
                    </span>
                  </div>
                  <button 
                    @click="deleteMethod('fido2', method.id)"
                    :disabled="loading"
                    :class="['text-red-500 hover:text-red-400 text-sm disabled:opacity-50']"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Windows Hello -->
            <div v-if="authMethods.methods.windowsHello.length > 0">
              <h4 :class="['font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">🪟 Windows Hello</h4>
              <div class="space-y-2">
                <div 
                  v-for="method in authMethods.methods.windowsHello" 
                  :key="method.id"
                  :class="['p-3 rounded-lg flex items-center justify-between', isDark ? 'bg-gray-700' : 'bg-gray-100']"
                >
                  <span :class="['text-sm', isDark ? 'text-gray-300' : 'text-gray-700']">
                    {{ method.displayName || 'Windows Hello' }}
                  </span>
                  <button 
                    @click="deleteMethod('windowsHello', method.id)"
                    :disabled="loading"
                    :class="['text-red-500 hover:text-red-400 text-sm disabled:opacity-50']"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Add New Method -->
            <div :class="['mt-4 pt-4 border-t', isDark ? 'border-gray-700' : 'border-gray-200']">
              <h4 :class="['font-medium mb-3', isDark ? 'text-gray-300' : 'text-gray-700']">➕ Add Method</h4>
              
              <div class="grid grid-cols-2 gap-4 mb-4">
                <!-- Add Phone -->
                <div>
                  <input
                    v-model="mfaForm.phone"
                    type="text"
                    placeholder="+1 5551234567"
                    :class="inputClass"
                  />
                  <button
                    @click="addPhone"
                    :disabled="loading || !mfaForm.phone"
                    :class="['mt-2 w-full py-2 px-3 text-sm rounded-lg font-medium disabled:opacity-50', isDark ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300']"
                  >
                    📱 Add Phone
                  </button>
                </div>
                
                <!-- Add Email -->
                <div>
                  <input
                    v-model="mfaForm.email"
                    type="email"
                    placeholder="recovery@email.com"
                    :class="inputClass"
                  />
                  <button
                    @click="addEmail"
                    :disabled="loading || !mfaForm.email"
                    :class="['mt-2 w-full py-2 px-3 text-sm rounded-lg font-medium disabled:opacity-50', isDark ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300']"
                  >
                    ✉️ Add Email
                  </button>
                </div>
              </div>
              
              <!-- Microsoft Authenticator Info -->
              <div :class="['p-3 rounded-lg border', isDark ? 'bg-blue-900/20 border-blue-700 text-blue-300' : 'bg-blue-50 border-blue-200 text-blue-700']">
                <div class="flex items-start gap-2">
                  <span class="text-lg">📲</span>
                  <div class="flex-1 text-sm">
                    <strong>Microsoft Authenticator:</strong> User must enable it from their account.
                    <a 
                      href="https://mysignins.microsoft.com/security-info" 
                      target="_blank" 
                      class="underline hover:no-underline ml-1"
                    >
                      Open Security Info →
                    </a>
                  </div>
                </div>
              </div>
            </div>
            
            <button
              @click="loadAuthMethods"
              :class="['mt-4 w-full py-2 px-4 rounded-lg font-medium', isDark ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300']"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
        
        <!-- Error Display -->
        <div v-if="error" :class="['mt-4 p-3 rounded-lg text-sm', isDark ? 'bg-red-900/30 text-red-300' : 'bg-red-50 text-red-700']">
          ❌ {{ error }}
        </div>
        
        <!-- Success Display -->
        <div v-if="success" :class="['mt-4 p-3 rounded-lg text-sm', isDark ? 'bg-green-900/30 text-green-300' : 'bg-green-50 text-green-700']">
          ✅ {{ success }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { adminAPI } from '../services/api'

const props = defineProps({
  isOpen: Boolean,
  isDark: Boolean,
  user: Object,
  accessToken: String
})

const emit = defineEmits(['close', 'action-completed', 'token-exchanged'])

// Tab configuration
const tabs = [
  { id: 'password', label: 'Reset Password', icon: '🔑', borderColor: 'border-orange-500', textColor: 'text-orange-500' },
  { id: 'tap', label: 'TAP', icon: '🎫', borderColor: 'border-purple-500', textColor: 'text-purple-500' },
  { id: 'mfa', label: 'MFA Methods', icon: '🔐', borderColor: 'border-blue-500', textColor: 'text-blue-500' }
]

// State
const activeTab = ref('password')
const loading = ref(false)
const loadingMfa = ref(false)
const error = ref('')
const success = ref('')
const showPassword = ref(false)

// ========== MULTI-TOKEN STATE ==========
const originalToken = ref(null)           // Token originale (MFA scopes)
const passwordResetToken = ref(null)      // Token Azure PowerShell (FOCI)
const originalTokenCapabilities = ref(null)
const passwordTokenCapabilities = ref(null)

// Capability Check State
const capabilities = ref(null)
const checkingCapabilities = ref(false)
const fociLoading = ref(false)

// Device Code Flow State
const deviceCodeFlow = ref({
  active: false,
  userCode: null,
  verificationUri: null,
  deviceCode: null,
  expiresIn: null,
  interval: 5,
  polling: false,
  clientId: '0c1307d4-29d6-4389-a11c-5cbe7f65d7fa'  // Azure Mobile App
})
const deviceCodeExpiresAt = ref(null)
const deviceCodeTimeRemaining = ref(0)
const codeCopied = ref(false)

// Password form
const passwordForm = ref({
  newPassword: '',
  forceChange: true
})

// TAP form & data
const tapForm = ref({
  lifetime: 60,
  isUsableOnce: false
})
const tapList = ref([])
const createdTap = ref(null)
const tapCopied = ref(false)

// MFA data
const authMethods = ref(null)
const mfaForm = ref({
  phone: '',
  email: ''
})

// Computed
const inputClass = computed(() => [
  'w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500',
  props.isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900'
])

const selectClass = computed(() => [
  'w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500',
  props.isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300 text-gray-900'
])

// Show multi-token status banner when both tokens are active
const showMultiTokenStatus = computed(() => {
  return originalToken.value && passwordResetToken.value
})

// Compute which banner to show
const capabilityBanner = computed(() => {
  if (checkingCapabilities.value || !capabilities.value) return null
  return capabilities.value.recommendation
})

// Get token for Password Reset (prefer FOCI, fallback to original)
const passwordToken = computed(() => {
  return passwordResetToken.value || originalToken.value
})

// Get token for TAP/MFA (ALWAYS original)
const tapMfaToken = computed(() => {
  return originalToken.value
})

// Compute action_type based on activeTab
const currentActionType = computed(() => {
  if (activeTab.value === 'password') return 'password_reset'
  if (activeTab.value === 'tap' || activeTab.value === 'mfa') return 'tap_mfa'
  return null
})

// Methods
const close = () => {
  resetState()
  emit('close')
}

const resetState = () => {
  error.value = ''
  success.value = ''
  passwordForm.value = { newPassword: '', forceChange: true }
  createdTap.value = null
  tapCopied.value = false
  mfaForm.value = { phone: '', email: '' }
  deviceCodeFlow.value.active = false
  deviceCodeFlow.value.polling = false
}

const generatePassword = () => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#$%^&*'
  let password = ''
  for (let i = 0; i < 16; i++) {
    password += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  passwordForm.value.newPassword = password
  showPassword.value = true
}

// ===== CAPABILITY CHECK WITH ACTION TYPE =====
const checkCapabilities = async (actionType = null) => {
  if (!originalToken.value) return
  
  checkingCapabilities.value = true
  error.value = ''
  
  try {
    // Check with appropriate token based on action type
    const tokenToCheck = actionType === 'password_reset' ? passwordToken.value : tapMfaToken.value
    
    const response = await adminAPI.checkCapabilities(tokenToCheck, actionType)
    if (response.data.success) {
      capabilities.value = response.data
      
      // CRITICAL: Check if backend auto-acquired token via FOCI
      if (response.data.auto_foci_success && response.data.auto_acquired_token) {
        console.log('[CapCheck] ✅ Backend auto-acquired token via FOCI!')
        
        // Save the auto-acquired token
        if (actionType === 'password_reset') {
          passwordResetToken.value = response.data.auto_acquired_token
          passwordTokenCapabilities.value = response.data
          console.log('[CapCheck] Saved auto-acquired token to passwordResetToken')
        }
        
        // Emit event so parent can update if needed (but only for MFA scopes, not password reset)
        const hasMfaScopes = response.data.scopes?.includes('UserAuthenticationMethod.ReadWrite.All')
        if (hasMfaScopes) {
          emit('token-exchanged', {
            access_token: response.data.auto_acquired_token,
            capabilities: response.data,
            token_id: response.data.token_id
          })
        }
      }
      
      // Store capabilities per token type
      if (actionType === 'password_reset') {
        passwordTokenCapabilities.value = response.data
      } else if (actionType === 'tap_mfa') {
        originalTokenCapabilities.value = response.data
      }
      
      console.log('[CapCheck] Result:', capabilities.value)
      console.log('[CapCheck] can_perform_actions:', response.data.can_perform_actions, 
                  'recommendation:', response.data.recommendation,
                  'auto_foci_success:', response.data.auto_foci_success)
      
      // AUTO-ACQUIRE TOKEN MANUALLY (frontend-triggered)
      // This runs ONLY if backend didn't already auto-acquire
      if (!response.data.auto_foci_success &&
          !response.data.can_perform_actions && 
          actionType === 'password_reset' && 
          response.data.recommendation === 'foci_auto_exchange' &&
          !passwordResetToken.value) {
        console.log('[CapCheck] Triggering frontend auto-acquire for password reset')
        await autoAcquirePasswordResetToken()
      } else {
        console.log('[CapCheck] Skipping frontend auto-acquire: auto_foci_success=' + response.data.auto_foci_success + 
                    ', can_perform=' + response.data.can_perform_actions + 
                    ', action=' + actionType + ', recommendation=' + response.data.recommendation)
      }
    } else {
      console.warn('[CapCheck] Failed:', response.data.error)
    }
  } catch (err) {
    console.error('[CapCheck] Error:', err)
  } finally {
    checkingCapabilities.value = false
  }
}

const performFociExchange = async () => {
  fociLoading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const response = await adminAPI.fociExchange(originalToken.value)
    
    if (response.data.success) {
      // Store as password reset token (DON'T overwrite original!)
      passwordResetToken.value = response.data.access_token
      passwordTokenCapabilities.value = response.data.capabilities
      success.value = '✅ Password Reset token activated via FOCI exchange!'
      
      // Emit event so parent can update if needed
      emit('token-exchanged', {
        access_token: response.data.access_token,
        capabilities: response.data.capabilities,
        token_id: response.data.token_id
      })
      
      console.log('[FOCI] Exchange successful, stored as passwordResetToken')
      
      // Re-check capabilities with new token
      await checkCapabilities('password_reset')
    } else {
      error.value = response.data.error || 'FOCI exchange failed'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message || 'FOCI exchange failed'
  } finally {
    fociLoading.value = false
  }
}

// ===== AUTO-ACQUIRE TOKEN (PASSWORD RESET) =====
const autoAcquirePasswordResetToken = async () => {
  console.log('[Auto-Acquire] Starting FOCI exchange for password reset...')
  fociLoading.value = true
  
  try {
    const response = await adminAPI.autoAcquireToken(originalToken.value, 'password_reset')
    
    if (response.data.success) {
      // Store as password reset token (DON'T overwrite original!)
      passwordResetToken.value = response.data.access_token
      passwordTokenCapabilities.value = response.data.capabilities
      success.value = '✅ Auto-acquired Password Reset token via FOCI exchange.'
      
      emit('token-exchanged', {
        access_token: response.data.access_token,
        capabilities: response.data.capabilities,
        token_id: response.data.token_id
      })
      
      console.log('[Auto-Acquire] Success, stored as passwordResetToken')
      
      // Re-check capabilities
      await checkCapabilities('password_reset')
    } else {
      console.warn('[Auto-Acquire] Failed:', response.data.error)
    }
  } catch (err) {
    console.error('[Auto-Acquire] Error:', err)
  } finally {
    fociLoading.value = false
  }
}

// ===== DEVICE CODE FLOW (TAP/MFA) =====
const startDeviceCodeFlow = async () => {
  error.value = ''
  success.value = ''
  deviceCodeFlow.value.active = true
  deviceCodeFlow.value.polling = false
  
  try {
    const response = await adminAPI.startDeviceCode(
      deviceCodeFlow.value.clientId,
      'https://graph.microsoft.com/.default offline_access'
    )
    
    if (response.data.success) {
      deviceCodeFlow.value.userCode = response.data.user_code
      deviceCodeFlow.value.verificationUri = response.data.verification_uri
      deviceCodeFlow.value.deviceCode = response.data.device_code
      deviceCodeFlow.value.expiresIn = response.data.expires_in
      deviceCodeFlow.value.interval = response.data.interval || 5
      
      // Set expiration timestamp and start countdown
      deviceCodeExpiresAt.value = Date.now() + (response.data.expires_in * 1000)
      deviceCodeTimeRemaining.value = response.data.expires_in
      
      // Start countdown interval
      const countdownInterval = setInterval(() => {
        const remaining = Math.floor((deviceCodeExpiresAt.value - Date.now()) / 1000)
        deviceCodeTimeRemaining.value = Math.max(0, remaining)
        
        // Stop countdown when expired or flow cancelled
        if (remaining <= 0 || !deviceCodeFlow.value.active) {
          clearInterval(countdownInterval)
        }
      }, 1000)
      
      console.log('[DeviceCode] Flow started, user code:', response.data.user_code)
      
      // Auto-start polling
      setTimeout(() => pollDeviceCode(), 3000)
    } else {
      error.value = response.data.error || 'Failed to start device code flow'
      deviceCodeFlow.value.active = false
      deviceCodeExpiresAt.value = null
      deviceCodeTimeRemaining.value = 0
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message || 'Failed to start device code flow'
    deviceCodeFlow.value.active = false
    deviceCodeExpiresAt.value = null
    deviceCodeTimeRemaining.value = 0
  }
}

const pollDeviceCode = async () => {
  if (!deviceCodeFlow.value.deviceCode) return
  
  if (deviceCodeFlow.value.polling) {
    console.log('[DeviceCode] Already polling, skipping...')
    return
  }
  
  deviceCodeFlow.value.polling = true
  console.log('[DeviceCode] Starting poll...')
  
  try {
    const response = await adminAPI.pollDeviceCode(
      deviceCodeFlow.value.clientId,
      deviceCodeFlow.value.deviceCode
    )
    
    if (response.data.success) {
      console.log('[DeviceCode] Authentication successful!')
      
      // Save token - this will update originalToken
      const saveResponse = await adminAPI.autoAcquireToken(
        originalToken.value,
        'tap_mfa',
        {
          access_token: response.data.access_token,
          refresh_token: response.data.refresh_token,
          client_id: deviceCodeFlow.value.clientId
        }
      )
      
      if (saveResponse.data.success) {
        // Update original token with new TAP/MFA capable token
        originalToken.value = saveResponse.data.access_token
        originalTokenCapabilities.value = saveResponse.data.capabilities
        success.value = '✅ TAP/MFA token activated! You can now manage authentication methods.'
        deviceCodeFlow.value.active = false
        deviceCodeFlow.value.polling = false
        deviceCodeExpiresAt.value = null
        deviceCodeTimeRemaining.value = 0
        
        emit('token-exchanged', {
          access_token: saveResponse.data.access_token,
          capabilities: saveResponse.data.capabilities,
          token_id: saveResponse.data.token_id
        })
        
        await checkCapabilities('tap_mfa')
      } else {
        error.value = 'Token acquired but failed to save: ' + saveResponse.data.error
        deviceCodeFlow.value.active = false
        deviceCodeFlow.value.polling = false
      }
    } else {
      if (response.data.status === 'pending') {
        console.log('[DeviceCode] Still pending, will poll again in ' + deviceCodeFlow.value.interval + 's')
        deviceCodeFlow.value.polling = false
        setTimeout(() => pollDeviceCode(), deviceCodeFlow.value.interval * 1000)
      } else if (response.data.status === 'slow_down') {
        deviceCodeFlow.value.interval += 2
        console.log('[DeviceCode] Slowing down, will poll again in ' + deviceCodeFlow.value.interval + 's')
        deviceCodeFlow.value.polling = false
        setTimeout(() => pollDeviceCode(), deviceCodeFlow.value.interval * 1000)
      } else {
        error.value = response.data.error || 'Device code flow failed'
        deviceCodeFlow.value.active = false
        deviceCodeFlow.value.polling = false
        deviceCodeExpiresAt.value = null
        deviceCodeTimeRemaining.value = 0
      }
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message || 'Device code polling failed'
    deviceCodeFlow.value.active = false
    deviceCodeFlow.value.polling = false
    deviceCodeExpiresAt.value = null
    deviceCodeTimeRemaining.value = 0
  }
}

const cancelDeviceCodeFlow = () => {
  deviceCodeFlow.value.active = false
  deviceCodeFlow.value.polling = false
  deviceCodeFlow.value.userCode = null
  deviceCodeFlow.value.deviceCode = null
  deviceCodeExpiresAt.value = null
  deviceCodeTimeRemaining.value = 0
  codeCopied.value = false
}

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(deviceCodeFlow.value.userCode)
    codeCopied.value = true
    setTimeout(() => {
      codeCopied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy code:', err)
  }
}

const formatTimeRemaining = (seconds) => {
  if (seconds <= 0) return '0s'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
}

// ===== PASSWORD RESET =====
const resetPassword = async () => {
  if (!passwordForm.value.newPassword) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  // LAZY CHECK: Check capabilities before attempting action
  await checkCapabilities('password_reset')
  
  // If no admin capabilities, stop here (banner will show options)
  if (passwordTokenCapabilities.value && !passwordTokenCapabilities.value.can_perform_actions) {
    loading.value = false
    error.value = 'Missing required permissions. Please acquire admin token first.'
    return
  }
  
  // Use password reset token (FOCI or original)
  const token = passwordToken.value
  console.log('[ResetPassword] Using token length:', token ? token.length : 0)
  
  try {
    const response = await adminAPI.resetPassword(
      token,
      props.user.id,
      passwordForm.value.newPassword,
      passwordForm.value.forceChange
    )
    
    if (response.data.success) {
      success.value = 'Password reset successfully!'
      emit('action-completed', { action: 'password_reset', user: props.user })
    } else {
      error.value = response.data.error || 'Failed to reset password'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message || 'Failed to reset password'
  } finally {
    loading.value = false
  }
}

// ===== TAP MANAGEMENT =====
const loadTapList = async () => {
  await checkCapabilities('tap_mfa')
  
  if (originalTokenCapabilities.value && !originalTokenCapabilities.value.can_perform_actions) {
    return
  }
  
  const token = tapMfaToken.value
  if (!token) return
  
  try {
    const response = await adminAPI.listTap(token, props.user.id)
    if (response.data.success) {
      tapList.value = response.data.taps || []
    }
  } catch (err) {
    console.warn('Could not load TAP list:', err.message)
  }
}

const createTap = async () => {
  loading.value = true
  error.value = ''
  success.value = ''
  createdTap.value = null
  
  await checkCapabilities('tap_mfa')
  
  if (originalTokenCapabilities.value && !originalTokenCapabilities.value.can_perform_actions) {
    loading.value = false
    error.value = 'Missing required permissions. Please acquire admin token first.'
    return
  }
  
  const token = tapMfaToken.value
  
  try {
    const response = await adminAPI.createTap(token, props.user.id, {
      lifetimeInMinutes: tapForm.value.lifetime,
      isUsableOnce: tapForm.value.isUsableOnce
    })
    
    if (response.data.success) {
      createdTap.value = response.data.tap
      success.value = 'TAP created successfully!'
      await loadTapList()
      emit('action-completed', { action: 'tap_created', user: props.user })
    } else {
      if (capabilities.value?.recommendation === 'au_scoped_warning' && 
          (response.data.error?.includes('Authorization failed') || response.data.error?.includes('accessDenied'))) {
        error.value = '⚠️ AU-scoped Role Limitation: Administrative Unit-scoped administrators cannot manage TAP.'
      } else {
        error.value = response.data.error || 'Failed to create TAP'
      }
    }
  } catch (err) {
    if (capabilities.value?.recommendation === 'au_scoped_warning' && 
        (err.response?.data?.error?.includes('Authorization failed') || err.response?.data?.error?.includes('accessDenied'))) {
      error.value = '⚠️ AU-scoped Role Limitation: Administrative Unit-scoped administrators cannot manage TAP.'
    } else {
      error.value = err.response?.data?.error || err.message || 'Failed to create TAP'
    }
  } finally {
    loading.value = false
  }
}

const deleteTap = async (tapId) => {
  if (!confirm('Delete this TAP?')) return
  
  loading.value = true
  error.value = ''
  
  await checkCapabilities('tap_mfa')
  
  if (originalTokenCapabilities.value && !originalTokenCapabilities.value.can_perform_actions) {
    loading.value = false
    error.value = 'Missing required permissions. Please acquire admin token first.'
    return
  }
  
  const token = tapMfaToken.value
  
  try {
    const response = await adminAPI.deleteTap(token, props.user.id, tapId)
    if (response.data.success) {
      success.value = 'TAP deleted'
      await loadTapList()
    } else {
      if (capabilities.value?.recommendation === 'au_scoped_warning' && 
          (response.data.error?.includes('Authorization failed') || response.data.error?.includes('accessDenied'))) {
        error.value = '⚠️ AU-scoped Role Limitation: Administrative Unit-scoped administrators cannot delete TAP.'
      } else {
        error.value = response.data.error || 'Failed to delete TAP'
      }
    }
  } catch (err) {
    if (capabilities.value?.recommendation === 'au_scoped_warning' && 
        (err.response?.data?.error?.includes('Authorization failed') || err.response?.data?.error?.includes('accessDenied'))) {
      error.value = '⚠️ AU-scoped Role Limitation: Administrative Unit-scoped administrators cannot delete TAP.'
    } else {
      error.value = err.response?.data?.error || err.message || 'Failed to delete TAP'
    }
  } finally {
    loading.value = false
  }
}

const copyTap = async () => {
  if (createdTap.value?.temporaryAccessPass) {
    try {
      await navigator.clipboard.writeText(createdTap.value.temporaryAccessPass)
      tapCopied.value = true
      setTimeout(() => { tapCopied.value = false }, 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }
}

// ===== MFA MANAGEMENT =====
const loadAuthMethods = async () => {
  loadingMfa.value = true
  error.value = ''
  
  await checkCapabilities('tap_mfa')
  
  if (originalTokenCapabilities.value && !originalTokenCapabilities.value.can_perform_actions) {
    loadingMfa.value = false
    return
  }
  
  const token = tapMfaToken.value
  if (!token) return
  
  try {
    const response = await adminAPI.listAuthMethods(token, props.user.id)
    if (response.data.success) {
      authMethods.value = response.data
    } else {
      if (capabilities.value?.recommendation === 'au_scoped_warning' && 
          (response.data.error?.includes('Authorization failed') || response.data.error?.includes('accessDenied'))) {
        error.value = '⚠️ AU-scoped Role Limitation: Cannot view authentication methods.'
      } else {
        error.value = response.data.error || 'Failed to load auth methods'
      }
    }
  } catch (err) {
    if (capabilities.value?.recommendation === 'au_scoped_warning' && 
        (err.response?.data?.error?.includes('Authorization failed') || err.response?.data?.error?.includes('accessDenied'))) {
      error.value = '⚠️ AU-scoped Role Limitation: Cannot view authentication methods.'
    } else {
      error.value = err.response?.data?.error || err.message || 'Failed to load auth methods'
    }
  } finally {
    loadingMfa.value = false
  }
}

const deleteMethod = async (methodType, methodId) => {
  if (!confirm(`Delete this ${methodType} authentication method?`)) return
  
  loading.value = true
  error.value = ''
  
  await checkCapabilities('tap_mfa')
  
  if (originalTokenCapabilities.value && !originalTokenCapabilities.value.can_perform_actions) {
    loading.value = false
    error.value = 'Missing required permissions. Please acquire admin token first.'
    return
  }
  
  const token = tapMfaToken.value
  
  try {
    const response = await adminAPI.deleteAuthMethod(token, props.user.id, methodType, methodId)
    if (response.data.success) {
      success.value = `${methodType} method deleted`
      await loadAuthMethods()
      emit('action-completed', { action: 'mfa_deleted', user: props.user, methodType })
    } else {
      if (capabilities.value?.recommendation === 'au_scoped_warning' && 
          (response.data.error?.includes('Authorization failed') || response.data.error?.includes('accessDenied'))) {
        error.value = '⚠️ AU-scoped Role Limitation: Cannot delete authentication methods.'
      } else {
        error.value = response.data.error || 'Failed to delete method'
      }
    }
  } catch (err) {
    if (capabilities.value?.recommendation === 'au_scoped_warning' && 
        (err.response?.data?.error?.includes('Authorization failed') || err.response?.data?.error?.includes('accessDenied'))) {
      error.value = '⚠️ AU-scoped Role Limitation: Cannot delete authentication methods.'
    } else {
      error.value = err.response?.data?.error || err.message || 'Failed to delete method'
    }
  } finally {
    loading.value = false
  }
}

const addPhone = async () => {
  if (!mfaForm.value.phone) return
  
  loading.value = true
  error.value = ''
  
  await checkCapabilities('tap_mfa')
  
  if (originalTokenCapabilities.value && !originalTokenCapabilities.value.can_perform_actions) {
    loading.value = false
    error.value = 'Missing required permissions. Please acquire admin token first.'
    return
  }
  
  const token = tapMfaToken.value
  
  try {
    const response = await adminAPI.addPhoneMethod(token, props.user.id, mfaForm.value.phone)
    if (response.data.success) {
      success.value = 'Phone method added!'
      mfaForm.value.phone = ''
      await loadAuthMethods()
      emit('action-completed', { action: 'mfa_added', user: props.user, methodType: 'phone' })
    } else {
      if (capabilities.value?.recommendation === 'au_scoped_warning' && 
          (response.data.error?.includes('Authorization failed') || response.data.error?.includes('accessDenied'))) {
        error.value = '⚠️ AU-scoped Role Limitation: Cannot add authentication methods.'
      } else {
        error.value = response.data.error || 'Failed to add phone'
      }
    }
  } catch (err) {
    if (capabilities.value?.recommendation === 'au_scoped_warning' && 
        (err.response?.data?.error?.includes('Authorization failed') || err.response?.data?.error?.includes('accessDenied'))) {
      error.value = '⚠️ AU-scoped Role Limitation: Cannot add authentication methods.'
    } else {
      error.value = err.response?.data?.error || err.message || 'Failed to add phone'
    }
  } finally {
    loading.value = false
  }
}

const addEmail = async () => {
  if (!mfaForm.value.email) return
  
  loading.value = true
  error.value = ''
  
  await checkCapabilities('tap_mfa')
  
  if (originalTokenCapabilities.value && !originalTokenCapabilities.value.can_perform_actions) {
    loading.value = false
    error.value = 'Missing required permissions. Please acquire admin token first.'
    return
  }
  
  const token = tapMfaToken.value
  
  try {
    const response = await adminAPI.addEmailMethod(token, props.user.id, mfaForm.value.email)
    if (response.data.success) {
      success.value = 'Email method added!'
      mfaForm.value.email = ''
      await loadAuthMethods()
      emit('action-completed', { action: 'mfa_added', user: props.user, methodType: 'email' })
    } else {
      if (capabilities.value?.recommendation === 'au_scoped_warning' && 
          (response.data.error?.includes('Authorization failed') || response.data.error?.includes('accessDenied'))) {
        error.value = '⚠️ AU-scoped Role Limitation: Cannot add authentication methods.'
      } else {
        error.value = response.data.error || 'Failed to add email'
      }
    }
  } catch (err) {
    if (capabilities.value?.recommendation === 'au_scoped_warning' && 
        (err.response?.data?.error?.includes('Authorization failed') || err.response?.data?.error?.includes('accessDenied'))) {
      error.value = '⚠️ AU-scoped Role Limitation: Cannot add authentication methods.'
    } else {
      error.value = err.response?.data?.error || err.message || 'Failed to add email'
    }
  } finally {
    loading.value = false
  }
}

// Load data when tab changes
watch(activeTab, async (newTab) => {
  error.value = ''
  success.value = ''
  
  if (newTab === 'tap') {
    await loadTapList()
  } else if (newTab === 'mfa') {
    await loadAuthMethods()
  } else if (newTab === 'password') {
    await checkCapabilities('password_reset')
  }
})

// Load initial data when modal opens
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen && props.user && props.accessToken) {
    resetState()
    
    // Initialize original token (NEVER overwrite this!)
    originalToken.value = props.accessToken
    passwordResetToken.value = null  // Reset password token
    capabilities.value = null
    originalTokenCapabilities.value = null
    passwordTokenCapabilities.value = null
    
    // Check capabilities for the initial tab (password)
    await checkCapabilities('password_reset')
    
    // Load tab-specific data
    if (activeTab.value === 'tap') {
      await loadTapList()
    } else if (activeTab.value === 'mfa') {
      await loadAuthMethods()
    }
  }
})
</script>
