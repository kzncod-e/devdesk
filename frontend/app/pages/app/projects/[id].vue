<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import draggable from 'vuedraggable'

import { computePosition } from '~/utils/position'
import type { Project, ProjectSummary, Task, TaskStatus } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'app' })

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const { api } = useAuth()
const queryClient = useQueryClient()
const { confirm } = useConfirm()
const { success, error } = useToast()

// Side-panel: open task detail in a drawer without leaving the board.
const openTaskId = ref<number | null>(null)
function onTaskDeleted() {
  openTaskId.value = null
  queryClient.invalidateQueries({ queryKey: ['tasks', projectId.value] })
  queryClient.invalidateQueries({ queryKey: ['summary', projectId.value] })
}

const { data: project } = useQuery({
  queryKey: computed(() => ['project', projectId.value]),
  queryFn: () => api<Project>(`/api/v1/projects/${projectId.value}`),
  enabled: computed(() => route.path.startsWith('/app/projects/') && !isNaN(projectId.value)),
})

const { workspaceId, setCurrent: setWorkspace } = useWorkspace()
watch(project, (p) => {
  if (p && p.workspace_id && p.workspace_id !== workspaceId.value) {
    setWorkspace(p.workspace_id)
  }
})
const { data: tasks, isPending } = useQuery({
  queryKey: computed(() => ['tasks', projectId.value]),
  queryFn: () => api<Task[]>(`/api/v1/projects/${projectId.value}/tasks`),
  enabled: computed(() => route.path.startsWith('/app/projects/') && !isNaN(projectId.value)),
})
const { data: summary } = useQuery({
  queryKey: computed(() => ['summary', projectId.value]),
  queryFn: () => api<ProjectSummary>(`/api/v1/projects/${projectId.value}/summary`),
  enabled: computed(() => route.path.startsWith('/app/projects/') && !isNaN(projectId.value)),
})

