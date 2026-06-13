import tailwindcss from '@tailwindcss/vite'

// Set at image build time so the Nitro server proxies /api to the FastAPI container.
// In local dev the devProxy below handles it instead.
const apiProxyTarget = process.env.API_PROXY_TARGET

export default defineNuxtConfig({
  compatibilityDate: '2026-06-13',
  devtools: { enabled: false },
  css: ['~/assets/css/main.css'],
  app: {
    pageTransition: { name: 'page', mode: 'out-in' },
  },
  vite: { plugins: [tailwindcss()] },
  routeRules: {
    // public pages: prerendered (fast first paint, SEO-safe, no user data)
    '/': { prerender: true },
    '/login': { prerender: true },
    '/register': { prerender: true },
    // authenticated app: client-side rendered (avoids SSR JWT juggling)
    '/app/**': { ssr: false },
    ...(apiProxyTarget ? { '/api/**': { proxy: `${apiProxyTarget}/api/**` } } : {}),
  },
  nitro: {
    devProxy: {
      '/api': { target: 'http://localhost:8000/api', changeOrigin: true },
    },
  },
})
