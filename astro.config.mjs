import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import { contentMarkdown } from './src/shared/lib/markdown.mjs';

const base = process.env.BASE_PATH || '/IRSL_web/';

export default defineConfig({
  site: process.env.SITE_URL || undefined,
  base,
  output: 'static',
  trailingSlash: 'always',
  integrations: [react()],
  markdown: { remarkPlugins: [[contentMarkdown, { base }]] },
  devToolbar: { enabled: false },
});
