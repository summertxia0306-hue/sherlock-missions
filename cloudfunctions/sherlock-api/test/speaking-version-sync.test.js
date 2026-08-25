'use strict'

const { it } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const { createFileSpeakingCourseProvider } = require('../speaking-service')

it('publishes the same semantic version used by the speaking API for all 12 courses', () => {
  const provider = createFileSpeakingCourseProvider()
  const publicDirectory = path.join(__dirname, '..', '..', '..', 'web', 'public', 'content', 'speaking')
  for (const item of provider.catalog()) {
    const child = JSON.parse(fs.readFileSync(path.join(publicDirectory, `${item.course_id}.json`), 'utf8'))
    assert.equal(child.course_version, item.course_version, item.course_id)
  }
})
