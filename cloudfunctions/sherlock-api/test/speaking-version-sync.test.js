'use strict'

const { it } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const { createFileSpeakingCourseProvider } = require('../speaking-service')

it('publishes matching versions only for formal courses and keeps hidden term courses function-only', () => {
  const provider = createFileSpeakingCourseProvider()
  const catalog = provider.catalog()
  assert.equal(catalog.length, 18)
  assert.equal(catalog.filter((item) => item.visible === false).length, 6)
  const publicDirectory = path.join(__dirname, '..', '..', '..', 'web', 'public', 'content', 'speaking')
  for (const item of catalog) {
    const publicFile = path.join(publicDirectory, `${item.course_id}.json`)
    if (!item.visible) {
      assert.equal(fs.existsSync(publicFile), false, item.course_id)
      continue
    }
    const child = JSON.parse(fs.readFileSync(publicFile, 'utf8'))
    assert.equal(child.course_version, item.course_version, item.course_id)
  }
})
