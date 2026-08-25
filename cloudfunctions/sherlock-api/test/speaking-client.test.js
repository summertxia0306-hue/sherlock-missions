'use strict'

const { it } = require('node:test')
const assert = require('node:assert/strict')
const { signature } = require('../speaking-client')

it('signs equivalent scorer payloads independently of CloudBase field order', () => {
  const key = '1234567890abcdef'
  const original = { result_id: 'r1', course_id: 'S01D39', question_id: 1, nested: { z: 2, a: 1 } }
  const reordered = { nested: { a: 1, z: 2 }, question_id: 1, course_id: 'S01D39', result_id: 'r1' }
  assert.equal(signature(original, key), signature(reordered, key))
})
