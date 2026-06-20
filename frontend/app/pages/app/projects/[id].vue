<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import draggable from 'vuedraggable'

import { computePosition } from '~/utils/position'
import type { Project, ProjectSummary, Task, TaskStatus, WorkflowState } from '~/types/api'

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

// Per-project board columns (custom workflow states).
const { data: states } = useQuery({
  queryKey: computed(() => ['states', projectId.value]),
  queryFn: () => api<WorkflowState[]>(`/api/v1/projects/${projectId.value}/states`),
  enabled: computed(() => route.path.startsWith('/app/projects/') && !isNaN(projectId.value)),
})

// Fallback dot colour by category when a state has no explicit colour.
const categoryDot: Record<TaskStatus, string> = {
  todo: 'bg-zinc-500', in_progress: 'bg-amber-500', done: 'bg-emerald-500',
}
function dotStyle(s: WorkflowState) {
  return s.color ? { backgroundColor: s.color } : undefined
}

// local mutable copies for vuedraggable, keyed by state id; rebuilt on refetch
const columns = reactive<Record<number, Task[]>>({})
function rebuildColumns() {
  const sts = states.value ?? []
  const list = tasks.value ?? []
  for (const k of Object.keys(columns)) delete columns[Number(k)]
  if (!sts.length) return
  const known = new Set(sts.map(s => s.id))
  for (const s of sts) columns[s.id] = []
  for (const t of list) {
    // place by state_id; orphans fall into a same-category column, else the first
    const target = (t.state_id && known.has(t.state_id))
      ? t.state_id
      : (sts.find(s => s.category === t.status) ?? sts[0]!).id
    columns[target]!.push(t)
  }
  for (const s of sts) columns[s.id]!.sort((a, b) => a.position - b.position)
}
watch([tasks, states], rebuildColumns, { immediate: true })

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

function onColumnChange(stateId: number, evt: DragChange) {
  const change = evt.added ?? evt.moved
  if (!change) return
  const column = columns[stateId] ?? []
  const { element, newIndex } = change
  const position = computePosition(
    column[newIndex - 1]?.position,
    column[newIndex + 1]?.position,
  )
  element.position = position
  element.state_id = stateId
  patchTask.mutate({ id: element.id, body: { state_id: stateId, position } })
}

// ── Inline quick-add (per column, keyed by state id) ──────────────────────────
const drafts = reactive<Record<number, string>>({})
const adding = ref<number | null>(null)

async function quickAdd(stateId: number) {
  const title = (drafts[stateId] ?? '').trim()
  if (!title) return
  drafts[stateId] = ''
  try {
    await api<Task>(`/api/v1/projects/${projectId.value}/tasks`, {
      method: 'POST',
      body: { title, state_id: stateId },
    })
    invalidate()
  } catch {
    error('Could not add task')
  }
}

// ── Workflow state (column) editor ────────────────────────────────────────────
function invalidateStates() {
  queryClient.invalidateQueries({ queryKey: ['states', projectId.value] })
}
const showStateForm = ref(false)
const editingState = ref<WorkflowState | null>(null)
const stateForm = reactive({ name: '', category: 'todo' as TaskStatus, color: '#5e6ad2' })

function openAddState() {
  editingState.value = null
  Object.assign(stateForm, { name: '', category: 'todo', color: '#5e6ad2' })
  showStateForm.value = true
}
function openEditState(s: WorkflowState) {
  editingState.value = s
  Object.assign(stateForm, { name: s.name, category: s.category, color: s.color ?? '#5e6ad2' })
  showStateForm.value = true
}

const saveState = useMutation({
  mutationFn: () => {
    const body = { name: stateForm.name.trim(), category: stateForm.category, color: stateForm.color }
    return editingState.value
      ? api<WorkflowState>(`/api/v1/projects/${projectId.value}/states/${editingState.value.id}`, { method: 'PATCH', body })
      : api<WorkflowState>(`/api/v1/projects/${projectId.value}/states`, { method: 'POST', body })
  },
  onSuccess: () => { showStateForm.value = false; invalidateStates() },
  onError: () => error('Could not save column'),
})

