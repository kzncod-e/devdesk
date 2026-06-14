<script setup lang="ts">
type Tone = 'default' | 'danger'
type Size = 'sm' | 'md'

const props = withDefaults(
  defineProps<{ icon: string; label: string; tone?: Tone; size?: Size; active?: boolean }>(),
  { tone: 'default', size: 'md' },
)

const sizes: Record<Size, string> = { sm: 'size-7', md: 'size-9' }
const tones: Record<Tone, string> = {
  default: 'text-ink-muted hover:bg-surface-2 hover:text-ink',
  danger: 'text-ink-subtle hover:bg-danger-soft hover:text-danger',
}
</script>

<template>
  <button
    type="button"
    :aria-label="label"
    :title="label"
    :class="[
      'inline-grid place-items-center rounded-lg transition duration-150 active:scale-90',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-ring)]',
      sizes[size],
      active ? 'bg-surface-2 text-ink' : tones[tone],
    ]"
  >
    <UiIcon :name="icon" :size="size === 'sm' ? 15 : 18" />
  </button>
</template>
