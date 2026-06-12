<script setup lang="ts">
import type { Task } from '~/types/api'

const props = defineProps<{ task?: Task | null; busy?: boolean }>()
const emit = defineEmits<{
  submit: [data: { title: string; description: string; priority: string; due_date: string | null }]
  cancel: []
}>()

const title = ref(props.task?.title ?? '')
const description = ref(props.task?.description ?? '')
const priority = ref(props.task?.priority ?? 'medium')
const dueDate = ref(props.task?.due_date ?? '')

function submit() {
  emit('submit', {
    title: title.value,
    description: description.value,
    priority: priority.value,
    due_date: dueDate.value || null,
  })
}
</script>

<template>
  <form
    class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
    @submit.prevent="submit"
  >
    <h2 class="font-semibold">{{ props.task ? 'Edit task' : 'New task' }}</h2>
    <label class="flex flex-col gap-1 text-sm font-medium">
      Title
      <input
        v-model="title"
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
    <div class="flex gap-4">
      <label class="flex flex-col gap-1 text-sm font-medium">
        Priority
        <select v-model="priority" class="rounded-lg border border-slate-300 px-3 py-2 font-normal">
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>
      <label class="flex flex-col gap-1 text-sm font-medium">
        Due date
        <input
          v-model="dueDate"
          type="date"
          class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
        >
      </label>
    </div>
    <div class="flex gap-2">
      <button
        type="submit"
        :disabled="busy"
        class="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {{ props.task ? 'Save' : 'Create' }}
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
