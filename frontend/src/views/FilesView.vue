<template>
  <div :class="['p-8 w-full', isDark ? 'bg-gray-900' : '']">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 :class="['text-3xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">Files</h1>
        <div :class="['flex items-center space-x-2 mt-2 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
          <button @click="navigateToRoot" :class="isDark ? 'hover:text-blue-400' : 'hover:text-blue-600'">
            🏠 Root
          </button>
          <span v-for="(crumb, index) in breadcrumbs" :key="index" class="flex items-center">
            <span class="mx-2">/</span>
            <button @click="navigateTo(crumb)" :class="isDark ? 'hover:text-blue-400' : 'hover:text-blue-600'">
              {{ crumb.name }}
            </button>
          </span>
        </div>
      </div>
      
      <div class="flex space-x-4">
        <!-- Bulk Download Button (shown when items selected) -->
        <button
          v-if="selectedItems.length > 0"
          @click="downloadSelectedZip"
          :disabled="downloadingZip"
          :class="['btn bg-green-600 text-white hover:bg-green-700 disabled:opacity-50', downloadingZip && 'cursor-not-allowed']"
        >
          {{ downloadingZip ? 'Creating ZIP...' : `📦 Download ${selectedItems.length} File${selectedItems.length > 1 ? 's' : ''} (ZIP)` }}
        </button>
        
        <!-- View Toggle -->
        <div :class="['flex border rounded-lg', isDark ? 'border-gray-600' : 'border-gray-300']">
          <button
            @click="viewMode = 'grid'"
            :class="[
              'px-3 py-2 text-sm font-semibold rounded-l-lg transition-colors',
              viewMode === 'grid'
                ? isDark ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white'
                : isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-white text-gray-700 hover:bg-gray-100'
            ]"
            title="Grid View"
          >
            ⊞ Grid
          </button>
          <button
            @click="viewMode = 'list'"
            :class="[
              'px-3 py-2 text-sm font-semibold rounded-r-lg transition-colors border-l',
              viewMode === 'list'
                ? isDark ? 'bg-blue-600 text-white border-blue-700' : 'bg-blue-600 text-white border-blue-700'
                : isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600 border-gray-600' : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'
            ]"
            title="List View"
          >
            ☰ List
          </button>
        </div>
        
        <button @click="showNewFolder = true" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          📁 New Folder
        </button>
        <button @click="showUpload = true" class="btn btn-primary">
          📤 Upload
        </button>
        <button @click="loadItems(null, true)" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          🔄 Refresh
        </button>
      </div>
    </div>
    
    <!-- Search -->
    <div class="mb-6">
      <div class="flex space-x-2">
        <input
          v-model="searchQuery"
          @keyup.enter="searchFiles"
          type="text"
          placeholder="Search files..."
          :class="[
            'flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            isDark ? 'bg-gray-800 border-gray-600 text-gray-100 placeholder-gray-400' : 'border-gray-300'
          ]"
        />
        <button @click="searchFiles" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          🔍 Search
        </button>
        <button v-if="isSearching" @click="clearSearch" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          ✕ Clear
        </button>
      </div>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p :class="['mt-4', isDark ? 'text-gray-400' : 'text-gray-500']">Loading files...</p>
    </div>
    
    <!-- Error -->
    <div v-else-if="error" :class="['border rounded-lg p-6 text-center', isDark ? 'bg-red-900/30 border-red-800' : 'bg-red-50 border-red-200']">
      <p :class="['font-semibold', isDark ? 'text-red-400' : 'text-red-600']">{{ error }}</p>
      <button @click="loadItems(null, true)" class="mt-4 btn btn-primary">Retry</button>
    </div>
    
    <!-- Empty -->
    <div v-else-if="items.length === 0" :class="['text-center py-12 rounded-lg shadow-md', isDark ? 'bg-gray-800' : 'bg-white']">
      <div class="text-6xl mb-4">📂</div>
      <h2 :class="['text-2xl font-semibold mb-2', isDark ? 'text-gray-100' : 'text-gray-800']">Empty Folder</h2>
      <p :class="isDark ? 'text-gray-400' : 'text-gray-500'">No files or folders here</p>
    </div>
    
    <!-- Grid View -->
    <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 gap-3">
      <FileItem
        v-for="item in items"
        :key="item.id"
        :item="item"
        :isDark="isDark"
        @open="openItem"
        @download="downloadFile"
        @delete="confirmDelete"
      />
    </div>
    
    <!-- List View (Windows Explorer style) -->
    <div v-else-if="viewMode === 'list'" :class="['rounded-lg shadow-md overflow-hidden', isDark ? 'bg-gray-800' : 'bg-white']">
      <table class="w-full">
        <thead :class="[isDark ? 'bg-gray-700' : 'bg-gray-50']">
          <tr>
            <th :class="['py-3 px-4 text-left', isDark ? 'text-gray-300' : 'text-gray-600']">
              <input
                type="checkbox"
                @change="toggleSelectAll"
                :checked="selectedItems.length > 0 && selectedItems.length === items.filter(i => !i.isFolder).length"
                :class="['w-4 h-4 rounded border-gray-300 cursor-pointer', isDark ? 'bg-gray-700 border-gray-600' : '']"
              />
            </th>
            <th :class="['py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider', isDark ? 'text-gray-300' : 'text-gray-600']">
              Name
            </th>
            <th :class="['py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider', isDark ? 'text-gray-300' : 'text-gray-600']">
              Size
            </th>
            <th :class="['py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider', isDark ? 'text-gray-300' : 'text-gray-600']">
              Type
            </th>
            <th :class="['py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider', isDark ? 'text-gray-300' : 'text-gray-600']">
              Modified
            </th>
            <th :class="['py-3 px-4 text-right text-xs font-semibold uppercase tracking-wider', isDark ? 'text-gray-300' : 'text-gray-600']">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in items"
            :key="item.id"
            :class="[
              'border-b hover:bg-opacity-50 transition-colors',
              isDark ? 'border-gray-700 hover:bg-gray-700' : 'border-gray-200 hover:bg-gray-50',
              isSelected(item.id) && !item.isFolder ? (isDark ? 'bg-blue-900/30' : 'bg-blue-50') : ''
            ]"
          >
            <!-- Checkbox Column -->
            <td :class="['py-3 px-4', isDark ? 'text-gray-300' : 'text-gray-700']">
              <input
                v-if="!item.isFolder"
                type="checkbox"
                :checked="isSelected(item.id)"
                @change="toggleSelectItem(item.id)"
                :class="['w-4 h-4 rounded border-gray-300 cursor-pointer', isDark ? 'bg-gray-700 border-gray-600' : '']"
              />
            </td>
            
            <!-- Name Column with Inline Rename -->
            <td :class="['py-3 px-4', isDark ? 'text-gray-300' : 'text-gray-700']">
              <div class="flex items-center space-x-2">
                <span class="text-2xl">{{ item.isFolder ? '📁' : '📄' }}</span>
                
                <!-- Normal Display -->
                <span
                  v-if="renamingItemId !== item.id"
                  @dblclick="startRename(item)"
                  :class="[
                    'font-medium cursor-pointer hover:text-blue-500 transition-colors',
                    item.isFolder && 'cursor-pointer'
                  ]"
                  @click="item.isFolder && openItem(item)"
                >
                  {{ item.name }}
                </span>
                
                <!-- Rename Input -->
                <input
                  v-else
                  v-model="renameValue"
                  @keyup.enter="executeRename(item.id)"
                  @keyup.esc="cancelRename"
                  @blur="executeRename(item.id)"
                  :class="[
                    'px-2 py-1 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'border-gray-300'
                  ]"
                  :disabled="renaming"
                />
              </div>
            </td>
            
            <!-- Size Column -->
            <td :class="['py-3 px-4 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
              {{ item.isFolder ? '-' : formatFileSize(item.size) }}
            </td>
            
            <!-- Type Column -->
            <td :class="['py-3 px-4 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
              {{ item.isFolder ? 'Folder' : (item.mimeType?.split('/')[1] || 'File') }}
            </td>
            
            <!-- Modified Column -->
            <td :class="['py-3 px-4 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
              {{ new Date(item.lastModifiedDateTime).toLocaleDateString() }}
            </td>
            
            <!-- Actions Column -->
            <td class="py-3 px-4 text-right">
              <div class="flex items-center justify-end space-x-2">
                <button
                  @click="startRename(item)"
                  :class="[
                    'px-3 py-1 rounded text-sm font-semibold transition-colors',
                    isDark ? 'bg-yellow-600 text-white hover:bg-yellow-700' : 'bg-yellow-500 text-white hover:bg-yellow-600'
                  ]"
                >
                  ✏️ Rename
                </button>
                <button
                  v-if="!item.isFolder"
                  @click="downloadFile(item.id)"
                  :class="[
                    'px-3 py-1 rounded text-sm font-semibold transition-colors',
                    isDark ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-blue-600 text-white hover:bg-blue-700'
                  ]"
                >
                  📥 Download
                </button>
                <button
                  @click="confirmDelete(item.id)"
                  :class="[
                    'px-3 py-1 rounded text-sm font-semibold transition-colors',
                    isDark ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-red-600 text-white hover:bg-red-700'
                  ]"
                >
                  🗑️ Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div :class="['rounded-lg shadow-xl w-full max-w-md m-4 p-6', isDark ? 'bg-gray-800' : 'bg-white']">
        <div class="mb-6">
          <div class="flex items-center mb-4">
            <div class="text-4xl mr-4">⚠️</div>
            <h2 :class="['text-xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">
              Confirm Delete
            </h2>
          </div>
          <p :class="['mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
            Are you sure you want to delete this {{ itemToDelete?.isFolder ? 'folder' : 'file' }}?
          </p>
          <div :class="['p-3 rounded-lg mt-3', isDark ? 'bg-gray-700' : 'bg-gray-100']">
            <div class="flex items-center space-x-2">
              <span class="text-2xl">{{ itemToDelete?.isFolder ? '📁' : '📄' }}</span>
              <span :class="['font-semibold truncate', isDark ? 'text-gray-100' : 'text-gray-900']">
                {{ itemToDelete?.name }}
              </span>
            </div>
          </div>
          <p :class="['text-sm mt-3', isDark ? 'text-red-400' : 'text-red-600']">
            ⚠️ This action cannot be undone.
          </p>
        </div>
        
        <div class="flex space-x-3">
          <button
            @click="cancelDelete"
            :disabled="deleting"
            :class="[
              'flex-1 py-2 px-4 rounded-lg font-semibold transition-colors',
              isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
              deleting && 'opacity-50 cursor-not-allowed'
            ]"
          >
            Cancel
          </button>
          <button
            @click="executeDelete"
            :disabled="deleting"
            class="flex-1 py-2 px-4 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ deleting ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
        
        <!-- Delete Error -->
        <div v-if="deleteError" :class="['mt-4 p-3 rounded-lg text-sm', isDark ? 'bg-red-900/30 text-red-300' : 'bg-red-50 text-red-700']">
          ❌ {{ deleteError }}
        </div>
      </div>
    </div>
    
    <!-- Upload Modal -->
    <div v-if="showUpload" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div :class="['rounded-lg shadow-xl w-full max-w-md m-4 p-6', isDark ? 'bg-gray-800' : 'bg-white']">
        <div class="flex items-center justify-between mb-6">
          <h2 :class="['text-2xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">Upload File</h2>
          <button @click="closeUpload" :class="['text-2xl', isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-400 hover:text-gray-600']">
            ✕
          </button>
        </div>
        
        <div class="space-y-4">
          <div>
            <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
              Select File:
            </label>
            <input
              type="file"
              @change="handleFileSelect"
              :class="[
                'w-full px-3 py-2 border rounded-lg',
                isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'border-gray-300'
              ]"
            />
          </div>
          
          <div v-if="selectedFile" :class="['p-3 rounded-lg', isDark ? 'bg-gray-700' : 'bg-gray-100']">
            <p :class="['text-sm font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Selected:</p>
            <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">{{ selectedFile.name }}</p>
            <p :class="['text-xs', isDark ? 'text-gray-500' : 'text-gray-500']">{{ formatFileSize(selectedFile.size) }}</p>
          </div>
          
          <div v-if="uploadError" :class="['p-3 rounded-lg text-sm', isDark ? 'bg-red-900/30 text-red-300' : 'bg-red-50 text-red-700']">
            {{ uploadError }}
          </div>
          
          <div v-if="uploadSuccess" :class="['p-3 rounded-lg text-sm', isDark ? 'bg-green-900/30 text-green-300' : 'bg-green-50 text-green-700']">
            ✓ File uploaded successfully!
          </div>
          
          <div class="flex space-x-3">
            <button
              @click="uploadFile"
              :disabled="!selectedFile || uploading"
              class="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ uploading ? 'Uploading...' : 'Upload' }}
            </button>
            <button
              @click="closeUpload"
              :disabled="uploading"
              :class="[
                'flex-1 py-2 px-4 rounded-lg font-semibold',
                isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
                uploading && 'opacity-50 cursor-not-allowed'
              ]"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- New Folder Modal -->
    <div v-if="showNewFolder" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div :class="['rounded-lg shadow-xl w-full max-w-md m-4 p-6', isDark ? 'bg-gray-800' : 'bg-white']">
        <div class="flex items-center justify-between mb-6">
          <h2 :class="['text-2xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">New Folder</h2>
          <button @click="closeNewFolder" :class="['text-2xl', isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-400 hover:text-gray-600']">
            ✕
          </button>
        </div>
        
        <div class="space-y-4">
          <div>
            <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
              Folder Name:
            </label>
            <input
              v-model="newFolderName"
              type="text"
              placeholder="Enter folder name"
              @keyup.enter="createFolder"
              :class="[
                'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400' : 'border-gray-300'
              ]"
            />
          </div>
          
          <div v-if="folderError" :class="['p-3 rounded-lg text-sm', isDark ? 'bg-red-900/30 text-red-300' : 'bg-red-50 text-red-700']">
            {{ folderError }}
          </div>
          
          <div class="flex space-x-3">
            <button
              @click="createFolder"
              :disabled="!newFolderName || creatingFolder"
              class="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ creatingFolder ? 'Creating...' : 'Create' }}
            </button>
            <button
              @click="closeNewFolder"
              :disabled="creatingFolder"
              :class="[
                'flex-1 py-2 px-4 rounded-lg font-semibold',
                isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
                creatingFolder && 'opacity-50 cursor-not-allowed'
              ]"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated, nextTick } from 'vue'
