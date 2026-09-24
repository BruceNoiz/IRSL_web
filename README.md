# IRSL_web

Git 僅保存程式與不含個資的文件；原始素材、網站個資副本與含個資的驗收／交接檔保留在本機，排除清單與交接方式見 [Git 資料保護](docs/GIT_PRIVACY.md)。新 clone 必須另行取得本機資料才能完整開發、建置與驗收；目前 Actions 未配置私有資料來源。

要新增論文、課程、成員或照片，請先閱讀 [網站內容維護指南](docs/MAINTENANCE.md)，內含檔案位置、操作範例、中英文同步與預覽／發布步驟。

IRSL 實驗室網站，使用 Astro + React 建立首頁、教師介紹（`members/`）與實驗室成員（`team/`）三頁。研究方向在首頁，教師個人資料、成果與教學課程整合於教師頁，實驗室位置在共用頁尾，成員頁目前為博士生／碩士生各五個待補位置。網站為適用 GitHub Pages 的純前端靜態輸出。

依 [TASK](.agent/TASK.md) 的 2026-09-24 R1–R7，已實作首頁名稱／logo 與教師頂部重設計、單段簡介、博士及碩士兩學歷、返回控制移除，並將內容／元件／樣式／圖片按 home、faculty、team 聚合。原始素材保留，維護入口見 [src 說明](src/README.md)，來源與覆寫見 [CONTENT_MAP](docs/CONTENT_MAP.md)。

本次交付尚未完全達標：R6 角色圖片下載受阻，仍保留十個 SVG；新版視覺與使用者確認未完成。詳細檢查結果及限制見 [實作交接](docs/IMPLEMENTATION.md)，舊 APPROVED 不代表本輪完成。未部署或推送；版本仍為 1.0.0。

## 開始工作

1. 閱讀 [AGENTS.md](AGENTS.md) 的協作規則與 [harness 說明](docs/HARNESS.md)。
2. 讀取 [.agent/TASK.md](.agent/TASK.md) 的目前任務；新任務可參考 [任務範本](.agent/TASK.template.md) 記錄目標、範圍與驗收條件。
3. 完成修改後執行 `make check` 並保存結果，交由審查角色更新 [.agent/REVIEW.md](.agent/REVIEW.md)。

## 檢查指令

需要 Node.js 22.12 以上（建議 Node 24 LTS）、npm、Python 3.9 以上、Bash、Git 與 Make。Python 檢查使用標準函式庫；網站與瀏覽器檢查需先安裝以下依賴。CI 使用 Node 24 與 Python 3.13。循環回歸測試使用本機替身，不需模型 CLI 或登入。

首次安裝（需 npm registry 網路）：

```sh
npm ci
PLAYWRIGHT_BROWSERS_PATH=.agent/logs/playwright npx playwright install chromium
```

本機與 CI 都使用 `npm ci`，保留 `package-lock.json` 並與 `package.json` 一起納入版本控制；新增或更新依賴時才用 `npm install` 更新鎖定檔。Linux 如缺瀏覽器系統依賴，使用 `npx playwright install --with-deps chromium`，仍設定同一個 `PLAYWRIGHT_BROWSERS_PATH`。

安裝出現 `ENOTFOUND` 時，可用 `npm ping --registry=https://registry.npmjs.org/` 對照受限執行環境與一般終端機的連線。本次確認是沙箱網路限制；安裝需允許對外連線，瀏覽器驗收另需允許本機埠與瀏覽器程序。取得相應執行權限後再重跑，保留完整驗收門檻。 測試固定使用 4322、4324、4325 埠；啟動失敗時先檢查是否被其他程序占用，確認程序用途後再停止或調整，勿直接終止一般開發伺服器。

```sh
make check
```

沒有 Make 的環境可在專案根目錄執行：

```sh
python3 scripts/check.py
```

檢查依序包含儲存庫與循環回歸、素材映射、Markdown 轉換、原圖一致性與 Astro 型別檢查。接著對 `/`、`/nested/review-lab/` 及實際 `BASE_PATH`（預設 `/IRSL_web/`，重複路徑只檢查一次）各自建置、檢查 HTML 原文涵蓋與本地連結／錨點／資產，並執行 Chromium 桌面與行動版、React 選單、無 JavaScript 導覽、開發及預覽伺服器驗證。最後 `dist/` 保留實際目標路徑的版本。任一失敗回傳非零退出碼，不會因依賴缺少而略過網站檢查。未檢查外部網址可用性、其他瀏覽器或真實模型服務；通過也不代表 reviewer 核准。

僅跑 Python 標準函式庫的來源與儲存庫測試（不需要 Node 或 npm，不等於網站驗收）：

```sh
make check-source
```

有 Node 時可另執行 `node --test tests/*.test.mjs`，驗證共用 Markdown 轉換與原圖一致性，亦不需要 npm 安裝。

## 本機開發與建置

```sh
npm run dev
npm run check
npm run build
npm run preview
```

開發及預覽預設網址為 `http://localhost:4321/IRSL_web/`（埠號以終端機輸出為準）。預覽前需先建置。網站程式在 [src](src/README.md)，素材對應與內容解讀見 [CONTENT_MAP](docs/CONTENT_MAP.md)。

`npm run build` 的產物位於 `dist/`，每個頁面都有自己的 `index.html`，不需伺服器端路由或 API。網站正文從 `src/features/*/content/` 匯入；`artifact/` 只作來源追溯，不需同步維護兩份正文。網站圖片與模組共置，Astro 本地 import 產生含 BASE_PATH 的網址；原始 logo／照片位元組不變。原始 DOCX、Markdown 與素材索引不公開，網站沒有資料下載入口。

