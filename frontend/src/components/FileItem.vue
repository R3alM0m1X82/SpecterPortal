<template>
  <div 
    :class="[
      'rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow cursor-pointer flex items-center justify-between',
      isDark ? 'bg-gray-800' : 'bg-white'
    ]"
    @click="handleClick"
  >
    <div class="flex items-center space-x-4 flex-1 min-w-0">
      <!-- Icon -->
      <div class="text-4xl flex-shrink-0">
        {{ getIcon() }}
      </div>
      
      <!-- Info -->
      <div class="flex-1 min-w-0">
        <h3 :class="['text-base font-semibold truncate', isDark ? 'text-gray-100' : 'text-gray-900']">
          {{ item.name }}
        </h3>
        <div :class="['flex items-center space-x-4 text-sm mt-1', isDark ? 'text-gray-400' : 'text-gray-500']">
          <span v-if="!item.isFolder">{{ formatSize(item.size) }}</span>
          <span v-if="item.isFolder">{{ item.childCount }} item(s)</span>
          <span>{{ formatDate(item.lastModifiedDateTime) }}</span>
        </div>
      </div>
    </div>
    
    <!-- Actions -->
    <div class="flex items-center space-x-2 ml-4" @click.stop>
      <button
        v-if="!item.isFolder"
        @click="$emit('download', item.id)"
        class="btn btn-sm btn-primary"
        title="Download"
      >
        ⬇️
      </button>
      
      <button
        @click="$emit('delete', item.id)"
        class="btn btn-sm btn-danger"
        title="Delete"
      >
        🗑️
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['open', 'download', 'delete'])

const handleClick = () => {
  emit('open', props.item)
}

const getIcon = () => {
  if (props.item.isFolder) {
    return '📁'
  }
  
  const name = props.item.name.toLowerCase()
  const ext = name.split('.').pop()
  
  const iconMap = {
    'pdf': '📄',
    'doc': '📝',
    'docx': '📝',
    'xls': '📊',
    'xlsx': '📊',
    'ppt': '📽️',
    'pptx': '📽️',
    'txt': '📃',
    'jpg': '🖼️',
    'jpeg': '🖼️',
    'png': '🖼️',
    'gif': '🖼️',
    'zip': '📦',
    'rar': '📦',
    'mp4': '🎬',
    'mp3': '🎵',
    'exe': '⚙️',
    'ps1': '⚡',
    'py': '🐍',
    'js': '📜'
  }
  
  return iconMap[ext] || '📄'
}

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  
  return date.toLocaleDateString()
}
</script>

<script>
export default {
  name: 'FileItem'
}
</script>

<style scoped>
.btn {
  @apply px-3 py-1 rounded-lg font-semibold text-xs transition-colors;
}

.btn-sm {
  @apply px-2 py-1 text-xs;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-danger {
  @apply bg-red-600 text-white hover:bg-red-700;
}
</style>
