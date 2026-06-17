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
  keywords?: string
  action: () => void
}

const { api, logout } = useAuth()
const { open, hide } = useCommandPalette()
const { mode, toggle: toggleTheme } = useTheme()
const { workspaces, workspaceId, setCurrent } = useWorkspace()
const { request: requestCreate } = useQuickCreate()
const { recents, pushRecent } = useSearchRecents()

const query = ref('')
const results = ref<SearchOut | null>(null)
const loading = ref(false)
const activeIndex = ref(0)
const input = ref<HTMLInputElement | null>(null)
let debounce: ReturnType<typeof setTimeout> | null = null

// ── Scope prefixes: "/p foo" searches only projects, etc. ──────────────────────
const SCOPES: Record<string, keyof SearchOut> = {
  p: 'projects',
  t: 'tasks',
  s: 'snippets',
  b: 'bookmarks',
}
const scopeMatch = computed(() => query.value.match(/^\/([ptsb])\s+(.*)$/i))
const scope = computed<keyof SearchOut | null>(() =>
  scopeMatch.value ? SCOPES[scopeMatch.value[1]!.toLowerCase()]! : null,
)
const searchTerm = computed(() =>
  (scopeMatch.value ? scopeMatch.value[2]! : query.value).trim(),
)

function go(path: string) {
  hide()
  navigateTo(path)
}

function openResult(path: string) {
  if (searchTerm.value) pushRecent(searchTerm.value)
  go(path)
}

// ── Actions ────────────────────────────────────────────────────────────────────
const navItems: Item[] = [
  { key: 'nav-projects', label: 'Go to Projects', icon: 'folder', action: () => go('/app') },
  { key: 'nav-snippets', label: 'Go to Snippets', icon: 'code', action: () => go('/app/snippets') },
  { key: 'nav-bookmarks', label: 'Go to Bookmarks', icon: 'bookmark', action: () => go('/app/bookmarks') },
]

const actions = computed<Item[]>(() => {
  const list: Item[] = [
    { key: 'a-new-project', label: 'New project', icon: 'plus', keywords: 'create add board', action: () => { hide(); requestCreate('project') } },
    { key: 'a-new-snippet', label: 'New snippet', icon: 'code', keywords: 'create add code', action: () => { hide(); requestCreate('snippet') } },
    { key: 'a-new-bookmark', label: 'New bookmark', icon: 'bookmark', keywords: 'create add link url', action: () => { hide(); requestCreate('bookmark') } },
    { key: 'a-templates', label: 'Browse templates', icon: 'layers', keywords: 'template scaffold reuse gallery', action: () => go('/app/templates') },
    { key: 'a-invite', label: 'Invite member', icon: 'user-plus', keywords: 'team people add invite', action: () => go('/app/settings') },
    { key: 'a-theme', label: mode.value === 'dark' ? 'Switch to light theme' : 'Switch to dark theme', icon: mode.value === 'dark' ? 'sun' : 'moon', keywords: 'theme dark light mode appearance', action: () => toggleTheme() },
    { key: 'a-settings', label: 'Open settings', icon: 'settings', keywords: 'profile account preferences', action: () => go('/app/settings') },
    { key: 'a-logout', label: 'Log out', icon: 'logout', keywords: 'signout sign out exit', action: () => { hide(); logout() } },
  ]
  for (const w of workspaces.value) {
    if (w.id === workspaceId.value) continue
    list.push({
      key: `ws-${w.id}`,
      label: `Switch to ${w.name}`,
      hint: 'Workspace',
      icon: 'layers',
      keywords: `workspace switch ${w.name}`,
      action: () => { hide(); setCurrent(w.id) },
    })
  }
  return list
})

function matchesAction(a: Item, term: string): boolean {
  const hay = `${a.label} ${a.keywords ?? ''}`.toLowerCase()
  return term.toLowerCase().split(/\s+/).filter(Boolean).every((t) => hay.includes(t))
}

