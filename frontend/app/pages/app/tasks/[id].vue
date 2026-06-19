<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Project, Task, TaskPriority, TaskStatus, UserBrief } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'app' })

const route = useRoute()
const taskId = computed(() => Number(route.params.id))
const { api } = useAuth()
const queryClient = useQueryClient()
const { confirm } = useConfirm()
const { success, error } = useToast()

// ── Fetch Task ──────────────────────────────────────────────────────────────
const { data: task, isPending: isTaskPending } = useQuery({
  queryKey: computed(() => ['task', taskId.value]),
  queryFn: () => api<Task>(`/api/v1/tasks/${taskId.value}`),
  enabled: computed(() => route.path.startsWith('/app/tasks/') && !isNaN(taskId.value)),
})

const { workspaceId, setCurrent: setWorkspace } = useWorkspace()
watch(task, (t) => {
  if (t && t.workspace_id && t.workspace_id !== workspaceId.value) {
    setWorkspace(t.workspace_id)
  }
})

// ── Fetch Project (using task's project_id) ──────────────────────────────────
const { data: project } = useQuery({
  queryKey: computed(() => ['project', task.value?.project_id]),
  queryFn: () => api<Project>(`/api/v1/projects/${task.value!.project_id}`),
  enabled: computed(() => route.path.startsWith('/app/tasks/') && task.value != null && task.value.id === taskId.value),
})

// ── Fetch Users (for assignee selector) ─────────────────────────────────────
const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: () => api<UserBrief[]>('/api/v1/users'),
})

// ── Inline Editing Local State ──────────────────────────────────────────────
const titleInput = ref('')
const descriptionInput = ref('')

watch(task, (newTask) => {
  if (newTask) {
    // Only update if the user isn't actively editing
    if (document.activeElement?.id !== 'task-title') {
      titleInput.value = newTask.title
    }
    if (document.activeElement?.id !== 'task-desc') {
      descriptionInput.value = newTask.description
    }
  }
}, { immediate: true })

// ── Mutations ───────────────────────────────────────────────────────────────
const patchTask = useMutation({
  mutationFn: (body: Partial<Task>) =>
    api<Task>(`/api/v1/tasks/${taskId.value}`, { method: 'PATCH', body }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['task', taskId.value] })
    queryClient.invalidateQueries({ queryKey: ['tasks'] })
  },
  onError: () => {
    error('Could not save change')
  },
})

const updateAssignees = useMutation({
  mutationFn: (user_ids: number[]) =>
    api<Task>(`/api/v1/tasks/${taskId.value}/assignees`, {
      method: 'PUT',
      body: { user_ids },
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['task', taskId.value] })
  },
  onError: () => {
    error('Could not update assignees')
  },
})

const deleteTask = useMutation({
  mutationFn: () => api(`/api/v1/tasks/${taskId.value}`, { method: 'DELETE' }),
  onSuccess: () => {
    success('Task deleted')
    if (project.value) {
      navigateTo(`/app/projects/${project.value.id}`)
    } else {
      navigateTo('/app')
    }
  },
  onError: () => {
    error('Could not delete task')
  },
})

// ── Save Helpers ────────────────────────────────────────────────────────────
function saveTitle() {
  const clean = titleInput.value.trim()
  if (clean && clean !== task.value?.title) {
    patchTask.mutate({ title: clean })
  }
}

function saveDescription() {
  if (descriptionInput.value !== task.value?.description) {
    patchTask.mutate({ description: descriptionInput.value })
  }
}

function selectStatus(status: TaskStatus) {
  if (status !== task.value?.status) {
    patchTask.mutate({ status })
  }
}

function selectPriority(priority: TaskPriority) {
  if (priority !== task.value?.priority) {
    patchTask.mutate({ priority })
  }
}

function updateDueDate(e: Event) {
  const val = (e.target as HTMLInputElement).value || null
  if (val !== task.value?.due_date) {
    patchTask.mutate({ due_date: val })
  }
}

function toggleAssignee(userId: number) {
  if (!task.value) return
  const currentIds = task.value.assignees.map(a => a.id)
  const idx = currentIds.indexOf(userId)
  if (idx === -1) {
    currentIds.push(userId)
  } else {
    currentIds.splice(idx, 1)
  }
  updateAssignees.mutate(currentIds)
}

async function confirmDelete() {
  const ok = await confirm({
    title: `Delete task?`,
    message: 'This permanently removes the task from the project.',
    confirmLabel: 'Delete task',
    danger: true,
  })
  if (ok) {
    deleteTask.mutate()
  }
}

// ── Presentation Mapping ─────────────────────────────────────────────────────
const priorityTone: Record<TaskPriority, 'gray' | 'amber' | 'red'> = {
  low: 'gray',
  medium: 'amber',
  high: 'red',
}

