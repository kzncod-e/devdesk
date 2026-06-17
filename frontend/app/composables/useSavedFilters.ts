import type { SavedFilter, SavedFilterKind } from '~/types/api'

/** Thin wrapper over the /saved-filters API (per-user, current workspace). */
export function useSavedFilters() {
  const { api } = useAuth()

  const list = (kind: SavedFilterKind) =>
    api<SavedFilter[]>(`/api/v1/saved-filters?kind=${kind}`)

  const create = (body: { name: string; kind: SavedFilterKind; query: Record<string, unknown> }) =>
    api<SavedFilter>('/api/v1/saved-filters', { method: 'POST', body })

  const remove = (id: number) =>
    api(`/api/v1/saved-filters/${id}`, { method: 'DELETE' })

  return { list, create, remove }
}
