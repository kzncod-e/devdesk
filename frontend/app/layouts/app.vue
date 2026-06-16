<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";

import { useAppReady } from "~/composables/useAppReady";
import { useCommandPalette } from "~/composables/useCommandPalette";
import { useTheme } from "~/composables/useTheme";
import type { Project } from "~/types/api";

const { user, api, logout } = useAuth();
const { mode, toggle: toggleTheme } = useTheme();
const { show: showPalette } = useCommandPalette();
const { isReady, hasOnboarded, markReady } = useAppReady();
const { success, error: toastError } = useToast();
const {
  unreadCount,
  refetchUnread,
} = useNotifications();
const {
  workspaces,
  workspaceId,
  current: currentWorkspace,
  load: loadWorkspaces,
  setCurrent: setWorkspace,
  createWorkspace,
} = useWorkspace();

// Load workspaces + poll unread notifications on entry (CSR-only shell).
onMounted(() => {
  loadWorkspaces().catch(() => {});
  refetchUnread().catch(() => {});
});

// New-workspace modal
const showCreateWorkspace = ref(false);
const newWorkspaceName = ref("");
const creatingWorkspace = ref(false);
async function onCreateWorkspace() {
  if (!newWorkspaceName.value.trim()) return;
  creatingWorkspace.value = true;
  try {
    await createWorkspace(newWorkspaceName.value.trim());
    success("Workspace created");
    showCreateWorkspace.value = false;
    newWorkspaceName.value = "";
    navigateTo("/app");
  } catch {
    toastError("Could not create workspace");
  } finally {
    creatingWorkspace.value = false;
  }
}

const showSplash = ref(!hasOnboarded.value);

onMounted(() => {
  if (showSplash.value) {
    const MIN_MS = 1200;
    const start = Date.now();
    const done = () => {
      const elapsed = Date.now() - start;
      const remaining = Math.max(0, MIN_MS - elapsed);
      setTimeout(() => {
        showSplash.value = false;
        markReady();
      }, remaining);
    };
    // mark ready once user data is present or after a short timeout
    if (user.value) {
      done();
    } else {
      const stop = watch(user, (u) => {
        if (u) {
          stop();
          done();
        }
      });
      setTimeout(() => {
        stop();
        showSplash.value = false;
        markReady();
      }, 4000);
    }
  } else {
    isReady.value = true;
  }
});

const nav = [
  { to: "/app/snippets", label: "Snippets", icon: "code" },
  { to: "/app/bookmarks", label: "Bookmarks", icon: "bookmark" },
  { to: "/app/settings", label: "Settings", icon: "settings" },
];

const route = useRoute();
function isActive(to: string) {
  return route.path.startsWith(to);
}

// ── Projects sub-nav (expandable, real projects) ───────────────
const { data: projects } = useQuery({
  queryKey: ["projects"],
  queryFn: () => api<Project[]>("/api/v1/projects"),
});

const onProjects = computed(
  () => route.path === "/app" || route.path.startsWith("/app/projects"),
);
const projectsOpen = ref(true);
// Auto-expand whenever the user is anywhere under Projects.
watch(onProjects, (v) => v && (projectsOpen.value = true), { immediate: true });

const activeProjectId = computed(() =>
  route.path.startsWith("/app/projects/")
    ? Number(route.params.id ?? route.path.split("/")[3])
    : null,
);

