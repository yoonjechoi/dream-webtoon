#!/usr/bin/env python3
"""project.json 으로 웹툰 · 보드 · 메이킹북 페이지를 만든다.

사용법: build_site.py <프로젝트 폴더> [--out site] [--only board]
나오는 것: site/index.html(웹툰) · site/board/ · site/making/ · site/img/ · robots.txt
"""
import argparse
import html
import json
import re
import shutil
from pathlib import Path

from lettering import balloon_svg

GAPS = {"none": 0, "short": 14, "medium": 52, "long": 132, "xlong": 200}
STATUS = {"done": "완료", "doing": "진행 중", "waiting": "기다림"}
MARKS = {"planned": "★", "fix": "◆"}
FONTS = "https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Gowun+Dodum&family=Jua&display=swap"
PLACE_KEYS = ("left", "right", "top", "bottom", "width")
E = html.escape


def color(palette, key, default):
    value = palette.get(key, default)
    return value if re.fullmatch(r"#[0-9a-fA-F]{3,8}", str(value)) else default


def head(project, title, extra="", og_image=""):
    p = project.get("palette") or {}
    base = project.get("site_url", "").rstrip("/")
    og = f'<meta property="og:image" content="{E(base)}/{E(og_image)}">' if base and og_image else ""
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex">
<title>{E(title)}</title>
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(project.get('subtitle', ''))}">{og}
<link rel="stylesheet" href="{FONTS}">
<style>
:root{{--bg:{color(p, 'bg', '#a9d3f2')};--pale:{color(p, 'pale', '#e4f2fc')};--deep:{color(p, 'deep', '#1f5f94')};--ink:{color(p, 'ink', '#12283b')};--paper:{color(p, 'paper', '#ffffff')};--note-bg:{color(p, 'note_bg', '#ffffff')};--note-ink:{color(p, 'note_ink', '#12283b')};
--title:"Black Han Sans","Apple SD Gothic Neo",sans-serif;--talk:"Jua","Apple SD Gothic Neo",sans-serif;--note:"Gowun Dodum","Apple SD Gothic Neo",sans-serif;
--gl:max(16px,env(safe-area-inset-left,0px));--gr:max(16px,env(safe-area-inset-right,0px))}}
*{{box-sizing:border-box}}html,body{{margin:0}}img{{max-width:100%;display:block}}p{{margin:0}}
h1{{font:400 clamp(2.2rem,10vw,3.2rem)/1.14 var(--title);margin:0;text-wrap:balance}}
h2{{font:400 1.45rem/1.3 var(--title);margin:0 0 10px;color:var(--deep);text-wrap:balance}}
a{{color:var(--deep);font-weight:700}}a:focus-visible{{outline:3px solid var(--deep);outline-offset:2px}}
{extra}
</style></head><body>
"""


def note_html(note):
    place = note.get("place", "out")
    text = E(note["text"]).replace("\n", "<br>")
    if place == "out":
        return f'<figcaption class="note out">{text}</figcaption>'
    style = ";".join(f"{k}:{float(v):g}%" for k, v in place.items() if k in PLACE_KEYS)
    return f'<figcaption class="note" style="{style}">{text}</figcaption>'


def image_html(cut, prefix):
    focus = cut.get("focus") or [50, 50]
    style = f' style="object-position:{float(focus[0]):g}% {float(focus[1]):g}%"' if cut.get("crop") else ""
    alt = E(cut.get("scene", ""), quote=True)
    return f'<img src="{prefix}img/{Path(cut["image"]).name}" alt="{alt}" loading="lazy" width="{cut["width"]}" height="{cut["height"]}"{style}>'


def stage_html(cut, prefix):
    inside = "".join(note_html(n) for n in cut.get("notes") or [] if n.get("place", "out") != "out") + balloon_svg(cut)
    ratio = f' style="aspect-ratio:{cut["width"]}/{cut["height"]}"' if cut.get("crop") else ""
    cls = "stage crop" if cut.get("crop") else "stage"
    return f'<div class="{cls}"{ratio}>{image_html(cut, prefix)}{inside}</div>'


def out_notes(cut):
    return [n for n in cut.get("notes") or [] if n.get("place", "out") == "out"]


def cut_html(cut, prefix=""):
    cls = "panel full" if cut.get("full") else "panel frame"
    outside = "".join(note_html(n) for n in out_notes(cut))
    gap = GAPS.get(cut.get("gap_after", "medium"), 52)
    return f'<figure class="{cls}">{outside}{stage_html(cut, prefix)}</figure><div style="height:{gap}px"></div>'


def pair_html(left, right, prefix=""):
    """한 줄 2컷. 해설은 두 칸 위에 함께 놓아 칸 높이를 맞춘다."""
    notes = "".join(note_html(n) for n in out_notes(left) + out_notes(right))
    gap = GAPS.get(right.get("gap_after", "medium"), 52)
    cells = "".join(f'<figure class="panel frame">{stage_html(c, prefix)}</figure>' for c in (left, right))
    top = f'<div class="panel rowcap">{notes}</div>' if notes else ""
    return f'{top}<div class="pair">{cells}</div><div style="height:{gap}px"></div>'


def cuts_html(cuts, prefix=""):
    out, i = [], 0
    while i < len(cuts):
        if cuts[i].get("half") and i + 1 < len(cuts) and cuts[i + 1].get("half"):
            out.append(pair_html(cuts[i], cuts[i + 1], prefix))
            i += 2
        else:
            out.append(cut_html(cuts[i], prefix))
            i += 1
    return out


def webtoon(project, cuts, prefix="", home=""):
    css = """
