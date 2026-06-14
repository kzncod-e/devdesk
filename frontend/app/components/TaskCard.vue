<script setup lang="ts">
import { computed } from 'vue'

import UiBadge from '~/components/UiBadge.vue'
import UiAvatar from '~/components/UiAvatar.vue'
import UiMenu from '~/components/UiMenu.vue'
import UiMenuItem from '~/components/UiMenuItem.vue'
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
  return new Date(`${props.task.due_date}T00:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })
})

// Show at most 3 avatars; the rest collapse into a +N chip.
const MAX_AVATARS = 3
const shownAssignees = computed(() => props.task.assignees.slice(0, MAX_AVATARS))
const extraAssignees = computed(() => Math.max(0, props.task.assignees.length - MAX_AVATARS))

const commentCount = computed(() => props.task.comment_count ?? 0)
const attachmentCount = computed(() => props.task.attachment_count ?? 0)
const hasFooter = computed(
  () =>
    props.task.assignees.length > 0 ||
    !!dueLabel.value ||
    commentCount.value > 0 ||
    attachmentCount.value > 0,
)
</script>

<template>
  <article
    class="group relative flex cursor-grab flex-col gap-2.5 rounded-xl border border-line bg-surface p-3 shadow-card transition-all duration-150 hover:border-line-strong hover:shadow-card-hover active:cursor-grabbing"
  >
    <header class="flex items-center gap-2">
      <UiBadge :tone="priorityTone[task.priority]" class="capitalize">
        <UiIcon name="flag" :size="11" />
        {{ task.priority }}
      </UiBadge>
      <UiMenu align="right" class="ml-auto">
        <template #trigger>
          <button
            type="button"
            class="grid size-7 place-items-center rounded-md text-ink-subtle opacity-0 transition hover:bg-surface-3 hover:text-ink-muted focus-within:opacity-100 group-hover:opacity-100"
            aria-label="Task actions"
          >
            <UiIcon name="more" :size="16" />
          </button>
        </template>
        <UiMenuItem icon="edit" @click="$emit('edit')">Edit task</UiMenuItem>
        <UiMenuItem icon="trash" danger @click="$emit('delete')">Delete task</UiMenuItem>
      </UiMenu>
    </header>

    <h3 class="text-sm font-semibold leading-snug text-ink">{{ task.title }}</h3>
    <p v-if="task.description" class="line-clamp-2 text-xs leading-relaxed text-ink-subtle">
      {{ task.description }}
    </p>

    <footer v-if="hasFooter" class="flex items-center gap-3 border-t border-line pt-2.5">
      <!-- Assignee avatar stack -->
      <div v-if="task.assignees.length" class="flex items-center -space-x-1.5">
        <UiAvatar
          v-for="a in shownAssignees"
          :key="a.id"
          :user="a"
          :size="22"
        />
        <span
          v-if="extraAssignees"
          class="inline-grid size-5.5 shrink-0 place-items-center rounded-full bg-surface-3 text-[10px] font-semibold text-ink-muted ring-2 ring-surface"
        >
          +{{ extraAssignees }}
        </span>
      </div>

      <div class="ml-auto flex items-center gap-3 text-xs text-ink-subtle">
        <span v-if="attachmentCount" class="inline-flex items-center gap-1">
          <UiIcon name="paperclip" :size="13" />
          {{ attachmentCount }}
        </span>
        <span v-if="commentCount" class="inline-flex items-center gap-1">
          <UiIcon name="comment" :size="13" />
          {{ commentCount }}
        </span>
        <span
          v-if="dueLabel"
          data-testid="due-date"
          class="inline-flex items-center gap-1"
        >
          <UiIcon name="calendar" :size="12" />
          {{ dueLabel }}
        </span>
      </div>
    </footer>
  </article>
</template>
