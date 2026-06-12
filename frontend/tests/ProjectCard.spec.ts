import { render, screen } from '@testing-library/vue'
import { describe, expect, it } from 'vitest'

import ProjectCard from '~/components/ProjectCard.vue'
import type { Project } from '~/types/api'

const project: Project = {
  id: 1,
  name: 'DevDesk',
  description: 'My workspace',
  status: 'active',
  color: '#6366f1',
}

describe('ProjectCard', () => {
  it('renders name, description and status', () => {
    render(ProjectCard, { props: { project } })
    expect(screen.getByText('DevDesk')).toBeTruthy()
    expect(screen.getByText('My workspace')).toBeTruthy()
    expect(screen.getByText('active')).toBeTruthy()
  })

  it('emits open, edit, archive and delete', async () => {
    const { emitted, getByRole } = render(ProjectCard, { props: { project } })
    getByRole('button', { name: /open/i }).click()
    getByRole('button', { name: /edit/i }).click()
    getByRole('button', { name: /archive/i }).click()
    getByRole('button', { name: /delete/i }).click()
    expect(emitted()).toHaveProperty('open')
    expect(emitted()).toHaveProperty('edit')
    expect(emitted()).toHaveProperty('archive')
    expect(emitted()).toHaveProperty('delete')
  })
})
