<script setup lang="ts">
import type { Template } from '~/types/api'

// Public, server-rendered (crawlable) — no auth, no app layout.
definePageMeta({ layout: false })

useSeoMeta({
  title: 'Template Gallery — DevDesk',
  description:
    'Browse community project and snippet templates. Scaffold a new project or '
    + 'reusable snippet in one click with DevDesk.',
  ogTitle: 'DevDesk Template Gallery',
  ogDescription: 'Ready-made project and snippet templates for developers.',
})

const kind = ref<'all' | 'project' | 'snippet'>('all')

const { data, pending } = await useFetch<Template[]>('/api/v1/templates/gallery', {
  query: { limit: 60 },
  default: () => [],
})

const visible = computed(() => {
  const all = data.value ?? []
  return kind.value === 'all' ? all : all.filter((t) => t.kind === kind.value)
})

const tabs = [
  { value: 'all', label: 'All' },
  { value: 'project', label: 'Projects' },
  { value: 'snippet', label: 'Snippets' },
] as const
</script>

<template>
  <div class="min-h-screen bg-canvas text-ink">
    <header class="border-b border-line bg-surface/70 backdrop-blur">
      <div class="mx-auto flex max-w-6xl items-center gap-3 px-5 py-4 md:px-8">
        <NuxtLink to="/" class="flex items-center gap-2">
          <span class="grid size-8 place-items-center rounded-lg bg-accent text-accent-fg">
            <UiIcon name="layers" :size="18" />
          </span>
          <span class="text-sm font-semibold">DevDesk</span>
        </NuxtLink>
        <nav class="ml-auto flex items-center gap-2">
          <NuxtLink to="/login" class="text-sm font-medium text-ink-muted transition hover:text-ink">
            Log in
          </NuxtLink>
          <NuxtLink
            to="/register"
            class="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition hover:opacity-90"
          >
            Get started
          </NuxtLink>
        </nav>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-5 py-12 md:px-8">
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-semibold tracking-tight">Template Gallery</h1>
        <p class="mx-auto mt-2 max-w-xl text-sm text-ink-muted">
          Community-published project and snippet templates. Sign in to scaffold any of
          these into your workspace in one click.
        </p>
      </div>

      <div class="mb-8 flex justify-center">
        <div class="flex gap-1 rounded-lg border border-line bg-surface p-1 shadow-sm">
          <button
            v-for="t in tabs"
            :key="t.value"
            :class="[
              'rounded-md px-3 py-1 text-sm font-medium transition',
              kind === t.value ? 'bg-accent-soft text-accent' : 'text-ink-muted hover:text-ink',
            ]"
            @click="kind = t.value"
          >
            {{ t.label }}
          </button>
        </div>
      </div>

      <div v-if="pending" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <UiSkeleton v-for="i in 6" :key="i" class="h-36 rounded-card" />
      </div>

      <UiEmptyState
        v-else-if="!visible.length"
        icon="layers"
        title="No public templates yet"
        description="Published templates will appear here."
      />

      <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article
          v-for="t in visible"
          :key="t.id"
          class="flex flex-col gap-3 rounded-card border border-line bg-surface p-5 shadow-card"
        >
          <div class="flex items-start gap-3">
            <span class="grid size-9 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent">
              <UiIcon :name="t.kind === 'project' ? 'folder' : 'code'" :size="18" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold text-ink">{{ t.name }}</p>
              <UiBadge :tone="t.kind === 'project' ? 'indigo' : 'gray'" class="mt-1 capitalize">
                {{ t.kind }}
              </UiBadge>
            </div>
          </div>
          <p class="line-clamp-2 min-h-8 text-xs text-ink-muted">
            {{ t.description || 'No description.' }}
          </p>
          <div class="mt-auto flex items-center justify-between">
            <span class="text-xs text-ink-subtle">Used {{ t.use_count }}×</span>
            <NuxtLink
              to="/app/templates"
              class="inline-flex items-center gap-1 text-sm font-medium text-accent transition hover:opacity-80"
            >
              Use in DevDesk
              <UiIcon name="chevron" :size="15" />
            </NuxtLink>
          </div>
        </article>
      </div>
    </main>
  </div>
</template>
