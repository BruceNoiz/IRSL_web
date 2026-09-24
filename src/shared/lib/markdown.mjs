import { relative, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
const featureDirectory = fileURLToPath(new URL('../../features/', import.meta.url));

// Shared presentation only. Editorial selection belongs in each feature's content files.
export function contentMarkdown({ base }) {
  return (tree, file) => {
    const path = relative(featureDirectory, file.path);
    if (path.startsWith('..') || !path.includes('/content/')) return;
    const id = basename(file.path, '.md');
    const prefix = `/${base.split('/').filter(Boolean).join('/')}${base === '/' ? '' : '/'}`;
    tree.children = tree.children.filter(node => !(node.type === 'heading' && node.depth === 1));
    let heading = 0;
    function visit(node) {
      if (node.type === 'heading') {
        node.depth = Math.min(node.depth + 1, 6);
        node.data = { ...node.data, hProperties: { id: `${id}-heading-${++heading}` } };
      }
      if ((node.type === 'link' || node.type === 'image') && node.url.startsWith('/') && !node.url.startsWith('//')) {
        node.url = `${prefix}${node.url.slice(1)}`;
      }
      node.children?.forEach(visit);
    }
    visit(tree);
  };
}
