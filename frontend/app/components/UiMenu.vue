<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

withDefaults(defineProps<{ align?: 'left' | 'right' }>(), { align: 'right' })

const open = ref(false)
const root = ref<HTMLElement | null>(null)

function close() {
  open.value = false
}

function onClickOutside(e: MouseEvent) {
  if (root.value && !root.value.contains(e.target as Node)) close()
}
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div ref="root" class="relative">
    <div @click="open = !open">
      <slot name="trigger" :open="open" />
    </div>
    <Transition name="pop">
      <div
        v-if="open"
        :class="[
          'absolute z-40 mt-2 min-w-48 origin-top overflow-hidden rounded-xl border border-line bg-surface p-1.5 shadow-pop',
          align === 'right' ? 'right-0' : 'left-0',
        ]"
        role="menu"
        @click="close"
      >
        <slot />
      </div>
    </Transition>
  </div>
</template>
