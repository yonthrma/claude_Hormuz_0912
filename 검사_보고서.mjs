// 어제도구/검사.mjs 를 오늘 과제(보고서 .md)에 맞게 확장한 것.
// 기계가 셀 수 있는 것만 본다: 4문항 구조, 근거 표기, 출처 검증, 숫자 재현.
//
//   node 검사_보고서.mjs [보고서_yonthrma.md]
//
// 실패가 있으면 종료 코드 1.

import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const HERE = dirname(fileURLToPath(import.meta.url));
const target = process.argv[2] ?? "보고서_yonthrma.md";
const path = resolve(HERE, target);
if (!existsSync(path)) { console.error(`파일이 없습니다: ${target}`); process.exit(2); }

const md = readFileSync(path, "utf8");
const 리서치 = existsSync(resolve(HERE, "리서치_외부정세_20260912.md"))
  ? readFileSync(resolve(HERE, "리서치_외부정세_20260912.md"), "utf8") : "";

const results = [];
const pass = (l) => results.push({ ok: true, l });
const fail = (l) => results.push({ ok: false, l });

// ── 1. 교안 115p 4문항이 모두 있는가 (CLAUDE.md 산출물 규격) ─────────
{
  const need = [["무엇이 문제인가", /^##\s*1\.\s*무엇이 문제인가/m],
                ["무엇이 근거인가", /^##\s*2\.\s*무엇이 근거인가/m],
                ["무엇을 할 것인가", /^##\s*3\.\s*무엇을 할 것인가/m],
                ["무엇을 모르는가", /^##\s*4\.\s*무엇을 모르는가/m]];
  const miss = need.filter(([, re]) => !re.test(md)).map(([n]) => n);
  if (miss.length === 0) pass("4문항(문제/근거/할 것/모르는 것) 섹션 모두 있음");
  else fail(`섹션 빠짐: ${miss.join(", ")}`);
}

// ── 2. "무엇을 모르는가" 가 비어 있지 않은가 ─────────────────────────
{
  const sec = md.split(/^##\s*4\.\s*무엇을 모르는가/m)[1]?.split(/^##\s/m)[0] ?? "";
  const rows = sec.split("\n").filter((l) => /^\|\s*\d+\s*\|/.test(l));
  if (rows.length >= 5) pass(`모르는 것 ${rows.length}개 (5개 이상)`);
  else fail(`모르는 것이 ${rows.length}개뿐`);
}

// ── 3. 6개 결정이 '할 것' 에 전부 있는가 (CLAUDE.md 본부장 결정 6개) ──
{
  const sec = md.split(/^##\s*3\.\s*무엇을 할 것인가/m)[1]?.split(/^##\s*4\./m)[0] ?? "";
  const need = ["선원", "선박·화물", "나머지 배", "실증 특례", "보험", "대외 발표"];
  const miss = need.filter((k) => !sec.includes(k));
  if (miss.length === 0) pass("결정 6개(선원/선박·화물/나머지 배/실증 특례/보험/대외 발표) 모두 다룸");
  else fail(`결정 항목 빠짐: ${miss.join(", ")}`);
  if (/최악 시나리오/.test(sec)) pass("최악 시나리오 항목 있음"); else fail("최악 시나리오 항목 없음");
}

// ── 4. 내부 근거 표기 [파일 / 위치] 가 충분한가 ─────────────────────
{
  const n = (md.match(/\[[^\]\n]*\.(md|csv|pdf)[^\]\n]*\]/g) ?? []).length;
  if (n >= 60) pass(`내부 근거 표기 ${n}곳`); else fail(`내부 근거 표기가 ${n}곳뿐 (60곳 이상 기대)`);
}

// ── 5. 외부 주장에 출처가 있고, 그 출처가 '본문 확인' 목록에 있는가 ─
{
  const urls = [...md.matchAll(/https?:\/\/[^\s)\]>]+/g)].map((m) => m[0]);
  // 보고서 본문은 URL 대신 [출처, 발행일] 로 쓰고 URL 은 리서치 문서에 둔다.
  // 그러므로 보고서에 나온 외부 출처 이름이 리서치 §9 '본문 확인' 표에 있는지 본다.
  const names = ["Windward", "gCaptain", "Al Jazeera", "Korea Herald", "Korea Times", "MBC", "시대일보", "헤럴드경제",
                 "외교부", "Maritime Executive", "Clyde & Co", "The Swedish Club", "한국일보", "Opinio Juris",
                 "UN DOALOS", "IMO", "DNV", "China P&I", "Institute War and Strikes Clauses"];
  const used = names.filter((n) => md.includes(n));
  const verifiedSec = 리서치.split("### 본문 확인")[1]?.split("### 제목")[0] ?? "";
  const notVerified = used.filter((n) => !verifiedSec.includes(n) && !verifiedSec.includes(n.replace("The ", "")));
  if (used.length > 0 && notVerified.length === 0) pass(`외부 출처 ${used.length}종 모두 리서치 §9 '본문 확인' 표에 있음`);
  else fail(`검증표에 없는 외부 출처: ${notVerified.join(", ") || "(외부 출처 없음)"}`);
  // 제목만 본 출처가 본문에 쓰였는가
  const titleOnly = ["Japan Times", "Manila Times", "Forbes", "SAFETY4SEA", "LIS-114", "MSC.595"];
  const body = md.split("## 4. 무엇을 모르는가")[0];
  const leaked = titleOnly.filter((n) => body.includes(n));
  if (leaked.length === 0) pass("제목만 확인한 출처가 본문(1~3장)에 쓰이지 않음");
  else fail(`제목만 확인한 출처가 본문에 쓰임: ${leaked.join(", ")}`);
  if (urls.length >= 3) pass(`링크 ${urls.length}개 (리서치 문서·부록 연결)`); else fail("링크가 3개 미만");
}

// ── 6. 단정·낙관 표현 (CLAUDE.md 낙관 금지) ─────────────────────────
{
  const banned = ["확실히 문제없", "반드시 석방", "곧 풀릴", "우리 책임은 없", "시스템은 문제없다."];
  const body = md.split("## 부록")[0];
  const hit = banned.filter((b) => body.includes(b));
  if (hit.length === 0) pass("단정·낙관 표현 없음"); else fail(`단정·낙관 표현: ${hit.join(" / ")}`);
  const vague = (body.match(/대체로|대부분|많은 |어느 정도/g) ?? []).length;
  if (vague <= 3) pass(`애매한 표현(대체로/대부분/많은/어느 정도) ${vague}회 (3회 이하)`);
  else fail(`애매한 표현 ${vague}회 — 숫자로 바꿀 것`);
}

// ── 7. 숫자 재현 (python 테스트 위임) ────────────────────────────────
{
  const r = spawnSync("python", [resolve(HERE, "분석/테스트_숫자재현.py"), path],
    { encoding: "utf8", env: { ...process.env, PYTHONIOENCODING: "utf-8" } });
  const out = (r.stdout ?? "") + (r.stderr ?? "");
  if (r.status === 0) pass("숫자 재현 테스트 통과 (부록 B ↔ JSON ↔ 원본 CSV)");
  else fail("숫자 재현 테스트 실패 — 아래 출력 참고");
  console.log(out.split("\n").map((l) => "     " + l).join("\n"));
}

console.log("");
for (const r of results) console.log(`  ${r.ok ? "✅" : "❌"} ${r.l}`);
const n = results.filter((r) => !r.ok).length;
console.log("");
console.log(n === 0 ? "  실패 0건" : `  ${n}건 실패`);
process.exit(n === 0 ? 0 : 1);
