<script setup lang="ts">
import type { Project } from '~/types/api'

const props = defineProps<{ project?: Project | null; busy?: boolean }>()
const emit = defineEmits<{
  submit: [data: { name: string; description: string; color: string; image?: File | null }]
  cancel: []
}>()

const name = ref(props.project?.name ?? '')
const description = ref(props.project?.description ?? '')
const color = ref(props.project?.color ?? '#6366f1')
const imageFile = ref<File | null>(null)
const imagePreview = ref<string | null>(props.project?.image_url ?? null)

const swatches = ['#6366f1', '#8b5cf6', '#ec4899', '#ef4444', '#f59e0b', '#10b981', '#06b6d4', '#3b82f6']

const fileInput = ref<HTMLInputElement | null>(null)

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) return
  if (file.size > 5 * 1024 * 1024) return
  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
}

function clearImage() {
  imageFile.value = null
  imagePreview.value = null
  if (fileInput.value) fileInput.value.value = ''
}
</script>

<template>
  <form class="flex flex-col gap-5" @submit.prevent="emit('submit', { name, description, color, image: imageFile })">
    <div class="flex flex-col gap-1.5">
      <label class="field-label">Name</label>
      <input v-model="name" type="text" required maxlength="200" placeholder="Project name" class="field-input">
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="field-label">Description</label>
      <textarea v-model="description" rows="3" placeholder="What is this project about?" class="field-input resize-none" />
    </div>

    <div class="flex flex-col gap-2">
      <label class="field-label">Color</label>
      <div class="flex flex-wrap items-center gap-2">
        <button
          v-for="s in swatches"
          :key="s"
          type="button"
          class="size-7 rounded-full ring-2 ring-offset-2 ring-offset-surface transition hover:scale-110"
          :class="color === s ? 'ring-ink' : 'ring-transparent'"
          :style="{ backgroundColor: s }"
          :aria-label="`Use color ${s}`"
          @click="color = s"
        />
        <label class="relative size-7 cursor-pointer overflow-hidden rounded-full border border-line">
          <input v-model="color" type="color" class="absolute inset-0 size-full cursor-pointer opacity-0">
          <span class="grid size-full place-items-center text-ink-subtle"><UiIcon name="plus" :size="14" /></span>
        </label>
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <label class="field-label">Cover image <span class="font-normal text-ink-subtle">(optional · PNG, JPG, WebP · max 5 MB)</span></label>
      <div
        v-if="imagePreview"
        class="relative overflow-hidden rounded-lg border border-line"
      >
        <img :src="imagePreview" alt="Preview" class="h-32 w-full object-cover">
        <button
          type="button"
          class="absolute right-2 top-2 grid size-6 place-items-center rounded-full bg-black/50 text-white hover:bg-black/70"
          aria-label="Remove image"
          @click="clearImage"
        >
          <UiIcon name="x" :size="12" />
        </button>
      </div>
      <label
        v-else
        class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-line bg-surface-2 py-6 text-sm text-ink-subtle transition hover:border-line-strong hover:bg-surface-3"
      >
        <UiIcon name="image" :size="20" />
        <span>Click to upload image</span>
        <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif" class="sr-only" @change="onFileChange">
      </label>
    </div>

    <div class="flex justify-end gap-2 pt-4">
      <UiButton variant="ghost" type="button" @click="emit('cancel')">Cancel</UiButton>
      <UiButton variant="primary" type="submit" :loading="busy" icon="check">
        {{ props.project ? 'Save changes' : 'Create project' }}
      </UiButton>
    </div>
  </form>
</template>
