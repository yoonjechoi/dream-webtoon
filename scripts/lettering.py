#!/usr/bin/env python3
"""말풍선을 그림 좌표의 SVG 로 그린다.

몸통과 꼬리는 한 덩어리 도형이라 테두리가 끊기지 않는다.
꼬리는 짧고 굵게 살짝 휘고, 속마음은 구름 풍선에 머리 쪽으로 작아지는 동그라미를 잇는다.
좌표가 그림 기준이라 화면 폭이 바뀌어도 꼬리가 같은 곳을 가리킨다.
"""
import html
import math


def talk_path(cx, cy, rx, ry, tx, ty):
    def edge(a):
        c, s = math.cos(a), math.sin(a)
        n = 2.5  # 타원보다 살짝 각진 모양
        r = (abs(c / rx) ** n + abs(s / ry) ** n) ** (-1 / n)
        return cx + r * c, cy + r * s

    aim = math.atan2((ty - cy) / ry, (tx - cx) / rx)
    root = 0.2  # 꼬리 뿌리 폭
    start, steps = aim + root, 72
    pts = [edge(start + (2 * math.pi - 2 * root) * i / steps) for i in range(steps + 1)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    (ex, ey), (sx, sy) = pts[-1], pts[0]
    bend = 0.22

    def mid(ax, ay):
        return (ax + tx) / 2 + (ty - ay) * bend, (ay + ty) / 2 - (tx - ax) * bend

    q1, q2 = mid(ex, ey), mid(sx, sy)
    return d + f" Q{q1[0]:.1f} {q1[1]:.1f} {tx} {ty} Q{q2[0]:.1f} {q2[1]:.1f} {sx:.1f} {sy:.1f} Z"


def cloud_path(cx, cy, rx, ry, bumps=12):
    pts = [
        (cx + rx * 0.92 * math.cos(2 * math.pi * i / bumps), cy + ry * 0.86 * math.sin(2 * math.pi * i / bumps))
        for i in range(bumps)
    ]
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, bumps + 1):
        x, y = pts[i % bumps]
        px, py = pts[i - 1]
        r = math.hypot(x - px, y - py) * 0.58
        d += f" A{r:.1f} {r:.1f} 0 0 1 {x:.1f} {y:.1f}"
    return d + " Z"


def lines_svg(cx, cy, lines, size):
    gap = size * 1.26
    top = cy - gap * (len(lines) - 1) / 2 + size * 0.35
    return "".join(
        f'<text x="{cx}" y="{top + i * gap:.1f}" text-anchor="middle" font-size="{size}">{html.escape(t)}</text>'
        for i, t in enumerate(lines)
    )


def balloon_svg(cut):
    """컷 하나의 말풍선을 SVG 한 장으로 돌려준다. 말풍선이 없으면 빈 문자열."""
    shapes, labels = "", []
    for b in cut.get("balloons") or []:
        if b["type"] == "talk":
            shapes += f'<path d="{talk_path(b["cx"], b["cy"], b["rx"], b["ry"], *b["tip"])}"/>'
        else:
            shapes += f'<path d="{cloud_path(b["cx"], b["cy"], b["rx"], b["ry"])}"/>'
            shapes += "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in b.get("dots") or [])
        shapes += lines_svg(b["cx"], b["cy"], b["lines"], b["size"])
        labels.append(" ".join(b["lines"]))
    if not shapes:
        return ""
    label = html.escape(" / ".join(labels), quote=True)
    return f'<svg class="balloon" viewBox="0 0 {cut["width"]} {cut["height"]}" role="img" aria-label="{label}">{shapes}</svg>'
