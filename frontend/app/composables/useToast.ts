export type ToastTone = 'default' | 'success' | 'error'

export interface Toast {
  id: number
  message: string
  tone: ToastTone
}

let counter = 0

/** Lightweight transient notifications rendered by <UiToaster>. */
export function useToast() {
  const toasts = useState<Toast[]>('toasts', () => [])

  function dismiss(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  function push(message: string, tone: ToastTone = 'default', timeout = 3500) {
    const id = ++counter
    toasts.value = [...toasts.value, { id, message, tone }]
    if (import.meta.client && timeout) setTimeout(() => dismiss(id), timeout)
    return id
  }

  return {
    toasts,
    dismiss,
    toast: (m: string) => push(m, 'default'),
    success: (m: string) => push(m, 'success'),
    error: (m: string) => push(m, 'error'),
  }
}
