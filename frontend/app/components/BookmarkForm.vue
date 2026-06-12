<script setup lang="ts">
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

const url = ref(props.bookmark?.url ?? '')
const title = ref(props.bookmark?.title ?? '')
const tags = ref<string[]>([...(props.bookmark?.tags ?? [])])
const projectId = ref<number | null>(props.bookmark?.project_id ?? null)

function submit() {
  if (props.bookmark) {
    // url is immutable after creation; metadata belongs to the fetcher
    emit('submit', { title: title.value, tags: tags.value, project_id: projectId.value })
  } else {
    emit('submit', { url: url.value, tags: tags.value, project_id: projectId.value })
  }
}
</script>

<template>
  <form
    class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
    @submit.prevent="submit"
  >
    <h2 class="font-semibold">{{ props.bookmark ? 'Edit bookmark' : 'New bookmark' }}</h2>
    <label v-if="!props.bookmark" class="flex flex-col gap-1 text-sm font-medium">
      URL
      <input
        v-model="url"
        type="url"
        required
        placeholder="https://…"
        class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
      >
    </label>
    <label v-else class="flex flex-col gap-1 text-sm font-medium">
      Title
      <input
        v-model="title"
        type="text"
        maxlength="300"
        class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
      >
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
    <div class="flex gap-2">
      <button
        type="submit"
        :disabled="busy"
        class="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {{ props.bookmark ? 'Save' : 'Add bookmark' }}
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
