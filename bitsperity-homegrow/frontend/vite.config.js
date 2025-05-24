import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
	plugins: [
		sveltekit(),
		VitePWA({
			registerType: 'autoUpdate',
			workbox: {
				globPatterns: ['**/*.{js,css,html,ico,png,svg}']
			},
			manifest: {
				name: 'HomeGrow v3',
				short_name: 'HomeGrow',
				description: 'Professional hydroponic monitoring and automation system',
				theme_color: '#16a34a',
				background_color: '#ffffff',
				display: 'standalone',
				scope: '/',
				start_url: '/',
				icons: [
					{
						src: 'icon-192.png',
						sizes: '192x192',
						type: 'image/png'
					},
					{
						src: 'icon-512.png',
						sizes: '512x512',
						type: 'image/png'
					},
					{
						src: 'icon-512.png',
						sizes: '512x512',
						type: 'image/png',
						purpose: 'any maskable'
					}
				]
			}
		})
	],
	server: {
		host: '0.0.0.0',
		port: 3000,
		proxy: {
			'/api': {
				target: 'http://localhost:4001',
				changeOrigin: true,
				secure: false,
				configure: (proxy, options) => {
					proxy.on('error', (err, req, res) => {
						console.log('proxy error', err);
					});
					proxy.on('proxyReq', (proxyReq, req, res) => {
						console.log('Sending Request to the Target:', req.method, req.url);
					});
					proxy.on('proxyRes', (proxyRes, req, res) => {
						console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
					});
				}
			}
		}
	},
	preview: {
		host: '0.0.0.0',
		port: 3000
	}
}); 