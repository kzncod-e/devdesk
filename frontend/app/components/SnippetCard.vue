<script setup lang="ts">
import { ref } from 'vue'

import CodeBlock from '~/components/CodeBlock.vue'
import type { Snippet } from '~/types/api'

const props = withDefaults(
  defineProps<{ snippet: Snippet; tagColors?: Record<string, string> }>(),
  { tagColors: () => ({}) },
)
defineEmits<{ edit: []; delete: []; template: [] }>()

const expanded = ref(false)

// Presentational: colors are supplied by the parent (from the tag registry).
function colorOf(tag: string): string {
  return props.tagColors[tag.toLowerCase()] ?? '#6366f1'
}
</script>

<template>
  <article
    class="group flex flex-col gap-3 rounded-card border border-line bg-surface p-4 shadow-card transition-all duration-200 hover:border-line-strong hover:shadow-card-hover"
  >
    <header class="flex items-center gap-2">
      <span class="grid size-8 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent">
        <UiIcon name="code" :size="16" />
      </span>
      <h2 class="min-w-0 flex-1 truncate text-sm font-semibold text-ink">{{ snippet.title }}</h2>
      <div
        class="flex shrink-0 gap-0.5 opacity-0 transition-opacity duration-150 focus-within:opacity-100 group-hover:opacity-100"
      >
        <button type="button" class="icon-btn" aria-label="Save snippet as template" @click="$emit('template')">
          <UiIcon name="layers" :size="15" />
        </button>
        <button type="button" class="icon-btn" aria-label="Edit snippet" @click="$emit('edit')">
          <UiIcon name="edit" :size="15" />
        </button>
        <button type="button" class="icon-btn icon-btn-danger" aria-label="Delete snippet" @click="$emit('delete')">
          <UiIcon name="trash" :size="15" />
        </button>
      </div>
    </header>

    <CodeBlock :code="snippet.code" :language="snippet.language" collapsible :expanded="expanded" />

    <button
      type="button"
      :aria-expanded="expanded"
      class="self-start text-xs font-medium text-ink-subtle transition hover:text-accent"
      @click="expanded = !expanded"
    >
      {{ expanded ? 'Show less' : 'Show more' }}
    </button>

    <p v-if="snippet.notes" class="text-sm text-ink-muted">{{ snippet.notes }}</p>

    <footer v-if="snippet.tags.length" class="flex flex-wrap items-center gap-1.5">
      <span
        v-for="tag in snippet.tags"
        :key="tag"
        class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
        :style="{ backgroundColor: `${colorOf(tag)}1a`, color: colorOf(tag) }"
      >
        <span class="size-1.5 rounded-full" :style="{ backgroundColor: colorOf(tag) }" />
        {{ tag }}
      </span>
    </footer>
  </article>
</template>
