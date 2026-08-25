'use strict'

const { it } = require('node:test')
const assert = require('node:assert/strict')
const config = require('../../../cloudbaserc.json')

it('keeps the public API timeout at least as long as the private speaking scorer', () => {
  const api = config.functions.find((item) => item.name === 'sherlock-api')
  const scorer = config.functions.find((item) => item.name === 'score-speaking')
  assert.ok(api)
  assert.ok(scorer)
  assert.ok(api.timeout >= scorer.timeout, `sherlock-api timeout ${api.timeout}s is shorter than score-speaking ${scorer.timeout}s`)
})
