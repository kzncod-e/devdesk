<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { AuditLog, AuditPage, Member, User, WorkspaceRole } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'app' })

const { user, fetchMe, api } = useAuth()
const { workspaceId, current: currentWorkspace } = useWorkspace()
const { confirm } = useConfirm()
const queryClient = useQueryClient()
const { success, error } = useToast()

const isAdmin = computed(() => user.value?.role === 'admin')

// ── Workspace members & invites ───────────────────────────────────
const wsRoles: WorkspaceRole[] = ['admin', 'editor', 'member', 'viewer']
const canManageMembers = computed(
  () => currentWorkspace.value?.role === 'owner' || currentWorkspace.value?.role === 'admin',
)
const membersKey = computed(() => ['members', workspaceId.value])

const { data: members, isPending: loadingMembers } = useQuery({
  queryKey: membersKey,
  queryFn: () => api<Member[]>(`/api/v1/workspaces/${workspaceId.value}/members`),
  enabled: computed(() => !!workspaceId.value),
})

const inviteEmail = ref('')
const inviteRole = ref<WorkspaceRole>('member')
const lastInviteToken = ref<string | null>(null)

const sendInvite = useMutation({
  mutationFn: () =>
    api<{ token: string }>(`/api/v1/workspaces/${workspaceId.value}/invites`, {
      method: 'POST',
      body: { email: inviteEmail.value.trim(), role: inviteRole.value },
    }),
  onSuccess: (res) => {
    lastInviteToken.value = res.token
    inviteEmail.value = ''
    success('Invite created')
  },
  onError: () => error('Could not create invite (check the email and your permissions)'),
})

const changeMemberRole = useMutation({
  mutationFn: ({ userId, role }: { userId: number; role: string }) =>
    api<Member>(`/api/v1/workspaces/${workspaceId.value}/members/${userId}`, {
      method: 'PATCH',
      body: { role },
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: membersKey.value })
    success('Role updated')
  },
  onError: () => error('Could not update role'),
})

async function removeMember(m: Member) {
  const ok = await confirm({
    title: `Remove ${m.name}?`,
    message: 'They will lose access to this workspace.',
    confirmLabel: 'Remove',
    danger: true,
  })
  if (!ok) return
  try {
    await api(`/api/v1/workspaces/${workspaceId.value}/members/${m.user_id}`, { method: 'DELETE' })
    queryClient.invalidateQueries({ queryKey: membersKey.value })
    success('Member removed')
  } catch {
    error('Could not remove member')
  }
}

async function copyInviteToken() {
  if (!lastInviteToken.value) return
  try {
    await navigator.clipboard.writeText(lastInviteToken.value)
    success('Invite token copied')
  } catch {
    error('Copy failed — select the token manually')
  }
}

// ── Profile form ──────────────────────────────────────────────────
const profileName = ref(user.value?.name ?? '')
watch(() => user.value?.name, v => { if (v) profileName.value = v })

const saveProfile = useMutation({
  mutationFn: () => api<User>('/api/v1/auth/me', { method: 'PATCH', body: { name: profileName.value } }),
  onSuccess: async () => {
    await fetchMe()
    success('Profile updated')
  },
  onError: () => error('Could not update profile'),
})

// ── User management (admin only) ──────────────────────────────────
const { data: users, isPending: loadingUsers } = useQuery({
  queryKey: ['admin-users'],
  queryFn: () => api<User[]>('/api/v1/admin/users'),
  enabled: isAdmin,
})

const roleOptions = ['member', 'manager', 'admin'] as const

const setRole = useMutation({
  mutationFn: ({ userId, role }: { userId: number; role: string }) =>
    api<User>(`/api/v1/admin/users/${userId}/role`, { method: 'PATCH', body: { role } }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    success('Role updated')
  },
  onError: () => error('Could not update role'),
})

const roleTone: Record<string, 'indigo' | 'amber' | 'red'> = {
  member: 'indigo',
  manager: 'amber',
  admin: 'red',
}

// ── Audit log (workspace owner / admin only) ──────────────────────
const auditAction = ref('')
const auditCursor = ref<number | null>(null)

const auditQueryKey = computed(() => [
  'workspace-audit', workspaceId.value, auditAction.value,
])

