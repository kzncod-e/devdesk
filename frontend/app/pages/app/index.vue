<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Activity, ActivityPage, Project } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'app' })

const { api } = useAuth()
const { uploadProjectImage } = useCloudinaryUpload()
const queryClient = useQueryClient()
const { workspaceId } = useWorkspace()
const saveTemplate = useSaveTemplate()

// ── Activity feed ─────────────────────────────────────────────────────────────
const { data: activityPage } = useQuery({
  queryKey: computed(() => ['workspace-activity', workspaceId.value]),
  queryFn: () =>
    api<ActivityPage>(`/api/v1/workspaces/${workspaceId.value}/activity?limit=20`),
  enabled: computed(() => workspaceId.value != null),
  refetchInterval: 30_000,
})

const activities = computed(() => activityPage.value?.items ?? [])

const VERB_ICON: Record<string, string> = {
  created: 'plus',
  updated: 'edit',
  deleted: 'trash',
  status_changed: 'check-circle',
  assignees_changed: 'user',
  invited: 'user-plus',
  joined: 'user-check',
  role_changed: 'shield',
  removed: 'user-minus',
}

function activityIcon(verb: string): string {
  return VERB_ICON[verb] ?? 'activity'
}

function activityLabel(a: Activity): string {
  const name = a.entity_name ? ` "${a.entity_name}"` : ''
  return `${a.verb.replace(/_/g, ' ')} ${a.entity_type}${name}`
}

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
const { confirm } = useConfirm()
const { success, error } = useToast()

const { data: projects, isPending } = useQuery({
  queryKey: ['projects'],
  queryFn: () => api<Project[]>('/api/v1/projects'),
})

const search = ref('')
const statusFilter = ref<'all' | 'active' | 'archived'>('all')

const visibleProjects = computed(() => {
  let list = projects.value ?? []
  if (statusFilter.value !== 'all') list = list.filter(p => p.status === statusFilter.value)
  const q = search.value.trim().toLowerCase()
  if (q) list = list.filter(p => p.name.toLowerCase().includes(q) || p.description.toLowerCase().includes(q))
  return list
})

// Compact top metrics (computed from the loaded list).
const metrics = computed(() => {
  const list = projects.value ?? []
  return [
    { label: 'Projects', value: list.length },
    { label: 'Active', value: list.filter(p => p.status === 'active').length },
    { label: 'Archived', value: list.filter(p => p.status === 'archived').length },
    { label: 'Tasks', value: list.reduce((n, p) => n + (p.task_count ?? 0), 0) },
  ]
})

const showForm = ref(false)
const editing = ref<Project | null>(null)

function openCreate() {
  editing.value = null
  showForm.value = true
}
function startEdit(p: Project) {
  editing.value = p
  showForm.value = true
}
function closeForm() {
  showForm.value = false
  editing.value = null
}

// Open the create modal when ⌘K requested a new project (from any page).
const { intent: quickCreateIntent, consume: consumeQuickCreate } = useQuickCreate()
watch(quickCreateIntent, () => {
  if (consumeQuickCreate('project')) openCreate()
}, { immediate: true })

const saveProject = useMutation({
  mutationFn: async (data: { name: string; description: string; color: string; image?: File | null }) => {
    const { image, ...fields } = data

    // Create or update the project record first (gets us the project.id we need for the upload key).
    let project = editing.value
      ? await api<Project>(`/api/v1/projects/${editing.value.id}`, { method: 'PATCH', body: fields })
      : await api<Project>('/api/v1/projects', { method: 'POST', body: fields })

    if (image) {
      // Upload directly to Cloudinary (browser → CDN, no Nitro proxy involved).
      const imageUrl = await uploadProjectImage(project.id, image)
      // Persist the CDN URL on the project record.
      project = await api<Project>(`/api/v1/projects/${project.id}`, {
        method: 'PATCH',
        body: { image_url: imageUrl },
      })
    }

    return project
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['projects'] })
    success(editing.value ? 'Project updated' : 'Project created')
    closeForm()
  },
  onError: () => error('Could not save project'),
})

