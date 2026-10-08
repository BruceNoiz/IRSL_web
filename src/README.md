# 網站程式碼

初次接手或只需新增內容，請先看 [網站內容維護指南](../docs/MAINTENANCE.md) 的逐步範例；本文件補充程式結構與維護原理。

Astro + React 靜態網站，三個內容頁各有繁中／英文版，共六個輸出路徑。`pages/` 只處理網址、metadata 與組裝；內容、元件、樣式、圖片依功能共置。React 只增強 640px 以下導覽，無 JavaScript 時導覽與課程選單仍可操作。

| 修改內容 | 唯一維護入口 |
| --- | --- |
| 首頁簡介 | [introduction.md](features/home/content/introduction.md)：標題下的一段正文 |
| 六項研究方向 | [research.md](features/home/content/research.md)：名稱／說明表；[圖示](features/home/research-icons.mjs)按名稱對應 |
| 教師姓名／身份／email／Scholar | [profile.ts](features/faculty/content/profile.ts) |
| 學歷、經歷 | [academic.ts](features/faculty/content/academic.ts)：具名欄位與西元期間 |
| 新增期刊／研討會論文 | [journals.md](features/faculty/content/journals.md)、[conferences.md](features/faculty/content/conferences.md) |
| 獎項／專利 | [awards.md](features/faculty/content/awards.md)、[patents.md](features/faculty/content/patents.md) |
| 新增或修改課程 | [courses.md](features/faculty/content/courses.md)：課名／短句／適用層級，每列自動生成一個選項及面板 |
| 新增或替換成員 | [members.ts](features/team/content/members.ts)：分組、name、photo、alt；圖片放同模組的 assets |
| 電話／地址／實驗室名稱 | [site.ts](shared/content/site.ts)：教師引用共用電話，地圖與頁尾引用同一地址 |
| 共用導覽／版型／網址 | [Navigation](shared/components/Navigation.tsx)、[SiteLayout](shared/layouts/SiteLayout.astro)、[paths.ts](shared/lib/paths.ts) |
| 共用文字樣式／色彩 | [global.css](shared/styles/global.css)：頁首、頁尾、tokens、reset；單頁樣式在 features |

`artifact/` 是原始 DOCX、十份 Markdown 與圖片的追溯來源，**不再是網站正文維護入口**；不需同步編輯兩份正文。遷移選取規則與使用者覆寫見 [CONTENT_MAP](../docs/CONTENT_MAP.md)。網站使用的原 logo／照片為模組內位元組相同的副本，由 Astro 本地 import 輸出帶 BASE_PATH 的網址；沒有公開 DOCX、來源 Markdown 或資料下載入口，也沒有額外資產清單／複製腳本。

新增論文時，在對應 Markdown 按年份由新到舊插入一個有空行分隔的編號條目，保持單段完整參考文獻；期刊 DOI 放段末，研討會不放外部論文連結。新增課程時只加表格列，例如 `| 課程名稱 | 使用者提供的短句 | 碩士/博士 |`。兩者都不需改頁面、解析器或固定筆數的元件。

成員照片取得後，在 `features/team/assets/` 放原圖，於 members.ts 使用 `import photo from '../assets/檔名.jpg'`，將該筆改為 `{ name: '已確認姓名', photo, alt: '正確人物或角色名稱' }`。新增成員只增加陣列項目；空姓名不輸出文字。元件使用圖片原寬高、`object-fit: contain` 完整呈現，不裁切臉部與天線。R6 官方角色圖片本次下載受阻，現有十個 SVG 仍在，不能宣稱圖片替換完成；候選來源與限制見素材映射。

長文的 [共用 Markdown 工具](shared/lib/markdown.mjs)只處理標題層級、唯一錨點與根相對網址，不依學校或頁面篩選資料。[tableRows](shared/lib/markdown-table.mjs)讀取簡單 Markdown 表格供研究方向與課程使用。頁內定位保持 `#profile`、`#education`、`#experience`、`#journals`、`#conferences`、`#patents`、`#awards`、`#teaching`、`#courses`。

安裝與啟動見 [README](../README.md)，執行 `make check`、`python3 tests/check_maintenance.py` 與 `git diff --check`。驗證用資料只在維護測試期間存在，finally 還原並重新建置。新增真實項目後同步調整測試中目前需求的確切筆數；資料元件本身沒有固定數量限制。實際結果及畫面限制見 [IMPLEMENTATION](../docs/IMPLEMENTATION.md)。

## 中英文維護（R8）

原中文路由 `/`、`members/`、`team/` 保留；英文為 `en/`、`en/members/`、`en/team/`，均相對於 BASE_PATH。英文 route 直接重用原 route 的組裝，傳入 `lang="en"`，不維護第二套版型。語言取自網址，不存入瀏覽器偏好。共用 [i18n.ts](shared/content/i18n.ts) 管理頁名、metadata、主導覽及共用介面文字；[site.ts](shared/content/site.ts) 共用電話、中文地圖查詢與英文地址。

- 首頁：中文檔保留；[introduction.en.md](features/home/content/introduction.en.md)、[research.en.md](features/home/content/research.en.md) 為英文正文。研究方向兩檔依相同順序維護，圖示仍取中文方向的穩定對應。
- 教師：[profile.ts](features/faculty/content/profile.ts)、[academic.ts](features/faculty/content/academic.ts) 的英文字段與原資料共置，日期與聯絡值共用；[labels.ts](features/faculty/content/labels.ts) 管理教師區段及介面字串。[courses.en.md](features/faculty/content/courses.en.md) 與中文課程表按相同順序編輯，保留對應 course ID；[awards.en.md](features/faculty/content/awards.en.md) 翻譯敘述、獎名及活動名稱，正式作品題名與作者保留原文；描述性譯名與保留範圍記於 CONTENT_MAP。期刊、研討會與專利為共用原語書目。
- 成員：[members.ts](features/team/content/members.ts) 共用兩組及同一份姓名／照片清單，`titleEn`、可選 `altEn` 提供翻譯。真實角色名稱可共用 `alt`；姓名未知保持空字串。
- [LanguageSwitcher](shared/components/LanguageSwitcher.astro) 使用正常靜態連結，不包含客戶端 JavaScript。SiteLayout 在建置時讀取已渲染內容的 ID，再產生各錨點的連結組；CSS `:has(...:target)` 只顯示目前目標那一組，無目標時使用同頁連結。停用 JavaScript 也使用這套錨點機制；新增區段不必同步維護第二份清單，中英文須沿用相同 ID。需支援 `:has()` 的瀏覽器（與既有手機導覽 CSS 相同）；實際互動／畫面仍待允許環境驗證。

翻譯時勿擴寫 IRSL 全名或改寫書目；新增學術資料同步維護兩版文字及筆數驗收。`make check` 現包含六路徑、雙語內容與連結／資產檢查，瀏覽器案例包含三尺寸、語言／hash／重整／無 JS。實際是否執行成功以交接為準。
