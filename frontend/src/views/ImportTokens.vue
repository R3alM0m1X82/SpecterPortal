<template>
  <div class="p-8 max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold text-gray-800 mb-8">Import Tokens</h1>
    
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
      <h2 class="text-lg font-semibold text-blue-800 mb-2">📄 How to Import</h2>
      <ol class="list-decimal list-inside space-y-2 text-blue-700">
        <li>Extract tokens using <strong>SpecterBroker</strong> tool</li>
        <li>Locate the generated <code class="bg-blue-100 px-2 py-1 rounded">tokens_output.json</code> file</li>
        <li>Paste the JSON content below or upload the file</li>
        <li>Click "Import Tokens" to add them to the database</li>
      </ol>
    </div>
    
    <div class="bg-white rounded-lg shadow-md p-6">
      <!-- File Upload -->
      <div class="mb-6">
        <label class="block text-sm font-semibold text-gray-700 mb-2">
          Upload JSON File
        </label>
        <div class="relative">
          <input
            type="file"
            accept=".json"
            multiple
            @change="handleFileUpload"
            ref="fileInput"
            class="hidden"
          />
          <button
            @click="$refs.fileInput.click()"
            class="w-full px-4 py-2 bg-blue-50 text-blue-700 rounded-lg border-2 border-blue-200 hover:bg-blue-100 transition-colors font-semibold text-sm flex items-center justify-center gap-2"
          >
            📁 Choose File
          </button>
          <p v-if="selectedFileName" class="text-xs text-gray-500 mt-2">Selected: {{ selectedFileName }}</p>
        </div>
      </div>
      
      <!-- OR Divider -->
      <div class="flex items-center my-6">
        <div class="flex-1 border-t border-gray-300"></div>
        <span class="px-4 text-gray-500 text-sm">OR</span>
        <div class="flex-1 border-t border-gray-300"></div>
      </div>
      
      <!-- Paste JSON -->
      <div class="mb-6">
        <label class="block text-sm font-semibold text-gray-700 mb-2">
          Paste JSON Content
        </label>
        <textarea
          v-model="jsonInput"
          rows="12"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
          placeholder='{"tokens": [...], "target": "PC-NAME", "extraction_time": "..."}'
        ></textarea>
      </div>
      
      <!-- Clear Before Import Option -->
      <div class="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <label class="flex items-center cursor-pointer">
          <input
            type="checkbox"
            v-model="clearBeforeImport"
            class="w-5 h-5 text-red-600 rounded focus:ring-2 focus:ring-red-500"
          />
          <span class="ml-3">
            <span class="font-semibold text-gray-800">Clear all existing tokens before import</span>
            <p class="text-sm text-gray-600 mt-1">
              ⚠️ This will delete ALL current tokens before importing new ones. Use this to avoid duplicates.
            </p>
          </span>
        </label>
      </div>
      
      <!-- Preview -->
      <div v-if="parsedData" class="mb-6 p-4 bg-gray-50 rounded-lg">
        <h3 class="text-sm font-semibold text-gray-700 mb-2">Preview:</h3>
        <div class="text-sm text-gray-600 space-y-1">
          <p><span class="font-semibold">Target:</span> {{ parsedData.target }}</p>
          <p><span class="font-semibold">Tokens:</span> {{ parsedData.tokens?.length || 0 }}</p>
          <p><span class="font-semibold">Extraction Time:</span> {{ parsedData.extraction_time }}</p>
        </div>
      </div>
      
      <!-- Error Message -->
      <div v-if="error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-red-700 text-sm">{{ error }}</p>
      </div>
      
      <!-- Success Message -->
      <div v-if="success" class="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <p class="text-green-700 text-sm">{{ success }}</p>
      </div>
      
      <!-- Actions -->
      <div class="flex space-x-4">
        <button
          @click="importTokens"
          :disabled="!jsonInput || importing"
          class="btn btn-primary flex-1"
          :class="{ 'opacity-50 cursor-not-allowed': !jsonInput || importing }"
        >
          {{ importing ? 'Importing...' : 'Import Tokens' }}
        </button>
        
        <button
          @click="clearForm"
          class="btn btn-secondary"
        >
          Clear
        </button>
        
        <router-link
          to="/tokens"
          class="btn btn-secondary"
        >
          Cancel
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const jsonInput = ref('')
const parsedData = ref(null)
const error = ref(null)
const success = ref(null)
const importing = ref(false)
const filename = ref('unknown.json')
const selectedFileName = ref('')
const clearBeforeImport = ref(false)

watch(jsonInput, (newValue) => {
  error.value = null
  parsedData.value = null
  
  if (!newValue.trim()) return
  
  try {
    const data = JSON.parse(newValue)
    parsedData.value = data
  } catch (e) {
    error.value = 'Invalid JSON format'
  }
})

const handleFileUpload = async (event) => {
  const files = Array.from(event.target.files)
  if (!files || files.length === 0) return
  
  if (files.length === 1) {
    // Single file - comportamento originale
    const file = files[0]
    filename.value = file.name
    selectedFileName.value = file.name
    
    const reader = new FileReader()
    reader.onload = (e) => {
      jsonInput.value = e.target.result
    }
    reader.readAsText(file)
  } else {
    // Multiple files - merge JSONs
    filename.value = `${files.length} files selected`
    selectedFileName.value = `${files.length} files selected`
    let allTokens = []
    let lastTarget = ''
    let lastExtractionTime = ''
    
    for (const file of files) {
      try {
        const text = await new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = (e) => resolve(e.target.result)
          reader.onerror = reject
          reader.readAsText(file)
        })
        
        const data = JSON.parse(text)
        if (data.tokens && Array.isArray(data.tokens)) {
          allTokens = allTokens.concat(data.tokens)
          lastTarget = data.target || lastTarget
          lastExtractionTime = data.extraction_time || lastExtractionTime
        }
      } catch (err) {
        console.error(`Failed to read ${file.name}:`, err)
      }
    }
    
    // Merge all tokens into single JSON
    const mergedJson = {
      tokens: allTokens,
      target: lastTarget,
      extraction_time: lastExtractionTime
    }
    
    jsonInput.value = JSON.stringify(mergedJson, null, 2)
  }
}

const importTokens = async () => {
  if (!parsedData.value) {
    error.value = 'Please provide valid JSON data'
    return
  }
  
  importing.value = true
  error.value = null
  success.value = null
  
  try {
    // Clear all tokens if option selected
    if (clearBeforeImport.value) {
      const tokensResponse = await fetch('http://localhost:5000/api/tokens')
      const tokensData = await tokensResponse.json()
      
      if (tokensData.success) {
        for (const token of tokensData.tokens) {
          await fetch(`http://localhost:5000/api/tokens/${token.id}`, {
            method: 'DELETE'
          })
        }
      }
    }
    
    // Import new tokens
    const response = await fetch('http://localhost:5000/api/tokens/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data: parsedData.value,
        filename: filename.value
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      success.value = data.message
      setTimeout(() => {
        router.push('/tokens')
      }, 2000)
    } else {
      error.value = data.message || 'Import failed'
    }
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to import tokens'
  } finally {
    importing.value = false
  }
}

const clearForm = () => {
  jsonInput.value = ''
  parsedData.value = null
  error.value = null
  success.value = null
  filename.value = 'unknown.json'
  clearBeforeImport.value = false
}
</script>

<style scoped>
.btn {
  @apply px-6 py-3 rounded-lg font-semibold transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-secondary {
  @apply bg-gray-200 text-gray-700 hover:bg-gray-300;
}
</style>
