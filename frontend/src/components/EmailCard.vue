<template>
  <div 
    @click="$emit('open', email.id)"
    :class="[
      'rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow cursor-pointer',
      isDark 
        ? (email.isRead ? 'bg-gray-800' : 'bg-gray-700') 
        : (email.isRead ? 'bg-white' : 'bg-blue-50')
    ]"
  >
    <div class="flex items-start justify-between">
      <div class="flex-1 min-w-0">
        <!-- From -->
        <div class="flex items-center space-x-2 mb-2">
          <span :class="['font-semibold', isDark ? 'text-gray-100' : 'text-gray-800']">
            {{ email.fromName }}
          </span>
          <span :class="['text-xs', isDark ? 'text-gray-400' : 'text-gray-500']">
            {{ email.from }}
          </span>
          <span v-if="!email.isRead" class="w-2 h-2 bg-blue-500 rounded-full"></span>
        </div>
        
        <!-- Subject -->
        <h3 :class="['text-base font-semibold mb-1 truncate', isDark ? 'text-gray-100' : 'text-gray-900']">
          {{ email.subject }}
        </h3>
        
        <!-- Preview -->
        <p :class="['text-sm truncate', isDark ? 'text-gray-400' : 'text-gray-600']">
          {{ email.bodyPreview }}
        </p>
      </div>
      
      <!-- Right side -->
      <div class="flex flex-col items-end ml-4 space-y-1">
        <span :class="['text-xs', isDark ? 'text-gray-400' : 'text-gray-500']">
          {{ formatDate(email.receivedDateTime) }}
        </span>
        <div class="flex space-x-1">
          <span v-if="email.hasAttachments" :class="isDark ? 'text-gray-500' : 'text-gray-400'" title="Has attachments">
            📎
          </span>
          <span v-if="email.importance === 'high'" class="text-red-500" title="High importance">
            ❗
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  email: {
    type: Object,
    required: true
  },
  isDark: {
    type: Boolean,
    default: false
  }
})

defineEmits(['open'])

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  
  return date.toLocaleDateString()
}
</script>
