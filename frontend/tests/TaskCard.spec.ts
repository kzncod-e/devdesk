import { fireEvent, render, screen } from '@testing-library/vue'
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
  assignees: [],
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

  it('emits edit and delete from the actions menu', async () => {
    const { emitted, getByLabelText, getByText } = render(TaskCard, { props: { task } })
    // Open the ⋯ menu, then trigger each item (menu closes after a click, so reopen).
    await fireEvent.click(getByLabelText('Task actions'))
    await fireEvent.click(getByText('Edit task'))
    await fireEvent.click(getByLabelText('Task actions'))
    await fireEvent.click(getByText('Delete task'))
    expect(emitted()).toHaveProperty('edit')
    expect(emitted()).toHaveProperty('delete')
  })

  it('renders an assignee avatar stack', () => {
    render(TaskCard, {
      props: {
        task: {
          ...task,
          assignees: [
            { id: 1, name: 'Ada Lovelace', avatar_url: null },
            { id: 2, name: 'Alan Turing', avatar_url: null },
          ],
        },
      },
    })
    // Initials fallback renders for users without an avatar image.
    expect(screen.getByText('AL')).toBeTruthy()
    expect(screen.getByText('AT')).toBeTruthy()
  })
})
