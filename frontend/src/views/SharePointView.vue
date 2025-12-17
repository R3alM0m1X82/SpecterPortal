<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-white">SharePoint Sites</h1>
        <p class="text-gray-400 mt-1">Browse and explore SharePoint site collections</p>
      </div>
      <div class="flex items-center space-x-3">
        <button
          @click="loadSites"
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          <span v-if="loading">Loading...</span>
          <span v-else>🔄 Refresh</span>
        </button>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="mb-6">
      <div class="relative">
        <input
          v-model="searchQuery"
          @keyup.enter="searchSites"
          type="text"
          placeholder="Search SharePoint sites..."
          class="w-full px-4 py-3 pl-12 bg-gray-800 border border-gray-700 text-white placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <svg class="absolute left-4 top-3.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <button
          v-if="searchQuery"
          @click="clearSearch"
          class="absolute right-4 top-3.5 text-gray-400 hover:text-gray-200"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-gray-800 rounded-lg shadow p-4 border border-gray-700">
        <p class="text-gray-400 text-sm">Total Sites</p>
        <p class="text-2xl font-bold text-blue-400">{{ sites.length }}</p>
      </div>
      <div class="bg-gray-800 rounded-lg shadow p-4 border border-gray-700">
        <p class="text-gray-400 text-sm">Team Sites</p>
        <p class="text-2xl font-bold text-green-400">{{ teamSitesCount }}</p>
      </div>
      <div class="bg-gray-800 rounded-lg shadow p-4 border border-gray-700">
        <p class="text-gray-400 text-sm">Communication Sites</p>
        <p class="text-2xl font-bold text-purple-400">{{ commSitesCount }}</p>
      </div>
      <div class="bg-gray-800 rounded-lg shadow p-4 border border-gray-700">
        <p class="text-gray-400 text-sm">Other Sites</p>
        <p class="text-2xl font-bold text-gray-300">{{ otherSitesCount }}</p>
      </div>
    </div>

    <!-- Token Error Banner -->
    <div v-if="tokenError" class="mb-6 bg-red-900/40 border-2 border-red-500 rounded-lg p-4">
      <div class="flex items-start">
        <svg class="w-8 h-8 text-red-400 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <h4 class="text-lg font-semibold text-red-300 mb-2">⚠️ No valid SharePoint token available</h4>
          <p class="text-sm text-red-200">
            Please authenticate with a token that has <span class="font-mono bg-red-800/50 px-1 rounded">Sites.Read.All</span> or <span class="font-mono bg-red-800/50 px-1 rounded">Sites.FullControl.All</span> scope
          </p>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Sites List -->
      <div class="lg:col-span-1">
        <div class="bg-gray-800 rounded-lg shadow border border-gray-700">
          <div class="p-4 border-b border-gray-700">
            <h2 class="text-lg font-semibold text-white">Sites</h2>
          </div>
          
          <div v-if="loading" class="p-8 text-center">
            <div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p class="text-gray-400">Loading sites...</p>
          </div>
          
          <div v-else-if="sites.length === 0" class="p-8 text-center">
            <div class="text-4xl mb-4">📂</div>
            <p class="text-gray-400">No SharePoint sites found</p>
            <p class="text-gray-500 text-sm mt-2">Try a different search query</p>
          </div>
          
          <div v-else class="divide-y divide-gray-700 max-h-[600px] overflow-y-auto">
            <div
              v-for="site in sites"
              :key="site.id"
              @click="selectSite(site)"
              class="p-4 hover:bg-gray-700 cursor-pointer transition-colors"
              :class="{ 'bg-blue-900/30': selectedSite?.id === site.id }"
            >
              <div class="flex items-start space-x-3">
                <div class="text-2xl">
                  {{ getSiteIcon(site.site_type) }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="font-medium text-white truncate">{{ site.name }}</p>
                  <p class="text-sm text-gray-400 truncate">{{ site.web_url }}</p>
                  <span class="inline-block mt-1 px-2 py-0.5 text-xs rounded-full"
                    :class="getSiteTypeBadgeClass(site.site_type)"
                  >
                    {{ site.site_type }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Site Details & Content -->
      <div class="lg:col-span-2">
        <!-- No Site Selected -->
        <div v-if="!selectedSite" class="bg-gray-800 rounded-lg shadow border border-gray-700 p-8 text-center">
          <div class="text-6xl mb-4">📋</div>
          <p class="text-gray-300 text-lg">Select a site to view details</p>
          <p class="text-gray-500 mt-2">Click on a site from the list to explore its content</p>
        </div>

        <!-- Site Details -->
        <div v-else class="space-y-6">
          <!-- Site Info Card -->
          <div class="bg-gray-800 rounded-lg shadow border border-gray-700">
            <div class="p-4 border-b border-gray-700">
              <div class="flex items-center justify-between">
                <h2 class="text-lg font-semibold text-white">{{ selectedSite.name }}</h2>
                <a
                  :href="selectedSite.web_url"
                  target="_blank"
                  class="px-3 py-1 text-sm bg-blue-900/50 text-blue-300 rounded-lg hover:bg-blue-900 transition-colors"
                >
                  🔗 Open in Browser
                </a>
              </div>
            </div>
            <div class="p-4">
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p class="text-gray-400">Type</p>
                  <p class="font-medium text-white">{{ selectedSite.site_type }}</p>
                </div>
                <div>
                  <p class="text-gray-400">Created</p>
                  <p class="font-medium text-white">{{ formatDate(selectedSite.created) }}</p>
                </div>
                <div class="col-span-2">
                  <p class="text-gray-400">Description</p>
                  <p class="font-medium text-white">{{ selectedSite.description || 'No description' }}</p>
                </div>
                <div class="col-span-2">
                  <p class="text-gray-400">URL</p>
                  <p class="font-mono text-xs break-all text-gray-300">{{ selectedSite.web_url }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Tabs -->
          <div class="bg-gray-800 rounded-lg shadow border border-gray-700">
            <div class="border-b border-gray-700">
              <nav class="flex -mb-px">
                <button
                  @click="activeTab = 'drives'"
                  class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
                  :class="activeTab === 'drives' 
                    ? 'border-blue-500 text-blue-400' 
                    : 'border-transparent text-gray-400 hover:text-gray-200'"
                >
                  📁 Document Libraries
                </button>
                <button
                  @click="activeTab = 'lists'"
                  class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
                  :class="activeTab === 'lists' 
                    ? 'border-blue-500 text-blue-400' 
                    : 'border-transparent text-gray-400 hover:text-gray-200'"
                >
                  📋 Lists
                </button>
                <button
                  @click="activeTab = 'files'"
                  class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
                  :class="activeTab === 'files' 
                    ? 'border-blue-500 text-blue-400' 
                    : 'border-transparent text-gray-400 hover:text-gray-200'"
                >
                  📄 Files
                </button>
              </nav>
            </div>

            <!-- Tab Content -->
            <div class="p-4">
              <!-- Drives Tab -->
              <div v-if="activeTab === 'drives'">
                <div v-if="loadingDrives" class="text-center py-8">
                  <div class="animate-spin w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                </div>
                <div v-else-if="drives.length === 0" class="text-center py-8 text-gray-400">
                  No document libraries found
                </div>
                <div v-else class="space-y-3">
                  <div
                    v-for="drive in drives"
                    :key="drive.id"
                    @click="selectDrive(drive)"
                    class="p-4 border border-gray-700 rounded-lg hover:bg-gray-700 cursor-pointer transition-colors"
                    :class="{ 'ring-2 ring-blue-500': selectedDrive?.id === drive.id }"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center space-x-3">
                        <div class="text-2xl">📁</div>
                        <div>
                          <p class="font-medium text-white">{{ drive.name }}</p>
                          <p class="text-sm text-gray-400">{{ drive.drive_type }}</p>
                        </div>
                      </div>
                      <div class="text-right text-sm">
                        <p class="text-gray-400">{{ formatBytes(drive.quota.used) }} used</p>
                        <p class="text-gray-500">of {{ formatBytes(drive.quota.total) }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Lists Tab -->
              <div v-if="activeTab === 'lists'">
                <div v-if="loadingLists" class="text-center py-8">
                  <div class="animate-spin w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                </div>
                <div v-else-if="lists.length === 0" class="text-center py-8 text-gray-400">
                  No lists found
                </div>
                <div v-else class="space-y-3">
                  <div
                    v-for="list in lists"
                    :key="list.id"
                    class="p-4 border border-gray-700 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center space-x-3">
                        <div class="text-2xl">📋</div>
                        <div>
                          <p class="font-medium text-white">{{ list.name }}</p>
                          <p class="text-sm text-gray-400">{{ list.list_info.template || 'Generic List' }}</p>
                        </div>
                      </div>
                      <a
                        :href="list.web_url"
                        target="_blank"
                        class="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        Open →
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Files Tab -->
              <div v-if="activeTab === 'files'">
                <div v-if="!selectedDrive" class="text-center py-8 text-gray-400">
                  Select a document library first
                </div>
                <div v-else-if="loadingFiles" class="text-center py-8">
                  <div class="animate-spin w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                </div>
                <div v-else>
                  <!-- Breadcrumb -->
                  <div class="flex items-center space-x-2 mb-4 text-sm">
                    <button
                      @click="navigateToRoot"
                      class="text-blue-400 hover:text-blue-300"
                    >
                      {{ selectedDrive.name }}
                    </button>
                    <template v-for="(crumb, index) in breadcrumbs" :key="index">
                      <span class="text-gray-500">/</span>
                      <button
                        @click="navigateToBreadcrumb(index)"
                        class="text-blue-400 hover:text-blue-300"
                      >
                        {{ crumb.name }}
                      </button>
                    </template>
                  </div>

                  <!-- Files List -->
                  <div v-if="files.length === 0" class="text-center py-8 text-gray-400">
                    This folder is empty
                  </div>
                  <div v-else class="space-y-2">
                    <div
                      v-for="file in files"
                      :key="file.id"
                      @click="handleFileClick(file)"
                      class="p-3 border border-gray-700 rounded-lg hover:bg-gray-700 cursor-pointer transition-colors flex items-center justify-between"
                    >
                      <div class="flex items-center space-x-3">
                        <div class="text-xl">{{ file.is_folder ? '📁' : getFileIcon(file.name) }}</div>
                        <div>
                          <p class="font-medium text-white">{{ file.name }}</p>
                          <p class="text-xs text-gray-400">
                            <span v-if="!file.is_folder">{{ formatBytes(file.size) }} • </span>
                            {{ formatDate(file.last_modified) }}
                          </p>
                        </div>
                      </div>
                      <button
                        v-if="!file.is_folder"
                        @click.stop="downloadFile(file)"
                        class="px-3 py-1 text-sm bg-green-900/50 text-green-300 rounded hover:bg-green-900 transition-colors"
                      >
                        ⬇️ Download
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// State
const sites = ref([])
const selectedSite = ref(null)
const drives = ref([])
const selectedDrive = ref(null)
const lists = ref([])
const files = ref([])
const breadcrumbs = ref([])

const loading = ref(false)
const loadingDrives = ref(false)
const loadingLists = ref(false)
const loadingFiles = ref(false)

const tokenError = ref(false)

const searchQuery = ref('')
const activeTab = ref('drives')

// Computed
const teamSitesCount = computed(() => 
  sites.value.filter(s => s.site_type === 'Team Site').length
)

const commSitesCount = computed(() => 
  sites.value.filter(s => s.site_type === 'Communication Site').length
)

const otherSitesCount = computed(() => 
  sites.value.filter(s => !['Team Site', 'Communication Site'].includes(s.site_type)).length
)

// Methods
const loadSites = async () => {
  loading.value = true
  tokenError.value = false
  try {
    const response = await axios.get(`${API_BASE}/api/sharepoint/sites`, {
      params: { search: searchQuery.value || '*' }
    })
    if (response.data.success) {
      sites.value = response.data.sites
    }
  } catch (error) {
    console.error('Failed to load sites:', error)
    // Check if error is due to missing/invalid token
    if (error.response && (error.response.status === 500 || error.response.status === 403)) {
      const errorMsg = error.response.data?.error || ''
      if (errorMsg.toLowerCase().includes('access') || errorMsg.toLowerCase().includes('denied')) {
        tokenError.value = true
      }
    }
  } finally {
    loading.value = false
  }
}

const searchSites = () => {
  loadSites()
}

const clearSearch = () => {
  searchQuery.value = ''
  loadSites()
}

const selectSite = async (site) => {
  selectedSite.value = site
  selectedDrive.value = null
  files.value = []
  breadcrumbs.value = []
  activeTab.value = 'drives'
  
  // Load drives and lists
  loadDrives(site.id)
  loadLists(site.id)
}

const loadDrives = async (siteId) => {
  loadingDrives.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/sharepoint/sites/${siteId}/drives`)
    if (response.data.success) {
      drives.value = response.data.drives
    }
  } catch (error) {
    console.error('Failed to load drives:', error)
    drives.value = []
  } finally {
    loadingDrives.value = false
  }
}

const loadLists = async (siteId) => {
  loadingLists.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/sharepoint/sites/${siteId}/lists`)
    if (response.data.success) {
      lists.value = response.data.lists
    }
  } catch (error) {
    console.error('Failed to load lists:', error)
    lists.value = []
  } finally {
    loadingLists.value = false
  }
}

const selectDrive = (drive) => {
  selectedDrive.value = drive
  breadcrumbs.value = []
  activeTab.value = 'files'
  loadDriveFiles(drive.id)
}

const loadDriveFiles = async (driveId, folderId = null) => {
  loadingFiles.value = true
  try {
    let url = `${API_BASE}/api/sharepoint/drives/${driveId}/root`
    if (folderId) {
      url = `${API_BASE}/api/sharepoint/drives/${driveId}/items/${folderId}/children`
    }
    
    const response = await axios.get(url)
    if (response.data.success) {
      files.value = response.data.items
    }
  } catch (error) {
    console.error('Failed to load files:', error)
    files.value = []
  } finally {
    loadingFiles.value = false
  }
}

const handleFileClick = (file) => {
  if (file.is_folder) {
    breadcrumbs.value.push({ id: file.id, name: file.name })
    loadDriveFiles(selectedDrive.value.id, file.id)
  }
}

const navigateToRoot = () => {
  breadcrumbs.value = []
  loadDriveFiles(selectedDrive.value.id)
}

const navigateToBreadcrumb = (index) => {
  const crumb = breadcrumbs.value[index]
  breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
  loadDriveFiles(selectedDrive.value.id, crumb.id)
}

const downloadFile = async (file) => {
  try {
    const response = await axios.get(
      `${API_BASE}/api/sharepoint/drives/${selectedDrive.value.id}/items/${file.id}/content`
    )
    if (response.data.success && response.data.download_url) {
      window.open(response.data.download_url, '_blank')
    }
  } catch (error) {
    console.error('Failed to get download URL:', error)
    alert('Failed to download file')
  }
}

// Helpers
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getSiteIcon = (siteType) => {
  const icons = {
    'Team Site': '👥',
    'Communication Site': '📢',
    'OneDrive': '☁️',
    'Site Collection': '🏢',
    'Site': '📄'
  }
  return icons[siteType] || '📄'
}

const getSiteTypeBadgeClass = (siteType) => {
  const classes = {
    'Team Site': 'bg-green-900/50 text-green-300',
    'Communication Site': 'bg-purple-900/50 text-purple-300',
    'OneDrive': 'bg-blue-900/50 text-blue-300',
    'Site Collection': 'bg-gray-700 text-gray-300',
    'Site': 'bg-gray-700 text-gray-300'
  }
  return classes[siteType] || 'bg-gray-700 text-gray-300'
}

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const icons = {
    'pdf': '📕',
    'doc': '📘', 'docx': '📘',
    'xls': '📗', 'xlsx': '📗',
    'ppt': '📙', 'pptx': '📙',
    'txt': '📄',
    'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
    'mp4': '🎬', 'avi': '🎬', 'mov': '🎬',
    'mp3': '🎵', 'wav': '🎵',
    'zip': '📦', 'rar': '📦', '7z': '📦',
    'exe': '⚙️', 'msi': '⚙️'
  }
  return icons[ext] || '📄'
}

// Lifecycle
onMounted(() => {
  loadSites()
})
</script>
