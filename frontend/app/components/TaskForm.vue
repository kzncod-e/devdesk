<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";
import { computed, ref } from "vue";

import type { Task, UserBrief } from "~/types/api";

const props = defineProps<{ task?: Task | null; busy?: boolean }>();
const emit = defineEmits<{
  submit: [
    data: {
      title: string;
      description: string;
      priority: string;
      due_date: string | null;
      assignee_ids: number[];
    },
  ];
  cancel: [];
}>();

const { api } = useAuth();
const { current: currentWorkspace } = useWorkspace();

const title = ref(props.task?.title ?? "");
const description = ref(props.task?.description ?? "");
const priority = ref(props.task?.priority ?? "medium");
const dueDate = ref(props.task?.due_date ?? "");
const assigneeIds = ref<number[]>(props.task?.assignees.map((a) => a.id) ?? []);

const priorities = [
  {
    value: "low",
    label: "Low",
    tone: "gray" as const,
    color: "text-ink-subtle",
  },
  {
    value: "medium",
    label: "Medium",
    tone: "amber" as const,
    color: "text-warning",
  },
  { value: "high", label: "High", tone: "red" as const, color: "text-danger" },
];

const priorityColor = computed(() => {
  const p = priorities.find((x) => x.value === priority.value);
  return p ? p.color : "text-ink-subtle";
});

const { data: users } = useQuery({
  queryKey: ["users"],
  queryFn: () => api<UserBrief[]>("/api/v1/users"),
});

const selectedAssigneesObjects = computed(() => {
  return (users.value ?? []).filter((u) => assigneeIds.value.includes(u.id));
});

function toggleAssignee(id: number) {
  const i = assigneeIds.value.indexOf(id);
  if (i === -1) assigneeIds.value.push(id);
  else assigneeIds.value.splice(i, 1);
}

function submit() {
  emit("submit", {
    title: title.value,
    description: description.value,
    priority: priority.value,
    due_date: dueDate.value || null,
    assignee_ids: assigneeIds.value,
  });
}

const workspaceLabel = computed(() =>
  (currentWorkspace?.value?.name ?? "Workspace").slice(0, 3).toUpperCase(),
);
</script>

<template>
  <form class="flex flex-col" @submit.prevent="submit">
    <!-- ── Linear-style breadcrumb header ── -->
    <div
      class="flex shrink-0 items-center justify-between border-b border-line px-5 py-3"
    >
      <div class="flex items-center gap-2 text-[0.8125rem]">
        <span
          class="inline-grid size-5 shrink-0 place-items-center rounded bg-accent text-[10px] font-bold text-accent-fg"
        >
          {{ workspaceLabel }}
        </span>
        <span class="text-ink-muted">{{
          currentWorkspace?.name ?? "Workspace"
        }}</span>
        <UiIcon name="chevron" :size="13" class="text-ink-subtle" />
        <span class="font-medium text-ink">{{
          task ? "Edit task" : "New task"
        }}</span>
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
      <div class="px-6 pt-6 pb-2">
        <!-- Inline title input -->
        <input
          v-model="title"
          type="text"
          required
          maxlength="200"
          placeholder="Task title"
          class="w-full bg-transparent text-[1.25rem] font-semibold tracking-tight text-ink placeholder:text-ink-subtle outline-none"
          autofocus
        />

        <!-- Inline description textarea -->
        <textarea
          v-model="description"
          placeholder="Add description or notes…"
          class="mt-3 min-h-[140px] w-full resize-none bg-transparent text-sm leading-relaxed text-ink placeholder:text-ink-subtle outline-none"
          rows="6"
        />

        <!-- Metadata chips row -->
        <div
          class="flex flex-wrap items-center gap-2 pt-4 pb-2 border-t border-line mt-4"
        >
          <!-- Priority pill -->
          <UiMenu align="left">
            <template #trigger>
              <button
                type="button"
                class="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink-muted transition hover:border-line-strong hover:bg-surface-2"
              >
                <UiIcon name="flag" :size="11" :class="priorityColor" />
                <span class="capitalize">Priority: {{ priority }}</span>
              </button>
            </template>
            <UiMenuItem
              v-for="p in priorities"
              :key="p.value"
              @click="priority = p.value as any"
            >
              <div class="flex items-center gap-2">
                <UiIcon name="flag" :size="11" :class="p.color" />
                <span class="capitalize text-xs font-medium text-ink">{{
                  p.label
                }}</span>
              </div>
            </UiMenuItem>
          </UiMenu>

          <!-- Assignees pill -->
          <UiMenu v-if="(users ?? []).length" align="left">
            <template #trigger>
              <button
                type="button"
                class="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1 text-xs font-medium text-ink-muted transition hover:border-line-strong hover:bg-surface-2"
              >
                <UiIcon name="user" :size="11" />
                <span>Assignee</span>
                <span v-if="assigneeIds.length" class="text-ink-subtle"
                  >({{ assigneeIds.length }})</span
                >
              </button>
            </template>
            <UiMenuItem
              v-for="u in users"
              :key="u.id"
              @click="toggleAssignee(u.id)"
            >
              <div class="flex items-center justify-between gap-3 w-full">
                <div class="flex items-center gap-2">
                  <UiAvatar :user="u" :size="18" />
                  <span class="text-xs font-medium text-ink">{{ u.name }}</span>
                </div>
                <UiIcon
                  v-if="assigneeIds.includes(u.id)"
                  name="check"
                  :size="11"
                  class="text-accent"
                />
              </div>
            </UiMenuItem>
          </UiMenu>

          <!-- Selected Assignees Avatars -->
          <div
            v-if="assigneeIds.length"
            class="flex items-center -space-x-1 mr-1"
          >
            <UiAvatar
              v-for="u in selectedAssigneesObjects"
              :key="u.id"
              :user="u"
              :size="18"
              class="ring-1 ring-surface"
              title="Assigned"
            />
          </div>

          <!-- Due Date pill -->
          <div class="relative flex items-center">
            <UiIcon
              name="calendar"
              :size="11"
              class="pointer-events-none absolute left-2.5 text-ink-subtle"
            />
            <input
              v-model="dueDate"
              type="date"
              class="rounded-full border border-line bg-surface pl-7 pr-2.5 py-0.5 text-xs font-medium text-ink-muted transition hover:border-line-strong focus:outline-none focus:ring-1 focus:ring-[var(--accent-ring)]"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- ── Footer ── -->
    <div
      class="flex shrink-0 items-center justify-end gap-2 border-t border-line px-5 py-3.5"
    >
      <UiButton variant="ghost" type="button" @click="emit('cancel')"
        >Cancel</UiButton
      >
      <UiButton
        variant="primary"
        type="submit"
        :loading="busy"
        :disabled="!title.trim()"
      >
        {{ task ? "Save changes" : "Create task" }}
      </UiButton>
    </div>
  </form>
</template>
