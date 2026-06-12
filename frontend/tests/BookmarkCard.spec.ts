import { render, screen } from '@testing-library/vue'
import { describe, expect, it } from 'vitest'

import BookmarkCard from '~/components/BookmarkCard.vue'
import type { Bookmark } from '~/types/api'

const bookmark: Bookmark = {
  id: 'b1',
  project_id: null,
  url: 'https://nuxt.com/docs',
  title: 'Nuxt Docs',
  description: 'The Nuxt documentation',
  tags: ['docs', 'vue'],
  favicon: 'https://nuxt.com/icon.png',
  fetched_meta: {},
}

describe('BookmarkCard', () => {
  it('renders linked title, description, favicon and tags', () => {
    render(BookmarkCard, { props: { bookmark } })
    const link = screen.getByRole('link', { name: /nuxt docs/i })
    expect(link.getAttribute('href')).toBe('https://nuxt.com/docs')
    expect(screen.getByText('The Nuxt documentation')).toBeTruthy()
    expect(screen.getByRole('img').getAttribute('src')).toBe('https://nuxt.com/icon.png')
    expect(screen.getByText('docs')).toBeTruthy()
    expect(screen.getByText('vue')).toBeTruthy()
  })

  it('falls back to the URL when no title was fetched yet', () => {
    render(BookmarkCard, { props: { bookmark: { ...bookmark, title: '', favicon: '' } } })
    expect(screen.getByRole('link', { name: /nuxt\.com\/docs/i })).toBeTruthy()
    expect(screen.queryByRole('img')).toBeNull()
  })

  it('emits edit and delete', async () => {
    const { emitted, getByRole } = render(BookmarkCard, { props: { bookmark } })
    getByRole('button', { name: /edit/i }).click()
    getByRole('button', { name: /delete/i }).click()
    expect(emitted()).toHaveProperty('edit')
    expect(emitted()).toHaveProperty('delete')
  })
})
