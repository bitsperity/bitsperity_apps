import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  
  server: {
    port: 3000,
    host: '0.0.0.0',
    strictPort: true
  },
  
  preview: {
    port: 3000,
    host: '0.0.0.0',
    strictPort: true
  },
  
  build: {
    target: 'node18',
    minify: 'esbuild',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['svelte', '@sveltejs/kit'],
          charts: ['chart.js'],
          utils: ['lodash-es']
        }
      }
    }
  },
  
  optimizeDeps: {
    include: ['socket.io-client', 'mqtt']
  },
  
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '3.0.0')
  }
}); 