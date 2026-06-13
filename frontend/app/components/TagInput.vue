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

function onBackspace() {
  if (!draft.value && props.modelValue.length) {
    removeTag(props.modelValue[props.modelValue.length - 1]!)
  }
}
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-1.5 rounded-lg border border-line bg-surface px-2 py-1.5 shadow-sm transition focus-within:border-accent focus-within:ring-4 focus-within:ring-[var(--accent-ring)]"
  >
    <TransitionGroup name="pop">
      <span
        v-for="tag in modelValue"
        :key="tag"
        class="inline-flex items-center gap-1 rounded-full bg-accent-soft px-2 py-0.5 text-xs font-medium text-accent"
      >
        {{ tag }}
        <button
          type="button"
          :aria-label="`Remove ${tag}`"
          class="grid size-3.5 place-items-center rounded-full transition hover:bg-accent hover:text-accent-fg"
          @click="removeTag(tag)"
        >
          <UiIcon name="x" :size="10" />
        </button>
      </span>
    </TransitionGroup>
    <input
      v-model="draft"
      type="text"
      placeholder="Add tag…"
      class="min-w-24 flex-1 border-none bg-transparent py-0.5 text-sm text-ink outline-none placeholder:text-ink-subtle"
      @keydown.enter.prevent="addTag"
      @keydown.delete="onBackspace"
    >
  </div>
</template>
