// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Sanitize HTML content to prevent XSS attacks.
 *
 * Uses a whitelist approach: only safe tags and attributes are allowed.
 * Everything else is escaped or stripped.
 */

const ALLOWED_TAGS = new Set([
  'p', 'br', 'b', 'i', 'em', 'strong', 'u', 's', 'strike',
  'ul', 'ol', 'li', 'a', 'span', 'div', 'blockquote', 'pre', 'code',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'sub', 'sup',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
])

const ALLOWED_ATTRS = new Set([
  'class', 'href', 'target', 'rel', 'title', 'id',
])

/**
 * Strip dangerous HTML from user content while preserving safe formatting.
 */
export function sanitizeHtml(html: string): string {
  if (!html) return ''

  const doc = new DOMParser().parseFromString(html, 'text/html')
  sanitizeNode(doc.body)
  return doc.body.innerHTML
}

function sanitizeNode(node: Node): void {
  const childNodes = Array.from(node.childNodes)

  for (const child of childNodes) {
    if (child.nodeType === Node.TEXT_NODE) {
      continue
    }

    if (child.nodeType === Node.COMMENT_NODE) {
      node.removeChild(child)
      continue
    }

    if (child.nodeType === Node.ELEMENT_NODE) {
      const el = child as Element
      const tagName = el.tagName.toLowerCase()

      if (!ALLOWED_TAGS.has(tagName)) {
        // Replace disallowed element with its text content
        const text = document.createTextNode(el.textContent || '')
        node.replaceChild(text, child)
        continue
      }

      // Remove disallowed attributes
      const attrs = Array.from(el.attributes)
      for (const attr of attrs) {
        if (!ALLOWED_ATTRS.has(attr.name)) {
          el.removeAttribute(attr.name)
        }
      }

      // Sanitize href to prevent javascript: URLs
      if (el.hasAttribute('href')) {
        const href = el.getAttribute('href') || ''
        if (!/^(?:https?:\/\/|mailto:|\/|#)/i.test(href.trim())) {
          el.removeAttribute('href')
        }
      }

      // Force external links to open safely
      if (tagName === 'a') {
        el.setAttribute('rel', 'noopener noreferrer')
      }

      // Recurse into children
      sanitizeNode(el)
    }
  }
}
