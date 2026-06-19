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
    head: {
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,700;12..96,800&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600&display=swap',
        },
      ],
    },
  },
  vite: { plugins: [tailwindcss()] },
  routeRules: {
    '/': { prerender: true },
    '/login': { prerender: true },
    '/register': { prerender: true },
    '/app/**': { ssr: false },
    ...(apiProxyTarget ? { '/api/**': { proxy: `${apiProxyTarget}/api/**` } } : {}),
  },
  nitro: {
    devProxy: {
      '/api': { target: 'http://localhost:8000/api', changeOrigin: true },
    },
  },
})
