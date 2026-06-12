import { render, screen } from '@testing-library/vue'
import { describe, expect, it } from 'vitest'

import UiBadge from '~/components/UiBadge.vue'

describe('UiBadge', () => {
  it('renders its slot content', () => {
    render(UiBadge, { slots: { default: 'high' } })
    expect(screen.getByText('high')).toBeTruthy()
  })

  it('applies the tone class', () => {
    const { container } = render(UiBadge, {
      props: { tone: 'red' },
      slots: { default: 'x' },
    })
    expect(container.querySelector('span')?.className).toContain('bg-red-100')
  })
})
