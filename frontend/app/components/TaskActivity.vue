<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import type { Activity, ActivityPage } from '~/types/api'

const props = defineProps<{ taskId: number }>()
const { api } = useAuth()

const { data, isPending } = useQuery({
  queryKey: computed(() => ['task-activity', props.taskId]),
  queryFn: () => api<ActivityPage>(`/api/v1/tasks/${props.taskId}/activity?limit=50`),
  enabled: computed(() => !isNaN(props.taskId)),
})

const items = computed(() => data.value?.items ?? [])

const VERB_ICON: Record<string, string> = {
  created: 'plus',
  updated: 'edit',
  status_changed: 'check-circle',
  assignees_changed: 'user',
  commented: 'comment',
  deleted: 'trash',
}
const icon = (verb: string) => VERB_ICON[verb] ?? 'activity'

function label(a: Activity): string {
  if (a.verb === 'commented') return 'commented'
  if (a.verb === 'status_changed') {
    const s = (a.metadata?.status as string) ?? ''
    return s ? `moved to ${s.replace('_', ' ')}` : 'changed status'
  }
  if (a.verb === 'assignees_changed') return 'updated assignees'
  if (a.verb === 'created') return 'created this task'
  return a.verb.replace(/_/g, ' ')
}

function timeAgo(iso: string): string {
  const s = Math.max(1, Math.floor((Date.now() - new Date(iso).getTime()) / 1000))
  if (s < 60) return 'just now'
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24)
  if (d < 7) return `${d}d ago`
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div>
    <div v-if="isPending" class="space-y-3">
      <div v-for="i in 3" :key="i" class="flex items-center gap-3">
        <UiSkeleton class="size-6 shrink-0 rounded-full" />
        <UiSkeleton class="h-3 w-48" />
      </div>
    </div>

    <p v-else-if="!items.length" class="py-6 text-center text-sm text-ink-subtle">
      No activity yet.
    </p>

    <ol v-else class="relative space-y-1 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-px before:bg-line">
      <li v-for="a in items" :key="a.id" class="relative flex items-start gap-3 py-1.5">
        <span class="z-10 mt-0.5 grid size-6 shrink-0 place-items-center rounded-full border border-line bg-surface text-ink-subtle">
          <UiIcon :name="icon(a.verb)" :size="12" />
        </span>
        <p class="text-sm leading-6 text-ink-muted">
          <span class="font-medium text-ink">{{ a.actor_name ?? 'Someone' }}</span>
          {{ ' ' }}{{ label(a) }}
          <span class="text-meta">· {{ timeAgo(a.created_at) }}</span>
        </p>
      </li>
    </ol>
  </div>
</template>
