const STORAGE_KEY = 'devdesk:onboarded'

export function useAppReady() {
  const isReady = useState('app:ready', () => false)

  function markReady() {
    isReady.value = true
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, '1')
    }
  }

  const hasOnboarded = computed(() => {
    if (!import.meta.client) return false
    return !!localStorage.getItem(STORAGE_KEY)
  })

  return { isReady, hasOnboarded, markReady }
}
