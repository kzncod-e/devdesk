/**
 * Cross-page "create" intent. The ⌘K palette can request a create modal that
 * lives on another page: it sets the intent and navigates; the target page
 * consumes the intent on mount (or reactively, if already mounted) and opens
 * its own form. Keeps the create modals page-local while making them reachable
 * from anywhere.
 */
export type QuickCreateKind = 'project' | 'snippet' | 'bookmark'

const ROUTE: Record<QuickCreateKind, string> = {
  project: '/app',
  snippet: '/app/snippets',
  bookmark: '/app/bookmarks',
}

export function useQuickCreate() {
  const intent = useState<QuickCreateKind | null>('quick-create:intent', () => null)

  function request(kind: QuickCreateKind): void {
    intent.value = kind
    navigateTo(ROUTE[kind])
  }

  /** Returns true exactly once for the matching kind, then clears the intent. */
  function consume(kind: QuickCreateKind): boolean {
    if (intent.value === kind) {
      intent.value = null
      return true
    }
    return false
  }

  return { intent, request, consume }
}
