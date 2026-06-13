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
  'relative inline-flex items-center justify-center gap-2 rounded-lg font-medium ' +
  'transition-all duration-150 active:scale-[0.97] disabled:pointer-events-none ' +
  'disabled:opacity-55 focus-visible:outline-none'

const variants: Record<Variant, string> = {
  primary:
    'bg-accent text-accent-fg shadow-sm hover:bg-accent-hover ' +
    'hover:shadow-[0_4px_14px_var(--accent-ring)] focus-visible:ring-4 focus-visible:ring-[var(--accent-ring)]',
  secondary:
    'border border-line bg-surface text-ink shadow-sm hover:border-line-strong ' +
    'hover:bg-surface-2 focus-visible:ring-4 focus-visible:ring-[var(--accent-ring)]',
  ghost:
    'text-ink-muted hover:bg-surface-2 hover:text-ink focus-visible:ring-2 focus-visible:ring-line-strong',
  subtle:
    'bg-accent-soft text-accent hover:brightness-95 focus-visible:ring-4 focus-visible:ring-[var(--accent-ring)]',
  danger:
    'bg-danger-soft text-danger hover:brightness-95 focus-visible:ring-2 focus-visible:ring-danger',
}

const sizes: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-9.5 px-4 text-sm',
  lg: 'h-11 px-5 text-sm',
}

const iconSize = { sm: 15, md: 16, lg: 18 }[props.size]
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
