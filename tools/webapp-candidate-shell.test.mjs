import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const scriptPath = resolve(import.meta.dirname, 'deploy-webapp-candidate.ps1')

test('Web App candidate is isolated, exact-origin, and keeps formal on GitHub', async () => {
  const script = await readFile(scriptPath, 'utf8')
  assert.match(script, /sherlock-english-family24-d7gqb6r6m2d722f7a\.webapps\.tcloudbase\.com/)
  assert.match(script, /VITE_APP_BASE\s*=\s*'\/sherlock-english\/'/)
  assert.match(script, /app deploy sherlock-english/)
  assert.match(script, /--deploy-path \/sherlock-english/)
  assert.match(script, /family24-web/)
  assert.match(script, /fn code update sherlock-api/)
  assert.match(script, /FORMAL_ENTRY_REQUIRED/)
  assert.match(script, /Assert-ApiError \$WebAppDenied 200 'FORMAL_ENTRY_REQUIRED'/)
  assert.match(script, /github-http-only/)
  assert.doesNotMatch(script, /app delete/)
  assert.doesNotMatch(script, /FORMAL_ENTRY_MODE['"]?\]\s*=\s*'webapp-http-only'/)
})
