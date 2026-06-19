<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Template, TemplateKind } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'app' })

const { list, use, remove } = useTemplates()
const { workspaceId } = useWorkspace()
const { confirm } = useConfirm()
const { success, error } = useToast()
const queryClient = useQueryClient()

const kind = ref<'all' | TemplateKind>('all')

const { data: templates, isPending } = useQuery({
  queryKey: computed(() => ['templates', workspaceId.value]),
  queryFn: () => list(),
  enabled: computed(() => workspaceId.value != null),
})

const visible = computed(() => {
  const all = templates.value ?? []
  return kind.value === 'all' ? all : all.filter((t) => t.kind === kind.value)
})

const useTemplate = useMutation({
  mutationFn: (t: Template) => use(t.id),
  onSuccess: (result) => {
    queryClient.invalidateQueries({ queryKey: ['templates'] })
    queryClient.invalidateQueries({ queryKey: ['projects'] })
    queryClient.invalidateQueries({ queryKey: ['snippets'] })
    success('Template applied')
    navigateTo(useTemplateResultPath(result))
  },
  onError: () => error('Could not use template'),
})

const deleteTemplate = useMutation({
  mutationFn: (t: Template) => remove(t.id),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['templates'] })
    success('Template deleted')
  },
  onError: () => error('Could not delete template'),
})

async function confirmDelete(t: Template) {
  const ok = await confirm({
    title: `Delete “${t.name}”?`,
    message: 'This removes the template. Content created from it is unaffected.',
    confirmLabel: 'Delete',
    danger: true,
  })
  if (ok) deleteTemplate.mutate(t)
}

// Own = belongs to the current workspace (globals/public-of-others aren't deletable).
function isOwn(t: Template) {
  return t.workspace_id != null && t.workspace_id === workspaceId.value
}

const tabs: { value: 'all' | TemplateKind; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'project', label: 'Projects' },
  { value: 'snippet', label: 'Snippets' },
]
</script>

<template>
  <div class="mx-auto max-w-6xl px-5 py-8 md:px-8">
    <header class="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-title">Templates</h1>
        <p class="mt-1 text-sm text-ink-muted">Reusable scaffolds for projects and snippets.</p>
      </div>
      <UiButton variant="ghost" icon="external" @click="navigateTo('/gallery')">Public gallery</UiButton>
    </header>

    <div class="mb-6 flex gap-1 rounded-lg border border-line bg-surface p-1 shadow-sm w-fit">
      <button
        v-for="t in tabs"
        :key="t.value"
        :class="[
          'rounded-md px-3 py-1 text-sm font-medium transition',
          kind === t.value ? 'bg-accent-soft text-accent' : 'text-ink-muted hover:text-ink',
        ]"
        @click="kind = t.value"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- loading -->
    <div v-if="isPending" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <UiSkeleton v-for="i in 6" :key="i" class="h-36 rounded-card" />
    </div>

    <UiEmptyState
      v-else-if="!visible.length"
      icon="layers"
      title="No templates yet"
      description="Save a project or snippet as a template from its menu, or browse the public gallery."
    >
      <UiButton variant="primary" icon="external" @click="navigateTo('/gallery')">Browse gallery</UiButton>
    </UiEmptyState>

    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="t in visible"
        :key="t.id"
        class="flex flex-col gap-3 rounded-card border border-line bg-surface p-5 transition hover:border-line-strong"
      >
        <div class="flex items-start gap-3">
          <span class="grid size-9 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent">
            <UiIcon :name="t.kind === 'project' ? 'folder' : 'code'" :size="18" />
          </span>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-semibold text-ink">{{ t.name }}</p>
            <div class="mt-1 flex items-center gap-1.5">
              <UiBadge :tone="t.kind === 'project' ? 'indigo' : 'gray'" class="capitalize">{{ t.kind }}</UiBadge>
              <UiBadge v-if="t.visibility === 'public'" tone="green">Public</UiBadge>
            </div>
          </div>
          <UiMenu align="right">
            <template #trigger>
              <UiIconButton icon="more" label="Template actions" size="sm" />
            </template>
            <UiMenuItem icon="layers" @click="useTemplate.mutate(t)">Use template</UiMenuItem>
            <UiMenuItem v-if="isOwn(t)" icon="trash" danger @click="confirmDelete(t)">Delete</UiMenuItem>
          </UiMenu>
        </div>

        <p class="line-clamp-2 min-h-8 text-xs text-ink-muted">
          {{ t.description || 'No description.' }}
        </p>

        <div class="mt-auto flex items-center justify-between">
          <span class="text-xs text-ink-subtle">Used {{ t.use_count }}×</span>
          <UiButton
            variant="primary"
            size="sm"
            icon="plus"
            :loading="useTemplate.isPending.value && useTemplate.variables.value?.id === t.id"
            @click="useTemplate.mutate(t)"
          >
            Use
          </UiButton>
        </div>
      </div>
    </div>
  </div>
</template>