import FileItem from '../components/FileItem.vue'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const items = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const isSearching = ref(false)
const breadcrumbs = ref([])
const currentFolderId = ref(null)

// Cache system (3 minutes TTL)
const CACHE_TTL = 3 * 60 * 1000 // 3 minutes in milliseconds
const filesCache = ref({}) // { 'null': { data: [...], timestamp: ... }, 'folder_id': { ... } }

const showUpload = ref(false)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadError = ref(null)
const uploadSuccess = ref(false)

const showNewFolder = ref(false)
const newFolderName = ref('')
const creatingFolder = ref(false)
const folderError = ref(null)

// Delete modal state
const showDeleteModal = ref(false)
const itemToDelete = ref(null)
const deleting = ref(false)
const deleteError = ref(null)

// View mode toggle
const viewMode = ref('list') // 'grid' or 'list'

// Multi-select state
const selectedItems = ref([])
const downloadingZip = ref(false)

// Rename state
const renamingItemId = ref(null)
const renameValue = ref('')
const renaming = ref(false)

// Cache helper function
const isCacheValid = (cacheEntry) => {
  if (!cacheEntry || !cacheEntry.timestamp) {
    return false
  }
  const age = Date.now() - cacheEntry.timestamp
  return age < CACHE_TTL
}

const loadItems = async (folderId = null, forceRefresh = false) => {
  const targetFolderId = folderId !== null ? folderId : currentFolderId.value
  const cacheKey = targetFolderId || 'root'
  
  // Check cache first (3 min TTL) - skip if forceRefresh
  if (!forceRefresh && filesCache.value[cacheKey] && isCacheValid(filesCache.value[cacheKey])) {
    console.log(`[CACHE] Using cached files for folder: ${cacheKey}`)
    items.value = filesCache.value[cacheKey].data
    return
  }
  
  loading.value = true
  error.value = null
  isSearching.value = false
  selectedItems.value = []
  
  try {
    const url = targetFolderId
      ? `http://localhost:5000/api/files/folder/${targetFolderId}`
      : 'http://localhost:5000/api/files/root'
    
    const response = await fetch(url)
    const data = await response.json()
    
    if (data.success) {
      items.value = data.items || []
      
      // Update cache
      filesCache.value[cacheKey] = {
        data: items.value,
        timestamp: Date.now()
      }
      console.log(`[CACHE] Files cached for folder: ${cacheKey}`)
    } else {
      error.value = data.error
    }
  } catch (err) {
    error.value = 'Failed to load files'
  } finally {
    loading.value = false
  }
}

