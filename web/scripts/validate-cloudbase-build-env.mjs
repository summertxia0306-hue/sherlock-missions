const REQUIRED = [
  'VITE_CLOUDBASE_ENV_ID',
  'VITE_CLOUDBASE_ACCESS_KEY',
  'VITE_CLOUDBASE_FUNCTION_NAME'
]

const GITHUB_GATEWAY_URL = 'https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com/sherlock-api'

export function validateCloudBaseBuildEnv(env) {
  const httpUrl = typeof env.VITE_SHERLOCK_API_URL === 'string' ? env.VITE_SHERLOCK_API_URL.trim() : ''
  if (httpUrl) {
    if (httpUrl !== GITHUB_GATEWAY_URL) {
      throw new Error('CloudBase production build blocked: invalid VITE_SHERLOCK_API_URL')
    }
    return 'http-gateway'
  }
  const missing = REQUIRED.filter((name) => typeof env[name] !== 'string' || !env[name].trim())
  if (missing.length) throw new Error(`CloudBase production build blocked: missing ${missing.join(', ')}`)
  return 'web-sdk'
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  validateCloudBaseBuildEnv(process.env)
}
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
