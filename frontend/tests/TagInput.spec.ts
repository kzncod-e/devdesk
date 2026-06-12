import { fireEvent, render, screen } from '@testing-library/vue'
import { describe, expect, it } from 'vitest'

import TagInput from '~/components/TagInput.vue'

describe('TagInput', () => {
  it('renders existing tags as chips', () => {
    render(TagInput, { props: { modelValue: ['nuxt', 'http'] } })
    expect(screen.getByText('nuxt')).toBeTruthy()
    expect(screen.getByText('http')).toBeTruthy()
  })

  it('adds a tag on Enter and emits update', async () => {
    const { emitted } = render(TagInput, { props: { modelValue: ['a'] } })
    const input = screen.getByRole('textbox')
    await fireEvent.update(input, 'newtag')
    await fireEvent.keyDown(input, { key: 'Enter' })
    expect(emitted()['update:modelValue']?.[0]).toEqual([['a', 'newtag']])
  })

  it('ignores duplicates and empty input', async () => {
    const { emitted } = render(TagInput, { props: { modelValue: ['a'] } })
    const input = screen.getByRole('textbox')
    await fireEvent.update(input, 'a')
    await fireEvent.keyDown(input, { key: 'Enter' })
    await fireEvent.update(input, '   ')
    await fireEvent.keyDown(input, { key: 'Enter' })
    expect(emitted()['update:modelValue']).toBeUndefined()
  })

  it('removes a tag via its remove button', async () => {
    const { emitted } = render(TagInput, { props: { modelValue: ['a', 'b'] } })
    await fireEvent.click(screen.getByRole('button', { name: /remove a/i }))
    expect(emitted()['update:modelValue']?.[0]).toEqual([['b']])
  })
})
