import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    // Only use proxy in development
    ...(command === 'serve' && {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    }),
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})) 