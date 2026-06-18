<script setup lang="ts">
import { useMutation } from '@tanstack/vue-query'
import { computed, ref, watch } from 'vue'

const { open, target, close } = useSaveTemplate()
const { capture } = useTemplates()
const { current: currentWorkspace } = useWorkspace()
const { success, error } = useToast()

const name = ref('')
const description = ref('')
const visibility = ref<'workspace' | 'public'>('workspace')

// Public publishing requires workspace:manage (owner/admin) — mirrors the backend.
const canPublish = computed(
  () => currentWorkspace.value?.role === 'owner' || currentWorkspace.value?.role === 'admin',
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

const workspaceLabel = computed(() =>
  (currentWorkspace?.value?.name ?? 'Workspace').slice(0, 3).toUpperCase()
)
</script>

<template>
  <UiModal
    :open="open"
    no-header
    width="max-w-xl"
    @close="close"
  >
    <form v-if="target" class="flex flex-col" @submit.prevent="save.mutate()">
      <!-- ── Linear-style breadcrumb header ── -->
      <div class="flex shrink-0 items-center justify-between border-b border-line px-5 py-3">
        <div class="flex items-center gap-2 text-[0.8125rem]">
          <span
            class="inline-grid size-5 shrink-0 place-items-center rounded bg-accent text-[10px] font-bold text-accent-fg"
          >
            {{ workspaceLabel }}
          </span>
          <span class="text-ink-muted">{{ currentWorkspace?.name ?? 'Workspace' }}</span>
          <UiIcon name="chevron" :size="13" class="text-ink-subtle" />
          <span class="font-medium text-ink">Save as template</span>
        </div>
        <button
          type="button"
          class="icon-btn"
          aria-label="Close"
          @click="close"
        >
          <UiIcon name="x" :size="16" />
        </button>
      </div>

      <!-- ── Body ── -->
      <div class="flex-1 overflow-y-auto overscroll-contain">
        <div class="px-6 pt-6 pb-2 space-y-4">
          <!-- Template Name Inline -->
          <div class="space-y-1.5">
            <input
              v-model="name"
              type="text"
              required
              maxlength="200"
              placeholder="Template name"
              class="w-full bg-transparent text-[1.25rem] font-semibold tracking-tight text-ink placeholder:text-ink-subtle outline-none"
              autofocus
            />
            <p class="text-xs text-ink-subtle">Capture this {{ target.kind }} for reuse</p>
          </div>

          <!-- Description -->
          <div class="space-y-1.5">
            <span class="field-label block uppercase tracking-wider text-[10px] font-semibold">Description</span>
            <textarea
              v-model="description"
              rows="2"
              maxlength="2000"
              placeholder="What's this template for?"
              class="w-full bg-transparent text-sm leading-relaxed text-ink placeholder:text-ink-subtle outline-none resize-none"
            />
          </div>

          <!-- Visibility fieldset -->
          <div class="space-y-2">
            <span class="field-label block uppercase tracking-wider text-[10px] font-semibold">Visibility</span>
            <div class="grid grid-cols-1 gap-2.5">
              <label
                class="flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition"
                :class="visibility === 'workspace' ? 'border-accent bg-accent-soft/20' : 'border-line hover:border-line-strong hover:bg-surface-2'"
              >
                <input
                  v-model="visibility"
                  type="radio"
                  value="workspace"
                  class="mt-1 accent-accent"
                />
                <div class="min-w-0 flex-1">
                  <span class="block text-sm font-semibold text-ink">Workspace members only</span>
                  <span class="block text-xs text-ink-subtle mt-0.5">Only members of this workspace can use it.</span>
                </div>
              </label>

              <label
                class="flex items-start gap-3 rounded-lg border p-3 transition"
                :class="[
                  visibility === 'public' ? 'border-accent bg-accent-soft/20' : 'border-line',
                  canPublish ? 'cursor-pointer hover:border-line-strong hover:bg-surface-2' : 'cursor-not-allowed opacity-50',
                ]"
              >
                <input
                  v-model="visibility"
                  type="radio"
                  value="public"
                  :disabled="!canPublish"
                  class="mt-1 accent-accent"
                />
                <div class="min-w-0 flex-1">
                  <span class="block text-sm font-semibold text-ink">Public gallery</span>
                  <span class="block text-xs text-ink-subtle mt-0.5">
                    {{ canPublish ? 'Anyone can discover and use it.' : 'Requires admin or owner role.' }}
                  </span>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Footer ── -->
      <div class="flex shrink-0 items-center justify-end gap-2 border-t border-line px-5 py-3.5">
        <UiButton variant="ghost" type="button" @click="close">Cancel</UiButton>
        <UiButton
          variant="primary"
          type="submit"
          :loading="save.isPending.value"
          :disabled="!name.trim()"
        >
          Save template
        </UiButton>
      </div>
    </form>
  </UiModal>
</template>
