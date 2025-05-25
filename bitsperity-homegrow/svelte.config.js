import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  
  kit: {
    adapter: adapter({
      out: 'build',
      precompress: true,
      envPrefix: ''
    }),
    
    alias: {
      $lib: 'src/lib',
      $components: 'src/lib/components',
      $stores: 'src/lib/stores',
      $utils: 'src/lib/utils',
      $types: 'src/lib/types',
      $api: 'src/lib/api',
      $mqtt: 'src/lib/mqtt',
      $beacon: 'src/lib/beacon',
      $database: 'src/lib/database'
    },
    
    files: {
      assets: 'static',
      hooks: {
        client: 'src/hooks.client.js',
        server: 'src/hooks.server.js'
      },
      lib: 'src/lib',
      params: 'src/params',
      routes: 'src/routes',
      serviceWorker: 'src/service-worker.js',
      appTemplate: 'src/app.html'
    },
    
    serviceWorker: {
      register: true
    },
    
    csrf: {
      checkOrigin: false
    }
  }
};

export default config; 