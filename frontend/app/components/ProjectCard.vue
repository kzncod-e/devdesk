<script setup lang="ts">
import UiBadge from '~/components/UiBadge.vue'
import type { Project } from '~/types/api'

defineProps<{ project: Project }>()
defineEmits<{
  open: []
  edit: []
  archive: []
  delete: []
}>()
</script>

<template>
  <article class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <header class="flex items-center gap-2">
      <span
        class="size-3 shrink-0 rounded-full"
        :style="{ backgroundColor: project.color }"
        aria-hidden="true"
      />
      <h2 class="flex-1 truncate text-lg font-semibold">{{ project.name }}</h2>
      <UiBadge :tone="project.status === 'active' ? 'green' : 'gray'">
        {{ project.status }}
      </UiBadge>
    </header>
    <p class="line-clamp-2 min-h-10 text-sm text-slate-600">{{ project.description }}</p>
    <footer class="flex gap-2 text-sm">
      <button
        class="rounded-lg bg-indigo-600 px-3 py-1.5 font-medium text-white hover:bg-indigo-700"
        @click="$emit('open')"
      >
        Open board
      </button>
      <button
        class="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-100"
        @click="$emit('edit')"
      >
        Edit
      </button>
      <button
        class="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-100"
        @click="$emit('archive')"
      >
        {{ project.status === 'active' ? 'Archive' : 'Unarchive' }}
      </button>
      <button
        class="ml-auto rounded-lg px-3 py-1.5 text-red-600 hover:bg-red-50"
        @click="$emit('delete')"
      >
        Delete
      </button>
    </footer>
  </article>
</template>
