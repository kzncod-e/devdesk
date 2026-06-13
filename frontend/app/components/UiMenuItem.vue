<script setup lang="ts">
withDefaults(defineProps<{ icon?: string; danger?: boolean }>(), {})
</script>

<template>
  <button
    type="button"
    role="menuitem"
    :class="[
      'flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm transition',
      danger
        ? 'text-danger hover:bg-danger-soft'
        : 'text-ink-muted hover:bg-surface-2 hover:text-ink',
    ]"
  >
    <UiIcon v-if="icon" :name="icon" :size="16" />
    <span class="flex-1"><slot /></span>
  </button>
</template>
