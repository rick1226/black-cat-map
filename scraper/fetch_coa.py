"""抓取農業部動物認領養資料，篩出黑貓，寫入 docs/data/cats.json。

用法：
    COA_API_URL=<農業部 API 網址> python scraper/fetch_coa.py
"""

import datetime
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request
import urllib.robotparser

from normalize import build_cat

UA = "BlackCatMapBot/0.1 (+https://github.com/rick1226/black-cat-map)"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data" / "cats.json"


def robots_allows(url):
    parts = urllib.parse.urlsplit(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{parts.scheme}://{parts.netloc}/robots.txt")
    rp.read()  # 讀不到就丟出例外，由呼叫端決定停止
    return rp.can_fetch(UA, url)


def fetch_json(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    url = os.environ.get("COA_API_URL", "").strip()
    if not url:
        sys.exit("未設定 COA_API_URL（農業部動物認領養 API 網址）")

    try:
        allowed = robots_allows(url)
    except Exception as exc:  # 保守處理：讀不到 robots.txt 就不抓
        sys.exit(f"無法讀取 robots.txt，為安全起見停止爬取：{exc}")
    if not allowed:
        sys.exit("robots.txt 不允許抓取此網址，停止。")

    data = fetch_json(url)
    records = data.get("data", data) if isinstance(data, dict) else data
    if not isinstance(records, list):
        sys.exit("API 回傳格式不是清單，請確認網址與欄位規格。")

    # 以台北時間判斷截止日（GitHub Actions 跑在 UTC）
    taipei = datetime.timezone(datetime.timedelta(hours=8))
    today = datetime.datetime.now(taipei).date().isoformat()

    cats = [cat for cat in (build_cat(r, today) for r in records) if cat]
    cats.sort(key=lambda c: (c["county"] or "~", c["id"]))

    # 防呆：若這次抓到 0 筆，但先前已有資料，就不覆蓋，避免網站變空
    if not cats and OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        if previous.get("count", 0) > 0:
            sys.exit("本次結果為 0 筆，保留既有資料並停止。")

    payload = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "count": len(cats),
        "cats": cats,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"寫入 {len(cats)} 筆黑貓資料到 {OUT}")


if __name__ == "__main__":
    main()
