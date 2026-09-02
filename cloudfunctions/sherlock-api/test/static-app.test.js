'use strict'

const test = require('node:test')
const assert = require('node:assert/strict')
const { mkdtemp, mkdir, rm, writeFile } = require('node:fs/promises')
const { join } = require('node:path')
const { tmpdir } = require('node:os')
const { createStaticApp } = require('../static-app')

async function fixture() {
  const root = await mkdtemp(join(tmpdir(), 'sherlock-static-app-'))
  await mkdir(join(root, 'assets'), { recursive: true })
  await mkdir(join(root, 'content', 'listening'), { recursive: true })
  await writeFile(join(root, 'index.html'), '<!doctype html><div id="root"></div>')
  await writeFile(join(root, 'assets', 'app-123.js'), 'console.info("app")')
  await writeFile(join(root, 'content', 'listening', 'catalog.json'), '[]')
  await writeFile(join(root, 'sw.js'), 'self.skipWaiting()')
  const manifest = {
    version: 1,
    files: {
      'index.html': { contentType: 'text/html; charset=utf-8', bytes: 36, sha256: 'a'.repeat(64) },
      'assets/app-123.js': { contentType: 'text/javascript; charset=utf-8', bytes: 19, sha256: 'b'.repeat(64) },
      'content/listening/catalog.json': { contentType: 'application/json; charset=utf-8', bytes: 2, sha256: 'c'.repeat(64) },
      'sw.js': { contentType: 'text/javascript; charset=utf-8', bytes: 18, sha256: 'd'.repeat(64) }
    },
    audio: {
      'audio/listening/W01D50/q01.mp3': { bytes: 11 }
    }
  }
  const app = createStaticApp({
    root,
    manifest,
    routePrefix: '/sherlock-api/',
    audioBaseUrl: 'https://family24.example.tcloudbaseapp.com/sherlock-english/'
  })
  return { root, app }
}

function request(path, method = 'GET') {
  return { httpMethod: method, path }
}

test('serves the PWA shell with inline disposition and strict browser headers', async () => {
  const { root, app } = await fixture()
  try {
    const response = await app.handle(request('/sherlock-api/'))
    assert.equal(response.statusCode, 200)
    assert.equal(response.headers['Content-Type'], 'text/html; charset=utf-8')
    assert.equal(response.headers['Cache-Control'], 'no-store')
    assert.equal(response.headers['Content-Disposition'], 'inline')
    assert.equal(response.headers['X-Content-Type-Options'], 'nosniff')
    assert.match(response.headers['Content-Security-Policy'], /default-src 'self'/)
    assert.match(response.body, /id="root"/)
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})

test('accepts the CloudBase gateway path after the mounted route prefix is stripped', async () => {
  const { root, app } = await fixture()
  try {
    const shell = await app.handle(request('/'))
    assert.equal(shell.statusCode, 200)
    assert.equal(shell.headers['Content-Type'], 'text/html; charset=utf-8')
    assert.match(shell.body, /id="root"/)
    const asset = await app.handle(request('/assets/app-123.js'))
    assert.equal(asset.statusCode, 200)
    assert.match(asset.headers['Cache-Control'], /immutable/)
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})

test('uses immutable caching for hashed assets and an empty body for HEAD', async () => {
  const { root, app } = await fixture()
  try {
    const get = await app.handle(request('/sherlock-api/assets/app-123.js'))
    assert.equal(get.statusCode, 200)
    assert.equal(get.headers['Content-Type'], 'text/javascript; charset=utf-8')
    assert.match(get.headers['Cache-Control'], /immutable/)
    const head = await app.handle(request('/sherlock-api/assets/app-123.js', 'HEAD'))
    assert.equal(head.statusCode, 200)
    assert.equal(head.body, '')
    assert.equal(head.headers['Content-Length'], String(Buffer.byteLength('console.info("app")')))
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})

test('falls back only extensionless SPA routes and returns 404 for unknown resources', async () => {
  const { root, app } = await fixture()
  try {
    assert.equal((await app.handle(request('/sherlock-api/listening'))).statusCode, 200)
    assert.equal((await app.handle(request('/sherlock-api/assets/missing.js'))).statusCode, 404)
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})

test('redirects only manifest-listed audio to the fixed CloudBase CDN', async () => {
  const { root, app } = await fixture()
  try {
    const allowed = await app.handle(request('/sherlock-api/audio/listening/W01D50/q01.mp3'))
    assert.equal(allowed.statusCode, 302)
    assert.equal(allowed.headers.Location, 'https://family24.example.tcloudbaseapp.com/sherlock-english/audio/listening/W01D50/q01.mp3')
    const denied = await app.handle(request('/sherlock-api/audio/listening/L4A-T1-W01-D01/q01.mp3'))
    assert.equal(denied.statusCode, 404)
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})

test('rejects raw and encoded traversal without reading outside the release root', async () => {
  const { root, app } = await fixture()
  try {
    for (const path of [
      '/sherlock-api/../index.js',
      '/sherlock-api/%2e%2e/index.js',
      '/sherlock-api/%252e%252e/index.js',
      '/sherlock-api/..\\index.js',
      '/sherlock-api/%5c..%5cindex.js',
      '/sherlock-api/%00index.html'
    ]) {
      const response = await app.handle(request(path))
      assert.ok([400, 404].includes(response.statusCode), `${path}: ${response.statusCode}`)
      assert.doesNotMatch(response.body || '', /require\(|cloudbase/)
    }
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})
