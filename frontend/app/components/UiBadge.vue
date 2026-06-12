<script setup lang="ts">
const props = withDefaults(defineProps<{ tone?: 'gray' | 'red' | 'amber' | 'green' | 'indigo' }>(), {
  tone: 'gray',
})

const toneClasses: Record<string, string> = {
  gray: 'bg-slate-100 text-slate-700',
  red: 'bg-red-100 text-red-700',
  amber: 'bg-amber-100 text-amber-700',
  green: 'bg-green-100 text-green-700',
  indigo: 'bg-indigo-100 text-indigo-700',
}
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
    :class="toneClasses[props.tone]"
  >
    <slot />
  </span>
</template>