// ── Result groups ───────────────────────────────────────────────────────────────
function resultGroups(r: SearchOut): { label: string; items: Item[] }[] {
  const out: { label: string; items: Item[] }[] = []
  if (r.projects.length) {
    out.push({ label: 'Projects', items: r.projects.map((p) => ({ key: `p-${p.id}`, label: p.name, hint: p.description, icon: 'folder', action: () => openResult(`/app/projects/${p.id}`) })) })
  }
  if (r.tasks.length) {
    out.push({ label: 'Tasks', items: r.tasks.map((t) => ({ key: `t-${t.id}`, label: t.title, hint: t.description, icon: 'check', action: () => openResult(`/app/projects/${t.project_id}`) })) })
  }
  if (r.snippets.length) {
    out.push({ label: 'Snippets', items: r.snippets.map((s) => ({ key: `s-${s.id}`, label: s.title, hint: s.language, icon: 'code', action: () => openResult('/app/snippets') })) })
  }
  if (r.bookmarks.length) {
    out.push({ label: 'Bookmarks', items: r.bookmarks.map((b) => ({ key: `b-${b.id}`, label: b.title || b.url, hint: b.url, icon: 'bookmark', action: () => openResult('/app/bookmarks') })) })
  }
  return out
}

const groups = computed<{ label: string; items: Item[] }[]>(() => {
  // Empty query → recents, actions, navigation.
  if (!query.value.trim()) {
    const out: { label: string; items: Item[] }[] = []
    if (recents.value.length) {
      out.push({
        label: 'Recent',
        items: recents.value.map((r, i) => ({ key: `r-${i}`, label: r, icon: 'search', action: () => { query.value = r } })),
      })
    }
    out.push({ label: 'Actions', items: actions.value })
    out.push({ label: 'Navigate', items: navItems })
    return out
  }

  const out: { label: string; items: Item[] }[] = []
  // Unscoped queries also surface matching actions ("new" → New project).
  if (!scope.value) {
    const acts = actions.value.filter((a) => matchesAction(a, searchTerm.value))
    if (acts.length) out.push({ label: 'Actions', items: acts })
  }
  if (results.value) out.push(...resultGroups(results.value))
  return out
})

const flat = computed(() => groups.value.flatMap((g) => g.items))
const showNoResults = computed(() => searchTerm.value !== '' && !loading.value && !flat.value.length)
const showScopeHint = computed(() => scope.value !== null && searchTerm.value === '')

watch([searchTerm, scope], ([term]) => {
  activeIndex.value = 0
  if (debounce) clearTimeout(debounce)
  if (!term) {
    results.value = null
    loading.value = false
    return
  }
  loading.value = true
  debounce = setTimeout(async () => {
    try {
      const params = new URLSearchParams({ q: term, limit: '6' })
      if (scope.value) params.set('types', scope.value)
      results.value = await api<SearchOut>(`/api/v1/search?${params.toString()}`)
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
                aria-label="Search or run a command"
                placeholder="Search or run a command…  (try /p /t /s /b)"
                class="h-14 flex-1 bg-transparent text-sm text-ink outline-none placeholder:text-ink-subtle"
              >
              <kbd class="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 text-[10px] font-medium text-ink-subtle">ESC</kbd>
            </div>

            <div class="max-h-[52vh] overflow-y-auto overscroll-contain p-2">
              <div v-if="loading" class="space-y-1.5 p-2">
                <UiSkeleton v-for="i in 4" :key="i" class="h-10 w-full rounded-lg" />
              </div>

              <p
                v-else-if="showScopeHint"
                class="px-3 py-10 text-center text-sm text-ink-muted"
              >
                Type to search {{ scope }}…
              </p>

              <p
                v-else-if="showNoResults"
                class="px-3 py-10 text-center text-sm text-ink-muted"
              >
                No results for “{{ searchTerm }}”.
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
              <span class="flex items-center gap-1"><kbd class="rounded border border-line px-1">↵</kbd> select</span>
              <span class="ml-auto hidden sm:flex items-center gap-1"><kbd class="rounded border border-line px-1">/p</kbd><kbd class="rounded border border-line px-1">/t</kbd><kbd class="rounded border border-line px-1">/s</kbd><kbd class="rounded border border-line px-1">/b</kbd> scope</span>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
