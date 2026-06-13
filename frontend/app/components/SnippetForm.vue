<script setup lang="ts">
import TagInput from '~/components/TagInput.vue'
import type { Project, Snippet } from '~/types/api'

const props = defineProps<{
  snippet?: Snippet | null
  projects?: Project[]
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
  }]
  cancel: []
}>()

const title = ref(props.snippet?.title ?? '')
const language = ref(props.snippet?.language ?? '')
const code = ref(props.snippet?.code ?? '')
const tags = ref<string[]>([...(props.snippet?.tags ?? [])])
const notes = ref(props.snippet?.notes ?? '')
const projectId = ref<number | null>(props.snippet?.project_id ?? null)

function submit() {
  emit('submit', {
    title: title.value,
    language: language.value,
    code: code.value,
    tags: tags.value,
    notes: notes.value,
    project_id: projectId.value,
  })
}
</script>

<template>
  <form class="flex flex-col gap-5" @submit.prevent="submit">
    <div class="flex gap-4">
      <div class="flex flex-1 flex-col gap-1.5">
        <label class="field-label">Title</label>
        <input v-model="title" type="text" required maxlength="200" placeholder="Snippet title" class="field-input">
      </div>
      <div class="flex w-40 flex-col gap-1.5">
        <label class="field-label">Language</label>
        <input v-model="language" type="text" required maxlength="50" placeholder="typescript" class="field-input">
      </div>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="field-label">Code</label>
      <textarea
        v-model="code"
        rows="10"
        required
        spellcheck="false"
        placeholder="Paste your code…"
        class="field-input resize-none rounded-lg bg-surface-2 font-mono text-xs leading-relaxed"
      />
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="field-label">Tags</label>
      <TagInput v-model="tags" />
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="field-label">Project</label>
      <select v-model="projectId" class="field-input">
        <option :value="null">— none —</option>
        <option v-for="p in projects ?? []" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="field-label">Notes</label>
      <textarea v-model="notes" rows="2" placeholder="Optional context" class="field-input resize-none" />
    </div>

    <div class="flex justify-end gap-2 pt-4">
      <UiButton variant="ghost" type="button" @click="emit('cancel')">Cancel</UiButton>
      <UiButton variant="primary" type="submit" :loading="busy" icon="check">
        {{ props.snippet ? 'Save changes' : 'Create snippet' }}
      </UiButton>
    </div>
  </form>
</template>
