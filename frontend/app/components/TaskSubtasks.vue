<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Task } from '~/types/api'

const props = defineProps<{ taskId: number; projectId: number; projectKey?: string | null }>()

const { api } = useAuth()
const queryClient = useQueryClient()
const { error } = useToast()

const key = computed(() => ['subtasks', props.taskId])

const { data: subtasks } = useQuery({
  queryKey: key,
  queryFn: () => api<Task[]>(`/api/v1/tasks/${props.taskId}/subtasks`),
  enabled: computed(() => !isNaN(props.taskId)),
})

const done = computed(() => (subtasks.value ?? []).filter((t) => t.status === 'done').length)
const total = computed(() => subtasks.value?.length ?? 0)

function invalidate() {
  queryClient.invalidateQueries({ queryKey: key.value })
  queryClient.invalidateQueries({ queryKey: ['tasks'] })
}

const draft = ref('')
const addMut = useMutation({
  mutationFn: (title: string) =>
    api<Task>(`/api/v1/projects/${props.projectId}/tasks`, {
      method: 'POST',
      body: { title, parent_task_id: props.taskId },
    }),
  onSuccess: () => { draft.value = ''; invalidate() },
  onError: () => error('Could not add sub-task'),
})
function add() {
  const t = draft.value.trim()
  if (t && !addMut.isPending.value) addMut.mutate(t)
}

const toggleMut = useMutation({
  mutationFn: (s: Task) =>
    api<Task>(`/api/v1/tasks/${s.id}`, {
      method: 'PATCH',
      body: { status: s.status === 'done' ? 'todo' : 'done' },
    }),
  onSuccess: invalidate,
  onError: () => error('Could not update sub-task'),
})
</script>

<template>
  <section class="space-y-2.5">
    <div class="flex items-center gap-2">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-ink-subtle">Sub-tasks</h3>
      <span v-if="total" class="text-meta tabular">{{ done }}/{{ total }}</span>
    </div>

    <ul v-if="total" class="divide-y divide-line rounded-card border border-line">
      <li v-for="s in subtasks" :key="s.id" class="group flex items-center gap-2.5 px-3 py-2">
        <button
          type="button"
          class="grid size-4 shrink-0 place-items-center rounded-[5px] border transition"
          :class="s.status === 'done' ? 'border-accent bg-accent text-accent-fg' : 'border-line-strong hover:border-ink-subtle'"
          :aria-label="s.status === 'done' ? 'Mark not done' : 'Mark done'"
          @click="toggleMut.mutate(s)"
        >
          <UiIcon v-if="s.status === 'done'" name="check" :size="11" />
        </button>
        <span class="shrink-0 font-mono text-[11px] text-ink-subtle">{{ taskRef(projectKey, s.number, s.id) }}</span>
        <NuxtLink
          :to="`/app/tasks/${s.id}`"
          class="min-w-0 flex-1 truncate text-sm transition hover:text-accent"
          :class="s.status === 'done' ? 'text-ink-subtle line-through' : 'text-ink'"
        >
          {{ s.title }}
        </NuxtLink>
      </li>
    </ul>

    <div class="flex items-center gap-2">
      <input
        v-model="draft"
        type="text"
        placeholder="Add a sub-task…"
        class="field-input h-8 flex-1"
        @keydown.enter.prevent="add"
      />
      <UiButton variant="secondary" size="sm" :loading="addMut.isPending.value" :disabled="!draft.trim()" @click="add">
        Add
      </UiButton>
    </div>
  </section>
</template>
