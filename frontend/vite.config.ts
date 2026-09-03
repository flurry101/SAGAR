import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { lingui } from '@lingui/vite-plugin';
import { VitePWA } from 'vite-plugin-pwa';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: ['@lingui/babel-plugin-lingui-macro'],
      },
    }),
    lingui(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'ORCA — Marine Ecosystem Reasoning & Safety PWA',
        short_name: 'ORCA Safety',
        description: 'Spatio-temporal maritime safety advisory & trip planning',
        theme_color: '#070d18',
        background_color: '#070d18',
        display: 'standalone',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          maplibre: ['maplibre-gl'],
          vendor: ['react', 'react-dom', 'zustand', '@tanstack/react-query', '@lingui/core', '@lingui/react']
        }
      }
    },
    chunkSizeWarningLimit: 800
  },
  server: {
    port: 5173,
    host: true
  }
});
