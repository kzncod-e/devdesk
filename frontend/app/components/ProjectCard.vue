<script setup lang="ts">
import { computed } from 'vue'

import UiBadge from '~/components/UiBadge.vue'
import type { Project } from '~/types/api'

const props = defineProps<{ project: Project }>()
defineEmits<{
  open: []
  edit: []
  archive: []
  delete: []
  template: []
}>()

const isActive = computed(() => props.project.status === 'active')

// Insert Cloudinary transformation params between /upload/ and the public_id.
// e.g. "https://res.cloudinary.com/cloud/image/upload/path/to/img.jpg"
//   → "https://res.cloudinary.com/cloud/image/upload/c_fill,g_auto,f_auto,q_auto,w_384,h_96/path/to/img.jpg"
function cldOptimize(url: string) {
  return url.replace('/upload/', '/upload/c_fill,g_auto,f_auto,q_auto,w_384,h_96/')
}
</script>

<template>
  <article
    class="group relative flex cursor-pointer flex-col gap-4 overflow-hidden rounded-card border border-line bg-surface shadow-card transition-all duration-200 ease-[var(--ease-out-soft)] hover:-translate-y-0.5 hover:border-line-strong hover:shadow-card-hover"
    @click="$emit('open')"
  >
    <!-- Cover image or accent bar -->
    <div v-if="project.image_url" class="relative h-24 overflow-hidden">
      <img
        :src="cldOptimize(project.image_url)"
        :alt="project.name"
        class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        width="384"
        height="96"
        loading="lazy"
      >
      <div class="absolute inset-0 bg-linear-to-b from-transparent to-surface/60" />
    </div>
    <span
      v-else
      class="pointer-events-none absolute inset-x-0 -top-px h-1 opacity-80"
      :style="{ background: `linear-gradient(90deg, ${project.color}, transparent)` }"
      aria-hidden="true"
    />

    <div :class="['flex flex-col gap-4', project.image_url ? 'px-5 pb-5' : 'p-5 pt-4']">
      <header class="flex items-start gap-3">
        <span
          class="mt-0.5 grid size-9 shrink-0 place-items-center rounded-lg text-sm font-semibold"
          :style="{ backgroundColor: `${project.color}1a`, color: project.color }"
          aria-hidden="true"
        >
          <UiIcon name="folder" :size="18" />
        </span>
        <div class="min-w-0 flex-1">
          <h2 class="truncate text-[15px] font-semibold text-ink">{{ project.name }}</h2>
          <UiBadge :tone="isActive ? 'green' : 'gray'" dot class="mt-1">
            {{ project.status }}
          </UiBadge>
        </div>

        <!-- contextual actions: fade in on hover, but stay accessible -->
        <div
          class="flex shrink-0 gap-0.5 opacity-0 transition-opacity duration-150 focus-within:opacity-100 group-hover:opacity-100"
          @click.stop
        >
          <button type="button" class="icon-btn" aria-label="Save project as template" @click="$emit('template')">
            <UiIcon name="layers" :size="15" />
          </button>
          <button type="button" class="icon-btn" aria-label="Edit project" @click="$emit('edit')">
            <UiIcon name="edit" :size="15" />
          </button>
          <button
            type="button"
            class="icon-btn"
            :aria-label="isActive ? 'Archive project' : 'Unarchive project'"
            @click="$emit('archive')"
          >
            <UiIcon :name="isActive ? 'archive' : 'unarchive'" :size="15" />
          </button>
          <button type="button" class="icon-btn icon-btn-danger" aria-label="Delete project" @click="$emit('delete')">
            <UiIcon name="trash" :size="15" />
          </button>
        </div>
      </header>

      <p class="line-clamp-2 min-h-10 text-sm text-ink-muted">
        {{ project.description || 'No description yet.' }}
      </p>

      <footer class="mt-auto flex items-center gap-1.5 text-sm font-medium text-accent">
        <button class="inline-flex items-center gap-1.5" @click.stop="$emit('open')">
          Open board
          <UiIcon name="chevron" :size="15" class="transition-transform duration-200 group-hover:translate-x-0.5" />
        </button>
      </footer>
    </div>
  </article>
</template>
