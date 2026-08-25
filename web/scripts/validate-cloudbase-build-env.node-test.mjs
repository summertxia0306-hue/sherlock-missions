import test from 'node:test'
import assert from 'node:assert/strict'
import { validateCloudBaseBuildEnv } from './validate-cloudbase-build-env.mjs'

test('blocks a production build that would omit CloudBase public configuration', () => {
  assert.throws(() => validateCloudBaseBuildEnv({}), /VITE_CLOUDBASE_ENV_ID/)
  assert.doesNotThrow(() => validateCloudBaseBuildEnv({
    VITE_CLOUDBASE_ENV_ID: 'family24-test',
    VITE_CLOUDBASE_ACCESS_KEY: 'publishable-key',
    VITE_CLOUDBASE_FUNCTION_NAME: 'sherlock-api'
  }))
})
