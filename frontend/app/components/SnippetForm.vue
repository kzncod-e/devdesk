<script setup lang="ts">
import { computed, ref } from 'vue'
import TagInput from '~/components/TagInput.vue'
import type { Collection, Project, Snippet } from '~/types/api'

const props = defineProps<{
  snippet?: Snippet | null
  projects?: Project[]
  collections?: Collection[]
  busy?: boolean
}>()
const emit = defineEmits<{
  submit: [data: {
    title: string
    language: string
    code: string
    tags: string[]
    notes: string
    project_id: number | null
    collection_id: number | null
  }]
  cancel: []
}>()

const { current: currentWorkspace } = useWorkspace()
const { names: tagSuggestions } = useTags()

const title = ref(props.snippet?.title ?? '')
const language = ref(props.snippet?.language ?? '')
const code = ref(props.snippet?.code ?? '')
const tags = ref<string[]>([...(props.snippet?.tags ?? [])])
const notes = ref(props.snippet?.notes ?? '')
const projectId = ref<number | null>(props.snippet?.project_id ?? null)
const collectionId = ref<number | null>(props.snippet?.collection_id ?? null)

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

const selectedCollectionName = computed(() => {
  if (collectionId.value === null) return 'none'
  const c = props.collections?.find(x => x.id === collectionId.value)
  return c ? c.name : 'none'
})

function submit() {
  emit('submit', {
    title: title.value,
    language: language.value || 'txt',
    code: code.value,
    tags: tags.value,
    notes: notes.value,
    project_id: projectId.value,
    collection_id: collectionId.value,
  })
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
        <span class="font-medium text-ink">{{ snippet ? 'Edit snippet' : 'New snippet' }}</span>
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
      <div class="px-6 pt-6 pb-2 space-y-4">
        <!-- Title & Language Inline -->
        <div class="flex items-start gap-4">
          <input
            v-model="title"
            type="text"
            required
            maxlength="200"
            placeholder="Snippet title"
            class="flex-1 bg-transparent text-[1.25rem] font-semibold tracking-tight text-ink placeholder:text-ink-subtle outline-none"
            autofocus
          />
          <input
            v-model="language"
            type="text"
            required
            maxlength="50"
            spellcheck="false"
            autocapitalize="off"
            placeholder="language (e.g. typescript)"
            class="w-48 bg-transparent text-right text-sm text-ink-muted placeholder:text-ink-subtle outline-none border-b border-transparent focus:border-line pb-1 mt-1 font-mono"
          />
        </div>

        <!-- Code Block Textarea -->
        <div class="relative rounded-lg border border-line overflow-hidden">
          <div class="flex items-center justify-between bg-surface-2 px-3 py-1.5 border-b border-line text-[11px] text-ink-subtle font-mono uppercase">
            <span>Editor</span>
            <span>{{ language || 'plain text' }}</span>
          </div>
          <textarea
            v-model="code"
            rows="10"
            required
            spellcheck="false"
            placeholder="Paste or write your code here…"
            class="w-full block bg-surface-2 p-3 font-mono text-xs leading-relaxed text-ink placeholder:text-ink-subtle outline-none resize-none"
          />
        </div>

        <!-- Notes (context info) -->
        <div class="space-y-1.5">
          <span class="field-label block uppercase tracking-wider text-[10px] font-semibold">Notes</span>
          <textarea
            v-model="notes"
            rows="2"
            placeholder="Add optional description, notes, or usage instructions…"
            class="w-full bg-transparent text-sm leading-relaxed text-ink placeholder:text-ink-subtle outline-none resize-none"
          />
        </div>

        <!-- Tags section -->
        <div class="space-y-1.5">
          <span class="field-label block uppercase tracking-wider text-[10px] font-semibold">Tags</span>
          <TagInput v-model="tags" :suggestions="tagSuggestions" aria-label="Tags" />
        </div>

        <!-- Metadata chips row (Project & Collection selectors) -->
        <div class="flex flex-wrap items-center gap-2 pt-4 pb-2 border-t border-line mt-4">
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

          <!-- Collection selector pill -->
          <UiMenu v-if="(collections ?? []).length" align="left">
            <template #trigger>
              <button
                type="button"
                class="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink-muted transition hover:border-line-strong hover:bg-surface-2"
              >
                <UiIcon name="layers" :size="11" />
                <span>Collection: {{ selectedCollectionName }}</span>
              </button>
            </template>
            <UiMenuItem
              @click="collectionId = null"
            >
              <span class="text-xs font-medium text-ink">— none —</span>
            </UiMenuItem>
            <UiMenuItem
              v-for="c in collections"
              :key="c.id"
              @click="collectionId = c.id"
            >
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium text-ink">{{ c.name }}</span>
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
        :disabled="!title.trim() || !code.trim()"
      >
        {{ snippet ? 'Save changes' : 'Create snippet' }}
      </UiButton>
    </div>
  </form>
</template>
