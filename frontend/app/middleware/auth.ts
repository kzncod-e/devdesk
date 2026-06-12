export default defineNuxtRouteMiddleware(async () => {
  // /app/** is ssr:false, so this only ever matters on the client
  if (import.meta.server) return
  const { token, refresh, fetchMe } = useAuth()
  if (!token.value) {
    const ok = await refresh()
    if (!ok) return navigateTo('/login')
    await fetchMe().catch(() => {})
  }
})
