<template>
  <div :class="['border rounded-lg overflow-hidden', isDark ? 'border-gray-600' : 'border-gray-300']">
    <!-- Toolbar -->
    <div :class="['flex flex-wrap items-center gap-1 p-2 border-b', isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-300']">
      <!-- Text Formatting -->
      <button
        @click="execCommand('bold')"
        :class="toolbarButtonClass"
        title="Bold (Ctrl+B)"
        type="button"
      >
        <strong>B</strong>
      </button>
      <button
        @click="execCommand('italic')"
        :class="toolbarButtonClass"
        title="Italic (Ctrl+I)"
        type="button"
      >
        <em>I</em>
      </button>
      <button
        @click="execCommand('underline')"
        :class="toolbarButtonClass"
        title="Underline (Ctrl+U)"
        type="button"
      >
        <u>U</u>
      </button>
      <button
        @click="execCommand('strikeThrough')"
        :class="toolbarButtonClass"
        title="Strikethrough"
        type="button"
      >
        <s>S</s>
      </button>
      
      <div :class="['w-px h-6 mx-1', isDark ? 'bg-gray-600' : 'bg-gray-300']"></div>
      
      <!-- Font Size -->
      <select
        @change="changeFontSize"
        :class="[
          'px-2 py-1 text-xs rounded border',
          isDark ? 'bg-gray-600 border-gray-500 text-gray-100' : 'bg-white border-gray-300 text-gray-700'
        ]"
        title="Font Size"
      >
        <option value="">Size</option>
        <option value="1">Small</option>
        <option value="3">Normal</option>
        <option value="5">Large</option>
        <option value="7">Huge</option>
      </select>
      
      <!-- Text Color -->
      <div class="relative">
        <input
          type="color"
          @input="changeTextColor"
          :class="['w-8 h-8 cursor-pointer rounded border', isDark ? 'border-gray-500' : 'border-gray-300']"
          title="Text Color"
        />
      </div>
      
      <!-- Background Color -->
      <div class="relative">
        <input
          type="color"
          @input="changeBackColor"
          :class="['w-8 h-8 cursor-pointer rounded border', isDark ? 'border-gray-500' : 'border-gray-300']"
          title="Background Color"
        />
      </div>
      
      <div :class="['w-px h-6 mx-1', isDark ? 'bg-gray-600' : 'bg-gray-300']"></div>
      
      <!-- Alignment -->
      <button
        @click="execCommand('justifyLeft')"
        :class="toolbarButtonClass"
        title="Align Left"
        type="button"
      >
        ⬅
      </button>
      <button
        @click="execCommand('justifyCenter')"
        :class="toolbarButtonClass"
        title="Align Center"
        type="button"
      >
        ↔
      </button>
      <button
        @click="execCommand('justifyRight')"
        :class="toolbarButtonClass"
        title="Align Right"
        type="button"
      >
        ➡
      </button>
      
      <div :class="['w-px h-6 mx-1', isDark ? 'bg-gray-600' : 'bg-gray-300']"></div>
      
      <!-- Lists -->
      <button
        @click="execCommand('insertUnorderedList')"
        :class="toolbarButtonClass"
        title="Bullet List"
        type="button"
      >
        • List
      </button>
      <button
        @click="execCommand('insertOrderedList')"
        :class="toolbarButtonClass"
        title="Numbered List"
        type="button"
      >
        1. List
      </button>
      
      <div :class="['w-px h-6 mx-1', isDark ? 'bg-gray-600' : 'bg-gray-300']"></div>
      
      <!-- Link -->
      <button
        @click="insertLink"
        :class="toolbarButtonClass"
        title="Insert Link"
        type="button"
      >
        🔗
      </button>
      
      <!-- Clear Formatting -->
      <button
        @click="execCommand('removeFormat')"
        :class="toolbarButtonClass"
        title="Clear Formatting"
        type="button"
      >
        ✖
      </button>
      
      <div :class="['w-px h-6 mx-1', isDark ? 'bg-gray-600' : 'bg-gray-300']"></div>
      
      <!-- View Toggle -->
      <button
        @click="toggleView"
        :class="toolbarButtonClass"
        title="Toggle HTML View"
        type="button"
      >
        {{ showHtml ? '📝' : '<>' }}
      </button>
    </div>
    
    <!-- Editor Area -->
    <div
      v-if="!showHtml"
      ref="editor"
      contenteditable="true"
      @input="onInput"
      @paste="onPaste"
      :class="[
        'min-h-[300px] max-h-[500px] overflow-y-auto p-4 focus:outline-none focus:ring-2 focus:ring-blue-500',
        isDark ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'
      ]"
    ></div>
    
    <!-- HTML Source View -->
    <textarea
      v-else
      v-model="htmlContent"
      @input="updateFromHtml"
      :class="[
        'w-full min-h-[300px] max-h-[500px] p-4 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none',
        isDark ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'
      ]"
    ></textarea>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const editor = ref(null)
