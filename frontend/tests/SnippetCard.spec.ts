import { render, screen } from '@testing-library/vue'
import { describe, expect, it } from 'vitest'

import SnippetCard from '~/components/SnippetCard.vue'
import type { Snippet } from '~/types/api'

const snippet: Snippet = {
  id: 'abc123',
  project_id: null,
  title: 'Fetch wrapper',
  language: 'typescript',
  code: 'export const x = 1',
  tags: ['nuxt', 'http'],
  notes: '',
}

describe('SnippetCard', () => {
  it('renders title, language and tags', () => {
    render(SnippetCard, { props: { snippet } })
    expect(screen.getByText('Fetch wrapper')).toBeTruthy()
    expect(screen.getByText('typescript')).toBeTruthy()
    expect(screen.getByText('nuxt')).toBeTruthy()
    expect(screen.getByText('http')).toBeTruthy()
  })

  it('renders the code', () => {
    // highlight.js splits the code across token spans, so match on textContent
    const { container } = render(SnippetCard, { props: { snippet } })
    expect(container.querySelector('pre')?.textContent).toContain('export const x = 1')
  })

  it('emits edit and delete', async () => {
    const { emitted, getByRole } = render(SnippetCard, { props: { snippet } })
    getByRole('button', { name: /edit/i }).click()
    getByRole('button', { name: /delete/i }).click()
    expect(emitted()).toHaveProperty('edit')
    expect(emitted()).toHaveProperty('delete')
  })
})
