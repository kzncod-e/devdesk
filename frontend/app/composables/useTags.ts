import { useQuery } from '@tanstack/vue-query'

import type { Tag } from '~/types/api'

const DEFAULT_COLOR = '#6366f1'

/** Workspace tag registry: name→color for colored chips + autocomplete. */
export function useTags() {
  const { api } = useAuth()
  const { workspaceId } = useWorkspace()

  const { data: tags } = useQuery({
    queryKey: computed(() => ['tags', workspaceId.value]),
    queryFn: () => api<Tag[]>('/api/v1/tags'),
    enabled: computed(() => workspaceId.value != null),
    staleTime: 60_000,
  })

  const colorMap = computed(() => {
    const m: Record<string, string> = {}
    for (const t of tags.value ?? []) m[t.name.toLowerCase()] = t.color
    return m
  })

  function colorOf(name: string): string {
    return colorMap.value[name.toLowerCase()] ?? DEFAULT_COLOR
  }

  const names = computed(() => (tags.value ?? []).map((t) => t.name))

  return { tags, colorOf, colorMap, names }
}
