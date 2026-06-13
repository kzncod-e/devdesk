<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'

// Single globally-mounted confirmation dialog driven by useConfirm().
const { state, settle } = useConfirm()

function onKeydown(e: KeyboardEvent) {
  if (!state.value.open) return
  if (e.key === 'Escape') settle(false)
  if (e.key === 'Enter') settle(true)
}

watch(
  () => state.value.open,
  (open) => {
    if (!import.meta.client) return
    if (open) window.addEventListener('keydown', onKeydown)
    else window.removeEventListener('keydown', onKeydown)
  },
)

onBeforeUnmount(() => {
  if (import.meta.client) window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="backdrop">
      <div
        v-if="state.open"
        class="fixed inset-0 z-[60] grid place-items-center bg-black/45 p-4 backdrop-blur-sm"
        @click.self="settle(false)"
      >
        <Transition name="dialog" appear>
          <div
            role="alertdialog"
            aria-modal="true"
            class="w-full max-w-sm rounded-2xl border border-line bg-surface p-6 shadow-overlay"
          >
            <div
              class="mb-4 grid size-11 place-items-center rounded-xl"
              :class="state.danger ? 'bg-danger-soft text-danger' : 'bg-accent-soft text-accent'"
            >
              <UiIcon :name="state.danger ? 'trash' : 'sparkles'" :size="22" />
            </div>
            <h2 class="text-base font-semibold text-ink">{{ state.title }}</h2>
            <p v-if="state.message" class="mt-1.5 text-sm text-ink-muted">{{ state.message }}</p>
            <div class="mt-6 flex justify-end gap-2">
              <UiButton variant="ghost" @click="settle(false)">
                {{ state.cancelLabel ?? 'Cancel' }}
              </UiButton>
              <UiButton
                :variant="state.danger ? 'primary' : 'primary'"
                :class="state.danger && 'bg-danger! text-white! hover:brightness-110'"
                @click="settle(true)"
              >
                {{ state.confirmLabel ?? 'Confirm' }}
              </UiButton>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
