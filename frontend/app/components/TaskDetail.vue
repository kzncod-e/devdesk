<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Project, Task, TaskPriority, UserBrief, WorkflowState } from '~/types/api'

const props = withDefaults(
  defineProps<{ taskId: number; compact?: boolean }>(),
  { compact: false },
)
const emit = defineEmits<{ deleted: []; close: [] }>()

const { api } = useAuth()
const queryClient = useQueryClient()
const { confirm } = useConfirm()
const { success, error } = useToast()

const enabled = computed(() => !isNaN(props.taskId))

const { data: task, isPending: isTaskPending } = useQuery({
  queryKey: computed(() => ['task', props.taskId]),
  queryFn: () => api<Task>(`/api/v1/tasks/${props.taskId}`),
  enabled,
})

// Keep the api() workspace header aligned with the task we're viewing (deep links).
const { workspaceId, setCurrent: setWorkspace } = useWorkspace()
watch(task, (t) => {
  if (t?.workspace_id && t.workspace_id !== workspaceId.value) setWorkspace(t.workspace_id)
})

const { data: project } = useQuery({
  queryKey: computed(() => ['project', task.value?.project_id]),
  queryFn: () => api<Project>(`/api/v1/projects/${task.value!.project_id}`),
  enabled: computed(() => enabled.value && task.value != null && task.value.id === props.taskId),
})

const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: () => api<UserBrief[]>('/api/v1/users'),
})

// Board columns (workflow states) for the state selector.
const { data: states } = useQuery({
  queryKey: computed(() => ['states', task.value?.project_id]),
  queryFn: () => api<WorkflowState[]>(`/api/v1/projects/${task.value!.project_id}/states`),
  enabled: computed(() => enabled.value && task.value != null && task.value.id === props.taskId),
})
const currentState = computed(() =>
  (states.value ?? []).find(s => s.id === task.value?.state_id) ?? null,
)
const categoryDot: Record<string, string> = {
  todo: 'bg-zinc-500', in_progress: 'bg-amber-500', done: 'bg-emerald-500',
}

// ── Inline edit state ─────────────────────────────────────────────────────────
const titleInput = ref('')
const descriptionInput = ref('')
watch(task, (t) => {
  if (!t) return
  if (document.activeElement?.id !== `task-title-${props.taskId}`) titleInput.value = t.title
  if (document.activeElement?.id !== `task-desc-${props.taskId}`) descriptionInput.value = t.description
}, { immediate: true })

// ── Mutations ─────────────────────────────────────────────────────────────────
const patchTask = useMutation({
  mutationFn: (body: Partial<Task>) =>
    api<Task>(`/api/v1/tasks/${props.taskId}`, { method: 'PATCH', body }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['task', props.taskId] })
    queryClient.invalidateQueries({ queryKey: ['tasks'] })
    queryClient.invalidateQueries({ queryKey: ['task-activity', props.taskId] })
  },
  onError: () => error('Could not save change'),
})

const updateAssignees = useMutation({
  mutationFn: (user_ids: number[]) =>
    api<Task>(`/api/v1/tasks/${props.taskId}/assignees`, { method: 'PUT', body: { user_ids } }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['task', props.taskId] })
    queryClient.invalidateQueries({ queryKey: ['task-activity', props.taskId] })
  },
  onError: () => error('Could not update assignees'),
})

const deleteTask = useMutation({
  mutationFn: () => api(`/api/v1/tasks/${props.taskId}`, { method: 'DELETE' }),
  onSuccess: () => {
    success('Task deleted')
    queryClient.invalidateQueries({ queryKey: ['tasks'] })
    emit('deleted')
    if (!props.compact) navigateTo(project.value ? `/app/projects/${project.value.id}` : '/app')
  },
  onError: () => error('Could not delete task'),
})

function saveTitle() {
  const clean = titleInput.value.trim()
  if (clean && clean !== task.value?.title) patchTask.mutate({ title: clean })
}
function saveDescription() {
  if (descriptionInput.value !== task.value?.description) patchTask.mutate({ description: descriptionInput.value })
}
function selectState(stateId: number) {
  if (stateId !== task.value?.state_id) patchTask.mutate({ state_id: stateId })
}
function selectPriority(priority: TaskPriority) {
  if (priority !== task.value?.priority) patchTask.mutate({ priority })
}
function updateDueDate(e: Event) {
  const val = (e.target as HTMLInputElement).value || null
  if (val !== task.value?.due_date) patchTask.mutate({ due_date: val })
}
function toggleAssignee(userId: number) {
  if (!task.value) return
  const ids = task.value.assignees.map((a) => a.id)
  const i = ids.indexOf(userId)
  if (i === -1) ids.push(userId)
  else ids.splice(i, 1)
  updateAssignees.mutate(ids)
}

async function confirmDelete() {
  const ok = await confirm({
    title: 'Delete task?',
    message: 'This permanently removes the task from the project.',
    confirmLabel: 'Delete task',
    danger: true,
  })
  if (ok) deleteTask.mutate()
}

