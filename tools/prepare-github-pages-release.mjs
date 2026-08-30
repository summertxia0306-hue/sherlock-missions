import { resolve } from 'node:path'
import { prepareGitHubPagesRelease } from './prepare-github-pages-release-lib.mjs'

const [distDir, pagesDir] = process.argv.slice(2)
if (!distDir || !pagesDir) {
  throw new Error('Usage: node tools/prepare-github-pages-release.mjs <dist-dir> <pages-checkout>')
}

const result = await prepareGitHubPagesRelease({
  distDir: resolve(distDir),
  pagesDir: resolve(pagesDir),
  expectedRemote: 'https://github.com/summertxia0306-hue/summertxia0306-hue.github.io.git'
})

process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