body{background:var(--bg);color:var(--ink);font:17px/1.6 var(--note);padding-block:0 72px;padding-left:var(--gl);padding-right:var(--gr);overflow-x:hidden}
main{max-width:480px;margin:0 auto;display:flex;flex-direction:column}
header{padding-block:56px 40px;display:flex;flex-direction:column;gap:8px}
.en{font:400 1rem/1.3 var(--talk);color:var(--deep)}
.panel{margin:0;line-height:0;min-width:0}.stage{position:relative;overflow:hidden}.panel img{width:100%;height:auto}
.stage.crop img{height:100%;object-fit:cover}
.frame .stage{border-radius:var(--radius);border:var(--frame)}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.bar{display:flex;justify-content:space-between;align-items:center;padding-block:12px;font:400 1rem/1.3 var(--talk)}.bar a{text-decoration:none}
.links{display:flex;gap:6px}.links a,.links b{font:400 .95rem/1.2 var(--talk);padding:7px 12px;border-radius:999px;border:1.5px solid var(--deep)}.links b{background:var(--deep);color:var(--bg)}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}.btn{background:var(--deep);color:var(--bg);text-decoration:none;border-radius:999px;padding:9px 18px;font:400 1rem/1.3 var(--talk)}
.full{margin-left:calc(-1*var(--gl));margin-right:calc(-1*var(--gr))}
@media (min-width:520px){.full{margin-left:-24px;margin-right:-24px}}
.note{position:absolute;background:var(--note-bg);color:var(--note-ink);border:2.5px solid var(--note-ink);padding:7px 11px;font:700 clamp(14px,3.9vw,17px)/1.42 var(--note);word-break:keep-all}
.panel:has(.out){display:flex;flex-direction:column}
.note.out{position:static;align-self:flex-start;max-width:100%;margin-bottom:6px}
.balloon{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.balloon path,.balloon circle{fill:#fff;stroke:#12283b;stroke-width:3;vector-effect:non-scaling-stroke;stroke-linejoin:round}
.balloon text{fill:#12283b;font-family:var(--talk)}
.pledge{margin-top:72px;border-top:3px solid var(--ink);padding-top:20px;display:flex;flex-direction:column;gap:6px}
.pledge b{font:400 1.05rem/1.3 var(--talk);color:var(--deep)}.pledge p{font:400 1.5rem/1.4 var(--title);text-wrap:balance}
.q{font:400 1.15rem/1.5 var(--talk);margin-top:28px}
"""
    first = next((Path(c["image"]).name for c in cuts if c.get("full")), Path(cuts[0]["image"]).name if cuts else "")
    title = project["title"]
    head_lines = E(title).replace(": ", ":<br>")
    css += f":root{{--radius:{'12px' if project.get('round') else '0'};--frame:{'0' if project.get('round') else '3px solid var(--ink)'}}}\n"
    out = [head(project, title, css, f"img/{first}"), "<main>"]
    if home:
        out.append(f'<nav class="bar"><a href="{home}">← {E(project.get("home_label", "처음으로"))}</a><span>{len(cuts)}컷</span></nav>')
    if project.get("nav"):
        items = "".join(
            f'<b aria-current="page">{E(x["text"])}</b>' if x.get("current") else f'<a href="{E(x["href"], quote=True)}">{E(x["text"])}</a>'
            for x in project["nav"]
        )
        out.append(f'<nav class="bar lang"><span>{E(project.get("short_title", ""))}</span><span class="links">{items}</span></nav>')
    out.append(f'<header><h1>{head_lines}</h1><p class="en">{E(project.get("subtitle", ""))}</p></header>')
    out += cuts_html(cuts, prefix)
    pledge = project.get("pledge")
    if pledge:
        out.append(f'<section class="pledge"><b>{E(pledge["label"])}</b><p>{E(pledge["text"])}</p></section>')
    if project.get("question"):
        out.append(f'<p class="q">{E(project["question"])}</p>')
    links = project.get("end_links")
    if links is None:
        links = [{"text": "이 웹툰은 어떻게 만들었을까? 메이킹북 보기", "href": f"{prefix}making/"}]
    if links:
        out.append('<div class="btns">' + "".join(f'<a class="btn" href="{E(x["href"], quote=True)}">{E(x["text"])}</a>' for x in links) + "</div>")
    out.append("</main></body></html>")
    return "\n".join(out)


def home_page(project):
    """작품 첫 화면. 표지, 소개, 막 목록."""
    info = project["home"]
    cover = Path(info["cover"]).name
    css = f"""
body{{background:var(--bg);color:var(--ink);font:17px/1.65 var(--note)}}
.hero{{position:relative;min-height:min(78vh,620px);display:flex;align-items:flex-end;background:url(img/{cover}) center 30%/cover}}
.hero:after{{content:"";position:absolute;inset:0;background:linear-gradient(transparent 30%,var(--bg))}}
.in{{position:relative;z-index:1;padding:24px var(--gr) 24px var(--gl);max-width:900px;margin:0 auto;width:100%}}
h1{{color:var(--deep)}}
.btns{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}.btn{{background:var(--deep);color:var(--bg);text-decoration:none;border-radius:999px;padding:10px 20px;font:400 1rem/1.3 var(--talk)}}.btn.o{{background:var(--paper);color:var(--ink)}}
h2{{max-width:900px;margin:18px auto 10px;padding-left:var(--gl);padding-right:var(--gr)}}
.rail{{display:flex;gap:12px;overflow-x:auto;padding:4px var(--gr) 56px var(--gl);max-width:932px;margin:0 auto}}
.card{{flex:0 0 200px;background:var(--paper);border-radius:14px;overflow:hidden}}.card img{{width:200px;height:230px;object-fit:cover}}.card div{{padding:10px 12px}}.card b{{font:400 1.05rem/1.3 var(--talk);display:block}}.card span{{font-size:.85rem}}
"""
    out = [head(project, project["title"], css, f"img/{cover}")]
    title = E(project["title"]).replace(": ", ":<br>")
    links = "".join(
        f'<a class="btn{" o" if i else ""}" href="{E(x["href"], quote=True)}">{E(x["text"])}</a>' for i, x in enumerate(info["links"])
    )
    out.append(f'<section class="hero"><div class="in"><h1>{title}</h1><p>{E(info["blurb"])}</p><div class="btns">{links}</div></div></section>')
    if info.get("acts"):
        out.append(f'<h2>{E(info.get("acts_title", "이야기"))}</h2><div class="rail">')
        for a in info["acts"]:
            out.append(f'<article class="card"><img src="img/{Path(a["image"]).name}" alt="" loading="lazy"><div><b>{E(a["title"])}</b><span>{E(a["text"])}</span></div></article>')
        out.append("</div>")
    out.append("</body></html>")
    return "\n".join(out)


def spend(project):
    return sum(c["credits"] for c in project.get("credits") or [])


def remaining(project):
    price = project.get("price_per_image", 0.5)
    count = sum(1 for c in project["cuts"] if c.get("status") in ("planned", "fix"))
    return count, count * price


def board(project, has_image):
    css = """
body{background:var(--pale);color:var(--ink);font:16px/1.6 var(--note);padding-block:0 64px;padding-left:var(--gl);padding-right:var(--gr)}
main{max-width:640px;margin:0 auto;display:flex;flex-direction:column;gap:36px}
header{padding-top:48px;display:flex;flex-direction:column;gap:10px}
ol{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}
.st{display:flex;justify-content:space-between;gap:12px;background:var(--paper);border:2px solid var(--ink);padding:9px 12px;font:400 1rem/1.4 var(--talk)}
.st.done{background:var(--bg)}.st small{font:400 .85rem/1.4 var(--note);display:block}
.cut{display:grid;grid-template-columns:84px 1fr;gap:12px;background:var(--paper);border:2px solid var(--ink);padding:10px;min-width:0}
.cut>div{min-width:0}
.th{width:84px;aspect-ratio:1;object-fit:cover;border:1.5px solid var(--ink)}
.new{width:84px;aspect-ratio:1;display:grid;place-items:center;background:var(--bg);font:400 .85rem/1.2 var(--talk);text-align:center;border:1.5px dashed var(--ink)}
.no{font:400 1.05rem/1.3 var(--talk)}.tag{font:400 .8rem/1 var(--talk);color:var(--deep);margin-left:6px}
.line{margin-top:4px;font:400 .98rem/1.45 var(--talk);color:var(--deep)}
.keys{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.92rem}
.ask{background:var(--ink);color:var(--paper);padding:16px;font:400 1.1rem/1.5 var(--talk)}
.cost{font-variant-numeric:tabular-nums}
"""
    title = f"{project['title']} 보드"
    out = [head(project, title, css), "<main>"]
    count, cost = remaining(project)
    out.append(f"<header><h1>{E(project['title'])}</h1><p>지금까지 {spend(project):g}크레딧을 썼어요. 그릴 그림 {count}장, {cost:g}크레딧 예상이에요.</p>")
    out.append('<p class="keys"><span>★ 새로 그릴 컷</span><span>◆ 고칠 컷</span><span>※ 인터뷰에 없는 연출</span></p></header>')
    stages = project.get("stages") or []
    if stages:
        out.append("<section><h2>진행 단계</h2><ol>")
        for s in stages:
            state = s.get("status", "waiting")
            note = f"<small>{E(s['note'])}</small>" if s.get("note") else ""
            out.append(f'<li class="st {E(state, quote=True)}"><span>{E(s["name"])}{note}</span><span>{E(STATUS.get(state, state))}</span></li>')
        out.append("</ol></section>")
    acts = {}
    for c in project["cuts"]:
        acts.setdefault(c.get("act", "이야기"), []).append(c)
    for act, cuts in acts.items():
        out.append(f"<section><h2>{E(act)}</h2><ol>")
        for c in cuts:
            mark = MARKS.get(c.get("status"), "") + ("※" if c.get("evidence") == "staged" else "")
            tag = f'<span class="tag">{mark}</span>' if mark else ""
            if has_image(c):
                thumb = f'<img class="th" src="../img/{Path(c["image"]).name}" alt="{c["no"]}번 컷" loading="lazy">'
            else:
                thumb = '<span class="new">새로<br>그릴 컷</span>'
            words = [n["text"] for n in c.get("notes") or []] + [" ".join(b["lines"]) for b in c.get("balloons") or []]
            words += c.get("planned_text") or []
            line = f'<p class="line">{E(" / ".join(words))}</p>' if words else ""
            out.append(f'<li class="cut">{thumb}<div><p class="no">{c["no"]}{tag}</p><p>{E(c.get("scene", ""))}</p>{line}</div></li>')
        out.append("</ol></section>")
    if project.get("ask"):
        out.append(f'<p class="ask">{E(project["ask"])}</p>')
    out.append("</main></body></html>")
    return "\n".join(out)


def making(project):
    css = """
body{background:var(--pale);color:var(--ink);font:17px/1.72 var(--note);padding-block:0 72px;padding-left:var(--gl);padding-right:var(--gr)}
main{max-width:680px;margin:0 auto;display:flex;flex-direction:column;gap:52px}
header{padding-top:56px;display:flex;flex-direction:column;gap:10px}
section{display:flex;flex-direction:column;gap:14px;min-width:0}
.stage{font:400 1rem/1 var(--talk);color:var(--deep)}
.shot{border:3px solid var(--ink);width:100%;height:auto}
.cap{font-size:.92rem;color:var(--deep)}
.qa{display:flex;flex-direction:column;gap:12px}
.bot,.him{max-width:88%;padding:9px 13px;border-radius:14px;font:400 1rem/1.5 var(--talk);border:2px solid var(--ink)}
.bot{background:var(--paper);align-self:flex-start}.him{background:var(--bg);align-self:flex-end}
.tw{overflow-x:auto;background:var(--paper);border:2px solid var(--ink)}
table{border-collapse:collapse;width:100%;min-width:320px;font-size:.95rem;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--bg);vertical-align:top}thead th{background:var(--bg);font:400 .95rem/1.3 var(--talk)}
tfoot td{font-weight:700;border-bottom:0}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:10px}.pair figure{margin:0;display:flex;flex-direction:column;gap:6px;min-width:0}
@media (max-width:460px){.pair{grid-template-columns:1fr}}
ul{margin:0;padding-left:1.2em;display:flex;flex-direction:column;gap:6px}
"""
    out = [head(project, f"{project['title']} 메이킹북", css), "<main>"]
    out.append(f'<header><p><a href="../">← 처음으로</a></p><h1>메이킹북</h1><p>{E(project.get("making_intro", "인터뷰 한 번이 웹툰이 되기까지의 기록이에요."))}</p></header>')
    qa = project.get("interview") or []
    if qa:
        out.append('<section><p class="stage">인터뷰</p><h2>묻고 답했어요</h2><div class="qa">')
        for i in qa:
            out.append(f'<p class="bot">{E(i["q"])}</p><p class="him">{E(i["a"])}</p>')
        out.append("</div></section>")
    done = [c for c in project["cuts"] if c.get("beat")]
    if done:
        out.append('<section><p class="stage">이야기</p><h2>이렇게 짰어요</h2><div class="tw"><table><thead><tr><th>컷</th><th>이야기 단계</th><th>장면</th></tr></thead><tbody>')
        out += [f'<tr><td>{c["no"]}</td><td>{E(c["beat"])}</td><td>{E(c.get("scene", ""))}</td></tr>' for c in done]
        out.append("</tbody></table></div></section>")
    chars = project.get("characters") or []
    if chars:
        out.append('<section><p class="stage">캐릭터</p><h2>얼굴을 정했어요</h2>')
        for c in chars:
            out.append(f'<img class="shot" src="../img/{Path(c["image"]).name}" alt="{E(c.get("caption", "캐릭터 시트"), quote=True)}" loading="lazy">')
            if c.get("caption"):
                out.append(f'<p class="cap">{E(c["caption"])}</p>')
        out.append("</section>")
    for r in project.get("retakes") or []:
        out.append(f'<section><p class="stage">다시 그리기</p><h2>{E(r["title"])}</h2><div class="pair">')
        out.append(f'<figure><img class="shot" src="../img/{Path(r["before"]).name}" alt="고치기 전" loading="lazy"><figcaption class="cap">고치기 전</figcaption></figure>')
        out.append(f'<figure><img class="shot" src="../img/{Path(r["after"]).name}" alt="고친 뒤" loading="lazy"><figcaption class="cap">고친 뒤</figcaption></figure></div></section>')
    credits = project.get("credits") or []
    if credits:
        out.append('<section><p class="stage">쓴 비용</p><h2>단계별 크레딧</h2><div class="tw"><table><thead><tr><th>단계</th><th>한 일</th><th>크레딧</th></tr></thead><tbody>')
        out += [f'<tr><td>{E(c["stage"])}</td><td>{E(c["what"])}</td><td>{c["credits"]:g}</td></tr>' for c in credits]
        out.append(f'</tbody><tfoot><tr><td colspan="2">합계</td><td>{spend(project):g}</td></tr></tfoot></table></div>')
        out += [f'<p class="cap">{E(x)}</p>' for x in project.get("cost_notes") or []]
        out.append("</section>")
    lessons = project.get("lessons") or []
    if lessons:
        out.append('<section><p class="stage">시행착오</p><h2>이번에 배운 것</h2><ul>')
        out += [f"<li>{E(x)}</li>" for x in lessons]
        out.append("</ul></section>")
    out.append('<p><a href="../">← 처음으로</a></p></main></body></html>')
    return "\n".join(out)


def safe_image(root, name):
    """그림은 art/ 안에서만 가져온다. consent.md 나 photo/ 가 공개되지 않게."""
    art = (root / "art").resolve()
    src = (root / name).resolve()
    if art not in src.parents:
        raise ValueError(f"그림은 art/ 안에 있어야 합니다: {name}")
    if not src.is_file():
        raise FileNotFoundError(f"그림이 없습니다: {name}")
    return src


def build(root, out, only=None):
    """only='board' 면 공개 전 공유용으로 보드만 만든다. 웹툰과 메이킹북은 지운다."""
    root, out = Path(root), Path(out)
    project = json.loads((root / "project.json").read_text(encoding="utf-8"))

    def has_image(cut):
        return bool(cut.get("image")) and (root / cut["image"]).exists()

    # 고칠 컷은 새 그림이 나올 때까지 지금 그림으로 둔다
    ready = [c for c in project["cuts"] if c.get("status", "done") in ("done", "fix") and has_image(c)]
    images = [c["image"] for c in project["cuts"] if has_image(c)]
    if only != "board":
        images += [c["image"] for c in project.get("characters") or []]
        for r in project.get("retakes") or []:
            images += [r["before"], r["after"]]
    shutil.rmtree(out / "img", ignore_errors=True)
    (out / "img").mkdir(parents=True)
    seen = {}
    for name in images:
        src = safe_image(root, name)
        if seen.setdefault(src.name, src) != src:
            raise ValueError(f"그림 이름이 겹칩니다: {src.name}")
        shutil.copy2(src, out / "img" / src.name)
    if project.get("home") and only != "board":
        images = [project["home"]["cover"]] + [a["image"] for a in project["home"].get("acts") or []]
        for name in images:
            src = safe_image(root, name)
            shutil.copy2(src, out / "img" / src.name)
    pages = {"board/index.html": board(project, has_image)}
    if only == "board":
        for stale in ("index.html", "read/index.html", "making/index.html"):
            (out / stale).unlink(missing_ok=True)
    else:
        pages["making/index.html"] = making(project)
        if project.get("home"):
            pages["index.html"] = home_page(project)
            pages["read/index.html"] = webtoon(project, ready, "../", "../")
        else:
            pages["index.html"] = webtoon(project, ready)
    for rel, text in pages.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    return len(ready)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project")
    ap.add_argument("--out")
    ap.add_argument("--only", choices=["board"], help="공개 전에는 보드만 만든다")
    args = ap.parse_args()
    target = args.out or str(Path(args.project) / "site")
    print(f"컷 {build(args.project, target, args.only)}개로 만들었습니다: {target}")
