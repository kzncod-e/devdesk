import type { TokenOut, User } from '~/types/api'

type FetchOptions = Parameters<typeof $fetch>[1]

export function useAuth() {
  // access token lives in memory only (spec §4); refresh token is an
  // httpOnly cookie scoped to /api/v1/auth that the browser manages
  const token = useState<string | null>('auth:access', () => null)
  const user = useState<User | null>('auth:user', () => null)
  // Active workspace id — managed by useWorkspace, read here to scope every request.
  const workspaceId = useState<number | null>('workspace:current', () => null)

  async function login(email: string, password: string): Promise<void> {
    const res = await $fetch<TokenOut>('/api/v1/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    token.value = res.access_token
    await fetchMe()
  }

  async function register(name: string, email: string, password: string): Promise<void> {
    await $fetch('/api/v1/auth/register', {
      method: 'POST',
      body: { name, email, password },
    })
    await login(email, password)
  }

  async function refresh(): Promise<boolean> {
    try {
      const res = await $fetch<TokenOut>('/api/v1/auth/refresh', { method: 'POST' })
      token.value = res.access_token
      return true
    } catch {
      token.value = null
      return false
    }
  }

  async function fetchMe(): Promise<void> {
    user.value = await api<User>('/api/v1/auth/me')
  }

  function logout(): void {
    token.value = null
    user.value = null
    navigateTo('/login')
  }

  /** Authenticated $fetch: bearer header + one transparent refresh-and-retry on 401. */
  async function api<T>(path: string, opts: FetchOptions = {}): Promise<T> {
    const doFetch = () =>
      $fetch<T>(path, {
        ...opts,
        headers: {
          ...(opts?.headers ?? {}),
          ...(token.value ? { Authorization: `Bearer ${token.value}` } : {}),
          ...(workspaceId.value ? { 'X-Workspace-Id': String(workspaceId.value) } : {}),
        },
      } as FetchOptions)
    try {
      return (await doFetch()) as T
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status
      if (status === 401 && (await refresh())) return (await doFetch()) as T
      throw err
    }
  }

  return { token, user, login, register, refresh, fetchMe, logout, api }
}
