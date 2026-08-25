const REQUIRED = [
  'VITE_CLOUDBASE_ENV_ID',
  'VITE_CLOUDBASE_ACCESS_KEY',
  'VITE_CLOUDBASE_FUNCTION_NAME'
]

export function validateCloudBaseBuildEnv(env) {
  const missing = REQUIRED.filter((name) => typeof env[name] !== 'string' || !env[name].trim())
  if (missing.length) throw new Error(`CloudBase production build blocked: missing ${missing.join(', ')}`)
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  validateCloudBaseBuildEnv(process.env)
}
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
