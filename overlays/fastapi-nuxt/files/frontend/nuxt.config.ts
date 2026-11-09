export default defineNuxtConfig({
  modules: ['@nuxt/ui'],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:60100/api/v1'
    }
  },
  typescript: { typeCheck: true }
})