const statusColumns: { key: TaskStatus; label: string; dot: string; bar: string }[] = [
  { key: 'todo', label: 'To do', dot: 'bg-zinc-500', bar: 'bg-zinc-500/10' },
  { key: 'in_progress', label: 'In progress', dot: 'bg-amber-500', bar: 'bg-amber-500/10' },
  { key: 'done', label: 'Done', dot: 'bg-emerald-500', bar: 'bg-emerald-500/10' },
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

const view = ref<'board' | 'list'>('board')
const views = [
  { key: 'board', label: 'Board', icon: 'board' },
  { key: 'list', label: 'List', icon: 'list' },
] as const

function invalidate() {
  queryClient.invalidateQueries({ queryKey: ['tasks', projectId.value] })
  queryClient.invalidateQueries({ queryKey: ['summary', projectId.value] })
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
    const created = await api<Task>(`/api/v1/projects/${projectId.value}/tasks`, {
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
  mutationFn: async (data: Record<string, unknown>) => {
    const { assignee_ids = [], ...fields } = data as { assignee_ids?: number[] }
    if (editing.value) {
      // PATCH covers scalar fields; assignees live on a separate endpoint.
      const task = await api<Task>(`/api/v1/tasks/${editing.value.id}`, { method: 'PATCH', body: fields })
      await api<Task>(`/api/v1/tasks/${editing.value.id}/assignees`, {
        method: 'PUT',
        body: { user_ids: assignee_ids },
      })
      return task
    }
    // Create accepts assignee_ids directly in the body.
    return api<Task>(`/api/v1/projects/${projectId.value}/tasks`, {
      method: 'POST',
      body: { ...fields, assignee_ids },
    })
  },
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
    <nav class="mb-4 flex items-center gap-1.5 text-sm text-ink-muted">
      <NuxtLink to="/app" class="transition hover:text-ink">Projects</NuxtLink>
      <UiIcon name="chevron" :size="14" class="text-ink-subtle" />
      <span class="font-medium text-ink">{{ project?.name ?? '…' }}</span>
    </nav>

    <header class="mb-7 flex flex-wrap items-start justify-between gap-4">
      <div class="flex items-start gap-3">
        <ProjectAvatar :name="project?.name" :size="28" class="mt-0.5" />
        <div>
          <h1 class="text-title">{{ project?.name ?? '…' }}</h1>
          <p v-if="project?.description" class="mt-1 max-w-xl text-sm text-ink-muted">
            {{ project.description }}
          </p>
        </div>
      </div>
      <UiButton variant="primary" icon="plus" @click="editing = null; showForm = true">New task</UiButton>
    </header>

    <!-- progress strip -->
    <div v-if="summary" class="mb-7 flex flex-wrap items-center gap-4 rounded-card border border-line bg-surface p-4 shadow-card">
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

    <!-- view tabs -->
    <div class="mb-5 flex items-center gap-1 border-b border-line">
      <button
        v-for="v in views"
        :key="v.key"
        type="button"
        :class="[
          'flex items-center gap-2 border-b-2 px-3 pb-2.5 pt-1 text-sm font-medium transition-colors',
          view === v.key
            ? 'border-accent text-ink'
            : 'border-transparent text-ink-muted hover:text-ink',
        ]"
        @click="view = v.key"
      >
        <UiIcon :name="v.icon" :size="16" />
        {{ v.label }}
      </button>
    </div>

    <!-- loading skeleton (shared by both views) -->
    <div v-if="isPending" class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <div v-for="i in 3" :key="i" class="space-y-2 rounded-card bg-surface-2 p-3">
        <UiSkeleton class="mb-3 h-4 w-24" />
        <UiSkeleton v-for="j in 3" :key="j" class="h-16 w-full rounded-lg" />
      </div>
    </div>

    <!-- board view -->
    <div v-else-if="view === 'board'" class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <section
        v-for="col in statusColumns"
        :key="col.key"
        class="flex flex-col rounded-card border border-line bg-surface-2/40 p-3"
      >
        <!-- Column Header -->
        <div class="mb-3 flex items-center gap-2 px-1.5 py-1 select-none">
          <span :class="['size-2 rounded-full', col.dot]" />
          <span class="text-sm font-semibold text-ink">{{ col.label }}</span>
          <span class="text-xs text-ink-subtle font-normal tabular">({{ columns[col.key].length }})</span>
        </div>

        <draggable
          :list="columns[col.key]"
          item-key="id"
          group="tasks"
          class="flex min-h-[160px] flex-1 flex-col gap-2"
          ghost-class="opacity-40"
          drag-class="rotate-2"
          animation="180"
          @change="onColumnChange(col.key, $event)"
        >
          <template #item="{ element }">
            <TaskCard
              :task="element"
              :project-key="project?.key"
              @open="openTaskId = element.id"
              @edit="startEdit(element)"
              @delete="confirmDelete(element)"
            />
          </template>
        </draggable>

        <!-- Empty State Column Placeholder -->
        <div
          v-if="!columns[col.key].length"
          class="flex flex-col items-center justify-center border border-dashed border-line rounded-lg py-8 px-4 text-center select-none bg-surface/20 my-2"
        >
          <UiIcon name="inbox" :size="14" class="text-ink-subtle mb-1" />
          <p class="text-xs font-semibold text-ink-muted">No tasks yet</p>
          <p class="text-[10px] text-ink-subtle mt-0.5">Drag tasks here or add below</p>
        </div>

        <!-- inline quick-add -->
        <div class="mt-2">
          <input
            v-model="drafts[col.key]"
            type="text"
            :aria-label="`Add a task to ${col.label}`"
            :placeholder="adding === col.key ? 'Task title, then Enter…' : '+ Add task'"
            class="w-full rounded-lg border border-transparent bg-transparent px-2.5 py-2 text-sm text-ink outline-none transition placeholder:text-ink-subtle focus:border-line focus:bg-surface focus:shadow-sm"
            @focus="adding = col.key"
            @blur="adding = null"
            @keydown.enter.prevent="quickAdd(col.key)"
          >
        </div>
      </section>
    </div>

    <!-- list view -->
    <div v-else class="overflow-hidden rounded-card border border-line bg-surface shadow-card">
      <template v-for="col in statusColumns" :key="col.key">
        <div
          v-if="columns[col.key].length"
          :class="['flex items-center gap-2 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-ink-muted', col.bar]"
        >
          <span :class="['size-2 rounded-full', col.dot]" />
          {{ col.label }}
          <span class="text-ink-subtle">· {{ columns[col.key].length }}</span>
        </div>
        <button
          v-for="task in columns[col.key]"
          :key="task.id"
          type="button"
          class="flex w-full items-center gap-3 border-b border-line px-4 py-3 text-left transition last:border-b-0 hover:bg-surface-2"
          @click="openTaskId = task.id"
        >
          <UiBadge :tone="{ low: 'gray', medium: 'amber', high: 'red' }[task.priority]" class="shrink-0 capitalize">
            <UiIcon name="flag" :size="11" />
            {{ task.priority }}
          </UiBadge>
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span class="font-mono text-xs text-ink-subtle shrink-0 select-all">{{ taskRef(project?.key, task.number, task.id) }}</span>
            <span class="truncate text-sm font-medium text-ink">{{ task.title }}</span>
          </div>
          <span
            v-if="task.due_date"
            class="hidden items-center gap-1 text-xs text-ink-subtle sm:inline-flex"
          >
            <UiIcon name="calendar" :size="12" />
            {{ new Date(`${task.due_date}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) }}
          </span>
          <div v-if="task.assignees.length" class="flex shrink-0 items-center -space-x-1.5">
            <UiAvatar v-for="a in task.assignees.slice(0, 3)" :key="a.id" :user="a" :size="22" />
          </div>
        </button>
      </template>
      <p v-if="!tasks?.length" class="px-4 py-10 text-center text-sm text-ink-subtle">
        No tasks yet.
      </p>
    </div>

    <UiModal
      :open="showForm"
      no-header
      width="max-w-2xl"
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

    <!-- Task detail side-panel -->
    <UiDrawer
      :open="openTaskId !== null"
      width="max-w-2xl"
      @close="openTaskId = null"
    >
      <TaskDetail
        v-if="openTaskId !== null"
        :key="openTaskId"
        :task-id="openTaskId"
        compact
        @close="openTaskId = null"
        @deleted="onTaskDeleted"
      />
    </UiDrawer>
  </div>
</template>
