// 디자인.md 를 읽어서 보고서_yonthrma.html / 발표_yonthrma.html 이 모양 규칙을 지켰는지 검사한다.
// 기준을 코드에 박지 않는다 — 색·글자 크기·최소 크기는 디자인.md 표에서 읽는다.
//
//   node 검사_HTML.mjs 보고서_yonthrma.html
//   node 검사_HTML.mjs 발표_yonthrma.html
//
// 실패가 있으면 종료 코드 1.

import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve, basename } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const target = process.argv[2] ?? "보고서_yonthrma.html";
const path = resolve(HERE, target);
if (!existsSync(path)) { console.error(`파일이 없습니다: ${target}`); process.exit(2); }
const html = readFileSync(path, "utf8");
const 디자인 = readFileSync(resolve(HERE, "디자인.md"), "utf8");
const 보고서md = existsSync(resolve(HERE, "보고서_yonthrma.md")) ? readFileSync(resolve(HERE, "보고서_yonthrma.md"), "utf8") : "";
const is발표 = basename(target).startsWith("발표");

const results = [];
const pass = (l) => results.push({ ok: true, l });
const fail = (l) => results.push({ ok: false, l });

// ── 디자인.md 에서 기준 읽기 ─────────────────────────────────────────
function 낮색() {
  const sec = 디자인.split(/###\s*낮/)[1]?.split(/\n###\s/)[0] ?? "";
  const out = {};
  for (const row of sec.split("\n")) {
    const m = row.match(/^\|\s*([^|]+?)\s*\|\s*`(#[0-9A-Fa-f]{6})`/);
    if (m) out[m[1].trim()] = m[2].toUpperCase();
  }
  return out;
}
function 뜻색() {
  const sec = 디자인.split(/###\s*뜻이 있는 색/)[1]?.split(/\n##\s/)[0] ?? "";
  const out = [];
  for (const row of sec.split("\n")) {
    const m = row.match(/^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|\s*`(#[0-9A-Fa-f]{6})`\s*\|\s*`(#[0-9A-Fa-f]{6})`/);
    if (m) out.push({ 뜻: m[1].trim(), 기호: m[2], 글자: m[3].toUpperCase(), 바탕: m[4].toUpperCase() });
  }
  return out;
}
function 글자크기표(절) {
  const sec = 디자인.split(/##\s*2\.\s*글자 크기/)[1]?.split(new RegExp(`###\\s*${절}`))[1]?.split(/\n###\s|\n##\s/)[0] ?? "";
  const out = {};
  for (const row of sec.split("\n")) {
    const m = row.match(/^\|\s*([^|]+?)\s*\|\s*(\d+)px\s*\|/);
    if (m) out[m[1].trim()] = Number(m[2]);
  }
  return out;
}
function 최소글자() {
  const m = is발표
    ? 디자인.match(/슬라이드에서는\s*(\d+)px\s*보다\s*작은\s*글자를\s*쓰지\s*않는다/)
    : 디자인.match(/\*\*(\d+)px\s*보다\s*작은\s*글자를\s*쓰지\s*않는다/);
  return m ? Number(m[1]) : (is발표 ? 18 : 13);
}
function 슬라이드수() {
  const m = 디자인.match(/\*\*(\d+)장\.\*\*/);
  return m ? Number(m[1]) : 12;
}

// ── 1. 색 ────────────────────────────────────────────────────────────
{
  const 색 = 낮색();
  const 필수 = ["바탕", "본문 글자", "보조 글자", "포인트"];
  const 빠짐 = 필수.filter((k) => 색[k] && !html.toUpperCase().includes(색[k]));
  if (Object.keys(색).length === 0) fail("디자인.md 낮 색 표를 못 읽음");
  else if (빠짐.length === 0) pass(`디자인.md 낮 색 ${필수.length}종(바탕·본문·보조·포인트) 모두 쓰임`);
  else fail(`디자인.md 색이 안 쓰임: ${빠짐.map((k) => `${k} ${색[k]}`).join(" / ")}`);
  // 문서에 없는 색을 쓰는가 (허용: 디자인.md 에 나온 색 전부 + #FFF/#fff 화이트)
  const 허용 = new Set([...Object.values(색), ...뜻색().flatMap((c) => [c.글자, c.바탕]), "#FFFFFF", "#FFF"]);
  for (const c of 뜻색()) { /* 테두리 색 */ }
  const 테두리 = [...디자인.matchAll(/`(#[0-9A-Fa-f]{6})`/g)].map((m) => m[1].toUpperCase());
  테두리.forEach((c) => 허용.add(c));
  const 쓰인 = [...new Set([...html.matchAll(/#[0-9A-Fa-f]{6}\b/g)].map((m) => m[0].toUpperCase()))];
  const 무단 = 쓰인.filter((c) => !허용.has(c));
  if (무단.length === 0) pass(`디자인.md 밖의 색 없음 (쓰인 색 ${쓰인.length}종)`);
  else fail(`디자인.md 에 없는 색: ${무단.join(", ")}`);
}

// ── 2. 뜻이 있는 색은 기호와 함께 ───────────────────────────────────
{
  const 뜻 = 뜻색();
  const 빠짐 = [];
  for (const c of 뜻) {
    if (!html.toUpperCase().includes(c.글자)) continue; // 안 쓴 색은 검사 안 함
    if (!html.includes(c.기호)) 빠짐.push(`${c.뜻}(${c.기호})`);
  }
  if (빠짐.length === 0) pass("뜻이 있는 색은 모두 기호(✔ ▲ ● ✕)와 함께 쓰임");
  else fail(`색만 있고 기호 없음: ${빠짐.join(", ")}`);
}

// ── 3. 글자 크기 ─────────────────────────────────────────────────────
{
  const 표 = 글자크기표(is발표 ? "발표" : "보고서");
  const 필요 = is발표
    ? [["슬라이드 제목", /h1\{[^}]*font-size:(\d+)px/], ["핵심 숫자 (한 장에 하나)", /\.num\{[^}]*font-size:(\d+)px/], ["본문 뼈대", /\.body\{[^}]*font-size:(\d+)px/], ["파일명 · 근거 · 출처", /\.src\{[^}]*font-size:(\d+)px/], ["슬라이드 번호 · 시간 구간", /\.hdr\{[^}]*font-size:(\d+)px/]]
    : [["문서 제목", /h1\{[^}]*font-size:(\d+)px/], ["절 제목 (1. 2. 3. 4.)", /h2\{[^}]*font-size:(\d+)px/], ["본문", /body\{[^}]*font-size:(\d+)px/], ["표 본문", /table\{[^}]*font-size:(\d+)px/], ["근거 표기 · 출처 · 부제", /\.cite\{[^}]*font-size:(\d+)px/]];
  const 어긋남 = [];
  for (const [쓰임, re] of 필요) {
    const want = 표[쓰임];
    if (want === undefined) { 어긋남.push(`${쓰임}(디자인.md 표에 없음)`); continue; }
    const m = html.match(re);
    if (!m) { 어긋남.push(`${쓰임}(css 못 찾음)`); continue; }
    if (Number(m[1]) !== want) 어긋남.push(`${쓰임} ${m[1]}px ≠ 기준 ${want}px`);
  }
  if (어긋남.length === 0) pass(`글자 크기 ${필요.length}종이 디자인.md ${is발표 ? "발표" : "보고서"} 표와 같음`);
  else fail(`글자 크기 불일치 — ${어긋남.join(" / ")}`);
}

// ── 4. 최소 글자 ─────────────────────────────────────────────────────
{
  const 하한 = 최소글자();
  const 작은 = [...html.matchAll(/font-size:\s*(\d+)px/g)].map((m) => Number(m[1])).filter((n) => n < 하한);
  if (작은.length === 0) pass(`${하한}px 보다 작은 글자 없음`);
  else fail(`${하한}px 보다 작은 글자 ${작은.length}곳 (${[...new Set(작은)].join(", ")}px)`);
  const 얇은 = [...html.matchAll(/font-weight:\s*(\d+)/g)].map((m) => Number(m[1])).filter((n) => n < 400);
  if (얇은.length === 0) pass("굵기 400 미만 없음"); else fail(`굵기 400 미만 ${얇은.length}곳`);
}

// ── 5. 인터넷 로드 없음 ──────────────────────────────────────────────
{
  const 바깥 = [...html.matchAll(/(?:src|href)\s*=\s*["']https?:\/\/[^"']+/g)].map((m) => m[0])
    .filter((s) => !/href\s*=\s*["']https?:\/\/(www\.|biz\.|imnews\.|news\.|maritime|windward|gcaptain|opiniojuris|under-tech|un\.org|korea\.kr|mofa|hankookilbo|swedishclub|chinapandi|imo\.org|dnv|clydeco|aljazeera|koreaherald|koreatimes|sidae|lmalloyds)/.test(s));
  // 부록 A 의 출처 링크(사용자가 누르는 a href)는 허용. 글꼴·스크립트·이미지·CSS 로드만 금지.
  const 로드 = [...html.matchAll(/<(?:link|script|img)[^>]+(?:href|src)\s*=\s*["']https?:\/\//g)].length + [...html.matchAll(/url\(\s*['"]?https?:\/\//g)].length + [...html.matchAll(/@import/g)].length;
  if (로드 === 0) pass("글꼴·스크립트·이미지·CSS 를 인터넷에서 불러오지 않음");
  else fail(`인터넷 로드 ${로드}곳`);
}

// ── 6. 애니메이션·그림자·그라데이션 없음 ────────────────────────────
{
  const 금지 = [["transition", /transition\s*:/], ["animation", /animation\s*:|@keyframes/], ["box-shadow", /box-shadow\s*:/], ["gradient", /gradient\(/]];
  const hit = 금지.filter(([, re]) => re.test(html)).map(([n]) => n);
  if (hit.length === 0) pass("애니메이션·전환·그림자·그라데이션 없음"); else fail(`금지 스타일: ${hit.join(", ")}`);
  const 고정 = [...html.matchAll(/position\s*:\s*fixed/g)].length;
  // 발표의 진행 막대(3px)·힌트는 디자인.md 가 허용. 보고서는 고정 요소 금지.
  if (is발표 ? 고정 <= 2 : 고정 === 0) pass(is발표 ? `고정 요소 ${고정}개 (진행 막대·힌트만)` : "고정(fixed) 요소 없음");
  else fail(`고정 요소 ${고정}개`);
}

// ── 7. 표는 스크롤 상자 안 ───────────────────────────────────────────
if (!is발표) {
  const n표 = (html.match(/<table/g) ?? []).length;
  const n상자 = (html.match(/class="tbl"/g) ?? []).length;
  if (n표 > 0 && n표 === n상자 && /\.tbl\{[^}]*overflow-x:auto/.test(html)) pass(`표 ${n표}개 모두 가로 스크롤 상자 안`);
  else fail(`표 ${n표}개 중 스크롤 상자 ${n상자}개`);
}

// ── 8. 내용 규칙 ─────────────────────────────────────────────────────
if (is발표) {
  const n = (html.match(/<section class="slide/g) ?? []).length;
  const want = 슬라이드수();
  if (n === want) pass(`슬라이드 ${n}장 (디자인.md ${want}장)`); else fail(`슬라이드 ${n}장 ≠ ${want}장`);
  const 구간 = { "3분 · 문제": 4, "4분 · 근거": 5, "2분 · 결론": 2, "1분 · 모르는 것": 1 };
  const 어긋 = Object.entries(구간).filter(([k, v]) => (html.match(new RegExp(`data-seg="${k}"`, "g")) ?? []).length !== v).map(([k]) => k);
  if (어긋.length === 0) pass("구간별 장수 4/5/2/1"); else fail(`구간 장수 불일치: ${어긋.join(", ")}`);
  const 근거없음 = [...html.matchAll(/<section class="slide[\s\S]*?<\/section>/g)].map((m) => m[0]).filter((s) => !/class="src">[^<]*\.(md|csv|py|json)/.test(s)).length;
  if (근거없음 === 0) pass("모든 슬라이드 하단에 파일명 근거 있음"); else fail(`파일명 근거 없는 슬라이드 ${근거없음}장`);
  // 슬라이드의 숫자는 보고서 md 에 있어야 한다 (슬라이드에만 있는 숫자 금지)
  // 머리(시간 구간·번호)는 교안 116p 배분이라 제외
  const 숫자 = [...new Set([...html.replace(/<style[\s\S]*?<\/style>|<script[\s\S]*?<\/script>|<div class="hdr">[\s\S]*?<\/div>|<!--[\s\S]*?-->|data-seg="[^"]*"/g, "").matchAll(/\d+(?:[.,]\d+)?\s*(?:NM|초|분|명|kn|건|행|장|일|파일|%|번)/g)].map((m) => m[0].replace(/\s+/g, " ")))];
  const 없음 = 숫자.filter((s) => !보고서md.replace(/\s+/g, " ").includes(s) && !보고서md.includes(s.replace(/,/g, "")) && !/\d+ \/ 12|12장|\d+ ?장/.test(s));
  if (없음.length === 0) pass(`슬라이드 숫자 표현 ${숫자.length}개 모두 보고서 md 에 있음`);
  else fail(`보고서 md 에 없는 슬라이드 숫자: ${없음.join(", ")}`);
} else {
  const need = ["무엇이 문제인가", "무엇이 근거인가", "무엇을 할 것인가", "무엇을 모르는가"];
  const miss = need.filter((k) => !new RegExp(`<h2[^>]*>\\d\\. ${k}`).test(html));
  if (miss.length === 0) pass("4문항 h2 모두 있음"); else fail(`h2 빠짐: ${miss.join(", ")}`);
  const 칩 = (html.match(/class="cite"/g) ?? []).length;
  if (칩 >= 60) pass(`근거 칩 ${칩}개`); else fail(`근거 칩 ${칩}개 (60 이상 기대)`);
  const 미확인 = (html.match(/chip unk/g) ?? []).length;
  if (미확인 > 0) pass(`▲ 미확인 칩 ${미확인}개`); else fail("▲ 미확인 칩 없음");
  if (/class="decision"/.test(html)) pass("결정 필요 사항 카드(포인트 테두리) 있음"); else fail("결정 카드 없음");
  if (/<nav class="toc"/.test(html)) pass("목차 있음"); else fail("목차 없음");
  // md 와 내용 일치: md 의 부록 B 숫자 값이 html 에도 있는가
  const rows = (보고서md.split("## 부록 B.")[1] ?? "").split("\n## ")[0].split("\n").map((l) => l.match(/^\|\s*(.+?)\s*\|/)).filter(Boolean).map((m) => m[1]).filter((v) => v !== "값" && v !== "---");
  const 빠진값 = rows.filter((v) => !html.includes(v));
  if (rows.length > 0 && 빠진값.length === 0) pass(`부록 B 숫자 ${rows.length}개가 HTML 에도 그대로 있음 (md ↔ html 일치)`);
  else fail(`HTML 에 없는 부록 B 값: ${빠진값.slice(0, 5).join(", ")}`);
}

console.log("");
for (const r of results) console.log(`  ${r.ok ? "✅" : "❌"} ${r.l}`);
const n = results.filter((r) => !r.ok).length;
console.log("");
console.log(n === 0 ? "  실패 0건" : `  ${n}건 실패`);
process.exit(n === 0 ? 0 : 1);