const openItem = (item) => {
  if (item.isFolder) {
    breadcrumbs.value.push({ id: item.id, name: item.name })
    currentFolderId.value = item.id
    loadItems(item.id)
  }
}

const navigateToRoot = () => {
  breadcrumbs.value = []
  currentFolderId.value = null
  loadItems(null)
}

const navigateTo = (crumb) => {
  const index = breadcrumbs.value.findIndex(c => c.id === crumb.id)
  breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
  currentFolderId.value = crumb.id
  loadItems(crumb.id)
}

const downloadFile = async (itemId) => {
  window.open(`http://localhost:5000/api/files/download/${itemId}`, '_blank')
}

// Delete functions with modal
const confirmDelete = (itemId) => {
  const item = items.value.find(i => i.id === itemId)
  if (item) {
    itemToDelete.value = item
    showDeleteModal.value = true
    deleteError.value = null
  }
}

const cancelDelete = () => {
  if (!deleting.value) {
    showDeleteModal.value = false
    itemToDelete.value = null
    deleteError.value = null
  }
}

const executeDelete = async () => {
  if (!itemToDelete.value) return
  
  deleting.value = true
  deleteError.value = null
  
  try {
    const response = await fetch(`http://localhost:5000/api/files/item/${itemToDelete.value.id}`, {
      method: 'DELETE'
    })
    const data = await response.json()
    
    if (data.success) {
      showDeleteModal.value = false
      itemToDelete.value = null
      await loadItems(null, true) // Force refresh after delete
    } else {
      deleteError.value = data.error || 'Failed to delete item'
    }
  } catch (err) {
    deleteError.value = 'Network error: Failed to delete item'
  } finally {
    deleting.value = false
  }
}

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
  uploadError.value = null
}

