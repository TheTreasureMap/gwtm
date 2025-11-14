import prettier from 'eslint-config-prettier';
import js from '@eslint/js';
import { includeIgnoreFile } from '@eslint/compat';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import { fileURLToPath } from 'node:url';
import ts from 'typescript-eslint';
import svelteConfig from './svelte.config.js';

const gitignorePath = fileURLToPath(new URL('./.gitignore', import.meta.url));

export default ts.config(
	includeIgnoreFile(gitignorePath),
	{
		ignores: [
			'docs/**/*',
			'src/lib/components/alerts/**/*',
			'src/routes/submit/instruments/**/*',
			'src/routes/alerts/**/*',
			'src/routes/register/**/*',
			'src/lib/components/forms/FootprintTypeSelector.svelte',
			'src/lib/components/forms/LoadPointingField.svelte',
			'src/lib/components/forms/TimeField.svelte',
			'src/lib/components/forms/examples/**/*',
			'src/lib/components/instruments/**/*',
			'src/lib/components/search/**/*',
			'src/lib/components/visualization/**/*',
			'src/lib/components/ui/FootprintVisualization.svelte',
			'src/lib/components/ui/PageContainer.svelte',
			'src/routes/documentation/**/*',
			'src/routes/manage/**/*',
			'coverage/**/*'
		]
	},
	js.configs.recommended,
	...ts.configs.recommended,
	...svelte.configs.recommended,
	prettier,
	...svelte.configs.prettier,
	{
		languageOptions: {
			globals: { ...globals.browser, ...globals.node }
		},
		rules: {
			'no-undef': 'off',
			'@typescript-eslint/no-explicit-any': 'warn',
			'@typescript-eslint/no-unused-vars': 'warn',
			'svelte/require-each-key': 'warn',
			'svelte/no-reactive-reassign': 'warn',
			'no-useless-escape': 'warn'
		}
	},
	{
		files: ['**/*.svelte', '**/*.svelte.ts', '**/*.svelte.js'],
		languageOptions: {
			parserOptions: {
				projectService: true,
				extraFileExtensions: ['.svelte'],
				parser: ts.parser,
				svelteConfig
			}
		}
	}
);
