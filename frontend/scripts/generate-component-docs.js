#!/usr/bin/env node

/**
 * Component Documentation Generator
 *
 * This script automatically generates API reference documentation for Svelte components
 * by parsing JSDoc comments and component exports.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { glob } from 'glob';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COMPONENTS_DIR = path.join(__dirname, '../src/lib/components');
const DOCS_DIR = path.join(__dirname, '../docs');
const OUTPUT_FILE = path.join(DOCS_DIR, 'component-api-reference.md');

/**
 * Parse JSDoc comments from component content
 */
function parseJSDoc(content) {
	const jsdocRegex = /\/\*\*([\s\S]*?)\*\//g;
	const docs = [];
	let match;

	while ((match = jsdocRegex.exec(content)) !== null) {
		const comment = match[1];
		const parsed = parseJSDocComment(comment);
		if (parsed.component) {
			docs.push(parsed);
		}
	}

	return docs;
}

/**
 * Parse individual JSDoc comment
 */
function parseJSDocComment(comment) {
	const lines = comment.split('\n').map((line) => line.replace(/^\s*\*\s?/, '').trim());
	const doc = {};
	let currentSection = 'description';
	let currentContent = [];

	for (const line of lines) {
		if (line.startsWith('@')) {
			// Save previous section
			if (currentContent.length > 0) {
				doc[currentSection] = currentContent.join('\n').trim();
				currentContent = [];
			}

			// Parse tag
			const tagMatch = line.match(/^@(\w+)(?:\s+(.*))?/);
			if (tagMatch) {
				const [, tag, content] = tagMatch;
				currentSection = tag;
				if (content) {
					currentContent.push(content);
				}
			}
		} else if (line) {
			currentContent.push(line);
		}
	}

	// Save last section
	if (currentContent.length > 0) {
		doc[currentSection] = currentContent.join('\n').trim();
	}

	return doc;
}

/**
 * Parse component props from script section
 */
function parseProps(content) {
	const propRegex = /\/\*\*([\s\S]*?)\*\/\s*export\s+let\s+(\w+)(?::\s*([^=]+?))?\s*=\s*([^;]+);?/g;
	const props = [];
	let match;

	while ((match = propRegex.exec(content)) !== null) {
		const [, comment, name, type, defaultValue] = match;
		const propDoc = parseJSDocComment(comment);

		props.push({
			name,
			type: propDoc.type || type?.trim() || 'any',
			default: propDoc.default || defaultValue?.trim() || 'undefined',
			description: propDoc.description || '',
			optional: propDoc.optional !== undefined,
			deprecated: propDoc.deprecated !== undefined
		});
	}

	return props;
}

/**
 * Parse component slots from HTML comments
 */
function parseSlots(content) {
	const slotCommentRegex = /<!--[\s\S]*?@slot\s+([^-]+?)-->/g;
	const slots = [];
	let match;

	while ((match = slotCommentRegex.exec(content)) !== null) {
		const slotContent = match[1];
		const lines = slotContent
			.split('\n')
			.map((line) => line.trim())
			.filter(Boolean);

		for (const line of lines) {
			const slotMatch = line.match(/@slot\s+(?:\{([^}]+)\}\s+)?(\w+)\s*-\s*(.+)/);
			if (slotMatch) {
				const [, props, name, description] = slotMatch;
				slots.push({
					name,
					description: description.trim(),
					props: props ? props.split(',').map((p) => p.trim()) : []
				});
			}
		}
	}

	return slots;
}

/**
 * Parse component events from JSDoc comments
 */
function parseEvents(content) {
	const eventRegex = /@event\s+(?:\{([^}]+)\}\s+)?(\w+)\s*-\s*(.+)/g;
	const events = [];
	let match;

	while ((match = eventRegex.exec(content)) !== null) {
		const [, type, name, description] = match;
		events.push({
			name,
			type: type || 'CustomEvent',
			description: description.trim()
		});
	}

	return events;
}

/**
 * Generate markdown documentation for a component
 */
