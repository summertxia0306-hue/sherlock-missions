import { describe, expect, it } from 'vitest'
import { getModule, visibleModules } from './modules'

describe('module registry', () => {
  it('keeps vocabulary registered but hidden', () => {
    expect(getModule('vocabulary')).toMatchObject({ id: 'vocabulary', visible: false })
    expect(visibleModules().map((item) => item.id)).toEqual(['listening', 'speaking', 'parent'])
  })
})

