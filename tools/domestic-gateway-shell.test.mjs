import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')

test('candidate deployment builds the exact domestic base and updates code without changing entry mode', async () => {
  const script = await readFile(resolve(root, 'tools', 'deploy-domestic-gateway-candidate.ps1'), 'utf8')
  assert.match(script, /VITE_APP_BASE\s*=\s*'\/sherlock-api\/'/)
  assert.match(script, /prepare-domestic-gateway-release\.mjs/)
  assert.match(script, /fn code update sherlock-api/)
  assert.match(script, /Wait-ForStaticShell/)
  assert.match(script, /FORMAL_ENTRY_REQUIRED/)
  assert.match(script, /github-http-only/)
  assert.doesNotMatch(script, /FORMAL_ENTRY_MODE['"]?\]\s*=\s*'domestic-http-only'/)
})

test('formal switch is exact-origin, rollback-capable, and changes only the approved entry mode', async () => {
  const script = await readFile(resolve(root, 'tools', 'switch-formal-entry-to-domestic.ps1'), 'utf8')
  assert.match(script, /github-http-only/)
  assert.match(script, /domestic-http-only/)
  assert.match(script, /family24-d7gqb6r6m2d722f7a-1383960965\.ap-shanghai\.app\.tcloudbase\.com/)
  assert.match(script, /summertxia0306-hue\.github\.io/)
  assert.match(script, /Deploy-Environment \$OriginalEnvironment/)
  assert.match(script, /FORMAL_ENTRY_REQUIRED/)
  assert.doesNotMatch(script, /FORMAL_ENABLED['"]?\]\s*=\s*'false'/)
})
