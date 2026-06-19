import { render, screen } from '@testing-library/vue'
import { describe, expect, it } from 'vitest'

import ProjectAvatar from '~/components/ProjectAvatar.vue'

describe('ProjectAvatar', () => {
  it('uses the first letter of the first two words', () => {
    render(ProjectAvatar, { props: { name: 'Live Starter' } })
    expect(screen.getByText('LS')).toBeTruthy()
  })

  it('uses the first two letters for a single-word name', () => {
    render(ProjectAvatar, { props: { name: 'Claude' } })
    expect(screen.getByText('CL')).toBeTruthy()
  })

  it('uppercases and ignores extra whitespace', () => {
    render(ProjectAvatar, { props: { name: '  new   project ' } })
    expect(screen.getByText('NP')).toBeTruthy()
  })

  it('falls back gracefully for an empty name', () => {
    render(ProjectAvatar, { props: { name: '' } })
    expect(screen.getByText('·')).toBeTruthy()
  })
})
