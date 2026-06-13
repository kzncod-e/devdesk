<script setup lang="ts">
withDefaults(
  defineProps<{ icon?: string; title: string; description?: string }>(),
  { icon: 'sparkles' },
)
</script>

<template>
  <div
    class="enter-rise flex flex-col items-center justify-center rounded-2xl border border-dashed border-line bg-surface/40 px-6 py-16 text-center"
  >
    <div class="relative mb-5">
      <div class="absolute inset-0 -z-10 scale-150 rounded-full bg-accent-soft blur-2xl opacity-70" aria-hidden="true" />
      <div class="grid size-16 place-items-center rounded-2xl border border-line bg-surface text-accent shadow-card">
        <UiIcon :name="icon" :size="28" />
      </div>
    </div>
    <h3 class="text-base font-semibold text-ink">{{ title }}</h3>
    <p v-if="description" class="mt-1.5 max-w-sm text-sm text-ink-muted">{{ description }}</p>
    <div v-if="$slots.default" class="mt-6">
      <slot />
    </div>
  </div>
</template>
