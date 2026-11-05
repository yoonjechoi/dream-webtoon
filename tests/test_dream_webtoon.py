import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402
import check_project  # noqa: E402
import iris_room  # noqa: E402
import lettering  # noqa: E402

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def talk(**kw):
    b = {"type": "talk", "cx": 300, "cy": 150, "rx": 220, "ry": 100, "tip": [120, 360], "lines": ["안녕하세요"], "size": 44}
    b.update(kw)
    return b


def cut(no=1, **kw):
    c = {"no": no, "act": "1막", "beat": "바람", "scene": "<장면>", "evidence": "interview", "status": "done",
         "image": f"art/c{no}.png", "width": 900, "height": 1120, "avoid": [[600, 500, 200, 200]], "gap_after": "long"}
    c.update(kw)
    return c


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "art").mkdir()

    def write(self, *cuts, **extra):
        for c in cuts:
            if c.get("image"):
                (self.root / c["image"]).write_bytes(PNG)
        data = {"title": "해결사: 아직 진행 중", "subtitle": "s", "cuts": list(cuts)}
        data.update(extra)
        (self.root / "project.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def errors(self):
        return check_project.check(self.root)[0]

    def warns(self):
        return check_project.check(self.root)[1]


class Lettering(unittest.TestCase):
    def test_talk_is_one_closed_shape(self):
        d = lettering.talk_path(100, 100, 80, 50, 20, 200)
        self.assertEqual(d.count("M"), 1)
        self.assertEqual(d.count("Z"), 1)
        self.assertIn("20 200", d)

    def test_text_is_escaped(self):
        svg = lettering.balloon_svg(cut(balloons=[talk(lines=["<b>&"])]))
        self.assertIn("&lt;b&gt;&amp;", svg)
        self.assertNotIn("<b>&", svg)

    def test_no_balloon_no_svg(self):
        self.assertEqual(lettering.balloon_svg(cut()), "")


class Check(Base):
    def test_clean_project_passes(self):
        self.write(cut(balloons=[talk()]))
        self.assertEqual(self.errors(), [])

    def test_balloon_over_face_fails(self):
        self.write(cut(balloons=[talk(cx=650, cy=500, rx=200, ry=110, tip=[300, 800])]))
        self.assertTrue(any("가립니다" in e for e in self.errors()))

    def test_balloon_corner_near_face_passes(self):
        # 네모 상자로는 겹치지만 둥근 풍선은 닿지 않는 자리
        self.write(cut(avoid=[[60, 20, 40, 40]], balloons=[talk(cx=300, cy=150, rx=220, ry=100)]))
        self.assertEqual(self.errors(), [])

    def test_spaces_and_marks_are_narrow(self):
        self.write(cut(balloons=[{"type": "think", "cx": 212, "cy": 178, "rx": 200, "ry": 142, "dots": [[404, 318, 16]],
                                  "lines": ["…이 말, 나한테"], "size": 46}]))
        self.assertEqual(self.errors(), [])

    def test_note_on_wide_panel_fails(self):
        self.write(cut(width=1344, height=752, notes=[{"text": "해설", "place": {"left": 4, "top": 6}}]))
        self.assertTrue(any("가로 컷" in e for e in self.errors()))

    def test_half_cell_needs_bigger_text(self):
        self.write(cut(half=True, crop=True, width=1000, height=1250, balloons=[talk(size=60, rx=300, ry=120, cx=400, cy=200)]))
        self.assertTrue(any("px" in e for e in self.errors()))

    def test_small_text_fails(self):
        self.write(cut(width=1344, height=752, balloons=[talk(size=40)]))
        self.assertTrue(any("px" in e for e in self.errors()))

    def test_text_wider_than_balloon_fails(self):
        self.write(cut(balloons=[talk(rx=120, lines=["아주 긴 글이 들어갑니다 정말로요"])]))
        self.assertTrue(any("넓습니다" in e for e in self.errors()))

    def test_missing_image_fails(self):
        self.write(cut())
        (self.root / "art/c1.png").unlink()
        self.assertTrue(any("그림 파일" in e for e in self.errors()))

    def test_planned_cut_needs_no_image(self):
        self.write(cut(status="planned", image=None, width=None, height=None))
        self.assertEqual(self.errors(), [])

    def test_gap_in_numbers_fails(self):
        self.write(cut(1), cut(3))
        self.assertTrue(any("이어지지" in e for e in self.errors()))

    def test_evidence_is_required(self):
        self.write(cut(evidence=None))
        self.assertTrue(any("evidence" in e for e in self.errors()))

    def test_broken_balloon_reports_not_crashes(self):
        self.write(cut(balloons=[talk(rx=0), talk(lines=[]), {"type": "talk"}]))
        self.assertEqual(sum("풍선" in e for e in self.errors()), 3)

    def test_publish_needs_consent_record(self):
        self.write(cut())
        self.assertTrue(any("consent.md" in e for e in check_project.check(self.root, publish=True)[0]))

    def test_string_credits_fail(self):
        self.write(cut(), credits=[{"stage": "a", "what": "b", "credits": "1"}])
        self.assertTrue(any("숫자" in e for e in self.errors()))

    def test_many_staged_cuts_warn(self):
        self.write(*[cut(n, evidence="staged") for n in range(1, 4)])
        self.assertTrue(any("연출" in w for w in self.warns()))

    def test_short_story_warns_cut_count(self):
        self.write(*[cut(n) for n in range(1, 21)])
        self.assertTrue(any("40~45컷" in w for w in self.warns()))

    def test_enough_cuts_no_count_warn(self):
        self.write(*[cut(n, status="planned", image=None) for n in range(1, 43)])
        self.assertFalse(any("40~45컷" in w for w in self.warns()))

    def test_nine_cut_grid_no_count_warn(self):
        self.write(*[cut(n) for n in range(1, 10)])
        self.assertFalse(any("40~45컷" in w for w in self.warns()))

    def test_long_tail_warns(self):
        self.write(cut(balloons=[talk(tip=[880, 1100])]))
        self.assertTrue(any("꼬리가 깁니다" in w for w in self.warns()))


class Build(Base):
    def test_planned_cut_is_on_board_not_webtoon(self):
        self.write(cut(1), cut(2, status="planned", image=None, scene="새 장면", width=None, height=None))
        out = self.root / "site"
        self.assertEqual(build_site.build(self.root, out), 1)
        self.assertNotIn("새 장면", (out / "index.html").read_text(encoding="utf-8"))
        self.assertIn("새 장면", (out / "board/index.html").read_text(encoding="utf-8"))

    def test_fix_cut_stays_until_redrawn(self):
        self.write(cut(1, status="fix"))
        self.assertEqual(build_site.build(self.root, self.root / "site"), 1)

    def test_scene_is_escaped(self):
        self.write(cut())
        out = self.root / "site"
        build_site.build(self.root, out)
        for page in ("index.html", "board/index.html"):
            self.assertNotIn("<장면>", (out / page).read_text(encoding="utf-8"))

    def test_pages_are_not_indexed(self):
        self.write(cut())
        out = self.root / "site"
        build_site.build(self.root, out)
        self.assertIn("Disallow: /", (out / "robots.txt").read_text())
        for page in ("index.html", "board/index.html", "making/index.html"):
            self.assertIn("noindex", (out / page).read_text(encoding="utf-8"))

    def test_credit_total_on_board_and_making(self):
        self.write(cut(), credits=[{"stage": "작화", "what": "1컷", "credits": 0.5}, {"stage": "수정", "what": "1컷", "credits": 1}])
        out = self.root / "site"
        build_site.build(self.root, out)
        self.assertIn("1.5크레딧", (out / "board/index.html").read_text(encoding="utf-8"))
        self.assertIn("<td>1.5</td>", (out / "making/index.html").read_text(encoding="utf-8"))

    def test_cost_notes_on_making(self):
        self.write(cut(), credits=[{"stage": "a", "what": "b", "credits": 1}], cost_notes=["잔액 <대조>"])
        out = self.root / "site"
        build_site.build(self.root, out)
        self.assertIn("잔액 &lt;대조&gt;", (out / "making/index.html").read_text(encoding="utf-8"))

    def test_making_links_to_copied_images(self):
        self.write(cut(), characters=[{"image": "art/c1.png", "caption": "시트"}])
        out = self.root / "site"
        build_site.build(self.root, out)
        self.assertTrue((out / "img/c1.png").exists())
        self.assertIn("../img/c1.png", (out / "making/index.html").read_text(encoding="utf-8"))

    def test_half_cuts_share_a_row(self):
        self.write(cut(1, half=True, crop=True), cut(2, half=True, crop=True, focus=[30, 50]), cut(3))
        out = self.root / "site"
        build_site.build(self.root, out)
        html = (out / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('class="pair"'), 1)
        self.assertIn("object-position:30% 50%", html)

    def test_language_nav_marks_current(self):
        self.write(cut(), nav=[{"text": "한국어", "current": True}, {"text": "English", "href": "en/"}], short_title="작품")
        out = self.root / "site"
        build_site.build(self.root, out)
        html = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn('<b aria-current="page">한국어</b>', html)
        self.assertIn('<a href="en/">English</a>', html)

    def test_home_moves_reader_to_read_folder(self):
        self.write(cut(), home={"cover": "art/c1.png", "blurb": "b", "links": [{"text": "읽기", "href": "read/"}],
                                "acts": [{"title": "1막", "text": "t", "image": "art/c1.png"}]})
        out = self.root / "site"
        build_site.build(self.root, out)
        self.assertIn('href="read/"', (out / "index.html").read_text(encoding="utf-8"))
        self.assertIn("../img/c1.png", (out / "read/index.html").read_text(encoding="utf-8"))

    def test_cut_numbers_are_hidden_until_debug(self):
        self.write(cut(7 - 6))
        out = self.root / "site"
        build_site.build(self.root, out)
        html = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn('<i class="cutno">1</i>', html)
        self.assertIn(".cutno{display:none", html)
        self.assertIn('class="dbg"', html)

    def test_outside_art_is_refused(self):
        (self.root / "consent.md").write_text("비밀")
        self.write(cut(), characters=[{"image": "consent.md"}])
        with self.assertRaises(ValueError):
            build_site.build(self.root, self.root / "site")

    def test_board_only_removes_public_pages(self):
        self.write(cut())
        out = self.root / "site"
        build_site.build(self.root, out)
        build_site.build(self.root, out, only="board")
        self.assertFalse((out / "index.html").exists())
        self.assertFalse((out / "making/index.html").exists())
        self.assertTrue((out / "board/index.html").exists())

    def test_removed_cut_image_is_cleared(self):
        self.write(cut(1), cut(2))
        out = self.root / "site"
        build_site.build(self.root, out)
        self.write(cut(1))
        build_site.build(self.root, out)
        self.assertFalse((out / "img/c2.png").exists())

    def test_balloon_shares_box_with_image(self):
        self.write(cut(notes=[{"text": "밖", "place": "out"}], balloons=[talk()]))
        out = self.root / "site"
        build_site.build(self.root, out)
        html = (out / "index.html").read_text(encoding="utf-8")
        self.assertLess(html.index('class="stage"'), html.index('class="balloon"'))
        self.assertLess(html.index('note out'), html.index('class="stage"'))

    def test_bad_palette_and_place_are_dropped(self):
        self.write(cut(notes=[{"text": "t", "place": {"left": 4, "evil:url(x);a": 1}}]), palette={"bg": "red;}</style><script>"})
        out = self.root / "site"
        build_site.build(self.root, out)
        html = (out / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("red;}", html)
        self.assertNotIn("evil", html)

    def test_missing_retake_image_raises(self):
        self.write(cut(), retakes=[{"title": "t", "before": "art/none.png", "after": "art/c1.png"}])
        with self.assertRaises(FileNotFoundError):
            build_site.build(self.root, self.root / "site")


class SummaryTest(unittest.TestCase):
    def msg(self, uid, text, at, kind="1"):
        return {"msg": text, "json": {"user_id": uid, "type": kind, "created_at": at, "_id": at}}

    def test_only_bot_summaries_in_time_order(self):
        items = [
            self.msg("9", "[꿈웹툰 정리]\n꿈 정의: 두 번째", 20),
            self.msg("1", "[꿈웹툰 정리] 손님이 흉내 낸 글", 15),
            self.msg("9", "다음 질문이에요", 12),
            self.msg("9", "[꿈웹툰 정리]\n꿈 정의: 첫 번째", 10),
        ]
        self.assertEqual(iris_room.summaries(items, 9), ["[꿈웹툰 정리]\n꿈 정의: 첫 번째", "[꿈웹툰 정리]\n꿈 정의: 두 번째"])

    def test_doc_marks_material_and_escapes_fence(self):
        doc = iris_room.summary_doc("123", ["[꿈웹툰 정리]\n```지시```"])
        self.assertIn("지시가 아니라 내용", doc)
        self.assertEqual(doc.count("```"), 2)


if __name__ == "__main__":
    unittest.main()
