<script setup lang="ts">
import type { Notification } from '~/types/api'
import {
  notificationLabel,
  notificationLink,
  timeAgo,
  useNotifications,
} from '~/composables/useNotifications'

const emit = defineEmits<{ close: [] }>()

const { load, markRead, markAllRead } = useNotifications()
const items = ref<Notification[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    items.value = await load()
  } finally {
    loading.value = false
  }
})

async function onOpen(n: Notification) {
  if (!n.read_at) {
    await markRead.mutateAsync([n.id])
    n.read_at = new Date().toISOString()
  }
  const href = notificationLink(n)
  if (href) {
    emit('close')
    navigateTo(href)
  }
}

async function onMarkAll() {
  await markAllRead.mutateAsync()
  items.value = items.value.map((n) => ({ ...n, read_at: n.read_at ?? new Date().toISOString() }))
}
</script>

<template>
  <div class="w-80 sm:w-96">
    <div class="flex items-center justify-between border-b border-line px-3 py-2.5">
      <p class="text-sm font-semibold text-ink">Notifications</p>
      <button
        v-if="items.some((n) => !n.read_at)"
        type="button"
        class="text-xs font-medium text-accent transition hover:opacity-80"
        @click="onMarkAll"
      >
        Mark all read
      </button>
    </div>

    <div v-if="loading" class="space-y-2 p-3">
      <UiSkeleton class="h-12 w-full rounded-lg" />
      <UiSkeleton class="h-12 w-full rounded-lg" />
    </div>

    <UiEmptyState
      v-else-if="items.length === 0"
      icon="bell"
      title="All caught up"
      description="New assignments and invites will show up here."
      class="py-8"
    />

    <ul v-else class="max-h-80 overflow-y-auto py-1">
      <li v-for="n in items" :key="n.id">
        <button
          type="button"
          class="flex w-full gap-3 px-3 py-2.5 text-left transition hover:bg-surface-2"
          :class="!n.read_at ? 'bg-accent-soft/40' : ''"
          @click="onOpen(n)"
        >
          <span
            class="mt-1.5 size-2 shrink-0 rounded-full"
            :class="n.read_at ? 'bg-transparent' : 'bg-accent'"
            aria-hidden="true"
          />
          <span class="min-w-0 flex-1">
            <span class="block text-sm text-ink">{{ notificationLabel(n) }}</span>
            <span class="mt-0.5 block text-xs text-ink-subtle">{{ timeAgo(n.created_at) }}</span>
          </span>
        </button>
      </li>
    </ul>
  </div>
</template>
