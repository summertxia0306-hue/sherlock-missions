'use strict'

const crypto = require('node:crypto')
const { hashPassword } = require('./core')

async function main() {
  const password = process.env.P1_PARENT_PASSWORD || process.argv[2]
  if (!password) {
    throw new Error('请通过 P1_PARENT_PASSWORD 环境变量或命令参数提供家长验收密码')
  }
  const passwordHash = await hashPassword(password)
  const sessionKey = crypto.randomBytes(32).toString('base64url')
  process.stdout.write(`PARENT_PASSWORD_SCRYPT=${passwordHash}\nPARENT_SESSION_HMAC_KEY=${sessionKey}\n`)
}

main().catch((error) => {
  process.stderr.write(`${error.message}\n`)
  process.exitCode = 1
})
