<script setup lang="ts">
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

const { names: tagSuggestions } = useTags()

const title = ref(props.snippet?.title ?? '')
const language = ref(props.snippet?.language ?? '')
const code = ref(props.snippet?.code ?? '')
const tags = ref<string[]>([...(props.snippet?.tags ?? [])])
const notes = ref(props.snippet?.notes ?? '')
const projectId = ref<number | null>(props.snippet?.project_id ?? null)
const collectionId = ref<number | null>(props.snippet?.collection_id ?? null)

function submit() {
  emit('submit', {
    title: title.value,
    language: language.value,
    code: code.value,
    tags: tags.value,
    notes: notes.value,
    project_id: projectId.value,
    collection_id: collectionId.value,
  })
}
</script>

<template>
  <form class="flex flex-col gap-5" @submit.prevent="submit">
    <div class="flex gap-4">
      <label class="flex flex-1 flex-col gap-1.5">
        <span class="field-label">Title</span>
        <input v-model="title" type="text" required maxlength="200" placeholder="Snippet title…" class="field-input">
      </label>
      <label class="flex w-40 flex-col gap-1.5">
        <span class="field-label">Language</span>
        <input v-model="language" type="text" required maxlength="50" spellcheck="false" autocapitalize="off" placeholder="typescript" class="field-input">
      </label>
    </div>

    <label class="flex flex-col gap-1.5">
      <span class="field-label">Code</span>
      <textarea
        v-model="code"
        rows="10"
        required
        spellcheck="false"
        placeholder="Paste your code…"
        class="field-input resize-none rounded-lg bg-surface-2 font-mono text-xs leading-relaxed"
      />
    </label>

    <div class="flex flex-col gap-1.5">
      <span class="field-label">Tags</span>
      <TagInput v-model="tags" :suggestions="tagSuggestions" aria-label="Tags" />
    </div>

    <div class="flex gap-4">
      <label class="flex flex-1 flex-col gap-1.5">
        <span class="field-label">Project</span>
        <select v-model="projectId" class="field-input">
          <option :value="null">— none —</option>
          <option v-for="p in projects ?? []" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </label>
      <label class="flex flex-1 flex-col gap-1.5">
        <span class="field-label">Collection</span>
        <select v-model="collectionId" class="field-input">
          <option :value="null">— none —</option>
          <option v-for="c in collections ?? []" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </label>
    </div>

    <label class="flex flex-col gap-1.5">
      <span class="field-label">Notes</span>
      <textarea v-model="notes" rows="2" placeholder="Optional context" class="field-input resize-none" />
    </label>

    <div class="flex justify-end gap-2 pt-4">
      <UiButton variant="ghost" type="button" @click="emit('cancel')">Cancel</UiButton>
      <UiButton variant="primary" type="submit" :loading="busy" icon="check">
        {{ props.snippet ? 'Save changes' : 'Create snippet' }}
      </UiButton>
    </div>
  </form>
</template>
