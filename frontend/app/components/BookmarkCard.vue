<script setup lang="ts">
import type { Bookmark } from '~/types/api'

defineProps<{ bookmark: Bookmark }>()
defineEmits<{ edit: []; delete: [] }>()
</script>

<template>
  <article class="flex gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <img
      v-if="bookmark.favicon"
      :src="bookmark.favicon"
      alt=""
      class="mt-1 size-5 shrink-0 rounded"
    >
    <div class="min-w-0 flex-1">
      <a
        :href="bookmark.url"
        target="_blank"
        rel="noopener noreferrer"
        class="font-semibold text-indigo-700 hover:underline"
      >
        {{ bookmark.title || bookmark.url.replace(/^https?:\/\//, '') }}
      </a>
      <p v-if="bookmark.description" class="mt-0.5 line-clamp-2 text-sm text-slate-600">
        {{ bookmark.description }}
      </p>
      <div class="mt-2 flex items-center gap-2">
        <span
          v-for="tag in bookmark.tags"
          :key="tag"
          class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
        >
          {{ tag }}
        </span>
      </div>
    </div>
    <div class="flex shrink-0 items-start gap-2 text-sm">
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
  </article>
</template>
