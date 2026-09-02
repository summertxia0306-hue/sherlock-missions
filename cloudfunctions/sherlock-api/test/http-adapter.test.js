'use strict'

const test = require('node:test')
const assert = require('node:assert/strict')

const {
  HttpRequestError,
  createHttpResponse,
  parseHttpGatewayEvent
} = require('../http-adapter')

const origin = 'https://summertxia0306-hue.github.io'
const domesticOrigin = 'https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com'

function request(overrides = {}) {
  return {
    httpMethod: 'POST',
    headers: {
      origin,
      'content-type': 'application/json',
      'x-sherlock-client-id': '123e4567-e89b-42d3-a456-426614174000'
    },
    body: JSON.stringify({ action: 'health' }),
    ...overrides
  }
}

test('parses an allowed GitHub Pages request and creates a stable opaque caller', () => {
  const first = parseHttpGatewayEvent(request())
  const second = parseHttpGatewayEvent(request())
  assert.equal(first.kind, 'request')
  assert.deepEqual(first.payload, { action: 'health' })
  assert.equal(first.callerId, second.callerId)
  assert.match(first.callerId, /^github:[a-f0-9]{32}$/)
  assert.equal(first.transport, 'github-http')
  assert.doesNotMatch(first.callerId, /123e4567/)
})

test('parses the exact domestic gateway origin as a separate trusted transport', () => {
  const parsed = parseHttpGatewayEvent(request({
    headers: { ...request().headers, origin: domesticOrigin }
  }))
  assert.equal(parsed.transport, 'domestic-http')
  assert.match(parsed.callerId, /^domestic:[a-f0-9]{32}$/)
})

test('handles preflight without invoking business logic', () => {
  const parsed = parseHttpGatewayEvent(request({ httpMethod: 'OPTIONS', body: '' }))
  assert.equal(parsed.kind, 'preflight')
  assert.equal(parsed.response.statusCode, 204)
  assert.equal(parsed.response.headers['Access-Control-Allow-Origin'], origin)
  assert.match(parsed.response.headers['Access-Control-Allow-Headers'], /X-Sherlock-Client-Id/)
})

test('rejects unapproved origins, methods, clients, and malformed bodies', () => {
  const cases = [
    request({ headers: { ...request().headers, origin: 'https://evil.example' } }),
    request({ httpMethod: 'GET' }),
    request({ headers: { ...request().headers, 'x-sherlock-client-id': '../bad' } }),
    request({ body: '{broken' })
  ]
  for (const event of cases) {
    assert.throws(() => parseHttpGatewayEvent(event), HttpRequestError)
  }
})

test('returns JSON with exact CORS and no-store headers', () => {
  const response = createHttpResponse({ ok: true }, 200)
  assert.equal(response.statusCode, 200)
  assert.equal(response.headers['Access-Control-Allow-Origin'], origin)
  assert.equal(response.headers['Cache-Control'], 'no-store')
  assert.deepEqual(JSON.parse(response.body), { ok: true })
})

test('returns CORS only for the exact allowed origin passed by the adapter', () => {
  const domestic = createHttpResponse({ ok: true }, 200, domesticOrigin)
  assert.equal(domestic.headers['Access-Control-Allow-Origin'], domesticOrigin)
  assert.throws(() => createHttpResponse({ ok: true }, 200, 'https://evil.example'), HttpRequestError)
})
