<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { useConfirm } from "~/composables/useConfirm";
import { useToast } from "~/composables/useToast";

import type { Project, Snippet } from "~/types/api";

definePageMeta({ middleware: "auth", layout: "app" });

const { api } = useAuth();
const queryClient = useQueryClient();
const { confirm } = useConfirm();
const { success, error } = useToast();
const saveTemplate = useSaveTemplate();

const languageFilter = ref("");
const tagFilter = ref("");
const projectFilter = ref<number | null>(null);

const filters = computed(() => {
  const params = new URLSearchParams();
  if (languageFilter.value) params.set("language", languageFilter.value);
  if (tagFilter.value) params.set("tag", tagFilter.value);
  if (projectFilter.value !== null)
    params.set("project_id", String(projectFilter.value));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
});

const { data: projects } = useQuery({
  queryKey: ["projects"],
  queryFn: () => api<Project[]>("/api/v1/projects"),
});

const { data: snippets, isPending } = useQuery({
  queryKey: ["snippets", filters],
  queryFn: () => api<Snippet[]>(`/api/v1/snippets${filters.value}`),
});

const hasFilters = computed(
  () =>
    !!languageFilter.value || !!tagFilter.value || projectFilter.value !== null,
);

const showForm = ref(false);
const editing = ref<Snippet | null>(null);

function openCreate() {
  editing.value = null;
  showForm.value = true;
}
function startEdit(s: Snippet) {
  editing.value = s;
  showForm.value = true;
}
function closeForm() {
  showForm.value = false;
  editing.value = null;
}

// Open the create modal when ⌘K requested a new snippet (from any page).
const { intent: quickCreateIntent, consume: consumeQuickCreate } = useQuickCreate();
watch(quickCreateIntent, () => {
  if (consumeQuickCreate("snippet")) openCreate();
}, { immediate: true });

const saveSnippet = useMutation({
  mutationFn: (data: Record<string, unknown>) =>
    editing.value
      ? api<Snippet>(`/api/v1/snippets/${editing.value.id}`, {
          method: "PATCH",
          body: data,
        })
      : api<Snippet>("/api/v1/snippets", { method: "POST", body: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["snippets"] });
    success(editing.value ? "Snippet updated" : "Snippet saved");
    closeForm();
  },
  onError: () => error("Could not save snippet"),
});

const deleteSnippet = useMutation({
  mutationFn: (s: Snippet) =>
    api(`/api/v1/snippets/${s.id}`, { method: "DELETE" }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["snippets"] });
    success("Snippet deleted");
  },
});

async function confirmDelete(s: Snippet) {
  const ok = await confirm({
    title: `Delete “${s.title}”?`,
    message: "This snippet will be permanently removed.",
    confirmLabel: "Delete",
    danger: true,
  });
  if (ok) deleteSnippet.mutate(s);
}
</script>

<template>
  <div class="mx-auto max-w-5xl px-5 py-8 md:px-8">
    <header class="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-ink">Snippets</h1>
        <p class="mt-1 text-sm text-ink-muted">Your personal code library.</p>
      </div>
      <UiButton variant="primary" icon="plus" @click="openCreate"
        >New snippet</UiButton
      >
    </header>

    <div class="mb-6 flex flex-wrap gap-3">
      <div class="relative">
        <UiIcon
          name="code"
          :size="15"
          class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle"
        />
        <input
          v-model="languageFilter"
          type="text"
          placeholder="Language…"
          class="field-input w-40 pl-9"
        />
      </div>
      <div class="relative">
        <UiIcon
          name="tag"
          :size="15"
          class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle"
        />
        <input
          v-model="tagFilter"
          type="text"
          placeholder="Tag…"
          class="field-input w-40 pl-9"
        />
      </div>
      <select v-model="projectFilter" class="field-input w-48">
        <option :value="null">All projects</option>
        <option v-for="p in projects ?? []" :key="p.id" :value="p.id">
          {{ p.name }}
        </option>
      </select>
    </div>

    <div v-if="isPending" class="flex flex-col gap-4">
      <div
        v-for="i in 4"
        :key="i"
        class="flex flex-col gap-3 rounded-card border border-line bg-surface p-4"
      >
        <div class="flex items-center gap-2">
          <UiSkeleton class="size-8 rounded-lg" />
          <UiSkeleton class="h-4 w-40" />
        </div>
        <UiSkeleton class="h-24 w-full rounded-lg" />
      </div>
    </div>

    <UiEmptyState
      v-else-if="!snippets?.length && !hasFilters"
      icon="code"
      title="No snippets yet"
      description="Save reusable code so you never hunt for it again."
    >
      <UiButton variant="primary" icon="plus" @click="openCreate"
        >Add a snippet</UiButton
      >
    </UiEmptyState>

    <UiEmptyState
      v-else-if="!snippets?.length"
      icon="search"
      title="No snippets found"
      description="Try clearing your filters."
    />

    <TransitionGroup
      v-else
      tag="div"
      name="fade"
      class="stagger flex flex-col gap-4"
    >
      <SnippetCard
        v-for="(s, i) in snippets"
        :key="s.id"
        :snippet="s"
        :style="{ '--i': i }"
        @edit="startEdit(s)"
        @delete="confirmDelete(s)"
        @template="saveTemplate.save({ kind: 'snippet', sourceId: s.id, sourceName: s.title })"
      />
    </TransitionGroup>

    <UiModal
      :open="showForm"
      width="max-w-2xl"
      :title="editing ? 'Edit snippet' : 'New snippet'"
      :subtitle="
        editing ? 'Update your saved code.' : 'Save a reusable piece of code.'
      "
      @close="closeForm"
    >
      <SnippetForm
        v-if="showForm"
        :key="editing?.id ?? 'new'"
        :snippet="editing"
        :projects="projects ?? []"
        :busy="saveSnippet.isPending.value"
        @submit="saveSnippet.mutate($event)"
        @cancel="closeForm"
      />
    </UiModal>
  </div>
</template>
