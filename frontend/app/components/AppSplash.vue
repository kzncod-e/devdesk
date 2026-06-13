<script setup lang="ts">
defineProps<{ show: boolean }>()
</script>

<template>
  <Transition name="splash" :duration="{ leave: 600 }">
    <div
      v-if="show"
      class="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-6 bg-canvas"
      aria-live="polite"
      aria-label="Loading DevDesk"
    >
      <div class="flex flex-col items-center gap-4">
        <div class="relative">
          <span class="grid size-16 place-items-center rounded-2xl bg-accent text-accent-fg shadow-overlay">
            <UiIcon name="layers" :size="32" />
          </span>
          <!-- pulsing ring -->
          <span class="absolute inset-0 animate-ping rounded-2xl bg-accent opacity-20" />
        </div>
        <div class="text-center">
          <p class="text-xl font-semibold tracking-tight text-ink">DevDesk</p>
          <p class="mt-1 text-sm text-ink-subtle">Loading your workspace…</p>
        </div>
      </div>

      <div class="h-0.5 w-48 overflow-hidden rounded-full bg-surface-3">
        <div class="h-full animate-[shimmer_1.6s_ease-in-out_infinite] rounded-full bg-accent" style="background-size: 200% 100%; background-image: linear-gradient(90deg, transparent, var(--accent), transparent)" />
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.splash-leave-active {
  transition: opacity 0.4s ease 0.15s, transform 0.4s var(--ease-out-soft) 0.15s;
}
.splash-leave-to {
  opacity: 0;
  transform: scale(1.04);
}
</style>
