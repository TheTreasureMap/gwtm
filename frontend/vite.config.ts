import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	plugins: [sveltekit(), tailwindcss()],
	server: {
		host: '0.0.0.0',
		port: 3000,
		strictPort: true,
		allowedHosts: true,
		hmr: {
			port: 3000
		},
		proxy: {
			// Only proxy in development - use environment-aware target
			'/api/v1': {
				target: process.env.FASTAPI_URL || 'http://fastapi-backend:8000',
				changeOrigin: true,
				secure: false
			},
			'/ajax_pointingfromid': {
				target: process.env.FASTAPI_URL || 'http://fastapi-backend:8000',
				changeOrigin: true,
				secure: false
			},
			'/admin': {
				target: process.env.FASTAPI_URL || 'http://fastapi-backend:8000',
				changeOrigin: true,
				secure: false
			}
		}
	},
	preview: {
		host: '0.0.0.0',
		port: 3000,
		strictPort: true
	},
	build: {
		outDir: 'build',
		sourcemap: true
	}
});
