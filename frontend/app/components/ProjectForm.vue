<script setup lang="ts">
import type { Project } from '~/types/api'

const props = defineProps<{ project?: Project | null; busy?: boolean }>()
const emit = defineEmits<{
  submit: [data: { name: string; description: string; color: string; image?: File | null }]
  cancel: []
}>()

const { current: currentWorkspace } = useWorkspace()

const name = ref(props.project?.name ?? '')
const summary = ref('')  // short inline summary (not persisted separately, appended to description)
const description = ref(props.project?.description ?? '')
const color = ref(props.project?.color ?? '#71717a')
const imageFile = ref<File | null>(null)
const imagePreview = ref<string | null>(props.project?.image_url ?? null)

// Monochrome-first: project markers are neutral grayscale, not brand colors.
const swatches = [
  '#71717a', '#a1a1aa', '#52525b', '#d4d4d8',
  '#3f3f46', '#737373', '#e4e4e7', '#18181b',
]
const showColorPicker = ref(false)

const statusOptions = ['Backlog', 'Planning', 'Active', 'On Hold', 'Done']
const selectedStatus = ref(props.project ? 'Active' : 'Backlog')

const fileInput = ref<HTMLInputElement | null>(null)
const fileError = ref('')

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    fileError.value = "That file isn't an image. Choose PNG, JPG or WebP."
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    fileError.value = 'Image must be under 5 MB.'
    return
  }
  fileError.value = ''
  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
}

function clearImage() {
  imageFile.value = null
  imagePreview.value = null
  if (fileInput.value) fileInput.value.value = ''
}

const workspaceLabel = computed(() =>
  (currentWorkspace?.value?.name ?? 'Workspace').slice(0, 3).toUpperCase()
)
</script>

