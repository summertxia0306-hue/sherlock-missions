'use strict'

const { readFile } = require('node:fs/promises')
const { join, resolve, sep } = require('node:path')

const TEXT_TYPES = /^(?:text\/|application\/(?:json|manifest\+json)|image\/svg\+xml)/
const AUDIO_PATH = /^audio\/(?:listening|speaking)\/[A-Za-z0-9-]+\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_.-]+\.mp3$/

function securityHeaders(audioOrigin) {
  return {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
    'Permissions-Policy': 'camera=(), geolocation=()',
    'Content-Security-Policy': `default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; media-src 'self' ${audioOrigin}; connect-src 'self'; manifest-src 'self'; worker-src 'self'`
  }
}

function response(statusCode, body = '', headers = {}, isBase64Encoded = false) {
  return { statusCode, headers, body, ...(isBase64Encoded ? { isBase64Encoded: true } : {}) }
}

function decodePath(rawPath) {
  if (typeof rawPath !== 'string' || rawPath.includes('\\') || rawPath.includes('\0')) return null
  let decoded = rawPath.split('?')[0]
  try {
    for (let index = 0; index < 3; index += 1) {
      const next = decodeURIComponent(decoded)
      if (next === decoded) break
      decoded = next
    }
  } catch {
    return null
  }
  if (decoded.includes('\\') || decoded.includes('\0') || /%[0-9a-f]{2}/i.test(decoded)) return null
  const segments = decoded.split('/')
  if (segments.some((segment) => segment === '.' || segment === '..')) return null
  return decoded
}

function eventPath(event) {
  return event?.path || event?.requestContext?.path || event?.requestContext?.http?.path || ''
}

function createStaticApp({ root, manifest, routePrefix, audioBaseUrl }) {
  const releaseRoot = resolve(root)
  const prefix = routePrefix.endsWith('/') ? routePrefix : `${routePrefix}/`
  const audioBase = new URL(audioBaseUrl)
  const headers = securityHeaders(audioBase.origin)
  const files = manifest?.files || {}
  const audio = manifest?.audio || {}

  async function handle(event) {
    const method = String(event?.httpMethod || '').toUpperCase()
    if (!['GET', 'HEAD'].includes(method)) return response(405, 'Method Not Allowed', { Allow: 'GET, HEAD' })
    const decoded = decodePath(eventPath(event))
    if (!decoded) return response(400, 'Bad Request', { ...headers, 'Cache-Control': 'no-store' })
    if (decoded === prefix.slice(0, -1)) {
      return response(308, '', { ...headers, Location: prefix, 'Cache-Control': 'no-store' })
    }
    if (!decoded.startsWith(prefix)) return response(404, 'Not Found', { ...headers, 'Cache-Control': 'no-store' })

    let relativePath = decoded.slice(prefix.length)
    if (!relativePath) relativePath = 'index.html'
    if (AUDIO_PATH.test(relativePath)) {
      if (!Object.hasOwn(audio, relativePath)) return response(404, 'Not Found', { ...headers, 'Cache-Control': 'no-store' })
      return response(302, '', {
        ...headers,
        Location: new URL(relativePath, audioBase).href,
        'Cache-Control': 'public, max-age=300'
      })
    }
    if (!Object.hasOwn(files, relativePath)) {
      if (relativePath.includes('.')) return response(404, 'Not Found', { ...headers, 'Cache-Control': 'no-store' })
      relativePath = 'index.html'
    }

    const metadata = files[relativePath]
    const absolute = resolve(releaseRoot, ...relativePath.split('/'))
    if (!absolute.startsWith(`${releaseRoot}${sep}`)) return response(400, 'Bad Request', { ...headers, 'Cache-Control': 'no-store' })
    let body
    try {
      body = await readFile(absolute)
    } catch {
      return response(503, 'Static application unavailable', { ...headers, 'Cache-Control': 'no-store' })
    }
    const cacheControl = relativePath === 'index.html' || relativePath === 'sw.js'
      ? 'no-store'
      : relativePath.startsWith('assets/')
        ? 'public, max-age=31536000, immutable'
        : 'no-cache'
    const common = {
      ...headers,
      'Content-Type': metadata.contentType,
      'Content-Length': String(body.byteLength),
      'Cache-Control': cacheControl,
      ETag: `"sha256-${metadata.sha256}"`
    }
    if (method === 'HEAD') return response(200, '', common)
    const isText = TEXT_TYPES.test(metadata.contentType)
    return response(200, isText ? body.toString('utf8') : body.toString('base64'), common, !isText)
  }

  return { handle }
}

module.exports = { createStaticApp, decodePath }
