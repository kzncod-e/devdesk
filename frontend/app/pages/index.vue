<script setup lang="ts">
// Marketing landing — prerendered. Cosmos / orbital design, but every colour is
// driven by the app's design tokens, so it adapts to the saved light/dark theme.
import { ref, onMounted, onBeforeUnmount } from 'vue'

// Satellites orbiting the command core. Each lives on a ring at a fixed angle.
const orbits = [
  { ring: 1, angle: 18,  icon: 'board' },
  { ring: 1, angle: 205, icon: 'command' },
  { ring: 2, angle: 70,  icon: 'code' },
  { ring: 2, angle: 168, icon: 'bell' },
  { ring: 2, angle: 300, icon: 'comment' },
  { ring: 3, angle: 30,  icon: 'bookmark' },
  { ring: 3, angle: 132, icon: 'sparkles' },
  { ring: 3, angle: 248, icon: 'users' },
] as const

// Expandable feature cards — collapsed shows a one-liner, expanded reveals details.
const features = [
  { icon: 'board', title: 'Projects & boards', short: 'Kanban with drag-and-drop, priorities, assignees and due dates.',
    meta: 'kanban · drag · due dates',
    details: ['Drag tasks across Todo / In progress / Done', 'Assignees, priorities and due dates per card', 'Per-project boards that stay in sync'] },
  { icon: 'code', title: 'Code snippets', short: 'A syntax-highlighted library for the code you reach for daily.',
    meta: 'syntax · search · tags',
    details: ['Syntax highlighting for every language', 'Tag and full-text search across your library', 'One-click copy — never dig through old repos'] },
  { icon: 'bookmark', title: 'Smart bookmarks', short: 'Paste a link; title, description and favicon are fetched for you.',
    meta: 'auto-meta · favicon',
    details: ['Automatic title, description & favicon', 'Organised, searchable reading list', 'Files itself the moment you paste'] },
  { icon: 'command', title: 'Command palette', short: 'Jump anywhere and search everything from a single keystroke.',
    meta: '⌘K · jump · search',
    details: ['⌘K from anywhere in the app', 'Fuzzy search across all your data', 'Keyboard-first — hands never leave home row'] },
  { icon: 'sparkles', title: 'Themes & dark mode', short: 'A token-based design system that flips light and dark instantly.',
    meta: 'light · dark · tokens',
    details: ['Light and dark, switched in one click', 'Consistent semantic design tokens', 'Respects your system preference'] },
  { icon: 'shield', title: 'Secure by default', short: 'JWT auth with role-based access for members, managers and admins.',
    meta: 'jwt · rbac · roles',
    details: ['Short-lived access tokens, httpOnly refresh', 'Role-based access control built in', 'Your workspace, scoped to your team'] },
]

const expanded = ref(features.map(() => false))
const toggle = (i: number) => { expanded.value[i] = !expanded.value[i] }

const stack = ['Nuxt 4', 'FastAPI', 'PostgreSQL', 'MongoDB', 'Docker', 'Cloudinary',
  'Tailwind v4', 'Vue Query', 'JWT auth']

// Pointer parallax — drifts the orbital cluster toward the cursor. Client-only,
// rAF-throttled, and a no-op under prefers-reduced-motion.
const cluster = ref<HTMLElement | null>(null)
let frame = 0
let detach: (() => void) | null = null

