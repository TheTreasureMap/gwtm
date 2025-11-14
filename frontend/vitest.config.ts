import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
	plugins: [sveltekit()],

	test: {
		// Test environment
		environment: 'jsdom',

		// Setup files
		setupFiles: ['./src/__tests__/setup.ts'],

		// Include patterns
		include: ['src/**/*.{test,spec}.{js,ts}'],

		// Global test utilities
		globals: true,

		// Coverage configuration
		coverage: {
			provider: 'v8',
			reporter: ['text', 'json', 'html', 'json-summary'],
			exclude: [
				'node_modules/',
				'src/__tests__/',
				'**/*.d.ts',
				'**/*.config.*',
				'src/app.html',
				'src/routes/**', // Exclude route components for now (focus on business logic)
				'src/lib/components/**/*.svelte', // Exclude Svelte components for now
				'src/lib/api/services/**' // Exclude API service calls (require mocking)
			],
			include: ['src/lib/utils/**', 'src/lib/validation/**', 'src/lib/stores/**'],
			// Coverage thresholds
			thresholds: {
				global: {
					branches: 80,
					functions: 80,
					lines: 80,
					statements: 80
				},
				// Higher standards for critical business logic
				'src/lib/validation/**': {
					branches: 90,
					functions: 90,
					lines: 90,
					statements: 90
				},
				'src/lib/utils/**': {
					branches: 85,
					functions: 85,
					lines: 85,
					statements: 85
				}
			}
		},

		// Test timeout
		testTimeout: 10000,

		// Watch options
		watch: {
			exclude: ['node_modules/**', 'build/**']
		}
	}
});
