# Claude Code 개발 스킬 묶음

두 갈래다. **앞으로 만들 것**을 다루는 스킬과, **이미 있는 것**을 다루는 스킬.

## 어느 걸 쓸지 모르겠으면

| 스킬 | 부르는 법 | 하는 일 |
| --- | --- | --- |
| [route](route/SKILL.md) | `/route <요청>` | 알아서 판단해서 조합·실행. `dispatcher` 에이전트가 저장소를 조사하고 계획을 짜면, 승인받아 그대로 진행 |

## 앞으로 만들 것

| 스킬 | 부르는 법 | 하는 일 |
| --- | --- | --- |
| [set-goal](set-goal/SKILL.md) | `/set-goal <주제>` | 막연한 아이디어 → 측정 가능한 목표, 성공 기준, 비목표, DoD |
| [interview](interview/SKILL.md) | `/interview <주제>` | 한 번에 한 질문씩 요구사항 캐내기 (discover 모드) |
| [interview](interview/SKILL.md) | `/interview grill` · `grill me` | 계획을 5축으로 적대적 심문 — 허점 먼저 찾기 (grill 모드) |
| [spec](spec/SKILL.md) | `/spec <기능>` | 명세서 한 장 쓰기 (무엇을·왜만, 구현 방법 금지) |
| [spec](spec/SKILL.md) | `/spec review <파일>` | 기존 명세를 10개 항목으로 점검 |
| [sdd](sdd/SKILL.md) | `/sdd <기능>` | 명세 우선 개발: spec.md → plan.md → tasks.md → 구현 |
| [tdd](tdd/SKILL.md) | `/tdd <대상>` | RED → GREEN → REFACTOR 강제 |
| [dev-loop](dev-loop/SKILL.md) | `/dev-loop <슬러그>` | 위 넷을 게이트로 묶은 전체 파이프라인 |

## 이미 있는 것

| 스킬 | 부르는 법 | 하는 일 |
| --- | --- | --- |
| [orient](orient/SKILL.md) | `/orient [경로]` | 처음 보는 코드 20분 파악 — 진입점·흐름·경계·위험 지점 지도 |
| [adr](adr/SKILL.md) | `/adr <결정>` | 기술 결정 하나를 기록 — 대안, 대가, 되돌리는 법까지 |
| [handoff](handoff/SKILL.md) | `/handoff` | 중단하며 상태 넘기기 — 다음 할 일을 파일:줄 로 |
| [handoff](handoff/SKILL.md) | `/handoff resume` | 최근 인수인계를 읽고 검증한 뒤 이어가기 |

## 어떤 걸 언제 쓰나

```
뭘 만들지 모르겠다            → /set-goal
만들 건 알겠는데 상세가 흐리다  → /interview
계획은 섰는데 자신이 없다      → /interview grill
요구사항을 문서로 남겨야 한다   → /spec
남이 쓴 명세가 미덥지 않다     → /spec review
무엇을 만들지 분명하다         → /sdd
지금 이 함수를 짜야 한다       → /tdd
처음부터 끝까지 제대로         → /dev-loop

이 코드 뭐지                  → /orient
왜 이렇게 했더라 (남길 때)     → /adr
오늘 여기까지                 → /handoff
어디까지 했더라               → /handoff resume
버그가 났다                   → /debug  (Claude Code 내장, 이 묶음 아님)

위 중 뭘 쓸지 모르겠다        → /route
```

## dispatcher 에이전트

`.claude/agents/dispatcher.md` — 요청을 받아 **어떤 스킬을 어떤 순서로 쓸지 판단**하는 서브에이전트.

역할이 나뉘어 있다:

| | dispatcher | 본 세션 |
| --- | --- | --- |
| 저장소 조사 · 계획 수립 | ⭕ | |
| 사용자와 대화 | ❌ 불가 | ⭕ |
| 파일 수정 | ❌ 안 함 | ⭕ |

`interview` · `set-goal` · `grill` 은 사용자에게 묻고 답을 기다리는 스킬이라
서브에이전트 안에서는 작동하지 않는다. 그래서 **판단만** 떼어 맡기고 실행은 본 세션이 한다.
dispatcher 가 모르는 것은 질문하지 않고 `물어볼 것` 목록으로 돌려주며, 본 세션이 대신 묻는다.

