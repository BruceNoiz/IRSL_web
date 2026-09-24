# Git 資料保護

使用者提供的個人資料只保留在本機，不納入 Git。這包含原始文件，以及網站文字、照片、任務／審查記錄、文件和驗收程式中的資料副本。實際規則以 `.gitignore` 為準。

## 追蹤範圍

| 項目 | 處理方式 |
| --- | --- |
| `artifact/` | 整個目錄忽略，包含 Word、擷取文字、原圖及含個資的素材索引 |
| `src/features/*/assets/` | 本機圖片忽略，涵蓋未來新增的成員照片 |
| home、faculty、team 的 `content/` | 網站資料副本忽略；faculty 的 `labels.ts` 只有介面標籤，可追蹤 |
| `src/shared/content/site.ts`、`i18n.ts` | 包含聯絡資料及具名頁面摘要，保留本機 |
| `src/features/faculty/FacultyProfile.astro` | 目前圖片 import 路徑含姓名，整檔保留本機 |
| `.agent/TASK.md`、`.agent/REVIEW.md` | 含使用者資料與回饋，保留本機；不改寫 reviewer 意見 |
| `docs/CONTENT_MAP.md`、`IMPLEMENTATION.md`、`MAINTENANCE.md` | 含資料值、具名圖片路徑或內容副本，保留本機 |
| `tests/assets.test.mjs`、`browser/site.spec.mjs`、`check_static.py`、`check_maintenance.py`、`test_site.py` | 目前嵌入真實資料或具名照片路徑，保留本機，仍可於本機執行 |
| `src/content/` 中舊資料檔及舊個人頁面 | 移除殘留索引，忽略已淘汰的資料位置，避免重新加入 |
| 建置、瀏覽器報告、截圖、`.agent/logs/` | 產物可能含個資，保持忽略；僅 logs 的空 `.gitkeep` 可追蹤 |
| 其餘版型、樣式、共用工具、無個資測試、套件鎖定檔與 CI 設定 | 保持可追蹤；提交前仍須檢查是否新增了資料值 |

本次採用保留本機檔案、只調整忽略規則及索引的方式，不改寫網站內容，也不將真實資料改成範例值。被排除的元件、測試及文件不是刪除的功能；日後若需納入 Git，應先將資料與具名路徑抽離，再檢查內容。

## 本機、交接與 CI

`git rm --cached` 只移除索引項目，本機檔案仍在。Git status 的 `D` 表示下一次提交會移除該路徑，不表示本機資料被刪除。忽略檔案不會包含在一般 `git add .`、clone 或 Git archive 中；需另行妥善備份。

新工作目錄或 CI runner 只有 Git 檔案，**不能直接建置完整網站或執行完整驗收**。維護者需要經適當的私下交接，把上述本機資料放回原路徑，再依 README 安裝依賴及執行 `make check`。目前 GitHub Actions 沒有資料注入設定；不得為了讓 CI 通過而強制加入個資，亦不降低現有驗收門檻。這次未新增資料上傳、雲端備份或部署。

Git 忽略不會改變網站輸出。若日後建置並發布，網站原本顯示的資料與照片仍會出現在發布產物中；此規則保護的是 Git 追蹤範圍。

## 提交前檢查

```sh
git status --short --untracked-files=all
git diff --stat
git diff --cached --stat
git ls-files -ci --exclude-standard
git ls-files -- artifact src/features/faculty/assets src/features/team/content
git diff --check
git diff --cached --check
```

兩個 `git ls-files` 檢查都應沒有輸出。`-ci --exclude-standard` 能找出已被忽略規則涵蓋、卻仍在索引中的檔案。新增檔案也要直接閱讀；不要用 `git add -f` 繞過個資規則，不要將資料抄到未排除的元件、註解或測試中。忽略規則依路徑生效，不是自動個資辨識器。

## 提交歷史與本次驗證

本機既有的兩筆提交已包含原始資料。移出索引及增加 `.gitignore` **不會清除舊提交、tag、reflog 或其他備份中的資料**。本次不改寫歷史、不建立提交、不推送；盤點時未設定 Git remote，因此無法據此判斷是否曾有其他分享副本。完整歷史清除需另外界定保留的版本及備份範圍。

驗證結果於本次整理完成後補記；不在此文件記錄實際姓名、聯絡值或資料內容。
