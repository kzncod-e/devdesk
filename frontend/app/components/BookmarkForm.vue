<script setup lang="ts">
import { computed, ref } from 'vue'
import TagInput from '~/components/TagInput.vue'
import type { Bookmark, Project } from '~/types/api'

const props = defineProps<{
  bookmark?: Bookmark | null
  projects?: Project[]
  busy?: boolean
}>()
const emit = defineEmits<{
  submit: [data: Record<string, unknown>]
  cancel: []
}>()

const { current: currentWorkspace } = useWorkspace()

const url = ref(props.bookmark?.url ?? '')
const title = ref(props.bookmark?.title ?? '')
const tags = ref<string[]>([...(props.bookmark?.tags ?? [])])
const projectId = ref<number | null>(props.bookmark?.project_id ?? null)

const selectedProjectName = computed(() => {
  if (projectId.value === null) return 'none'
  const p = props.projects?.find(x => x.id === projectId.value)
  return p ? p.name : 'none'
})

const selectedProjectColor = computed(() => {
  if (projectId.value === null) return 'transparent'
  const p = props.projects?.find(x => x.id === projectId.value)
  return p ? p.color : 'transparent'
})

function submit() {
  if (props.bookmark) {
    emit('submit', { title: title.value, tags: tags.value, project_id: projectId.value })
  } else {
    emit('submit', { url: url.value, tags: tags.value, project_id: projectId.value })
  }
}

const workspaceLabel = computed(() =>
  (currentWorkspace?.value?.name ?? 'Workspace').slice(0, 3).toUpperCase()
)
</script>

<template>
  <form class="flex flex-col" @submit.prevent="submit">
    <!-- ── Linear-style breadcrumb header ── -->
    <div class="flex shrink-0 items-center justify-between border-b border-line px-5 py-3">
      <div class="flex items-center gap-2 text-[0.8125rem]">
        <span
          class="inline-grid size-5 shrink-0 place-items-center rounded bg-accent text-[10px] font-bold text-accent-fg"
        >
          {{ workspaceLabel }}
        </span>
        <span class="text-ink-muted">{{ currentWorkspace?.name ?? 'Workspace' }}</span>
        <UiIcon name="chevron" :size="13" class="text-ink-subtle" />
        <span class="font-medium text-ink">{{ bookmark ? 'Edit bookmark' : 'New bookmark' }}</span>
      </div>
      <button
        type="button"
        class="icon-btn"
        aria-label="Close"
        @click="emit('cancel')"
      >
        <UiIcon name="x" :size="16" />
      </button>
    </div>

    <!-- ── Body ── -->
    <div class="flex-1 overflow-y-auto overscroll-contain">
      <div class="px-6 pt-6 pb-2">
        <!-- URL field when creating -->
        <div v-if="!bookmark" class="space-y-1.5">
          <input
            v-model="url"
            type="url"
            required
            inputmode="url"
            autocapitalize="off"
            placeholder="Paste URL (https://…)"
            class="w-full bg-transparent text-[1.25rem] font-semibold tracking-tight text-ink placeholder:text-ink-subtle outline-none"
            autofocus
          />
          <p class="text-xs text-ink-subtle">Title, description and favicon are fetched automatically.</p>
        </div>

        <!-- Title field when editing -->
        <div v-else class="space-y-1.5">
          <input
            v-model="title"
            type="text"
            maxlength="300"
            placeholder="Bookmark title"
            class="w-full bg-transparent text-[1.25rem] font-semibold tracking-tight text-ink placeholder:text-ink-subtle outline-none"
            autofocus
          />
        </div>

        <!-- Tags section -->
        <div class="mt-5 space-y-2">
          <span class="field-label block uppercase tracking-wider text-[10px] font-semibold">Tags</span>
          <TagInput v-model="tags" aria-label="Tags" />
        </div>

        <!-- Metadata chips row (Project selector) -->
        <div class="flex flex-wrap items-center gap-1.5 pt-4 pb-2 border-t border-line mt-5">
          <!-- Project selector pill -->
          <UiMenu v-if="(projects ?? []).length" align="left">
            <template #trigger>
              <button
                type="button"
                class="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink-muted transition hover:border-line-strong hover:bg-surface-2"
              >
                <span
                  v-if="projectId !== null"
                  class="size-1.5 rounded-full"
                  :style="{ backgroundColor: selectedProjectColor }"
                />
                <UiIcon v-else name="folder" :size="11" />
                <span>Project: {{ selectedProjectName }}</span>
              </button>
            </template>
            <UiMenuItem
              @click="projectId = null"
            >
              <span class="text-xs font-medium text-ink">— none —</span>
            </UiMenuItem>
            <UiMenuItem
              v-for="p in projects"
              :key="p.id"
              @click="projectId = p.id"
            >
              <div class="flex items-center gap-2">
                <span class="size-1.5 rounded-full" :style="{ backgroundColor: p.color }" />
                <span class="text-xs font-medium text-ink">{{ p.name }}</span>
              </div>
            </UiMenuItem>
          </UiMenu>
        </div>
      </div>
    </div>

    <!-- ── Footer ── -->
    <div class="flex shrink-0 items-center justify-end gap-2 border-t border-line px-5 py-3.5">
      <UiButton variant="ghost" type="button" @click="emit('cancel')">Cancel</UiButton>
      <UiButton
        variant="primary"
        type="submit"
        :loading="busy"
        :disabled="!bookmark ? !url.trim() : !title.trim()"
      >
        {{ bookmark ? 'Save changes' : 'Add bookmark' }}
      </UiButton>
    </div>
  </form>
</template>
