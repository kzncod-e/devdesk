<script setup lang="ts">
const features = [
  { icon: 'folder', title: 'Projects & boards', desc: 'Kanban boards with drag-and-drop tasks, priorities and due dates.' },
  { icon: 'code', title: 'Code snippets', desc: 'A syntax-highlighted library for the code you reach for daily.' },
  { icon: 'bookmark', title: 'Smart bookmarks', desc: 'Paste a link — title, description and favicon are fetched for you.' },
  { icon: 'command', title: 'Command palette', desc: 'Jump anywhere and search everything with ⌘K.' },
]
</script>

<template>
  <div class="relative min-h-screen overflow-hidden bg-canvas text-ink">
    <div class="bg-grid pointer-events-none absolute inset-0 opacity-40 [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" aria-hidden="true" />
    <div class="pointer-events-none absolute left-1/2 top-0 z-0 h-72 w-2xl -translate-x-1/2 rounded-full bg-accent-soft blur-3xl" aria-hidden="true" />

    <header class="relative mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
      <div class="flex items-center gap-2.5">
        <span class="grid size-8 place-items-center rounded-lg bg-accent text-accent-fg shadow-sm">
          <UiIcon name="layers" :size="18" />
        </span>
        <span class="text-[15px] font-semibold tracking-tight">DevDesk</span>
      </div>
      <div class="flex items-center gap-2">
        <NuxtLink to="/login"><UiButton variant="ghost">Log in</UiButton></NuxtLink>
        <NuxtLink to="/register"><UiButton variant="primary">Get started</UiButton></NuxtLink>
      </div>
    </header>

    <main class="relative mx-auto max-w-6xl px-6">
      <section class="enter-rise mx-auto max-w-2xl py-20 text-center md:py-28">
        <span class="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-ink-muted shadow-sm">
          <UiIcon name="sparkles" :size="13" class="text-accent" />
          One workspace for daily development
        </span>
        <h1 class="mt-6 text-4xl font-semibold tracking-tight md:text-6xl">
          Your dev workflow,<br>
          <span class="bg-linear-to-r from-accent to-violet-500 bg-clip-text text-transparent">beautifully organized.</span>
        </h1>
        <p class="mx-auto mt-5 max-w-xl text-lg text-ink-muted">
          Projects, tasks, snippets and bookmarks — together in one fast, focused
          workspace built for the way developers actually work.
        </p>
        <div class="mt-8 flex items-center justify-center gap-3">
          <NuxtLink to="/register"><UiButton variant="primary" size="lg" icon-right="chevron">Start for free</UiButton></NuxtLink>
          <NuxtLink to="/login"><UiButton variant="secondary" size="lg">Log in</UiButton></NuxtLink>
        </div>
      </section>

      <section class="stagger grid grid-cols-1 gap-4 pb-24 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="(f, i) in features"
          :key="f.title"
          :style="{ '--i': i }"
          class="rounded-card border border-line bg-surface p-5 shadow-card transition-all duration-200 hover:-translate-y-1 hover:shadow-card-hover"
        >
          <span class="grid size-10 place-items-center rounded-lg bg-accent-soft text-accent">
            <UiIcon :name="f.icon" :size="20" />
          </span>
          <h3 class="mt-4 text-sm font-semibold">{{ f.title }}</h3>
          <p class="mt-1.5 text-sm text-ink-muted">{{ f.desc }}</p>
        </div>
      </section>
    </main>
  </div>
</template>
