<template>
  <div>
    <div class="mb-4 lg:mb-6">
      <h1 class="page-title">提交任务</h1>
      <p class="mt-1 page-subtitle">保持 Markio 轻量能力：docling + MinerU</p>
    </div>

    <div class="max-w-5xl mx-auto">
      <div class="card mb-6">
        <h2 class="section-title mb-4">上传文件</h2>
        <FileUploader
          ref="fileUploader"
          :multiple="false"
          accept=".pdf,.doc,.docx,.ppt,.pptx,.xlsx,.html,.htm,.epub,.png,.jpg,.jpeg"
          accept-hint="支持常见文档与图片文件"
          @update:files="onFilesChange"
        />
      </div>

      <div class="card mb-6">
        <h2 class="section-title mb-4">处理参数</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6">
          <div v-if="isPdfFile">
            <label class="block text-sm font-medium text-tertiary mb-2">parse_method</label>
            <select v-model="form.parse_method" class="w-full px-3 py-2 border border-default rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option value="auto">auto</option>
              <option value="txt">txt</option>
              <option value="ocr">ocr</option>
            </select>
          </div>

          <div v-if="isPdfFile">
            <label class="block text-sm font-medium text-tertiary mb-2">lang</label>
            <select v-model="form.lang" class="w-full px-3 py-2 border border-default rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option value="ch">ch</option>
              <option value="en">en</option>
              <option value="japan">japan</option>
              <option value="korean">korean</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-tertiary mb-2">priority</label>
            <input
              v-model.number="form.priority"
              type="number"
              min="-10"
              max="100"
              class="w-full px-3 py-2 border border-default rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-tertiary mb-2">output_dir</label>
            <input
              v-model="form.output_dir"
              type="text"
              class="w-full px-3 py-2 border border-default rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div v-if="isPdfFile">
            <label class="block text-sm font-medium text-tertiary mb-2">start_page</label>
            <input
              v-model.number="form.start_page"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-default rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div v-if="isPdfFile">
            <label class="block text-sm font-medium text-tertiary mb-2">end_page（留空表示最后一页）</label>
            <input
              v-model="form.end_page"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-default rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
        <p v-if="!isPdfFile" class="mt-3 text-sm text-secondary">
          当前文件不是 PDF，已自动隐藏 PDF 专属参数（parse_method/lang/start_page/end_page/save_middle_content）。
        </p>
        <p v-if="pageRangeError" class="mt-3 text-sm text-danger break-words" dir="auto">{{ pageRangeError }}</p>
        <p v-if="fileTypeError" class="mt-2 text-sm text-danger break-words" dir="auto">{{ fileTypeError }}</p>

        <div class="mt-4 space-y-2">
          <label class="flex items-center">
            <input v-model="form.save_parsed_content" type="checkbox" class="w-4 h-4 text-primary-600 border-default rounded" />
            <span class="ml-2 text-sm text-tertiary">保存解析内容</span>
          </label>
          <label v-if="isPdfFile" class="flex items-center">
            <input v-model="form.save_middle_content" type="checkbox" class="w-4 h-4 text-primary-600 border-default rounded" />
            <span class="ml-2 text-sm text-tertiary">保存中间结果</span>
          </label>
        </div>

        <div class="mt-6 flex gap-3">
          <button
            @click="submit"
            :disabled="taskStore.submitting || !canSubmit"
            class="btn btn-primary flex items-center"
          >
            <Upload class="w-4 h-4 mr-2" />
            {{ taskStore.submitting ? '提交中...' : '提交任务' }}
          </button>
          <router-link to="/tasks" class="btn btn-secondary">查看任务列表</router-link>
        </div>
      </div>

      <div class="card">
        <h2 class="section-title mb-4">提交结果</h2>
        <pre class="bg-code text-code text-xs p-4 rounded-lg overflow-auto min-h-32 whitespace-pre-wrap break-words" dir="auto">{{ resultText }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Upload } from 'lucide-vue-next'

import FileUploader from '@/components/FileUploader.vue'
import { useTaskStore } from '@/stores'
import { toast } from '@/utils/toast'

const taskStore = useTaskStore()
const fileUploader = ref<InstanceType<typeof FileUploader> | null>(null)

const files = ref<File[]>([])
const resultText = ref('等待提交...')
const SUPPORTED_EXTENSIONS = new Set([
  '.pdf',
  '.doc',
  '.docx',
  '.ppt',
  '.pptx',
  '.xlsx',
  '.html',
  '.htm',
  '.epub',
  '.png',
  '.jpg',
  '.jpeg',
])

const form = reactive({
  parse_method: 'auto' as 'auto' | 'txt' | 'ocr',
  lang: 'ch' as 'ch' | 'en' | 'japan' | 'korean',
  priority: 0,
  save_parsed_content: false,
  save_middle_content: false,
  output_dir: 'outputs',
  start_page: 0,
  end_page: '' as '' | number,
})

const pageRangeError = computed(() => {
  if (form.end_page === '') {
    return ''
  }
  return Number(form.end_page) < form.start_page
    ? 'end_page 不能小于 start_page'
    : ''
})

function getFileExtension(filename: string): string {
  const index = filename.lastIndexOf('.')
  if (index < 0) {
    return ''
  }
  return filename.slice(index).toLowerCase()
}

const fileTypeError = computed(() => {
  if (files.value.length === 0) {
    return ''
  }
  const ext = getFileExtension(files.value[0].name)
  if (SUPPORTED_EXTENSIONS.has(ext)) {
    return ''
  }
  return `不支持的文件类型：${ext || '无扩展名'}`
})

const canSubmit = computed(() => {
  return files.value.length > 0 && !pageRangeError.value && !fileTypeError.value
})

const currentFileExtension = computed(() => {
  if (files.value.length === 0) {
    return ''
  }
  return getFileExtension(files.value[0].name)
})

const isPdfFile = computed(() => currentFileExtension.value === '.pdf')

function onFilesChange(nextFiles: File[]) {
  files.value = nextFiles
  if (!isPdfFile.value) {
    form.parse_method = 'auto'
    form.lang = 'ch'
    form.start_page = 0
    form.end_page = ''
    form.save_middle_content = false
  }
}

async function submit() {
  if (files.value.length === 0) {
    resultText.value = '请先选择文件'
    toast.warning('请先选择文件')
    return
  }
  if (pageRangeError.value) {
    resultText.value = pageRangeError.value
    toast.warning(pageRangeError.value)
    return
  }
  if (fileTypeError.value) {
    resultText.value = fileTypeError.value
    toast.warning(fileTypeError.value)
    return
  }

  const file = files.value[0]

  let result
  try {
    result = await taskStore.submit({
      file,
      parse_method: form.parse_method,
      lang: form.lang,
      priority: form.priority,
      save_parsed_content: form.save_parsed_content,
      save_middle_content: form.save_middle_content,
      output_dir: form.output_dir,
      start_page: form.start_page,
      end_page: form.end_page === '' ? null : form.end_page,
    })
  } catch (error: any) {
    const message = error?.message || '提交失败'
    resultText.value = message
    toast.error(message)
    return
  }

  resultText.value = JSON.stringify(result, null, 2)
  toast.success('任务提交成功')
  fileUploader.value?.clearFiles()
  files.value = []

  try {
    await taskStore.loadDashboard(8)
  } catch {
    toast.warning('任务已提交成功，但仪表盘刷新失败，可稍后手动刷新')
  }
}
</script>
