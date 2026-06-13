<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{ open: boolean; title?: string; subtitle?: string; width?: string }>(),
  { width: 'max-w-lg' },
)
const emit = defineEmits<{ close: [] }>()

const panel = ref<HTMLElement | null>(null)

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
    return
  }
  if (e.key === 'Tab' && panel.value) {
    // Simple focus trap within the panel.
    const focusable = panel.value.querySelectorAll<HTMLElement>(
      'a[href],button:not([disabled]),textarea,input,select,[tabindex]:not([tabindex="-1"])',
    )
    if (!focusable.length) return
    const first = focusable[0]!
    const last = focusable[focusable.length - 1]!
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }
}

watch(
  () => props.open,
  async (open) => {
    if (!import.meta.client) return
    document.body.style.overflow = open ? 'hidden' : ''
    if (open) {
      window.addEventListener('keydown', onKeydown)
      await nextTick()
      panel.value
        ?.querySelector<HTMLElement>('input,textarea,button,[tabindex]')
        ?.focus()
    } else {
      window.removeEventListener('keydown', onKeydown)
    }
  },
)

onBeforeUnmount(() => {
  if (!import.meta.client) return
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="backdrop">
      <div
        v-if="open"
        class="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
        @click="emit('close')"
      />
    </Transition>
    <Transition name="drawer">
      <aside
        v-if="open"
        ref="panel"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        :class="[
          'fixed inset-y-0 right-0 z-50 flex w-full flex-col bg-surface shadow-overlay',
          'border-l border-line',
          width,
        ]"
      >
        <header class="flex items-start justify-between gap-4 border-b border-line px-6 py-5">
          <div class="min-w-0">
            <h2 v-if="title" class="truncate text-lg font-semibold text-ink">{{ title }}</h2>
            <p v-if="subtitle" class="mt-0.5 text-sm text-ink-muted">{{ subtitle }}</p>
          </div>
          <UiIconButton icon="x" label="Close" @click="emit('close')" />
        </header>
        <div class="flex-1 overflow-y-auto px-6 py-5">
          <slot />
        </div>
        <footer v-if="$slots.footer" class="border-t border-line px-6 py-4">
          <slot name="footer" />
        </footer>
      </aside>
    </Transition>
  </Teleport>
</template>
