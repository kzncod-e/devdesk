import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Notification, NotificationPage } from '~/types/api'

export function useNotifications() {
  const { api } = useAuth()
  const queryClient = useQueryClient()

  const { data: unreadData, refetch: refetchUnread } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => api<{ count: number }>('/api/v1/notifications/unread-count'),
    refetchInterval: 60_000,
  })

  const unreadCount = computed(() => unreadData.value?.count ?? 0)

  async function load(): Promise<Notification[]> {
    const result = await api<NotificationPage>('/api/v1/notifications?limit=20')
    return result.items
  }

  const markRead = useMutation({
    mutationFn: (ids: number[]) =>
      api<{ updated: number }>('/api/v1/notifications/read', {
        method: 'POST',
        body: { ids },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const markAllRead = useMutation({
    mutationFn: () =>
      api<{ updated: number }>('/api/v1/notifications/read', {
        method: 'POST',
        body: { all: true },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }

  return {
    unreadCount,
    load,
    refetchUnread,
    markRead,
    markAllRead,
    invalidate,
  }
}

export function notificationLabel(n: Notification): string {
  const p = n.payload
  switch (n.type) {
    case 'task.assigned':
      return `${p.actor_name ?? 'Someone'} assigned you to "${p.task_title ?? 'a task'}"`
    case 'workspace.invite':
      return `${p.actor_name ?? 'Someone'} invited you to ${p.workspace_name ?? 'a workspace'}`
    case 'member.role_changed':
      return `Your role in ${p.workspace_name ?? 'a workspace'} changed to ${p.new_role ?? 'member'}`
    default:
      return 'New notification'
  }
}

export function notificationLink(n: Notification): string | null {
  switch (n.type) {
    case 'task.assigned': {
      const projectId = n.payload.project_id
      return typeof projectId === 'number' ? `/app/projects/${projectId}` : null
    }
    case 'workspace.invite':
      return '/app/settings'
    default:
      return null
  }
}

export function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
