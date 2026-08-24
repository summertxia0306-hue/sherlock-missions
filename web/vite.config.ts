import { resolve } from 'node:path'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => ({
  base: '/sherlock-english/',
  plugins: [
    react(),
    mode !== 'test' && VitePWA({
      registerType: 'prompt',
      includeAssets: ['sherlock-mark.svg'],
      manifest: {
        name: '夏洛恪英语学习',
        short_name: '夏洛恪英语',
        description: '夏洛恪的英语学习 PWA',
        theme_color: '#12372a',
        background_color: '#f7f3e8',
        display: 'standalone',
        start_url: '/sherlock-english/',
        scope: '/sherlock-english/',
        icons: [
          {
            src: 'sherlock-mark.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        navigateFallback: '/sherlock-english/index.html',
        globPatterns: ['**/*.{js,css,html,svg,woff2,json}'],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.includes('/sherlock-english/audio/listening/'),
            handler: 'CacheFirst',
            options: {
              cacheName: 'sherlock-listening-audio-v1',
              expiration: { maxEntries: 240, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] }
            }
          }
        ]
      }
    })
  ].filter(Boolean),
  resolve: mode === 'test' ? {
    alias: {
      'virtual:pwa-register/react': resolve(import.meta.dirname, 'src/test/pwa-register.ts')
    }
  } : undefined,
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/main.tsx', 'src/test/**', 'src/**/*.d.ts'],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80
      }
    }
  }
}))
