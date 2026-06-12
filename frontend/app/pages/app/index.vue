<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Project } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const { api } = useAuth()
const queryClient = useQueryClient()

const { data: projects, isPending } = useQuery({
  queryKey: ['projects'],
  queryFn: () => api<Project[]>('/api/v1/projects'),
})

const showForm = ref(false)
const editing = ref<Project | null>(null)

function invalidate() {
  queryClient.invalidateQueries({ queryKey: ['projects'] })
  showForm.value = false
  editing.value = null
}

const saveProject = useMutation({
  mutationFn: (data: { name: string; description: string; color: string }) =>
    editing.value
      ? api<Project>(`/api/v1/projects/${editing.value.id}`, { method: 'PATCH', body: data })
      : api<Project>('/api/v1/projects', { method: 'POST', body: data }),
  onSuccess: invalidate,
})

const toggleArchive = useMutation({
  mutationFn: (p: Project) =>
    api<Project>(`/api/v1/projects/${p.id}`, {
      method: 'PATCH',
      body: { status: p.status === 'active' ? 'archived' : 'active' },
    }),
  onSuccess: invalidate,
})

const deleteProject = useMutation({
  mutationFn: (p: Project) =>
    api(`/api/v1/projects/${p.id}`, { method: 'DELETE' }),
  onSuccess: invalidate,
})

function startEdit(p: Project) {
  editing.value = p
  showForm.value = true
}

function confirmDelete(p: Project) {
  if (window.confirm(`Delete project "${p.name}" and all its tasks?`)) {
    deleteProject.mutate(p)
  }
}
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl p-6">
      <div class="mb-6 flex items-center justify-between">
        <h1 class="text-2xl font-bold">Projects</h1>
        <button
          class="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700"
          @click="editing = null; showForm = true"
        >
          New project
        </button>
      </div>

      <ProjectForm
        v-if="showForm"
        :key="editing?.id ?? 'new'"
        :project="editing"
        :busy="saveProject.isPending.value"
        class="mb-6"
        @submit="saveProject.mutate($event)"
        @cancel="showForm = false; editing = null"
      />

      <p v-if="isPending" class="text-slate-500">Loading projects…</p>
      <p v-else-if="!projects?.length" class="text-slate-500">
        No projects yet — create your first one.
      </p>
      <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ProjectCard
          v-for="p in projects"
          :key="p.id"
          :project="p"
          @open="navigateTo(`/app/projects/${p.id}`)"
          @edit="startEdit(p)"
          @archive="toggleArchive.mutate(p)"
          @delete="confirmDelete(p)"
        />
      </div>
    </main>
  </div>
</template>
