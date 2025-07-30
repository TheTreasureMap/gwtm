import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

// Ultra-stable development configuration for containers
// Use this if the main config still has ESBuild issues
export default defineConfig({
	plugins: [sveltekit(), tailwindcss()],
	define: {
		'process.env.NODE_ENV': JSON.stringify('development')
	},
	server: {
		host: '0.0.0.0',
		port: 3000,
		strictPort: true,
		hmr: {
			port: 3000,
			overlay: false
		},
		watch: {
			ignored: ['**/node_modules/**', '**/.git/**', '**/build/**', '**/.svelte-kit/**'],
			usePolling: true,
			interval: 2000
		},
		middlewareMode: false,
		fs: {
			strict: false
		}
	},
	preview: {
		host: '0.0.0.0',
		port: 3000,
		strictPort: true
	},
	build: {
		outDir: 'build',
		sourcemap: false, // Disable sourcemaps for faster builds
		minify: false, // Disable minification to avoid ESBuild
		rollupOptions: {
			output: {
				chunkFileNames: 'chunks/[name].js',
				entryFileNames: 'entries/[name].js',
				assetFileNames: 'assets/[name].[ext]'
			}
		}
	},
	// Completely disable ESBuild and optimizations
	optimizeDeps: {
		disabled: true
	},
	esbuild: false
});
