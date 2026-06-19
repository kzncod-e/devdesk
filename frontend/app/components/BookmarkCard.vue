<script setup lang="ts">
import { computed } from 'vue'

import type { Bookmark } from '~/types/api'

const props = defineProps<{ bookmark: Bookmark }>()
defineEmits<{ edit: []; delete: [] }>()

const host = computed(() => {
  try {
    return new URL(props.bookmark.url).hostname.replace(/^www\./, '')
  } catch {
    return props.bookmark.url.replace(/^https?:\/\//, '')
  }
})
</script>

<template>
  <article
    class="group flex items-center gap-3.5 rounded-card border border-line bg-surface p-3.5 shadow-card transition-all duration-200 ease-[var(--ease-out-soft)] hover:-translate-y-0.5 hover:border-line-strong hover:shadow-card-hover"
  >
    <div class="grid size-10 shrink-0 place-items-center overflow-hidden rounded-lg border border-line bg-surface-2">
      <img v-if="bookmark.favicon" :src="bookmark.favicon" alt="" class="size-5 rounded">
      <UiIcon v-else name="bookmark" :size="18" class="text-ink-subtle" />
    </div>

    <div class="min-w-0 flex-1">
      <a
        :href="bookmark.url"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-1.5 text-card-title transition hover:text-accent"
      >
        <span class="truncate">{{ bookmark.title || bookmark.url.replace(/^https?:\/\//, '') }}</span>
        <UiIcon name="external" :size="13" class="shrink-0 text-ink-subtle" />
      </a>
      <p v-if="bookmark.description" class="mt-0.5 line-clamp-1 text-sm text-ink-muted">
        {{ bookmark.description }}
      </p>
      <div class="mt-1 flex flex-wrap items-center gap-1.5">
        <span class="text-xs text-ink-subtle">{{ host }}</span>
        <span v-if="bookmark.tags.length" class="text-ink-subtle">·</span>
        <span
          v-for="tag in bookmark.tags"
          :key="tag"
          class="rounded-full bg-surface-2 px-2 py-0.5 text-xs text-ink-muted"
        >
          {{ tag }}
        </span>
      </div>
    </div>

    <div
      class="flex shrink-0 gap-0.5 opacity-0 transition-opacity duration-150 focus-within:opacity-100 group-hover:opacity-100"
    >
      <button type="button" class="icon-btn" aria-label="Edit bookmark" @click="$emit('edit')">
        <UiIcon name="edit" :size="15" />
      </button>
      <button type="button" class="icon-btn icon-btn-danger" aria-label="Delete bookmark" @click="$emit('delete')">
        <UiIcon name="trash" :size="15" />
      </button>
    </div>
  </article>
</template>
