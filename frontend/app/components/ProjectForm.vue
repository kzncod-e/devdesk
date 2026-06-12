<script setup lang="ts">
import type { Project } from '~/types/api'

const props = defineProps<{ project?: Project | null; busy?: boolean }>()
const emit = defineEmits<{
  submit: [data: { name: string; description: string; color: string }]
  cancel: []
}>()

const name = ref(props.project?.name ?? '')
const description = ref(props.project?.description ?? '')
const color = ref(props.project?.color ?? '#6366f1')
</script>

<template>
  <form
    class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
    @submit.prevent="emit('submit', { name, description, color })"
  >
    <h2 class="font-semibold">{{ props.project ? 'Edit project' : 'New project' }}</h2>
    <label class="flex flex-col gap-1 text-sm font-medium">
      Name
      <input
        v-model="name"
        type="text"
        required
        maxlength="200"
        class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
      >
    </label>
    <label class="flex flex-col gap-1 text-sm font-medium">
      Description
      <textarea
        v-model="description"
        rows="2"
        class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
      />
    </label>
    <label class="flex items-center gap-2 text-sm font-medium">
      Color
      <input v-model="color" type="color" class="h-8 w-12 cursor-pointer rounded border border-slate-300">
    </label>
    <div class="flex gap-2">
      <button
        type="submit"
        :disabled="busy"
        class="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {{ props.project ? 'Save' : 'Create' }}
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
