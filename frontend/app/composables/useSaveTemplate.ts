import type { TemplateKind } from '~/types/api'

interface SaveTarget {
  kind: TemplateKind
  sourceId: number
  sourceName: string
}

/**
 * Shared state for the global "Save as template" modal (mounted once in the app
 * layout). Any page or card can open it with a source; the modal owns the
 * capture mutation. Mirrors the useConfirm/useToast singleton pattern.
 */
export function useSaveTemplate() {
  const open = useState<boolean>('save-template:open', () => false)
  const target = useState<SaveTarget | null>('save-template:target', () => null)

  function save(t: SaveTarget): void {
    target.value = t
    open.value = true
  }

  function close(): void {
    open.value = false
    target.value = null
  }

  return { open, target, save, close }
}
