// Temporary decorative icons, keyed by the exact research direction in content/research.md.
// Replace a path here to update its icon everywhere; all icons use a 32 × 32 viewBox.
export const researchIconPaths = {
  '建築節能與環境控制': 'M5 27V12l11-7 11 7v15H5Zm7 0v-8h8v8M11 13h2m6 0h2M17 2l-3 7h5l-3 7',
  '室內空氣品質與熱舒適': 'M4 10h16a4 4 0 1 0-4-4M4 16h22a3 3 0 1 1-3 3M4 22h10a4 4 0 1 1-4 4',
  '智慧感測與設備控制': 'M11 11h10v10H11ZM16 3v4m0 18v4M3 16h4m18 0h4M8 8l3 3m10 10 3 3M24 8l-3 3M11 21l-3 3M14 16h4',
  '建築資訊模型': 'M16 3 29 10 16 17 3 10 16 3Zm-13 7v12l13 7 13-7V10M16 17v12M9 7l14 7v11M23 7 9 14v11',
  '演算法與資源最佳化': 'M5 5h6v6H5Zm16 0h6v6h-6ZM13 21h6v6h-6ZM11 8h10M8 11v5h8v5m8-10v5h-8',
  '都市氣候與公共風險溝通': 'M3 28V15h8v13m0 0V9h8v19m0 0V19h10v9M1 28h30M23 3v3m6 0-2 2M25 10a3 3 0 1 0-5 2M6 19h2m-2 4h2m6-10h2m-2 5h2m8 5h2',
};

export function researchIcon(name) {
  const path = researchIconPaths[name];
  if (!path) throw new Error(`Missing research icon: ${name}`);
  return `<svg class="research-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="${path}" /></svg>`;
}
