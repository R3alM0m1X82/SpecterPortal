<template>
  <div :class="['p-8 w-full', isDark ? 'bg-gray-900' : '']">
    <button @click="$router.back()" :class="['mb-6 flex items-center', isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800']">
      ← Back to Inbox
    </button>
    
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p :class="['mt-4', isDark ? 'text-gray-400' : 'text-gray-500']">Loading email...</p>
    </div>
    
    <div v-else-if="error" :class="['border rounded-lg p-6 text-center', isDark ? 'bg-red-900/30 border-red-800' : 'bg-red-50 border-red-200']">
      <p :class="['font-semibold', isDark ? 'text-red-400' : 'text-red-600']">{{ error }}</p>
    </div>
    
    <div v-else-if="email" :class="['rounded-lg shadow-lg', isDark ? 'bg-gray-800' : 'bg-white']">
      <div :class="['p-6 border-b', isDark ? 'border-gray-700' : '']">
        <div class="flex items-start justify-between mb-4">
          <h1 :class="['text-2xl font-bold flex-1', isDark ? 'text-gray-100' : 'text-gray-900']">
            {{ email.subject }}
          </h1>
          
          <!-- Action Buttons -->
          <div class="flex space-x-2 ml-4">
            <button
              @click="handleReply"
              :class="['btn btn-secondary', isDark ? 'btn-secondary-dark' : '']"
              title="Reply"
            >
              ↩️ Reply
            </button>
            <button
              @click="handleForward"
              :class="['btn btn-secondary', isDark ? 'btn-secondary-dark' : '']"
              title="Forward"
            >
              ➡️ Forward
            </button>
          </div>
        </div>
        
        <div class="space-y-2 text-sm">
          <div class="flex items-center">
            <span :class="['font-semibold w-20', isDark ? 'text-gray-300' : 'text-gray-700']">From:</span>
            <span :class="isDark ? 'text-gray-100' : 'text-gray-900'">{{ email.fromName }}</span>
            <span :class="['ml-2', isDark ? 'text-gray-400' : 'text-gray-500']">&lt;{{ email.from }}&gt;</span>
          </div>
          
          <div class="flex items-center">
            <span :class="['font-semibold w-20', isDark ? 'text-gray-300' : 'text-gray-700']">To:</span>
            <span :class="isDark ? 'text-gray-100' : 'text-gray-900'">{{ email.toRecipients?.join(', ') }}</span>
          </div>
          
          <div v-if="email.ccRecipients?.length" class="flex items-center">
            <span :class="['font-semibold w-20', isDark ? 'text-gray-300' : 'text-gray-700']">Cc:</span>
            <span :class="isDark ? 'text-gray-100' : 'text-gray-900'">{{ email.ccRecipients.join(', ') }}</span>
          </div>
          
          <div class="flex items-center">
            <span :class="['font-semibold w-20', isDark ? 'text-gray-300' : 'text-gray-700']">Date:</span>
            <span :class="isDark ? 'text-gray-100' : 'text-gray-900'">{{ formatDate(email.receivedDateTime) }}</span>
          </div>
          
          <div v-if="email.hasAttachments" :class="['flex items-center', isDark ? 'text-gray-400' : 'text-gray-600']">
            <span class="font-semibold w-20">📎</span>
            <span>{{ attachments.length }} attachment(s)</span>
          </div>
        </div>
      </div>
      
      <!-- Attachments -->
      <div v-if="attachments.length > 0" :class="['p-6 border-b', isDark ? 'bg-gray-700/50 border-gray-700' : 'bg-gray-50']">
        <h3 :class="['font-semibold mb-3', isDark ? 'text-gray-200' : 'text-gray-800']">Attachments:</h3>
        <div class="space-y-2">
          <div v-for="att in attachments" :key="att.id" 
               :class="['flex items-center justify-between p-3 rounded border', isDark ? 'bg-gray-800 border-gray-600 hover:bg-gray-700' : 'bg-white hover:bg-gray-50']">
            <div class="flex items-center space-x-3">
              <span class="text-2xl">📎</span>
              <div>
                <p :class="['font-semibold', isDark ? 'text-gray-200' : 'text-gray-800']">{{ att.name }}</p>
                <p :class="['text-xs', isDark ? 'text-gray-400' : 'text-gray-500']">{{ formatSize(att.size) }}</p>
              </div>
            </div>
            <button @click="downloadAttachment(att.id, att.name)" 
                    class="btn btn-primary btn-sm">
              Download
            </button>
          </div>
        </div>
      </div>
      
      <!-- Body -->
      <div :class="['p-6', isDark ? 'email-content-wrapper-dark' : 'email-content-wrapper']">
        <div 
          v-if="email.bodyType && email.bodyType.toLowerCase() === 'html'"
          v-html="email.body"
          :class="isDark ? 'email-html-body-dark' : 'email-html-body'"
        ></div>
        <div v-else :class="['whitespace-pre-wrap', isDark ? 'text-gray-200' : 'text-gray-800']">{{ email.body }}</div>
      </div>
    </div>
    
    <!-- Compose Modal for Reply/Forward -->
    <div v-if="showCompose" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div :class="['rounded-lg shadow-xl w-full max-w-4xl max-h-[95vh] overflow-y-auto', isDark ? 'bg-gray-800' : 'bg-white']">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 :class="['text-2xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">
              {{ composeMode === 'reply' ? '↩️ Reply' : '➡️ Forward' }}
            </h2>
            <button @click="closeCompose" :class="['text-2xl', isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-400 hover:text-gray-600']">
              ✕
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">To:</label>
              <input
                v-model="composeData.to"
                type="email"
                placeholder="recipient@example.com"
                :class="[
                  'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400' : 'border-gray-300'
                ]"
              />
            </div>

            <div>
              <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">Subject:</label>
              <input
                v-model="composeData.subject"
                type="text"
                placeholder="Email subject"
                :class="[
                  'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400' : 'border-gray-300'
                ]"
              />
            </div>

            <div>
              <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">Body:</label>
              <HTMLEditor
                v-model="composeData.body"
                :isDark="isDark"
              />
            </div>

            <div v-if="sendError" :class="['p-3 border rounded text-sm', isDark ? 'bg-red-900/30 border-red-800 text-red-400' : 'bg-red-50 border-red-200 text-red-600']">
              {{ sendError }}
            </div>

            <div v-if="sendSuccess" :class="['p-3 border rounded text-sm', isDark ? 'bg-green-900/30 border-green-800 text-green-400' : 'bg-green-50 border-green-200 text-green-600']">
              ✓ Email sent successfully!
            </div>

            <div class="flex space-x-3 pt-4">
              <button
                @click="sendEmail"
                :disabled="sending"
                class="btn btn-primary flex-1"
              >
                {{ sending ? 'Sending...' : '📤 Send' }}
              </button>
              <button @click="closeCompose" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import HTMLEditor from '../components/HTMLEditor.vue'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()

