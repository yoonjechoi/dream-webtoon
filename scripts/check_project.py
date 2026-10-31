#!/usr/bin/env python3
"""project.json 을 점검한다. 사람이 고쳐 달라고 했던 실수를 코드로 막는다.

[실패] 공개하면 안 되는 문제 · [주의] 사람이 봐야 할 것. 실패가 있으면 종료 코드 1.
공개 직전에는 --publish 를 붙인다. 인터뷰 기록과 동의 기록까지 본다.
"""
import json
import math
import sys
from pathlib import Path

PHONE = 343  # 컷이 놓이는 휴대폰 폭(px)
PHONE_FULL = 375  # 폭을 꽉 채운 컷
MIN_PX = 14


def balloon_box(b):
    return b["cx"] - b["rx"], b["cy"] - b["ry"], b["rx"] * 2, b["ry"] * 2


def in_balloon(b, x, y):
    return (abs(x - b["cx"]) / b["rx"]) ** 2.5 + (abs(y - b["cy"]) / b["ry"]) ** 2.5 <= 1


def covers(b, box):
    """풍선의 실제 모양이 얼굴 자리에 걸치는지 본다. 네모로 보면 모서리가 잘못 걸린다."""
    x, y, w, h = box
    inside = lambda px, py: x <= px <= x + w and y <= py <= y + h
    corners = [(x + w * i / 4, y + h * j / 4) for i in range(5) for j in range(5)]
    if any(in_balloon(b, px, py) for px, py in corners):
        return True
    return any(
        inside(b["cx"] + b["rx"] * math.cos(a / 18 * math.pi), b["cy"] + b["ry"] * math.sin(a / 18 * math.pi))
        for a in range(36)
    )


def text_width(line, size):
    """한글은 거의 한 글자 폭, 공백과 문장 부호는 좁다."""
    em = 0
    for ch in line:
        if ch == " ":
            em += 0.3
        elif "\uac00" <= ch <= "\ud7a3":
            em += 0.95
        else:
            em += 0.55
    return em * size


def valid_balloon(b):
    """모양이 틀린 풍선은 계산하지 않고 알린다."""
    try:
        if float(b["rx"]) <= 0 or float(b["ry"]) <= 0 or float(b["size"]) <= 0:
            return "크기가 0 입니다"
        float(b["cx"]), float(b["cy"])
        if not b["lines"] or not all(isinstance(t, str) and t for t in b["lines"]):
            return "lines 가 비었습니다"
        if b.get("type") == "talk" and len(b["tip"]) != 2:
            return "tip 이 없습니다"
    except (KeyError, TypeError, ValueError):
        return "칸이 빠졌습니다"
    return ""


