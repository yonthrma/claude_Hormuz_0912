# -*- coding: utf-8 -*-
"""
보고서_yonthrma.md → 보고서_yonthrma.html
디자인.md 규칙을 CSS 로 옮기고, 본문은 md 그대로 변환한다. 새 문장을 만들지 않는다.

    python 분석/보고서_html변환.py
"""
import html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "보고서_yonthrma.md")
OUT = os.path.join(ROOT, "보고서_yonthrma.html")

md = open(SRC, encoding="utf-8").read().replace("\r\n", "\n")
lines = md.split("\n")

# ── 인라인 ──────────────────────────────────────────────────────────
CITE_RE = re.compile(r"\[([^\[\]]+?)\](?!\()")

def inline(s):
    s = html.escape(s, quote=False)
    # 마크다운 링크 [t](u) → 임시 토큰
    links = []
    def _lnk(m):
        links.append((m.group(1), m.group(2))); return f"\x00L{len(links)-1}\x00"
    s = re.sub(r"\[([^\]]+?)\]\(([^)]+?)\)", _lnk, s)
    # 자동 링크 &lt;http…&gt;
    s = re.sub(r"&lt;(https?://[^&\s]+)&gt;", lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', s)
    # 근거 칩 [파일 / 위치], [출처, 발행일]
    s = CITE_RE.sub(lambda m: f'<span class="cite">{m.group(1)}</span>', s)
    # 미확인 칩 (뒤에 한글이 안 이어질 때)
    s = re.sub(r"미확인(?![가-힣])", '<span class="chip unk">▲ 미확인</span>', s)
    # 굵게, 코드
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+?)`", r"<code>\1</code>", s)
    for i, (t, u) in enumerate(links):
        s = s.replace(f"\x00L{i}\x00", f'<a href="{u}">{t}</a>')
    return s

# ── 블록 ────────────────────────────────────────────────────────────
out = []
toc = []
i = 0
in_decision = False
in_summary = False
sec_no = 0

cur_h2 = ""

def flush_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [c for c in cells if not all(re.fullmatch(r":?-{3,}:?", x) for x in c)]
    if not cells: return ""
    head, body = cells[0], cells[1:]
    h = "".join(f"<th>{inline(c)}</th>" for c in head)
    b = ""
    for r in body:
        tds = []
        for j, c in enumerate(r):
            cls = ' class="k"' if j == 0 else ""
            v = inline(c)
            if j == 0 and cur_h2.startswith("부록 C"):
                v = '<span class="chip no">✕</span> ' + v       # 채택하지 않은 안
            if j == 0 and cur_h2.startswith("부록 A"):
                v = '<span class="chip ok">✔</span> ' + v       # 본문 확인한 출처
            tds.append(f"<td{cls}>{v}</td>")
        b += "<tr>" + "".join(tds) + "</tr>"
    return f'<div class="tbl"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

def close_decision():
    global in_decision
    if in_decision:
        out.append("</div>"); in_decision = False

band_line = None
sub_line = None

while i < len(lines):
    ln = lines[i]
    if not ln.strip():
        i += 1; continue
    if ln.startswith("# "):
        out.append(f"<h1>{inline(ln[2:])}</h1>")
        # 다음 두 줄: 문서번호 줄, 수신 줄
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        while j < len(lines) and lines[j].strip():
            if band_line is None: band_line = lines[j].strip()
            elif sub_line is None: sub_line = lines[j].strip()
            j += 1
        if sub_line: out.append(f'<p class="sub">{inline(sub_line)}</p>')
        i = j; continue
    if ln.startswith("## "):
        close_decision(); in_summary = False
        title = ln[3:].strip()
        m = re.match(r"^(\d)\.\s", title)
        if m:
            sec_no = int(m.group(1)); sid = f"s{sec_no}"
        elif title.startswith("결정 필요"):
            sid = "decide"
        elif title.startswith("개요"):
            sid = "overview"
        elif title.startswith("부록"):
            sid = "apx" + re.sub(r"[^A-Z]", "", title.split(".")[0])
        else:
            sid = "h" + str(len(toc))
        toc.append((sid, title))
        cur_h2 = title
        if sid == "decide":
            out.append(f'<div class="decision" id="{sid}"><h2>{inline(title)}</h2>')
            in_decision = True
        else:
            out.append(f'<h2 id="{sid}">{inline(title)}</h2>')
        i += 1; continue
    if ln.startswith("### "):
        t = ln[4:].strip()
        in_summary = t.startswith("요약")
        out.append(f"<h3>{inline(t)}</h3>"); i += 1; continue
    if ln.startswith("#### "):
        out.append(f"<h4>{inline(ln[5:])}</h4>"); i += 1; continue
    if ln.strip() == "---":
        close_decision(); i += 1; continue
    if ln.lstrip().startswith("|"):
        rows = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            rows.append(lines[i]); i += 1
        out.append(flush_table(rows)); continue
    if re.match(r"^\s*[-*]\s", ln) or re.match(r"^\s*\d+\.\s", ln):
        ordered = bool(re.match(r"^\s*\d+\.\s", ln))
        items = []
        while i < len(lines) and (re.match(r"^\s*[-*]\s", lines[i]) or re.match(r"^\s*\d+\.\s", lines[i]) or (lines[i].startswith("  ") and lines[i].strip())):
            if re.match(r"^\s*([-*]|\d+\.)\s", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s", "", lines[i]))
            else:
                items[-1] += " " + lines[i].strip()
            i += 1
        cls = ' class="sum"' if in_summary and ordered else ""
        tag = "ol" if ordered else "ul"
        lis = []
        for it in items:
            h = inline(it)
            if it.startswith("검토 결과"):
                h = re.sub(r"<strong>(.+?)</strong>", r'<span class="chip pt">\1</span>', h, count=1)
            lis.append(f"<li>{h}</li>")
        out.append(f"<{tag}{cls}>" + "".join(lis) + f"</{tag}>")
        continue
    # 문단 (연속 줄 합침)
    para = []
    while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||\s*[-*]\s|\s*\d+\.\s|---)", lines[i]):
        para.append(lines[i].strip()); i += 1
    if para:
        out.append(f"<p>{inline(' '.join(para))}</p>")

close_decision()

toc_html = "".join(f'<a href="#{sid}">{html.escape(t)}</a>' for sid, t in toc)

CSS = """
:root{--bg:#FBF8F2;--card:#FFFFFF;--ink:#1F2933;--sub:#52606D;--line:#1F2933;--soft:#CBD2D9;--thead:#EEF1F4;--pt:#7A2A46;--ptbg:#FFE3EE;
--ok:#00614A;--okbg:#D9F9F0;--okln:#00B88E;--unk:#8A5A00;--unkbg:#FFF1CC;--unkln:#C99A2E;--bad:#8A2B2B;--badbg:#F7E0E0;--badln:#C25A5A}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;font-size:15px;line-height:1.7;font-weight:400}
.band{background:var(--line);color:var(--bg);font-size:13px;font-weight:600;padding:8px 16px}
main{max-width:860px;margin:0 auto;padding:16px 16px 60px}
h1{font-size:22px;font-weight:800;margin:14px 0 4px;line-height:1.35}
.sub{color:var(--sub);font-size:13px;font-weight:600;margin:0 0 14px}
nav.toc{background:var(--card);border:2px solid var(--line);border-radius:8px;padding:10px 14px;margin:0 0 18px;font-size:13px;font-weight:600}
nav.toc a{color:var(--pt);text-decoration:none;margin:0 10px 4px 0;display:inline-block}
h2{font-size:18px;font-weight:700;margin:28px 0 10px;padding-left:12px;border-left:4px solid var(--line);line-height:1.4}
h3{font-size:16px;font-weight:700;margin:20px 0 8px}
h4{font-size:15px;font-weight:700;margin:14px 0 6px}
p{margin:0 0 10px}
ul,ol{margin:0 0 10px;padding-left:22px}
li{margin:0 0 6px}
ol.sum{list-style:none;padding-left:0;counter-reset:s}
ol.sum li{counter-increment:s;padding-left:34px;position:relative}
ol.sum li::before{content:"● " counter(s);position:absolute;left:0;color:var(--bad);font-weight:800}
strong{font-weight:700}
code{font-family:Consolas,"Malgun Gothic",monospace;font-size:14px;background:var(--thead);padding:0 4px;border-radius:4px}
a{color:var(--pt)}
.cite{display:inline-block;color:var(--sub);font-size:13px;font-weight:600;border:1px solid var(--soft);border-radius:4px;padding:0 4px;margin:0 2px;white-space:nowrap;line-height:1.5;vertical-align:baseline}
.chip{display:inline-block;font-size:13px;font-weight:800;border:2px solid;border-radius:4px;padding:0 6px;margin:0 2px;line-height:1.5;white-space:nowrap}
.chip.unk{color:var(--unk);background:var(--unkbg);border-color:var(--unkln)}
.chip.pt{color:var(--pt);background:var(--ptbg);border-color:var(--pt)}
.chip.ok{color:var(--ok);background:var(--okbg);border-color:var(--okln)}
.chip.bad{color:var(--bad);background:var(--badbg);border-color:var(--badln)}
.chip.no{color:var(--sub);background:var(--thead);border-color:var(--soft)}
.decision{background:var(--card);border:2px solid var(--pt);border-radius:8px;padding:4px 16px 12px;margin:18px 0}
.decision h2{border-left-color:var(--pt);color:var(--pt);margin-top:12px}
.tbl{overflow-x:auto;background:var(--card);border:2px solid var(--line);border-radius:6px;margin:0 0 14px}
table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.5}
th{background:var(--thead);text-align:left;padding:8px 10px;border-bottom:2px solid var(--line);font-weight:700;white-space:nowrap}
td{padding:8px 10px;border-top:1px solid var(--soft);vertical-align:top}
td.k{font-weight:700}
@media print{.band{-webkit-print-color-adjust:exact}.tbl{overflow:visible;border:1px solid var(--line)}h2{break-after:avoid}}
"""

page = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>항차 이상 보고서 — HANBADA 3 호르무즈 억류 (TR-2026-0912 안)</title>
<style>{CSS}</style>
</head>
<body>
<div class="band">{inline(band_line or '')}</div>
<main>
{out[0]}
{out[1] if len(out) > 1 and out[1].startswith('<p class="sub">') else ''}
<nav class="toc" aria-label="목차">{toc_html}</nav>
{''.join(out[2:] if len(out) > 1 and out[1].startswith('<p class="sub">') else out[1:])}
</main>
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(page)
print(f"OK {OUT} ({len(page):,} chars) — 절 {len(toc)}개, 근거 칩 {page.count('class=\"cite\"')}개, 미확인 칩 {page.count('chip unk')}개")