const canViewAudit = computed(
  () => currentWorkspace.value?.role === 'owner' || currentWorkspace.value?.role === 'admin',
)

const { data: auditPage, isPending: loadingAudit } = useQuery({
  queryKey: auditQueryKey,
  queryFn: () => {
    const params = new URLSearchParams({ limit: '50' })
    if (auditAction.value) params.set('action', auditAction.value)
    if (auditCursor.value) params.set('before', String(auditCursor.value))
    return api<AuditPage>(`/api/v1/workspaces/${workspaceId.value}/audit?${params}`)
  },
  enabled: computed(() => !!workspaceId.value && canViewAudit.value),
})

const auditRows = computed(() => auditPage.value?.items ?? [])

const AUDIT_ACTIONS = [
  '', 'workspace.created',
  'project.created', 'project.updated', 'project.deleted',
  'task.created', 'task.updated', 'task.deleted', 'task.status_changed',
  'snippet.created', 'snippet.deleted',
  'bookmark.created', 'bookmark.deleted',
  'member.invited', 'member.joined', 'member.role_changed', 'member.removed',
]

function auditTimeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function auditSummary(row: AuditLog): string {
  return [row.action, row.target_type, row.target_id ? `#${row.target_id}` : '']
    .filter(Boolean).join(' · ')
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-5 py-8 md:px-8">
    <header class="mb-8">
      <h1 class="text-2xl font-semibold tracking-tight text-ink">Settings</h1>
      <p class="mt-1 text-sm text-ink-muted">Manage your profile and workspace.</p>
    </header>

    <!-- Profile section -->
    <section class="mb-8 rounded-xl border border-line bg-surface p-6 shadow-card">
      <h2 class="mb-4 flex items-center gap-2 text-base font-semibold text-ink">
        <span class="grid size-7 place-items-center rounded-lg bg-accent-soft text-accent">
          <UiIcon name="user" :size="15" />
        </span>
        Profile
      </h2>

      <form class="flex flex-col gap-4" @submit.prevent="saveProfile.mutate()">
        <label class="flex flex-col gap-1.5">
          <span class="field-label">Display name</span>
          <input v-model="profileName" type="text" required maxlength="120" autocomplete="name" class="field-input sm:max-w-xs">
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="field-label">Email</span>
          <input :value="user?.email" type="email" disabled class="field-input sm:max-w-xs">
        </label>
        <div class="flex items-center gap-3">
          <UiButton variant="primary" type="submit" :loading="saveProfile.isPending.value" icon="check" size="sm">
            Save profile
          </UiButton>
          <UiBadge :tone="roleTone[user?.role ?? 'member'] ?? 'indigo'" class="capitalize">
            {{ user?.role ?? 'member' }}
          </UiBadge>
        </div>
      </form>
    </section>

    <!-- Workspace members & invites -->
    <section class="mb-8 rounded-xl border border-line bg-surface p-6 shadow-card">
      <h2 class="mb-1 flex items-center gap-2 text-base font-semibold text-ink">
        <span class="grid size-7 place-items-center rounded-lg bg-accent-soft text-accent">
          <UiIcon name="users" :size="15" />
        </span>
        Members
        <span class="ml-auto truncate text-xs font-normal text-ink-subtle">
          {{ currentWorkspace?.name }}
        </span>
      </h2>
      <p class="mb-4 text-sm text-ink-muted">
        People with access to this workspace's projects, snippets and bookmarks.
      </p>

      <!-- Invite form (managers only) -->
      <form
        v-if="canManageMembers"
        class="mb-5 flex flex-wrap items-end gap-2"
        @submit.prevent="sendInvite.mutate()"
      >
        <label class="flex flex-1 flex-col gap-1.5" style="min-width: 12rem">
          <span class="field-label">Invite by email</span>
          <input
            v-model="inviteEmail"
            type="email"
            required
            placeholder="teammate@company.com"
            class="field-input"
          />
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="field-label">Role</span>
          <select v-model="inviteRole" class="field-input w-32 capitalize">
            <option v-for="r in wsRoles" :key="r" :value="r" class="capitalize">{{ r }}</option>
          </select>
        </label>
        <UiButton
          variant="primary"
          type="submit"
          icon="plus"
          :loading="sendInvite.isPending.value"
        >
          Invite
        </UiButton>
      </form>

      <!-- Generated invite token (no email delivery yet) -->
      <div
        v-if="lastInviteToken"
        class="mb-5 rounded-lg border border-accent/30 bg-accent-soft p-3"
      >
        <p class="mb-1.5 text-xs font-medium text-accent">
          Share this invite token — the invitee accepts it after signing up:
        </p>
        <div class="flex items-center gap-2">
          <code
            class="min-w-0 flex-1 truncate rounded bg-surface px-2 py-1.5 font-mono text-xs text-ink"
            >{{ lastInviteToken }}</code
          >
          <UiButton variant="secondary" size="sm" icon="copy" @click="copyInviteToken">
            Copy
          </UiButton>
        </div>
      </div>

      <div v-if="loadingMembers" class="flex flex-col gap-2">
        <div v-for="i in 3" :key="i" class="flex items-center gap-3 py-2">
          <UiSkeleton class="size-9 rounded-full" />
          <div class="flex-1 space-y-1.5">
            <UiSkeleton class="h-4 w-40" />
            <UiSkeleton class="h-3 w-56" />
          </div>
          <UiSkeleton class="h-8 w-28 rounded-lg" />
        </div>
      </div>

      <ul v-else class="flex flex-col divide-y divide-line">
        <li
          v-for="m in members ?? []"
          :key="m.user_id"
          class="flex flex-wrap items-center gap-3 py-3"
        >
          <span class="grid size-9 shrink-0 place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent">
            {{ m.name.split(' ').map((p: string) => p[0]).slice(0, 2).join('').toUpperCase() }}
          </span>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium text-ink">
              {{ m.name }}
              <span v-if="m.user_id === user?.id" class="ml-1.5 text-xs font-normal text-ink-subtle">(you)</span>
            </p>
            <p class="truncate text-xs text-ink-subtle">{{ m.email }}</p>
          </div>

          <template v-if="canManageMembers && m.user_id !== user?.id">
            <select
              :value="m.role"
              :disabled="changeMemberRole.isPending.value"
              :aria-label="`Change role for ${m.name}`"
              class="field-input w-28 py-1.5 text-xs capitalize"
              @change="changeMemberRole.mutate({ userId: m.user_id, role: ($event.target as HTMLSelectElement).value })"
            >
              <option v-for="r in wsRoles" :key="r" :value="r" class="capitalize">{{ r }}</option>
              <option value="owner" class="capitalize">owner</option>
            </select>
            <UiIconButton icon="trash" label="Remove member" size="sm" @click="removeMember(m)" />
          </template>
          <UiBadge v-else tone="indigo" class="capitalize">{{ m.role }}</UiBadge>
        </li>
      </ul>
    </section>

    <!-- Audit log (workspace owner / admin only) -->
    <section v-if="canViewAudit" class="mb-8 rounded-xl border border-line bg-surface p-6 shadow-card">
      <h2 class="mb-1 flex items-center gap-2 text-base font-semibold text-ink">
        <span class="grid size-7 place-items-center rounded-lg bg-accent-soft text-accent">
          <UiIcon name="list" :size="15" />
        </span>
        Audit Log
        <span class="ml-auto rounded-full bg-surface-2 px-2 py-0.5 text-xs font-medium text-ink-muted">Owner / Admin</span>
      </h2>
      <p class="mb-4 text-sm text-ink-muted">
        Immutable record of all workspace actions.
      </p>

      <div class="mb-4 flex flex-wrap items-center gap-3">
        <label class="flex flex-col gap-1">
          <span class="field-label">Filter by action</span>
          <select v-model="auditAction" class="field-input w-56 py-1.5 text-xs">
            <option value="">All actions</option>
            <option v-for="a in AUDIT_ACTIONS.slice(1)" :key="a" :value="a">{{ a }}</option>
          </select>
        </label>
      </div>

      <!-- skeleton -->
      <div v-if="loadingAudit" class="flex flex-col divide-y divide-line">
        <div v-for="i in 5" :key="i" class="flex items-center gap-3 py-3">
          <UiSkeleton class="h-3 w-40" />
          <UiSkeleton class="h-3 w-28" />
          <div class="ml-auto">
            <UiSkeleton class="h-3 w-20" />
          </div>
        </div>
      </div>

      <!-- empty -->
      <p v-else-if="!auditRows.length" class="py-6 text-center text-sm text-ink-subtle">
        No audit events yet.
      </p>

      <!-- table -->
      <div v-else class="overflow-x-auto rounded-lg border border-line">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-line bg-surface-2 text-left text-ink-muted">
              <th class="px-3 py-2 font-medium">Action</th>
              <th class="px-3 py-2 font-medium">Actor</th>
              <th class="px-3 py-2 font-medium">Target</th>
              <th class="px-3 py-2 font-medium">When</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-line">
            <tr
              v-for="row in auditRows"
              :key="row.id"
              class="group hover:bg-surface-2"
            >
              <td class="px-3 py-2 font-mono text-ink">{{ row.action }}</td>
              <td class="px-3 py-2 text-ink-muted">{{ row.actor_name ?? '—' }}</td>
              <td class="px-3 py-2 text-ink-muted">
                <span v-if="row.target_type">
                  {{ row.target_type }}<span v-if="row.target_id" class="ml-1 text-ink-subtle">#{{ row.target_id }}</span>
                </span>
                <span v-else class="text-ink-subtle">—</span>
              </td>
              <td class="px-3 py-2 text-ink-subtle">{{ auditTimeAgo(row.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="auditPage?.next_cursor" class="mt-3 text-center text-xs text-ink-subtle">
        Showing first 50 events. Keyset pagination cursor: {{ auditPage.next_cursor }}
      </p>
    </section>

    <!-- User management (admin only) -->
    <section v-if="isAdmin" class="rounded-xl border border-line bg-surface p-6 shadow-card">
      <h2 class="mb-4 flex items-center gap-2 text-base font-semibold text-ink">
        <span class="grid size-7 place-items-center rounded-lg bg-accent-soft text-accent">
          <UiIcon name="users" :size="15" />
        </span>
        User Management
        <span class="ml-auto rounded-full bg-surface-2 px-2 py-0.5 text-xs font-medium text-ink-muted">Admin</span>
      </h2>

      <div v-if="loadingUsers" class="flex flex-col gap-2">
        <div v-for="i in 4" :key="i" class="flex items-center gap-3 py-2">
          <UiSkeleton class="size-9 rounded-full" />
          <div class="flex-1 space-y-1.5">
            <UiSkeleton class="h-4 w-40" />
            <UiSkeleton class="h-3 w-56" />
          </div>
          <UiSkeleton class="h-8 w-28 rounded-lg" />
        </div>
      </div>

      <UiEmptyState
        v-else-if="!users?.length"
        icon="users"
        title="No users found"
        description="Something went wrong loading the user list."
      />

      <ul v-else class="flex flex-col divide-y divide-line">
        <li
          v-for="u in users"
          :key="u.id"
          class="flex flex-wrap items-center gap-3 py-3"
        >
          <span class="grid size-9 shrink-0 place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent">
            {{ u.name.split(' ').map((p: string) => p[0]).slice(0, 2).join('').toUpperCase() }}
          </span>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium text-ink">
              {{ u.name }}
              <span v-if="u.id === user?.id" class="ml-1.5 text-xs font-normal text-ink-subtle">(you)</span>
            </p>
            <p class="truncate text-xs text-ink-subtle">{{ u.email }}</p>
          </div>
          <select
            :value="u.role"
            :disabled="u.id === user?.id || setRole.isPending.value"
            :aria-label="`Change role for ${u.name}`"
            class="field-input w-32 py-1.5 text-xs"
            @change="setRole.mutate({ userId: u.id, role: ($event.target as HTMLSelectElement).value })"
          >
            <option v-for="r in roleOptions" :key="r" :value="r" class="capitalize">
              {{ r }}
            </option>
          </select>
        </li>
      </ul>
    </section>

    <!-- Non-admin role info -->
    <section v-else class="rounded-xl border border-line bg-surface-2 p-6">
      <div class="flex items-center gap-3 text-ink-muted">
        <span class="grid size-8 place-items-center rounded-lg bg-surface-3 text-ink-subtle">
          <UiIcon name="shield" :size="16" />
        </span>
        <p class="text-sm">
          User management requires <strong class="text-ink">admin</strong> role. Contact your workspace admin to change roles.
        </p>
      </div>
    </section>
  </div>
</template>
