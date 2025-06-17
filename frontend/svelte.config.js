import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter({
			// Default options for static adapter
			pages: 'build',
			assets: 'build',
			fallback: 'index.html', // SPA fallback
			precompress: false,
			strict: true
		})
	}
};

export default config;