판단 기준의 핵심은 **요청 크기**다. XS(오타·한 줄)면 스킬을 하나도 쓰지 않는 게 정답이고,
가장 흔한 실패는 작은 일에 파이프라인을 씌우는 것이다.

`spec` 과 `sdd` 는 겹쳐 보이지만 범위가 다르다.
`spec` 은 **명세 문서 한 장**에서 끝나고, `sdd` 는 **명세 → 계획 → 작업 → 구현** 전체를 게이트로 묶는다.
문서만 필요하면 `/spec`, 끝까지 갈 거면 `/sdd`.

작은 일(오타 수정, 한 줄 변경)에는 쓰지 않는다. `/dev-loop` 는 특히 과하다.

## grill 모드에 대해

`grill me` 는 **계획을 공격해서 약한 곳을 미리 찾는** 모드다. 사람이 아니라 아이디어를 친다.

- 시작 전에 동의를 받는다
- 5축(근거 · 범위 · 실패 · 대안 · 검증)으로 축마다 최대 2발
- "모르겠다"는 정당한 답 — 기록하고 넘어간다
- "그만"이라고 하면 즉시 멈추고 정리한다

## 설치

이 저장소 안에서는 이미 동작한다 (`.claude/skills/` 에 있음).

다른 프로젝트에서도 쓰려면 사용자 전역 폴더로 복사한다.

Windows (PowerShell):

```bash
Copy-Item -Recurse -Force .\.claude\skills\* "$env:USERPROFILE\.claude\skills\"
```

macOS / Linux:

```bash
cp -R ./.claude/skills/* ~/.claude/skills/
```

복사 후 `/route`, `/set-goal`, `/interview`, `/spec`, `/sdd`, `/tdd`, `/dev-loop`, `/orient`, `/adr`, `/handoff` 를 어디서든 쓸 수 있다.
(스킬은 폴더를 열 때 로드된다. 이미 그 폴더에서 세션이 열려 있었다면 새 세션을 시작한다.)

`dispatcher` 에이전트도 함께 쓰려면 agents 폴더도 복사한다.

```bash
Copy-Item -Recurse -Force .\.claude\agents\* "$env:USERPROFILE\.claude\agents\"
```

에이전트는 스킬과 달리 **새 세션에서만 로드된다.** 복사 후 세션을 다시 시작할 것.
`/route` 는 dispatcher 없이도 동작하지만, 그때는 판단을 본 세션이 직접 한다.

## 이름 규칙 주의

스킬 이름이 Claude Code 내장 명령어와 겹치면 **조용히 등록되지 않는다.**
`goal` 이 그래서 `set-goal` 이 됐다. 새 스킬을 추가한 뒤에는 목록에 실제로 떴는지 확인할 것.

확인된 충돌: `goal`, `plan`, `tasks` — 전부 내장 명령어라 스킬 이름으로 못 쓴다.
`debug` 는 이미 스킬이 존재하므로 만들지 않았다. `/debug` 를 그대로 쓴다.

의도적으로 만들지 않은 것: 코드 리뷰(`/code-review`), 보안 점검(`/security-review`),
리팩터링(`/simplify`), CLAUDE.md 생성(`/init`) — 전부 내장 기능이 이미 있다.

## 구조

각 스킬은 `SKILL.md` 하나로 끝난다. YAML 프론트매터의 `description` 이 언제 이 스킬이 켜질지를 결정하므로,
동작을 바꾸고 싶으면 본문을, 켜지는 조건을 바꾸고 싶으면 `description` 을 고친다.

에이전트는 `.claude/agents/<이름>.md` 한 장이다. 프론트매터에 `name`, `description`,
`tools`(쓸 수 있는 도구 제한), `model` 을 적는다. dispatcher 는 읽기 도구만 갖고 있어서
구조적으로 파일을 못 고친다.

```
.claude/
├── agents/
│   └── dispatcher.md     라우팅 판단 전담
└── skills/
    ├── route/SKILL.md        판단 + 실행 진입점
    │
    ├── set-goal/SKILL.md     ┐
    ├── interview/SKILL.md    │
    ├── spec/SKILL.md         ├ 앞으로 만들 것
    ├── sdd/SKILL.md          │
    ├── tdd/SKILL.md          │
    ├── dev-loop/SKILL.md     ┘
    │
    ├── orient/SKILL.md       ┐
    ├── adr/SKILL.md          ├ 이미 있는 것
    └── handoff/SKILL.md      ┘
```