onMounted(() => {
  const el = cluster.value
  if (!el || matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const onMove = (e: PointerEvent) => {
    cancelAnimationFrame(frame)
    frame = requestAnimationFrame(() => {
      const x = (e.clientX / innerWidth - 0.5)
      const y = (e.clientY / innerHeight - 0.5)
      el.style.setProperty('--px', `${x * 26}px`)
      el.style.setProperty('--py', `${y * 26}px`)
    })
  }
  window.addEventListener('pointermove', onMove, { passive: true })
  detach = () => window.removeEventListener('pointermove', onMove)
})
onBeforeUnmount(() => { cancelAnimationFrame(frame); detach?.() })
</script>

<template>
  <div class="cz-root relative min-h-screen overflow-x-hidden bg-canvas text-ink antialiased">

    <!-- ── Atmosphere ─────────────────────────────────────── -->
    <div class="cz-mesh" aria-hidden="true" />
    <div class="cz-grid" aria-hidden="true" />
    <div class="cz-grain" aria-hidden="true" />

    <!-- ── Nav ────────────────────────────────────────────── -->
    <header class="relative z-30 px-4 pt-4 sm:px-6">
      <div class="cz-glass mx-auto flex max-w-6xl items-center justify-between rounded-2xl px-4 py-2.5 sm:px-5">
        <div class="flex items-center gap-2.5">
          <UiLogo :size="30" />
          <span class="cz-display text-[15px] font-bold tracking-tight text-ink">devdesk</span>
          <span class="ml-1 hidden rounded-full border border-line bg-surface px-2 py-0.5 font-mono text-[10px] text-ink-muted sm:inline">
            v2.0
          </span>
        </div>
        <nav class="hidden items-center gap-7 font-mono text-[13px] text-ink-muted md:flex">
          <a href="#features" class="cz-navlink">Features</a>
          <a href="#preview" class="cz-navlink">Preview</a>
          <a href="#stack" class="cz-navlink">Stack</a>
        </nav>
        <div class="flex items-center gap-1.5">
          <NuxtLink to="/login"><UiButton variant="ghost">Log in</UiButton></NuxtLink>
          <NuxtLink to="/register"><UiButton variant="primary">Join now</UiButton></NuxtLink>
        </div>
      </div>
    </header>

    <!-- ── Hero ───────────────────────────────────────────── -->
    <section class="relative z-10 mx-auto grid max-w-6xl grid-cols-1 items-center gap-10 px-6 pb-16 pt-16 lg:grid-cols-12 lg:gap-6 lg:pt-24">

      <!-- Left: headline -->
      <div class="cz-stagger lg:col-span-6">
        <p class="font-mono text-xs uppercase tracking-[0.3em] text-ink-muted" style="--i:0">
          <span class="text-accent">//</span> developer workspace
        </p>

        <h1 class="cz-display mt-6 text-[2.85rem] font-extrabold leading-[0.96] tracking-[-0.035em] text-ink sm:text-6xl lg:text-[4.7rem]" style="--i:1">
          Everything<br>
          you build,<br>
          <span class="cz-grad">finally</span>
          <span class="font-display text-ink"> in orbit.</span>
        </h1>

        <p class="mt-7 max-w-md text-[17px] leading-relaxed text-ink-muted" style="--i:2">
          Projects, tasks, code snippets and bookmarks — one fast, focused
          workspace where every tool is a single keystroke away. No tab sprawl.
          No context loss.
        </p>

        <div class="mt-9 flex flex-wrap items-center gap-3" style="--i:3">
          <NuxtLink to="/register">
            <UiButton variant="primary" size="lg" icon-right="chevron">Start for free</UiButton>
          </NuxtLink>
          <NuxtLink to="/login">
            <UiButton variant="secondary" size="lg">Log in</UiButton>
          </NuxtLink>
          <span class="ml-1 font-mono text-xs text-ink-subtle">$ no card required</span>
        </div>

        <div class="mt-10 flex items-center gap-6" style="--i:4">
          <div>
            <p class="cz-display text-2xl font-bold text-ink">4-in-1</p>
            <p class="font-mono text-[11px] text-ink-subtle">unified workspace</p>
          </div>
          <span class="h-8 w-px bg-line" />
          <div>
            <p class="cz-display text-2xl font-bold text-ink">⌘K</p>
            <p class="font-mono text-[11px] text-ink-subtle">jump anywhere</p>
          </div>
        </div>
      </div>

      <!-- Right: orbital command system -->
      <div class="relative lg:col-span-6">
        <div ref="cluster" class="cz-cluster cz-rise mx-auto aspect-square w-full max-w-[34rem]">

          <!-- ring guides -->
          <span class="cz-ringline" style="--d:42%" aria-hidden="true" />
          <span class="cz-ringline" style="--d:68%" aria-hidden="true" />
          <span class="cz-ringline" style="--d:96%" aria-hidden="true" />

          <!-- orbiting satellites -->
          <div v-for="r in 3" :key="r" class="cz-ring" :class="`cz-ring-${r}`" aria-hidden="true">
            <template v-for="(s, i) in orbits" :key="i">
              <span
                v-if="s.ring === r"
                class="cz-sat"
                :style="{ '--a': s.angle + 'deg' }"
              >
                <span class="cz-sat-pos">
                  <span class="cz-sat-inner" :style="{ animationDelay: (i * 0.6) + 's' }">
                    <UiIcon :name="s.icon" :size="20" />
                  </span>
                </span>
              </span>
            </template>
          </div>

          <!-- gravitational core: the command palette -->
          <div class="cz-core">
            <div class="cz-core-glow" aria-hidden="true" />
            <p class="cz-display text-[2.7rem] font-extrabold leading-none text-ink">⌘K</p>
            <p class="mt-1 font-mono text-[11px] uppercase tracking-[0.2em] text-ink-muted">command core</p>
            <p class="mt-3 font-mono text-[11px] text-ink-subtle">everything, one keystroke</p>
          </div>

          <!-- floating cursor tag, à la collaborative pointers -->
          <div class="cz-cursor text-ink" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 2l5 12 2-5 5-2L2 2z" fill="currentColor"/></svg>
            <span class="cz-cursor-tag">you</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Stack ticker ───────────────────────────────────── -->
    <div id="stack" class="relative z-10 border-y border-line py-4 mask-[linear-gradient(to_right,transparent,#000_8%,#000_92%,transparent)]">
      <div class="flex w-max animate-marquee gap-10 pr-10" aria-hidden="true">
        <template v-for="n in 2" :key="n">
          <span v-for="w in stack" :key="`${n}-${w}`"
            class="flex items-center gap-10 font-mono text-sm text-ink-muted">
            {{ w }}<span class="text-accent">✦</span>
          </span>
        </template>
      </div>
    </div>

    <!-- ── Product preview (intentional dark "screenshot") ── -->
    <section id="preview" class="relative z-10 mx-auto max-w-6xl px-4 pt-24">
      <p class="mb-5 text-center font-mono text-xs uppercase tracking-[0.3em] text-ink-subtle">
        <span class="text-accent">//</span> a real board, not a mockup
      </p>

      <div class="cz-glass relative overflow-hidden rounded-[1.5rem] p-2">
        <div class="pointer-events-none absolute left-1/2 top-0 h-64 w-3/4 -translate-x-1/2 rounded-full bg-accent opacity-25 blur-[90px]" aria-hidden="true" />

        <div class="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0c0a16]">
          <!-- chrome -->
          <div class="flex items-center gap-2 border-b border-white/10 bg-[#0a0812] px-4 py-2.5">
            <span class="size-3 rounded-full bg-rose-500/80" />
            <span class="size-3 rounded-full bg-amber-400/80" />
            <span class="size-3 rounded-full bg-emerald-500/80" />
            <div class="mx-auto flex w-56 items-center justify-center gap-1.5 rounded-md bg-white/5 px-3 py-1 font-mono text-[11px] text-white/35">
              <UiIcon name="shield" :size="11" /> devdesk.app
            </div>
          </div>

          <div class="flex h-104 overflow-hidden">
            <!-- sidebar -->
            <aside class="flex w-48 shrink-0 flex-col gap-1 border-r border-white/5 bg-[#080610] p-3">
              <div class="mb-3 flex items-center gap-2 px-2 py-1">
                <span class="grid size-6 place-items-center rounded-md bg-accent text-accent-fg">
                  <UiIcon name="layers" :size="13" />
                </span>
                <span class="cz-display text-xs font-bold text-white/85">devdesk</span>
              </div>
              <div v-for="(label, icon) in { '⬡': 'Projects', '☰': 'Tasks', '◇': 'Snippets', '⬖': 'Bookmarks' }"
                :key="icon"
                class="flex items-center gap-2 rounded-md px-2 py-1.5 text-[11px]"
                :class="label === 'Projects' ? 'bg-white/10 text-white/90' : 'text-white/40 hover:bg-white/5'">
                <span class="text-[10px]">{{ icon }}</span>{{ label }}
              </div>
              <div class="mt-auto rounded-lg border border-white/5 bg-white/5 px-2.5 py-2">
                <p class="font-mono text-[10px] text-white/40">press</p>
                <p class="font-mono text-[11px] text-accent">⌘K to search</p>
              </div>
            </aside>

            <!-- board -->
            <div class="flex flex-1 flex-col overflow-hidden bg-[#0b0914]">
              <div class="flex items-center justify-between border-b border-white/5 px-5 py-3">
                <div>
                  <p class="text-[11px] font-semibold text-white/85">DevDesk v2</p>
                  <p class="font-mono text-[10px] text-white/30">4 tasks · 2 in progress</p>
                </div>
                <div class="flex gap-2">
                  <span class="rounded-full bg-accent/25 px-2.5 py-0.5 text-[10px] font-medium text-accent">Active</span>
                  <span class="rounded-full bg-white/5 px-2.5 py-0.5 text-[10px] text-white/40">+ Add task</span>
                </div>
              </div>

              <div class="flex flex-1 gap-3 overflow-x-auto p-4">
                <div class="flex w-44 shrink-0 flex-col gap-2">
                  <p class="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/30">Todo</p>
                  <div class="rounded-lg border border-white/5 bg-white/[0.03] p-3">
                    <p class="text-[11px] font-medium text-white/70">Setup CI pipeline</p>
                    <span class="mt-2 inline-block rounded bg-amber-500/20 px-1.5 py-0.5 text-[9px] text-amber-300">medium</span>
                  </div>
                  <div class="rounded-lg border border-white/5 bg-white/[0.03] p-3">
                    <p class="text-[11px] font-medium text-white/70">Write API docs</p>
                    <span class="mt-2 inline-block rounded bg-white/10 px-1.5 py-0.5 text-[9px] text-white/45">low</span>
                  </div>
                </div>
                <div class="flex w-44 shrink-0 flex-col gap-2">
                  <p class="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/30">In Progress</p>
                  <div class="rounded-lg border border-accent/30 bg-accent/10 p-3 ring-1 ring-accent/20">
                    <p class="text-[11px] font-medium text-white/90">Auth middleware</p>
                    <span class="mt-2 inline-block rounded bg-rose-500/20 px-1.5 py-0.5 text-[9px] text-rose-300">high</span>
                  </div>
                  <div class="rounded-lg border border-white/5 bg-white/[0.03] p-3">
                    <p class="text-[11px] font-medium text-white/70">Design system tokens</p>
                    <span class="mt-2 inline-block rounded bg-amber-500/20 px-1.5 py-0.5 text-[9px] text-amber-300">medium</span>
                  </div>
                </div>
                <div class="flex w-44 shrink-0 flex-col gap-2">
                  <p class="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/30">Done</p>
                  <div class="rounded-lg border border-white/5 bg-white/[0.03] p-3 opacity-60">
                    <p class="text-[11px] font-medium text-white/70 line-through">Database schema</p>
                    <span class="mt-2 inline-block rounded bg-emerald-500/20 px-1.5 py-0.5 text-[9px] text-emerald-300">done</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Features (expandable cards) ────────────────────── -->
    <section id="features" class="relative z-10 mx-auto max-w-6xl px-6 pb-8 pt-28">
      <div class="mb-12 max-w-2xl">
        <p class="font-mono text-xs uppercase tracking-[0.3em] text-accent">
          <span class="text-ink-subtle">//</span> what's inside
        </p>
        <h2 class="cz-display mt-4 text-4xl font-extrabold leading-tight tracking-[-0.03em] text-ink sm:text-5xl">
          Everything you need, <span class="font-display font-normal italic text-ink-muted">nothing</span> you don't.
        </h2>
        <p class="mt-3 text-sm text-ink-muted">Tap a card to see what each tool gives you.</p>
      </div>

      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <button
          v-for="(f, i) in features"
          :key="f.title"
          type="button"
          class="cz-card group flex flex-col items-start p-5 text-left"
          :class="{ 'cz-card-open': expanded[i] }"
          :aria-expanded="expanded[i]"
          @click="toggle(i)"
        >
          <span class="flex w-full items-start justify-between">
            <span class="grid size-11 shrink-0 place-items-center rounded-xl bg-accent-soft text-accent transition-transform duration-300 group-hover:-rotate-6">
              <UiIcon :name="f.icon" :size="22" />
            </span>
            <span class="mt-1 text-ink-subtle transition-transform duration-300" :class="{ 'rotate-180': expanded[i] }">
              <UiIcon name="chevronDown" :size="18" />
            </span>
          </span>

          <span class="cz-display mt-4 block text-[15px] font-semibold tracking-tight text-ink">{{ f.title }}</span>
          <span class="mt-1.5 block text-[13.5px] leading-relaxed text-ink-muted">{{ f.short }}</span>

          <!-- expandable region: animates 0fr → 1fr -->
          <span
            class="grid w-full transition-all duration-300 ease-out"
            :class="expanded[i] ? 'mt-4 grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
          >
            <span class="overflow-hidden">
              <span class="block space-y-2 border-t border-line pt-3.5">
                <span v-for="d in f.details" :key="d" class="flex items-start gap-2 text-[13px] leading-snug text-ink-muted">
                  <UiIcon name="check" :size="14" class="mt-0.5 shrink-0 text-accent" />{{ d }}
                </span>
                <span class="block pt-1 font-mono text-[11px] text-ink-subtle">{{ f.meta }}</span>
              </span>
            </span>
          </span>
        </button>
      </div>
    </section>

    <!-- ── CTA ────────────────────────────────────────────── -->
    <section class="relative z-10 mx-auto max-w-6xl px-6 pb-28 pt-14">
      <div class="grain relative overflow-hidden rounded-[1.75rem] bg-accent px-8 py-16 text-center shadow-overlay">
        <div class="pointer-events-none absolute inset-0 bg-blueprint opacity-10 mask-none" aria-hidden="true" />
        <h2 class="cz-display relative mx-auto max-w-xl text-4xl font-extrabold leading-tight tracking-[-0.03em] text-accent-fg sm:text-5xl">
          Stop juggling tabs.<br>Start <span class="font-display font-normal italic">shipping.</span>
        </h2>
        <p class="relative mx-auto mt-4 max-w-md text-accent-fg/80">
          Your projects, tasks, snippets and bookmarks — together in under a minute.
        </p>
        <div class="relative mt-9 flex justify-center">
          <NuxtLink to="/register">
            <span class="inline-flex h-12 items-center gap-2 rounded-xl bg-accent-fg px-6 text-sm font-semibold text-accent shadow-lg transition active:scale-[0.97] hover:brightness-95">
              Create your workspace <UiIcon name="chevron" :size="16" />
            </span>
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- ── Footer ─────────────────────────────────────────── -->
    <footer class="relative z-10 border-t border-line">
      <div class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-8 sm:flex-row">
        <div class="flex items-center gap-2 font-mono text-xs text-ink-muted">
          <span class="grid size-5 place-items-center rounded bg-accent text-accent-fg">
            <UiIcon name="layers" :size="12" />
          </span>
          devdesk — built for builders
        </div>
        <p class="font-mono text-xs text-ink-subtle">© 2026 · projects · tasks · snippets · bookmarks</p>
      </div>
    </footer>

  </div>
</template>

<style>
/* The cosmos design, re-skinned onto the app's design tokens so it follows the
   saved light/dark theme. Bespoke geometry stays in cz-* classes; all colour
   comes from --accent / --surface / --line / --ink and friends. */
.cz-root { isolation: isolate; }

/* Gradient-mesh aurora, slowly drifting — tinted from the accent token */
.cz-mesh {
  position: fixed;
  inset: -20%;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(40% 45% at 82% 14%, color-mix(in oklab, var(--accent) 30%, transparent), transparent 72%),
    radial-gradient(48% 50% at 16% 24%, color-mix(in oklab, var(--accent) 18%, transparent), transparent 72%),
    radial-gradient(55% 55% at 75% 86%, color-mix(in oklab, var(--accent) 22%, transparent), transparent 72%);
  animation: cz-drift 26s ease-in-out infinite alternate;
}
@keyframes cz-drift {
  0%   { transform: translate3d(0, 0, 0) scale(1); }
  50%  { transform: translate3d(2%, -2%, 0) scale(1.06); }
  100% { transform: translate3d(-2%, 2%, 0) scale(1.03); }
}

.cz-grid {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    linear-gradient(to right, var(--line) 1px, transparent 1px),
    linear-gradient(to bottom, var(--line) 1px, transparent 1px);
  background-size: 64px 64px;
  opacity: 0.6;
  -webkit-mask-image: radial-gradient(120% 80% at 50% 0%, #000 30%, transparent 75%);
  mask-image: radial-gradient(120% 80% at 50% 0%, #000 30%, transparent 75%);
}

.cz-grain::after,
.cz-grain {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
.cz-grain::after {
  content: "";
  opacity: 0.35;
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.35'/%3E%3C/svg%3E");
}

/* Glassmorphism — token surface + line, theme-aware shadow */
.cz-glass {
  background: color-mix(in srgb, var(--surface) 72%, transparent);
  border: 1px solid var(--line);
  backdrop-filter: blur(16px) saturate(1.2);
  -webkit-backdrop-filter: blur(16px) saturate(1.2);
  box-shadow: var(--shadow-pop);
}

.cz-display {
  font-family: "Bricolage Grotesque", ui-sans-serif, system-ui, sans-serif;
  font-optical-sizing: auto;
}

.cz-grad {
  background: linear-gradient(100deg, var(--accent-hover), var(--accent));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.cz-navlink { position: relative; transition: color 0.2s; }
.cz-navlink:hover { color: var(--ink); }
.cz-navlink::after {
  content: "";
  position: absolute;
  left: 0; bottom: -4px;
  width: 0; height: 1px;
  background: var(--accent);
  transition: width 0.25s var(--ease-out-soft);
}
.cz-navlink:hover::after { width: 100%; }

/* ── Orbital system ── */
.cz-cluster {
  position: relative;
  transform: translate3d(var(--px, 0), var(--py, 0), 0);
  transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}

.cz-ringline {
  position: absolute;
  inset: 0;
  margin: auto;
  width: var(--d);
  height: var(--d);
  border-radius: 50%;
  border: 1px solid var(--line);
  box-shadow: inset 0 0 60px color-mix(in oklab, var(--accent) 10%, transparent);
}

.cz-ring { position: absolute; inset: 0; margin: auto; border-radius: 50%; }
.cz-ring-1 { width: 42%; height: 42%; }
.cz-ring-2 { width: 68%; height: 68%; }
.cz-ring-3 { width: 96%; height: 96%; }

/* .cz-sat fills the ring box and rotates the pinned tile to angle --a around the
   ring centre. .cz-sat-pos un-tilts it so the icon stays upright. .cz-sat-inner
   bobs on its own (translate only — no rotation conflict). */
.cz-sat { position: absolute; inset: 0; transform: rotate(var(--a)); }
.cz-sat-pos {
  position: absolute;
  top: 0;
  left: 50%;
  width: 44px;
  height: 44px;
  margin: -22px 0 0 -22px;
  transform: rotate(calc(-1 * var(--a)));
}

.cz-sat-inner {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  animation: cz-bob 5.5s ease-in-out infinite;
  color: var(--accent);
  background: var(--surface);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-card), 0 8px 24px color-mix(in oklab, var(--accent) 22%, transparent);
}

/* core */
.cz-core {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 38%;
  height: 38%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  border-radius: 50%;
  background: radial-gradient(circle at 50% 35%, color-mix(in oklab, var(--accent) 20%, var(--surface)), var(--surface) 74%);
  border: 1px solid var(--line);
  box-shadow: 0 0 60px color-mix(in oklab, var(--accent) 28%, transparent), var(--shadow-card);
}
.cz-core-glow {
  position: absolute;
  inset: -30%;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in oklab, var(--accent) 30%, transparent), transparent 60%);
  animation: cz-pulse 4.5s ease-in-out infinite;
  z-index: -1;
}
@keyframes cz-pulse {
  0%, 100% { transform: scale(1); opacity: 0.7; }
  50% { transform: scale(1.12); opacity: 1; }
}

/* floating collaborative cursor */
.cz-cursor {
  position: absolute;
  top: 64%;
  left: 12%;
  display: flex;
  align-items: flex-start;
  gap: 2px;
  animation: cz-float 6s ease-in-out infinite;
  filter: drop-shadow(0 4px 8px color-mix(in oklab, var(--ink) 25%, transparent));
}
.cz-cursor-tag {
  margin-top: 8px;
  border-radius: 9px;
  padding: 2px 9px;
  font: 600 11px/1.4 "JetBrains Mono", monospace;
  color: var(--accent-fg);
  background: var(--accent);
  box-shadow: 0 6px 16px color-mix(in oklab, var(--accent) 45%, transparent);
}
@keyframes cz-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
@keyframes cz-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* ── Expandable feature cards ── */
.cz-card {
  border-radius: var(--radius-card);
  background: var(--surface);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-card);
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}
.cz-card:hover { border-color: var(--line-strong); box-shadow: var(--shadow-card-hover); }
.cz-card-open { border-color: var(--line-strong); box-shadow: var(--shadow-card-hover); }
.cz-card:focus-visible {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-ring);
}

/* entrances */
.cz-stagger > * {
  animation: cz-up 0.6s var(--ease-out-soft) both;
  animation-delay: calc(var(--i, 0) * 90ms);
}
.cz-rise {
  animation: cz-pop 0.9s var(--ease-out-soft) 0.15s both;
}
@keyframes cz-up {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes cz-pop {
  from { opacity: 0; transform: scale(0.92); }
  to { opacity: 1; transform: scale(1); }
}

@media (prefers-reduced-motion: reduce) {
  .cz-mesh, .cz-ring, .cz-sat-inner, .cz-core-glow, .cz-cursor { animation: none !important; }
}
</style>