function openFull() {
  navigateTo(`/app/tasks/${props.taskId}`)
  emit('close')
}

// ── Presentation ──────────────────────────────────────────────────────────────
const priorityOptions: { key: TaskPriority; label: string; text: string }[] = [
  { key: 'low', label: 'Low', text: 'text-ink-subtle' },
  { key: 'medium', label: 'Medium', text: 'text-warning' },
  { key: 'high', label: 'High', text: 'text-danger' },
]
const priorityText = (p?: TaskPriority) =>
  priorityOptions.find((o) => o.key === p)?.text ?? 'text-ink-subtle'

const isSaving = computed(() => patchTask.isPending.value || updateAssignees.isPending.value)

const activeTab = ref<'comments' | 'activity'>('comments')
</script>

<template>
  <div v-if="isTaskPending" class="space-y-4">
    <UiSkeleton class="h-8 w-2/3" />
    <UiSkeleton class="h-40 w-full" />
  </div>

  <div v-else-if="task">
    <!-- Action bar -->
    <div class="mb-5 flex items-center justify-between gap-3">
      <nav v-if="!compact" class="flex items-center gap-1.5 text-sm text-ink-muted">
        <NuxtLink to="/app" class="transition hover:text-ink">Projects</NuxtLink>
        <UiIcon name="chevron" :size="14" class="text-ink-subtle" />
        <NuxtLink v-if="project" :to="`/app/projects/${project.id}`" class="transition hover:text-ink">{{ project.name }}</NuxtLink>
        <span v-else class="text-ink-subtle">…</span>
        <UiIcon name="chevron" :size="14" class="text-ink-subtle" />
        <span class="font-medium text-ink">{{ taskRef(project?.key, task.number, taskId) }}</span>
      </nav>
      <span v-else class="font-mono text-xs font-semibold tracking-wider text-ink-subtle">{{ taskRef(project?.key, task.number, taskId) }}</span>

      <div class="flex items-center gap-2">
        <Transition name="fade">
          <span v-if="isSaving" class="mr-1 flex items-center gap-1.5 text-xs text-ink-subtle">
            <svg class="size-3 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2.5" class="opacity-25" />
              <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
            </svg>
            Saving…
          </span>
        </Transition>
        <UiButton v-if="compact" variant="ghost" size="sm" icon="external" @click="openFull">Open</UiButton>
        <UiButton variant="ghost" size="sm" icon="trash" class="text-ink-subtle hover:text-danger" @click="confirmDelete">Delete</UiButton>
        <UiButton v-if="!compact && project" variant="secondary" size="sm" icon="arrow-left" @click="navigateTo(`/app/projects/${project.id}`)">Back to board</UiButton>
      </div>
    </div>

    <!-- Title -->
    <input
      :id="`task-title-${taskId}`"
      v-model="titleInput"
      type="text"
      placeholder="Issue title"
      class="w-full border-0 border-b border-transparent bg-transparent px-0 py-1 text-title font-semibold tracking-tight text-ink outline-none transition-colors placeholder:text-ink-subtle focus:border-line"
      maxlength="200"
      @blur="saveTitle"
      @keydown.enter.prevent="($event.target as HTMLInputElement).blur()"
    />

    <!-- Body -->
    <div :class="compact ? 'mt-4 flex flex-col gap-5' : 'mt-4 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]'">
      <section class="flex min-w-0 flex-col gap-4">
        <textarea
          :id="`task-desc-${taskId}`"
          v-model="descriptionInput"
          placeholder="Add description…"
          class="min-h-32 w-full resize-none border-0 bg-transparent px-0 py-1 text-sm leading-relaxed text-ink outline-none placeholder:text-ink-subtle focus:ring-0"
          @blur="saveDescription"
        />

        <!-- Sub-tasks -->
        <div class="border-t border-line pt-4">
          <TaskSubtasks :task-id="taskId" :project-id="task.project_id" :project-key="project?.key" />
        </div>

        <!-- Tabs -->
        <div class="border-t border-line pt-4">
          <div role="tablist" class="mb-4 flex gap-1">
            <button
              v-for="t in (['comments','activity'] as const)"
              :key="t"
              type="button"
              :class="[
                'rounded-control px-3 py-1.5 text-sm font-medium capitalize transition',
                activeTab === t ? 'bg-surface-2 text-ink' : 'text-ink-muted hover:bg-surface-2 hover:text-ink',
              ]"
              @click="activeTab = t"
            >
              {{ t }}
            </button>
          </div>
          <TaskComments v-show="activeTab === 'comments'" :task-id="taskId" :users="users ?? []" />
          <TaskActivity v-if="activeTab === 'activity'" :task-id="taskId" />
        </div>
      </section>

      <!-- Properties -->
      <aside :class="compact ? 'order-first' : ''">
        <div class="rounded-card border border-line bg-surface p-4 shadow-card">
          <h3 class="mb-4 text-xs font-semibold uppercase tracking-wider text-ink-subtle">Properties</h3>
          <div class="divide-y divide-line text-sm">
            <!-- Project -->
            <div class="flex items-center justify-between py-2.5">
              <span class="field-label text-xs uppercase tracking-wider">Project</span>
              <span v-if="project" class="inline-flex items-center gap-2 font-medium text-ink">
                <ProjectAvatar :name="project.name" :size="18" />{{ project.name }}
              </span>
              <span v-else class="text-ink-subtle">—</span>
            </div>
            <!-- Status (workflow state) -->
            <div class="flex items-center justify-between py-2.5">
              <span class="field-label text-xs uppercase tracking-wider">Status</span>
              <UiMenu align="right">
                <template #trigger>
                  <button type="button" class="flex items-center gap-1.5 rounded-control border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink transition hover:border-line-strong hover:bg-surface-2">
                    <span class="size-1.5 rounded-full" :class="currentState?.color ? '' : categoryDot[currentState?.category ?? 'todo']" :style="currentState?.color ? { backgroundColor: currentState.color } : undefined" />
                    {{ currentState?.name ?? 'To do' }}
                    <UiIcon name="chevronDown" :size="10" class="text-ink-subtle" />
                  </button>
                </template>
                <UiMenuItem v-for="s in states ?? []" :key="s.id" @click="selectState(s.id)">
                  <span class="flex items-center gap-2">
                    <span class="size-2 rounded-full" :class="s.color ? '' : categoryDot[s.category]" :style="s.color ? { backgroundColor: s.color } : undefined" />
                    {{ s.name }}
                  </span>
                </UiMenuItem>
              </UiMenu>
            </div>
            <!-- Priority -->
            <div class="flex items-center justify-between py-2.5">
              <span class="field-label text-xs uppercase tracking-wider">Priority</span>
              <UiMenu align="right">
                <template #trigger>
                  <button type="button" class="flex items-center gap-1.5 rounded-control border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink transition hover:border-line-strong hover:bg-surface-2">
                    <UiIcon name="flag" :size="10" :class="priorityText(task.priority)" />
                    <span class="capitalize">{{ task.priority }}</span>
                    <UiIcon name="chevronDown" :size="10" class="text-ink-subtle" />
                  </button>
                </template>
                <UiMenuItem v-for="opt in priorityOptions" :key="opt.key" @click="selectPriority(opt.key)">
                  <span class="flex items-center gap-2"><UiIcon name="flag" :size="12" :class="opt.text" />{{ opt.label }}</span>
                </UiMenuItem>
              </UiMenu>
            </div>
            <!-- Due date -->
            <div class="flex items-center justify-between py-2.5">
              <span class="field-label text-xs uppercase tracking-wider">Due date</span>
              <input type="date" :value="task.due_date ?? ''" class="rounded-control border border-line bg-surface px-2 py-0.5 text-xs text-ink outline-none transition focus:border-accent" @change="updateDueDate" />
            </div>
            <!-- Assignees -->
            <div class="flex flex-col gap-2 py-2.5">
              <div class="flex items-center justify-between">
                <span class="field-label text-xs uppercase tracking-wider">Assignees</span>
                <UiMenu align="right">
                  <template #trigger>
                    <button type="button" class="flex items-center gap-1.5 rounded-control border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink transition hover:border-line-strong hover:bg-surface-2">
                      Assign…<UiIcon name="chevronDown" :size="10" class="text-ink-subtle" />
                    </button>
                  </template>
                  <div class="max-h-56 overflow-y-auto py-1">
                    <UiMenuItem v-for="u in users ?? []" :key="u.id" @click="toggleAssignee(u.id)">
                      <span class="flex items-center gap-2">
                        <span class="flex size-3.5 items-center justify-center rounded border border-line text-[10px]" :class="task.assignees.some(a => a.id === u.id) ? 'border-accent bg-accent text-accent-fg' : ''">
                          <UiIcon v-if="task.assignees.some(a => a.id === u.id)" name="check" :size="8" />
                        </span>
                        <UiAvatar :user="u" :size="18" />{{ u.name }}
                      </span>
                    </UiMenuItem>
                    <p v-if="!(users ?? []).length" class="px-3 py-2 text-xs text-ink-subtle">No members in workspace.</p>
                  </div>
                </UiMenu>
              </div>
              <div v-if="task.assignees.length" class="mt-1 flex flex-wrap gap-1.5">
                <span v-for="a in task.assignees" :key="a.id" class="flex cursor-pointer items-center gap-1.5 rounded-full border border-line bg-surface-2 py-0.5 pl-0.5 pr-2.5 text-xs text-ink-muted transition hover:border-line-strong" @click="toggleAssignee(a.id)">
                  <UiAvatar :user="a" :size="16" />{{ a.name }}<UiIcon name="x" :size="10" class="text-ink-subtle hover:text-ink" />
                </span>
              </div>
              <p v-else class="mt-0.5 text-xs italic text-ink-subtle">Unassigned</p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>
