<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { useConfirm } from "~/composables/useConfirm";
import { useToast } from "~/composables/useToast";

import type { Collection, Project, SavedFilter, Snippet } from "~/types/api";

definePageMeta({ middleware: "auth", layout: "app" });

const { api } = useAuth();
const queryClient = useQueryClient();
const { confirm } = useConfirm();
const { success, error } = useToast();
const saveTemplate = useSaveTemplate();
const { workspaceId } = useWorkspace();
const collectionsApi = useCollections();
const savedFiltersApi = useSavedFilters();
const { colorMap: tagColors } = useTags();

const languageFilter = ref("");
const tagFilter = ref("");
const projectFilter = ref<number | null>(null);
const collectionFilter = ref<number | null>(null);

const filters = computed(() => {
  const params = new URLSearchParams();
  if (languageFilter.value) params.set("language", languageFilter.value);
  if (tagFilter.value) params.set("tag", tagFilter.value);
  if (projectFilter.value !== null) params.set("project_id", String(projectFilter.value));
  if (collectionFilter.value !== null) params.set("collection_id", String(collectionFilter.value));
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

// ── Collections ─────────────────────────────────────────────────────────────
const collectionsKey = computed(() => ["collections", "snippet", workspaceId.value]);
const { data: collections } = useQuery({
  queryKey: collectionsKey,
  queryFn: () => collectionsApi.list("snippet"),
  enabled: computed(() => workspaceId.value != null),
});

const newFolder = ref("");
const creatingFolder = ref(false);
async function createFolder() {
  const name = newFolder.value.trim();
  if (!name) return;
  creatingFolder.value = true;
  try {
    await collectionsApi.create({ name, kind: "snippet" });
    queryClient.invalidateQueries({ queryKey: collectionsKey.value });
    newFolder.value = "";
    success("Folder created");
  } catch {
    error("Could not create folder");
  } finally {
    creatingFolder.value = false;
  }
}

async function deleteFolder(c: Collection) {
  const ok = await confirm({
    title: `Delete “${c.name}”?`,
    message: "Snippets inside are kept, just uncategorized.",
    confirmLabel: "Delete folder",
    danger: true,
  });
  if (!ok) return;
  try {
    await collectionsApi.remove(c.id);
    if (collectionFilter.value === c.id) collectionFilter.value = null;
    queryClient.invalidateQueries({ queryKey: collectionsKey.value });
    success("Folder deleted");
  } catch {
    error("Could not delete folder");
  }
}

// ── Saved filters ────────────────────────────────────────────────────────────
const savedKey = computed(() => ["saved-filters", "snippet", workspaceId.value]);
const { data: savedFilters } = useQuery({
  queryKey: savedKey,
  queryFn: () => savedFiltersApi.list("snippet"),
  enabled: computed(() => workspaceId.value != null),
});

const hasFilters = computed(
  () =>
    !!languageFilter.value || !!tagFilter.value ||
    projectFilter.value !== null || collectionFilter.value !== null,
);

function clearFilters() {
  languageFilter.value = "";
  tagFilter.value = "";
  projectFilter.value = null;
  collectionFilter.value = null;
}

function applySavedFilter(f: SavedFilter) {
  const q = f.query as Record<string, unknown>;
  languageFilter.value = (q.language as string) ?? "";
  tagFilter.value = (q.tag as string) ?? "";
  projectFilter.value = (q.project_id as number | null) ?? null;
  collectionFilter.value = (q.collection_id as number | null) ?? null;
}

const showSaveView = ref(false);
const viewName = ref("");
const savingView = ref(false);
async function saveCurrentView() {
  const name = viewName.value.trim();
  if (!name) return;
  savingView.value = true;
  try {
    await savedFiltersApi.create({
      name,
      kind: "snippet",
      query: {
        language: languageFilter.value || undefined,
        tag: tagFilter.value || undefined,
        project_id: projectFilter.value,
        collection_id: collectionFilter.value,
      },
    });
    queryClient.invalidateQueries({ queryKey: savedKey.value });
    showSaveView.value = false;
    viewName.value = "";
    success("View saved");
  } catch {
    error("Could not save view");
  } finally {
    savingView.value = false;
  }
}

async function deleteSavedFilter(f: SavedFilter) {
  try {
    await savedFiltersApi.remove(f.id);
    queryClient.invalidateQueries({ queryKey: savedKey.value });
  } catch {
    error("Could not delete view");
  }
}

// ── Snippet CRUD ─────────────────────────────────────────────────────────────
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
      ? api<Snippet>(`/api/v1/snippets/${editing.value.id}`, { method: "PATCH", body: data })
      : api<Snippet>("/api/v1/snippets", { method: "POST", body: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["snippets"] });
    queryClient.invalidateQueries({ queryKey: ["tags"] });
    success(editing.value ? "Snippet updated" : "Snippet saved");
    closeForm();
  },
  onError: () => error("Could not save snippet"),
});

