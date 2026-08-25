import crypto from 'node:crypto'
import childProcess from 'node:child_process'
import fs from 'node:fs'

const [payloadPath, eventPath, envId] = process.argv.slice(2)
if (!payloadPath || !eventPath || !envId) process.exit(2)
if (!/^[a-z0-9-]{3,80}$/.test(envId)) process.exit(2)

const command = `npx --yes --package=@cloudbase/cli@3.8.0 tcb -e ${envId} fn detail score-speaking --json`
const output = childProcess.execFileSync(process.env.ComSpec || 'cmd.exe', ['/d', '/s', '/c', command], {
  encoding: 'utf8', windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']
})
const detail = JSON.parse(output.slice(output.indexOf('{')))
const key = detail.data?.Environment?.Variables?.find((item) => item.Key === 'SPEAKING_INTERNAL_HMAC_KEY')?.Value
if (typeof key !== 'string' || key.length < 16) process.exit(3)

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map((item) => canonicalJson(item)).join(',')}]`
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().filter((key) => value[key] !== undefined)
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`
  }
  return JSON.stringify(value)
}

const payload = JSON.parse(fs.readFileSync(payloadPath, 'utf8'))
const signature = crypto.createHmac('sha256', key).update(canonicalJson(payload)).digest('base64url')
fs.writeFileSync(eventPath, JSON.stringify({ payload, signature }), 'utf8')
