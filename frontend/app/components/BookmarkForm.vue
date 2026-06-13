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
  <form class="flex flex-col gap-5" @submit.prevent="submit">
    <div v-if="!props.bookmark" class="flex flex-col gap-1.5">
      <label class="field-label">URL</label>
      <div class="relative">
        <UiIcon name="bookmark" :size="16" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle" />
        <input v-model="url" type="url" required placeholder="https://…" class="field-input pl-9">
      </div>
      <p class="text-xs text-ink-subtle">Title, description and favicon are fetched automatically.</p>
    </div>
    <div v-else class="flex flex-col gap-1.5">
      <label class="field-label">Title</label>
      <input v-model="title" type="text" maxlength="300" class="field-input">
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

    <div class="flex justify-end gap-2 pt-4">
      <UiButton variant="ghost" type="button" @click="emit('cancel')">Cancel</UiButton>
      <UiButton variant="primary" type="submit" :loading="busy" icon="check">
        {{ props.bookmark ? 'Save changes' : 'Add bookmark' }}
      </UiButton>
    </div>
  </form>
</template>