def check(root, publish=False):
    root = Path(root)
    errors, warns = [], []
    project = json.loads((root / "project.json").read_text(encoding="utf-8"))
    for key in ("title", "cuts"):
        if not project.get(key):
            errors.append(f"{key} 가 없습니다")
    for key in ("title", "subtitle", "site_url", "making_intro", "question"):
        if key in project and not isinstance(project[key], str):
            errors.append(f"{key} 는 글이어야 합니다")
    for item in project.get("credits") or []:
        if not isinstance(item.get("credits"), (int, float)):
            errors.append("credits 의 값은 숫자여야 합니다")
    for item in project.get("characters") or []:
        if not (root / item.get("image", "?")).is_file():
            errors.append(f"캐릭터 그림이 없습니다: {item.get('image')}")
    if publish:
        for name in ("interview.md", "consent.md"):
            if not (root / name).is_file():
                errors.append(f"공개 전에 {name} 이 있어야 합니다")
        if not project.get("site_url"):
            warns.append("site_url 이 없어 미리보기 이미지가 나오지 않습니다")
    cuts = project.get("cuts") or []
    if [c.get("no") for c in cuts] != list(range(1, len(cuts) + 1)):
        errors.append("컷 번호가 1부터 이어지지 않습니다")

    for c in cuts:
        no, tag = c.get("no"), f"{c.get('no')}번 컷"
        status = c.get("status", "done")
        if "planned_text" in c and not isinstance(c["planned_text"], list):
            errors.append(f"{tag}: planned_text 는 목록이어야 합니다")
        if status not in ("done", "planned", "fix"):
            errors.append(f"{tag}: status 는 done · planned · fix 중 하나입니다")
        if c.get("evidence") not in ("interview", "staged"):
            errors.append(f"{tag}: evidence 는 interview 또는 staged 입니다")
        if status in ("done", "fix"):
            if not c.get("image") or not (root / c["image"]).is_file():
                errors.append(f"{tag}: 그림 파일이 없습니다")
            if not (c.get("width") and c.get("height")):
                errors.append(f"{tag}: width · height 가 없습니다")
                continue
        if status == "planned" or not c.get("width"):
            continue
        w, h = c["width"], c["height"]
        avoid = c.get("avoid") or []
        people = c.get("people", True)
        if people and not avoid and (c.get("balloons") or any(n.get("place", "out") != "out" for n in c.get("notes") or [])):
            warns.append(f"{tag}: 글이 그림 위에 있는데 avoid(얼굴 자리)가 없어 가림을 점검하지 못했습니다")
        phone = (PHONE_FULL if c.get("full") else PHONE) / w
        for b in c.get("balloons") or []:
            problem = valid_balloon(b)
            if problem:
                errors.append(f"{tag}: 풍선 {problem}")
                continue
            label = " ".join(b.get("lines") or [])
            if b.get("type") not in ("talk", "think"):
                errors.append(f"{tag}: 풍선 type 은 talk 또는 think 입니다")
                continue
            x, y, bw, bh = balloon_box(b)
            if x < 0 or y < 0 or x + bw > w or y + bh > h:
                errors.append(f"{tag}: 「{label}」 풍선이 그림 밖으로 나갑니다")
            if b["size"] * phone < MIN_PX:
                errors.append(f"{tag}: 「{label}」 글자가 휴대폰에서 {b['size'] * phone:.1f}px 입니다. {MIN_PX}px 이상으로")
            room = b["rx"] * (1.9 if b["type"] == "talk" else 1.75)
            if max(text_width(t, b["size"]) for t in b["lines"]) > room:
                errors.append(f"{tag}: 「{label}」 글이 풍선보다 넓습니다")
            height = len(b["lines"]) * b["size"] * 1.26
            if height > b["ry"] * 1.8:
                errors.append(f"{tag}: 「{label}」 줄이 풍선보다 높습니다")
            for box in avoid:
                if covers(b, box):
                    errors.append(f"{tag}: 「{label}」 풍선이 얼굴 자리를 가립니다")
            if b["type"] == "talk":
                tx, ty = b["tip"]
                if not (0 <= tx <= w and 0 <= ty <= h):
                    errors.append(f"{tag}: 「{label}」 꼬리가 그림 밖을 가리킵니다")
                reach = math.hypot((tx - b["cx"]) / b["rx"], (ty - b["cy"]) / b["ry"])
                if reach > 2.4:
                    warns.append(f"{tag}: 「{label}」 꼬리가 깁니다. 풍선을 말하는 사람 쪽으로 옮기세요")
                if reach < 1.15:
                    errors.append(f"{tag}: 「{label}」 꼬리 끝이 풍선 안에 있습니다")
                for box in avoid:
                    if box[0] <= tx <= box[0] + box[2] and box[1] <= ty <= box[1] + box[3]:
                        warns.append(f"{tag}: 「{label}」 꼬리가 얼굴에 닿습니다. 입 바로 앞에서 멈추게 하세요")
            elif not b.get("dots"):
                warns.append(f"{tag}: 「{label}」 속마음 풍선에 동그라미가 없습니다")
        for n in c.get("notes") or []:
            if n.get("place", "out") != "out" and w > h:
                errors.append(f"{tag}: 가로 컷의 해설은 그림을 가립니다. place 를 out 으로 하세요")

    staged = sum(1 for c in cuts if c.get("evidence") == "staged")
    if cuts and staged / len(cuts) > 0.4:
        warns.append(f"전체 {len(cuts)}컷 중 {staged}컷이 연출입니다. 본인에게 더 물어 사실로 바꿀 수 있는지 보세요")
    for r in project.get("retakes") or []:
        for key in ("before", "after"):
            if not (root / r[key]).is_file():
                errors.append(f"다시 그리기 그림이 없습니다: {r[key]}")
    return errors, warns, {
        "컷": len(cuts),
        "완료": sum(1 for c in cuts if c.get("status", "done") == "done"),
        "그릴 그림": sum(1 for c in cuts if c.get("status") in ("planned", "fix")),
        "연출": staged,
    }


def main(root, publish=False):
    errors, warns, summary = check(root, publish)
    print(" · ".join(f"{k} {v}" for k, v in summary.items()))
    for e in errors:
        print(f"[실패] {e}")
    for w in warns:
        print(f"[주의] {w}")
    if not errors and not warns:
        print("[통과] 걸린 곳이 없습니다")
    return 1 if errors else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--publish"]
    sys.exit(main(args[0] if args else ".", "--publish" in sys.argv))