const toggleArchive = useMutation({
  mutationFn: (p: Project) =>
    api<Project>(`/api/v1/projects/${p.id}`, {
      method: 'PATCH',
      body: { status: p.status === 'active' ? 'archived' : 'active' },
    }),
  onSuccess: (_, p) => {
    queryClient.invalidateQueries({ queryKey: ['projects'] })
    success(p.status === 'active' ? 'Project archived' : 'Project restored')
  },
})

const deleteProject = useMutation({
  mutationFn: (p: Project) => api(`/api/v1/projects/${p.id}`, { method: 'DELETE' }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['projects'] })
    success('Project deleted')
  },
})

async function confirmDelete(p: Project) {
  const ok = await confirm({
    title: `Delete "${p.name}"?`,
    message: 'This permanently removes the project and all of its tasks.',
    confirmLabel: 'Delete project',
    danger: true,
  })
  if (ok) deleteProject.mutate(p)
}
</script>

<template>
  <div class="mx-auto max-w-7xl px-5 py-8 md:px-8">
    <header class="mb-5 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-title">Projects</h1>
      <UiButton variant="primary" icon="plus" size="sm" @click="openCreate">New project</UiButton>
    </header>

    <!-- Compact metrics (no cards) -->
    <div class="mb-6 flex flex-wrap items-center gap-x-8 gap-y-2 border-b border-line pb-5">
      <div v-for="m in metrics" :key="m.label" class="flex items-baseline gap-1.5">
        <span class="text-xl font-semibold tabular text-ink">{{ m.value }}</span>
        <span class="text-xs text-ink-subtle">{{ m.label }}</span>
      </div>
    </div>

    <div class="flex flex-col gap-8 xl:flex-row xl:items-start xl:gap-8">
      <!-- ── Projects list ───────────────────────────────────────────────── -->
      <div class="min-w-0 flex-1">
        <!-- Toolbar -->
        <div class="mb-4 flex flex-wrap items-center gap-3">
          <div class="relative flex-1 sm:max-w-xs">
            <UiIcon name="search" :size="15" class="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-subtle" />
            <input v-model="search" type="text" placeholder="Filter projects…" class="field-input h-8 pl-8">
          </div>
          <div class="flex gap-0.5 rounded-control border border-line p-0.5">
            <button
              v-for="s in (['all', 'active', 'archived'] as const)"
              :key="s"
              :class="[
                'rounded-[5px] px-2.5 py-1 text-xs font-medium capitalize transition',
                statusFilter === s ? 'bg-surface-3 text-ink' : 'text-ink-muted hover:text-ink',
              ]"
              @click="statusFilter = s"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <!-- loading -->
        <div v-if="isPending" class="overflow-hidden rounded-card border border-line">
          <div v-for="i in 6" :key="i" class="flex items-center gap-3 border-b border-line px-4 py-3 last:border-0">
            <UiSkeleton class="size-7 shrink-0 rounded-[6px]" />
            <UiSkeleton class="h-3.5 w-40" />
            <UiSkeleton class="ml-auto h-3 w-16" />
          </div>
        </div>

        <!-- empty -->
        <UiEmptyState
          v-else-if="!projects?.length"
          icon="folder"
          title="No projects yet"
          description="Create your first project to start tracking tasks, snippets and bookmarks."
        >
          <UiButton variant="primary" icon="plus" @click="openCreate">Create a project</UiButton>
        </UiEmptyState>

        <UiEmptyState
          v-else-if="!visibleProjects.length"
          icon="search"
          title="No matches"
          description="No projects match your current filters."
        />

        <!-- list / table -->
        <div v-else class="overflow-hidden rounded-card border border-line">
          <!-- column header -->
          <div class="flex items-center gap-3 border-b border-line bg-surface-2 px-4 py-2 text-eyebrow">
            <span class="w-7 shrink-0" />
            <span class="flex-1">Project</span>
            <span class="hidden w-20 shrink-0 sm:block">Status</span>
            <span class="hidden w-16 shrink-0 text-right md:block">Tasks</span>
            <span class="hidden w-20 shrink-0 text-right lg:block">Updated</span>
            <span class="w-7 shrink-0" />
          </div>

          <!-- rows -->
          <div class="divide-y divide-line">
            <div
              v-for="p in visibleProjects"
              :key="p.id"
              class="group flex cursor-pointer items-center gap-3 px-4 py-2.5 transition-colors duration-150 hover:bg-surface-2"
              role="button"
              tabindex="0"
              @click="navigateTo(`/app/projects/${p.id}`)"
              @keydown.enter="navigateTo(`/app/projects/${p.id}`)"
            >
              <ProjectAvatar :name="p.name" :size="28" class="shrink-0" />
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="truncate text-sm font-medium text-ink group-hover:text-ink">{{ p.name }}</span>
                  <span class="shrink-0 font-mono text-[11px] text-ink-subtle">{{ p.key }}</span>
                </div>
                <p class="truncate text-xs text-ink-subtle">{{ p.description || 'No description' }}</p>
              </div>

              <div class="hidden w-20 shrink-0 sm:block">
                <UiBadge :tone="p.status === 'active' ? 'green' : 'gray'" dot class="capitalize">{{ p.status }}</UiBadge>
              </div>
              <span class="tabular hidden w-16 shrink-0 text-right text-xs text-ink-muted md:block">{{ p.task_count ?? 0 }}</span>
              <span class="tabular hidden w-20 shrink-0 text-right text-meta lg:block">{{ p.updated_at ? timeAgo(p.updated_at) : '—' }}</span>

              <!-- quick actions (hover) -->
              <span class="shrink-0" @click.stop>
                <UiMenu align="right">
                  <template #trigger>
                    <button
                      type="button"
                      class="grid size-7 place-items-center rounded-control text-ink-subtle opacity-0 transition hover:bg-surface-3 hover:text-ink-muted focus-within:opacity-100 group-hover:opacity-100"
                      aria-label="Project actions"
                    >
                      <UiIcon name="more" :size="16" />
                    </button>
                  </template>
                  <UiMenuItem icon="edit" @click="startEdit(p)">Edit</UiMenuItem>
                  <UiMenuItem icon="layers" @click="saveTemplate.save({ kind: 'project', sourceId: p.id, sourceName: p.name })">Save as template</UiMenuItem>
                  <UiMenuItem :icon="p.status === 'active' ? 'archive' : 'unarchive'" @click="toggleArchive.mutate(p)">
                    {{ p.status === 'active' ? 'Archive' : 'Restore' }}
                  </UiMenuItem>
                  <UiMenuItem icon="trash" danger @click="confirmDelete(p)">Delete</UiMenuItem>
                </UiMenu>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Activity feed (light, integrated) ───────────────────────────── -->
      <aside class="w-full xl:w-64 xl:shrink-0">
        <h2 class="mb-3 text-eyebrow">Activity</h2>

        <div v-if="!activityPage" class="space-y-3">
          <div v-for="i in 5" :key="i" class="flex gap-2.5">
            <UiSkeleton class="mt-0.5 size-4 shrink-0 rounded-full" />
            <UiSkeleton class="h-3 w-full" />
          </div>
        </div>

        <p v-else-if="!activities.length" class="text-sm text-ink-subtle">No activity yet.</p>

        <ul v-else class="space-y-3">
          <li v-for="a in activities" :key="a.id" class="flex gap-2.5">
            <UiIcon :name="activityIcon(a.verb)" :size="13" class="mt-0.5 shrink-0 text-ink-subtle" />
            <div class="min-w-0 flex-1 leading-snug">
              <p class="text-xs text-ink-muted">
                <span class="font-medium text-ink">{{ a.actor_name ?? 'System' }}</span>
                {{ ' ' + activityLabel(a) }}
              </p>
              <p class="text-[11px] text-ink-subtle">{{ timeAgo(a.created_at) }}</p>
            </div>
          </li>
        </ul>
      </aside>
    </div>

    <UiModal
      :open="showForm"
      no-header
      width="max-w-2xl"
      @close="closeForm"
    >
      <ProjectForm
        v-if="showForm"
        :key="editing?.id ?? 'new'"
        :project="editing"
        :busy="saveProject.isPending.value"
        @submit="saveProject.mutate($event)"
        @cancel="closeForm"
      />
    </UiModal>
  </div>
</template>
