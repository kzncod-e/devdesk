<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{ open: boolean; title?: string; subtitle?: string; width?: string; noHeader?: boolean }>(),
  { width: 'max-w-lg', noHeader: false },
)
const emit = defineEmits<{ close: [] }>()

const panel = ref<HTMLElement | null>(null)

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
    return
  }
  if (e.key === 'Tab' && panel.value) {
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
        class="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4 backdrop-blur-sm sm:p-6"
        @click.self="emit('close')"
      >
        <Transition name="dialog" appear>
          <div
            v-if="open"
            ref="panel"
            role="dialog"
            aria-modal="true"
            :aria-label="title"
            :class="[
              'flex w-full flex-col rounded-modal border border-line bg-surface shadow-overlay',
              'max-h-[88dvh]',
              width,
            ]"
          >
            <header v-if="!noHeader" class="flex shrink-0 items-start justify-between gap-4 border-b border-line px-5 py-3.5">
              <div class="min-w-0">
                <h2 v-if="title" class="truncate text-heading">{{ title }}</h2>
                <p v-if="subtitle" class="mt-0.5 text-helper">{{ subtitle }}</p>
              </div>
              <UiIconButton icon="x" label="Close" @click="emit('close')" />
            </header>
            <div :class="['flex-1 overflow-y-auto overscroll-contain', noHeader ? '' : 'px-5 py-4']">
              <slot />
            </div>
            <footer v-if="$slots.footer" class="shrink-0 border-t border-line px-5 py-3.5">
              <slot name="footer" />
            </footer>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
