export interface ConfirmOptions {
  title: string
  message?: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}

interface ConfirmState extends ConfirmOptions {
  open: boolean
  resolve: ((ok: boolean) => void) | null
}

/** Promise-based confirmation backed by a single globally-mounted dialog. */
export function useConfirm() {
  const state = useState<ConfirmState>('confirm:state', () => ({
    open: false,
    title: '',
    resolve: null,
  }))

  function confirm(options: ConfirmOptions): Promise<boolean> {
    return new Promise((resolve) => {
      state.value = { ...options, open: true, resolve }
    })
  }

  function settle(ok: boolean) {
    state.value.resolve?.(ok)
    state.value = { ...state.value, open: false, resolve: null }
  }

  return { state, confirm, settle }
}
