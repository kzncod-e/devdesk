<script setup lang="ts">
import { computed, ref } from 'vue'
import hljs from 'highlight.js/lib/common'
import 'highlight.js/styles/github.css'

const props = withDefaults(
  defineProps<{ code: string; language?: string; collapsible?: boolean; expanded?: boolean }>(),
  { collapsible: false, expanded: true },
)

const copied = ref(false)

const highlighted = computed(() => {
  try {
    if (props.language && hljs.getLanguage(props.language)) {
      return hljs.highlight(props.code, { language: props.language }).value
    }
    return hljs.highlightAuto(props.code).value
  } catch {
    return props.code
  }
})

async function copy() {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    setTimeout(() => (copied.value = false), 1600)
  } catch {
    /* clipboard unavailable */
  }
}
</script>

<template>
  <div class="overflow-hidden rounded-lg border border-line bg-surface-2">
    <div class="flex items-center gap-2 border-b border-line px-3 py-1.5">
      <span class="flex gap-1.5" aria-hidden="true">
        <span class="size-2.5 rounded-full bg-red-400/70" />
        <span class="size-2.5 rounded-full bg-amber-400/70" />
        <span class="size-2.5 rounded-full bg-green-400/70" />
      </span>
      <span class="ml-1 font-mono text-xs text-ink-subtle">{{ language || 'code' }}</span>
      <button
        type="button"
        class="ml-auto inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-ink-subtle transition hover:bg-surface-3 hover:text-ink"
        :aria-label="copied ? 'Copied' : 'Copy code'"
        @click.stop="copy"
      >
        <UiIcon :name="copied ? 'check' : 'copy'" :size="14" :class="copied && 'text-success'" />
        <span :class="copied && 'text-success'">{{ copied ? 'Copied' : 'Copy' }}</span>
      </button>
    </div>
    <pre
      :class="[
        'overflow-auto bg-transparent p-3 text-xs leading-relaxed transition-[max-height] duration-300',
        collapsible && !expanded ? 'max-h-24' : 'max-h-80',
      ]"
    ><code class="hljs bg-transparent!" v-html="highlighted" /></pre>
  </div>
</template>
