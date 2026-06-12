import { render, screen } from '@testing-library/vue'
import { describe, expect, it } from 'vitest'

import TaskCard from '~/components/TaskCard.vue'
import type { Task } from '~/types/api'

const task: Task = {
  id: 1,
  project_id: 1,
  title: 'Ship milestone 2',
  description: 'Board + Nuxt',
  status: 'todo',
  priority: 'high',
  position: 1024,
  due_date: '2026-07-01',
}

describe('TaskCard', () => {
  it('renders title, priority and due date', () => {
    render(TaskCard, { props: { task } })
    expect(screen.getByText('Ship milestone 2')).toBeTruthy()
    expect(screen.getByText('high')).toBeTruthy()
    expect(screen.getByText(/jul 1/i)).toBeTruthy()
  })

  it('omits the due date element when not set', () => {
    render(TaskCard, { props: { task: { ...task, due_date: null } } })
    expect(screen.queryByTestId('due-date')).toBeNull()
  })

  it('emits edit and delete', async () => {
    const { emitted, getByRole } = render(TaskCard, { props: { task } })
    getByRole('button', { name: /edit/i }).click()
    getByRole('button', { name: /delete/i }).click()
    expect(emitted()).toHaveProperty('edit')
    expect(emitted()).toHaveProperty('delete')
  })
})
