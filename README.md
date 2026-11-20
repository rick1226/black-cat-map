# 黑貓認養地圖

彙整台灣公開的黑貓認養資訊，依縣市篩選。架構刻意保持最低成本：沒有資料庫、沒有後端、沒有付費 API。

## 架構

- `scraper/fetch_coa.py`：抓取農業部動物認領養資料，篩出黑貓，輸出 `docs/data/cats.json`。
- `scraper/normalize.py`：欄位轉換、縣市判斷、黑貓判斷。
- `docs/`：純靜態網頁（HTML + JavaScript），由 GitHub Pages 發佈。
- `.github/workflows/crawl.yml`：每天一次（台北時間 09:17）在 GitHub 雲端執行測試、抓資料、部署頁面。執行時不需要你的電腦開機。

## 本機執行

```bash
# 1. 測試（不需網路）
python -m unittest discover -s tests -v

# 2. 抓資料（需要 API 網址）
COA_API_URL="<農業部 API 網址>" python scraper/fetch_coa.py

# 3. 預覽網頁
cd docs && python -m http.server 8000
```

## 上線設定

1. 把專案推到 GitHub 公開 repo。
2. 在 repo 的 Settings → Pages，Source 選 **GitHub Actions**。
3. 在 Settings → Secrets and variables → Actions → Variables，新增 `COA_API_URL`。
4. 手動執行一次 `crawl-and-deploy` workflow 確認。

## 待辦（上線前必做）

- [x] 確認農業部 API 網址與回傳欄位（已用實際資料 8711 筆驗證，欄位與程式一致，回傳為單一清單）。
- [x] 把 `scraper/fetch_coa.py` 的 User-Agent 聯絡資訊換成 repo 網址。
- [ ] 確認 API 是否會分頁（目前一次回傳全部 8711 筆，尚未遇到分頁）。
- [ ] 確認授權條款，網站頁尾標示資料來源。
- [ ] 加入更多來源（各縣市動保處、台灣認養地圖等），每個來源先確認 robots.txt 與使用條款。
- [ ] 下架判斷與跨來源去重。

## 已做的選擇（可以再調整）

- **黑貓定義**：貓，且毛色正好是「黑色」。黑白、黑棕、黑虎斑等混色不納入（以目前資料估計約 79 隻）。
- **沒有毛色欄位時**：才退而看標題是否含「黑」。
- **縣市判斷**：依收容所地址、地點、收容所名稱比對 22 個縣市名稱，「台」統一視為「臺」。
- **圖片**：直接引用原站的圖片網址，不轉存。
