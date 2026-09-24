# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## 5. IRSL_web 專案約定

- 專案現況與目錄入口見 [README.md](README.md)，開發流程見 [docs/HARNESS.md](docs/HARNESS.md)。目前已有網站素材，網站需求以 [.agent/TASK.md](.agent/TASK.md) 為準。
- 開始任務前讀取 TASK；開新任務時可參考 [.agent/TASK.template.md](.agent/TASK.template.md)，列出目標、範圍、假設及驗收方式。保留使用者在工作期間新增的需求。
- [.agent/REVIEW.md](.agent/REVIEW.md) 由審查角色更新，第一行使用 `APPROVED` 或 `CHANGES_REQUESTED`，後接 `Blocking Issues`、`Important Issues`、`Suggestions`、`Explanation` 四個二級標題。實作角色記錄實際驗證結果與限制，不自行核准。
- 網站程式碼放在 `src/`，自動檢查放在 `tests/`；共用檢查入口為 `make check`，亦可執行 `python3 scripts/check.py`。
- 原始 `artifact/基本資料.docx` 與擷取照片是素材來源；除非任務要求修改來源，保留原檔。編輯素材時同步維護 [artifact/README.md](artifact/README.md) 與相關連結，不自行推測學經歷、論文或課程資訊。
- 任務產生的暫存輸出放在 `.agent/logs/`；交付時提供指令、結果與限制供審查角色寫入 REVIEW，不以被忽略的本機日誌作為唯一紀錄。
- 新增工具、依賴或網站框架時，同步更新安裝方式、檢查指令與 CI。檢查尚未實作或未執行時要明確記錄。
- 審查同時查看 `git diff` 與 `git status --short --untracked-files=all`；未追蹤檔案需要直接閱讀，不能視為沒有變更。
- 網頁不得新增或保留編輯／製作過程的提示句，例如「這邊先保留」「內容待補」「以下列出 12 篇」「共 12 篇，依原文件順序列出」，也不可改寫成同義提示。待補事項、整理方式與實作說明只記在 TASK、素材映射或實作交接等專案文件，不直接把素材中的編輯註記帶入網頁。Agent 完成任務及審查前，須逐頁檢視實際畫面與建置輸出文字，確認全站沒有這類提示句；仍有遺留即不符合完成條件。
