<script setup lang="ts">
const props = withDefaults(
  defineProps<{ tone?: 'gray' | 'red' | 'amber' | 'green' | 'indigo'; dot?: boolean }>(),
  { tone: 'gray' },
)

// Tone classes intentionally keep their literal bg-*-100 tokens (asserted by tests),
// with rings + dark-mode tweaks layered on for a more refined look.
// Monochrome-first: gray/indigo render as neutral zinc (no brand color).
// Color is reserved for status tones only (red/amber/green).
const toneClasses: Record<string, string> = {
  gray: 'bg-zinc-100 text-zinc-600 ring-zinc-200/70 dark:bg-white/10 dark:text-zinc-300 dark:ring-white/15',
  red: 'bg-red-100 text-red-700 ring-red-200/70 dark:bg-red-400/10 dark:text-red-300 dark:ring-red-400/20',
  amber: 'bg-amber-100 text-amber-700 ring-amber-200/70 dark:bg-amber-400/10 dark:text-amber-300 dark:ring-amber-400/20',
  green: 'bg-green-100 text-green-700 ring-green-200/70 dark:bg-green-400/10 dark:text-green-300 dark:ring-green-400/20',
  indigo: 'bg-zinc-100 text-zinc-600 ring-zinc-200/70 dark:bg-white/10 dark:text-zinc-300 dark:ring-white/15',
}

const dotColor: Record<string, string> = {
  gray: 'bg-zinc-400',
  red: 'bg-red-500',
  amber: 'bg-amber-500',
  green: 'bg-green-500',
  indigo: 'bg-zinc-400',
}
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium capitalize ring-1 ring-inset"
    :class="toneClasses[props.tone]"
  >
    <span v-if="dot" class="size-1.5 rounded-full" :class="dotColor[props.tone]" aria-hidden="true" />
    <slot />
  </span>
</template>
