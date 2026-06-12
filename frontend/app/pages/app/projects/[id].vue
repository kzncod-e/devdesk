<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import draggable from 'vuedraggable'

import { computePosition } from '~/utils/position'
import type { Project, ProjectSummary, Task, TaskStatus } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const projectId = Number(route.params.id)
const { api } = useAuth()
const queryClient = useQueryClient()

const { data: project } = useQuery({
  queryKey: ['project', projectId],
  queryFn: () => api<Project>(`/api/v1/projects/${projectId}`),
})
const { data: tasks } = useQuery({
  queryKey: ['tasks', projectId],
  queryFn: () => api<Task[]>(`/api/v1/projects/${projectId}/tasks`),
})
const { data: summary } = useQuery({
  queryKey: ['summary', projectId],
  queryFn: () => api<ProjectSummary>(`/api/v1/projects/${projectId}/summary`),
})

const statusColumns: { key: TaskStatus; label: string }[] = [
  { key: 'todo', label: 'To do' },
  { key: 'in_progress', label: 'In progress' },
  { key: 'done', label: 'Done' },
]

// local mutable copies for vuedraggable; rebuilt whenever the query refetches
const columns = reactive<Record<TaskStatus, Task[]>>({ todo: [], in_progress: [], done: [] })
watch(
  tasks,
  (list) => {
    for (const col of statusColumns) {
      columns[col.key] = (list ?? [])
        .filter(t => t.status === col.key)
        .sort((a, b) => a.position - b.position)
    }
  },
  { immediate: true },
)

function invalidate() {
  queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
  queryClient.invalidateQueries({ queryKey: ['summary', projectId] })
}

const patchTask = useMutation({
  mutationFn: ({ id, body }: { id: number; body: Record<string, unknown> }) =>
    api<Task>(`/api/v1/tasks/${id}`, { method: 'PATCH', body }),
  onSuccess: invalidate,
})

type DragChange = {
  added?: { element: Task; newIndex: number }
  moved?: { element: Task; newIndex: number }
}

function onColumnChange(status: TaskStatus, evt: DragChange) {
  const change = evt.added ?? evt.moved
  if (!change) return
  const column = columns[status]
  const { element, newIndex } = change
  const position = computePosition(
    column[newIndex - 1]?.position,
    column[newIndex + 1]?.position,
  )
  element.position = position
  element.status = status
  patchTask.mutate({ id: element.id, body: { status, position } })
}

const showForm = ref(false)
const editing = ref<Task | null>(null)

const saveTask = useMutation({
  mutationFn: (data: Record<string, unknown>) =>
    editing.value
      ? api<Task>(`/api/v1/tasks/${editing.value.id}`, { method: 'PATCH', body: data })
      : api<Task>(`/api/v1/projects/${projectId}/tasks`, { method: 'POST', body: data }),
  onSuccess: () => {
    invalidate()
    showForm.value = false
    editing.value = null
  },
})

const deleteTask = useMutation({
  mutationFn: (t: Task) => api(`/api/v1/tasks/${t.id}`, { method: 'DELETE' }),
  onSuccess: invalidate,
})

function startEdit(t: Task) {
  editing.value = t
  showForm.value = true
}

function confirmDelete(t: Task) {
  if (window.confirm(`Delete task "${t.title}"?`)) deleteTask.mutate(t)
}
</script>

<template>
  <div>
    <AppHeader>
      <span class="text-slate-400">/</span>
      <span class="font-medium">{{ project?.name ?? '…' }}</span>
    </AppHeader>
    <main class="mx-auto max-w-6xl p-6">
      <div class="mb-6 flex flex-wrap items-center gap-3">
        <h1 class="text-2xl font-bold">Board</h1>
        <template v-if="summary">
          <UiBadge tone="indigo">{{ summary.tasks.total }} tasks</UiBadge>
          <UiBadge tone="green">{{ summary.tasks.done }} done</UiBadge>
        </template>
        <button
          class="ml-auto rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700"
          @click="editing = null; showForm = true"
        >
          New task
        </button>
      </div>

      <TaskForm
        v-if="showForm"
        :key="editing?.id ?? 'new'"
        :task="editing"
        :busy="saveTask.isPending.value"
        class="mb-6"
        @submit="saveTask.mutate($event)"
        @cancel="showForm = false; editing = null"
      />

      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <section
          v-for="col in statusColumns"
          :key="col.key"
          class="rounded-xl bg-slate-100 p-3"
        >
          <h2 class="mb-3 flex items-center gap-2 px-1 text-sm font-semibold text-slate-700">
            {{ col.label }}
            <span class="text-slate-400">{{ columns[col.key].length }}</span>
          </h2>
          <draggable
            :list="columns[col.key]"
            item-key="id"
            group="tasks"
            class="flex min-h-24 flex-col gap-2"
            @change="onColumnChange(col.key, $event)"
          >
            <template #item="{ element }">
              <TaskCard
                :task="element"
                @edit="startEdit(element)"
                @delete="confirmDelete(element)"
              />
            </template>
          </draggable>
        </section>
      </div>
    </main>
  </div>
</template>
