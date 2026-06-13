<script setup lang="ts">
import type { Task } from '~/types/api'

const props = defineProps<{ task?: Task | null; busy?: boolean }>()
const emit = defineEmits<{
  submit: [data: { title: string; description: string; priority: string; due_date: string | null }]
  cancel: []
}>()

const title = ref(props.task?.title ?? '')
const description = ref(props.task?.description ?? '')
const priority = ref(props.task?.priority ?? 'medium')
const dueDate = ref(props.task?.due_date ?? '')

const priorities = [
  { value: 'low', label: 'Low', tone: 'gray' as const },
  { value: 'medium', label: 'Medium', tone: 'amber' as const },
  { value: 'high', label: 'High', tone: 'red' as const },
]

function submit() {
  emit('submit', {
    title: title.value,
    description: description.value,
    priority: priority.value,
    due_date: dueDate.value || null,
  })
}
</script>

<template>
  <form class="flex flex-col gap-5" @submit.prevent="submit">
    <div class="flex flex-col gap-1.5">
      <label class="field-label">Title</label>
      <input v-model="title" type="text" required maxlength="200" placeholder="What needs doing?" class="field-input">
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="field-label">Description</label>
      <textarea v-model="description" rows="4" placeholder="Add detail…" class="field-input resize-none" />
    </div>

    <div class="flex flex-col gap-2">
      <label class="field-label">Priority</label>
      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="p in priorities"
          :key="p.value"
          type="button"
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

    <div class="flex flex-col gap-1.5">
      <label class="field-label">Due date</label>
      <input v-model="dueDate" type="date" class="field-input">
    </div>

    <div class="flex justify-end gap-2 pt-4">
      <UiButton variant="ghost" type="button" @click="emit('cancel')">Cancel</UiButton>
      <UiButton variant="primary" type="submit" :loading="busy" icon="check">
        {{ props.task ? 'Save changes' : 'Create task' }}
      </UiButton>
    </div>
  </form>
</template>
