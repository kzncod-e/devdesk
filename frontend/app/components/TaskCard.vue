<script setup lang="ts">
import { computed } from 'vue'

import UiBadge from '~/components/UiBadge.vue'
import UiAvatar from '~/components/UiAvatar.vue'
import UiMenu from '~/components/UiMenu.vue'
import UiMenuItem from '~/components/UiMenuItem.vue'
import type { Task, TaskPriority } from '~/types/api'

const props = defineProps<{ task: Task }>()
defineEmits<{ edit: []; delete: [] }>()

function navigateToTask(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target.closest('button') || target.closest('a') || target.closest('[role="menu"]')) {
    return
  }
  navigateTo(`/app/tasks/${props.task.id}`)
}

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

function formatTaskId(id: number) {
  return `TASK-${String(id).padStart(3, '0')}`
}

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
    class="group relative flex cursor-pointer cursor-grab flex-col gap-2 rounded-lg border border-line bg-surface p-3.5 shadow-card transition-all duration-200 ease-[var(--ease-out-soft)] hover:-translate-y-0.5 hover:border-line-strong hover:shadow-card-hover active:cursor-grabbing"
    @click="navigateToTask"
  >
    <!-- Top Row: ID, Priority, Options -->
    <div class="flex items-center justify-between gap-2">
      <div class="flex items-center gap-1.5">
        <span class="font-mono text-[10px] font-semibold tracking-wider text-ink-subtle">
          {{ formatTaskId(task.id) }}
        </span>
        <span class="text-line-strong font-normal text-[10px] select-none">|</span>
        <UiBadge :tone="priorityTone[task.priority]" class="capitalize !py-0.5 !px-1.5 !text-[9px]">
          {{ task.priority }}
        </UiBadge>
      </div>

      <!-- Actions -->
      <UiMenu align="right">
        <template #trigger>
          <button
            type="button"
            class="grid size-5 place-items-center rounded text-ink-subtle opacity-0 transition hover:bg-surface-2 hover:text-ink-muted focus-within:opacity-100 group-hover:opacity-100"
            aria-label="Task actions"
          >
            <UiIcon name="more" :size="12" />
          </button>
        </template>
        <UiMenuItem icon="edit" @click="$emit('edit')">Edit task</UiMenuItem>
        <UiMenuItem icon="trash" danger @click="$emit('delete')">Delete task</UiMenuItem>
      </UiMenu>
    </div>

    <!-- Middle Section: Title & Description -->
    <div class="space-y-1">
      <h3 class="text-xs font-semibold leading-snug text-ink group-hover:text-accent transition-colors duration-150">
        {{ task.title }}
      </h3>
      <p v-if="task.description" class="line-clamp-2 text-[11px] leading-relaxed text-ink-subtle">
        {{ task.description }}
      </p>
    </div>

    <!-- Bottom Section: Assignees, Due Date, Metadata -->
    <div v-if="hasFooter" class="flex items-center justify-between border-t border-line/50 pt-2 mt-1">
      <!-- Assignee avatar stack -->
      <div v-if="task.assignees.length" class="flex items-center -space-x-1">
        <UiAvatar
          v-for="a in shownAssignees"
          :key="a.id"
          :user="a"
          :size="18"
          class="ring-1 ring-surface"
        />
        <span
          v-if="extraAssignees"
          class="inline-grid size-4.5 shrink-0 place-items-center rounded-full bg-surface-3 text-[8px] font-semibold text-ink-muted ring-1 ring-surface"
        >
          +{{ extraAssignees }}
        </span>
      </div>
      <div v-else />

      <!-- Due date & Metadata -->
      <div class="flex items-center gap-2.5 text-[10px] text-ink-subtle">
        <span v-if="attachmentCount" class="inline-flex items-center gap-0.5" title="Attachments">
          <UiIcon name="paperclip" :size="10" />
          <span class="font-medium">{{ attachmentCount }}</span>
        </span>
        <span v-if="commentCount" class="inline-flex items-center gap-0.5" title="Comments">
          <UiIcon name="comment" :size="10" />
          <span class="font-medium">{{ commentCount }}</span>
        </span>
        <span
          v-if="dueLabel"
          data-testid="due-date"
          class="inline-flex items-center gap-1 rounded bg-surface-2 px-1.5 py-0.5 border border-line"
        >
          <UiIcon name="calendar" :size="10" />
          <span class="font-medium">{{ dueLabel }}</span>
        </span>
      </div>
    </div>
  </article>
</template>
