<script setup lang="ts">
withDefaults(defineProps<{ rounded?: string }>(), { rounded: 'rounded-md' })
</script>

<template>
  <div
    :class="[
      'animate-shimmer bg-size-[200%_100%]',
      'bg-linear-to-r from-surface-2 via-surface-3 to-surface-2',
      rounded,
    ]"
    aria-hidden="true"
  />
</template>
