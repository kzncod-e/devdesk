<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { Bookmark, Project, Snippet, Task } from '~/types/api'

interface SearchOut {
  projects: Project[]
  tasks: Task[]
  snippets: Snippet[]
  bookmarks: Bookmark[]
}

interface Item {
  key: string
  label: string
  hint?: string
  icon: string
  action: () => void
}

const { api } = useAuth()
const { open, hide } = useCommandPalette()

const query = ref('')
const results = ref<SearchOut | null>(null)
const loading = ref(false)
const activeIndex = ref(0)
const input = ref<HTMLInputElement | null>(null)
let debounce: ReturnType<typeof setTimeout> | null = null

const navItems: Item[] = [
  { key: 'nav-projects', label: 'Go to Projects', icon: 'folder', action: () => go('/app') },
  { key: 'nav-snippets', label: 'Go to Snippets', icon: 'code', action: () => go('/app/snippets') },
  { key: 'nav-bookmarks', label: 'Go to Bookmarks', icon: 'bookmark', action: () => go('/app/bookmarks') },
]

function go(path: string) {
  hide()
  navigateTo(path)
}

const groups = computed<{ label: string; items: Item[] }[]>(() => {
  if (!query.value.trim()) {
    return [{ label: 'Navigate', items: navItems }]
  }
  if (!results.value) return []
  const out: { label: string; items: Item[] }[] = []
  const r = results.value
  if (r.projects.length) {
    out.push({
      label: 'Projects',
      items: r.projects.map(p => ({
        key: `p-${p.id}`,
        label: p.name,
        hint: p.description,
        icon: 'folder',
        action: () => go(`/app/projects/${p.id}`),
      })),
    })
  }
  if (r.tasks.length) {
    out.push({
      label: 'Tasks',
      items: r.tasks.map(t => ({
        key: `t-${t.id}`,
        label: t.title,
        hint: t.description,
        icon: 'check',
        action: () => go(`/app/projects/${t.project_id}`),
      })),
    })
  }
  if (r.snippets.length) {
    out.push({
      label: 'Snippets',
      items: r.snippets.map(s => ({
        key: `s-${s.id}`,
        label: s.title,
        hint: s.language,
        icon: 'code',
        action: () => go('/app/snippets'),
      })),
    })
  }
  if (r.bookmarks.length) {
    out.push({
      label: 'Bookmarks',
      items: r.bookmarks.map(b => ({
        key: `b-${b.id}`,
        label: b.title || b.url,
        hint: b.url,
        icon: 'bookmark',
        action: () => go('/app/bookmarks'),
      })),
    })
  }
  return out
})

const flat = computed(() => groups.value.flatMap(g => g.items))

watch(query, (q) => {
  activeIndex.value = 0
  if (debounce) clearTimeout(debounce)
  if (!q.trim()) {
    results.value = null
    loading.value = false
    return
  }
  loading.value = true
  debounce = setTimeout(async () => {
    try {
      results.value = await api<SearchOut>(`/api/v1/search?q=${encodeURIComponent(q)}&limit=6`)
    } catch {
      results.value = { projects: [], tasks: [], snippets: [], bookmarks: [] }
    } finally {
      loading.value = false
    }
  }, 180)
})

watch(open, async (isOpen) => {
  if (isOpen) {
    query.value = ''
    results.value = null
    activeIndex.value = 0
    await nextTick()
    input.value?.focus()
  }
})

function move(delta: number) {
  const n = flat.value.length
  if (!n) return
  activeIndex.value = (activeIndex.value + delta + n) % n
}

function onKeydown(e: KeyboardEvent) {
  const cmdK = (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k'
  if (cmdK) {
    e.preventDefault()
    useCommandPalette().toggle()
    return
  }
  if (!open.value) return
  if (e.key === 'Escape') hide()
  else if (e.key === 'ArrowDown') {
    e.preventDefault()
    move(1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    move(-1)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    flat.value[activeIndex.value]?.action()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition name="backdrop">
      <div
        v-if="open"
        class="fixed inset-0 z-[65] flex items-start justify-center bg-black/45 px-4 pt-[12vh] backdrop-blur-sm"
        @click.self="hide"
      >
        <Transition name="dialog" appear>
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
            class="w-full max-w-xl overflow-hidden rounded-2xl border border-line bg-surface shadow-overlay"
          >
            <div class="flex items-center gap-3 border-b border-line px-4">
              <UiIcon name="search" :size="18" class="text-ink-subtle" />
              <input
                ref="input"
                v-model="query"
                type="search"
                aria-label="Search projects, tasks, snippets and bookmarks"
                placeholder="Search projects, tasks, snippets, bookmarks…"
                class="h-14 flex-1 bg-transparent text-sm text-ink outline-none placeholder:text-ink-subtle"
              >
              <kbd class="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 text-[10px] font-medium text-ink-subtle">ESC</kbd>
            </div>

            <div class="max-h-[52vh] overflow-y-auto overscroll-contain p-2">
              <div v-if="loading" class="space-y-1.5 p-2">
                <UiSkeleton v-for="i in 4" :key="i" class="h-10 w-full rounded-lg" />
              </div>

              <p
                v-else-if="query.trim() && !flat.length"
                class="px-3 py-10 text-center text-sm text-ink-muted"
              >
                No results for “{{ query }}”.
              </p>

              <div v-for="group in groups" v-else :key="group.label" class="mb-1.5">
                <p class="px-2.5 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-ink-subtle">
                  {{ group.label }}
                </p>
                <button
                  v-for="item in group.items"
                  :key="item.key"
                  type="button"
                  :class="[
                    'flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left transition',
                    flat[activeIndex]?.key === item.key ? 'bg-accent-soft' : 'hover:bg-surface-2',
                  ]"
                  @mousemove="activeIndex = flat.findIndex(f => f.key === item.key)"
                  @click="item.action"
                >
                  <span
                    class="grid size-7 shrink-0 place-items-center rounded-md bg-surface-2 text-ink-muted"
                    :class="flat[activeIndex]?.key === item.key && 'text-accent'"
                  >
                    <UiIcon :name="item.icon" :size="15" />
                  </span>
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-sm text-ink">{{ item.label }}</span>
                    <span v-if="item.hint" class="block truncate text-xs text-ink-subtle">{{ item.hint }}</span>
                  </span>
                  <UiIcon
                    v-if="flat[activeIndex]?.key === item.key"
                    name="chevron"
                    :size="15"
                    class="text-accent"
                  />
                </button>
              </div>
            </div>

            <div class="flex items-center gap-4 border-t border-line px-4 py-2.5 text-[11px] text-ink-subtle">
              <span class="flex items-center gap-1"><kbd class="rounded border border-line px-1">↑</kbd><kbd class="rounded border border-line px-1">↓</kbd> navigate</span>
              <span class="flex items-center gap-1"><kbd class="rounded border border-line px-1">↵</kbd> open</span>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
