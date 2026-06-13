<script setup lang="ts">
const { toasts, dismiss } = useToast()

const toneIcon: Record<string, string> = {
  default: 'sparkles',
  success: 'check',
  error: 'x',
}
const toneClass: Record<string, string> = {
  default: 'text-accent',
  success: 'text-success',
  error: 'text-danger',
}
</script>

<template>
  <Teleport to="body">
    <div class="pointer-events-none fixed bottom-5 right-5 z-[70] flex w-80 flex-col gap-2.5">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="pointer-events-auto flex items-start gap-3 rounded-xl border border-line bg-surface px-4 py-3 shadow-pop"
          role="status"
        >
          <span
            class="mt-0.5 grid size-6 shrink-0 place-items-center rounded-md bg-surface-2"
            :class="toneClass[t.tone]"
          >
            <UiIcon :name="toneIcon[t.tone]" :size="15" />
          </span>
          <p class="flex-1 text-sm text-ink">{{ t.message }}</p>
          <button
            class="text-ink-subtle transition hover:text-ink"
            aria-label="Dismiss"
            @click="dismiss(t.id)"
          >
            <UiIcon name="x" :size="15" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
