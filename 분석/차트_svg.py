# -*- coding: utf-8 -*-
"""
원본 CSV 에서 발표용 시계열 그래프 2장을 인라인 SVG 로 그려 발표_yonthrma.html 에 심는다.
  1) 위성수신: 분 평균 위성 수·SNR, 교란 등급 띠, 사건 표시   (22:30 ~ 01:30)
  2) 항적:     분 평균 침로(hdg)·속력(sog), 사건 표시          (23:00 ~ 01:15)
색은 디자인.md 팔레트만. 글자는 CSS 클래스(18px 이상)로만 지정. 그림 파일 없음.

    python 분석/차트_svg.py
"""
import csv, os, re
from collections import defaultdict
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "사건데이터")
HTML = os.path.join(ROOT, "발표_yonthrma.html")

INK, SUB, SOFT, PT = "#1F2933", "#52606D", "#CBD2D9", "#7A2A46"
UNKBG, BADBG, BAD = "#FFF1CC", "#F7E0E0", "#8A2B2B"

def ts(s): return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
def T(h, m, day=11): return datetime(2026, 9, day, h, m)

# ── 데이터: 분 평균 ─────────────────────────────────────────────────
def minute_avg(path, cols, t0, t1):
    acc = defaultdict(lambda: defaultdict(float)); n = defaultdict(int); mx = defaultdict(int)
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t = ts(r["utc_kst"])
            if t < t0 or t >= t1: continue
            k = t.replace(second=0)
            n[k] += 1
            for c in cols: acc[k][c] += float(r[c])
            if "interference_level" in r: mx[k] = max(mx[k], int(r["interference_level"]))
    keys = sorted(n)
    return keys, {c: [acc[k][c] / n[k] for k in keys] for c in cols}, [mx[k] for k in keys]

g_keys, g, g_int = minute_avg(os.path.join(DATA, "운항로그", "위성수신_HANBADA3.csv"), ["sats_used", "avg_snr_dbhz"], T(22, 30), T(1, 30, 12))
t_keys, tr, _ = minute_avg(os.path.join(DATA, "운항로그", "항적_HANBADA3.csv"), ["hdg_deg", "sog_kn"], T(23, 0), T(1, 15, 12))

# ── SVG 도구 ────────────────────────────────────────────────────────
W = 1152
def xmap(t, t0, t1, x0=70, x1=W - 20):
    return x0 + (t - t0).total_seconds() / (t1 - t0).total_seconds() * (x1 - x0)
def ymap(v, lo, hi, y0, y1):  # y0 아래, y1 위
    return y0 - (v - lo) / (hi - lo) * (y0 - y1)
def poly(pts, color, w=3):
    return f'<polyline fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>'