const uploadFile = async () => {
  if (!selectedFile.value) return
  
  uploading.value = true
  uploadError.value = null
  uploadSuccess.value = false
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    if (currentFolderId.value) {
      formData.append('folder_id', currentFolderId.value)
    }
    
    const response = await fetch('http://localhost:5000/api/files/upload', {
      method: 'POST',
      body: formData
    })
    const data = await response.json()
    
    if (data.success) {
      uploadSuccess.value = true
      selectedFile.value = null
      setTimeout(() => {
        closeUpload()
        loadItems(null, true) // Force refresh after upload
      }, 1500)
    } else {
      uploadError.value = data.error
    }
  } catch (err) {
    uploadError.value = 'Upload failed'
  } finally {
    uploading.value = false
  }
}

const closeUpload = () => {
  if (!uploading.value) {
    showUpload.value = false
    selectedFile.value = null
    uploadError.value = null
    uploadSuccess.value = false
  }
}

const createFolder = async () => {
  if (!newFolderName.value) return
  
  creatingFolder.value = true
  folderError.value = null
  
  try {
    const response = await fetch('http://localhost:5000/api/files/folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newFolderName.value,
        parent_id: currentFolderId.value
      })
    })
    const data = await response.json()
    
    if (data.success) {
      closeNewFolder()
      loadItems(null, true) // Force refresh after folder creation
    } else {
      folderError.value = data.error
    }
  } catch (err) {
    folderError.value = 'Failed to create folder'
  } finally {
    creatingFolder.value = false
  }
}

