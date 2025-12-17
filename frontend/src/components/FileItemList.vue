<template>
  <tr 
    :class="[
      'border-b hover:bg-opacity-50 cursor-pointer transition-colors',
      isDark ? 'border-gray-700 hover:bg-gray-700' : 'border-gray-200 hover:bg-gray-50'
    ]"
    @click="handleClick"
  >
    <!-- Icon + Name -->
    <td :class="['py-3 px-4', isDark ? 'text-gray-100' : 'text-gray-900']">
      <div class="flex items-center space-x-3">
        <span class="text-xl flex-shrink-0">{{ getIcon() }}</span>
        <span class="font-medium truncate">{{ item.name }}</span>
      </div>
    </td>
    
    <!-- Size -->
    <td :class="['py-3 px-4 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
      <span v-if="!item.isFolder">{{ formatSize(item.size) }}</span>
      <span v-else>—</span>
    </td>
    
    <!-- Type -->
    <td :class="['py-3 px-4 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
      <span v-if="item.isFolder">Folder</span>
      <span v-else>{{ getFileType() }}</span>
    </td>
    
    <!-- Modified -->
    <td :class="['py-3 px-4 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
      {{ formatDate(item.lastModifiedDateTime) }}
    </td>
    
    <!-- Actions -->
    <td class="py-3 px-4 text-right" @click.stop>
      <div class="flex items-center justify-end space-x-2">
        <button
          v-if="!item.isFolder"
          @click="$emit('download', item.id)"
          :class="[
            'px-2 py-1 rounded text-xs font-semibold transition-colors',
            isDark ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-blue-600 text-white hover:bg-blue-700'
          ]"
          title="Download"
        >
          ⬇️ Download
        </button>
        
        <button
          @click="$emit('delete', item.id)"
          :class="[
            'px-2 py-1 rounded text-xs font-semibold transition-colors',
            isDark ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-red-600 text-white hover:bg-red-700'
          ]"
          title="Delete"
        >
          🗑️ Delete
        </button>
      </div>
    </td>
  </tr>
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

const getFileType = () => {
  const name = props.item.name.toLowerCase()
  const ext = name.split('.').pop()
  
  const typeMap = {
    'pdf': 'PDF Document',
    'doc': 'Word Document',
    'docx': 'Word Document',
    'xls': 'Excel Spreadsheet',
    'xlsx': 'Excel Spreadsheet',
    'ppt': 'PowerPoint',
    'pptx': 'PowerPoint',
    'txt': 'Text File',
    'jpg': 'JPEG Image',
    'jpeg': 'JPEG Image',
    'png': 'PNG Image',
    'gif': 'GIF Image',
    'zip': 'ZIP Archive',
    'rar': 'RAR Archive',
    'mp4': 'Video',
    'mp3': 'Audio',
    'exe': 'Executable',
    'ps1': 'PowerShell Script',
    'py': 'Python Script',
    'js': 'JavaScript File'
  }
  
  return typeMap[ext] || ext.toUpperCase() + ' File'
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
  
  if (diffDays === 0) return 'Today ' + date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  if (diffDays === 1) return 'Yesterday ' + date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  if (diffDays < 7) return `${diffDays} days ago`
  
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<script>
export default {
  name: 'FileItemList'
}
</script>
