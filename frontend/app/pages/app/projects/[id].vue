<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import draggable from 'vuedraggable'

import { computePosition } from '~/utils/position'
import type { Project, ProjectSummary, Task, TaskStatus } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'app' })

const route = useRoute()
const projectId = Number(route.params.id)
const { api } = useAuth()
const queryClient = useQueryClient()
const { confirm } = useConfirm()
const { success, error } = useToast()

const { data: project } = useQuery({
  queryKey: ['project', projectId],
  queryFn: () => api<Project>(`/api/v1/projects/${projectId}`),
})
const { data: tasks, isPending } = useQuery({
  queryKey: ['tasks', projectId],
  queryFn: () => api<Task[]>(`/api/v1/projects/${projectId}/tasks`),
})
const { data: summary } = useQuery({
  queryKey: ['summary', projectId],
  queryFn: () => api<ProjectSummary>(`/api/v1/projects/${projectId}/summary`),
})

const statusColumns: { key: TaskStatus; label: string; tone: 'gray' | 'amber' | 'green' }[] = [
  { key: 'todo', label: 'To do', tone: 'gray' },
  { key: 'in_progress', label: 'In progress', tone: 'amber' },
  { key: 'done', label: 'Done', tone: 'green' },
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

const progress = computed(() => {
  if (!summary.value || !summary.value.tasks.total) return 0
  return Math.round((summary.value.tasks.done / summary.value.tasks.total) * 100)
})

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

// ── Inline quick-add (per column) ──────────────────────────────
const drafts = reactive<Record<TaskStatus, string>>({ todo: '', in_progress: '', done: '' })
const adding = ref<TaskStatus | null>(null)

async function quickAdd(status: TaskStatus) {
  const title = drafts[status].trim()
  if (!title) return
  drafts[status] = ''
  try {
    // tasks are created in `todo`; move to the target column if needed
    const created = await api<Task>(`/api/v1/projects/${projectId}/tasks`, {
      method: 'POST',
      body: { title },
    })
    if (status !== 'todo') {
      const last = columns[status][columns[status].length - 1]
      const position = computePosition(last?.position, undefined)
      await api<Task>(`/api/v1/tasks/${created.id}`, {
        method: 'PATCH',
        body: { status, position },
      })
    }
    invalidate()
  } catch {
    error('Could not add task')
  }
}

// ── Detailed create / edit drawer ──────────────────────────────
const showForm = ref(false)
const editing = ref<Task | null>(null)

function startEdit(t: Task) {
  editing.value = t
  showForm.value = true
}
function closeForm() {
  showForm.value = false
  editing.value = null
}

const saveTask = useMutation({
  mutationFn: (data: Record<string, unknown>) =>
    editing.value
      ? api<Task>(`/api/v1/tasks/${editing.value.id}`, { method: 'PATCH', body: data })
      : api<Task>(`/api/v1/projects/${projectId}/tasks`, { method: 'POST', body: data }),
  onSuccess: () => {
    invalidate()
    success(editing.value ? 'Task updated' : 'Task created')
    closeForm()
  },
  onError: () => error('Could not save task'),
})

const deleteTask = useMutation({
  mutationFn: (t: Task) => api(`/api/v1/tasks/${t.id}`, { method: 'DELETE' }),
  onSuccess: () => {
    invalidate()
    success('Task deleted')
  },
})

async function confirmDelete(t: Task) {
  const ok = await confirm({
    title: `Delete “${t.title}”?`,
    confirmLabel: 'Delete',
    danger: true,
  })
  if (ok) deleteTask.mutate(t)
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-5 py-8 md:px-8">
    <NuxtLink
      to="/app"
      class="mb-4 inline-flex items-center gap-1.5 text-sm text-ink-muted transition hover:text-ink"
    >
      <UiIcon name="chevron" :size="15" class="rotate-180" />
      Projects
    </NuxtLink>

    <header class="mb-7 flex flex-wrap items-start justify-between gap-4">
      <div class="flex items-start gap-3">
        <span
          class="mt-1 size-3.5 shrink-0 rounded-full"
          :style="{ backgroundColor: project?.color ?? '#6366f1' }"
          aria-hidden="true"
        />
        <div>
          <h1 class="text-2xl font-semibold tracking-tight text-ink">{{ project?.name ?? '…' }}</h1>
          <p v-if="project?.description" class="mt-1 max-w-xl text-sm text-ink-muted">
            {{ project.description }}
          </p>
        </div>
      </div>
      <UiButton variant="primary" icon="plus" @click="editing = null; showForm = true">New task</UiButton>
    </header>

    <!-- progress strip -->
    <div v-if="summary" class="mb-7 flex flex-wrap items-center gap-4 rounded-xl border border-line bg-surface p-4 shadow-card">
      <div class="flex items-center gap-2">
        <UiBadge tone="indigo">{{ summary.tasks.total }} tasks</UiBadge>
        <UiBadge tone="green" dot>{{ summary.tasks.done }} done</UiBadge>
      </div>
      <div class="flex flex-1 items-center gap-3 sm:min-w-48">
        <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-3">
          <div
            class="h-full rounded-full bg-accent transition-all duration-500"
            :style="{ width: `${progress}%` }"
          />
        </div>
        <span class="text-xs font-medium tabular-nums text-ink-muted">{{ progress }}%</span>
      </div>
    </div>

    <!-- board -->
    <div v-if="isPending" class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <div v-for="i in 3" :key="i" class="space-y-2 rounded-xl bg-surface-2 p-3">
        <UiSkeleton class="mb-3 h-4 w-24" />
        <UiSkeleton v-for="j in 3" :key="j" class="h-16 w-full rounded-lg" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <section
        v-for="col in statusColumns"
        :key="col.key"
        class="flex flex-col rounded-xl border border-line bg-surface-2/60 p-3"
      >
        <h2 class="mb-3 flex items-center gap-2 px-1 text-sm font-semibold text-ink">
          <span class="size-2 rounded-full" :class="{
            todo: 'bg-slate-400', in_progress: 'bg-amber-500', done: 'bg-green-500',
          }[col.key]" />
          {{ col.label }}
          <span class="ml-auto rounded-full bg-surface-3 px-2 py-0.5 text-xs font-medium text-ink-muted">
            {{ columns[col.key].length }}
          </span>
        </h2>

        <draggable
          :list="columns[col.key]"
          item-key="id"
          group="tasks"
          class="flex min-h-2 flex-1 flex-col gap-2"
          ghost-class="opacity-40"
          drag-class="rotate-2"
          animation="180"
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

        <p
          v-if="!columns[col.key].length"
          class="rounded-lg border border-dashed border-line py-6 text-center text-xs text-ink-subtle"
        >
          Drop tasks here
        </p>

        <!-- inline quick-add -->
        <div class="mt-2">
          <input
            v-model="drafts[col.key]"
            type="text"
            :placeholder="adding === col.key ? 'Task title, then Enter…' : '+ Add task'"
            class="w-full rounded-lg border border-transparent bg-transparent px-2.5 py-2 text-sm text-ink outline-none transition placeholder:text-ink-subtle focus:border-line focus:bg-surface focus:shadow-sm"
            @focus="adding = col.key"
            @blur="adding = null"
            @keydown.enter.prevent="quickAdd(col.key)"
          >
        </div>
      </section>
    </div>

    <UiModal
      :open="showForm"
      :title="editing ? 'Edit task' : 'New task'"
      :subtitle="editing ? 'Update task details.' : 'Add a task to this board.'"
      @close="closeForm"
    >
      <TaskForm
        v-if="showForm"
        :key="editing?.id ?? 'new'"
        :task="editing"
        :busy="saveTask.isPending.value"
        @submit="saveTask.mutate($event)"
        @cancel="closeForm"
      />
    </UiModal>
  </div>
</template>
