<script setup lang="ts">
import CodeBlock from '~/components/CodeBlock.vue'
import UiBadge from '~/components/UiBadge.vue'
import type { Snippet } from '~/types/api'

defineProps<{ snippet: Snippet }>()
defineEmits<{ edit: []; delete: [] }>()
</script>

<template>
  <article class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <header class="flex items-center gap-2">
      <h2 class="flex-1 truncate font-semibold">{{ snippet.title }}</h2>
      <UiBadge tone="indigo">{{ snippet.language }}</UiBadge>
    </header>
    <CodeBlock :code="snippet.code" :language="snippet.language" />
    <p v-if="snippet.notes" class="text-sm text-slate-600">{{ snippet.notes }}</p>
    <footer class="flex items-center gap-2">
      <span
        v-for="tag in snippet.tags"
        :key="tag"
        class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
      >
        {{ tag }}
      </span>
      <div class="ml-auto flex gap-2 text-sm">
        <button
          class="rounded-lg border border-slate-300 px-3 py-1 hover:bg-slate-100"
          @click="$emit('edit')"
        >
          Edit
        </button>
        <button
          class="rounded-lg px-3 py-1 text-red-600 hover:bg-red-50"
          @click="$emit('delete')"
        >
          Delete
        </button>
      </div>
    </footer>
  </article>
</template>
