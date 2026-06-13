export type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'devdesk:theme'

/** Reactive light/dark theme, persisted to localStorage and reflected on <html>. */
export function useTheme() {
  const mode = useState<ThemeMode>('theme:mode', () => 'light')

  function apply(next: ThemeMode) {
    mode.value = next
    if (import.meta.client) {
      document.documentElement.classList.toggle('dark', next === 'dark')
      document.documentElement.style.colorScheme = next
      localStorage.setItem(STORAGE_KEY, next)
    }
  }

  function init() {
    if (!import.meta.client) return
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    apply(stored ?? (prefersDark ? 'dark' : 'light'))
  }

  function toggle() {
    apply(mode.value === 'dark' ? 'light' : 'dark')
  }

  return { mode, init, toggle, apply }
}
