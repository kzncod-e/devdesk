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
    <header class="flex items-center gap-2">
      <UiBadge :tone="priorityTone[task.priority]" class="capitalize">
        <UiIcon name="flag" :size="11" />
        {{ task.priority }}
      </UiBadge>
      <div class="ml-auto flex shrink-0 gap-0.5 opacity-0 transition-opacity duration-150 focus-within:opacity-100 group-hover:opacity-100">
        <button type="button" class="icon-btn" aria-label="Edit task" @click.stop="$emit('edit')">
          <UiIcon name="edit" :size="14" />
        </button>
        <button type="button" class="icon-btn icon-btn-danger" aria-label="Delete task" @click.stop="$emit('delete')">
          <UiIcon name="trash" :size="14" />
        </button>
      </div>
    </header>
    <h3 class="text-sm font-semibold leading-snug text-ink">{{ task.title }}</h3>
    <p v-if="task.description" class="line-clamp-2 text-xs leading-relaxed text-ink-subtle">
      {{ task.description }}
    </p>
    <footer v-if="dueLabel" class="flex items-center gap-2 border-t border-line pt-2">
      <span
        data-testid="due-date"
        class="inline-flex items-center gap-1 text-xs text-ink-subtle"
      >
        <UiIcon name="calendar" :size="12" />
        {{ dueLabel }}
      </span>
    </footer>
  </article>
</template>
