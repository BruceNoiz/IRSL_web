# 基礎 harness 驗證記錄

## 範圍

- 任務：補充 IRSL_web 基礎 harness 架構。
- 日期：2026-09-20。
- 環境：macOS、Python 3.9.6、GNU Make 3.81；無第三方 Python 依賴。
- 交付內容：專案指引、任務範本、審查協定、共用檢查入口、儲存庫驗收測試與 CI 設定。
- 保留工作期間新增的 TASK 網站需求及 `agent-loop.sh`；未執行網站任務或代理循環。

## 驗證證據

| 指令或檢查 | 實際結果 |
| --- | --- |
| `make check` | 5 組測試通過，退出碼 0 |
| 在其他工作目錄以絕對路徑執行 `scripts/check.py` | 5 組測試通過，退出碼 0 |
| 隔離副本中修改資料後執行 `make check` | 下列 11 個情境均回傳預期錯誤；Make 退出碼皆為 2 |
| 原始素材 SHA-256 比對 | 原有 13 份正式素材全數一致；不含 Word 自動管理的 `~$` 暫存鎖定檔 |
| Ruby YAML 載入 workflow | 可解析且檢查步驟為 `make check`；僅為設定檔檢查 |
| `make help` | 正確顯示檢查指令 |
| `bash -n agent-loop.sh` | Shell 語法檢查通過；未呼叫模型 CLI |
| 新增與修改的 harness 文件／程式空白檢查 | 通過；包含尚未被 Git 追蹤的檔案 |

隔離驗證以 Python `tempfile` 建立專案副本，每次只改一個條件，再以 `subprocess` 執行 `make check` 並檢查退出碼與錯誤訊息；未修改原始素材。

1. 刪除 `.agent/TASK.md`：回報缺少必要檔案。
2. 刪除教師照片：回報本地連結目標不存在。
3. 刪除索引中的基本介紹列：回報素材未列入索引。
4. 清空基本介紹 Markdown：回報缺少文件標題。
5. 加入非 UTF-8 的 Markdown：回報編碼錯誤。
6. 加入指向專案外的本地連結：回報連結超出專案目錄。
7. 移除所有測試檔：回報找不到測試。
8. 移除 `tests/`：回報缺少測試目錄。
9. 加入語法錯誤的測試檔：測試載入失敗，回報語法錯誤。
10. 將 REVIEW 第一行改為未知狀態：回報審查狀態錯誤。
11. 移除 REVIEW 必要區段：回報缺少審查區段。

本機摘要另存於 `.agent/logs/fault-checks.json`（已忽略，不是唯一驗證紀錄）。

## 限制與交接

- GitHub Actions 尚未在遠端執行。
- 尚無網站應用程式，未執行網站建置或瀏覽器測試。
- `agent-loop.sh` 的模型 CLI 呼叫與獨立審查尚未驗證；後續審查仍需處理 untracked 檔案不會出現在 `git diff` 的情況。
- 本地連結檢查的支援格式與略過項目見 [harness 說明](../docs/HARNESS.md)。
- 下一步：依 TASK 實作 Astro + React 靜態網站，再將建置與頁面行為檢查接入 `make check`。
