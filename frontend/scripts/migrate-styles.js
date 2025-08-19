#!/usr/bin/env node

/**
 * Style Migration Script
 * Helps migrate existing Tailwind classes to design system classes
 */

import fs from 'fs';
import path from 'path';
import { glob } from 'glob';

// Common class mappings
const classMappings = {
	// Button mappings
	'bg-blue-600 text-white hover:bg-blue-700': 'btn-primary',
	'bg-gray-300 text-gray-700 hover:bg-gray-400': 'btn-secondary',
	'bg-transparent text-blue-600 hover:bg-blue-50': 'btn-ghost',
	'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50': 'btn-outline',
	'bg-red-600 text-white hover:bg-red-700': 'btn-danger',

	// Size mappings
	'px-3 py-1.5 text-sm': 'btn-sm',
	'px-4 py-2 text-sm': 'btn-md',
	'px-6 py-3 text-base': 'btn-lg',

	// Card mappings
	'bg-white rounded-lg shadow-lg': 'card-base',
	'hover:shadow-xl transition-shadow duration-200': 'card-hover',
	'p-4': 'card-padding-sm',
	'p-6': 'card-padding-md',
	'p-8': 'card-padding-lg',

	// Form mappings
	'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300':
		'form-input',
	'block text-sm font-medium leading-6 text-gray-900': 'form-label',

	// Navigation mappings
	'text-gray-700 hover:text-blue-600': 'nav-link',
	'block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100': 'nav-dropdown-item',

	// Status mappings
	'bg-green-100 text-green-800 border-green-200': 'status-success',
	'bg-yellow-100 text-yellow-800 border-yellow-200': 'status-warning',
	'bg-red-100 text-red-800 border-red-200': 'status-error',
	'bg-blue-100 text-blue-800 border-blue-200': 'status-info',
	'bg-gray-100 text-gray-800 border-gray-200': 'status-neutral',

	// Container mappings
	'max-w-7xl mx-auto px-4': 'container-responsive',
	'max-w-md mx-auto': 'container-sm',
	'max-w-2xl mx-auto': 'container-md',
	'max-w-4xl mx-auto': 'container-lg'
};

// Color token mappings
const colorMappings = {
	'blue-50': 'primary-50',
	'blue-100': 'primary-100',
	'blue-200': 'primary-200',
	'blue-300': 'primary-300',
	'blue-400': 'primary-400',
	'blue-500': 'primary-500',
	'blue-600': 'primary-600',
	'blue-700': 'primary-700',
	'blue-800': 'primary-800',
	'blue-900': 'primary-900',

	'green-100': 'success-100',
	'green-500': 'success-500',
	'green-600': 'success-600',
	'green-700': 'success-700',

	'red-100': 'error-100',
	'red-500': 'error-500',
	'red-600': 'error-600',
	'red-700': 'error-700',

	'yellow-100': 'warning-100',
	'yellow-500': 'warning-500',
	'yellow-600': 'warning-600',
	'yellow-700': 'warning-700'
};

function migrateFile(filePath) {
	let content = fs.readFileSync(filePath, 'utf8');
	let changed = false;

	// Replace class mappings
	for (const [oldClasses, newClass] of Object.entries(classMappings)) {
		const regex = new RegExp(oldClasses.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
		if (content.includes(oldClasses)) {
			content = content.replace(regex, newClass);
			changed = true;
			console.log(`  ✓ Replaced "${oldClasses}" with "${newClass}"`);
		}
	}

	// Replace color tokens
	for (const [oldColor, newColor] of Object.entries(colorMappings)) {
		const regex = new RegExp(`\\b${oldColor}\\b`, 'g');
		if (content.includes(oldColor)) {
			content = content.replace(regex, newColor);
			changed = true;
			console.log(`  ✓ Replaced color "${oldColor}" with "${newColor}"`);
		}
	}

	if (changed) {
		fs.writeFileSync(filePath, content);
		return true;
	}

	return false;
}

async function migrateStyles() {
	console.log('🎨 Starting style migration...\n');

	// Find all Svelte files
	const files = await glob('src/**/*.svelte', { cwd: 'frontend' });

	let totalFiles = 0;
	let changedFiles = 0;

	for (const file of files) {
		const fullPath = path.join('frontend', file);
		console.log(`Processing: ${file}`);

		const wasChanged = migrateFile(fullPath);
		totalFiles++;

		if (wasChanged) {
			changedFiles++;
			console.log(`  ✅ Updated\n`);
		} else {
			console.log(`  ⏭️  No changes needed\n`);
		}
	}

	console.log(`\n🎉 Migration complete!`);
	console.log(`📊 Files processed: ${totalFiles}`);
	console.log(`📝 Files updated: ${changedFiles}`);
	console.log(`\n💡 Next steps:`);
	console.log(`   1. Review the changes and test your application`);
	console.log(`   2. Update components to use classBuilder functions`);
	console.log(`   3. Add design system imports where needed`);
}

// Run migration if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
	migrateStyles().catch(console.error);
}

export { migrateStyles, classMappings, colorMappings };
