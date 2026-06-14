<script setup lang="ts">
// Marketing landing — prerendered. Self-contained "orbital control room" dark theme:
// it commits to a futuristic cosmos aesthetic regardless of the saved app theme.
import { ref, onMounted, onBeforeUnmount } from 'vue'

const pillars = [
  { no: '01', icon: 'board', title: 'Projects & boards', meta: 'kanban · drag · due dates',
    desc: 'Kanban boards with drag-and-drop tasks, priorities, assignees and due dates. Your roadmap, finally legible.' },
  { no: '02', icon: 'code', title: 'Code snippets', meta: 'syntax · search · tags',
    desc: 'A syntax-highlighted library for the code you reach for daily. Tag it, search it, paste it — never dig through old repos again.' },
  { no: '03', icon: 'bookmark', title: 'Smart bookmarks', meta: 'auto-meta · favicon',
    desc: 'Paste a link and the title, description and favicon are fetched for you. A reading list that files itself.' },
  { no: '04', icon: 'command', title: 'Command palette', meta: '⌘K · jump · search',
    desc: 'Jump anywhere and search everything from a single keystroke. Hands stay on the keyboard, flow stays unbroken.' },
]

// Satellites orbiting the command core. Each lives on a ring at a fixed angle.
const orbits = [
  { ring: 1, angle: 18,  icon: 'board',    tone: 'indigo' },
  { ring: 1, angle: 205, icon: 'command',  tone: 'violet' },
  { ring: 2, angle: 70,  icon: 'code',     tone: 'sky' },
  { ring: 2, angle: 168, icon: 'bell',     tone: 'amber' },
  { ring: 2, angle: 300, icon: 'comment',  tone: 'rose' },
  { ring: 3, angle: 30,  icon: 'bookmark', tone: 'emerald' },
  { ring: 3, angle: 132, icon: 'sparkles', tone: 'amber' },
  { ring: 3, angle: 248, icon: 'users',    tone: 'violet' },
] as const

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
  <div class="cz-root relative min-h-screen overflow-x-hidden antialiased">

    <!-- ── Atmosphere ─────────────────────────────────────── -->
    <div class="cz-mesh" aria-hidden="true" />
    <div class="cz-grid" aria-hidden="true" />
    <div class="cz-grain" aria-hidden="true" />
    <div class="cz-vignette" aria-hidden="true" />

    <!-- ── Nav ────────────────────────────────────────────── -->
    <header class="relative z-30 px-4 pt-4 sm:px-6">
      <div class="cz-glass mx-auto flex max-w-6xl items-center justify-between rounded-2xl px-4 py-2.5 sm:px-5">
        <div class="flex items-center gap-2.5">
          <span class="cz-logo grid size-8 place-items-center rounded-xl">
            <UiIcon name="layers" :size="17" />
          </span>
          <span class="cz-display text-[15px] font-bold tracking-tight text-white">devdesk</span>
          <span class="ml-1 hidden rounded-full border border-white/10 bg-white/5 px-2 py-0.5 font-mono text-[10px] text-white/45 sm:inline">
            v2.0
          </span>
        </div>
        <nav class="hidden items-center gap-7 font-mono text-[13px] text-white/55 md:flex">
          <a href="#features" class="cz-navlink">Features</a>
          <a href="#preview" class="cz-navlink">Preview</a>
          <a href="#stack" class="cz-navlink">Stack</a>
        </nav>
        <div class="flex items-center gap-2">
          <NuxtLink to="/login" class="hidden px-3 py-1.5 font-mono text-[13px] text-white/65 transition hover:text-white sm:inline">Log in</NuxtLink>
          <NuxtLink to="/register" class="cz-btn cz-btn-sm">Join now</NuxtLink>
        </div>
      </div>
    </header>

    <!-- ── Hero ───────────────────────────────────────────── -->
    <section class="relative z-10 mx-auto grid max-w-6xl grid-cols-1 items-center gap-10 px-6 pb-16 pt-16 lg:grid-cols-12 lg:gap-6 lg:pt-24">

      <!-- Left: headline -->
      <div class="cz-stagger lg:col-span-6">
        <p class="font-mono text-xs uppercase tracking-[0.3em] text-white/45" style="--i:0">
          <span class="text-[var(--cz-a)]">//</span> developer workspace
        </p>

        <h1 class="cz-display mt-6 text-[2.85rem] font-extrabold leading-[0.96] tracking-[-0.035em] text-white sm:text-6xl lg:text-[4.7rem]" style="--i:1">
          Everything<br>
          you build,<br>
          <span class="cz-grad">finally</span>
          <span class="font-display text-white/90"> in orbit.</span>
        </h1>

        <p class="mt-7 max-w-md text-[17px] leading-relaxed text-white/65" style="--i:2">
          Projects, tasks, code snippets and bookmarks — one fast, focused
          workspace where every tool is a single keystroke away. No tab sprawl.
          No context loss.
        </p>

        <div class="mt-9 flex flex-wrap items-center gap-3" style="--i:3">
          <NuxtLink to="/register" class="cz-btn cz-btn-lg group">
            Start for free
            <UiIcon name="chevron" :size="17" class="transition-transform duration-300 group-hover:translate-x-0.5" />
          </NuxtLink>
          <NuxtLink to="/login" class="cz-btn-ghost cz-btn-lg">Log in</NuxtLink>
          <span class="ml-1 font-mono text-xs text-white/35">$ no card required</span>
        </div>

        <div class="mt-10 flex items-center gap-6" style="--i:4">
          <div>
            <p class="cz-display text-2xl font-bold text-white">4-in-1</p>
            <p class="font-mono text-[11px] text-white/40">unified workspace</p>
          </div>
          <span class="h-8 w-px bg-white/10" />
          <div>
            <p class="cz-display text-2xl font-bold text-white">⌘K</p>
            <p class="font-mono text-[11px] text-white/40">jump anywhere</p>
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
                  <span class="cz-sat-inner" :data-tone="s.tone" :style="{ animationDelay: (i * 0.6) + 's' }">
                    <UiIcon :name="s.icon" :size="20" />
                  </span>
                </span>
              </span>
            </template>
          </div>

          <!-- gravitational core: the command palette -->
          <div class="cz-core">
            <div class="cz-core-glow" aria-hidden="true" />
            <p class="cz-display text-[2.7rem] font-extrabold leading-none text-white">⌘K</p>
            <p class="mt-1 font-mono text-[11px] uppercase tracking-[0.2em] text-white/55">command core</p>
            <p class="mt-3 font-mono text-[11px] text-white/40">everything, one keystroke</p>
          </div>

          <!-- floating cursor tag, à la collaborative pointers -->
          <div class="cz-cursor" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 2l5 12 2-5 5-2L2 2z" fill="#fff"/></svg>
            <span class="cz-cursor-tag">you</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Stack ticker ───────────────────────────────────── -->
    <div id="stack" class="relative z-10 border-y border-white/[0.07] py-4 mask-[linear-gradient(to_right,transparent,#000_8%,#000_92%,transparent)]">
      <div class="flex w-max animate-marquee gap-10 pr-10" aria-hidden="true">
        <template v-for="n in 2" :key="n">
          <span v-for="w in stack" :key="`${n}-${w}`"
            class="flex items-center gap-10 font-mono text-sm text-white/40">
            {{ w }}<span class="text-[var(--cz-a)]">✦</span>
          </span>
        </template>
      </div>
    </div>

    <!-- ── Product preview ────────────────────────────────── -->
    <section id="preview" class="relative z-10 mx-auto max-w-6xl px-4 pt-24">
      <p class="mb-5 text-center font-mono text-xs uppercase tracking-[0.3em] text-white/40">
        <span class="text-[var(--cz-a)]">//</span> a real board, not a mockup
      </p>

      <div class="cz-glass relative overflow-hidden rounded-[1.5rem] p-2">
        <div class="pointer-events-none absolute left-1/2 top-0 h-64 w-3/4 -translate-x-1/2 rounded-full bg-[var(--cz-a)] opacity-25 blur-[90px]" aria-hidden="true" />

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
                <span class="cz-logo grid size-6 place-items-center rounded-md text-[10px]">
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
                <p class="font-mono text-[11px] text-[var(--cz-a2)]">⌘K to search</p>
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
                  <span class="rounded-full bg-[var(--cz-a)]/25 px-2.5 py-0.5 text-[10px] font-medium text-[var(--cz-a2)]">Active</span>
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
                  <div class="rounded-lg border border-[var(--cz-a)]/30 bg-[var(--cz-a)]/10 p-3 ring-1 ring-[var(--cz-a)]/20">
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

    <!-- ── Features ───────────────────────────────────────── -->
    <section id="features" class="relative z-10 mx-auto max-w-5xl px-6 pb-8 pt-28">
      <div class="mb-14 max-w-2xl">
        <p class="font-mono text-xs uppercase tracking-[0.3em] text-[var(--cz-a)]">
          <span class="text-white/40">//</span> what's inside
        </p>
        <h2 class="cz-display mt-4 text-4xl font-extrabold leading-tight tracking-[-0.03em] text-white sm:text-5xl">
          Four tools. <span class="font-display font-normal text-white/55">One</span> workspace.
        </h2>
      </div>

      <div class="flex flex-col">
        <article
          v-for="(p, idx) in pillars"
          :key="p.no"
          class="group grid grid-cols-1 items-center gap-6 border-t border-white/[0.08] py-9 sm:grid-cols-12 sm:gap-10"
        >
          <div class="flex items-center gap-5 sm:col-span-5" :class="idx % 2 ? 'sm:order-2' : ''">
            <span class="cz-display text-5xl font-bold text-white/15 transition-colors group-hover:text-[var(--cz-a2)]">{{ p.no }}</span>
            <span class="cz-feat-icon grid size-12 shrink-0 place-items-center rounded-2xl transition-transform duration-300 group-hover:-rotate-6">
              <UiIcon :name="p.icon" :size="24" />
            </span>
          </div>
          <div class="sm:col-span-7" :class="idx % 2 ? 'sm:order-1 sm:text-right' : ''">
            <h3 class="text-xl font-semibold tracking-tight text-white">{{ p.title }}</h3>
            <p class="mt-2 text-[15px] leading-relaxed text-white/55">{{ p.desc }}</p>
            <p class="mt-3 font-mono text-xs text-white/35">{{ p.meta }}</p>
          </div>
        </article>
      </div>
    </section>

    <!-- ── CTA ────────────────────────────────────────────── -->
    <section class="relative z-10 mx-auto max-w-6xl px-6 pb-28 pt-14">
      <div class="cz-cta relative overflow-hidden rounded-[1.75rem] px-8 py-16 text-center">
        <div class="cz-grain" aria-hidden="true" />
        <h2 class="cz-display relative mx-auto max-w-xl text-4xl font-extrabold leading-tight tracking-[-0.03em] text-white sm:text-5xl">
          Stop juggling tabs.<br>Start <span class="font-display font-normal italic">shipping.</span>
        </h2>
        <p class="relative mx-auto mt-4 max-w-md text-white/70">
          Your projects, tasks, snippets and bookmarks — together in under a minute.
        </p>
        <div class="relative mt-9 flex justify-center">
          <NuxtLink to="/register" class="cz-btn cz-btn-lg cz-btn-invert group">
            Create your workspace
            <UiIcon name="chevron" :size="16" class="transition-transform duration-300 group-hover:translate-x-0.5" />
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- ── Footer ─────────────────────────────────────────── -->
    <footer class="relative z-10 border-t border-white/[0.07]">
      <div class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-8 sm:flex-row">
        <div class="flex items-center gap-2 font-mono text-xs text-white/45">
          <span class="cz-logo grid size-5 place-items-center rounded">
            <UiIcon name="layers" :size="12" />
          </span>
          devdesk — built for builders
        </div>
        <p class="font-mono text-xs text-white/30">© 2026 · projects · tasks · snippets · bookmarks</p>
      </div>
    </footer>

  </div>
