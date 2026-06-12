import { describe, expect, it } from 'vitest'

import { POSITION_STEP, computePosition } from '~/utils/position'

describe('computePosition', () => {
  it('starts an empty column at one step', () => {
    expect(computePosition(undefined, undefined)).toBe(POSITION_STEP)
  })

  it('drops at the top: half of the next position', () => {
    expect(computePosition(undefined, 1024)).toBe(512)
  })

  it('drops at the bottom: previous plus one step', () => {
    expect(computePosition(2048, undefined)).toBe(2048 + POSITION_STEP)
  })

  it('drops between two cards: midpoint', () => {
    expect(computePosition(1024, 2048)).toBe(1536)
  })
})
