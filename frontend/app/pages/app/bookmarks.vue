<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { useConfirm } from '~/composables/useConfirm'
import { useToast } from '~/composables/useToast'

import type { Bookmark, Project } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'app' })

const { api } = useAuth()
const queryClient = useQueryClient()
const { confirm } = useConfirm()
const { success, error } = useToast()

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

const { data: bookmarks, isPending } = useQuery({
  queryKey: ['bookmarks', filters],
  queryFn: () => api<Bookmark[]>(`/api/v1/bookmarks${filters.value}`),
})

const hasFilters = computed(() => !!tagFilter.value || projectFilter.value !== null)

const showForm = ref(false)
const editing = ref<Bookmark | null>(null)

function openCreate() {
  editing.value = null
  showForm.value = true
}
function startEdit(b: Bookmark) {
  editing.value = b
  showForm.value = true
}
function closeForm() {
  showForm.value = false
  editing.value = null
}

const saveBookmark = useMutation({
  mutationFn: (data: Record<string, unknown>) =>
    editing.value
      ? api<Bookmark>(`/api/v1/bookmarks/${editing.value.id}`, { method: 'PATCH', body: data })
      : api<Bookmark>('/api/v1/bookmarks', { method: 'POST', body: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['bookmarks'] })
    success(editing.value ? 'Bookmark updated' : 'Bookmark added')
    closeForm()
    // metadata lands asynchronously after create; refresh shortly after
    setTimeout(() => queryClient.invalidateQueries({ queryKey: ['bookmarks'] }), 1500)
  },
  onError: () => error('Could not save bookmark'),
})

const deleteBookmark = useMutation({
  mutationFn: (b: Bookmark) => api(`/api/v1/bookmarks/${b.id}`, { method: 'DELETE' }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['bookmarks'] })
    success('Bookmark deleted')
  },
})

async function confirmDelete(b: Bookmark) {
  const ok = await confirm({
    title: `Delete bookmark?`,
    message: b.title || b.url,
    confirmLabel: 'Delete',
    danger: true,
  })
  if (ok) deleteBookmark.mutate(b)
}
</script>

<template>
  <div class="mx-auto max-w-4xl px-5 py-8 md:px-8">
    <header class="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-ink">Bookmarks</h1>
        <p class="mt-1 text-sm text-ink-muted">Links worth keeping.</p>
      </div>
      <UiButton variant="primary" icon="plus" @click="openCreate">New bookmark</UiButton>
    </header>

    <div class="mb-6 flex flex-wrap gap-3">
      <div class="relative">
        <UiIcon name="tag" :size="15" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle" />
        <input v-model="tagFilter" type="text" placeholder="Tag…" class="field-input w-44 pl-9">
      </div>
      <select v-model="projectFilter" class="field-input w-48">
        <option :value="null">All projects</option>
        <option v-for="p in projects ?? []" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </div>

    <div v-if="isPending" class="flex flex-col gap-3">
      <div v-for="i in 5" :key="i" class="flex items-center gap-3.5 rounded-card border border-line bg-surface p-3.5">
        <UiSkeleton class="size-10 rounded-lg" />
        <div class="flex-1 space-y-2">
          <UiSkeleton class="h-4 w-1/2" />
          <UiSkeleton class="h-3 w-1/3" />
        </div>
      </div>
    </div>

    <UiEmptyState
      v-else-if="!bookmarks?.length && !hasFilters"
      icon="bookmark"
      title="No bookmarks yet"
      description="Paste a URL and we'll fetch its title, description and favicon for you."
    >
      <UiButton variant="primary" icon="plus" @click="openCreate">Add a bookmark</UiButton>
    </UiEmptyState>

    <UiEmptyState
      v-else-if="!bookmarks?.length"
      icon="search"
      title="No bookmarks found"
      description="Try clearing your filters."
    />

    <TransitionGroup v-else tag="div" name="fade" class="stagger flex flex-col gap-3">
      <BookmarkCard
        v-for="(b, i) in bookmarks"
        :key="b.id"
        :bookmark="b"
        :style="{ '--i': i }"
        @edit="startEdit(b)"
        @delete="confirmDelete(b)"
      />
    </TransitionGroup>

    <UiModal
      :open="showForm"
      :title="editing ? 'Edit bookmark' : 'New bookmark'"
      :subtitle="editing ? 'Update tags and title.' : 'Save a link to revisit later.'"
      @close="closeForm"
    >
      <BookmarkForm
        v-if="showForm"
        :key="editing?.id ?? 'new'"
        :bookmark="editing"
        :projects="projects ?? []"
        :busy="saveBookmark.isPending.value"
        @submit="saveBookmark.mutate($event)"
        @cancel="closeForm"
      />
    </UiModal>
  </div>
</template>