</template>

<style>
/* ── Cosmos palette (scoped to the landing by the .cz-root cascade) ── */
.cz-root {
  --cz-bg: #07060f;
  --cz-a: #7c5cff;   /* violet accent */
  --cz-a2: #a594ff;  /* lighter violet */
  --cz-warm: #ff9d6c;
  background: var(--cz-bg);
  color: #fff;
  isolation: isolate;
}

/* Gradient-mesh aurora, slowly drifting */
.cz-mesh {
  position: fixed;
  inset: -20%;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(38% 42% at 18% 22%, rgba(255, 157, 108, 0.30), transparent 70%),
    radial-gradient(45% 48% at 82% 16%, rgba(124, 92, 255, 0.42), transparent 72%),
    radial-gradient(50% 50% at 75% 78%, rgba(190, 96, 255, 0.32), transparent 72%),
    radial-gradient(55% 55% at 25% 88%, rgba(72, 86, 255, 0.30), transparent 72%);
  filter: saturate(1.15);
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
    linear-gradient(to right, rgba(255, 255, 255, 0.045) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.045) 1px, transparent 1px);
  background-size: 64px 64px;
  -webkit-mask-image: radial-gradient(120% 80% at 50% 0%, #000 30%, transparent 75%);
  mask-image: radial-gradient(120% 80% at 50% 0%, #000 30%, transparent 75%);
}

.cz-vignette {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(120% 100% at 50% -10%, transparent 55%, rgba(0, 0, 0, 0.55) 100%);
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
  opacity: 0.4;
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.35'/%3E%3C/svg%3E");
}

/* Glassmorphism */
.cz-glass {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px) saturate(1.2);
  -webkit-backdrop-filter: blur(16px) saturate(1.2);
  box-shadow: 0 20px 50px rgba(5, 2, 20, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.cz-display {
  font-family: "Bricolage Grotesque", ui-sans-serif, system-ui, sans-serif;
  font-optical-sizing: auto;
}

.cz-logo {
  background: linear-gradient(135deg, #8b7bff, #6a4cff);
  color: #fff;
  box-shadow: 0 6px 18px rgba(124, 92, 255, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.cz-grad {
  background: linear-gradient(100deg, var(--cz-warm), var(--cz-a2) 55%, var(--cz-a));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.cz-navlink { position: relative; transition: color 0.2s; }
.cz-navlink:hover { color: #fff; }
.cz-navlink::after {
  content: "";
  position: absolute;
  left: 0; bottom: -4px;
  width: 0; height: 1px;
  background: var(--cz-a2);
  transition: width 0.25s var(--ease-out-soft);
}
.cz-navlink:hover::after { width: 100%; }

/* ── Buttons ── */
.cz-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border-radius: 0.85rem;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #8b7bff, #6a4cff);
  box-shadow: 0 10px 30px rgba(106, 76, 255, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition: transform 0.18s var(--ease-spring), box-shadow 0.25s, filter 0.2s;
}
.cz-btn:hover { transform: translateY(-2px); box-shadow: 0 16px 40px rgba(106, 76, 255, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.4); }
.cz-btn:active { transform: translateY(0) scale(0.98); }
.cz-btn-sm { padding: 0.42rem 0.9rem; font-size: 13px; }
.cz-btn-lg { padding: 0.75rem 1.4rem; font-size: 15px; }
.cz-btn-invert {
  background: #fff;
  color: #1a1130;
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.4);
}
.cz-btn-invert:hover { filter: brightness(0.96); box-shadow: 0 18px 48px rgba(0, 0, 0, 0.5); }

.cz-btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border-radius: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(8px);
  transition: transform 0.18s var(--ease-spring), background 0.2s, border-color 0.2s;
}
.cz-btn-ghost:hover { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.28); transform: translateY(-2px); }

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
  border: 1px solid rgba(255, 255, 255, 0.09);
  box-shadow: inset 0 0 60px rgba(124, 92, 255, 0.08);
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
  color: #fff;
  background: rgba(20, 16, 36, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(6px);
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.12);
}
.cz-sat-inner[data-tone="indigo"]  { box-shadow: 0 8px 26px rgba(99, 102, 241, 0.55), inset 0 1px 0 rgba(255,255,255,0.18); color: #c4c2ff; }
.cz-sat-inner[data-tone="violet"]  { box-shadow: 0 8px 26px rgba(168, 85, 247, 0.55), inset 0 1px 0 rgba(255,255,255,0.18); color: #e0c2ff; }
.cz-sat-inner[data-tone="sky"]     { box-shadow: 0 8px 26px rgba(56, 189, 248, 0.5),  inset 0 1px 0 rgba(255,255,255,0.18); color: #b3e6ff; }
.cz-sat-inner[data-tone="amber"]   { box-shadow: 0 8px 26px rgba(251, 146, 60, 0.55), inset 0 1px 0 rgba(255,255,255,0.18); color: #ffd6ab; }
.cz-sat-inner[data-tone="rose"]    { box-shadow: 0 8px 26px rgba(244, 63, 94, 0.5),   inset 0 1px 0 rgba(255,255,255,0.18); color: #ffc2cf; }
.cz-sat-inner[data-tone="emerald"] { box-shadow: 0 8px 26px rgba(16, 185, 129, 0.5),  inset 0 1px 0 rgba(255,255,255,0.18); color: #aef0d6; }

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
  background: radial-gradient(circle at 50% 35%, rgba(124, 92, 255, 0.28), rgba(12, 9, 24, 0.92) 72%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 60px rgba(124, 92, 255, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}
.cz-core-glow {
  position: absolute;
  inset: -30%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 92, 255, 0.35), transparent 60%);
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
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));
}
.cz-cursor-tag {
  margin-top: 8px;
  border-radius: 9px;
  padding: 2px 9px;
  font: 600 11px/1.4 "JetBrains Mono", monospace;
  color: #fff;
  background: linear-gradient(135deg, #8b7bff, #6a4cff);
  box-shadow: 0 6px 16px rgba(106, 76, 255, 0.5);
}
@keyframes cz-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
@keyframes cz-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* feature icon tiles */
.cz-feat-icon {
  color: var(--cz-a2);
  background: rgba(124, 92, 255, 0.12);
  border: 1px solid rgba(124, 92, 255, 0.22);
}

/* CTA panel */
.cz-cta {
  background: linear-gradient(135deg, #6a4cff 0%, #8b5cff 45%, #ff9d6c 130%);
  box-shadow: 0 30px 80px rgba(106, 76, 255, 0.45);
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
