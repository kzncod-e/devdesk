<script setup lang="ts">
const features = [
  { icon: 'folder', title: 'Projects & boards', desc: 'Kanban boards with drag-and-drop tasks, priorities and due dates.' },
  { icon: 'code', title: 'Code snippets', desc: 'A syntax-highlighted library for the code you reach for daily.' },
  { icon: 'bookmark', title: 'Smart bookmarks', desc: 'Paste a link — title, description and favicon are fetched for you.' },
  { icon: 'command', title: 'Command palette', desc: 'Jump anywhere and search everything with ⌘K.' },
]
</script>

<template>
  <div class="min-h-screen overflow-hidden bg-white text-ink">

    <!-- Nav -->
    <header class="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
      <div class="flex items-center gap-2.5">
        <span class="grid size-8 place-items-center rounded-lg bg-accent text-accent-fg shadow-sm">
          <UiIcon name="layers" :size="18" />
        </span>
        <span class="text-[15px] font-semibold tracking-tight text-gray-900">DevDesk</span>
      </div>
      <div class="flex items-center gap-2">
        <NuxtLink to="/login"><UiButton variant="ghost">Log in</UiButton></NuxtLink>
        <NuxtLink to="/register"><UiButton variant="primary">Get started</UiButton></NuxtLink>
      </div>
    </header>

    <!-- Hero copy -->
    <section class="mx-auto max-w-3xl px-6 pb-14 pt-16 text-center">
      <p class="mb-4 text-xs font-semibold uppercase tracking-widest text-ink-muted">
        Developer Workspace
      </p>
      <h1 class="text-5xl font-bold leading-tight tracking-tight text-gray-950 md:text-6xl lg:text-[4.25rem]">
        Your dev workflow,<br>
        organized beautifully.
      </h1>
      <p class="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-gray-500">
        Projects, tasks, snippets and bookmarks — all in one fast, focused workspace
        built for the way developers actually work.
      </p>
      <div class="mt-8 flex items-center justify-center gap-3">
        <NuxtLink to="/register">
          <UiButton variant="primary" size="lg">Start for free →</UiButton>
        </NuxtLink>
        <NuxtLink to="/login">
          <UiButton variant="ghost" size="lg">Log in</UiButton>
        </NuxtLink>
      </div>
    </section>

    <!-- Product interface section -->
    <section class="relative mx-auto max-w-6xl px-4 pb-0">
      <!-- Dark container with gradient -->
      <div class="relative overflow-hidden rounded-t-2xl bg-gray-950 pt-8 shadow-2xl ring-1 ring-white/10">

        <!-- Subtle glow behind the mockup -->
        <div class="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2 h-64 w-3/4 rounded-full bg-accent opacity-10 blur-3xl" aria-hidden="true" />

        <!-- Browser chrome -->
        <div class="relative mx-auto w-[92%] overflow-hidden rounded-t-xl border border-white/10 bg-[#1a1a2e] shadow-xl">
          <!-- Chrome bar -->
          <div class="flex items-center gap-2 border-b border-white/10 bg-[#111] px-4 py-2.5">
            <span class="size-3 rounded-full bg-red-500/80" />
            <span class="size-3 rounded-full bg-yellow-400/80" />
            <span class="size-3 rounded-full bg-green-500/80" />
            <div class="mx-auto flex w-56 items-center justify-center rounded-md bg-white/5 px-3 py-1 text-[11px] text-gray-500">
              devdesk.app
            </div>
          </div>

          <!-- App shell -->
          <div class="flex h-105 overflow-hidden">

            <!-- Sidebar -->
            <aside class="flex w-48 shrink-0 flex-col gap-1 border-r border-white/5 bg-[#0f0f1a] p-3">
              <div class="mb-3 flex items-center gap-2 px-2 py-1">
                <span class="grid size-6 place-items-center rounded bg-accent text-white text-[10px]">D</span>
                <span class="text-xs font-semibold text-white/80">DevDesk</span>
              </div>
              <div v-for="(label, icon) in { '⬡': 'Projects', '☰': 'Tasks', '◇': 'Snippets', '⬖': 'Bookmarks' }" :key="icon" class="flex items-center gap-2 rounded-md px-2 py-1.5 text-[11px] text-white/40 hover:bg-white/5 hover:text-white/70" :class="{ 'bg-white/8 text-white/80': label === 'Projects' }">
                <span class="text-[10px]">{{ icon }}</span>
                {{ label }}
              </div>
            </aside>

            <!-- Main content: Kanban board -->
            <div class="flex flex-1 flex-col overflow-hidden bg-[#12121f]">
              <!-- Top bar -->
              <div class="flex items-center justify-between border-b border-white/5 px-5 py-3">
                <div>
                  <p class="text-[11px] font-semibold text-white/80">DevDesk v2</p>
                  <p class="text-[10px] text-white/30">4 tasks · 2 in progress</p>
                </div>
                <div class="flex gap-2">
                  <span class="rounded-full bg-accent/20 px-2.5 py-0.5 text-[10px] font-medium text-accent">Active</span>
                  <span class="rounded-full bg-white/5 px-2.5 py-0.5 text-[10px] text-white/40">+ Add task</span>
                </div>
              </div>

              <!-- Kanban columns -->
              <div class="flex flex-1 gap-3 overflow-x-auto p-4">

                <!-- Todo -->
                <div class="flex w-44 shrink-0 flex-col gap-2">
                  <p class="mb-1 text-[10px] font-semibold uppercase tracking-wider text-white/30">Todo</p>
                  <div class="rounded-lg border border-white/5 bg-white/3 p-3">
                    <p class="text-[11px] font-medium text-white/70">Setup CI pipeline</p>
                    <div class="mt-2 flex items-center gap-1.5">
                      <span class="rounded bg-yellow-500/20 px-1.5 py-0.5 text-[9px] text-yellow-400">medium</span>
                    </div>
                  </div>
                  <div class="rounded-lg border border-white/5 bg-white/3 p-3">
                    <p class="text-[11px] font-medium text-white/70">Write API docs</p>
                    <div class="mt-2 flex items-center gap-1.5">
                      <span class="rounded bg-gray-500/20 px-1.5 py-0.5 text-[9px] text-gray-400">low</span>
                    </div>
                  </div>
                </div>

                <!-- In Progress -->
                <div class="flex w-44 shrink-0 flex-col gap-2">
                  <p class="mb-1 text-[10px] font-semibold uppercase tracking-wider text-white/30">In Progress</p>
                  <div class="rounded-lg border border-accent/20 bg-accent/5 p-3 ring-1 ring-accent/10">
                    <p class="text-[11px] font-medium text-white/80">Auth middleware</p>
                    <div class="mt-2 flex items-center gap-1.5">
                      <span class="rounded bg-red-500/20 px-1.5 py-0.5 text-[9px] text-red-400">high</span>
                    </div>
                  </div>
                  <div class="rounded-lg border border-white/5 bg-white/3 p-3">
                    <p class="text-[11px] font-medium text-white/70">Design system tokens</p>
                    <div class="mt-2 flex items-center gap-1.5">
                      <span class="rounded bg-yellow-500/20 px-1.5 py-0.5 text-[9px] text-yellow-400">medium</span>
                    </div>
                  </div>
                </div>

                <!-- Done -->
                <div class="flex w-44 shrink-0 flex-col gap-2">
                  <p class="mb-1 text-[10px] font-semibold uppercase tracking-wider text-white/30">Done</p>
                  <div class="rounded-lg border border-white/5 bg-white/3 p-3 opacity-60">
                    <p class="text-[11px] font-medium text-white/70 line-through">Database schema</p>
                    <div class="mt-2 flex items-center gap-1.5">
                      <span class="rounded bg-green-500/20 px-1.5 py-0.5 text-[9px] text-green-400">done</span>
                    </div>
                  </div>
                </div>

              </div>
            </div>

          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="bg-white px-6 pb-24 pt-20">
      <div class="mx-auto grid max-w-5xl grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="f in features"
          :key="f.title"
          class="rounded-2xl border border-gray-100 bg-gray-50 p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-md"
        >
          <span class="grid size-10 place-items-center rounded-xl bg-accent-soft text-accent">
            <UiIcon :name="f.icon" :size="20" />
          </span>
          <h3 class="mt-4 text-sm font-semibold text-gray-900">{{ f.title }}</h3>
          <p class="mt-1.5 text-sm text-gray-500">{{ f.desc }}</p>
        </div>
      </div>
    </section>

  </div>
</template>
