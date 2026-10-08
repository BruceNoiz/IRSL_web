# IRSL_web

IRSL 實驗室網站，使用 Astro + React 建立的純前端靜態網站，可部署於 GitHub Pages。

## Install

需要 Node.js 22.12 以上（建議 Node 24 LTS）與 npm。

```sh
npm ci
```

## Usage

```sh
npm run dev       # 本機開發，預設 http://localhost:4321/IRSL_web/
npm run check     # Astro 型別檢查
npm run build     # 建置至 dist/
npm run preview   # 預覽建置結果（需先 build）
```

預設 `BASE_PATH=/IRSL_web/`；其他路徑或網域可在建置時指定：

```sh
SITE_URL=https://example.github.io BASE_PATH=/my-lab/ npm run build
```

## 資料結構

```
src/
├── pages/               # 路由：首頁、教師（members）、成員（team），en/ 為英文版
├── features/
│   ├── home/            # 首頁：實驗室介紹、研究方向
│   │   └── content/     # introduction*.md、research*.md
│   ├── faculty/         # 教師頁：個人資料、論文、專利、獲獎、課程
│   │   └── content/     # profile.ts、academic.ts、journals.md、courses*.md …
│   └── team/            # 實驗室成員
│       └── content/     # members.ts
└── shared/              # 共用版型、導覽元件、樣式與工具函式
```

網站內容集中在各 `features/*/content/`，修改對應檔案後重新建置即可反映；`*.en.md` 為英文版內容。
