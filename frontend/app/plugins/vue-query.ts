import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

export default defineNuxtPlugin((nuxtApp) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: 1, staleTime: 5_000 } },
  })
  nuxtApp.vueApp.use(VueQueryPlugin, { queryClient })
})
