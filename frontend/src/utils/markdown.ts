import DOMPurify from 'dompurify'
import { marked } from 'marked'

/** Render untrusted Markdown to sanitized HTML for preview. */
export function renderMarkdown(source: string): string {
  const html = marked.parse(source, { async: false, gfm: true, breaks: false }) as string
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
}