const closeNewFolder = () => {
  if (!creatingFolder.value) {
    showNewFolder.value = false
    newFolderName.value = ''
    folderError.value = null
  }
}

const searchFiles = async () => {
  if (!searchQuery.value) return
  
  loading.value = true
  error.value = null
  isSearching.value = true
  
  try {
    const response = await fetch(`http://localhost:5000/api/files/search?q=${encodeURIComponent(searchQuery.value)}`)
    const data = await response.json()
    
    if (data.success) {
      items.value = data.items || []
    } else {
      error.value = data.error
    }
  } catch (err) {
    error.value = 'Search failed'
  } finally {
    loading.value = false
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  isSearching.value = false
  loadItems()
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

// Multi-select functions
const toggleSelectItem = (itemId) => {
  const index = selectedItems.value.indexOf(itemId)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push(itemId)
  }
}

const toggleSelectAll = () => {
  if (selectedItems.value.length === items.value.filter(i => !i.isFolder).length) {
    selectedItems.value = []
  } else {
    selectedItems.value = items.value.filter(i => !i.isFolder).map(i => i.id)
  }
}

const isSelected = (itemId) => {
  return selectedItems.value.includes(itemId)
}

const downloadSelectedZip = async () => {
  if (selectedItems.value.length === 0) return
  
  downloadingZip.value = true
  
  try {
    const response = await fetch('http://localhost:5000/api/files/bulk-download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_ids: selectedItems.value })
    })
    
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'onedrive_files.zip'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      selectedItems.value = []
    } else {
      alert('Failed to download files')
    }
  } catch (err) {
    alert('Download failed: ' + err.message)
  } finally {
    downloadingZip.value = false
  }
}

