/// <reference types="vitest/config" />
import path from 'node:path'
import diagnostics_channel from 'node:diagnostics_channel'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { defineConfig } from 'vite'

// Polyfill para tracingChannel em Node 18
if (!(diagnostics_channel as any).tracingChannel) {
  (diagnostics_channel as any).tracingChannel = () => ({
    start: { publish: () => {} },
    end: { publish: () => {} },
    asyncStart: { publish: () => {} },
    asyncEnd: { publish: () => {} },
    error: { publish: () => {} },
    trace: (fn: any) => fn(),
  })
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/api/'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              networkTimeoutSeconds: 5,
            },
          },
        ],
      },
      manifest: {
        name: "Estética Manager",
        short_name: "Estética",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#8b5cf6",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" }
        ]
      }
    })
  ],
  server: {
    host: true,
    allowedHosts: true,
  },
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  test: {
    environment: 'happy-dom',
    globals: false,
    pool: 'vmThreads',
  },
})
