<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Project, Snippet } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const { api } = useAuth()
const queryClient = useQueryClient()

const languageFilter = ref('')
const tagFilter = ref('')
const projectFilter = ref<number | null>(null)

const filters = computed(() => {
  const params = new URLSearchParams()
  if (languageFilter.value) params.set('language', languageFilter.value)
  if (tagFilter.value) params.set('tag', tagFilter.value)
  if (projectFilter.value !== null) params.set('project_id', String(projectFilter.value))
  const qs = params.toString()
  return qs ? `?${qs}` : ''
})

const { data: projects } = useQuery({
  queryKey: ['projects'],
  queryFn: () => api<Project[]>('/api/v1/projects'),
})

const { data: snippets, isPending } = useQuery({
  queryKey: ['snippets', filters],
  queryFn: () => api<Snippet[]>(`/api/v1/snippets${filters.value}`),
})

const showForm = ref(false)
const editing = ref<Snippet | null>(null)

function invalidate() {
  queryClient.invalidateQueries({ queryKey: ['snippets'] })
  showForm.value = false
  editing.value = null
}

const saveSnippet = useMutation({
  mutationFn: (data: Record<string, unknown>) =>
    editing.value
      ? api<Snippet>(`/api/v1/snippets/${editing.value.id}`, { method: 'PATCH', body: data })
      : api<Snippet>('/api/v1/snippets', { method: 'POST', body: data }),
  onSuccess: invalidate,
})

const deleteSnippet = useMutation({
  mutationFn: (s: Snippet) => api(`/api/v1/snippets/${s.id}`, { method: 'DELETE' }),
  onSuccess: invalidate,
})

function startEdit(s: Snippet) {
  editing.value = s
  showForm.value = true
}

function confirmDelete(s: Snippet) {
  if (window.confirm(`Delete snippet "${s.title}"?`)) deleteSnippet.mutate(s)
}
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-4xl p-6">
      <div class="mb-6 flex flex-wrap items-center gap-3">
        <h1 class="text-2xl font-bold">Snippets</h1>
        <button
          class="ml-auto rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700"
          @click="editing = null; showForm = true"
        >
          New snippet
        </button>
      </div>

      <div class="mb-6 flex flex-wrap gap-3 text-sm">
        <input
          v-model="languageFilter"
          type="text"
          placeholder="Filter by language…"
          class="rounded-lg border border-slate-300 px-3 py-2"
        >
        <input
          v-model="tagFilter"
          type="text"
          placeholder="Filter by tag…"
          class="rounded-lg border border-slate-300 px-3 py-2"
        >
        <select
          v-model="projectFilter"
          class="rounded-lg border border-slate-300 px-3 py-2"
        >
          <option :value="null">All projects</option>
          <option v-for="p in projects ?? []" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>

      <SnippetForm
        v-if="showForm"
        :key="editing?.id ?? 'new'"
        :snippet="editing"
        :projects="projects ?? []"
        :busy="saveSnippet.isPending.value"
        class="mb-6"
        @submit="saveSnippet.mutate($event)"
        @cancel="showForm = false; editing = null"
      />

      <p v-if="isPending" class="text-slate-500">Loading snippets…</p>
      <p v-else-if="!snippets?.length" class="text-slate-500">
        No snippets found.
      </p>
      <div v-else class="flex flex-col gap-4">
        <SnippetCard
          v-for="s in snippets"
          :key="s.id"
          :snippet="s"
          @edit="startEdit(s)"
          @delete="confirmDelete(s)"
        />
      </div>
    </main>
  </div>
</template>
