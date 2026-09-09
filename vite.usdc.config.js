import { defineConfig } from 'vite'
import { resolve } from 'node:path'
export default defineConfig({ build: { outDir: resolve('core/static/core/usdc-payments'), emptyOutDir: true,
  rollupOptions: { input: resolve('frontend/usdc-payments.js'), output: { entryFileNames: 'usdc-payments.js', chunkFileNames: '[name]-[hash].js' } }
} })