const showHtml = ref(false)
const htmlContent = ref('')

const toolbarButtonClass = computed(() => [
  'px-2 py-1 text-sm rounded transition-colors',
  props.isDark 
    ? 'bg-gray-600 text-gray-100 hover:bg-gray-500' 
    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
])

// Initialize editor content
onMounted(() => {
  if (editor.value && props.modelValue) {
    editor.value.innerHTML = props.modelValue
  }
  htmlContent.value = props.modelValue
})

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  if (editor.value && editor.value.innerHTML !== newVal) {
    editor.value.innerHTML = newVal
    htmlContent.value = newVal
  }
})

// Execute formatting command
const execCommand = (command, value = null) => {
  // First restore focus to editor
  if (editor.value) {
    editor.value.focus()
  }
  
  // Execute command
  document.execCommand(command, false, value)
  
  // Update content
  onInput()
}

// Change font size
const changeFontSize = (event) => {
  const size = event.target.value
  if (size) {
    execCommand('fontSize', size)
    event.target.value = ''
  }
}

// Change text color
const changeTextColor = (event) => {
  execCommand('foreColor', event.target.value)
}

// Change background color
const changeBackColor = (event) => {
  execCommand('backColor', event.target.value)
}

// Insert link
const insertLink = () => {
  const url = prompt('Enter URL:')
  if (url) {
    execCommand('createLink', url)
  }
}

// Handle input
const onInput = () => {
  if (editor.value) {
    const html = editor.value.innerHTML
    htmlContent.value = html
    emit('update:modelValue', html)
  }
}

// Handle paste - keep formatting
const onPaste = (event) => {
  // Let browser handle paste normally to preserve formatting
  setTimeout(() => {
    onInput()
  }, 10)
}

// Toggle between WYSIWYG and HTML view
const toggleView = async () => {
  if (!showHtml.value) {
    // Switching to HTML view
    htmlContent.value = editor.value?.innerHTML || ''
  } else {
    // Switching back to WYSIWYG
    await nextTick()
    if (editor.value) {
      editor.value.innerHTML = htmlContent.value
    }
  }
  showHtml.value = !showHtml.value
}

// Update from HTML source
const updateFromHtml = () => {
  emit('update:modelValue', htmlContent.value)
}
</script>

<style scoped>
/* Style for editor content */
[contenteditable] {
  outline: none;
}

[contenteditable]:empty:before {
  content: 'Type your message here...';
  color: #9ca3af;
  pointer-events: none;
}

[contenteditable] p {
  margin: 0.5em 0;
}

[contenteditable] ul,
[contenteditable] ol {
  margin: 0.5em 0;
  padding-left: 2em;
}

[contenteditable] li {
  margin: 0.25em 0;
}

[contenteditable] a {
  color: #3b82f6;
  text-decoration: underline;
}

[contenteditable] h1,
[contenteditable] h2,
[contenteditable] h3 {
  margin: 0.75em 0 0.5em 0;
  font-weight: bold;
}

[contenteditable] h1 {
  font-size: 2em;
}

[contenteditable] h2 {
  font-size: 1.5em;
}

[contenteditable] h3 {
  font-size: 1.25em;
}
</style>
