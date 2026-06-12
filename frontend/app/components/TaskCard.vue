<script setup lang="ts">
import { computed } from 'vue'

import UiBadge from '~/components/UiBadge.vue'
import type { Task, TaskPriority } from '~/types/api'

const props = defineProps<{ task: Task }>()
defineEmits<{ edit: []; delete: [] }>()

const priorityTone: Record<TaskPriority, 'gray' | 'amber' | 'red'> = {
  low: 'gray',
  medium: 'amber',
  high: 'red',
}

const dueLabel = computed(() => {
  if (!props.task.due_date) return null
  return new Date(`${props.task.due_date}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
})
</script>

<template>
  <article
    class="group flex cursor-grab flex-col gap-2 rounded-lg border border-slate-200 bg-white p-3 shadow-sm active:cursor-grabbing"
  >
    <div class="flex items-start gap-2">
      <h3 class="flex-1 text-sm font-medium">{{ task.title }}</h3>
      <div class="hidden gap-1 group-hover:flex">
        <button
          class="rounded px-1 text-xs text-slate-500 hover:bg-slate-100"
          aria-label="Edit task"
          @click="$emit('edit')"
        >
          Edit
        </button>
        <button
          class="rounded px-1 text-xs text-red-500 hover:bg-red-50"
          aria-label="Delete task"
          @click="$emit('delete')"
        >
          Delete
        </button>
      </div>
    </div>
    <p v-if="task.description" class="line-clamp-2 text-xs text-slate-500">
      {{ task.description }}
    </p>
    <footer class="flex items-center gap-2">
      <UiBadge :tone="priorityTone[task.priority]">{{ task.priority }}</UiBadge>
      <span v-if="dueLabel" data-testid="due-date" class="text-xs text-slate-500">
        {{ dueLabel }}
      </span>
    </footer>
  </article>
</template>
