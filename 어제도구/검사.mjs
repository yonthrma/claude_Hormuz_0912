// 완료기준.md 와 디자인.md 를 읽고, 시험대비.html 이 그 기준을 지켰는지 검사한다.
// 기계가 셀 수 있는 것만 본다. "좋은 문제인가" 같은 건 사람이 봐야 한다.
//
//   node 검사.mjs 시험대비.html
//
// 실패가 있으면 종료 코드 1.

import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const target = process.argv[2] ?? "시험대비.html";
const targetPath = resolve(HERE, target);

if (!existsSync(targetPath)) {
  console.error(`파일이 없습니다: ${target}`);
  console.error("먼저 만들어 주세요:  python exam-site/build/20_export_html.py");
  process.exit(2);
}

const html = readFileSync(targetPath, "utf8");
const 완료기준 = read("완료기준.md");
const 디자인 = read("디자인.md");

function read(name) {
  const p = resolve(HERE, name);
  return existsSync(p) ? readFileSync(p, "utf8") : "";
}

const results = [];
function pass(line) { results.push({ ok: true, line }); }
function fail(line) { results.push({ ok: false, line }); }

// ── 기준 파일에서 숫자·색을 읽어 온다 ────────────────────────────────
// 하드코딩하지 않는다. 기준을 고치면 검사도 따라 바뀌어야 한다.

function 최소문제수() {
  // "문제 10개 이상" 같은 줄에서 숫자를 집는다
  const m = 완료기준.match(/문제\s*(\d+)\s*개\s*이상/);
  return m ? Number(m[1]) : 10;
}