const statusOptions: { key: TaskStatus; label: string; dot: string }[] = [
  { key: 'todo', label: 'To do', dot: 'bg-zinc-500' },
  { key: 'in_progress', label: 'In progress', dot: 'bg-amber-500' },
  { key: 'done', label: 'Done', dot: 'bg-emerald-500' },
]

const priorityOptions: { key: TaskPriority; label: string; tone: 'gray' | 'amber' | 'red' }[] = [
  { key: 'low', label: 'Low', tone: 'gray' },
  { key: 'medium', label: 'Medium', tone: 'amber' },
  { key: 'high', label: 'High', tone: 'red' },
]

const isSaving = computed(() => patchTask.isPending.value || updateAssignees.isPending.value)
</script>

<template>
  <div class="mx-auto max-w-6xl px-5 py-8 md:px-8">
    <!-- Breadcrumb header -->
    <header class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <nav class="flex items-center gap-1.5 text-sm text-ink-muted">
        <NuxtLink to="/app" class="transition hover:text-ink">Projects</NuxtLink>
        <UiIcon name="chevron" :size="14" class="text-ink-subtle" />
        <NuxtLink
          v-if="project"
          :to="`/app/projects/${project.id}`"
          class="transition hover:text-ink"
        >
          {{ project.name }}
        </NuxtLink>
        <span v-else class="text-ink-subtle">…</span>
        <UiIcon name="chevron" :size="14" class="text-ink-subtle" />
        <span class="font-medium text-ink">TASK-{{ taskId }}</span>

        <Transition name="fade">
          <span v-if="isSaving" class="ml-3 flex items-center gap-1.5 text-xs text-ink-subtle">
            <svg class="size-3 animate-spin text-ink-subtle" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2.5" class="opacity-25" />
              <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
            </svg>
            Saving…
          </span>
        </Transition>
      </nav>

      <div class="flex items-center gap-2">
        <UiButton
          variant="ghost"
          size="sm"
          icon="trash"
          class="text-ink-subtle hover:text-danger"
          @click="confirmDelete"
        >
          Delete
        </UiButton>
        <UiButton
          v-if="project"
          variant="secondary"
          size="sm"
          icon="arrow-left"
          @click="navigateTo(`/app/projects/${project.id}`)"
        >
          Back to board
        </UiButton>
      </div>
    </header>

    <!-- Main visual skeleton loader -->
    <div v-if="isTaskPending" class="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_300px]">
      <div class="space-y-4">
        <UiSkeleton class="h-8 w-2/3" />
        <UiSkeleton class="h-48 w-full" />
      </div>
      <div class="space-y-4">
        <UiSkeleton class="h-44 w-full" />
      </div>
    </div>

    <!-- Layout Grid -->
    <div v-else-if="task" class="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_300px]">
      <!-- Left side (Editable Content) -->
      <section class="flex flex-col gap-4">
        <input
          id="task-title"
          v-model="titleInput"
          type="text"
          placeholder="Issue title"
          class="w-full bg-transparent px-0 py-1 text-title font-semibold tracking-tight text-ink placeholder:text-ink-subtle outline-none border-0 border-b border-transparent focus:border-line transition-colors"
          maxlength="200"
          @blur="saveTitle"
          @keydown.enter.prevent="saveTitle; $event.target.blur()"
        />

        <textarea
          id="task-desc"
          v-model="descriptionInput"
          placeholder="Add description..."
          class="min-h-[260px] w-full resize-none bg-transparent px-0 py-1 text-sm leading-relaxed text-ink placeholder:text-ink-subtle outline-none border-0 focus:ring-0"
          @blur="saveDescription"
        />
      </section>

      <!-- Right side (Sidebar Properties) -->
      <aside class="flex flex-col gap-4">
        <div class="rounded-card border border-line bg-surface p-4 shadow-card">
          <h3 class="mb-4 text-xs font-semibold uppercase tracking-wider text-ink-subtle">
            Properties
          </h3>

          <div class="divide-y divide-line text-sm">
            <!-- Project Display -->
            <div class="flex items-center justify-between py-2.5">
              <span class="field-label text-xs uppercase tracking-wider">Project</span>
              <span v-if="project" class="inline-flex items-center gap-2 font-medium text-ink">
                <ProjectAvatar :name="project.name" :size="18" />
                {{ project.name }}
              </span>
              <span v-else class="text-ink-subtle">—</span>
            </div>

            <!-- Status Manager -->
            <div class="flex items-center justify-between py-2.5">
              <span class="field-label text-xs uppercase tracking-wider">Status</span>
              <UiMenu align="right">
                <template #trigger>
                  <button
                    type="button"
                    class="flex items-center gap-1.5 rounded-control border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink transition hover:border-line-strong hover:bg-surface-2"
                  >
                    <span
                      class="size-1.5 rounded-full"
                      :class="statusOptions.find(o => o.key === task?.status)?.dot ?? 'bg-slate-400'"
                    />
                    {{ statusOptions.find(o => o.key === task?.status)?.label ?? 'To do' }}
                    <UiIcon name="chevronDown" :size="10" class="text-ink-subtle" />
                  </button>
                </template>
                <UiMenuItem
                  v-for="opt in statusOptions"
                  :key="opt.key"
                  @click="selectStatus(opt.key)"
                >
                  <span class="flex items-center gap-2">
                    <span class="size-2 rounded-full" :class="opt.dot" />
                    {{ opt.label }}
                  </span>
                </UiMenuItem>
              </UiMenu>
            </div>

            <!-- Priority Manager -->
            <div class="flex items-center justify-between py-2.5">
              <span class="field-label text-xs uppercase tracking-wider">Priority</span>
              <UiMenu align="right">
                <template #trigger>
                  <button
                    type="button"
                    class="flex items-center gap-1.5 rounded-control border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink transition hover:border-line-strong hover:bg-surface-2"
                  >
                    <UiIcon name="flag" :size="10" :class="`text-${priorityTone[task.priority]}`" />
                    <span class="capitalize">{{ task.priority }}</span>
                    <UiIcon name="chevronDown" :size="10" class="text-ink-subtle" />
                  </button>
                </template>
                <UiMenuItem
                  v-for="opt in priorityOptions"
                  :key="opt.key"
                  @click="selectPriority(opt.key)"
                >
                  <span class="flex items-center gap-2">
                    <UiIcon name="flag" :size="12" :class="`text-${opt.tone}`" />
                    {{ opt.label }}
                  </span>
                </UiMenuItem>
              </UiMenu>
            </div>

            <!-- Due Date Manager -->
            <div class="flex items-center justify-between py-2.5">
              <span class="field-label text-xs uppercase tracking-wider">Due date</span>
              <input
                type="date"
                :value="task.due_date ?? ''"
                class="rounded-control border border-line bg-surface px-2 py-0.5 text-xs text-ink outline-none transition focus:border-accent"
                @change="updateDueDate"
              />
            </div>

            <!-- Assignees Manager -->
            <div class="flex flex-col gap-2 py-2.5">
              <div class="flex items-center justify-between">
                <span class="field-label text-xs uppercase tracking-wider">Assignees</span>
                <UiMenu align="right">
                  <template #trigger>
                    <button
                      type="button"
                      class="flex items-center gap-1.5 rounded-control border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink transition hover:border-line-strong hover:bg-surface-2"
                    >
                      Assign…
                      <UiIcon name="chevronDown" :size="10" class="text-ink-subtle" />
                    </button>
                  </template>
                  <div class="max-h-56 overflow-y-auto py-1">
                    <UiMenuItem
                      v-for="u in users ?? []"
                      :key="u.id"
                      @click="toggleAssignee(u.id)"
                    >
                      <span class="flex items-center gap-2">
                        <span
                          class="size-3.5 rounded border border-line flex items-center justify-center text-[10px]"
                          :class="task.assignees.some(a => a.id === u.id) ? 'bg-accent text-accent-fg border-accent' : ''"
                        >
                          <UiIcon
                            v-if="task.assignees.some(a => a.id === u.id)"
                            name="check"
                            :size="8"
                          />
                        </span>
                        <UiAvatar :user="u" :size="18" />
                        {{ u.name }}
                      </span>
                    </UiMenuItem>
                    <p
                      v-if="!(users ?? []).length"
                      class="px-3 py-2 text-xs text-ink-subtle"
                    >
                      No members in workspace.
                    </p>
                  </div>
                </UiMenu>
              </div>

              <!-- Assignee Avatar List -->
              <div v-if="task.assignees.length" class="mt-1 flex flex-wrap gap-1.5">
                <span
                  v-for="a in task.assignees"
                  :key="a.id"
                  class="flex items-center gap-1.5 rounded-full border border-line bg-surface-2 py-0.5 pl-0.5 pr-2.5 text-xs text-ink-muted transition hover:border-line-strong cursor-pointer"
                  @click="toggleAssignee(a.id)"
                >
                  <UiAvatar :user="a" :size="16" />
                  {{ a.name }}
                  <UiIcon name="x" :size="10" class="text-ink-subtle hover:text-ink" />
                </span>
              </div>
              <p v-else class="text-xs text-ink-subtle italic mt-0.5">
                Unassigned
              </p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>