const email = ref(null)
const attachments = ref([])
const loading = ref(false)
const error = ref(null)

// Compose modal state
const showCompose = ref(false)
const composeMode = ref('reply') // 'reply' or 'forward'
const sending = ref(false)
const sendError = ref(null)
const sendSuccess = ref(false)
const composeData = ref({
  to: '',
  subject: '',
  body: ''
})

const loadEmail = async () => {
  loading.value = true
  error.value = null
  
  try {
    const emailId = route.params.id
    const response = await fetch(`http://localhost:5000/api/emails/${emailId}`)
    const data = await response.json()
    
    console.log('API Response:', data)
    console.log('Body Type:', data.message?.bodyType)
    console.log('Body:', data.message?.body)

    if (data.success) {
      email.value = data.message
      if (data.message.hasAttachments) {
        await loadAttachments(emailId)
      }
    } else {
      error.value = data.error
    }
  } catch (err) {
    error.value = 'Failed to load email'
  } finally {
    loading.value = false
  }
}

const loadAttachments = async (emailId) => {
  try {
    const response = await fetch(`http://localhost:5000/api/emails/${emailId}/attachments`)
    const data = await response.json()
    if (data.success) {
      attachments.value = data.attachments
    }
  } catch (err) {
    console.error('Failed to load attachments:', err)
  }
}

const downloadAttachment = async (attachmentId, filename) => {
  try {
    const emailId = route.params.id
    const response = await fetch(
      `http://localhost:5000/api/emails/${emailId}/attachments/${attachmentId}/download`
    )
    
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    }
  } catch (err) {
    console.error('Download failed:', err)
    alert('Failed to download attachment')
  }
}

