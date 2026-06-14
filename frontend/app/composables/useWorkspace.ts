import { useQueryClient } from '@tanstack/vue-query'

import type { Workspace } from '~/types/api'

const STORAGE_KEY = 'devdesk:workspace'

/**
 * Active-workspace state. The selected id is shared (via useState) with useAuth's
 * api() wrapper, which attaches it as `X-Workspace-Id` on every request.
 */
export function useWorkspace() {
  const { api } = useAuth()
  const workspaceId = useState<number | null>('workspace:current', () => null)
  const workspaces = useState<Workspace[]>('workspace:list', () => [])
  const loaded = useState<boolean>('workspace:loaded', () => false)
  const queryClient = useQueryClient()

  const current = computed(
    () => workspaces.value.find((w) => w.id === workspaceId.value) ?? null,
  )

  async function load(): Promise<void> {
    const list = await api<Workspace[]>('/api/v1/workspaces')
    workspaces.value = list
    const saved = import.meta.client ? Number(localStorage.getItem(STORAGE_KEY)) : 0
    const pick = list.find((w) => w.id === saved) ?? list[0] ?? null
    workspaceId.value = pick?.id ?? null
    if (pick && import.meta.client) localStorage.setItem(STORAGE_KEY, String(pick.id))
    loaded.value = true
  }

  function setCurrent(id: number): void {
    if (id === workspaceId.value) return
    workspaceId.value = id
    if (import.meta.client) localStorage.setItem(STORAGE_KEY, String(id))
    // Cached data belongs to the previous workspace — drop it and refetch.
    queryClient.invalidateQueries()
  }

  async function createWorkspace(name: string): Promise<Workspace> {
    const ws = await api<Workspace>('/api/v1/workspaces', { method: 'POST', body: { name } })
    workspaces.value = [...workspaces.value, ws]
    setCurrent(ws.id)
    return ws
  }

  return { workspaces, workspaceId, current, loaded, load, setCurrent, createWorkspace }
}
