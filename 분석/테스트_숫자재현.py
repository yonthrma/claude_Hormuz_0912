# -*- coding: utf-8 -*-
"""
보고서 부록 B '숫자 재현표' 의 모든 값이
  (1) 분석/결과_사실재구성.json 에 같은 값으로 있고
  (2) 그 JSON 이 원본 CSV 에서 다시 계산해도 같은지
확인한다. 하나라도 어긋나면 종료 코드 1.

    python 분석/테스트_숫자재현.py [보고서_경로]
"""
import json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPORT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "보고서_yonthrma.md")
JSON_PATH = os.path.join(HERE, "결과_사실재구성.json")

fails = []

# ── (2) 원본에서 재계산 → 기존 JSON 과 비교 ─────────────────────────
def recompute():
    tmpdir = tempfile.mkdtemp()
    # 스크립트를 임시 폴더로 복사해 돌리면 OUT 이 임시 폴더에 생긴다
    src = open(os.path.join(HERE, "사실재구성.py"), encoding="utf-8").read()
    tmp_script = os.path.join(tmpdir, "사실재구성.py")
    open(tmp_script, "w", encoding="utf-8").write(src)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, tmp_script, os.path.join(ROOT, "사건데이터")],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    if r.returncode != 0:
        fails.append(f"재계산 스크립트 실패:\n{r.stderr[-2000:]}")
        return None
    return json.load(open(os.path.join(tmpdir, "결과_사실재구성.json"), encoding="utf-8"))

committed = json.load(open(JSON_PATH, encoding="utf-8"))
fresh = recompute()
if fresh is not None:
    if json.dumps(fresh, sort_keys=True, ensure_ascii=False) == json.dumps(committed, sort_keys=True, ensure_ascii=False):
        print("  ✅ 재계산 JSON == 저장된 JSON (원본 CSV 에서 다시 계산해도 같음)")
    else:
        # 어디가 다른지 최상위 키만
        diff = [k for k in set(fresh) | set(committed) if json.dumps(fresh.get(k), sort_keys=True) != json.dumps(committed.get(k), sort_keys=True)]
        fails.append(f"재계산 JSON 이 저장된 JSON 과 다름 — 다른 최상위 키: {diff}")

# ── (1) 보고서 부록 B 표 → JSON 대조 ────────────────────────────────
md = open(REPORT, encoding="utf-8").read()
sec = md.split("## 부록 B.")[1].split("\n## ")[0] if "## 부록 B." in md else ""
rows = []
for line in sec.splitlines():
    m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", line)
    if not m or m.group(1) in ("값", "---"): continue
    rows.append((m.group(1), m.group(2), m.group(3)))
if not rows:
    fails.append("부록 B 표를 찾지 못함")

def resolve(path):
    is_len = path.startswith("len(") and path.endswith(")")
    if is_len: path = path[4:-1]
    cur = committed
    for part in [p.strip() for p in path.split(" > ")]:
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            if part not in cur: raise KeyError(part)
            cur = cur[part]
    return len(cur) if is_len else cur

def same(expected_str, actual):
    if isinstance(actual, (int, float)) and not isinstance(actual, bool):
        try:
            return abs(float(expected_str) - float(actual)) < 1e-6
        except ValueError:
            return False
    return str(actual) == expected_str

ok = 0
for val, meaning, key in rows:
    try:
        actual = resolve(key)
    except (KeyError, IndexError, ValueError) as e:
        fails.append(f"키 없음: {key}  ({meaning}) — {e!r}"); continue
    if same(val, actual): ok += 1
    else: fails.append(f"값 불일치: {meaning} — 보고서 {val} / JSON {actual}  [{key}]")

print(f"  {'✅' if ok == len(rows) else '❌'} 부록 B 숫자 {ok}/{len(rows)} 개가 JSON 과 일치")

# ── 보고서 본문에 나오는 주요 숫자가 부록 B 에도 있는지 (누락 방지) ───
body = md.split("## 부록 B.")[0]
must = ["86분", "120초", "26.2°", "55.37 NM", "1.149 NM", "1.144 NM", "69.3", "13.77", "0.4 NM", "23:32:37"]
missing = [s for s in must if s not in body]
if missing: fails.append(f"본문에서 기대한 숫자 표현이 없음: {missing}")
else: print(f"  ✅ 본문 핵심 숫자 표현 {len(must)}개 확인")

print()
for f in fails: print("  ❌", f)
print("  실패 0건" if not fails else f"  {len(fails)}건 실패")
sys.exit(0 if not fails else 1)