<template>
  <form
    class="flex flex-col"
    @submit.prevent="emit('submit', { name, description, color, image: imageFile })"
  >
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
        <span class="font-medium text-ink">{{ project ? 'Edit project' : 'New project' }}</span>
      </div>
      <button
        type="button"
        class="icon-btn"
        aria-label="Close"
        @click="emit('cancel')"
      >
        <UiIcon name="x" :size="16" />
      </button>
    </div>

    <!-- ── Body ── -->
    <div class="flex-1 overflow-y-auto overscroll-contain">
      <div class="px-6 pt-6 pb-2 space-y-0">
        <!-- Icon + Name + Summary stacked block -->
        <div class="flex items-start gap-3.5">
          <!-- Color / Icon picker button -->
          <div class="relative mt-1 shrink-0">
            <button
              type="button"
              class="grid size-9 place-items-center rounded-lg border border-line bg-surface-2 text-ink-muted transition hover:border-line-strong hover:bg-surface-3"
              :style="{ color }"
              aria-label="Pick project color"
              @click="showColorPicker = !showColorPicker"
            >
              <UiIcon name="folder" :size="18" />
            </button>

          <!-- Color picker dropdown -->
          <Transition name="pop">
            <div v-if="showColorPicker" class="absolute left-0 top-11 z-50">
              <!-- Backdrop to close picker -->
              <div class="fixed inset-0 z-0" @click="showColorPicker = false" />
              <div
                class="relative z-10 flex flex-wrap gap-1.5 rounded-card border border-line bg-surface p-3 shadow-pop"
                style="width: 188px"
              >
                <button
                  v-for="s in swatches"
                  :key="s"
                  type="button"
                  class="size-6 rounded-full ring-2 ring-offset-1 ring-offset-surface transition hover:scale-110"
                  :class="color === s ? 'ring-ink' : 'ring-transparent'"
                  :style="{ backgroundColor: s }"
                  :aria-label="`Color ${s}`"
                  @click="color = s; showColorPicker = false"
                />
                <label class="relative size-6 cursor-pointer overflow-hidden rounded-full border border-line" title="Custom color">
                  <input
                    v-model="color"
                    type="color"
                    class="absolute inset-0 size-full cursor-pointer opacity-0"
                    @change="showColorPicker = false"
                  />
                  <span class="grid size-full place-items-center text-[10px] text-ink-subtle">+</span>
                </label>
              </div>
            </div>
          </Transition>
          </div>

          <!-- Inline name + summary inputs -->
          <div class="min-w-0 flex-1 space-y-1">
            <input
              v-model="name"
              type="text"
              required
              maxlength="200"
              placeholder="Project name"
              class="w-full bg-transparent text-[1.25rem] font-semibold tracking-tight text-ink placeholder:text-ink-subtle outline-none"
              autofocus
            />
            <input
              v-model="summary"
              type="text"
              maxlength="300"
              placeholder="Add a short summary..."
              class="w-full bg-transparent text-sm text-ink-muted placeholder:text-ink-subtle outline-none"
            />
          </div>
        </div>

        <!-- ── Metadata chips row ── -->
        <div class="flex flex-wrap items-center gap-1.5 pt-4 pb-2 border-b border-line">
          <!-- Status chip -->
          <UiMenu align="left">
            <template #trigger>
              <button
                type="button"
                class="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-0.5 text-xs font-medium text-ink-muted transition hover:border-line-strong hover:bg-surface-2"
              >
                <span class="size-1.5 rounded-full bg-slate-400" />
                {{ selectedStatus }}
              </button>
            </template>
            <UiMenuItem
              v-for="s in statusOptions"
              :key="s"
              @click="selectedStatus = s"
            >
              {{ s }}
            </UiMenuItem>
          </UiMenu>

          <!-- Color chip -->
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-0.5 text-xs font-medium text-ink-muted transition hover:border-line-strong hover:bg-surface-2"
            @click="showColorPicker = !showColorPicker"
          >
            <span
              class="size-1.5 rounded-full transition"
              :style="{ backgroundColor: color }"
            />
            Color
          </button>

          <!-- Cover image chip -->
          <label
            class="flex cursor-pointer items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-0.5 text-xs font-medium text-ink-muted transition hover:border-line-strong hover:bg-surface-2"
          >
            <UiIcon name="image" :size="11" />
            {{ imagePreview ? 'Change cover' : 'Cover' }}
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="sr-only"
              @change="onFileChange"
            />
          </label>

          <button
            v-if="imagePreview"
            type="button"
            class="flex items-center gap-1 rounded-full border border-danger/30 bg-danger-soft px-2.5 py-0.5 text-xs font-medium text-danger transition"
            @click="clearImage"
          >
            <UiIcon name="x" :size="10" />
            Remove
          </button>
        </div>

        <p v-if="fileError" role="alert" class="pt-2 text-xs text-danger">{{ fileError }}</p>

        <!-- Cover image preview -->
        <div v-if="imagePreview" class="relative mt-3 overflow-hidden rounded-card border border-line">
          <img :src="imagePreview" alt="Cover" class="h-28 w-full object-cover" />
          <button
            type="button"
            class="absolute right-2 top-2 grid size-6 place-items-center rounded-full bg-black/50 text-white transition hover:bg-black/70"
            aria-label="Remove image"
            @click="clearImage"
          >
            <UiIcon name="x" :size="12" />
          </button>
        </div>

        <!-- ── Description (document feel) ── -->
        <textarea
          v-model="description"
          placeholder="Write a description, a project brief, or collect ideas..."
          class="mt-4 min-h-[120px] w-full resize-none bg-transparent text-sm leading-relaxed text-ink placeholder:text-ink-subtle outline-none"
          rows="6"
        />
      </div>
    </div>

    <!-- ── Footer ── -->
    <div class="flex shrink-0 items-center justify-end gap-2 border-t border-line px-5 py-3.5">
      <UiButton variant="ghost" type="button" @click="emit('cancel')">Cancel</UiButton>
      <UiButton
        variant="primary"
        type="submit"
        :loading="busy"
        :disabled="!name.trim()"
      >
        {{ project ? 'Save changes' : 'Create project' }}
      </UiButton>
    </div>
  </form>
</template>
