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
    <div class="flex flex-col gap-8 xl:flex-row xl:items-start xl:gap-6">

      <!-- ── Projects column ─────────────────────────────────────────────── -->
      <div class="min-w-0 flex-1">
        <header class="mb-7 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 class="text-2xl font-semibold tracking-tight text-ink">Projects</h1>
            <p class="mt-1 text-sm text-ink-muted">Organize your work into boards.</p>
          </div>
          <UiButton variant="primary" icon="plus" @click="openCreate">New project</UiButton>
        </header>

        <div class="mb-6 flex flex-wrap items-center gap-3">
          <div class="relative flex-1 sm:max-w-xs">
            <UiIcon name="search" :size="16" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle" />
            <input v-model="search" type="text" placeholder="Filter projects…" class="field-input pl-9">
          </div>
          <div class="flex gap-1 rounded-lg border border-line bg-surface p-1 shadow-sm">
            <button
              v-for="s in (['all', 'active', 'archived'] as const)"
              :key="s"
              :class="[
                'rounded-md px-3 py-1 text-sm font-medium capitalize transition',
                statusFilter === s ? 'bg-accent-soft text-accent' : 'text-ink-muted hover:text-ink',
              ]"
              @click="statusFilter = s"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <!-- loading -->
        <div v-if="isPending" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="i in 6" :key="i" class="flex flex-col gap-4 rounded-card border border-line bg-surface p-5">
            <div class="flex gap-3">
              <UiSkeleton class="size-9 rounded-lg" />
              <div class="flex-1 space-y-2">
                <UiSkeleton class="h-4 w-2/3" />
                <UiSkeleton class="h-3 w-20" />
              </div>
            </div>
            <UiSkeleton class="h-8 w-full" />
            <UiSkeleton class="h-4 w-24" />
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

        <!-- grid -->
        <TransitionGroup
          v-else
          tag="div"
          name="fade"
          class="stagger grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          <ProjectCard
            v-for="(p, i) in visibleProjects"
            :key="p.id"
            :project="p"
            :style="{ '--i': i }"
            @open="navigateTo(`/app/projects/${p.id}`)"
            @edit="startEdit(p)"
            @archive="toggleArchive.mutate(p)"
            @delete="confirmDelete(p)"
            @template="saveTemplate.save({ kind: 'project', sourceId: p.id, sourceName: p.name })"
          />
        </TransitionGroup>
      </div>

      <!-- ── Activity feed sidebar ───────────────────────────────────────── -->
      <aside class="w-full xl:w-72 xl:shrink-0">
        <div class="rounded-card border border-line bg-surface">
          <div class="flex items-center gap-2 border-b border-line px-4 py-3">
            <UiIcon name="activity" :size="15" class="text-ink-muted" />
            <span class="text-sm font-medium text-ink">Activity</span>
          </div>

          <!-- skeleton -->
          <div v-if="!activityPage" class="divide-y divide-line">
            <div v-for="i in 5" :key="i" class="flex gap-3 px-4 py-3">
              <UiSkeleton class="mt-0.5 size-6 shrink-0 rounded-full" />
              <div class="flex-1 space-y-1.5">
                <UiSkeleton class="h-3 w-full" />
                <UiSkeleton class="h-3 w-2/3" />
              </div>
            </div>
          </div>

          <!-- empty -->
          <p v-else-if="!activities.length" class="px-4 py-6 text-center text-sm text-ink-subtle">
            No activity yet.
          </p>

          <!-- list -->
          <ul v-else class="divide-y divide-line">
            <li
              v-for="a in activities"
              :key="a.id"
              class="flex gap-3 px-4 py-3"
            >
              <span class="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent">
                <UiIcon :name="activityIcon(a.verb)" :size="12" />
              </span>
              <div class="min-w-0 flex-1">
                <p class="truncate text-xs text-ink">
                  <span class="font-medium">{{ a.actor_name ?? 'System' }}</span>
                  {{ ' ' + activityLabel(a) }}
                </p>
                <p class="mt-0.5 text-xs text-ink-subtle">{{ timeAgo(a.created_at) }}</p>
              </div>
            </li>
          </ul>
        </div>
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
