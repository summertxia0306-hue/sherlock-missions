'use strict'

const crypto = require('node:crypto')

const ALLOWED_ORIGIN = 'https://summertxia0306-hue.github.io'
const MAX_BODY_BYTES = 1_200_000
const CLIENT_ID_PATTERN = /^[A-Za-z0-9_-]{16,128}$/

class HttpRequestError extends Error {
  constructor(code, statusCode) {
    super(code)
    this.name = 'HttpRequestError'
    this.code = code
    this.statusCode = statusCode
  }
}

function normalizedHeaders(headers = {}) {
  return Object.fromEntries(Object.entries(headers).map(([name, value]) => [name.toLowerCase(), String(value)]))
}

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Sherlock-Client-Id',
    'Access-Control-Max-Age': '600',
    'Cache-Control': 'no-store',
    Vary: 'Origin'
  }
}

function createHttpResponse(result, statusCode = 200, includeCors = true) {
  return {
    statusCode,
    headers: {
      ...(includeCors ? corsHeaders() : {}),
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store'
    },
    body: statusCode === 204 ? '' : JSON.stringify(result)
  }
}

function isHttpGatewayEvent(event) {
  return Boolean(event && typeof event === 'object' && typeof event.httpMethod === 'string')
}

function parseHttpGatewayEvent(event) {
  const headers = normalizedHeaders(event?.headers)
  const origin = headers.origin
  if (origin !== ALLOWED_ORIGIN) throw new HttpRequestError('HTTP_ORIGIN_DENIED', 403)

  const method = String(event.httpMethod || '').toUpperCase()
  if (method === 'OPTIONS') {
    return { kind: 'preflight', response: createHttpResponse(null, 204) }
  }
  if (method !== 'POST') throw new HttpRequestError('HTTP_METHOD_NOT_ALLOWED', 405)
  if (!headers['content-type']?.toLowerCase().includes('application/json')) {
    throw new HttpRequestError('HTTP_CONTENT_TYPE_REQUIRED', 415)
  }

  const clientId = headers['x-sherlock-client-id'] || ''
  if (!CLIENT_ID_PATTERN.test(clientId)) throw new HttpRequestError('HTTP_CLIENT_REQUIRED', 400)

  let rawBody = event.body
  if (event.isBase64Encoded === true && typeof rawBody === 'string') {
    rawBody = Buffer.from(rawBody, 'base64').toString('utf8')
  }
  if (typeof rawBody !== 'string' || Buffer.byteLength(rawBody, 'utf8') > MAX_BODY_BYTES) {
    throw new HttpRequestError('HTTP_BODY_INVALID', 413)
  }

  let payload
  try {
    payload = JSON.parse(rawBody)
  } catch {
    throw new HttpRequestError('HTTP_BODY_INVALID', 400)
  }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new HttpRequestError('HTTP_BODY_INVALID', 400)
  }

  const digest = crypto.createHash('sha256').update(clientId).digest('hex').slice(0, 32)
  return { kind: 'request', payload, callerId: `github:${digest}` }
}

module.exports = {
  ALLOWED_ORIGIN,
  HttpRequestError,
  createHttpResponse,
  isHttpGatewayEvent,
  parseHttpGatewayEvent
}
