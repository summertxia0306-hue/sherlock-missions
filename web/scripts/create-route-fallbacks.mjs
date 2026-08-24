import { copyFile, mkdir, readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const dist = new URL('../dist/', import.meta.url)
const indexPath = new URL('index.html', dist)
const html = await readFile(indexPath, 'utf8')

if (!html.includes('/sherlock-english/assets/')) {
  throw new Error('Build output does not use the required /sherlock-english/ base path')
}

for (const route of ['listening', 'speaking', 'parent']) {
  const routeDirectory = new URL(`${route}/`, dist)
  await mkdir(routeDirectory, { recursive: true })
  await copyFile(indexPath, join(fileURLToPath(routeDirectory), 'index.html'))
}
