<template>
  <div class="w-full">
    <div
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
      @keydown="onKeyDown"
      :class="dropzoneClass"
      class="border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-500"
      @click="openFileDialog"
      role="button"
      tabindex="0"
      aria-label="文件上传拖拽区域"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="accept"
        :multiple="multiple"
        class="hidden"
        @change="onFileChange"
        aria-label="选择上传文件"
      />

      <Upload class="mx-auto h-12 w-12 text-gray-400" />
      <p class="mt-2 text-sm text-gray-600">
        <span class="font-semibold text-primary-600">点击上传</span> 或拖拽文件到这里
      </p>
      <p class="mt-1 text-xs text-gray-500">{{ acceptHint }}</p>
      <p v-if="maxSize" class="text-xs text-gray-400">最大文件大小: {{ formatFileSize(maxSize) }}</p>
    </div>

    <div v-if="files.length > 0" class="mt-4 space-y-2">
      <div
        v-for="(file, index) in files"
        :key="index"
        class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
      >
        <div class="flex items-center flex-1 min-w-0">
          <FileText class="w-5 h-5 text-gray-400 flex-shrink-0" />
          <div class="ml-3 flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ file.name }}</p>
            <p class="text-xs text-gray-500">{{ formatFileSize(file.size) }}</p>
          </div>
        </div>
        <button
          @click="removeFile(index)"
          class="ml-2 p-1 text-gray-400 hover:text-red-600 transition-colors"
          :aria-label="`移除文件 ${file.name}`"
        >
          <X class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { FileText, Upload, X } from 'lucide-vue-next'

import { formatFileSize } from '@/utils/format'

const props = withDefaults(defineProps<{
  accept?: string
  multiple?: boolean
  maxSize?: number
  acceptHint?: string
}>(), {
  accept: '*',
  multiple: true,
  acceptHint: '',
})

const emit = defineEmits<{
  'update:files': [files: File[]]
}>()

const fileInput = ref<HTMLInputElement>()
const files = ref<File[]>([])
const isDragging = ref(false)

const dropzoneClass = computed(() => {
  if (isDragging.value) {
    return 'border-primary-500 bg-primary-50'
  }
  return 'border-gray-300 hover:border-primary-400'
})

function openFileDialog() {
  fileInput.value?.click()
}

function onKeyDown(event: KeyboardEvent) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    openFileDialog()
  }
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files) {
    addFiles(Array.from(target.files))
  }
}

function onDragOver() {
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files) {
    addFiles(Array.from(event.dataTransfer.files))
  }
}

function addFiles(newFiles: File[]) {
  if (props.maxSize) {
    newFiles = newFiles.filter((file) => file.size <= props.maxSize!)
  }

  if (props.multiple) {
    files.value = [...files.value, ...newFiles]
  } else {
    files.value = newFiles.slice(0, 1)
  }

  emit('update:files', files.value)
}

function removeFile(index: number) {
  files.value.splice(index, 1)
  emit('update:files', files.value)
}

defineExpose({
  clearFiles: () => {
    files.value = []
    emit('update:files', files.value)
  },
})
</script>