R7 維護驗證另執行 `python3 tests/check_maintenance.py`：暫時加入論文、課程、成員與照片，確認建置自動反映；最後還原來源與 `/IRSL_web/` 建置。紀錄位於 `.agent/logs/redesign-20260924/`。

## GitHub Pages 設定與後續部署

預設 `BASE_PATH=/IRSL_web/`。其他 repository 名稱或根網域需在建置、開發、預覽時使用相同設定，例如：

```sh
SITE_URL=https://example.github.io BASE_PATH=/my-lab/ npm run build
BASE_PATH=/my-lab/ npm run preview
python3 tests/check_static.py dist /my-lab/
PLAYWRIGHT_BROWSERS_PATH=.agent/logs/playwright BASE_PATH=/my-lab/ npm run test:browser
```

完整驗收其他路徑可執行 `BASE_PATH=/my-lab/ make check`；Playwright、靜態伺服器與 Astro 開發／預覽皆使用同一個 base。

`SITE_URL` 設為實際網域（不含 repository 子路徑），未提供時不輸出 canonical URL；`BASE_PATH` 使用前後都有斜線的 `/repository/`，根網域則為 `/`。導覽、Markdown 連結、圖片、CSS 與 React 腳本都須隨 base 生成。設定依 [Astro GitHub Pages 官方文件](https://docs.astro.build/en/guides/deploy/github/)。

若日後要發布，先確認 [實作交接](docs/IMPLEMENTATION.md) 的驗證結果與剩餘需求，並取得獨立審查，再由維護者將 repository 的 Settings → Pages → Source 設為 GitHub Actions，手動執行 [Publish GitHub Pages manually](.github/workflows/pages.yml)。此流程依 repository 名稱設定 `site/base` 後執行 `make check`，因此實際發布路徑也經過瀏覽器驗證，再上傳 `dist/` 並發布。一般 push／pull request 只執行 [檢查 CI](.github/workflows/check.yml)，不觸發發布。自訂網域需另調整工作流程的 `SITE_URL`／`BASE_PATH`。

本次沒有部署、推送或執行任何 GitHub Actions 工作流程。

## 執行代理循環

真正執行 [agent-loop.sh](agent-loop.sh) 另外需要 Make，以及已完成登入設定的 Codex CLI 與 Claude Code。執行後會依 `.agent/TASK.md` 修改專案，最多三輪；操作細節與日誌說明見 [harness 說明](docs/HARNESS.md#實作與審查循環)。

啟動前將指定的頁面／區段、預期修改及參考圖片路徑寫入 TASK；腳本不會自動繼承其他對話。Codex 負責依位置修改、設計及實測，Claude 同時審查內容位置與實際桌面／手機畫面。測試通過不等於視覺驗收，reviewer 核准也不代替使用者對新版的確認。

```sh
bash agent-loop.sh
```

每次模型或 `make check` 指令預設逾時 1800 秒；每次 Claude 審查預設最多 30 回合。兩者都可用正整數調整：

```sh
CLAUDE_MAX_TURNS=45 AGENT_TIMEOUT_SECONDS=3600 bash agent-loop.sh
```

若審查超限或中斷，可對目前檔案單獨重新檢查並審查：

```sh
CLAUDE_MAX_TURNS=45 bash agent-loop.sh --review-only
```

此模式重新執行 `make check`、保存目前差異並呼叫 Claude 一次，不呼叫 Codex、不沿用舊檢查結果，也不會自動接續實作。得到 `CHANGES_REQUESTED` 後，先查看 REVIEW，再以一般循環處理修正。審查失敗時會顯示 stdout／stderr 路徑與末尾內容，保留上一份有效 REVIEW。

每次執行的紀錄保存在獨立的 `.agent/logs/run-*/`。退出碼 `0` 表示本輪檢查通過且 reviewer 核准；`1` 表示指令、格式、儲存或逾時錯誤；`2` 表示三輪仍要求修改，或單次 `--review-only` 結果為 `CHANGES_REQUESTED`。停止不會還原已完成的程式修改。

## 專案地圖

| 位置 | 用途 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 共用協作規則與專案約定 |
| [CLAUDE.md](CLAUDE.md) | Claude 協作入口，專案約定引用 AGENTS.md |
| [.agent/](.agent/) | 目前任務、任務範本、審查結果與本機執行紀錄 |
| [agent-loop.sh](agent-loop.sh) | 實作／檢查／審查循環，使用 TASK 與 REVIEW |
| [scripts/agent_loop.py](scripts/agent_loop.py) | 指令逾時、審查格式驗證與原子替換 |
| [docs/HARNESS.md](docs/HARNESS.md) | 開發流程、驗證範圍與擴充方式 |
| [artifact/README.md](artifact/README.md) | 原始資料與 10 份網站內容素材索引 |
| [src/](src/) | Astro 頁面、React 導覽、共用版型、樣式與內容映射 |
| [astro.config.mjs](astro.config.mjs) | 靜態輸出、GitHub Pages base 與素材渲染設定 |
| [docs/CONTENT_MAP.md](docs/CONTENT_MAP.md) | 素材涵蓋與解讀假設 |
| [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) | 實作結果與尚未完成的驗證 |
| [tests/](tests/) | 可自動執行的驗收檢查 |
| [scripts/check.py](scripts/check.py) | 本機與 CI 共用的檢查入口 |
| [.github/workflows/check.yml](.github/workflows/check.yml) | GitHub Actions 檢查設定 |