// Reply handler
const handleReply = () => {
  if (!email.value) return
  
  composeMode.value = 'reply'
  
  // Pre-populate To with sender
  composeData.value.to = email.value.from
  
  // Add RE: prefix if not already present
  let subject = email.value.subject || '(No subject)'
  if (!subject.toLowerCase().startsWith('re:')) {
    subject = 'RE: ' + subject
  }
  composeData.value.subject = subject
  
  // Quote original message
  const originalDate = formatDate(email.value.receivedDateTime)
  const originalFrom = `${email.value.fromName} <${email.value.from}>`
  
  let quotedBody = `<br><br><hr><p><strong>On ${originalDate}, ${originalFrom} wrote:</strong></p><blockquote style="margin-left: 20px; padding-left: 10px; border-left: 3px solid #ccc;">${email.value.body}</blockquote>`
  
  composeData.value.body = quotedBody
  
  showCompose.value = true
}

// Forward handler
const handleForward = () => {
  if (!email.value) return
  
  composeMode.value = 'forward'
  
  // To field is empty (user must enter)
  composeData.value.to = ''
  
  // Add FW: prefix if not already present
  let subject = email.value.subject || '(No subject)'
  if (!subject.toLowerCase().startsWith('fw:') && !subject.toLowerCase().startsWith('fwd:')) {
    subject = 'FW: ' + subject
  }
  composeData.value.subject = subject
  
  // Format forwarded message
  const originalDate = formatDate(email.value.receivedDateTime)
  const originalFrom = `${email.value.fromName} <${email.value.from}>`
  const originalTo = email.value.toRecipients?.join(', ') || ''
  
  let forwardedBody = `<br><br><hr><p><strong>---------- Forwarded message ----------</strong></p>`
  forwardedBody += `<p><strong>From:</strong> ${originalFrom}<br>`
  forwardedBody += `<strong>Date:</strong> ${originalDate}<br>`
  forwardedBody += `<strong>Subject:</strong> ${email.value.subject}<br>`
  forwardedBody += `<strong>To:</strong> ${originalTo}</p><br>`
  forwardedBody += `${email.value.body}`
  
  composeData.value.body = forwardedBody
  
  showCompose.value = true
}

const sendEmail = async () => {
  if (!composeData.value.to || !composeData.value.subject || !composeData.value.body) {
    sendError.value = 'Please fill all fields'
    return
  }

  sending.value = true
  sendError.value = null
  sendSuccess.value = false

  try {
    const response = await fetch('http://localhost:5000/api/emails/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(composeData.value)
    })

    const data = await response.json()

    if (data.success) {
      sendSuccess.value = true
      setTimeout(() => {
        closeCompose()
      }, 2000)
    } else {
      sendError.value = data.error
    }
  } catch (err) {
    sendError.value = 'Failed to send email'
  } finally {
    sending.value = false
  }
}

const closeCompose = () => {
  if (!sending.value) {
    showCompose.value = false
    composeData.value = { to: '', subject: '', body: '' }
    sendError.value = null
    sendSuccess.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString()
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(() => {
  loadEmail()
})
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-lg font-semibold text-sm transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply bg-gray-600 text-white hover:bg-gray-700;
}

.btn-secondary-dark {
  @apply bg-gray-700 text-gray-300 hover:bg-gray-600;
}

.btn-sm {
  @apply px-3 py-1 text-xs;
}

.email-content-wrapper {
  background: #ffffff;
}

.email-content-wrapper-dark {
  background: #1f2937;
}

.email-html-body {
  line-height: 1.6;
  color: #333;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.email-html-body-dark {
  line-height: 1.6;
  color: #e5e7eb;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* Reset email styles */
.email-html-body :deep(p),
.email-html-body-dark :deep(p) {
  margin: 0.5em 0;
}

.email-html-body :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}

.email-html-body-dark :deep(a) {
  color: #60a5fa;
  text-decoration: underline;
}

.email-html-body :deep(img),
.email-html-body-dark :deep(img) {
  max-width: 100%;
  height: auto;
}

.email-html-body :deep(table),
.email-html-body-dark :deep(table) {
  border-collapse: collapse;
  width: 100%;
}
</style>
