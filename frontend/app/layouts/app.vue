<script setup lang="ts">
const { user, logout } = useAuth()
const { mode, toggle: toggleTheme } = useTheme()
const { show: showPalette } = useCommandPalette()
const { isReady, hasOnboarded, markReady } = useAppReady()

const showSplash = ref(!hasOnboarded.value)

onMounted(() => {
  if (showSplash.value) {
    const MIN_MS = 1200
    const start = Date.now()
    const done = () => {
      const elapsed = Date.now() - start
      const remaining = Math.max(0, MIN_MS - elapsed)
      setTimeout(() => {
        showSplash.value = false
        markReady()
      }, remaining)
    }
    // mark ready once user data is present or after a short timeout
    if (user.value) {
      done()
    } else {
      const stop = watch(user, (u) => {
        if (u) { stop(); done() }
      })
      setTimeout(() => { stop(); showSplash.value = false; markReady() }, 4000)
    }
  } else {
    isReady.value = true
  }
})

const nav = [
  { to: '/app', label: 'Projects', icon: 'folder' },
  { to: '/app/snippets', label: 'Snippets', icon: 'code' },
  { to: '/app/bookmarks', label: 'Bookmarks', icon: 'bookmark' },
  { to: '/app/settings', label: 'Settings', icon: 'settings' },
]

const route = useRoute()
function isActive(to: string) {
  if (to === '/app') return route.path === '/app' || route.path.startsWith('/app/projects')
  return route.path.startsWith(to)
}

const initials = computed(() =>
  (user.value?.name ?? 'U')
    .split(' ')
    .map(p => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase(),
)
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-canvas text-ink">
    <!-- Sidebar -->
    <aside class="hidden w-60 shrink-0 flex-col border-r border-line bg-surface/60 px-3 py-4 md:flex">
      <NuxtLink to="/app" class="mb-6 flex items-center gap-2.5 px-2">
        <span class="grid size-8 place-items-center rounded-lg bg-accent text-accent-fg shadow-sm">
          <UiIcon name="layers" :size="18" />
        </span>
        <span class="text-[15px] font-semibold tracking-tight">DevDesk</span>
      </NuxtLink>

      <button
        class="mb-4 flex items-center gap-2.5 rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink-subtle shadow-sm transition hover:border-line-strong hover:text-ink-muted"
        @click="showPalette"
      >
        <UiIcon name="search" :size="16" />
        <span class="flex-1 text-left">Search…</span>
        <kbd class="rounded border border-line bg-surface-2 px-1.5 py-0.5 text-[10px] font-medium">⌘K</kbd>
      </button>

      <nav class="flex flex-col gap-1">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          :class="[
            'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
            isActive(item.to)
              ? 'text-ink'
              : 'text-ink-muted hover:bg-surface-2 hover:text-ink',
          ]"
        >
          <span
            v-if="isActive(item.to)"
            class="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-accent transition-all"
            aria-hidden="true"
          />
          <span
            :class="[
              'grid size-7 place-items-center rounded-md transition',
              isActive(item.to) ? 'bg-accent-soft text-accent' : 'text-ink-subtle group-hover:text-ink-muted',
            ]"
          >
            <UiIcon :name="item.icon" :size="17" />
          </span>
          {{ item.label }}
        </NuxtLink>
      </nav>

      <div class="mt-auto flex items-center gap-2 border-t border-line pt-3">
        <span class="grid size-8 shrink-0 place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent">
          {{ initials }}
        </span>
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium text-ink">{{ user?.name ?? '—' }}</p>
          <p class="truncate text-xs text-ink-subtle">{{ user?.email }}</p>
        </div>
        <UiIconButton icon="logout" label="Log out" size="sm" @click="logout()" />
      </div>
    </aside>

    <!-- Main column -->
    <div class="flex min-w-0 flex-1 flex-col">
      <!-- Top bar -->
      <header class="flex h-14 shrink-0 items-center gap-3 border-b border-line bg-surface/70 px-4 backdrop-blur md:px-6">
        <NuxtLink to="/app" class="flex items-center gap-2 md:hidden">
          <span class="grid size-7 place-items-center rounded-lg bg-accent text-accent-fg">
            <UiIcon name="layers" :size="16" />
          </span>
        </NuxtLink>

        <button
          class="flex flex-1 items-center gap-2.5 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-ink-subtle transition hover:border-line-strong md:max-w-md"
          @click="showPalette"
        >
          <UiIcon name="search" :size="16" />
          <span class="flex-1 text-left">Search everything…</span>
          <kbd class="hidden rounded border border-line bg-surface-2 px-1.5 py-0.5 text-[10px] font-medium sm:block">⌘K</kbd>
        </button>

        <div class="ml-auto flex items-center gap-1">
          <UiIconButton
            :icon="mode === 'dark' ? 'sun' : 'moon'"
            :label="mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
            @click="toggleTheme"
          />
          <UiMenu align="right">
            <template #trigger>
              <button
                class="grid size-9 place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent transition hover:brightness-95"
                aria-label="Account menu"
              >
                {{ initials }}
              </button>
            </template>
            <div class="px-2.5 py-2">
              <p class="truncate text-sm font-medium text-ink">{{ user?.name }}</p>
              <p class="truncate text-xs text-ink-subtle">{{ user?.email }}</p>
              <UiBadge v-if="user?.role" tone="indigo" class="mt-1.5 capitalize">{{ user.role }}</UiBadge>
            </div>
            <div class="my-1 h-px bg-line" />
            <UiMenuItem icon="settings" @click="navigateTo('/app/settings')">Settings</UiMenuItem>
            <UiMenuItem icon="logout" danger @click="logout()">Log out</UiMenuItem>
          </UiMenu>
        </div>
      </header>

      <!-- Mobile nav -->
      <nav class="flex shrink-0 gap-1 border-b border-line bg-surface/60 px-4 py-2 md:hidden">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium',
            isActive(item.to) ? 'bg-accent-soft text-accent' : 'text-ink-muted',
          ]"
        >
          <UiIcon :name="item.icon" :size="16" />
          {{ item.label }}
        </NuxtLink>
      </nav>

      <main class="flex-1 overflow-y-auto">
        <slot />
      </main>
    </div>

    <CommandPalette />
    <UiToaster />
    <UiConfirm />
    <AppSplash :show="showSplash" />
  </div>
</template>
