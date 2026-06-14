<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'

import type { Task, UserBrief } from '~/types/api'

const props = defineProps<{ task?: Task | null; busy?: boolean }>()
const emit = defineEmits<{
  submit: [data: { title: string; description: string; priority: string; due_date: string | null; assignee_ids: number[] }]
  cancel: []
}>()

const { api } = useAuth()

const title = ref(props.task?.title ?? '')
const description = ref(props.task?.description ?? '')
const priority = ref(props.task?.priority ?? 'medium')
const dueDate = ref(props.task?.due_date ?? '')
const assigneeIds = ref<number[]>(props.task?.assignees.map(a => a.id) ?? [])

const priorities = [
  { value: 'low', label: 'Low', tone: 'gray' as const },
  { value: 'medium', label: 'Medium', tone: 'amber' as const },
  { value: 'high', label: 'High', tone: 'red' as const },
]

const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: () => api<UserBrief[]>('/api/v1/users'),
})

function toggleAssignee(id: number) {
  const i = assigneeIds.value.indexOf(id)
  if (i === -1) assigneeIds.value.push(id)
  else assigneeIds.value.splice(i, 1)
}

function submit() {
  emit('submit', {
    title: title.value,
    description: description.value,
    priority: priority.value,
    due_date: dueDate.value || null,
    assignee_ids: assigneeIds.value,
  })
}
</script>

<template>
  <form class="flex flex-col gap-5" @submit.prevent="submit">
    <label class="flex flex-col gap-1.5">
      <span class="field-label">Title</span>
      <input v-model="title" type="text" required maxlength="200" placeholder="What needs doing?" class="field-input">
    </label>

    <label class="flex flex-col gap-1.5">
      <span class="field-label">Description</span>
      <textarea v-model="description" rows="4" placeholder="Add detail…" class="field-input resize-none" />
    </label>

    <div class="flex flex-col gap-2" role="group" aria-label="Priority">
      <span class="field-label">Priority</span>
      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="p in priorities"
          :key="p.value"
          type="button"
          :aria-pressed="priority === p.value"
          :class="[
            'rounded-lg border px-3 py-2 text-sm font-medium capitalize transition',
            priority === p.value
              ? 'border-accent bg-accent-soft text-accent'
              : 'border-line text-ink-muted hover:border-line-strong hover:bg-surface-2',
          ]"
          @click="priority = p.value"
        >
          {{ p.label }}
        </button>
      </div>
    </div>

    <label class="flex flex-col gap-1.5">
      <span class="field-label">Due date</span>
      <input v-model="dueDate" type="date" class="field-input">
    </label>

    <div v-if="(users ?? []).length" class="flex flex-col gap-2" role="group" aria-label="Assignees">
      <span class="field-label">Assignees</span>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="u in users"
          :key="u.id"
          type="button"
          :aria-pressed="assigneeIds.includes(u.id)"
          :class="[
            'flex items-center gap-2 rounded-full border py-1 pl-1 pr-3 text-sm transition',
            assigneeIds.includes(u.id)
              ? 'border-accent bg-accent-soft text-accent'
              : 'border-line text-ink-muted hover:border-line-strong hover:bg-surface-2',
          ]"
          @click="toggleAssignee(u.id)"
        >
          <UiAvatar :user="u" :size="22" />
          {{ u.name }}
        </button>
      </div>
    </div>

    <div class="flex justify-end gap-2 pt-4">
      <UiButton variant="ghost" type="button" @click="emit('cancel')">Cancel</UiButton>
      <UiButton variant="primary" type="submit" :loading="busy" icon="check">
        {{ props.task ? 'Save changes' : 'Create task' }}
      </UiButton>
    </div>
  </form>
</template>
