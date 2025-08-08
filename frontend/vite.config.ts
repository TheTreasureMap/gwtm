import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	plugins: [sveltekit(), tailwindcss()],
	server: {
		host: '0.0.0.0',
		port: 3000,
		strictPort: true,
		hmr: {
			port: 3000
		},
		proxy: {
			'/api/v1': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			},
			'/ajax_pointingfromid': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			},
			'/admin': {
				target: 'http://localhost:8000',
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
