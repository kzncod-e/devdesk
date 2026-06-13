<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Project } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'app' })

const { api } = useAuth()
const queryClient = useQueryClient()
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

async function uploadImage(projectId: number, imageFile: File) {
  const form = new FormData()
  form.append('file', imageFile)
  await api(`/api/v1/projects/${projectId}/image`, { method: 'POST', body: form })
}

const saveProject = useMutation({
  mutationFn: async (data: { name: string; description: string; color: string; image?: File | null }) => {
    const { image, ...fields } = data
    const project = editing.value
      ? await api<Project>(`/api/v1/projects/${editing.value.id}`, { method: 'PATCH', body: fields })
      : await api<Project>('/api/v1/projects', { method: 'POST', body: fields })
    if (image) await uploadImage(project.id, image)
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
  <div class="mx-auto max-w-6xl px-5 py-8 md:px-8">
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
      />
    </TransitionGroup>

    <UiModal
      :open="showForm"
      :title="editing ? 'Edit project' : 'New project'"
      :subtitle="editing ? 'Update the project details.' : 'Spin up a new board.'"
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
