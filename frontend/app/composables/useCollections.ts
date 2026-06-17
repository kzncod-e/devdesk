import type { Collection, CollectionKind } from '~/types/api'

/** Thin wrapper over the /collections API. Pages own their own useQuery/useMutation. */
export function useCollections() {
  const { api } = useAuth()

  const list = (kind: CollectionKind) =>
    api<Collection[]>(`/api/v1/collections?kind=${kind}`)

  const create = (body: { name: string; kind: CollectionKind; parent_id?: number | null }) =>
    api<Collection>('/api/v1/collections', { method: 'POST', body })

  const rename = (id: number, name: string) =>
    api<Collection>(`/api/v1/collections/${id}`, { method: 'PATCH', body: { name } })

  const remove = (id: number) =>
    api(`/api/v1/collections/${id}`, { method: 'DELETE' })

  return { list, create, rename, remove }
}
