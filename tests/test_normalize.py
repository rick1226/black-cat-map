import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scraper"))

from normalize import COUNTIES, build_cat, county_of  # noqa: E402

TODAY = "2026-11-20"


class CountyTests(unittest.TestCase):
    def test_has_22_counties(self):
        self.assertEqual(len(COUNTIES), 22)

    def test_traditional_and_simplified_taipei(self):
        self.assertEqual(county_of("台北市大安區"), "臺北市")

    def test_similar_names_not_confused(self):
        self.assertEqual(county_of("新竹縣竹北市"), "新竹縣")
        self.assertEqual(county_of("新竹市東區"), "新竹市")
        self.assertEqual(county_of("嘉義縣太保市"), "嘉義縣")
        self.assertEqual(county_of("嘉義市西區"), "嘉義市")

    def test_first_text_has_priority(self):
        self.assertEqual(county_of("高雄市左營區", "臺南市"), "高雄市")

    def test_unknown_returns_none(self):
        self.assertIsNone(county_of("不明地點"))


class BlackCatTests(unittest.TestCase):
    def test_black_cat_kept_with_county(self):
        raw = {
            "animal_id": "1",
            "animal_kind": "貓",
            "animal_colour": "黑色",
            "animal_title": "小黑",
            "shelter_address": "新北市板橋區某路1號",
        }
        cat = build_cat(raw, TODAY)
        self.assertIsNotNone(cat)
        self.assertEqual(cat["id"], "coa-1")
        self.assertEqual(cat["county"], "新北市")

    def test_dog_dropped(self):
        raw = {"animal_id": "2", "animal_kind": "狗", "animal_colour": "黑"}
        self.assertIsNone(build_cat(raw, TODAY))

    def test_other_colour_dropped(self):
        raw = {"animal_id": "3", "animal_kind": "貓", "animal_colour": "橘"}
        self.assertIsNone(build_cat(raw, TODAY))

    def test_black_white_not_counted_as_black(self):
        raw = {"animal_id": "4", "animal_kind": "貓", "animal_colour": "黑白色"}
        self.assertIsNone(build_cat(raw, TODAY))

    def test_mixed_black_colours_not_counted(self):
        # 資料中常見的混色：黑棕、黑黃、黑虎斑、黑灰等，都不算黑貓
        for colour in ["黑棕色", "黑黃色", "黑虎斑色", "黑灰色", "咖啡黑色"]:
            raw = {"animal_id": "40", "animal_kind": "貓", "animal_colour": colour}
            self.assertIsNone(build_cat(raw, TODAY), colour)

    def test_missing_id_dropped(self):
        raw = {"animal_kind": "貓", "animal_colour": "黑"}
        self.assertIsNone(build_cat(raw, TODAY))

    def test_title_fallback_when_no_colour(self):
        raw = {"animal_id": "5", "animal_kind": "貓", "animal_title": "黑貓小花"}
        cat = build_cat(raw, TODAY)
        self.assertIsNotNone(cat)
        self.assertEqual(cat["colour"], "（依標題判斷為黑色）")

    def test_chinese_field_names(self):
        raw = {
            "animal_id": "9",
            "動物的類型": "貓",
            "動物毛色": "黑",
            "動物的實際所在地": "臺中市西屯區",
        }
        cat = build_cat(raw, TODAY)
        self.assertEqual(cat["county"], "臺中市")

    def test_county_none_when_unknown(self):
        raw = {"animal_id": "10", "animal_kind": "貓", "animal_colour": "黑"}
        cat = build_cat(raw, TODAY)
        self.assertIsNone(cat["county"])

    def test_numeric_id_accepted(self):
        # 官方 API 的 animal_id 是數字，不是字串
        raw = {"animal_id": 475108, "animal_kind": "貓", "animal_colour": "黑色"}
        cat = build_cat(raw, TODAY)
        self.assertEqual(cat["id"], "coa-475108")


class AdoptionStatusTests(unittest.TestCase):
    def base(self, **extra):
        raw = {"animal_id": "20", "animal_kind": "貓", "animal_colour": "黑色"}
        raw.update(extra)
        return raw

    def test_open_status_kept(self):
        self.assertIsNotNone(build_cat(self.base(animal_status="OPEN"), TODAY))

    def test_non_open_status_dropped(self):
        self.assertIsNone(build_cat(self.base(animal_status="CLOSED"), TODAY))

    def test_far_future_close_date_kept(self):
        raw = self.base(animal_status="OPEN", animal_closeddate="2999-12-31")
        self.assertIsNotNone(build_cat(raw, TODAY))

    def test_past_close_date_dropped(self):
        raw = self.base(animal_status="OPEN", animal_closeddate="2026-11-01")
        self.assertIsNone(build_cat(raw, TODAY))


class DisplayTests(unittest.TestCase):
    def test_name_falls_back_to_subid(self):
        raw = {
            "animal_id": "30",
            "animal_subid": "115-B095D",
            "animal_kind": "貓",
            "animal_colour": "黑色",
            "animal_title": "",
        }
        self.assertEqual(build_cat(raw, TODAY)["name"], "收容編號 115-B095D")

    def test_sex_mapped_to_label(self):
        raw = {"animal_id": "31", "animal_kind": "貓", "animal_colour": "黑", "animal_sex": "F"}
        self.assertEqual(build_cat(raw, TODAY)["sex"], "母")


if __name__ == "__main__":
    unittest.main()