const deleteSnippet = useMutation({
  mutationFn: (s: Snippet) => api(`/api/v1/snippets/${s.id}`, { method: "DELETE" }),
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
  <div class="mx-auto max-w-6xl px-5 py-8 md:px-8">
    <header class="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-ink">Snippets</h1>
        <p class="mt-1 text-sm text-ink-muted">Your personal code library.</p>
      </div>
      <UiButton variant="primary" icon="plus" @click="openCreate">New snippet</UiButton>
    </header>

    <div class="flex flex-col gap-6 lg:flex-row lg:items-start">
      <!-- ── Collections rail ──────────────────────────────────────────── -->
      <aside class="w-full lg:w-56 lg:shrink-0">
        <div class="rounded-card border border-line bg-surface p-3">
          <p class="px-1 pb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-subtle">
            Folders
          </p>
          <button
            :class="[
              'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition',
              collectionFilter === null ? 'bg-accent-soft text-accent' : 'text-ink-muted hover:bg-surface-2 hover:text-ink',
            ]"
            @click="collectionFilter = null"
          >
            <UiIcon name="layers" :size="15" /> All snippets
          </button>
          <button
            v-for="c in collections ?? []"
            :key="c.id"
            :class="[
              'group flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition',
              collectionFilter === c.id ? 'bg-accent-soft text-accent' : 'text-ink-muted hover:bg-surface-2 hover:text-ink',
            ]"
            @click="collectionFilter = c.id"
          >
            <UiIcon name="folder" :size="15" />
            <span class="min-w-0 flex-1 truncate">{{ c.name }}</span>
            <button
              type="button"
              class="opacity-0 transition group-hover:opacity-100"
              :aria-label="`Delete ${c.name}`"
              @click.stop="deleteFolder(c)"
            >
              <UiIcon name="trash" :size="13" class="text-ink-subtle hover:text-red-500" />
            </button>
          </button>

          <form class="mt-2 flex gap-1.5 border-t border-line pt-2" @submit.prevent="createFolder">
            <input
              v-model="newFolder"
              type="text"
              maxlength="120"
              placeholder="New folder…"
              class="field-input h-8 flex-1 text-xs"
            >
            <UiIconButton icon="plus" label="Create folder" size="sm" :disabled="creatingFolder || !newFolder.trim()" @click="createFolder" />
          </form>
        </div>
      </aside>

      <!-- ── Main column ───────────────────────────────────────────────── -->
      <div class="min-w-0 flex-1">
        <div class="mb-5 flex flex-wrap items-center gap-3">
          <div class="relative">
            <UiIcon name="code" :size="15" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle" />
            <input v-model="languageFilter" type="text" placeholder="Language…" class="field-input w-36 pl-9">
          </div>
          <div class="relative">
            <UiIcon name="tag" :size="15" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle" />
            <input v-model="tagFilter" type="text" placeholder="Tag…" class="field-input w-36 pl-9">
          </div>
          <select v-model="projectFilter" class="field-input w-44">
            <option :value="null">All projects</option>
            <option v-for="p in projects ?? []" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>

          <!-- Saved views -->
          <UiMenu align="right">
            <template #trigger>
              <UiButton variant="ghost" size="sm" icon="bookmark">Views</UiButton>
            </template>
            <p class="px-2.5 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-ink-subtle">
              Saved views
            </p>
            <p v-if="!savedFilters?.length" class="px-2.5 py-1.5 text-xs text-ink-subtle">
              No saved views yet.
            </p>
            <div
              v-for="f in savedFilters ?? []"
              :key="f.id"
              class="flex items-center gap-1 px-1"
            >
              <UiMenuItem icon="search" class="flex-1" @click="applySavedFilter(f)">{{ f.name }}</UiMenuItem>
              <button type="button" class="px-1.5 text-ink-subtle hover:text-red-500" :aria-label="`Delete ${f.name}`" @click="deleteSavedFilter(f)">
                <UiIcon name="trash" :size="13" />
              </button>
            </div>
            <div class="my-1 h-px bg-line" />
            <UiMenuItem icon="plus" :disabled="!hasFilters" @click="showSaveView = true">Save current view…</UiMenuItem>
          </UiMenu>

          <UiButton v-if="hasFilters" variant="ghost" size="sm" icon="x" @click="clearFilters">Clear</UiButton>
        </div>

        <div v-if="isPending" class="flex flex-col gap-4">
          <div v-for="i in 4" :key="i" class="flex flex-col gap-3 rounded-card border border-line bg-surface p-4">
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
          <UiButton variant="primary" icon="plus" @click="openCreate">Add a snippet</UiButton>
        </UiEmptyState>

        <UiEmptyState
          v-else-if="!snippets?.length"
          icon="search"
          title="No snippets found"
          description="Try clearing your filters."
        />

        <TransitionGroup v-else tag="div" name="fade" class="stagger flex flex-col gap-4">
          <SnippetCard
            v-for="(s, i) in snippets"
            :key="s.id"
            :snippet="s"
            :tag-colors="tagColors"
            :style="{ '--i': i }"
            @edit="startEdit(s)"
            @delete="confirmDelete(s)"
            @template="saveTemplate.save({ kind: 'snippet', sourceId: s.id, sourceName: s.title })"
          />
        </TransitionGroup>
      </div>
    </div>

    <UiModal
      :open="showForm"
      no-header
      width="max-w-2xl"
      @close="closeForm"
    >
      <SnippetForm
        v-if="showForm"
        :key="editing?.id ?? 'new'"
        :snippet="editing"
        :projects="projects ?? []"
        :collections="collections ?? []"
        :busy="saveSnippet.isPending.value"
        @submit="saveSnippet.mutate($event)"
        @cancel="closeForm"
      />
    </UiModal>

    <UiModal
      :open="showSaveView"
      no-header
      width="max-w-md"
      @close="showSaveView = false"
    >
      <form class="flex flex-col" @submit.prevent="saveCurrentView">
        <!-- Breadcrumb / Header -->
        <div class="flex shrink-0 items-center justify-between border-b border-line px-5 py-3">
          <div class="flex items-center gap-2 text-[0.8125rem]">
            <span class="font-medium text-ink">Save view</span>
          </div>
          <button
            type="button"
            class="icon-btn"
            aria-label="Close"
            @click="showSaveView = false"
          >
            <UiIcon name="x" :size="16" />
          </button>
        </div>
        <div class="p-5">
          <label class="flex flex-col gap-1.5">
            <span class="field-label">View name</span>
            <input v-model="viewName" type="text" required maxlength="120" placeholder="e.g. Python · infra" class="field-input">
          </label>
        </div>
        <div class="flex shrink-0 items-center justify-end gap-2 border-t border-line px-5 py-3.5">
          <UiButton variant="ghost" type="button" @click="showSaveView = false">Cancel</UiButton>
          <UiButton variant="primary" type="submit" :loading="savingView" :disabled="!viewName.trim()">
            Save view
          </UiButton>
        </div>
      </form>
    </UiModal>
  </div>
</template>
