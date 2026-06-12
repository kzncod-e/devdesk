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
  <form
    class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
    @submit.prevent="submit"
  >
    <h2 class="font-semibold">{{ props.snippet ? 'Edit snippet' : 'New snippet' }}</h2>
    <div class="flex gap-4">
      <label class="flex flex-1 flex-col gap-1 text-sm font-medium">
        Title
        <input
          v-model="title"
          type="text"
          required
          maxlength="200"
          class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
        >
      </label>
      <label class="flex w-44 flex-col gap-1 text-sm font-medium">
        Language
        <input
          v-model="language"
          type="text"
          required
          maxlength="50"
          placeholder="typescript"
          class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
        >
      </label>
    </div>
    <label class="flex flex-col gap-1 text-sm font-medium">
      Code
      <textarea
        v-model="code"
        rows="8"
        required
        spellcheck="false"
        class="rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs font-normal"
      />
    </label>
    <div class="flex gap-4">
      <label class="flex flex-1 flex-col gap-1 text-sm font-medium">
        Tags
        <TagInput v-model="tags" />
      </label>
      <label class="flex w-56 flex-col gap-1 text-sm font-medium">
        Project
        <select
          v-model="projectId"
          class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
        >
          <option :value="null">— none —</option>
          <option v-for="p in projects ?? []" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </label>
    </div>
    <label class="flex flex-col gap-1 text-sm font-medium">
      Notes
      <textarea
        v-model="notes"
        rows="2"
        class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
      />
    </label>
    <div class="flex gap-2">
      <button
        type="submit"
        :disabled="busy"
        class="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {{ props.snippet ? 'Save' : 'Create' }}
      </button>
      <button
        type="button"
        class="rounded-lg border border-slate-300 px-4 py-2 hover:bg-slate-100"
        @click="emit('cancel')"
      >
        Cancel
      </button>
    </div>
  </form>
</template>