// Rename functions
const startRename = async (item) => {
  renamingItemId.value = item.id
  renameValue.value = item.name
  
  await nextTick()
  
  const inputs = document.querySelectorAll('table tbody tr input:not([type="checkbox"])')
  if (inputs.length > 0) {
    inputs[0].focus()
    inputs[0].select()
  }
}

const cancelRename = () => {
  renamingItemId.value = null
  renameValue.value = ''
}

const executeRename = async (itemId) => {
  if (!renameValue.value.trim() || renaming.value) return
  
  const newName = renameValue.value.trim()
  
  if (newName === items.value.find(i => i.id === itemId)?.name) {
    cancelRename()
    return
  }
  
  renaming.value = true
  
  try {
    console.log('Renaming item:', itemId, 'to:', newName)
    
    const response = await fetch(`http://localhost:5000/api/files/item/${itemId}/rename`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName })
    })
    
    console.log('Rename response status:', response.status)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    console.log('Rename response data:', data)
    
    if (data.success) {
      renamingItemId.value = null
      renameValue.value = ''
      await loadItems(null, true) // Force refresh after rename
    } else {
      alert('Rename failed: ' + (data.error || 'Unknown error'))
      renamingItemId.value = null
    }
  } catch (err) {
    console.error('Rename error:', err)
    alert('Rename failed: ' + err.message)
    renamingItemId.value = null
  } finally {
    renaming.value = false
  }
}

onMounted(() => {
  loadItems()
})

// Called when component is reactivated from keep-alive cache
onActivated(() => {
  // loadItems() will use cache if valid (< 3 min), or fetch fresh data if expired
  loadItems()
})
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-lg font-semibold transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-secondary {
  @apply bg-gray-600 text-white hover:bg-gray-700;
}

.btn-secondary-dark {
  @apply bg-gray-700 text-gray-300 hover:bg-gray-600;
}
</style>
