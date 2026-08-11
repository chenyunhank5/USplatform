import { defineConfig } from 'vite'
import { resolve } from 'node:path'

export default defineConfig({
  build: {
    emptyOutDir: true,
    outDir: resolve(__dirname, 'core/static/core/wallet-connect'),
    rollupOptions: {
      input: resolve(__dirname, 'frontend/wallet-connect.js'),
      output: {
        entryFileNames: 'wallet-connect.js',
        chunkFileNames: 'wallet-connect-[name]-[hash].js',
        assetFileNames: 'wallet-connect-[name]-[hash][extname]'
      }
    }
  }
})
