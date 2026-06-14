<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { User } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'app' })

const { user, fetchMe, api } = useAuth()
const queryClient = useQueryClient()
const { success, error } = useToast()

const isAdmin = computed(() => user.value?.role === 'admin')

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
