<template>
  <div :class="['p-8 min-h-screen', bgContainer]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 :class="['text-3xl font-bold', textPrimary]">Automation Accounts</h1>
        <p :class="['text-sm mt-1', textSecondary]">Azure Automation enumeration and exploitation</p>
      </div>
      <div class="flex items-center space-x-3">
        <!-- Subscription Selector -->
        <select 
          v-model="selectedSubscription" 
          @change="loadAutomationAccounts"
          :class="[
            'px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:outline-none',
            isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'
          ]"
        >
          <option value="">Select Subscription</option>
          <option v-for="sub in subscriptions" :key="sub.id" :value="sub.id">
            {{ sub.displayName }}
          </option>
        </select>
        <!-- Refresh Button -->
        <button 
          @click="forceRefresh" 
          :disabled="loading || !selectedSubscription"
          class="refresh-btn"
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
    <div v-if="!selectedSubscription" class="text-center py-12">
      <svg :class="['w-16 h-16 mx-auto mb-4', textIcon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 :class="['text-lg font-semibold mb-2', textTertiary]">Select a Subscription</h3>
      <p :class="[textPlaceholder]">Choose a subscription from the dropdown to view Automation Accounts</p>
    </div>

    <!-- Content with Tabs -->
    <div v-else-if="!loading">
      <!-- Tabs Navigation -->
      <div :class="[bgPrimary, borderPrimary, 'rounded-t-lg border-t border-l border-r']">
        <div class="flex border-b" :class="[isDark ? 'border-gray-700' : 'border-gray-300']">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="currentTab = tab.id"
            :class="[
              'px-6 py-3 font-medium transition-colors relative',
              currentTab === tab.id
                ? (isDark ? 'text-blue-400 bg-gray-750' : 'text-blue-600 bg-gray-50')
                : (isDark ? 'text-gray-400 hover:text-gray-300 hover:bg-gray-750' : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50')
            ]"
          >
            {{ tab.name }}
            <div 
              v-if="currentTab === tab.id" 
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500"
            ></div>
          </button>
        </div>
      </div>

      <!-- Tab Content -->
      <div :class="[bgPrimary, borderPrimary, 'rounded-b-lg border-b border-l border-r p-6']">
        <!-- Overview Tab -->
        <div v-if="currentTab === 'overview'">
          <div v-if="automationAccounts.length === 0" class="text-center py-12">
            <svg :class="['w-16 h-16 mx-auto mb-4', textIcon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 :class="['text-lg font-semibold mb-2', textTertiary]">No Automation Accounts</h3>
            <p :class="[textPlaceholder]">No automation accounts found in this subscription</p>
          </div>
          
          <div v-else class="space-y-4">
            <div 
              v-for="account in automationAccounts" 
              :key="account.id"
              @click="selectAutomationAccount(account)"
              :class="[
                bgSecondary,
                borderSecondary,
                selectedAccount?.id === account.id ? 'ring-2 ring-blue-500' : '',
                'p-4 rounded-lg border cursor-pointer hover:border-blue-500 transition-all'
              ]"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                  <!-- Azure Automation Icon -->
                  <svg class="h-12 w-12" viewBox="0 0 18 18">
                    <defs>
                      <linearGradient id="autoGradient" x1="9" y1="0" x2="9" y2="18" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#68217A"/>
                        <stop offset="1" stop-color="#481A5C"/>
                      </linearGradient>
                    </defs>
                    <path d="M0 3.5C0 1.567 1.567 0 3.5 0h11C16.433 0 18 1.567 18 3.5v11c0 1.933-1.567 3.5-3.5 3.5h-11C1.567 18 0 16.433 0 14.5v-11z" fill="url(#autoGradient)"/>
                    <path d="M6 5l3 3-3 3m3 0h3" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <div>
                    <h3 :class="['text-lg font-semibold', textPrimary]">{{ account.name }}</h3>
                    <p :class="['text-sm', textSecondary]">{{ account.location }} • {{ account.resourceGroup }}</p>
                    <p v-if="account.creationTime" :class="['text-xs mt-1', textSecondary]">
                      Created: {{ new Date(account.creationTime).toLocaleDateString() }}
                    </p>
                  </div>
                </div>
                
                <span 
                  :class="[
                    isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800',
                    'px-3 py-1 text-xs font-semibold rounded-full'
                  ]"
                >
                  {{ account.state || 'Active' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Runbooks Tab -->
        <div v-if="currentTab === 'runbooks'">
          <div v-if="!selectedAccount" :class="['text-center py-12', textSecondary]">
            <p>Please select an Automation Account from the Overview tab</p>
          </div>
          
          <div v-else>
            <div class="flex items-center justify-between mb-4">
              <h3 :class="['text-lg font-semibold', textPrimary]">Runbooks in {{ selectedAccount.name }}</h3>
              <button 
                @click="showCreateRunbookModal = true"
                class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <span>Create Runbook</span>
              </button>
            </div>

            <div v-if="loadingRunbooks" class="text-center py-12">
              <svg class="animate-spin h-8 w-8 mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>

            <div v-else-if="runbooks.length === 0" class="text-center py-12">
              <p :class="[textSecondary]">No runbooks found in this automation account</p>
            </div>

            <div v-else class="space-y-3">
              <div 
                v-for="runbook in runbooks" 
                :key="runbook.id"
                :class="[bgSecondary, borderSecondary, 'p-4 rounded-lg border']"
              >
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <h4 :class="['font-semibold', textPrimary]">{{ runbook.name }}</h4>
                    <div class="flex items-center space-x-4 mt-1">
                      <span :class="['text-xs', textSecondary]">Type: {{ runbook.runbookType }}</span>
                      <span 
                        :class="[
                          'text-xs px-2 py-0.5 rounded-full',
                          runbook.state === 'Published' 
                            ? 'bg-green-900 text-green-300' 
                            : 'bg-yellow-900 text-yellow-300'
                        ]"
                      >
                        {{ runbook.state }}
                      </span>
                      <span v-if="runbook.lastModifiedTime" :class="['text-xs', textSecondary]">
                        Modified: {{ new Date(runbook.lastModifiedTime).toLocaleString() }}
                      </span>
                    </div>
                    <p v-if="runbook.description" :class="['text-sm mt-2', textSecondary]">
                      {{ runbook.description }}
                    </p>
                  </div>
                  
                  <div class="flex items-center space-x-2 ml-4">
                    <button
                      @click="viewRunbookContent(runbook)"
                      class="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                    >
                      View Code
                    </button>
                    <button
                      @click="startRunbookExecution(runbook)"
                      :disabled="runbook.state !== 'Published'"
                      :class="[
                        'px-3 py-1 text-sm rounded transition-colors',
                        runbook.state === 'Published'
                          ? 'bg-green-600 hover:bg-green-700 text-white'
                          : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      ]"
                    >
                      Start
                    </button>
                    <button
                      @click="confirmDeleteRunbook(runbook)"
                      class="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Hybrid Workers Tab -->
        <div v-if="currentTab === 'hybrid-workers'">
          <div v-if="!selectedAccount" :class="['text-center py-12', textSecondary]">
            <p>Please select an Automation Account from the Overview tab</p>
          </div>
          
          <div v-else>
            <h3 :class="['text-lg font-semibold mb-4', textPrimary]">
              Hybrid Worker Groups in {{ selectedAccount.name }}
            </h3>

            <div v-if="loadingHybridWorkers" class="text-center py-12">
              <svg class="animate-spin h-8 w-8 mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>

            <div v-else-if="hybridWorkerGroups.length === 0" class="text-center py-12">
              <p :class="[textSecondary]">No Hybrid Worker Groups found in this automation account</p>
            </div>

            <div v-else class="space-y-6">
              <!-- Hybrid Worker Group Card -->
              <div 
                v-for="group in hybridWorkerGroups" 
                :key="group.id"
                :class="[
                  bgSecondary, 
                  borderSecondary, 
                  'rounded-xl border-2 shadow-lg overflow-hidden transition-all duration-300 hover:shadow-2xl'
                ]"
              >
                <!-- Group Header -->
                <div :class="[isDark ? 'bg-gray-700/50' : 'bg-gray-100', 'px-6 py-4 border-b', borderSecondary]">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-4">
                      <!-- Icon -->
                      <div :class="[
                        isDark ? 'bg-blue-900/30 text-blue-400' : 'bg-blue-100 text-blue-600',
                        'w-12 h-12 rounded-lg flex items-center justify-center'
                      ]">
                        <!-- Hybrid Connectivity Hub Icon - OFFICIAL Microsoft Azure -->
                        <svg class="w-7 h-7" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 18 18"><defs><linearGradient id="uuid-d431b8f0" x1="11.079" y1="17.397" x2="2.392" y2="4.224" gradientTransform="translate(0 20) scale(1 -1)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0fafff"/><stop offset="1" stop-color="#2764e7"/></linearGradient><linearGradient id="uuid-fbb395b9" x1="11.079" y1="17.397" x2="2.392" y2="4.224" gradientTransform="translate(0 20) scale(1 -1)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0094f0"/><stop offset="1" stop-color="#2052cb"/></linearGradient><linearGradient id="uuid-1d01284c" x1="7.926" y1=".897" x2="6.275" y2="12.951" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#d8f7ff"/><stop offset="1" stop-color="#8cd0ff"/></linearGradient><linearGradient id="uuid-2ec8b26d" x1="11.615" y1="8.885" x2="11.615" y2="-.136" gradientTransform="translate(0 20) scale(1 -1)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#d8f7ff"/><stop offset="1" stop-color="#83b9f9"/></linearGradient></defs><path d="M1.604.125C.787.125.125.787.125,1.604v14.792c0,.817.662,1.479,1.479,1.479h10.513c.817,0,1.479-.662,1.479-1.479V7.626c0-.817-.662-1.479-1.479-1.479h-1.532V1.604c0-.817-.662-1.479-1.479-1.479H1.604Z" fill="url(#uuid-d431b8f0)"/><path d="M9.109,16.851h3.008c.251,0,.455-.204.455-.455V7.626c0-.251-.204-.455-.455-.455h-1.532c-.566,0-1.024-.459-1.024-1.024V1.604c0-.251-.204-.455-.455-.455H1.604c-.251,0-.455.204-.455.455v14.792c0,.251.204.455.455.455h7.505ZM9.116,17.875h3c.817,0,1.479-.662,1.479-1.479V7.626c0-.817-.662-1.479-1.479-1.479h-1.532V1.604c0-.817-.662-1.479-1.479-1.479H1.604C.787.125.125.787.125,1.604v14.792c0,.817.662,1.479,1.479,1.479h7.512Z" fill="url(#uuid-fbb395b9)" fill-rule="evenodd"/><path d="M4.246,14.336c0-.408.331-.74.74-.74h3.592c.408,0,.74.331.74.74v3.539h-5.071v-3.539Z" fill="#fff"/><path d="M3.612,2.344c-.613,0-1.109.497-1.109,1.109s.497,1.109,1.109,1.109,1.109-.497,1.109-1.109-.497-1.109-1.109-1.109ZM7.098,2.344c-.613,0-1.109.497-1.109,1.109s.497,1.109,1.109,1.109,1.109-.497,1.109-1.109-.497-1.109-1.109-1.109ZM7.098,5.83c-.613,0-1.109.497-1.109,1.109s.497,1.109,1.109,1.109,1.109-.497,1.109-1.109-.497-1.109-1.109-1.109ZM7.098,9.317c-.613,0-1.109.497-1.109,1.109s.497,1.109,1.109,1.109,1.109-.497,1.109-1.109-.497-1.109-1.109-1.109ZM10.585,9.317c-.613,0-1.109.497-1.109,1.109s.497,1.109,1.109,1.109,1.109-.497,1.109-1.109-.497-1.109-1.109-1.109ZM3.612,5.83c-.613,0-1.109.497-1.109,1.109s.497,1.109,1.109,1.109,1.109-.497,1.109-1.109-.497-1.109-1.109-1.109ZM3.612,9.317c-.613,0-1.109.497-1.109,1.109s.497,1.109,1.109,1.109,1.109-.497,1.109-1.109-.497-1.109-1.109-1.109Z" fill="url(#uuid-1d01284c)"/><path d="M7.732,17.87c-1.327-.082-2.377-1.184-2.377-2.531,0-1.375,1.094-2.494,2.46-2.535.364-1.721,1.892-3.012,3.721-3.012s3.357,1.291,3.721,3.013c.027,0,.055-.001.082-.001,1.4,0,2.536,1.135,2.536,2.536s-1.135,2.536-2.536,2.536h-7.607v-.005Z" fill="url(#uuid-2ec8b26d)"/></svg>
                      </div>
                      
                      <!-- Group Info -->
                      <div>
                        <h4 :class="['text-xl font-bold', textPrimary]">{{ group.name }}</h4>
                        <div class="flex items-center gap-3 mt-1">
                          <span :class="[
                            'px-2.5 py-0.5 rounded-full text-xs font-semibold',
                            isDark ? 'bg-purple-900/30 text-purple-300' : 'bg-purple-100 text-purple-700'
                          ]">
                            {{ group.groupType || 'System' }}
                          </span>
                          <span :class="['text-sm', textSecondary]">
                            {{ workersCache[group.name]?.length || 0 }} worker(s)
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Expand/Collapse Button -->
                    <button
                      @click="toggleWorkerGroup(group)"
                      :class="[
                        'px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200',
                        'flex items-center gap-2',
                        isDark 
                          ? 'bg-blue-900/30 text-blue-400 hover:bg-blue-900/50' 
                          : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                      ]"
                    >
                      <span>{{ expandedGroups.includes(group.name) ? 'Hide Workers' : 'Show Workers' }}</span>
                      <svg 
                        class="w-5 h-5 transition-transform duration-200" 
                        :class="{ 'rotate-180': expandedGroups.includes(group.name) }"
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </div>
                </div>

                <!-- Workers List (Expandable) -->
                <div v-if="expandedGroups.includes(group.name)" class="p-6">
                  <div v-if="!workersCache[group.name]" class="text-center py-8">
                    <svg class="animate-spin h-8 w-8 mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>

                  <div v-else-if="workersCache[group.name].length === 0" :class="['text-center py-8', textSecondary]">
                    <svg class="w-16 h-16 mx-auto mb-3 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/>
                    </svg>
                    <p class="text-sm font-medium">No workers in this group</p>
                  </div>

                  <!-- Workers Grid -->
                  <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div 
                      v-for="worker in workersCache[group.name]" 
                      :key="worker.id"
                      :class="[
                        isDark ? 'bg-gray-700/50 border-gray-600' : 'bg-white border-gray-200',
                        'border-2 rounded-lg p-5 hover:shadow-lg transition-all duration-200'
                      ]"
                    >
                      <!-- Worker Header -->
                      <div class="flex items-start justify-between mb-4">
                        <div class="flex-1">
                          <div class="flex items-center gap-2 mb-2">
                            <svg class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                            </svg>
                            <h5 :class="['font-bold text-lg', textPrimary]">{{ worker.name }}</h5>
                          </div>
                        </div>
                      </div>

                      <!-- Worker Details Grid -->
                      <div class="space-y-3">
                        <!-- Type -->
                        <div class="flex items-center gap-3">
                          <span :class="['text-xs font-medium w-24', textSecondary]">Type</span>
                          <span :class="[
                            'px-2.5 py-1 rounded-md text-xs font-semibold',
                            isDark ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-100 text-blue-700'
                          ]">
                            {{ worker.workerType || 'Server - Azure Arc' }}
                          </span>
                        </div>

                        <!-- Platform -->
                        <div v-if="worker.platform" class="flex items-center gap-3">
                          <span :class="['text-xs font-medium w-24', textSecondary]">Platform</span>
                          <span :class="['text-sm font-mono', textPrimary]">
                            {{ worker.platform }}
                          </span>
                        </div>

                        <!-- IP Address -->
                        <div class="flex items-center gap-3">
                          <span :class="['text-xs font-medium w-24', textSecondary]">IP Address</span>
                          <span :class="['text-sm font-mono', textPrimary]">
                            {{ worker.ip || 'N/A' }}
                          </span>
                        </div>

                        <!-- Registration Time -->
                        <div v-if="worker.registrationTime" class="flex items-center gap-3">
                          <span :class="['text-xs font-medium w-24', textSecondary]">Registered</span>
                          <span :class="['text-sm', textPrimary]">
                            {{ new Date(worker.registrationTime).toLocaleString() }}
                          </span>
                        </div>

                        <!-- Last Seen -->
                        <div v-if="worker.lastSeenDateTime" class="flex items-center gap-3">
                          <span :class="['text-xs font-medium w-24', textSecondary]">Last Seen</span>
                          <span :class="['text-sm', textPrimary]">
                            {{ formatLastSeen(worker.lastSeenDateTime) }}
                          </span>
                        </div>

                        <!-- VM Resource (if available) -->
                        <div v-if="worker.vmResourceId" class="mt-4 pt-3 border-t" :class="[borderSecondary]">
                          <span :class="['text-xs font-medium block mb-1', textSecondary]">Azure VM</span>
                          <span :class="['text-xs font-mono break-all', textPrimary]">
                            {{ worker.vmResourceId }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Variables Tab -->
        <div v-if="currentTab === 'variables'">
          <div v-if="!selectedAccount" :class="['text-center py-12', textSecondary]">
            <p>Please select an Automation Account from the Overview tab</p>
          </div>
          
          <div v-else>
            <div class="flex items-center justify-between mb-4">
              <h3 :class="['text-lg font-semibold', textPrimary]">
                Variables in {{ selectedAccount.name }}
              </h3>
              <button
                @click="loadVariables(false)"
                :disabled="loadingVariables"
                :class="[
                  'px-4 py-2 rounded transition-colors',
                  isDark ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-800',
                  loadingVariables ? 'opacity-50 cursor-not-allowed' : ''
                ]"
              >
                {{ loadingVariables ? 'Loading...' : 'Refresh' }}
              </button>
            </div>

            <div v-if="loadingVariables" class="text-center py-12">
              <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <p :class="['mt-4', textSecondary]">Loading variables...</p>
            </div>

            <div v-else-if="variables.length === 0" :class="['text-center py-12', textSecondary]">
              <svg :class="['w-16 h-16 mx-auto mb-4', textIcon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p>No variables found in this Automation Account</p>
            </div>

            <div v-else class="space-y-3">
              <div 
                v-for="variable in variables" 
                :key="variable.id"
                :class="[isDark ? 'bg-gray-700' : 'bg-gray-50', 'p-4 rounded-lg border', borderPrimary]"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center space-x-3">
                      <h4 :class="['font-semibold', textPrimary]">{{ variable.name }}</h4>
                      <span 
                        v-if="variable.isEncrypted"
                        :class="[
                          isDark ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-800',
                          'px-2 py-0.5 text-xs font-semibold rounded'
                        ]"
                      >
                        🔒 Encrypted
                      </span>
                    </div>
                    
                    <div v-if="variable.description" :class="['text-sm mt-2', textSecondary]">
                      {{ variable.description }}
                    </div>
                    
                    <div :class="[isDark ? 'bg-gray-800' : 'bg-white', 'p-3 rounded mt-3 font-mono text-sm', textPrimary]">
                      <div v-if="variable.isEncrypted" class="text-red-400">
                        ⚠️ Value is encrypted and cannot be retrieved via API
                      </div>
                      <div v-else-if="variable.value">
                        <span class="text-green-400">Value:</span> {{ variable.value }}
                      </div>
                      <div v-else class="text-gray-500">
                        (No value set)
                      </div>
                    </div>
                    
                    <div class="flex items-center space-x-4 mt-3 text-xs" :class="[textSecondary]">
                      <span v-if="variable.creationTime">
                        Created: {{ new Date(variable.creationTime).toLocaleString() }}
                      </span>
                      <span v-if="variable.lastModifiedTime">
                        Modified: {{ new Date(variable.lastModifiedTime).toLocaleString() }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Red Team Note -->
              <div :class="[isDark ? 'bg-red-900 border-red-700' : 'bg-red-50 border-red-200', 'p-4 rounded-lg border mt-6']">
                <div class="flex items-start">
                  <svg class="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                  <div>
                    <h4 :class="['font-semibold', isDark ? 'text-red-300' : 'text-red-800']">Red Team Note</h4>
                    <p :class="['text-sm mt-1', isDark ? 'text-red-200' : 'text-red-700']">
                      Variables often contain sensitive data like API keys, connection strings, and credentials. 
                      Encrypted variables cannot be retrieved via API but may be accessible from runbook execution context.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Permissions Tab -->
        <div v-if="currentTab === 'permissions'">
          <div v-if="!selectedAccount" :class="['text-center py-12', textSecondary]">
            <p>Please select an Automation Account from the Overview tab</p>
          </div>
          
          <div v-else>
            <div class="flex items-center justify-between mb-4">
              <h3 :class="['text-lg font-semibold', textPrimary]">
                Permissions on {{ selectedAccount.name }}
              </h3>
              <button
                @click="loadPermissions"
                :disabled="loadingPermissions"
                class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                {{ loadingPermissions ? 'Checking...' : 'Check Permissions' }}
              </button>
            </div>

            <div v-if="loadingPermissions" class="text-center py-12">
              <svg class="animate-spin h-8 w-8 mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>

            <div v-else-if="permissions">
              <div :class="[bgSecondary, 'p-4 rounded-lg']">
                <h4 :class="['font-semibold mb-3', textPrimary]">Your Permissions</h4>

                <div v-if="permissions.length === 0" :class="['text-sm', textSecondary]">
                  No permissions found or insufficient access
                </div>

                <div v-else class="space-y-4">
                  <div 
                    v-for="(perm, idx) in permissions" 
                    :key="idx"
                    :class="[isDark ? 'bg-gray-700' : 'bg-gray-100', 'p-3 rounded']"
                  >
                    <div class="mb-2">
                      <span :class="['font-medium', textPrimary]">Actions:</span>
                      <div v-if="perm.actions.length === 0" :class="['text-sm mt-1', textSecondary]">
                        None
                      </div>
                      <ul v-else class="list-disc list-inside mt-1 text-sm" :class="[textSecondary]">
                        <li v-for="action in perm.actions.slice(0, 10)" :key="action">{{ action }}</li>
                        <li v-if="perm.actions.length > 10" class="text-blue-500">
                          + {{ perm.actions.length - 10 }} more actions...
                        </li>
                      </ul>
                    </div>

                    <div v-if="perm.notActions && perm.notActions.length > 0" class="mt-2">
                      <span :class="['font-medium', textPrimary]">Not Actions:</span>
                      <ul class="list-disc list-inside mt-1 text-sm" :class="[textSecondary]">
                        <li v-for="action in perm.notActions.slice(0, 5)" :key="action">{{ action }}</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Managed Identity Tab -->
        <div v-if="currentTab === 'identity'">
          <div v-if="!selectedAccount" :class="['text-center py-12', textSecondary]">
            <p>Please select an Automation Account from the Overview tab</p>
          </div>
          
          <div v-else>
            <div class="flex items-center justify-between mb-4">
              <h3 :class="['text-lg font-semibold', textPrimary]">
                Managed Identity Analysis - {{ selectedAccount.name }}
              </h3>
              <button
                @click="checkManagedIdentity"
                :disabled="loadingIdentity"
                class="refresh-btn"
              >
                <svg v-if="loadingIdentity" class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>{{ loadingIdentity ? 'Analyzing...' : 'Analyze Identity' }}</span>
              </button>
            </div>

            <!-- Loading State -->
            <div v-if="loadingIdentity" class="text-center py-12">
              <svg class="animate-spin h-8 w-8 mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p :class="['mt-4', textSecondary]">Checking Managed Identity and role assignments...</p>
            </div>

            <!-- Identity Results -->
            <div v-else-if="identityData">
              <!-- FASE 1: Overview Cards -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <!-- Identity Status Card -->
                <div class="bg-gray-800 rounded-lg border p-4" :class="identityData.identity.enabled ? 'border-green-500' : 'border-gray-600'">
                  <div class="flex items-center justify-between mb-3">
                    <h3 class="text-lg font-semibold text-white flex items-center">
                      🎭 Identity Status
                    </h3>
                    <span 
                      :class="[
                        'px-2 py-1 text-xs font-semibold rounded-full',
                        identityData.identity.enabled 
                          ? 'bg-green-900 text-green-300' 
                          : 'bg-gray-700 text-gray-300'
                      ]"
                    >
                      {{ identityData.identity.enabled ? '✓ ENABLED' : '✗ DISABLED' }}
                    </span>
                  </div>

                  <div v-if="identityData.identity.enabled" class="space-y-2 text-sm">
                    <div class="flex justify-between text-gray-300">
                      <span>Type:</span>
                      <span class="font-semibold text-white">{{ identityData.identity.type }}</span>
                    </div>
                    <div class="flex flex-col mt-2 pt-2 border-t border-gray-700">
                      <span class="text-gray-400 text-xs mb-1">Principal ID:</span>
                      <span class="font-mono text-xs text-blue-400 break-all">{{ identityData.identity.principalId }}</span>
                    </div>
                  </div>

                  <div v-else class="text-sm text-gray-400">
                    Managed Identity is not enabled for this Automation Account
                  </div>
                </div>

                <!-- Security Risk Assessment Card -->
                <div v-if="identityData.identity.enabled" class="bg-gray-800 rounded-lg border p-4" 
                  :class="identityData.riskScore === 'Critical' ? 'border-red-500' :
                          identityData.riskScore === 'High' ? 'border-orange-500' :
                          identityData.riskScore === 'Medium' ? 'border-yellow-500' :
                          'border-green-500'">
                  <div class="flex items-center justify-between mb-3">
                    <h3 class="text-lg font-semibold text-white flex items-center">
                      🛡️ Risk Assessment
                    </h3>
                    <span 
                      :class="[
                        'px-2 py-1 text-xs font-semibold rounded-full',
                        identityData.riskScore === 'Critical' ? 'bg-red-900 text-red-300' :
                        identityData.riskScore === 'High' ? 'bg-orange-900 text-orange-300' :
                        identityData.riskScore === 'Medium' ? 'bg-yellow-900 text-yellow-300' :
                        'bg-green-900 text-green-300'
                      ]"
                    >
                      {{ identityData.riskScore.toUpperCase() }}
                    </span>
                  </div>

                  <div class="space-y-2 text-sm">
                    <div class="flex justify-between text-gray-300">
                      <span>Role Assignments:</span>
                      <span class="font-semibold text-white text-xl">{{ identityData.roleAssignments.length }}</span>
                    </div>
                    <div v-if="identityData.riskScore === 'Critical' || identityData.riskScore === 'High'" class="mt-3 pt-3 border-t border-gray-700">
                      <p class="text-red-400 text-xs">
                        ⚠️ High-privilege roles detected - review permissions immediately
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Role Assignments -->
              <div v-if="identityData.roleAssignments.length > 0" class="bg-gray-800 rounded-lg border border-gray-700 p-4 mb-4">
                <h3 class="text-lg font-semibold text-white mb-4">🔑 Role Assignments</h3>
                
                <div class="space-y-3">
                  <div 
                    v-for="(role, idx) in identityData.roleAssignments" 
                    :key="idx"
                    class="bg-gray-900 rounded-lg p-4 border-l-4"
                    :class="role.roleName.toLowerCase().includes('owner') || role.roleName.toLowerCase().includes('contributor') ? 'border-red-500' : 
                            role.roleName.toLowerCase().includes('admin') ? 'border-orange-500' : 
                            'border-blue-500'"
                  >
                    <div class="flex items-start justify-between mb-2">
                      <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                          <span class="text-white font-semibold text-base">{{ role.roleName }}</span>
                          <span 
                            class="px-2 py-1 text-xs font-semibold rounded"
                            :class="role.scopeLevel === 'Subscription' ? 'bg-purple-900 text-purple-300' :
                                    role.scopeLevel === 'Resource Group' ? 'bg-blue-900 text-blue-300' :
                                    'bg-gray-700 text-gray-300'"
                          >
                            {{ role.scopeLevel }}
                          </span>
                        </div>
                        
                        <div class="text-sm mt-2">
                          <span class="text-gray-400 text-xs">Scope:</span>
                          <div class="font-mono text-xs mt-1 text-gray-300 break-all bg-gray-800 p-2 rounded">
                            {{ role.scope }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Recommendations -->
              <div v-if="identityData.recommendations.length > 0" class="bg-gray-800 rounded-lg border border-yellow-500 p-4">
                <h3 class="text-lg font-semibold text-white mb-4">💡 Security Recommendations</h3>
                
                <ul class="space-y-3">
                  <li 
                    v-for="(rec, idx) in identityData.recommendations" 
                    :key="idx"
                    class="text-sm flex items-start bg-yellow-900/20 p-3 rounded-lg"
                  >
                    <span class="text-yellow-400 mr-2 text-lg">⚠️</span>
                    <span class="text-gray-300">{{ rec }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Runbook Modal -->
    <div 
      v-if="showCreateRunbookModal" 
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="showCreateRunbookModal = false"
    >
      <div :class="[bgPrimary, 'rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto']">
        <div class="p-6">
          <h2 :class="['text-2xl font-bold mb-4', textPrimary]">Create New Runbook</h2>
          
          <div class="space-y-4">
            <div>
              <label :class="['block text-sm font-medium mb-1', textPrimary]">Runbook Name *</label>
              <input
                v-model="newRunbook.name"
                type="text"
                :class="[
                  bgSecondary,
                  textPrimary,
                  borderSecondary,
                  'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'
                ]"
                placeholder="my-runbook"
              />
            </div>

            <div>
              <label :class="['block text-sm font-medium mb-1', textPrimary]">Runbook Type</label>
              <select
                v-model="newRunbook.type"
                :class="[
                  bgSecondary,
                  textPrimary,
                  borderSecondary,
                  'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'
                ]"
              >
                <option value="PowerShell">PowerShell</option>
                <option value="PowerShellWorkflow">PowerShell Workflow</option>
                <option value="Python2">Python 2</option>
                <option value="Python3">Python 3</option>
              </select>
            </div>

            <div>
              <label :class="['block text-sm font-medium mb-1', textPrimary]">Description (optional)</label>
              <input
                v-model="newRunbook.description"
                type="text"
                :class="[
                  bgSecondary,
                  textPrimary,
                  borderSecondary,
                  'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'
                ]"
                placeholder="Runbook description"
              />
            </div>

            <div>
              <label :class="['block text-sm font-medium mb-1', textPrimary]">Script Content</label>
              <textarea
                v-model="newRunbook.content"
                rows="12"
                :class="[
                  bgSecondary,
                  textPrimary,
                  borderSecondary,
                  'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500 font-mono text-sm'
                ]"
                placeholder="Write-Output 'Hello from Automation!'"
              ></textarea>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button
              @click="showCreateRunbookModal = false"
              :class="[bgSecondary, textPrimary, 'px-4 py-2 rounded-lg hover:bg-opacity-80 transition-colors']"
            >
              Cancel
            </button>
            <button
              @click="createRunbook"
              :disabled="creatingRunbook || !newRunbook.name"
              class="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg transition-colors"
            >
              {{ creatingRunbook ? 'Creating...' : 'Create Runbook' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- View Runbook Content Modal -->
    <div 
      v-if="showRunbookContentModal" 
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="showRunbookContentModal = false"
    >
      <div :class="[bgPrimary, 'rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto']">
        <div class="p-6">
          <h2 :class="['text-2xl font-bold mb-4', textPrimary]">{{ selectedRunbook?.name }}</h2>
          
          <div v-if="loadingRunbookContent" class="text-center py-12">
            <svg class="animate-spin h-8 w-8 mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>

          <pre v-else :class="[bgSecondary, textPrimary, 'p-4 rounded-lg overflow-x-auto text-sm']"><code>{{ runbookContent }}</code></pre>

          <div class="flex justify-end mt-4">
            <button
              @click="showRunbookContentModal = false"
              :class="[bgSecondary, textPrimary, 'px-4 py-2 rounded-lg hover:bg-opacity-80 transition-colors']"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Start Runbook Modal -->
    <div 
      v-if="showStartRunbookModal" 
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="showStartRunbookModal = false"
    >
      <div :class="[bgPrimary, 'rounded-lg max-w-xl w-full']">
        <div class="p-6">
          <h2 :class="['text-2xl font-bold mb-4', textPrimary]">Start Runbook: {{ selectedRunbook?.name }}</h2>
          
          <div class="space-y-4">
            <div>
              <label :class="['block text-sm font-medium mb-1', textPrimary]">Run On (optional)</label>
              <select
                v-model="runbookExecution.runOn"
                :class="[
                  bgSecondary,
                  textPrimary,
                  borderSecondary,
                  'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'
                ]"
              >
                <option value="">Azure (Cloud)</option>
                <option v-for="group in hybridWorkerGroups" :key="group.name" :value="group.name">
                  {{ group.name }} (Hybrid Worker)
                </option>
              </select>
              <p :class="['text-xs mt-1', textSecondary]">
                Select a Hybrid Worker Group to execute on-premises, or leave empty for cloud execution
              </p>
            </div>

            <div v-if="runbookExecution.output" :class="[bgSecondary, 'p-4 rounded-lg']">
              <h4 :class="['font-semibold mb-2', textPrimary]">Job Started Successfully</h4>
              <p :class="['text-sm', textSecondary]">
                Job ID: <span class="font-mono text-blue-400">{{ runbookExecution.jobId }}</span>
              </p>
              <p :class="['text-xs mt-2', textSecondary]">
                The runbook job has been queued. You can check the job status and output using the Job ID.
              </p>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button
              @click="showStartRunbookModal = false"
              :class="[bgSecondary, textPrimary, 'px-4 py-2 rounded-lg hover:bg-opacity-80 transition-colors']"
            >
              Close
            </button>
            <button
              v-if="!runbookExecution.output"
              @click="executeRunbook"
              :disabled="startingRunbook"
              class="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg transition-colors"
            >
              {{ startingRunbook ? 'Starting...' : 'Start Job' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Runbook Modal -->
    <div 
      v-if="showDeleteModal" 
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showDeleteModal = false"
    >
      <div :class="[bgPrimary, 'rounded-lg shadow-xl p-6 max-w-md w-full mx-4']">
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div class="ml-3 flex-1">
            <h3 :class="['text-lg font-medium', textPrimary]">Delete Runbook</h3>
            <div :class="['mt-2 text-sm', textSecondary]">
              <p>Are you sure you want to delete the runbook <strong>{{ runbookToDelete?.name }}</strong>?</p>
              <p class="mt-2">This action cannot be undone.</p>
            </div>
          </div>
        </div>

        <div class="mt-6 flex justify-end space-x-3">
          <button
            @click="showDeleteModal = false"
            :disabled="deletingRunbook"
            :class="[
              'px-4 py-2 rounded transition-colors',
              isDark ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-gray-300 hover:bg-gray-400 text-gray-800',
              deletingRunbook ? 'opacity-50 cursor-not-allowed' : ''
            ]"
          >
            Cancel
          </button>
          <button
            @click="deleteRunbook"
            :disabled="deletingRunbook"
            class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ deletingRunbook ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AutomationAccountsView',
  props: {
    isDark: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      subscriptions: [],
      selectedSubscription: '',
      automationAccounts: [],
      selectedAccount: null,
      loading: false,
      error: null,
      
      // Cache (5 min TTL)
      accountsCache: null,
      accountsCacheTime: null,
      runbooksCache: {},
      hybridWorkersCache: {},
      CACHE_TTL: 300000, // 5 minutes
      
      // Tabs
      currentTab: 'overview',
      tabs: [
        { id: 'overview', name: 'Overview' },
        { id: 'runbooks', name: 'Runbooks' },
        { id: 'hybrid-workers', name: 'Hybrid Workers' },
        { id: 'variables', name: 'Variables' },
        { id: 'permissions', name: 'Permissions' },
        { id: 'identity', name: 'Managed Identity' }
      ],
      
      // Runbooks
      runbooks: [],
      loadingRunbooks: false,
      showCreateRunbookModal: false,
      creatingRunbook: false,
      newRunbook: {
        name: '',
        type: 'PowerShell',
        description: '',
        content: ''
      },
      showRunbookContentModal: false,
      loadingRunbookContent: false,
      selectedRunbook: null,
      runbookContent: '',
      showStartRunbookModal: false,
      startingRunbook: false,
      runbookExecution: {
        runOn: '',
        output: null,
        jobId: null
      },
      
      // Delete Runbook
      showDeleteModal: false,
      runbookToDelete: null,
      deletingRunbook: false,
      
      // Hybrid Workers
      hybridWorkerGroups: [],
      loadingHybridWorkers: false,
      expandedGroups: [],
      workersCache: {},
      
      // Variables
      variables: [],
      loadingVariables: false,
      variablesCache: {},
      
      // Permissions
      permissions: null,
      loadingPermissions: false,
      
      // Managed Identity
      identityData: null,
      loadingIdentity: false
    }
  },
  computed: {
    bgPrimary() {
      return this.isDark ? 'bg-gray-800' : 'bg-white';
    },
    bgSecondary() {
      return this.isDark ? 'bg-gray-700' : 'bg-gray-100';
    },
    bgContainer() {
      return this.isDark ? 'bg-gray-900' : 'bg-gray-50';
    },
    textPrimary() {
      return this.isDark ? 'text-white' : 'text-gray-900';
    },
    textSecondary() {
      return this.isDark ? 'text-gray-400' : 'text-gray-600';
    },
    textTertiary() {
      return this.isDark ? 'text-gray-300' : 'text-gray-700';
    },
    textPlaceholder() {
      return this.isDark ? 'text-gray-500' : 'text-gray-500';
    },
    textIcon() {
      return this.isDark ? 'text-gray-600' : 'text-gray-400';
    },
    borderPrimary() {
      return this.isDark ? 'border-gray-700' : 'border-gray-300';
    },
    borderSecondary() {
      return this.isDark ? 'border-gray-600' : 'border-gray-400';
    }
  },
  mounted() {
    this.loadSubscriptions()
  },
  watch: {
    selectedAccount(newAccount) {
      if (newAccount) {
        if (this.currentTab === 'runbooks') {
          this.loadRunbooks()
        } else if (this.currentTab === 'hybrid-workers') {
          this.loadHybridWorkerGroups()
        }
      }
    },
    currentTab(newTab) {
      if (this.selectedAccount) {
        if (newTab === 'runbooks' && this.runbooks.length === 0) {
          this.loadRunbooks()
        } else if (newTab === 'hybrid-workers' && this.hybridWorkerGroups.length === 0) {
          this.loadHybridWorkerGroups()
        } else if (newTab === 'variables' && this.variables.length === 0) {
          this.loadVariables()
        }
      }
    }
  },
  methods: {
    formatLastSeen(dateTime) {
      if (!dateTime) return 'N/A'
      
      const now = new Date()
      const lastSeen = new Date(dateTime)
      const diffMs = now - lastSeen
      const diffMins = Math.floor(diffMs / (1000 * 60))
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
      
      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
      if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
      
      // For older dates, show full date
      return lastSeen.toLocaleString()
    },
    
    async loadSubscriptions() {
      try {
        const response = await axios.get('http://localhost:5000/api/azure/subscriptions')
        if (response.data.success) {
          this.subscriptions = response.data.subscriptions
          // Check if no subscriptions - likely no ARM token
          if (this.subscriptions.length === 0) {
            this.error = 'No valid ARM token found'
          } else {
            this.error = null
            if (this.subscriptions.length === 1) {
              this.selectedSubscription = this.subscriptions[0].id
              this.loadAutomationAccounts()
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
    
    async loadAutomationAccounts(useCache = true) {
      if (!this.selectedSubscription) return
      
      // Check cache
      if (useCache && this.accountsCache && this.accountsCacheTime) {
        const age = Date.now() - this.accountsCacheTime
        if (age < this.CACHE_TTL) {
          console.log('[CACHE HIT] Automation Accounts')
          this.automationAccounts = this.accountsCache
          return
        }
      }
      
      this.loading = true
      this.error = null
      this.selectedAccount = null
      this.automationAccounts = []
      
      try {
        const response = await axios.get(`http://localhost:5000/api/azure/subscriptions/${this.selectedSubscription}/automation`)
        
        if (response.data.success) {
          this.automationAccounts = response.data.automation_accounts
          
          // Cache results
          this.accountsCache = this.automationAccounts
          this.accountsCacheTime = Date.now()
        } else {
          this.error = response.data.error || 'Failed to load Automation Accounts'
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message
      } finally {
        this.loading = false
      }
    },
    
    forceRefresh() {
      // Force refresh (bypass cache)
      this.accountsCache = null
      this.accountsCacheTime = null
      this.runbooksCache = {}
      this.hybridWorkersCache = {}
      this.loadAutomationAccounts(false)
    },
    
    selectAutomationAccount(account) {
      this.selectedAccount = account
      this.currentTab = 'runbooks'
    },
    
    async loadRunbooks(useCache = true) {
      if (!this.selectedAccount) return
      
      // Check cache
      const cacheKey = this.selectedAccount.id
      if (useCache && this.runbooksCache[cacheKey]) {
        const cached = this.runbooksCache[cacheKey]
        if (Date.now() - cached.time < this.CACHE_TTL) {
          console.log('[CACHE HIT] Runbooks')
          this.runbooks = cached.data
          return
        }
      }
      
      this.loadingRunbooks = true
      try {
        const response = await axios.get(`http://localhost:5000/api/azure/automation/${encodeURIComponent(this.selectedAccount.id)}/runbooks`)
        
        if (response.data.success) {
          this.runbooks = response.data.runbooks
          
          // Cache results
          this.runbooksCache[cacheKey] = {
            data: this.runbooks,
            time: Date.now()
          }
        } else {
          this.error = response.data.error
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message
      } finally {
        this.loadingRunbooks = false
      }
    },
    
    async createRunbook() {
      if (!this.newRunbook.name) return
      
      this.creatingRunbook = true
      try {
        const response = await axios.post(
          `http://localhost:5000/api/azure/automation/${encodeURIComponent(this.selectedAccount.id)}/runbooks/create`,
          {
            runbook_name: this.newRunbook.name,
            runbook_type: this.newRunbook.type,
            description: this.newRunbook.description,
            script_content: this.newRunbook.content
          }
        )
        
        if (response.data.success) {
          this.showCreateRunbookModal = false
          this.newRunbook = {
            name: '',
            type: 'PowerShell',
            description: '',
            content: ''
          }
          
          // Clear cache and reload
          delete this.runbooksCache[this.selectedAccount.id]
          this.loadRunbooks(false)
          
          alert('Runbook created successfully!')
        } else {
          alert(`Failed to create runbook: ${response.data.error}`)
        }
      } catch (err) {
        alert(`Error: ${err.response?.data?.error || err.message}`)
      } finally {
        this.creatingRunbook = false
      }
    },
    
    async viewRunbookContent(runbook) {
      this.selectedRunbook = runbook
      this.showRunbookContentModal = true
      this.loadingRunbookContent = true
      this.runbookContent = ''
      
      try {
        // FIX: Remove leading slash from runbook.id to avoid double slash in URL
        // runbook.id = "/subscriptions/..." → cleanId = "subscriptions/..."
        const cleanId = runbook.id.startsWith('/') ? runbook.id.substring(1) : runbook.id
        const response = await axios.get(`http://localhost:5000/api/azure/automation/runbook/${encodeURIComponent(cleanId)}/content`)
        
        if (response.data.success) {
          this.runbookContent = response.data.content
        } else {
          this.runbookContent = `Error: ${response.data.error}`
        }
      } catch (err) {
        this.runbookContent = `Error: ${err.response?.data?.error || err.message}`
      } finally {
        this.loadingRunbookContent = false
      }
    },
    
    startRunbookExecution(runbook) {
      this.selectedRunbook = runbook
      this.showStartRunbookModal = true
      this.runbookExecution = {
        runOn: '',
        output: null,
        jobId: null
      }
    },
    
    async executeRunbook() {
      this.startingRunbook = true
      
      try {
        const response = await axios.post(
          `http://localhost:5000/api/azure/automation/${encodeURIComponent(this.selectedAccount.id)}/runbooks/${this.selectedRunbook.name}/start`,
          {
            run_on: this.runbookExecution.runOn || null
          }
        )
        
        if (response.data.success) {
          this.runbookExecution.output = response.data
          this.runbookExecution.jobId = response.data.job_id
        } else {
          alert(`Failed to start runbook: ${response.data.error}`)
        }
      } catch (err) {
        alert(`Error: ${err.response?.data?.error || err.message}`)
      } finally {
        this.startingRunbook = false
      }
    },
    
    confirmDeleteRunbook(runbook) {
      this.runbookToDelete = runbook
      this.showDeleteModal = true
    },
    
    async deleteRunbook() {
      this.deletingRunbook = true
      
      try {
        const cleanId = this.runbookToDelete.id.startsWith('/') 
          ? this.runbookToDelete.id.substring(1) 
          : this.runbookToDelete.id
        
        const response = await axios.delete(
          `http://localhost:5000/api/azure/automation/runbook/${encodeURIComponent(cleanId)}`
        )
        
        if (response.data.success) {
          // Remove runbook from cache
          const cacheKey = this.selectedAccount.id
          if (this.runbooksCache[cacheKey]) {
            this.runbooksCache[cacheKey].data = this.runbooksCache[cacheKey].data.filter(
              r => r.id !== this.runbookToDelete.id
            )
          }
          
          // Close modal and refresh
          this.showDeleteModal = false
          this.runbookToDelete = null
          
          // Reload runbooks to refresh the list
          await this.loadRunbooks(false)
        } else {
          alert(`Failed to delete runbook: ${response.data.error}`)
        }
      } catch (err) {
        alert(`Error: ${err.response?.data?.error || err.message}`)
      } finally {
        this.deletingRunbook = false
      }
    },
    
    async loadHybridWorkerGroups(useCache = true) {
      if (!this.selectedAccount) return
      
      // Check cache
      const cacheKey = this.selectedAccount.id
      if (useCache && this.hybridWorkersCache[cacheKey]) {
        const cached = this.hybridWorkersCache[cacheKey]
        if (Date.now() - cached.time < this.CACHE_TTL) {
          console.log('[CACHE HIT] Hybrid Workers')
          this.hybridWorkerGroups = cached.data
          return
        }
      }
      
      this.loadingHybridWorkers = true
      try {
        const response = await axios.get(`http://localhost:5000/api/azure/automation/${encodeURIComponent(this.selectedAccount.id)}/hybridworkers`)
        
        if (response.data.success) {
          this.hybridWorkerGroups = response.data.hybrid_worker_groups
          
          // Cache results
          this.hybridWorkersCache[cacheKey] = {
            data: this.hybridWorkerGroups,
            time: Date.now()
          }
        } else {
          this.error = response.data.error
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message
      } finally {
        this.loadingHybridWorkers = false
      }
    },
    
    async toggleWorkerGroup(group) {
      const index = this.expandedGroups.indexOf(group.name)
      
      if (index > -1) {
        // Collapse
        this.expandedGroups.splice(index, 1)
      } else {
        // Expand
        this.expandedGroups.push(group.name)
        
        // Load workers if not cached
        if (!this.workersCache[group.name]) {
          try {
            const response = await axios.get(
              `http://localhost:5000/api/azure/automation/${encodeURIComponent(this.selectedAccount.id)}/hybridworkers/${group.name}`
            )
            
            if (response.data.success) {
              this.workersCache[group.name] = response.data.hybrid_workers
            }
          } catch (err) {
            console.error('Failed to load workers:', err)
            this.workersCache[group.name] = []
          }
        }
      }
    },
    
    async loadVariables(useCache = true) {
      if (!this.selectedAccount) return
      
      // Check cache
      const cacheKey = this.selectedAccount.id
      if (useCache && this.variablesCache[cacheKey]) {
        const cached = this.variablesCache[cacheKey]
        if (Date.now() - cached.time < this.CACHE_TTL) {
          console.log('[CACHE HIT] Variables')
          this.variables = cached.data
          return
        }
      }
      
      console.log('[CACHE MISS] Variables - fetching from API')
      this.loadingVariables = true
      try {
        const response = await axios.get(
          `http://localhost:5000/api/azure/automation/${encodeURIComponent(this.selectedAccount.id)}/variables`
        )
        
        if (response.data.success) {
          this.variables = response.data.variables || []
          
          // Cache result
          this.variablesCache[cacheKey] = {
            data: this.variables,
            time: Date.now()
          }
        } else {
          this.error = response.data.error
          this.variables = []
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message
        this.variables = []
      } finally {
        this.loadingVariables = false
      }
    },
    
    async loadPermissions() {
      if (!this.selectedAccount) return
      
      this.loadingPermissions = true
      try {
        const response = await axios.get(
          `http://localhost:5000/api/azure/permissions/check?resource_id=${encodeURIComponent(this.selectedAccount.id)}`
        )
        
        if (response.data.success) {
          this.permissions = response.data.permissions
        } else {
          this.error = response.data.error
          this.permissions = []
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message
        this.permissions = []
      } finally {
        this.loadingPermissions = false
      }
    },
    
    async checkManagedIdentity() {
      if (!this.selectedAccount) return
      
      this.loadingIdentity = true
      this.identityData = null
      this.error = null
      
      try {
        // Remove leading slash if present
        const accountId = this.selectedAccount.id.startsWith('/') 
          ? this.selectedAccount.id.substring(1) 
          : this.selectedAccount.id
        
        const response = await axios.get(
          `http://localhost:5000/api/azure/automation/${encodeURIComponent(accountId)}/managed-identity`
        )
        
        if (response.data.success) {
          this.identityData = response.data
          console.log('[Identity] Analysis complete:', this.identityData)
        } else {
          this.error = response.data.error || 'Failed to analyze Managed Identity'
        }
      } catch (err) {
        console.error('[Identity] Error:', err)
        this.error = err.response?.data?.error || err.message || 'Failed to check Managed Identity'
      } finally {
        this.loadingIdentity = false
      }
    }
  }
}
</script>

<style scoped>
.bg-gray-750 {
  background-color: #2d3748;
}

/* KeyVaults-style buttons */
.subscription-select {
  padding: 10px 15px;
  border: 1px solid #4a5568;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  min-width: 250px;
  background: #2d3748;
  color: #f3f4f6;
}

.subscription-select:focus {
  outline: none;
  border-color: #3498db;
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
</style>

