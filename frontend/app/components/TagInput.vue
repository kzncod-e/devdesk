<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ modelValue: string[] }>()
const emit = defineEmits<{ 'update:modelValue': [tags: string[]] }>()

const draft = ref('')

function addTag() {
  const tag = draft.value.trim().toLowerCase()
  if (!tag || props.modelValue.includes(tag)) return
  emit('update:modelValue', [...props.modelValue, tag])
  draft.value = ''
}

function removeTag(tag: string) {
  emit('update:modelValue', props.modelValue.filter(t => t !== tag))
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-1.5 rounded-lg border border-slate-300 px-2 py-1.5">
    <span
      v-for="tag in modelValue"
      :key="tag"
      class="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700"
    >
      {{ tag }}
      <button
        type="button"
        :aria-label="`Remove ${tag}`"
        class="hover:text-indigo-950"
        @click="removeTag(tag)"
      >
        ×
      </button>
    </span>
    <input
      v-model="draft"
      type="text"
      placeholder="Add tag…"
      class="min-w-24 flex-1 border-none py-0.5 text-sm outline-none"
      @keydown.enter.prevent="addTag"
    >
  </div>
</template>