const initials = computed(() =>
  (user.value?.name ?? "U")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase(),
);
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-canvas text-ink">
    <!-- Sidebar -->
    <aside
      class="hidden w-60 shrink-0 flex-col border-r border-line bg-surface/60 px-3 py-4 md:flex"
    >
      <UiMenu align="left" class="mb-5 block">
        <template #trigger>
          <button
            class="flex w-full items-center gap-2.5 rounded-lg border border-line bg-surface px-2.5 py-2 text-left shadow-sm transition hover:border-line-strong"
            aria-label="Switch workspace"
          >
            <span
              class="grid size-8 shrink-0 place-items-center rounded-lg bg-accent text-accent-fg shadow-sm"
            >
              <UiIcon name="layers" :size="18" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-semibold">{{
                currentWorkspace?.name ?? "DevDesk"
              }}</span>
              <span class="block truncate text-[11px] capitalize text-ink-subtle">{{
                currentWorkspace?.role ?? "workspace"
              }}</span>
            </span>
            <UiIcon name="chevronDown" :size="15" class="shrink-0 text-ink-subtle" />
          </button>
        </template>
        <p
          class="px-2.5 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-ink-subtle"
        >
          Workspaces
        </p>
        <UiMenuItem
          v-for="w in workspaces"
          :key="w.id"
          :icon="w.id === workspaceId ? 'check' : 'folder'"
          @click="setWorkspace(w.id)"
        >
          {{ w.name }}
        </UiMenuItem>
        <div class="my-1 h-px bg-line" />
        <UiMenuItem icon="plus" @click="showCreateWorkspace = true"
          >New workspace</UiMenuItem
        >
        <UiMenuItem icon="users" @click="navigateTo('/app/settings')"
          >Members &amp; settings</UiMenuItem
        >
      </UiMenu>

      <button
        class="mb-4 flex items-center gap-2.5 rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink-subtle shadow-sm transition hover:border-line-strong hover:text-ink-muted"
        @click="showPalette"
      >
        <UiIcon name="search" :size="16" />
        <span class="flex-1 text-left">Search…</span>
        <kbd
          class="rounded border border-line bg-surface-2 px-1.5 py-0.5 text-[10px] font-medium"
          >⌘K</kbd
        >
      </button>

      <p class="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-wider text-ink-subtle">
        Workspace
      </p>
      <nav class="flex flex-col gap-0.5">
        <!-- Projects: expandable section -->
        <div>
          <div
            :class="[
              'group flex items-center gap-2.5 rounded-lg pl-3 pr-1.5 text-sm font-medium transition-colors',
              onProjects ? 'bg-accent-soft text-accent' : 'text-ink-muted hover:bg-surface-2 hover:text-ink',
            ]"
          >
            <NuxtLink to="/app" class="flex flex-1 items-center gap-2.5 py-2">
              <UiIcon
                name="folder"
                :size="18"
                :class="onProjects ? 'text-accent' : 'text-ink-subtle group-hover:text-ink-muted'"
              />
              Projects
            </NuxtLink>
            <button
              type="button"
              class="grid size-6 place-items-center rounded-md text-ink-subtle transition hover:bg-surface-3"
              :aria-label="projectsOpen ? 'Collapse projects' : 'Expand projects'"
              @click="projectsOpen = !projectsOpen"
            >
              <UiIcon name="chevronDown" :size="15" :class="['transition-transform', projectsOpen ? '' : '-rotate-90']" />
            </button>
          </div>

          <div v-if="projectsOpen" class="mt-1 ml-4.5 flex flex-col">
            <NuxtLink
              v-for="p in projects ?? []"
              :key="p.id"
              :to="`/app/projects/${p.id}`"
              :class="[
                'group/proj relative flex items-center gap-2 rounded-md py-1.5 pl-5 pr-2.5 text-sm transition-colors',
                // vertical trunk: full height, but the last row only draws to its centre (clean tree end)
                'before:absolute before:left-0 before:top-0 before:w-px before:bg-line before:h-full last:before:h-1/2',
                // horizontal elbow tick into the row
                'after:absolute after:left-0 after:top-1/2 after:h-px after:w-3 after:-translate-y-1/2 after:bg-line',
                activeProjectId === p.id ? 'bg-surface-2 font-medium text-ink' : 'text-ink-muted hover:bg-surface-2 hover:text-ink',
              ]"
            >
              <span
                class="size-2 shrink-0 rounded-full ring-2 ring-surface transition-transform group-hover/proj:scale-110"
                :style="{ backgroundColor: p.color }"
              />
              <span class="truncate">{{ p.name }}</span>
            </NuxtLink>
            <p
              v-if="!(projects ?? []).length"
              class="relative py-1.5 pl-5 text-xs text-ink-subtle before:absolute before:left-0 before:top-0 before:h-1/2 before:w-px before:bg-line after:absolute after:left-0 after:top-1/2 after:h-px after:w-3 after:bg-line"
            >
              No projects yet
            </p>
          </div>
        </div>

        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          :class="[
            'group flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
            isActive(item.to)
              ? 'bg-accent-soft text-accent'
              : 'text-ink-muted hover:bg-surface-2 hover:text-ink',
          ]"
        >
          <UiIcon
            :name="item.icon"
            :size="18"
            :class="isActive(item.to) ? 'text-accent' : 'text-ink-subtle group-hover:text-ink-muted'"
          />
          {{ item.label }}
        </NuxtLink>
      </nav>

      <div class="mt-auto flex items-center gap-2 border-t border-line pt-3">
        <span
          class="grid size-8 shrink-0 place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent"
        >
          {{ initials }}
        </span>
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium text-ink">
            {{ user?.name ?? "—" }}
          </p>
          <p class="truncate text-xs text-ink-subtle">{{ user?.email }}</p>
        </div>
        <UiIconButton
          icon="logout"
          label="Log out"
          size="sm"
          @click="logout()"
        />
      </div>
    </aside>

    <!-- Main column -->
    <div class="flex min-w-0 flex-1 flex-col">
      <!-- Top bar -->
      <header
        class="flex h-14 shrink-0 items-center gap-3 border-b border-line bg-surface/70 px-4 backdrop-blur md:px-6"
      >
        <NuxtLink to="/app" class="flex items-center gap-2 md:hidden">
          <span
            class="grid size-7 place-items-center rounded-lg bg-accent text-accent-fg"
          >
            <UiIcon name="layers" :size="16" />
          </span>
        </NuxtLink>

        <button
          class="flex flex-1 items-center gap-2.5 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-ink-subtle transition hover:border-line-strong md:max-w-md"
          @click="showPalette"
        >
          <UiIcon name="search" :size="16" />
          <span class="flex-1 text-left">Search everything…</span>
          <kbd
            class="hidden rounded border border-line bg-surface-2 px-1.5 py-0.5 text-[10px] font-medium sm:block"
            >⌘K</kbd
          >
        </button>

        <div class="ml-auto flex items-center gap-1">
          <UiIconButton
            :icon="mode === 'dark' ? 'sun' : 'moon'"
            :label="
              mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
            "
            @click="toggleTheme"
          />
          <UiMenu align="right">
            <template #trigger>
              <span class="relative inline-flex">
                <UiIconButton icon="bell" label="Notifications" />
                <span
                  v-if="unreadCount > 0"
                  class="pointer-events-none absolute right-1 top-1 grid min-w-4 place-items-center rounded-full bg-accent px-1 text-[10px] font-semibold leading-4 text-accent-fg ring-2 ring-surface"
                  aria-hidden="true"
                >
                  {{ unreadCount > 9 ? '9+' : unreadCount }}
                </span>
              </span>
            </template>
            <NotificationPanel @close="() => {}" />
          </UiMenu>
          <UiMenu align="right">
            <template #trigger>
              <button
                class="flex items-center gap-2 rounded-full py-1 pl-1 pr-1.5 transition hover:bg-surface-2 sm:pr-2.5"
                aria-label="Account menu"
              >
                <span
                  class="grid size-8 shrink-0 place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent"
                >
                  {{ initials }}
                </span>
                <span class="hidden max-w-32 truncate text-sm font-medium text-ink sm:block">
                  {{ user?.name ?? "Account" }}
                </span>
                <UiIcon name="chevronDown" :size="15" class="hidden text-ink-subtle sm:block" />
              </button>
            </template>
            <div class="px-2.5 py-2">
              <p class="truncate text-sm font-medium text-ink">
                {{ user?.name }}
              </p>
              <p class="truncate text-xs text-ink-subtle">{{ user?.email }}</p>
              <UiBadge
                v-if="user?.role"
                tone="indigo"
                class="mt-1.5 capitalize"
                >{{ user.role }}</UiBadge
              >
            </div>
            <div class="my-1 h-px bg-line" />
            <UiMenuItem icon="settings" @click="navigateTo('/app/settings')"
              >Settings</UiMenuItem
            >
            <UiMenuItem icon="logout" danger @click="logout()"
              >Log out</UiMenuItem
            >
          </UiMenu>
        </div>
      </header>

      <!-- Mobile nav -->
      <nav
        class="flex shrink-0 gap-1 overflow-x-auto border-b border-line bg-surface/60 px-4 py-2 md:hidden"
      >
        <NuxtLink
          to="/app"
          :class="[
            'flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium',
            onProjects ? 'bg-accent-soft text-accent' : 'text-ink-muted',
          ]"
        >
          <UiIcon name="folder" :size="16" />
          Projects
        </NuxtLink>
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium',
            isActive(item.to) ? 'bg-accent-soft text-accent' : 'text-ink-muted',
          ]"
        >
          <UiIcon :name="item.icon" :size="16" />
          {{ item.label }}
        </NuxtLink>
      </nav>

      <main class="flex-1 overflow-y-auto">
        <slot />
      </main>
    </div>

    <UiModal
      :open="showCreateWorkspace"
      title="New workspace"
      subtitle="Group projects, snippets and bookmarks for a team."
      @close="showCreateWorkspace = false"
    >
      <form class="flex flex-col gap-4" @submit.prevent="onCreateWorkspace">
        <div>
          <label class="field-label" for="ws-name">Name</label>
          <input
            id="ws-name"
            v-model="newWorkspaceName"
            class="field-input mt-1"
            placeholder="Acme Inc"
            maxlength="200"
          />
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <UiButton
            variant="ghost"
            type="button"
            @click="showCreateWorkspace = false"
            >Cancel</UiButton
          >
          <UiButton
            variant="primary"
            type="submit"
            :loading="creatingWorkspace"
            :disabled="!newWorkspaceName.trim()"
            >Create workspace</UiButton
          >
        </div>
      </form>
    </UiModal>

    <CommandPalette />
    <UiToaster />
    <UiConfirm />
    <AppSplash :show="showSplash" />
  </div>
</template>
