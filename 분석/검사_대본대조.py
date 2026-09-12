# -*- coding: utf-8 -*-
"""
화면에 있는 것을 대본이 말하는지 대조한다.

슬라이드에 근거·숫자가 떠 있는데 대본이 그걸 안 짚으면, 청중은 화면을 읽다가 놓친다.
디자인.md §6 "화면에 있는 것은 반드시 말한다" 를 기계로 확인한다.

    python 분석/검사_대본대조.py

확인 대상
  1. 12장 결정 표의 "핵심 근거" 칸 항목 (결정 6건 × 2개)
  2. 각 장의 핵심 숫자 (.num)
  3. 각 장의 제목에 나오는 숫자

실패가 있으면 종료 코드 1.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "발표_yonthrma.html")
SCRIPT = os.path.join(ROOT, "발표준비", "발표대본.md")

html = open(HTML, encoding="utf-8").read()
# 대본은 공백을 지워 비교한다 (줄바꿈·띄어쓰기 차이를 무시)
sc = re.sub(r"\s+", "", open(SCRIPT, encoding="utf-8").read())

fails = []

def spoken(item: str) -> bool:
    """대본이 이 항목을 말하는가. 통째로 있거나, 숫자 토큰이 모두 있으면 통과."""
    key = re.sub(r"\s+", "", item)
    if key in sc:
        return True
    nums = re.findall(r"\d+(?:\.\d+)?", key)
    return bool(nums) and all(n in sc for n in nums)

# ── 1. 12장 결정 표의 핵심 근거 ─────────────────────────────────────
m = re.search(r"<span>12 / \d+</span>[\s\S]*?</section>", html)
if not m:
    fails.append("12장을 찾지 못함")
else:
    rows = re.findall(r'<tr><td class="k">([^<]+)</td>.*?</td><td>([^<]+)</td></tr>', m.group(0))
    if len(rows) != 6:
        fails.append(f"12장 표가 6행이 아님 ({len(rows)}행)")
    n_ok = 0
    for name, ev in rows:
        for item in [x.strip() for x in ev.split("·") if x.strip()]:
            if spoken(item):
                n_ok += 1
            else:
                fails.append(f"12장 '{name}' 의 근거 '{item}' 를 대본이 말하지 않음")
    print(f"  {'✅' if not fails else '❌'} 12장 결정 표 핵심 근거 {n_ok}개 대본에 있음")

# ── 2. 각 장의 핵심 숫자 ────────────────────────────────────────────
n_num = n_num_ok = 0
for sec in re.finditer(r"<span>(\d+) / \d+</span>([\s\S]*?)</section>", html):
    n, body = sec.group(1), sec.group(2)
    for num in re.findall(r'<div class="num[^"]*">([^<]+)</div>', body):
        n_num += 1
        if spoken(num):
            n_num_ok += 1
        else:
            fails.append(f"{n}장 핵심 숫자 '{num.strip()}' 를 대본이 말하지 않음")
print(f"  {'✅' if n_num == n_num_ok else '❌'} 핵심 숫자 {n_num_ok}/{n_num}개 대본에 있음")

# ── 3. 장 제목의 숫자 ───────────────────────────────────────────────
n_t = n_t_ok = 0
for sec in re.finditer(r"<span>(\d+) / \d+</span>([\s\S]*?)</section>", html):
    n, body = sec.group(1), sec.group(2)
    h1 = re.search(r"<h1>([\s\S]*?)</h1>", body)
    if not h1:
        continue
    title = re.sub(r"<[^>]+>", " ", h1.group(1))
    # 날짜·시각·문서번호는 말로 다르게 부르므로(09-12 → "오늘", 23:12 → "11시 12분") 제외
    title = re.sub(r"TR-\d+-\d+|\d{2,4}-\d{2}(?:-\d{2,4})?|\d{1,2}:\d{2}", " ", title)
    for num in re.findall(r"\d+(?:\.\d+)?", title):
        if len(num) < 2:       # 한 자리 숫자는 조문 번호 등이라 건너뜀
            continue
        n_t += 1
        if num in sc:
            n_t_ok += 1
        else:
            fails.append(f"{n}장 제목의 숫자 '{num}' 를 대본이 말하지 않음")
print(f"  {'✅' if n_t == n_t_ok else '❌'} 제목 숫자 {n_t_ok}/{n_t}개 대본에 있음")

print()
for f in fails:
    print("  ❌", f)
print("  실패 0건" if not fails else f"  {len(fails)}건 실패")
sys.exit(0 if not fails else 1)