def axis(y, x0=70, x1=W - 20): return f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{SOFT}" stroke-width="1"/>'
def ylab(x, y, s, cls="t"): return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="end">{s}</text>'
def xticks(t0, t1, y, step=30):
    out = []; t = t0.replace(minute=(t0.minute // step) * step)
    while t <= t1:
        if t >= t0:
            x = xmap(t, t0, t1); out.append(f'<line x1="{x:.1f}" y1="{y-4}" x2="{x:.1f}" y2="{y+4}" stroke="{SOFT}"/><text class="t" x="{x:.1f}" y="{y+22}" text-anchor="middle">{t.strftime("%H:%M")}</text>')
        t += timedelta(minutes=step)
    return "".join(out)
def marker(t, t0, t1, ytop, ybot, label, row=0):
    x = xmap(t, t0, t1); ly = 18 + row * 22
    line = f'<line x1="{x:.1f}" y1="{ytop}" x2="{x:.1f}" y2="{ybot}" stroke="{PT}" stroke-width="2" stroke-dasharray="6 5"/>'
    return line + (f'<text class="lab" x="{x:.1f}" y="{ly}" text-anchor="middle">{label}</text>' if label else "")

# ── 1) 위성수신 ─────────────────────────────────────────────────────
def chart_gnss():
    t0, t1 = T(22, 30), T(1, 30, 12); H = 300
    sats_y0, sats_y1 = 150, 62        # 위성 수 패널 (위 62px 는 사건 라벨 2줄)
    snr_y0, snr_y1 = 268, 178         # SNR 패널
    out = [f'<svg class="ch" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="위성 수와 SNR 분 평균, 교란 등급 띠">']
    # 교란 띠 (등급 1 노랑, 2 빨강) — 두 패널에 걸쳐
    for k, lv in zip(g_keys, g_int):
        if lv > 0:
            x = xmap(k, t0, t1); w = xmap(k + timedelta(minutes=1), t0, t1) - x
            out.append(f'<rect x="{x:.1f}" y="{sats_y1}" width="{w+0.5:.1f}" height="{snr_y0 - sats_y1}" fill="{BADBG if lv == 2 else UNKBG}"/>')
    # 축·라벨
    for v in (0, 7, 14): out.append(axis(ymap(v, 0, 15, sats_y0, sats_y1)) + ylab(60, ymap(v, 0, 15, sats_y0, sats_y1) + 6, str(v)))
    for v in (14, 30, 45): out.append(axis(ymap(v, 10, 50, snr_y0, snr_y1)) + ylab(60, ymap(v, 10, 50, snr_y0, snr_y1) + 6, str(v)))
    out.append(f'<text class="lab" x="70" y="{sats_y1 - 8}">위성 수 (분 평균)</text>')
    out.append(f'<text class="lab" x="70" y="{snr_y1 - 8}">SNR dB-Hz (분 평균)</text>')
    out.append(poly([(xmap(k, t0, t1), ymap(v, 0, 15, sats_y0, sats_y1)) for k, v in zip(g_keys, g["sats_used"])], INK))
    out.append(poly([(xmap(k, t0, t1), ymap(v, 10, 50, snr_y0, snr_y1)) for k, v in zip(g_keys, g["avg_snr_dbhz"])], SUB))
    out.append(xticks(t0, t1, snr_y0 + 2))
    # 사건 표시는 신호와 관련된 셋만 (23:32 재계산은 항적 그래프에)
    for t, lab, row in ((T(23, 12), "23:12 교란 시작", 0), (T(23, 29), "23:29 등급 2", 1), (T(0, 58, 12), "00:58 수동 전환·교란 종료", 0)):
        out.append(marker(t, t0, t1, sats_y1 - 4, snr_y0, lab, row))
    # 띠 범례 — 오른쪽 위 둘째 줄 (눈금 라벨과 겹치지 않게)
    out.append(f'<rect x="{W-330}" y="29" width="18" height="14" fill="{UNKBG}" stroke="{SOFT}"/><text class="t" x="{W-306}" y="41">교란 등급 1</text>')
    out.append(f'<rect x="{W-180}" y="29" width="18" height="14" fill="{BADBG}" stroke="{SOFT}"/><text class="t" x="{W-156}" y="41">교란 등급 2</text>')
    out.append("</svg>")
    return "".join(out)

# ── 2) 항적 ─────────────────────────────────────────────────────────
def chart_track():
    t0, t1 = T(23, 0), T(1, 15, 12); H = 300
    hdg_y0, hdg_y1 = 170, 78          # 침로 패널 285~325 (위 78px 는 사건 라벨 3줄)
    sog_y0, sog_y1 = 268, 195         # 속력 패널 0~16
    out = [f'<svg class="ch" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="침로와 속력 분 평균, 사건 표시">']
    for v in (290, 300, 310, 320): out.append(axis(ymap(v, 285, 325, hdg_y0, hdg_y1)) + ylab(60, ymap(v, 285, 325, hdg_y0, hdg_y1) + 6, f"{v}°"))
    for v in (0, 7, 14): out.append(axis(ymap(v, 0, 16, sog_y0, sog_y1)) + ylab(60, ymap(v, 0, 16, sog_y0, sog_y1) + 6, str(v)))
    out.append(f'<text class="lab" x="70" y="{hdg_y1 - 8}">침로 hdg (분 평균)</text>')
    out.append(f'<text class="lab" x="70" y="{sog_y1 - 8}">속력 kn (분 평균)</text>')
    out.append(poly([(xmap(k, t0, t1), ymap(min(max(v, 285), 325), 285, 325, hdg_y0, hdg_y1)) for k, v in zip(t_keys, tr["hdg_deg"])], BAD))
    out.append(poly([(xmap(k, t0, t1), ymap(v, 0, 16, sog_y0, sog_y1)) for k, v in zip(t_keys, tr["sog_kn"])], INK))
    out.append(xticks(t0, t1, sog_y0 + 2, step=15))
    # 라벨 3줄로 겹침 방지. VHF 두 호출은 선 둘, 라벨 하나.
    marks = ((T(23, 12), "23:12 교란", 0), (T(23, 32), "23:32 재계산", 0), (T(23, 41), "23:41 경계 접근", 1), (T(23, 47), "23:47·52 VHF", 2),
             (T(23, 52), "", 2), (T(23, 58), "23:58 경계 통과", 0), (T(0, 4, 12), "00:04 선명 호출", 1), (T(0, 58, 12), "00:58 수동 전환", 0))
    for t, lab, row in marks: out.append(marker(t, t0, t1, hdg_y1 - 4, sog_y0, lab, row))
    # 시작·끝 침로 값
    out.append(f'<text class="lab" x="{xmap(T(23,32),t0,t1)+6:.1f}" y="{ymap(291.5,285,325,hdg_y0,hdg_y1)+22:.1f}">291.5°</text>')
    out.append(f'<text class="lab" x="{xmap(T(0,58,12),t0,t1)-8:.1f}" y="{ymap(317.7,285,325,hdg_y0,hdg_y1)-8:.1f}" text-anchor="end">317.7°</text>')
    out.append("</svg>")
    return "".join(out)

# ── HTML 에 심기 ─────────────────────────────────────────────────────
html = open(HTML, encoding="utf-8").read()
for tag, svg in (("gnss", chart_gnss()), ("track", chart_track())):
    pat = re.compile(rf"(<!--CHART:{tag}-->)[\s\S]*?(<!--/CHART:{tag}-->)")
    if not pat.search(html): raise SystemExit(f"표식 없음: {tag}")
    html = pat.sub(lambda m: m.group(1) + svg + m.group(2), html)
open(HTML, "w", encoding="utf-8").write(html)
print(f"OK 그래프 2장 심음 — 위성수신 {len(g_keys)}분, 항적 {len(t_keys)}분 · sats 범위 {min(g['sats_used']):.1f}~{max(g['sats_used']):.1f} · hdg 범위 {min(tr['hdg_deg']):.1f}~{max(tr['hdg_deg']):.1f}")
