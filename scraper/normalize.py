"""把農業部動物認領養的原始資料轉成統一格式，並只保留黑貓。"""

COUNTIES = (
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "基隆市", "新竹市", "嘉義市",
    "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣",
    "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣",
)

COA_PAGE = "https://data.coa.gov.tw/Query/ServiceTransDetail.aspx?id=QcbUEzN6E6DL"


def _canon(text):
    # 「台」與「臺」混用很常見，統一成「臺」再比對
    return (text or "").replace("台", "臺")


def county_of(*texts):
    """依序檢查每段文字，回傳第一個找到的縣市名稱；找不到回傳 None。"""
    for text in texts:
        canon = _canon(text)
        for county in COUNTIES:
            if county in canon:
                return county
    return None


def _get(raw, *keys):
    """依序嘗試多個欄位名稱（英文或中文），回傳第一個有值的字串。"""
    for key in keys:
        value = raw.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


BLACK_COLOURS = {"黑色", "黑"}


def is_black_cat(kind, colour, title):
    """黑貓 = 貓，且毛色正好是「黑色」。
    黑棕、黑黃、黑虎斑、黑白等混色不算黑貓（資料中這類混色超過 400 隻，刻意排除）。
    沒有毛色欄位時，退而看標題是否含「黑」且不含「白」。"""
    is_cat = "貓" in kind or kind.lower() == "cat"
    if not is_cat:
        return False
    if colour:
        return colour.strip() in BLACK_COLOURS
    return "黑" in title and "白" not in title


SEX_LABEL = {"M": "公", "F": "母"}


def is_open_for_adoption(raw, today):
    """狀態為 OPEN，且開放認養截止日尚未過（沒有截止日或 2999-12-31 視為未截止）。
    today 為 'YYYY-MM-DD' 字串。"""
    status = _get(raw, "animal_status", "動物狀態").upper()
    if status and status != "OPEN":
        return False
    closed = _get(raw, "animal_closeddate", "開放認養時間(迄)")
    if closed and closed < today:
        return False
    return True


def build_cat(raw, today):
    """回傳統一格式的一筆資料；不是黑貓、未開放認養或缺少編號時回傳 None。"""
    animal_id = _get(raw, "animal_id")
    if not animal_id:
        return None

    kind = _get(raw, "animal_kind", "動物的類型")
    colour = _get(raw, "animal_colour", "動物毛色")
    title = _get(raw, "animal_title")
    if not is_black_cat(kind, colour, title):
        return None
    if not is_open_for_adoption(raw, today):
        return None

    subid = _get(raw, "animal_subid", "動物的收容編號")
    address = _get(raw, "shelter_address")
    place = _get(raw, "animal_place", "動物的實際所在地")
    shelter = _get(raw, "shelter_name")
    sex = _get(raw, "animal_sex", "動物性別")

    return {
        "id": f"coa-{animal_id}",
        "name": title or (f"收容編號 {subid}" if subid else f"編號 {animal_id}"),
        "kind": kind,
        "colour": colour or "（依標題判斷為黑色）",
        "sex": SEX_LABEL.get(sex, ""),
        "age": _get(raw, "animal_age", "動物年紀"),
        "county": county_of(address, place, shelter),
        "shelter": shelter,
        "address": address,
        "image": _get(raw, "album_file"),
        "source": "農業部動物認領養",
        "url": COA_PAGE,
    }
