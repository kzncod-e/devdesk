<script setup lang="ts">
import { useMutation } from '@tanstack/vue-query'

import type { TemplateVisibility } from '~/types/api'

const { open, target, close } = useSaveTemplate()
const { capture } = useTemplates()
const { current } = useWorkspace()
const { success, error } = useToast()

const name = ref('')
const description = ref('')
const visibility = ref<TemplateVisibility>('workspace')

// Public publishing requires workspace:manage (owner/admin) — mirrors the backend.
const canPublish = computed(
  () => current.value?.role === 'owner' || current.value?.role === 'admin',
)

// Prefill a sensible name each time the modal opens for a new source.
watch(open, (isOpen) => {
  if (isOpen && target.value) {
    name.value = `${target.value.sourceName} template`
    description.value = ''
    visibility.value = 'workspace'
  }
})

const save = useMutation({
  mutationFn: () =>
    capture({
      kind: target.value!.kind,
      source_id: target.value!.sourceId,
      name: name.value.trim(),
      description: description.value.trim(),
      visibility: visibility.value,
    }),
  onSuccess: (tpl) => {
    success(`Saved “${tpl.name}” as a template`)
    close()
  },
  onError: () => error('Could not save template'),
})
</script>

<template>
  <UiModal
    :open="open"
    title="Save as template"
    :subtitle="target ? `Capture this ${target.kind} for reuse` : ''"
    @close="close"
  >
    <form v-if="target" class="flex flex-col gap-4" @submit.prevent="save.mutate()">
      <label class="flex flex-col gap-1.5">
        <span class="field-label">Template name</span>
        <input v-model="name" type="text" required maxlength="200" class="field-input">
      </label>

      <label class="flex flex-col gap-1.5">
        <span class="field-label">Description</span>
        <textarea v-model="description" rows="2" maxlength="2000" class="field-input resize-none"
                  placeholder="What's this template for?" />
      </label>

      <fieldset class="flex flex-col gap-2">
        <span class="field-label">Visibility</span>
        <label class="flex items-start gap-2.5 rounded-lg border border-line p-2.5"
               :class="visibility === 'workspace' ? 'border-line-strong bg-surface-2' : ''">
          <input v-model="visibility" type="radio" value="workspace" class="mt-0.5">
          <span class="min-w-0">
            <span class="block text-sm font-medium text-ink">Workspace</span>
            <span class="block text-xs text-ink-subtle">Only members of this workspace can use it.</span>
          </span>
        </label>
        <label
          class="flex items-start gap-2.5 rounded-lg border border-line p-2.5"
          :class="[
            visibility === 'public' ? 'border-line-strong bg-surface-2' : '',
            !canPublish ? 'cursor-not-allowed opacity-50' : '',
          ]"
        >
          <input v-model="visibility" type="radio" value="public" :disabled="!canPublish" class="mt-0.5">
          <span class="min-w-0">
            <span class="block text-sm font-medium text-ink">Public gallery</span>
            <span class="block text-xs text-ink-subtle">
              {{ canPublish ? 'Anyone can discover and use it.' : 'Requires admin or owner role.' }}
            </span>
          </span>
        </label>
      </fieldset>

      <div class="flex justify-end gap-2 pt-2">
        <UiButton variant="ghost" type="button" @click="close">Cancel</UiButton>
        <UiButton variant="primary" type="submit" :loading="save.isPending.value"
                  :disabled="!name.trim()">
          Save template
        </UiButton>
      </div>
    </form>
  </UiModal>
</template>
