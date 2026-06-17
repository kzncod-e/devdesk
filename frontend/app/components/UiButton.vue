<script setup lang="ts">
type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'subtle'
type Size = 'sm' | 'md' | 'lg'

const props = withDefaults(
  defineProps<{
    variant?: Variant
    size?: Size
    icon?: string
    iconRight?: string
    loading?: boolean
    block?: boolean
    type?: 'button' | 'submit'
  }>(),
  { variant: 'secondary', size: 'md', type: 'button' },
)

const base =
  'relative inline-flex items-center justify-center gap-1.5 rounded-control font-medium ' +
  'transition duration-150 active:scale-[0.98] disabled:pointer-events-none ' +
  'disabled:opacity-55 focus-visible:outline-none'

const variants: Record<Variant, string> = {
  primary:
    'bg-accent text-accent-fg hover:bg-accent-hover ' +
    'focus-visible:ring-[3px] focus-visible:ring-[var(--accent-ring)]',
  secondary:
    'border border-line bg-surface text-ink hover:border-line-strong ' +
    'hover:bg-surface-2 focus-visible:ring-[3px] focus-visible:ring-[var(--accent-ring)]',
  ghost:
    'text-ink-muted hover:bg-surface-2 hover:text-ink focus-visible:ring-2 focus-visible:ring-line-strong',
  subtle:
    'bg-accent-soft text-accent hover:brightness-95 focus-visible:ring-[3px] focus-visible:ring-[var(--accent-ring)]',
  danger:
    'bg-danger-soft text-danger hover:brightness-95 focus-visible:ring-2 focus-visible:ring-danger',
}

const sizes: Record<Size, string> = {
  sm: 'h-7 px-2.5 text-xs',
  md: 'h-8 px-3 text-sm',
  lg: 'h-10 px-4 text-sm',
}

const iconSize = { sm: 14, md: 15, lg: 17 }[props.size]
</script>

<template>
  <button
    :type="type"
    :disabled="loading || ($attrs.disabled as boolean)"
    :class="[base, variants[variant], sizes[size], block && 'w-full']"
  >
    <span
      v-if="loading"
      class="absolute inset-0 grid place-items-center"
      aria-hidden="true"
    >
      <svg class="size-4 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2.5" class="opacity-25" />
        <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
      </svg>
    </span>
    <span :class="['contents', loading && 'invisible']">
      <UiIcon v-if="icon" :name="icon" :size="iconSize" />
      <slot />
      <UiIcon v-if="iconRight" :name="iconRight" :size="iconSize" />
    </span>
  </button>
</template>