async function deleteState(s: WorkflowState) {
  const ok = await confirm({
    title: `Delete "${s.name}" column?`,
    message: 'The column must be empty. Tasks in it must be moved first.',
    confirmLabel: 'Delete column',
    danger: true,
  })
  if (!ok) return
  try {
    await api(`/api/v1/projects/${projectId.value}/states/${s.id}`, { method: 'DELETE' })
    invalidateStates()
    success('Column deleted')
  } catch {
    error("Couldn't delete — move this column's tasks first")
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
    <div v-else-if="view === 'board'" class="flex gap-4 overflow-x-auto pb-2">
      <section
        v-for="s in states ?? []"
        :key="s.id"
        class="group flex w-80 shrink-0 flex-col rounded-card border border-line bg-surface-2/40 p-3"
      >
        <!-- Column Header -->
        <div class="mb-3 flex items-center gap-2 px-1.5 py-1 select-none">
          <span class="size-2 rounded-full" :class="s.color ? '' : categoryDot[s.category]" :style="dotStyle(s)" />
          <span class="text-sm font-semibold text-ink">{{ s.name }}</span>
          <span class="text-xs text-ink-subtle font-normal tabular">({{ columns[s.id]?.length ?? 0 }})</span>
          <UiMenu align="right" class="ml-auto">
            <template #trigger>
              <button
                type="button"
                class="grid size-6 place-items-center rounded text-ink-subtle opacity-0 transition hover:bg-surface-2 hover:text-ink-muted focus-within:opacity-100 group-hover:opacity-100"
                aria-label="Column actions"
              >
                <UiIcon name="more" :size="14" />
              </button>
            </template>
            <UiMenuItem icon="edit" @click="openEditState(s)">Rename / recolor</UiMenuItem>
            <UiMenuItem icon="trash" danger @click="deleteState(s)">Delete column</UiMenuItem>
          </UiMenu>
        </div>

        <draggable
          :list="columns[s.id]"
          item-key="id"
          group="tasks"
          class="flex min-h-[160px] flex-1 flex-col gap-2"
          ghost-class="opacity-40"
          drag-class="rotate-2"
          animation="180"
          @change="onColumnChange(s.id, $event)"
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
          v-if="!(columns[s.id]?.length)"
          class="my-2 flex flex-col items-center justify-center rounded-lg border border-dashed border-line bg-surface/20 px-4 py-8 text-center select-none"
        >
          <UiIcon name="inbox" :size="14" class="mb-1 text-ink-subtle" />
          <p class="text-xs font-semibold text-ink-muted">No tasks yet</p>
          <p class="mt-0.5 text-[10px] text-ink-subtle">Drag tasks here or add below</p>
        </div>

        <!-- inline quick-add -->
        <div class="mt-2">
          <input
            v-model="drafts[s.id]"
            type="text"
            :aria-label="`Add a task to ${s.name}`"
            :placeholder="adding === s.id ? 'Task title, then Enter…' : '+ Add task'"
            class="w-full rounded-lg border border-transparent bg-transparent px-2.5 py-2 text-sm text-ink outline-none transition placeholder:text-ink-subtle focus:border-line focus:bg-surface focus:shadow-sm"
            @focus="adding = s.id"
            @blur="adding = null"
            @keydown.enter.prevent="quickAdd(s.id)"
          >
        </div>
      </section>

      <!-- Add column -->
      <button
        type="button"
        class="flex h-11 w-72 shrink-0 items-center justify-center gap-1.5 rounded-card border border-dashed border-line text-sm text-ink-muted transition hover:border-line-strong hover:bg-surface-2 hover:text-ink"
        @click="openAddState"
      >
        <UiIcon name="plus" :size="14" /> Add column
      </button>
    </div>

    <!-- list view -->
    <div v-else class="overflow-hidden rounded-card border border-line bg-surface shadow-card">
      <template v-for="s in states ?? []" :key="s.id">
        <div
          v-if="columns[s.id]?.length"
          class="flex items-center gap-2 bg-surface-2 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-ink-muted"
        >
          <span class="size-2 rounded-full" :class="s.color ? '' : categoryDot[s.category]" :style="dotStyle(s)" />
          {{ s.name }}
          <span class="text-ink-subtle">· {{ columns[s.id]?.length ?? 0 }}</span>
        </div>
        <button
          v-for="task in columns[s.id]"
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

    <!-- Workflow state (column) editor -->
    <UiModal
      :open="showStateForm"
      :title="editingState ? 'Edit column' : 'New column'"
      width="max-w-sm"
      @close="showStateForm = false"
    >
      <form class="flex flex-col gap-4" @submit.prevent="saveState.mutate()">
        <label class="flex flex-col gap-1.5">
          <span class="field-label">Name</span>
          <input v-model="stateForm.name" type="text" required maxlength="50" placeholder="e.g. In Review" class="field-input">
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="field-label">Category</span>
          <select v-model="stateForm.category" class="field-input">
            <option value="todo">Unstarted (todo)</option>
            <option value="in_progress">Started (in progress)</option>
            <option value="done">Completed (done)</option>
          </select>
          <span class="text-helper">Drives progress/“done” reporting.</span>
        </label>
        <label class="flex items-center gap-2.5">
          <input v-model="stateForm.color" type="color" class="size-8 cursor-pointer rounded-control border border-line bg-surface">
          <span class="field-label">Column colour</span>
        </label>
        <div class="flex justify-end gap-2 pt-1">
          <UiButton variant="ghost" type="button" @click="showStateForm = false">Cancel</UiButton>
          <UiButton variant="primary" type="submit" :loading="saveState.isPending.value" :disabled="!stateForm.name.trim()">
            {{ editingState ? 'Save column' : 'Add column' }}
          </UiButton>
        </div>
      </form>
    </UiModal>
  </div>
</template>
