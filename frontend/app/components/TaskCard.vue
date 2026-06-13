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
    class="group relative flex cursor-grab flex-col gap-2 rounded-xl border border-line bg-surface p-3 shadow-card transition-all duration-150 hover:border-line-strong hover:shadow-card-hover active:cursor-grabbing"
  >
    <div class="flex items-start gap-2">
      <h3 class="flex-1 text-sm font-medium leading-snug text-ink">{{ task.title }}</h3>
      <div class="flex shrink-0 gap-0.5 opacity-0 transition-opacity duration-150 focus-within:opacity-100 group-hover:opacity-100">
        <button type="button" class="icon-btn" aria-label="Edit task" @click.stop="$emit('edit')">
          <UiIcon name="edit" :size="14" />
        </button>
        <button type="button" class="icon-btn icon-btn-danger" aria-label="Delete task" @click.stop="$emit('delete')">
          <UiIcon name="trash" :size="14" />
        </button>
      </div>
    </div>
    <p v-if="task.description" class="line-clamp-2 text-xs leading-relaxed text-ink-subtle">
      {{ task.description }}
    </p>
    <footer class="flex items-center gap-2">
      <UiBadge :tone="priorityTone[task.priority]" dot>{{ task.priority }}</UiBadge>
      <span
        v-if="dueLabel"
        data-testid="due-date"
        class="inline-flex items-center gap-1 text-xs text-ink-subtle"
      >
        <UiIcon name="calendar" :size="12" />
        {{ dueLabel }}
      </span>
    </footer>
  </article>
</template>
