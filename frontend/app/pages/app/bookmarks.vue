<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Bookmark, Project } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const { api } = useAuth()
const queryClient = useQueryClient()

const tagFilter = ref('')
const projectFilter = ref<number | null>(null)

const filters = computed(() => {
  const params = new URLSearchParams()
  if (tagFilter.value) params.set('tag', tagFilter.value)
  if (projectFilter.value !== null) params.set('project_id', String(projectFilter.value))
  const qs = params.toString()
  return qs ? `?${qs}` : ''
})

const { data: projects } = useQuery({
  queryKey: ['projects'],
  queryFn: () => api<Project[]>('/api/v1/projects'),
})

const { data: bookmarks, isPending, refetch } = useQuery({
  queryKey: ['bookmarks', filters],
  queryFn: () => api<Bookmark[]>(`/api/v1/bookmarks${filters.value}`),
})

const showForm = ref(false)
const editing = ref<Bookmark | null>(null)

function invalidate() {
  queryClient.invalidateQueries({ queryKey: ['bookmarks'] })
  showForm.value = false
  editing.value = null
}

const saveBookmark = useMutation({
  mutationFn: (data: Record<string, unknown>) =>
    editing.value
      ? api<Bookmark>(`/api/v1/bookmarks/${editing.value.id}`, { method: 'PATCH', body: data })
      : api<Bookmark>('/api/v1/bookmarks', { method: 'POST', body: data }),
  onSuccess: () => {
    invalidate()
    // metadata lands asynchronously after create; refresh shortly after
    setTimeout(() => queryClient.invalidateQueries({ queryKey: ['bookmarks'] }), 1500)
  },
})

const deleteBookmark = useMutation({
  mutationFn: (b: Bookmark) => api(`/api/v1/bookmarks/${b.id}`, { method: 'DELETE' }),
  onSuccess: invalidate,
})

function startEdit(b: Bookmark) {
  editing.value = b
  showForm.value = true
}

function confirmDelete(b: Bookmark) {
  if (window.confirm(`Delete bookmark "${b.title || b.url}"?`)) deleteBookmark.mutate(b)
}
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-4xl p-6">
      <div class="mb-6 flex flex-wrap items-center gap-3">
        <h1 class="text-2xl font-bold">Bookmarks</h1>
        <button
          class="rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-100"
          @click="refetch()"
        >
          Refresh
        </button>
        <button
          class="ml-auto rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700"
          @click="editing = null; showForm = true"
        >
          New bookmark
        </button>
      </div>

      <div class="mb-6 flex flex-wrap gap-3 text-sm">
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

      <BookmarkForm
        v-if="showForm"
        :key="editing?.id ?? 'new'"
        :bookmark="editing"
        :projects="projects ?? []"
        :busy="saveBookmark.isPending.value"
        class="mb-6"
        @submit="saveBookmark.mutate($event)"
        @cancel="showForm = false; editing = null"
      />

      <p v-if="isPending" class="text-slate-500">Loading bookmarks…</p>
      <p v-else-if="!bookmarks?.length" class="text-slate-500">
        No bookmarks found.
      </p>
      <div v-else class="flex flex-col gap-3">
        <BookmarkCard
          v-for="b in bookmarks"
          :key="b.id"
          :bookmark="b"
          @edit="startEdit(b)"
          @delete="confirmDelete(b)"
        />
      </div>
    </main>
  </div>
</template>
