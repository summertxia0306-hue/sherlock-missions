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
  assert.doesNotThrow(() => validateCloudBaseBuildEnv({
    VITE_SHERLOCK_API_URL: 'https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com/sherlock-api'
  }))
  assert.throws(() => validateCloudBaseBuildEnv({
    VITE_SHERLOCK_API_URL: 'http://wrong.example/sherlock-api'
  }), /VITE_SHERLOCK_API_URL/)
})
