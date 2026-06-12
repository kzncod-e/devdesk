<script setup lang="ts">
import { computed } from 'vue'
import hljs from 'highlight.js/lib/common'
import 'highlight.js/styles/github.css'

const props = defineProps<{ code: string; language?: string }>()

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
</script>

<template>
  <pre
    class="max-h-64 overflow-auto rounded-lg bg-slate-50 p-3 text-xs leading-relaxed"
  ><code class="hljs !bg-transparent" v-html="highlighted" /></pre>
</template>
