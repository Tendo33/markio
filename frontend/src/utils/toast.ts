export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastOptions {
  message: string
  type?: ToastType
  duration?: number
}

const toastQueue: ToastOptions[] = []
let activeToast = false
let toastContainer: HTMLDivElement | null = null
const SVG_NS = 'http://www.w3.org/2000/svg'

function getThemeValue(name: string, fallback: string) {
  if (typeof window === 'undefined') {
    return fallback
  }
  const value = window.getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

function ensureContainer() {
  if (toastContainer) {
    return toastContainer
  }
  const container = document.createElement('div')
  container.setAttribute('aria-live', 'polite')
  container.setAttribute('aria-atomic', 'true')
  Object.assign(container.style, {
    position: 'fixed',
    top: '1rem',
    right: '1rem',
    zIndex: '9999',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    maxWidth: 'min(500px, calc(100vw - 2rem))',
  })
  document.body.appendChild(container)
  toastContainer = container
  return container
}

function enqueueToast(options: ToastOptions) {
  if (toastQueue.length >= 30) {
    toastQueue.shift()
  }
  toastQueue.push(options)
  if (!activeToast) {
    void showNextToast()
  }
}

async function showNextToast() {
  const nextToast = toastQueue.shift()
  if (!nextToast) {
    activeToast = false
    return
  }
  activeToast = true

  const container = ensureContainer()
  const toastElement = buildToastElement(nextToast)
  container.appendChild(toastElement)

  requestAnimationFrame(() => {
    toastElement.style.opacity = '1'
    toastElement.style.transform = 'translateX(0)'
  })

  const timeout = Math.max(1000, nextToast.duration ?? 3000)
  await wait(timeout)
  toastElement.style.opacity = '0'
  toastElement.style.transform = 'translateX(100%)'
  await wait(220)
  toastElement.remove()

  activeToast = false
  if (toastQueue.length > 0) {
    void showNextToast()
  }
}

function buildToastElement(options: ToastOptions): HTMLDivElement {
  const { message, type = 'info' } = options
  const colors = getToastColors(type)

  const toast = document.createElement('div')
  toast.setAttribute('role', type === 'error' ? 'alert' : 'status')
  Object.assign(toast.style, {
    minWidth: '250px',
    padding: '0.875rem 1rem',
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
    boxShadow: '0 16px 32px -20px rgba(22, 33, 23, 0.4)',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    fontSize: '14px',
    fontWeight: '500',
    lineHeight: '1.5',
    transition: 'all 0.2s ease',
    transform: 'translateX(100%)',
    opacity: '0',
    backgroundColor: colors.bg,
    color: colors.text,
    fontFamily: '"Soehne", "Soehne Buch", "Geist", "SF Pro Text", "PingFang SC", "Noto Sans SC", sans-serif',
  })

  const icon = document.createElement('span')
  Object.assign(icon.style, {
    flexShrink: '0',
    width: '18px',
    height: '18px',
    color: colors.text,
  })
  icon.appendChild(createToastIcon(type))

  const messageElement = document.createElement('span')
  messageElement.innerText = message
  Object.assign(messageElement.style, {
    flex: '1',
    wordBreak: 'break-word',
    color: colors.text,
    fontSize: '14px',
    lineHeight: '1.45',
    fontWeight: '500',
  })

  toast.appendChild(icon)
  toast.appendChild(messageElement)
  return toast
}

function wait(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function getToastColors(type: ToastType): { bg: string; text: string; border: string } {
  const colorMap = {
    success: {
      bg: getThemeValue('--toast-success-bg', '#154e3c'),
      text: getThemeValue('--toast-success-text', '#f7faf6'),
      border: getThemeValue('--status-success-border', '#b8decb'),
    },
    error: {
      bg: getThemeValue('--toast-error-bg', '#9d281e'),
      text: getThemeValue('--toast-error-text', '#f7faf6'),
      border: getThemeValue('--status-danger-border', '#e8b7b1'),
    },
    warning: {
      bg: getThemeValue('--toast-warning-bg', '#8b5300'),
      text: getThemeValue('--toast-warning-text', '#f7faf6'),
      border: getThemeValue('--status-warning-border', '#e8d3a3'),
    },
    info: {
      bg: getThemeValue('--toast-info-bg', '#1f4ea8'),
      text: getThemeValue('--toast-info-text', '#f7faf6'),
      border: getThemeValue('--status-info-border', '#c5d5f4'),
    },
  }
  return colorMap[type]
}

function createToastIcon(type: ToastType): SVGSVGElement {
  const pathByType: Record<ToastType, string> = {
    success:
      'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z',
    error:
      'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z',
    warning:
      'M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z',
    info:
      'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z',
  }

  const svg = document.createElementNS(SVG_NS, 'svg')
  svg.setAttribute('viewBox', '0 0 20 20')
  svg.setAttribute('fill', 'currentColor')
  svg.setAttribute('aria-hidden', 'true')

  const path = document.createElementNS(SVG_NS, 'path')
  path.setAttribute('fill-rule', 'evenodd')
  path.setAttribute('clip-rule', 'evenodd')
  path.setAttribute('d', pathByType[type])

  svg.appendChild(path)
  return svg
}

export function showToast(options: ToastOptions) {
  const message = options.message?.trim()
  if (!message) {
    return
  }
  enqueueToast(options)
}

export const toast = {
  success: (message: string) => showToast({ message, type: 'success' }),
  error: (message: string) => showToast({ message, type: 'error' }),
  warning: (message: string) => showToast({ message, type: 'warning' }),
  info: (message: string) => showToast({ message, type: 'info' }),
}
