/** Recent search terms for the ⌘K palette. Per-device, so localStorage — no
 * backend round-trip on every keystroke and no cross-device sync to maintain. */
const KEY = 'devdesk:search-recents'
const MAX = 5

export function useSearchRecents() {
  const recents = useState<string[]>('search:recents', () => [])

  if (import.meta.client && recents.value.length === 0) {
    try {
      recents.value = JSON.parse(localStorage.getItem(KEY) || '[]')
    } catch {
      recents.value = []
    }
  }

  function pushRecent(term: string): void {
    const t = term.trim()
    if (!t) return
    const next = [t, ...recents.value.filter((r) => r.toLowerCase() !== t.toLowerCase())].slice(0, MAX)
    recents.value = next
    if (import.meta.client) localStorage.setItem(KEY, JSON.stringify(next))
  }

  function clearRecents(): void {
    recents.value = []
    if (import.meta.client) localStorage.removeItem(KEY)
  }

  return { recents, pushRecent, clearRecents }
}
