import assert from 'node:assert/strict';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { contentMarkdown } from '../src/shared/lib/markdown.mjs';
import { tableRows } from '../src/shared/lib/markdown-table.mjs';
import { researchIcon, researchIconPaths } from '../src/features/home/research-icons.mjs';

const source = fileURLToPath(new URL('../src/features/faculty/content/journals.md', import.meta.url));
for (const base of ['/', '/IRSL_web/', '/nested/lab', '/nested/lab/']) {
  test(`Shared Markdown preserves content, links and unique headings under ${base}`, () => {
    const prefix = base.endsWith('/') ? base : `${base}/`;
    const tree = { type: 'root', children: [
      { type: 'heading', depth: 1, children: [{ type: 'text', value: '文件標題' }] },
      { type: 'heading', depth: 2, children: [{ type: 'text', value: '同名標題' }] },
      { type: 'paragraph', children: [
        { type: 'link', url: '/members/#education' },
        { type: 'image', url: '/assets/photo.jpg', alt: '照片' },
        { type: 'link', url: 'https://example.invalid/paper' },
        { type: 'text', value: '博士、碩士與全部學術內容' },
      ] },
      { type: 'heading', depth: 2, children: [{ type: 'text', value: '同名標題' }] },
    ] };
    contentMarkdown({ base })(tree, { path: source });
    assert.equal(tree.children.length, 3);
    assert.equal(tree.children[0].depth, 3);
    assert.notEqual(tree.children[0].data.hProperties.id, tree.children[2].data.hProperties.id);
    const [link, image, external, text] = tree.children[1].children;
    assert.equal(link.url, `${prefix}members/#education`);
    assert.equal(image.url, `${prefix}assets/photo.jpg`);
    assert.equal(image.alt, '照片');
    assert.equal(external.url, 'https://example.invalid/paper');
    assert.equal(text.value, '博士、碩士與全部學術內容');
  });
}

test('Unrelated and original source Markdown is unchanged', () => {
  for (const path of ['docs/journals.md', 'artifact/02_學歷.md']) {
    const tree = { type: 'root', children: [{ type: 'heading', depth: 1 }] };
    const before = structuredClone(tree);
    contentMarkdown({ base: '/' })(tree, { path: fileURLToPath(new URL(`../${path}`, import.meta.url)) });
    assert.deepEqual(tree, before);
  }
});

test('Adding a Markdown table row does not require a renderer change', () => {
  const table = '# 課程\n\n| 課程 | 內容 | 層級 |\n| --- | --- | --- |\n| A | 完整內容 | 大學部 |\n';
  assert.deepEqual(tableRows(table + '| B | 新內容 | 碩士/博士 |\n'), [['A', '完整內容', '大學部'], ['B', '新內容', '碩士/博士']]);
});

test('Every research direction has a decorative icon', () => {
  assert.equal(Object.keys(researchIconPaths).length, 6);
  for (const name of Object.keys(researchIconPaths)) {
    assert.match(researchIcon(name), /aria-hidden="true" focusable="false"/);
  }
});
