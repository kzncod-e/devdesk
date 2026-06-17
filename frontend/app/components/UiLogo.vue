<script setup lang="ts">
/**
 * DevDesk brand mark — a "framed prompt": a code bracket embracing a chevron
 * (`[›`). Monochrome, geometric, no gradients or blobs. Reads as a terminal
 * prompt inside a workspace frame.
 *
 * variants:
 *   tile  — mark reversed out of an accent rounded-square (sidebar / avatar slot)
 *   mark  — bare mark in currentColor (inherits text color)
 * showName renders the "DevDesk" wordmark beside the mark.
 */
const props = withDefaults(
  defineProps<{ size?: number; variant?: 'tile' | 'mark'; showName?: boolean }>(),
  { size: 28, variant: 'tile', showName: false },
)

const inner = Math.round(props.size * 0.6)
</script>

<template>
  <span class="inline-flex items-center gap-2">
    <span
      v-if="variant === 'tile'"
      class="grid shrink-0 place-items-center rounded-control bg-accent text-accent-fg"
      :style="{ width: `${size}px`, height: `${size}px` }"
    >
      <svg :width="inner" :height="inner" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M10 5H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h3" stroke="currentColor"
              stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" />
        <path d="m13.5 8.5 3.5 3.5-3.5 3.5" stroke="currentColor"
              stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </span>
    <svg
      v-else
      :width="size" :height="size" viewBox="0 0 24 24" fill="none"
      class="shrink-0 text-ink" aria-hidden="true"
    >
      <path d="M10 5H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h3" stroke="currentColor"
            stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" />
      <path d="m13.5 8.5 3.5 3.5-3.5 3.5" stroke="currentColor"
            stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" />
    </svg>

    <span
      v-if="showName"
      class="text-[0.9375rem] font-semibold tracking-[-0.02em] text-ink"
    >Dev<span class="text-ink-muted">Desk</span></span>
  </span>
</template>
