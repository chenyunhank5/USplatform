import { defineConfig } from 'vite'
import { resolve } from 'node:path'

export default defineConfig({
  root: resolve(__dirname, 'frontend'),
  base: '/static/core/aztoken-deployer/',
  server: {
    fs: {
      allow: [resolve(__dirname)]
    }
  },
  build: {
    emptyOutDir: true,
    outDir: resolve(__dirname, 'core/static/core/aztoken-deployer'),
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => assetInfo.name?.endsWith('.css')
          ? 'aztoken-deployer.css'
          : 'assets/[name][extname]',
        entryFileNames: 'aztoken-deployer.js',
        inlineDynamicImports: true,
      },
      input: resolve(__dirname, 'frontend/aztoken-deployer.html')
    }
  }
})