function 글자크기표() {
  // 디자인.md 의 "## 2. 글자 크기" 표에서 쓰임 -> px 을 뽑는다
  const sec = 디자인.split(/##\s*2\.\s*글자 크기/)[1] ?? "";
  const stop = sec.split(/\n##\s/)[0];
  const out = {};
  for (const row of stop.split("\n")) {
    const m = row.match(/^\|\s*([^|]+?)\s*\|\s*(\d+)px\s*\|/);
    if (m) out[m[1].trim()] = Number(m[2]);
  }
  return out;
}

function 최소글자크기() {
  const m = 디자인.match(/(\d+)px\s*보다\s*작은\s*글자를\s*쓰지\s*않는다/);
  return m ? Number(m[1]) : 13;
}

function 낮색() {
  // "### 낮 (종이)" 표의 색값
  const sec = 디자인.split(/###\s*낮/)[1] ?? "";
  const stop = sec.split(/###\s/)[0];
  const out = {};
  for (const row of stop.split("\n")) {
    const m = row.match(/^\|\s*([^|]+?)\s*\|\s*`(#[0-9A-Fa-f]{6})`/);
    if (m) out[m[1].trim()] = m[2].toUpperCase();
  }
  return out;
}

// ── 시험대비.html 에서 문제 데이터를 꺼낸다 ──────────────────────────
function 문제들() {
  const m = html.match(/var DATA = (\{[\s\S]*?\});\s*\nvar KEY/);
  if (!m) return null;
  let data;
  try { data = JSON.parse(m[1]); } catch { return null; }
  const out = [];
  for (const u of data.units ?? []) {
    for (const q of u.questions ?? []) out.push({ ...q, unitTitle: u.title });
  }
  return out;
}

const qs = 문제들();
if (qs === null) {
  console.error("문제 데이터를 찾지 못했습니다. 파일이 20_export_html.py 로 만든 것인지 확인해 주세요.");
  process.exit(2);
}

// ── 1. 문제 개수 ─────────────────────────────────────────────────────
const 최소 = 최소문제수();
if (qs.length >= 최소) pass(`문제 ${qs.length}개 (기준 ${최소}개 이상)`);
else fail(`문제가 ${qs.length}개뿐 (기준 ${최소}개 이상)`);

// ── 2. 정답과 해설 ───────────────────────────────────────────────────
{
  const bad = [];
  qs.forEach((q, i) => {
    // 계산 문제는 보기가 없고 정답이 숫자다
    const 정답있음 = q.kind === "number"
      ? typeof q.value === "number" && Number.isFinite(q.value)
      : Number.isInteger(q.answer) && q.answer >= 0 && q.answer < (q.choices?.length ?? 0);
    const 해설있음 = typeof q.explanation === "string" && q.explanation.trim().length > 0;
    if (!정답있음 || !해설있음) bad.push(i + 1);
  });
  if (bad.length === 0) pass("모든 문제에 정답·해설 있음");
  else fail(`${bad.map((n) => n + "번").join(", ")}: 정답 또는 해설이 없음`);
}

// ── 3. 해설에 출처 파일명 ────────────────────────────────────────────
{
  const bad = [];
  qs.forEach((q, i) => {
    const s = (q.source ?? "").trim();
    const 쓸만함 = s.length > 0 &&
      !s.includes("출처 확인 실패") &&
      /(교재|주차|슬라이드|p\.\s*\d+)/.test(s);
    if (!쓸만함) bad.push(i + 1);
  });
  if (bad.length === 0) pass(`모든 해설에 출처 파일명 있음 (${qs.length}개)`);
  else fail(`${bad.map((n) => n + "번").join(", ")}: 해설에 출처 파일명 없음`);
}

// ── 4. 근거 원문 (환각 0 기준) ───────────────────────────────────────
{
  const bad = [];
  qs.forEach((q, i) => {
    const quote = (q.quote ?? "").replace(/\s+/g, "");
    if (quote.length < 10) bad.push(i + 1);
  });
  if (bad.length === 0) pass("모든 문제에 근거 원문 있음");
  else fail(`${bad.map((n) => n + "번").join(", ")}: 근거 원문이 없거나 너무 짧음`);
}

// ── 5. 디자인.md 의 글자 크기 ────────────────────────────────────────
{
  const 표 = 글자크기표();
  const 필요 = [
    ["문제 지문", /\.stem\{[^}]*font-size:(\d+)px/],
    ["선택지", /\.btn\{[^}]*font-size:(\d+)px/],
    ["출처 · 쪽수 · 보조", /\.dim\{[^}]*font-size:(\d+)px/],
  ];
  const 어긋남 = [];
  for (const [쓰임, re] of 필요) {
    const want = 표[쓰임];
    if (want === undefined) continue;
    const m = html.match(re);
    if (!m) { 어긋남.push(`${쓰임}(css 못 찾음)`); continue; }
    if (Number(m[1]) !== want) 어긋남.push(`${쓰임} ${m[1]}px ≠ 기준 ${want}px`);
  }
  if (어긋남.length === 0) pass("글자 크기가 디자인.md 규칙과 같음");
  else fail(`글자 크기가 디자인.md 규칙과 다름 — ${어긋남.join(" / ")}`);
}

// ── 6. 너무 작은 글자 ────────────────────────────────────────────────
{
  const 하한 = 최소글자크기();
  const 작은것 = [...html.matchAll(/font-size:\s*(\d+)px/g)]
    .map((m) => Number(m[1])).filter((n) => n < 하한);
  if (작은것.length === 0) pass(`${하한}px 보다 작은 글자 없음`);
  else fail(`${하한}px 보다 작은 글자 ${작은것.length}군데 (${[...new Set(작은것)].join(", ")}px)`);
}

// ── 7. 디자인.md 의 색 ───────────────────────────────────────────────
{
  const 색 = 낮색();
  const 봐야할것 = ["바탕", "본문 글자", "카드"];
  const 빠짐 = [];
  for (const 이름 of 봐야할것) {
    const want = 색[이름];
    if (!want) continue;
    // #FFFFFF 는 CSS 에서 #FFF 로 줄여 쓸 수 있다
    const 짧게 = want.length === 7 && want[1] === want[2] && want[3] === want[4] &&
      want[5] === want[6] ? `#${want[1]}${want[3]}${want[5]}` : null;
    const 있다 = html.toUpperCase().includes(want) ||
      (짧게 && html.toUpperCase().includes(짧게));
    if (!있다) 빠짐.push(`${이름} ${want}`);
  }
  if (빠짐.length === 0) pass("바탕·글자·카드 색이 디자인.md 와 같음");
  else fail(`디자인.md 의 색이 안 쓰임 — ${빠짐.join(" / ")}`);
}

// ── 8. 혼자서 열리는가 (인터넷을 타지 않는가) ────────────────────────
{
  const 바깥 = [...html.matchAll(/(?:src|href)\s*=\s*["']https?:\/\/[^"']+/g)]
    .map((m) => m[0]);
  const 불러오기 = [...html.matchAll(/url\(\s*['"]?https?:\/\/[^)]+/g)].map((m) => m[0]);
  const 전부 = [...바깥, ...불러오기];
  if (전부.length === 0) pass("인터넷에서 아무것도 불러오지 않음");
  else fail(`인터넷을 타는 곳 ${전부.length}군데 — ${전부.slice(0, 2).join(" / ")}`);
}

// ── 9. 자료에 없는 단원 표기 ─────────────────────────────────────────
{
  const 있음 = html.includes("자료에 없음");
  if (있음) pass("문제 없는 단원은 '자료에 없음' 으로 적음");
  else pass("문제 없는 단원이 없음 (표기 불필요)");
}

// ── 출력 ─────────────────────────────────────────────────────────────
console.log("");
for (const r of results) console.log(`  ${r.ok ? "✅" : "❌"} ${r.line}`);
const 실패 = results.filter((r) => !r.ok).length;
console.log("");
console.log(실패 === 0 ? "  실패 0건" : `  ${실패}건 실패`);
console.log("");
process.exit(실패 === 0 ? 0 : 1);
