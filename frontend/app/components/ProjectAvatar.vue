<script setup lang="ts">
import { computed } from 'vue'

/**
 * Project identity monogram — a neutral, monochrome rounded square with the
 * project's initials. Deterministic per name, used everywhere a project is
 * represented (sidebar, cards, board header, search, etc.) so identity stays
 * consistent across the app. No colour — identity comes from the initials.
 */
const props = withDefaults(
  defineProps<{ name?: string | null; size?: number }>(),
  { size: 20 },
)

// Two+ words → first letter of the first two words; one word → first two letters.
const initials = computed(() => {
  const parts = (props.name ?? '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '·'
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase()
  return (parts[0]![0]! + parts[1]![0]!).toUpperCase()
})
</script>

<template>
  <span
    class="inline-grid shrink-0 select-none place-items-center rounded-[6px] border border-line bg-surface-3
      font-semibold leading-none tracking-[-0.02em] text-ink-muted transition-colors"
    :style="{
      width: `${size}px`,
      height: `${size}px`,
      fontSize: `${Math.max(9, Math.round(size * 0.42))}px`,
    }"
    :title="name ?? undefined"
  >{{ initials }}</span>
</template>