function generateComponentDoc(componentData) {
	const { name, doc, props, slots, events, filePath } = componentData;

	let markdown = `## ${name}\n\n`;

	if (doc.description) {
		markdown += `${doc.description}\n\n`;
	}

	// Add metadata
	if (doc.category || doc.version || doc.since) {
		markdown += `**Metadata:**\n`;
		if (doc.category) markdown += `- **Category:** ${doc.category}\n`;
		if (doc.version) markdown += `- **Version:** ${doc.version}\n`;
		if (doc.since) markdown += `- **Since:** ${doc.since}\n`;
		markdown += '\n';
	}

	// Add file path
	markdown += `**File:** \`${filePath.replace(process.cwd(), '.')}\`\n\n`;

	// Props
	if (props.length > 0) {
		markdown += `### Props\n\n`;
		markdown += `| Name | Type | Default | Description |\n`;
		markdown += `|------|------|---------|-------------|\n`;

		for (const prop of props) {
			const typeStr = prop.type.replace(/\|/g, '\\|');
			const defaultStr = prop.default === 'undefined' ? '-' : `\`${prop.default}\``;
			const nameStr = prop.optional ? `${prop.name}?` : prop.name;
			const deprecatedStr = prop.deprecated ? ' ⚠️ *Deprecated*' : '';

			markdown += `| \`${nameStr}\` | \`${typeStr}\` | ${defaultStr} | ${prop.description}${deprecatedStr} |\n`;
		}
		markdown += '\n';
	}

	// Events
	if (events.length > 0) {
		markdown += `### Events\n\n`;
		markdown += `| Name | Type | Description |\n`;
		markdown += `|------|------|-------------|\n`;

		for (const event of events) {
			markdown += `| \`${event.name}\` | \`${event.type}\` | ${event.description} |\n`;
		}
		markdown += '\n';
	}

	// Slots
	if (slots.length > 0) {
		markdown += `### Slots\n\n`;
		markdown += `| Name | Props | Description |\n`;
		markdown += `|------|-------|-------------|\n`;

		for (const slot of slots) {
			const propsStr = slot.props.length > 0 ? slot.props.map((p) => `\`${p}\``).join(', ') : '-';
			markdown += `| \`${slot.name}\` | ${propsStr} | ${slot.description} |\n`;
		}
		markdown += '\n';
	}

	// Examples
	if (doc.example) {
		markdown += `### Example\n\n`;
		markdown += `${doc.example}\n\n`;
	}

	// Accessibility notes
	if (doc.accessibility) {
		markdown += `### Accessibility\n\n`;
		markdown += `${doc.accessibility}\n\n`;
	}

	// Performance notes
	if (doc.performance) {
		markdown += `### Performance\n\n`;
		markdown += `${doc.performance}\n\n`;
	}

	// See also
	if (doc.see) {
		markdown += `### See Also\n\n`;
		markdown += `${doc.see}\n\n`;
	}

	markdown += '---\n\n';

	return markdown;
}

/**
 * Main function to generate documentation
 */
async function generateDocs() {
	console.log('🔍 Scanning for Svelte components...');

	const componentFiles = await glob('**/*.svelte', {
		cwd: COMPONENTS_DIR,
		absolute: true
	});

	console.log(`📋 Found ${componentFiles.length} component files`);

	const components = [];
	const categories = new Map();

	for (const filePath of componentFiles) {
		try {
			const content = fs.readFileSync(filePath, 'utf-8');
			const docs = parseJSDoc(content);

			if (docs.length > 0) {
				const mainDoc = docs[0]; // Use first JSDoc comment as main documentation
				const componentName = mainDoc.component || path.basename(filePath, '.svelte');

				const props = parseProps(content);
				const slots = parseSlots(content);
				const events = parseEvents(content);

				const componentData = {
					name: componentName,
					doc: mainDoc,
					props,
					slots,
					events,
					filePath
				};

				components.push(componentData);

				// Group by category
				const category = mainDoc.category || 'Uncategorized';
				if (!categories.has(category)) {
					categories.set(category, []);
				}
				categories.get(category).push(componentData);

				console.log(`✅ Parsed ${componentName} (${category})`);
			} else {
				console.log(`⚠️  No documentation found for ${path.basename(filePath)}`);
			}
		} catch (error) {
			console.error(`❌ Error processing ${filePath}:`, error.message);
		}
	}

	// Generate markdown
	console.log('\n📝 Generating API reference...');

	let markdown = `# Component API Reference\n\n`;
	markdown += `*This documentation is automatically generated from component JSDoc comments.*\n\n`;
	markdown += `**Generated:** ${new Date().toISOString()}\n`;
	markdown += `**Components:** ${components.length}\n\n`;

	// Table of contents
	markdown += `## Table of Contents\n\n`;

	for (const [category, categoryComponents] of categories.entries()) {
		markdown += `### ${category}\n\n`;
		for (const component of categoryComponents) {
			markdown += `- [${component.name}](#${component.name.toLowerCase()})\n`;
		}
		markdown += '\n';
	}

	markdown += '\n---\n\n';

	// Component documentation
	for (const [category, categoryComponents] of categories.entries()) {
		markdown += `# ${category} Components\n\n`;

		for (const component of categoryComponents) {
			markdown += generateComponentDoc(component);
		}
	}

	// Write to file
	fs.writeFileSync(OUTPUT_FILE, markdown);

	console.log(`\n✅ Documentation generated: ${OUTPUT_FILE}`);
	console.log(`📊 Total components documented: ${components.length}`);
	console.log(`📂 Categories: ${Array.from(categories.keys()).join(', ')}`);
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
	generateDocs().catch(console.error);
}

export { generateDocs };
