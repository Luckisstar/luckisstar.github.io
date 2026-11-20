---
layout: default
title: "[오픈소스 소개] Cloudflare security-audit-skill: 코딩 에이전트를 6단계 보안 감사관으로 만드는 스킬"
description: "Cloudflare가 공개한 security-audit 스킬의 6단계 감사 흐름, 커버리지 원장, 별도 검증 에이전트의 반증, findings.json 스키마와 검증기, 샌드박스 요구 사항, 2026년 9월 이후 멈춘 유지보수 현황을 정리했습니다."
date: 2026-11-20 11:00:00 +0900
categories: [opensource]
---

# [오픈소스 소개] Cloudflare security-audit-skill: 코딩 에이전트를 6단계 보안 감사관으로 만드는 스킬

- **저장소:** [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) · [공식 블로그: Build your own vulnerability harness](https://blog.cloudflare.com/build-your-own-vulnerability-harness/)
- **라이선스:** MIT (LICENSE 원문 기준, Copyright (c) 2025-2026 Cloudflare, Inc.)
- **언어:** 에이전트용 지침 Markdown 15개 파일(1,778줄)과 Node.js 검증 스크립트(JavaScript, 외부 의존성 없음)
- **현황 (2026-11-20 기준):** GitHub 스타 약 7.6만 개, 포크 약 5,100개. 릴리스와 태그는 없고, 커밋은 2026-06-18부터 2026-09-14까지 14개입니다.
- **유지보수 상태 (2026-11-20 기준):** 보관(archived)된 저장소는 아니지만, **마지막 커밋(2026-09-14) 이후 두 달 넘게 코드 변경과 PR 병합이 없습니다.** 마지막으로 병합된 PR은 2026-09-10의 #12입니다. 열린 이슈 52개와 열린 PR 84개가 쌓여 있고, 2026-09-15 이후 올라온 이슈 55개와 PR 90개 가운데 병합된 것은 없으며 닫힌 15건은 모두 작성자 본인이 닫았습니다. 이슈와 PR 157건 어디에도 라벨이나 담당자가 지정되어 있지 않고, GitHub API에서 저장소 협력자(COLLABORATOR)나 조직 멤버(MEMBER)로 표시되는 계정의 댓글과 리뷰도 찾지 못했습니다(조직 멤버십이 비공개인 계정은 API로 구분되지 않을 수 있습니다). README에는 지원 범위나 유지보수 정책에 대한 언급이 없고 연락처 이메일만 있습니다. 저장소 어디에도 중단이나 보관을 알리는 문구는 없으므로 "중단"이라고 단정할 수는 없지만, 지금은 열려 있는 문제를 사용자가 직접 감당해야 하는 상태로 보는 편이 안전합니다.
- **샌드박스 제약:** README와 `SKILL.md`는 감사 대상의 빌드, 테스트, 프로세스를 **OS가 강제하는 샌드박스 안에서만** 실행하라고 요구합니다(외부 네트워크 차단, 허용 목록으로 채운 빈 환경 변수, 자원 제한, 지정된 scratch 경로에만 쓰기). 이 조건을 갖추지 못하면 대상 코드를 실행하지 않고 해당 단서를 `needs_validation`(검증 필요) 상태로 남깁니다.
- **1회 실행의 한계:** README는 "자체 테스트에서 한 번의 실행은 반복 실행이 찾은 전체 취약점의 약 절반을 찾았다"고 밝힙니다. Cloudflare의 자체 발표이며 측정 대상과 횟수는 공개되지 않았습니다.
- **사용자 보고 사고:** 이슈 트래커에는 OS 샌드박스가 없는 Windows 11에서 에이전트가 "빈 환경"을 만들려다 실제 사용자 프로필(`~/.claude`, `~/.ssh` 등)을 지웠다는 보고([#128](https://github.com/cloudflare/security-audit-skill/issues/128), 2026-11-01)가 열려 있습니다. 제3자의 보고이고 필자가 재현하거나 관리자가 확인한 내용은 아니지만, 샌드박스 없는 환경에서 전체 감사를 맡기기 전에 알아 둘 만한 내용입니다.
- **이 글의 범위:** 이 스킬은 대상 코드를 직접 다루는 보안 도구이므로, **필자는 실제 감사를 실행하지 않았습니다.** 아래 내용은 저장소의 문서와 스키마, 검증 스크립트 소스, 공식 블로그를 읽고 정리한 것입니다.

## 한 줄 요약

**security-audit-skill은 코딩 에이전트에게 "정찰 → 커버리지 기반 탐색 → 반증 → 구조화 출력 → 재검증 → 보고서"의 6단계 보안 감사 절차를 따르게 하는 Agent Skill(지침 묶음)입니다.** Cloudflare가 사내 취약점 탐색 하네스를 만들 때 출발점으로 쓴 스킬을 공개한 것으로, 취약점을 찾은 에이전트와 그것을 검증하는 에이전트를 반드시 분리하고, 결과를 스키마로 검증되는 `findings.json`에 남기는 것이 핵심입니다. 자기 저장소를 병렬 서브에이전트가 있는 코딩 에이전트로 점검해 보려는 개발자와 보안 담당자, 그리고 자체 취약점 탐색 파이프라인을 설계하려는 팀에게 참고가 됩니다.

## 어떤 문제를 푸나

코딩 에이전트에게 "이 코드의 보안 취약점을 찾아 줘"라고만 했을 때 생기는 문제를, 이 스킬의 문서와 Cloudflare 블로그가 겨냥하는 지점 기준으로 정리하면 세 가지입니다.

- **어디를 봤는지 알 수 없습니다.** 에이전트는 눈에 띄는 파일 몇 개를 읽고 "인증 로직을 검토했다"고 말합니다. 보지 않은 영역이 어디인지는 보고서에 남지 않습니다.
- **스스로 찾은 것을 스스로 옳다고 합니다.** Cloudflare 블로그는 이를 "헌터가 자기 숙제를 채점하게 두면 자신이 낸 모든 것을 자신 있게 검증한다"고 표현합니다. 블로그가 든 실패 사례는 구체적입니다. 에이전트가 익스플로잇이 통하도록 소스를 고친 뒤 자기가 만든 버그를 보고하거나, "exec()는 실행한다, 따라서 치명적 취약점" 같은 동어반복 테스트를 씁니다.
- **모범 사례 위반을 취약점으로 부풀립니다.** 쿠키에 속성 하나가 빠졌다는 사실과, 그것으로 누가 무엇을 잃는지는 다른 문제입니다.

이 스킬은 세 문제를 각각 커버리지 원장(coverage ledger), 독립 검증 에이전트, "신뢰 경계와 결과가 있어야 취약점"이라는 판정 규칙으로 풉니다. `SKILL.md` 첫 문단은 "영향받는 주체, 자원, 보안 결과가 구체적이지 않은 후보는 확정된 발견이 아니다"라고 못 박습니다.

블로그에 따르면 Cloudflare는 약 450줄짜리 security-audit 스킬을 저장소 하나에 돌리며 실제 버그가 나올 때까지 프롬프트를 다듬었고, 그 뒤 오케스트레이션을 붙여 128개 저장소를 도는 사내 하네스로 키웠습니다(약 6주 소요, 자체 발표). 공개된 저장소는 그 "단일 저장소용 출발점"입니다. 다만 뒤에서 설명하듯 **블로그가 묘사한 초기 스킬과 지금 저장소의 내용은 꽤 다릅니다.**

## 핵심 개념

| 개념 | 설명 |
|---|---|
| 부모(Parent) | 감사를 조정하는 에이전트. `findings.json`, 원장, 보고서 같은 공유 파일을 쓰는 유일한 주체입니다 |
| 헌터(hunter) | 원장의 단위를 배정받아 취약점 후보를 찾는 서브에이전트. 자기 `scratch/` 디렉터리에만 쓸 수 있습니다 |
| 검증자(verifier) | 후보를 찾지 않은 새 에이전트. 후보를 반증하려고 시도합니다 |
| 커버리지 비평가 | 헌터 웨이브가 끝날 때마다 원장을 읽고 빠진 영역을 제안하는 에이전트. 발견이 아니라 커버리지만 제안합니다 |
| 커버리지 원장 | `coverage-ledger.json`. 진입 표면 × 신뢰 경계 × 하위 시스템 × 공격 유형 조합마다 한 단위씩 기록합니다 |
| 지문(fingerprint) | 같은 근본 원인에 붙는 소스 기반 식별자. 줄 번호, 웨이브, 에이전트, 심각도, 판정을 넣지 않아 실행 간에 유지됩니다 |
| 판정 3종 | `confirmed`(확정), `needs_validation`(검증 필요), `rejected`(기각) |
| 실행 프로필 | `quick`, `standard`(기본), `deep`. 넓이와 중복 검증 횟수만 바꾸고 증거 기준은 바꾸지 않습니다 |
| 동반 파일 | 도메인별 공격 유형 문서 10개(AI/LLM, 웹 프로토콜과 인증, 클라이언트 측, 메모리 안전성 등) |

세 판정의 구분이 이 스킬의 중심입니다. README의 정의는 이렇습니다.

- `confirmed`: 완전한 소스 추적(trace)과 제한된 범위에서 관찰한 결과가 있음. 심각도는 이 판정에만 붙습니다.
- `needs_validation`: 소스에 근거한 가설이지만, 정확히 어떤 사실이 풀리지 않았는지가 명시됨. 심각도가 없습니다.
- `rejected`: 검증 과정에서 반증된 후보. 이후 실행이 같은 주장을 반복하지 않도록 기록으로 남깁니다.

`SKILL.md`는 `needs_validation`이 "확신이 낮은 확정 취약점"이 아니라고 강조합니다. 배포 설정, 프록시 동작, ID 정책처럼 **저장소에 없는 사실이 결정적일 때, 있다고도 없다고도 가정하지 말고** 빠진 사실과 안전한 확인 방법을 적으라는 뜻입니다.

## 동작 원리

README와 `SKILL.md`, 단계별 문서를 기준으로 정리한 전체 감사(full audit) 흐름입니다.

```
 user: "security audit this codebase"
        │
        ▼
 Parent  (coordinates, sole writer of shared files)
        │  run-metadata.json  (profile, scope, budget, source ref)
        ▼
 Phase 1  Reconnaissance
        │  4 research agents (1a product/stack, 1b principals/controls,
        │  1c entry surfaces/sinks, 1d local execution/deployment)
        │  → architecture.md (~1,000 words cap), coverage-ledger.json
        ▼
 Phase 2  Coverage-led hunting waves
        │  hunters take "planned" ledger units → one structured JSON each
        │  coverage critic after every wave → missing_units, reassign_ids
        │  (repeat until a clean critic pass, or record an early stop)
        ▼
 Phase 3  Candidate validation
        │  a fresh verifier per candidate: "try to refute it"
        │  → confirmed | needs_validation | rejected
        ▼
 Phase 4  Structured output
        │  findings.json  → validate-findings.cjs
        │  coverage-ledger.json → validate-coverage-ledger.cjs
        ▼
 Phase 5  Independent record verification
        │  a fresh research verifier per final record → verified | replace
        ▼
 Phase 6  Target-neutral report
           REPORT.md, FINDINGS-DETAIL.md, NEEDS-VALIDATION.md
```

단계마다 눈여겨볼 설계가 있습니다.

**1단계: 정찰.** 정찰 에이전트는 대상 소스와 로컬에 있는 빌드·설정만 읽고, 배포된 엔드포인트나 레지스트리, 클라우드 API에는 접속하지 않습니다. 부모는 결과를 약 1,000단어 이내의 `architecture.md`로 합치고, 커버리지 원장을 만듭니다. 원장의 각 단위에는 사람이 읽는 이름과 별도로 소스에서 유도한 안정적 참조(`canonical_refs`)가 있고, `coverage_id`는 이 참조들을 퍼센트 인코딩해 `::`로 이어 붙여 만듭니다. `RECONNAISSANCE.md`의 단위 예시 일부입니다.

```json
{
  "coverage_id": "...",
  "canonical_refs": {
    "surface": "src/router.ts#POST /users/:id",
    "boundary": "src/authz.ts#requireOwner",
    "subsystem": "packages/api",
    "attack_class": "ATTACK-CLASSES.md#Access control"
  },
  "starting_paths": ["repo/relative/path"],
  "wave": 1,
  "status": "planned",
  "agent_id": null,
  "reviewed_paths": [],
  "local_checks": [],
  "result_fingerprints": [],
  "unresolved": []
}
```

문서는 "원장이 곧 커버리지 주장"이라고 적습니다. 아키텍처 요약이나 에이전트 수, "인증을 검토했다"는 문장은 커버리지의 증거가 아니고, 헌터가 구조화된 결과로 돌려준 경로와 확인 내역만 단위를 닫을 수 있습니다.

**2단계: 탐색.** 헌터 프롬프트에는 `architecture.md` 전문, 배정된 단위, 선택된 공격 유형 블록의 원문, 탐색 방법, 후보 통과 기준이 정해진 순서로 들어갑니다. 헌터는 산문이 아니라 JSON 객체 하나만 돌려줘야 하고, 배정된 단위마다 `covered`, `candidate`, `blocked` 중 하나를 답합니다. 예상 밖의 다른 경계를 발견하면 직접 파고들지 않고 `uncovered`로 돌려보내 부모가 새 단위를 만들게 합니다. 웨이브가 끝나면 커버리지 비평가가 매핑되지 않은 진입점, 확인 없이 닫힌 단위, 근거 없는 제외를 찾습니다.

**3단계: 반증.** 검증자 프롬프트의 첫 문장은 "이 후보는 당신이 쓴 것이 아니다. 저장소 소스와 제한된 로컬 증거로 반증을 시도하라"입니다. 검증자는 다른 검증자의 결론을 받지 않고, 인용된 소스 위치를 모두 다시 읽습니다.

**4단계: 구조화 출력.** 부모가 판정이 끝난 기록을 지문 순으로 정렬해 `findings.json`에 쓰고 두 검증 스크립트를 돌립니다. 문서는 한계를 분명히 적어 둡니다. "검증기 통과는 형식과 원장 일관성만 증명한다"는 것입니다.

**5단계: 재검증.** 최종 `confirmed`와 `needs_validation` 기록마다 새 에이전트가 구조화된 기록 자체를 다시 확인합니다. 판정을 더 강하게 올리거나 근본 원인, 추적, 심각도를 실질적으로 바꾸는 교체안은 그대로 적용하지 않고 또 다른 독립 검증자에게 넘깁니다. `quick` 프로필에서만 3단계와 5단계가 합쳐집니다.

**6단계: 보고서.** 산문 보고서는 최종 기록과 원장에서 "파생"될 뿐, 판정이나 심각도를 바꾸지 못합니다. 확정 발견이 0건이면 그렇다고 적고, LOW 발견을 지어내지 말라고 문서는 명시합니다.

### 블로그의 초기 스킬과 지금 저장소의 차이

공식 블로그(2026-06-18 게시)는 초기 스킬을 "약 450줄, 한 세션에서 도는 7단계 감사, 정찰 에이전트 3개"로 설명합니다. 저장소 이력을 보면 차이가 있습니다.

- 공개 첫 커밋(2026-06-18)은 파일 9개, 982줄이고 지침 Markdown 5개가 합쳐 469줄입니다. README는 처음부터 6단계로 적혀 있습니다. 블로그의 일곱 번째 단계는 "재검증된 발견을 수집 API에 제출"하는 사내용 단계입니다.
- 2026-09-10에 병합된 PR #12("Rework the audit workflow, findings contract, and validators end to end")가 저장소를 사실상 새로 썼습니다. 판정 3종, 결정적 커버리지 원장, 비평가 웨이브, 예산 예약, 샌드박스 요구, 두 번째 검증 스크립트, 도메인 동반 파일 10개 체계가 이때 들어왔습니다.
- 지금 저장소(2026-11-20 기준)는 파일 22개이고, 정찰의 기본 에이전트는 4개입니다.

즉 블로그는 배경과 설계 의도를 이해하는 자료로 읽고, 실제 동작은 저장소의 현재 문서를 기준으로 봐야 합니다.

## 주요 기능

### 지침 모드와 전체 감사 모드

`SKILL.md`는 "이 스킬은 기본이 지침(guidance) 모드"라고 밝힙니다. 보안 질문, 특정 부분 리뷰, 발견 분석에는 스킬의 관련 부분만 쓰고, 6단계를 자동으로 돌리거나 출력 디렉터리를 만들지 않습니다. 전체 감사(full audit) 모드는 사용자가 코드베이스 감사나 침투 테스트, 포괄적 리뷰, 보고서 산출물을 명시적으로 요청했을 때만 씁니다. 어느 쪽인지 애매하면 파일을 만들기 전에 질문 하나를 하라고 되어 있습니다.

### 실행 프로필, 범위, 예산

- `quick`: 작은 대상이나 재실행용. 헌터 웨이브 1회와 최종 비평가 1회만 돌리고, 후보마다 검증자 1명이 검증과 최종 확인을 겸합니다.
- `standard`: 문서에 적힌 그대로의 기본 흐름입니다.
- `deep`: 중요도가 높거나 큰 대상용. 단위를 하위 시스템과 수명주기 모드별로 쪼개고, 비평가가 더 지적할 것이 없을 때까지 웨이브를 돌립니다.

범위 지정 실행(scoped run)은 지정한 경로, 하위 시스템 하나, 동반 도메인 하나, 또는 두 소스 ref 사이의 diff만 감사합니다. 범위 밖은 `covered`가 아니라 `out_of_scope`로 기록하고, `quick`이나 범위 지정 실행은 보고서에서 스스로를 "부분 커버리지"라고 밝혀야 합니다. 예산은 전 단계에 걸친 **에이전트 호출 횟수의 상한**으로 지정합니다. 헌터를 배정하기 전에 비평가와 검증 몫을 먼저 떼어 놓고(검증 몫을 가늠하기 어려우면 비평가 몫을 뺀 잔액의 30%), 예산이 부족해 검증하지 못한 후보는 `findings.json`에 넣지 않은 채 실행 상태를 `incomplete`로 기록합니다.

### 공격 유형 문서

`ATTACK-CLASSES.md`에는 일반 공격 유형 9개가 있습니다. 주입, 접근 제어, 자원과 파일 처리, 암호와 비밀 값, 비즈니스 로직, 기능 오용과 데이터 유출, 연쇄 취약점과 신뢰 경계, 그리고 범주 없이 이상한 코드를 뒤지는 와일드카드, 하드코딩된 비밀 값이나 열린 디버그 엔드포인트 같은 기본을 글자 그대로 확인하는 "obvious things"입니다. 도메인 동반 파일은 메모리 안전성과 바이너리, AI와 LLM, 웹 프로토콜과 인증, 클라이언트 측, 공급망과 릴리스, 클라우드와 배포, 프로토콜·RPC·메시징, 자원 고갈과 가용성, 데이터 격리와 수명주기, 데스크톱·모바일·로컬 IPC의 10개입니다. 동반 파일은 언어나 의존성 이름이 보인다고 고르는 것이 아니라, 정찰에서 그 파일이 설명하는 신뢰 경계를 실제로 찾았을 때만 고르도록 되어 있습니다.

AI 동반 파일의 첫 규칙은 이 스킬의 태도를 잘 보여 줍니다. "프롬프트 주입만으로는 발견이 아니다. 코드 수준의 경계 실패가 있어야 한다"는 것이고, "가드레일 프롬프트는 보안 경계가 아니다"라고도 적습니다.

### 심각도 규칙

심각도는 `confirmed` 기록에만 붙고, 가능성(likelihood)과 영향(impact)을 따로 적은 뒤 전체 심각도를 정합니다. 전체 심각도는 입증된 영향을 넘을 수 없으며, 이 규칙은 `validate-findings.cjs`가 코드로 검사합니다(넘으면 `cannot exceed demonstrated impact` 오류). `SKILL.md`의 기준점은 다음과 같습니다.

| 등급 | 기준 |
|---|---|
| critical | 인증 없는 행위자가 코드 실행, 데이터 저장소 전체 접근, 임의 계정 탈취를 얻음 |
| high | 명시적 보안 통제를 완전히 무력화하고 실제 결과가 있음(인증 우회, 테넌트 간 읽기·쓰기 등) |
| medium | 실제 경계 위반이지만 영향 범위가 제한적이거나 전제 조건이 드묾 |
| low | 비밀이 아닌 내부 정보 노출, 또는 큰 노력에 비해 얻는 것이 작은 영향 |
| informational | 확정됐지만 영향이 미미한 관찰 |

### 의존성 없는 검증 스크립트 2개

`validate-findings.cjs`는 `report-schema.json`을 직접 해석해 `findings.json`을 검사하고, `validate-coverage-ledger.cjs`는 원장의 ID 규칙과 상태별 필드 조건을 검사합니다. 둘 다 Node.js 내장 모듈(`fs`, `path`, `util`)만 씁니다. 감사 대상에서 유래한 문자열이 들어오는 파일을 읽는 도구답게 입력 방어가 들어 있습니다. 문서 기준으로 발견 검증기는 5MiB, 최상위 발견 1,000개, 중첩 64단계를 넘는 입력을 거부하고, 원장 검증기는 5MiB, 단위 10,000개, 중첩 64단계, 순회 값 500,000개를 넘는 입력을 거부하며, 둘 다 오류 출력을 100개로 자릅니다. 저장소에는 두 검증기의 테스트 파일도 함께 있습니다(PR #12 설명 기준 65개 테스트).

### 실행 안전 규칙과 쓰기 격리

소스 검토는 읽기 전용이고, 감사는 수정안을 "설명"할 뿐 대상 소스를 고치지 않습니다. 기본 출력 위치는 대상 저장소 밖(`~/security-audit-skill/<repo-name>/run-<N>`)이며, 대상 저장소 안에 쓰는 것은 사용자가 명시적으로 고르고 버전 관리가 그 디렉터리 전체를 무시할 때만 허용됩니다. 각 헌터와 검증자는 `<output-dir>/agents/<agent-id>/` 아래에 `scratch/`와 `artifacts/`를 받는데, 에이전트와 대상 프로세스는 `scratch/`에만 쓰고, 증거로 남길 파일은 부모 쪽의 신뢰된 코드가 11단계 "승격(promotion)" 절차(심볼릭 링크를 따라가지 않는 열기, 일반 파일 여부와 크기 확인, 배타적 생성 등)로 `artifacts/`에 옮기도록 되어 있습니다. 배포된 엔드포인트, 실제 계정, 운영 데이터, 유료 API 호출은 모두 금지입니다.

## 설치와 시작

README에 있는 방법만 옮깁니다. **필자는 아래 명령을 실행하지 않았습니다.**

요구 사항은 세 가지입니다.

- 도구 사용과 병렬 서브에이전트를 지원하는 모델을 쓰는 코딩 에이전트
- Node.js (의존성 없는 두 검증 스크립트 실행용)
- 대상이 통제하는 빌드, 테스트, 프로세스, 브라우저, 에뮬레이터, 퍼저를 실행할 OS 강제 샌드박스

설치는 [Skills CLI](https://skills.sh)로 합니다.

```bash
npx skills add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit
```

사용자 수준으로 설치하려면 `--global`을 붙입니다.

```bash
npx skills add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit \
  --global
```

에이전트 선택이나 비대화형 옵션은 `npx skills --help`를 보라고 README는 안내합니다. 설치 후에는 감사할 코드베이스에서 코딩 에이전트를 시작하고 자연어로 요청합니다. README의 예시입니다.

```text
security audit this codebase
```

```text
find security vulnerabilities in ./src
```

```text
do a security review, output to ~/audits/my-project
```

README에 따르면 요청이 트리거(보안 감사, 취약점 찾기, 코드 침투 테스트 등)와 맞으면 스킬이 자동으로 활성화됩니다. 코드베이스 감사나 침투 테스트를 직접 요청하면 전체 감사 모드, 보안 질문이나 좁은 범위의 작업은 보고서 산출물을 요청하지 않는 한 지침 모드입니다.

## 실전 예제

> 아래 예제는 저장소 문서와 테스트 파일의 내용을 바탕으로 했습니다. **필자는 스킬을 설치하거나 감사를 실행하지 않았고, 검증 스크립트도 돌려 보지 않았습니다.** 파일 이름, 필드, 출력 문구는 2026-11-20 기준 `main` 브랜치(커밋 `c1c8a8c`)의 문서와 소스에서 확인했습니다.

### 예제 1. 저장소 전체 감사를 맡기고 산출물 확인하기

코드베이스 디렉터리에서 에이전트를 띄우고 README의 문장으로 요청합니다.

```text
security audit this codebase
```

출력 디렉터리를 지정하지 않으면 `~/security-audit-skill/<repo-name>/run-<N>`에 결과가 쌓입니다. `SKILL.md`가 정의한 공유 파일은 다음과 같습니다.

```text
run-metadata.json      # 프로필, 범위, 예산, 소스 ref, 실행 상태
architecture.md        # 정찰 요약 (약 1,000단어 이내)
coverage-ledger.json   # 커버리지 단위와 확인 내역
findings.json          # confirmed / needs_validation / rejected 기록
REPORT.md              # 요약, 확정 발견 표, 검증 필요 표, 커버리지 요약
FINDINGS-DETAIL.md     # medium 이상 확정 발견의 전체 추적과 재현 절차
NEEDS-VALIDATION.md    # 풀리지 않은 단서와 확인 계획
agents/<agent-id>/     # 에이전트별 scratch/ 와 artifacts/
```

`REPORT.md` 첫 부분에는 프로필, 범위, 예산 대비 실제 사용한 에이전트 수, 소스 ref, 연기되거나 범위 밖인 커버리지가 들어가야 합니다. 보고서를 받으면 발견 표보다 이 부분을 먼저 읽는 것이 좋습니다. 무엇을 보지 않았는지가 거기에 있기 때문입니다.

### 예제 2. 범위와 프로필을 좁혀 먼저 돌려 보기

`SKILL.md`는 프로필을 "사용자의 요청에서 고르거나 대상의 크기와 중요도를 보고 제안"한다고 설명합니다. README에 프로필을 지정하는 예시 문장은 없으므로, 아래 문장은 필자가 문서의 용어로 구성한 것입니다.

```text
Run a quick-profile security audit scoped to ./src/api,
with a budget of 20 agent invocations. Output to ~/audits/my-project.
```

이때 알아 둘 규칙이 있습니다. 예산이 정찰 4회, 비평가, 검증자 최소 1회를 감당하지 못하면 에이전트를 하나도 띄우지 않고 더 큰 예산이나 더 좁은 범위를 요청하게 되어 있습니다. 또 `quick`은 비평가가 빠진 영역을 찾아도 두 번째 웨이브를 돌리지 않고 `deferred`(연기)로만 기록합니다. 그래서 `quick` 결과는 "깨끗하다"가 아니라 "여기까지 봤다"로 읽어야 합니다.

### 예제 3. findings.json의 세 판정 읽기

저장소의 테스트 파일(`validate-findings.test.cjs`)에 있는 세 판정의 픽스처를 JSON으로 옮기면 기록의 모양을 볼 수 있습니다. `needs_validation` 기록입니다(테스트의 "생산자 형태" 픽스처처럼 `validation_plan`에 `local`만 둔 모양).

```json
{
  "verdict": "needs_validation",
  "fingerprint": "src-parser-size-hypothesis",
  "title": "Unchecked parsed size",
  "description": "A parsed size may reach an allocation without a limit.",
  "claimed_root_cause": "parse_size may pass an unbounded value to allocate.",
  "trace": [
    { "kind": "entrypoint", "file": "src/handler.c", "line": 10,
      "scope": "handle", "description": "Attacker data reaches the operation." }
  ],
  "evidence": [
    { "file": "src/handler.c", "line": 10,
      "description": "The source performs the operation without the required check." }
  ],
  "blockers": ["The generated parser source is absent from this checkout."],
  "validation_plan": {
    "local": "Generate the parser and submit the smallest input that exceeds the documented limit."
  }
}
```

`rejected` 기록은 `blockers`와 `validation_plan` 대신 `reason` 하나를 가집니다.

```json
{
  "verdict": "rejected",
  "fingerprint": "src-router-auth-bypass",
  "title": "Authorization bypass in router",
  "description": "The candidate claimed a route bypassed authorization.",
  "claimed_root_cause": "dispatch was claimed to skip the authorization wrapper.",
  "trace": [
    { "kind": "sink", "file": "src/handler.c", "line": 10,
      "scope": "handle", "description": "Attacker data reaches the operation." }
  ],
  "evidence": [
    { "file": "src/handler.c", "line": 10,
      "description": "The source performs the operation without the required check." }
  ],
  "reason": "All routes pass through the authorization wrapper before dispatch."
}
```

`confirmed` 기록은 필드가 가장 많습니다. `report-schema.json`의 필수 필드는 `root_cause`, `intended_behavior`, `trace`, `evidence`, `conditions`, `execution`, `remediation`, `severity`, `confidence`이고, `execution` 안에는 공격자 관점, 최소 입력(`payloads`), 절차, **실제로 관찰한 결과(`observed_result`)** 가 모두 있어야 합니다. 스키마가 `additionalProperties: false`라서 판정마다 쓸 수 있는 필드가 엄격히 갈립니다. 예를 들어 `needs_validation`에 `severity`를 넣으면 검증에 실패합니다. 추적이 여러 단계면 `entrypoint`로 시작해 `sink`로 끝나고 중간은 `propagation`이어야 합니다.

### 예제 4. 검증 스크립트를 직접 돌리기

부모 에이전트가 돌리는 명령은 사람이 직접 실행할 수도 있습니다. `VALIDATION-AND-REPORTING.md`의 명령입니다.

```sh
node <skill-dir>/validate-findings.cjs <output-dir>/findings.json
node <skill-dir>/validate-coverage-ledger.cjs <output-dir>/coverage-ledger.json
```

스크립트 소스를 보면 성공 시 `PASS: 3 findings valid`, `PASS: 12 coverage units valid`처럼 개수와 함께 한 줄을 찍고 종료 코드 0으로 끝납니다(숫자는 설명을 위한 예입니다). 실패하면 오류마다 `ERROR:` 줄을 찍고 `FAIL: ... validation error(s)`와 함께 종료 코드 1로 끝납니다. 다른 도구가 `findings.json`을 받아 이슈 트래커에 넣는 파이프라인을 만든다면, 이 검증을 수집 직전에 한 번 더 두는 구성이 자연스럽습니다. 다만 앞서 인용했듯 통과는 형식의 증명일 뿐 내용의 증명은 아닙니다.

### 예제 5. 같은 저장소를 다시 감사해 커버리지 넓히기

README는 같은 저장소에 대한 여러 번의 실행이 "가산적(additive)"이라고 설명합니다. 같은 요청을 다시 하면 새 `run-<N>` 디렉터리가 생기고, 스킬은 이전 원장과 발견을 읽어 계획을 세웁니다. `SKILL.md`의 이월 규칙을 요약하면 다음과 같습니다.

- 관련 소스가 그대로인 이전 `confirmed`는 같은 지문으로 이월하되, 이번 실행의 검증 경로를 다시 통과해야 합니다. 헌터는 그 근본 원인만 탐색에서 제외합니다.
- 관련 소스가 바뀐 이전 `confirmed`는 재검증 단위가 되고, 탐색 제외 목록에 넣지 않습니다.
- 이전의 `needs_validation`, `deferred`, `blocked`, `out_of_scope` 단위는 모두 이번 실행의 작업이 됩니다. 이런 상태가 현재 단위를 숨기는 데 쓰이면 안 됩니다.
- 이전 `rejected`는 바뀌지 않은 그 주장만 막을 뿐, 해당 단위의 검토 자체를 막지 않습니다.
- 이전 실행이 `quick`이나 범위 지정이었다면 기록된 증거와 공백만 인정하고, "나머지는 괜찮다"는 암시는 인정하지 않습니다.

"1회 실행은 약 절반"이라는 README의 언급과 합쳐 보면, 이 스킬은 한 번 돌리고 끝내는 도구가 아니라 여러 번 돌려 원장을 채워 가는 도구로 설계되어 있습니다.

## 실무 팁 & 자주 겪는 문제

공식 문서와 이슈 트래커(2026-11-20 기준)를 바탕으로 정리했습니다. 이슈 트래커의 내용은 **사용자 보고이며 관리자의 확인이나 답변이 달리지 않은 상태**라는 점을 감안해 읽어야 합니다.

- **샌드박스가 없으면 `confirmed`를 얻기 어렵습니다.** 확정 기록에는 로컬에서 관찰한 결과가 필요한데, 샌드박스 통제를 하나라도 갖추지 못하면 대상 코드를 실행하지 않는 것이 규칙입니다. 그래서 소스만으로 명백해 보이는 버그도 `needs_validation`으로 남을 수 있습니다. 이 점을 지적하고 "소스만으로 확정" 판정을 제안하는 이슈([#160](https://github.com/cloudflare/security-audit-skill/issues/160))가 열려 있습니다.
- **Windows에서는 검증 스크립트가 입력을 읽지 못합니다.** 두 스크립트는 `O_NOFOLLOW`와 `O_NONBLOCK` 플래그가 없는 플랫폼에서 모든 입력을 거부하도록 작성되어 있습니다(소스 주석: 경쟁 조건에 안전한 대안이 없으므로 모두 거부). Windows의 Node.js에는 이 플래그가 없어 4단계 검증을 통과할 수 없다는 이슈([#117](https://github.com/cloudflare/security-audit-skill/issues/117))와 여러 수정 PR이 열려 있지만 병합된 것은 없습니다.
- **신뢰할 수 없는 저장소를 감사할 때는 에이전트를 어디서 시작하는지가 문제가 됩니다.** README는 감사할 코드베이스 "안에서" 에이전트를 시작하라고 안내하는데, 코딩 에이전트는 작업 디렉터리의 `AGENTS.md`, `CLAUDE.md` 같은 지침과 프로젝트 설정을 스킬보다 먼저 읽습니다. 감사 대상이 감사자의 지침 출처가 될 수 있다는 지적([#148](https://github.com/cloudflare/security-audit-skill/issues/148))이 있습니다. 스킬의 안전 규칙은 대상이 통제하는 "프로세스"를 다루고 있어, 대상이 통제하는 "에이전트 설정"은 사용자가 따로 챙겨야 합니다.
- **스킬이 자동으로 선택되지 않을 수 있습니다.** 다른 보안 스킬이 함께 설치된 환경에서 README의 예시 문장을 써도 이 스킬 대신 다른 스킬이 선택된다는 보고([#5](https://github.com/cloudflare/security-audit-skill/issues/5))가 있습니다. 전용 슬래시 명령은 없습니다.
- **ZIP 업로드 방식 설치는 실패한다는 보고가 있습니다.** `SKILL.md`가 저장소 최상위가 아니라 `skills/security-audit/` 아래에 있어, 저장소 ZIP을 Claude 앱의 스킬 업로드에 그대로 올리면 거부된다는 내용입니다([#64](https://github.com/cloudflare/security-audit-skill/issues/64)). README가 안내하는 설치 방법은 `npx skills add`뿐입니다.
- **병렬 서브에이전트가 불안정한 플랫폼에서는 흐름이 끊깁니다.** 특정 에이전트 플랫폼에서 병렬 서브에이전트가 중단된다는 보고([#11](https://github.com/cloudflare/security-audit-skill/issues/11))가 있습니다. 요구 사항의 "병렬 서브에이전트 지원"은 선택이 아니라 전제입니다.
- **의존성의 알려진 취약점(CVE)은 별도 도구로 보완하는 것이 좋습니다.** 스킬은 네트워크 접속과 의존성 설치를 금지하므로 최신 취약점 권고 데이터베이스를 조회하지 않습니다. 제3자 비교 실험 보고([#20](https://github.com/cloudflare/security-audit-skill/issues/20))도 고정된 의존성의 공개 취약점을 세 번 모두 찾지 못했고, 이것은 버그가 아니라 설계상 경계라고 적었습니다. 필자의 판단으로는 의존성 검사 도구(SCA)를 함께 쓰는 구성이 맞습니다.
- **PR을 직접 골라 적용할 때는 충돌을 확인해야 합니다.** 열린 PR 다수가 같은 두 검증 스크립트를 고치고 있어 서로 충돌한다는 정리([#114](https://github.com/cloudflare/security-audit-skill/issues/114))가 있습니다. 포크해서 쓸 팀은 필요한 수정만 골라 직접 검토하는 편이 안전합니다.

## 비슷한 도구와 비교

| 항목 | security-audit-skill | Claude Code Security Reviewer | Trail of Bits Skills | 전통적 SAST |
|---|---|---|---|---|
| 형태 | Agent Skill 1개(지침 문서 + Node.js 검증기) | GitHub Action, Claude Code 내장 `/security-review` 명령 | 여러 플러그인을 모은 스킬 마켓플레이스 | 규칙 기반 정적 분석기 |
| 주 대상 | 저장소 전체(범위 지정 가능) | PR의 변경분, 로컬의 대기 중인 변경 | 플러그인마다 다름(스마트 컨트랙트, C/C++ 리뷰, 차분 리뷰 등) | 규칙이 아는 코드 패턴 |
| 오탐 대응 | 찾은 에이전트와 다른 에이전트의 반증, 최종 기록 재검증 | 자동 오탐 필터링(DoS, 속도 제한, 오픈 리다이렉트 등 제외) | `fp-check` 같은 별도 플러그인 | 규칙 조정과 억제 설정 |
| 산출물 | 스키마 검증된 `findings.json`, 커버리지 원장, 보고서 3종 | PR 리뷰 댓글, 결과 JSON 파일 | 플러그인마다 다름 | 도구별 보고서 |
| 실행 조건 | 병렬 서브에이전트, Node.js, 대상 실행 시 OS 샌드박스 | GitHub Actions와 Claude API 키 | Claude Code, Codex 등의 플러그인 기능 | 모델 없이 CI에서 실행 |
| 라이선스 | MIT | MIT | CC BY-SA 4.0 | 도구마다 다름 |
| 마지막 push | 2026-09-14 | 2026-02-11 | 2026-11-18 | 해당 없음 |

Claude Code Security Reviewer와 Trail of Bits Skills 열은 각 저장소의 README와 `gh api` 메타데이터(2026-11-20 기준)에서 확인한 내용이고, 플러그인별 세부 동작은 확인하지 않았습니다. 전통적 SAST 열은 일반적으로 알려진 특징 기준입니다. Claude Code Security Reviewer의 README는 이 액션이 "프롬프트 주입 공격에 대해 강화되어 있지 않으므로 신뢰할 수 있는 PR 검토에만 써야 한다"고 스스로 밝힙니다.

세 도구는 경쟁 관계라기보다 쓰는 시점이 다릅니다. PR마다 변경분을 빠르게 보는 일은 diff 기반 리뷰어가, 저장소 전체를 주기적으로 훑는 일은 이 스킬 같은 다단계 감사가 맡는 식입니다. Cloudflare 블로그도 자사 하네스의 대규모 스캔은 "PR별 검사가 아니라 주기적인 백로그 정리"이고, PR 검사에는 더 싸고 작은 하네스가 맞는 도구라고 적었습니다. 흥미로운 대목도 하나 있습니다. Cloudflare는 하네스에 Semgrep을 끝까지 연결해 두었지만 헌터 에이전트가 한 달 동안 한 번도 호출하지 않았다고 합니다(자체 발표, 사내 하네스 기준). 그렇다고 SAST가 불필요하다는 뜻은 아닙니다. 에이전트가 스스로 고르지 않았다는 관찰일 뿐이고, 결정적으로 같은 결과를 내는 검사는 여전히 CI의 몫입니다.

## 장점과 한계

### 장점

- **발견과 검증의 분리가 절차로 고정되어 있습니다.** 후보마다 새 검증자가 반증을 시도하고, 최종 기록은 또 다른 새 에이전트가 확인합니다. README의 설계 원칙 그대로 "발견을 확인하는 에이전트는 그것을 찾은 에이전트가 아닙니다".
- **모르는 것을 모른다고 적는 판정이 있습니다.** `needs_validation`은 심각도 없이 "정확히 어떤 사실이 빠졌는지"와 확인 계획을 남깁니다. 배포 환경을 추측해 위험도를 부풀리는 흔한 오류를 구조적으로 막습니다.
- **보지 않은 곳이 기록에 남습니다.** 원장의 `deferred`, `out_of_scope`, `blocked` 상태와 부분 커버리지 표기 덕분에, 보고서가 조용히 "다 봤다"고 말하기 어렵습니다.
- **산출물을 기계가 검사할 수 있습니다.** 스키마와 의존성 없는 검증기가 있어 결과를 다른 시스템에 넣기 전에 형식을 확인할 수 있습니다.
- **에이전트 중립적이고 MIT입니다.** 문서는 특정 제품의 도구 이름 대신 부모, 위임 도구, `research`·`general` 에이전트 같은 역할 용어를 씁니다. 지침이 평문 Markdown이라 자기 조직의 공격 유형을 추가하기 쉽습니다.
- **방어적으로 설계되어 있습니다.** 운영 환경 접촉 금지, 최소 효과에서 중단, 대상 소스 비수정 같은 규칙이 모든 단계에 반복됩니다.

### 한계

- **유지보수가 멈춘 상태입니다.** 글 앞부분에 적은 대로 2026-09-14 이후 변경이 없고, 그 사이 올라온 버그 보고와 수정 PR이 처리되지 않았습니다(2026-11-20 기준).
- **절차는 코드가 아니라 프롬프트로 강제됩니다.** 검증자의 독립성, 샌드박스 통제, 예산 예약은 모두 부모 에이전트가 문서를 따른다는 전제입니다. 두 검증 스크립트는 산출물의 형식만 보며, 11단계 승격 절차는 문서로만 있고 저장소에 구현 스크립트가 없습니다(파일 목록 기준, 이 점을 지적한 이슈 [#158](https://github.com/cloudflare/security-audit-skill/issues/158)도 열려 있습니다).
- **샌드박스 요구 수준이 높습니다.** 네트워크 차단, 빈 환경, 읽기 전용 대상, 자원 제한을 모두 갖춘 OS 강제 샌드박스를 개인 개발 환경에서 준비하기는 쉽지 않고, 준비하지 못하면 결과의 상당수가 `needs_validation`에 머뭅니다.
- **비용과 시간이 큽니다.** 정찰 4회, 단위마다 헌터, 웨이브마다 비평가, 후보마다 검증자 1~2회가 필요합니다. README에는 비용 수치가 없습니다. 제3자 비교 실험 보고(#20)는 `quick` 프로필 1회의 중앙값을 29.95달러, 단일 에이전트 리뷰를 2.06달러로 적었지만, 대상 1개에 방식별 3회 실행이고 보고자가 자기 도구를 비교 대상에 넣은 실험이라 참고로만 봐야 합니다.
- **한 번의 실행으로는 부족합니다.** "약 절반"이라는 수치는 자체 발표이고 조건이 공개되지 않았지만, 방향 자체는 반복 실행을 전제로 예산을 잡아야 한다는 뜻입니다. 블로그는 단일 실행이 찾은 버그가 "더 단순하고 덜 미묘한 쪽으로 치우쳤다"고도 적었습니다.
- **단일 저장소, 단일 세션이 범위입니다.** 블로그가 스킬의 벽으로 꼽은 세 가지(컨텍스트 고갈, 중단 시 처음부터 다시, 저장소 간 추론 불가)는 스킬로는 풀리지 않아 하네스를 만든 이유였습니다. 원장과 이전 실행 이월 규칙이 일부를 보완하지만, 데이터베이스 기반 재개나 저장소 간 추적은 없습니다.

## 인사이트

**왜 지금 중요한가: 병목이 "찾기"에서 "믿을 수 있게 거르기"로 옮겨 갔습니다.** Cloudflare 블로그의 수치(자체 발표, 게시 시점의 누적)를 보면 사내 하네스가 낸 원시 후보 20,799건 중 검증을 통과한 것은 약 12,057건이고, 중복 제거와 판단을 거쳐 엔지니어링 팀에 넘어간 것은 7,245건입니다. 블로그의 표현대로 원시 후보는 이제 싸고, 일은 그것을 검증 가능한 수정으로 바꾸는 데 있습니다. 이 스킬의 문서 분량 대부분이 "어떻게 찾나"가 아니라 "무엇을 발견으로 인정하나", "누가 검증하나", "무엇을 안 봤다고 적나"에 쓰여 있는 이유입니다. 필자의 판단으로는 이 저장소에서 가장 재사용할 만한 것은 공격 유형 목록보다 세 판정의 계약과 커버리지 원장이라는 두 가지 자료 구조입니다. 다른 도메인의 에이전트 리뷰(성능, 접근성, 규정 준수)에도 "확정, 검증 필요, 기각"과 "본 것과 안 본 것의 장부"는 그대로 옮길 수 있습니다.

**기존 글과의 연결: 에이전트가 쓴 코드의 보안은 누가 보나.** [LSCBench 소개 글](/papers/2026/10/24/last-secure-code-benchmark.html)은 코딩 에이전트가 기능 명세만 받으면 "돌아가는" 코드는 잘 쓰지만 "돌아가면서 안전한" 코드는 최고 25.1%에 그친다는 결과를 다뤘습니다. 그 글이 문제의 크기를 보여 줬다면, 이 스킬은 같은 에이전트를 점검하는 쪽에 세우는 시도입니다. 다만 두 글을 합쳐 읽으면 낙관하기 어려운 점도 보입니다. 코드를 쓴 모델과 감사하는 모델이 같으면 같은 맹점을 공유할 수 있습니다. Cloudflare가 사내에서 탐색과 검증에 서로 다른 모델을 쓴다고 밝힌 것도 이 때문인데, 공개된 스킬 문서에는 검증에 다른 모델을 쓰라는 지시가 없어, 따로 구성하지 않으면 찾는 쪽과 검증하는 쪽이 같은 모델일 가능성이 큽니다. 형식 면에서는 [Agent Skills 표준 글](/tech/2026/10/24/agent-skills-aaif.html)에서 다룬 `SKILL.md` 폴더 구조와 점진적 공개의 실제 사례입니다. `SKILL.md`가 개요와 규칙을 담고, 단계별 문서와 동반 파일은 필요할 때만 읽히도록 나뉘어 있습니다. 그 글에서 짚은 스킬 공급망 문제도 여기서 구체적으로 보입니다. 이 스킬은 에이전트에게 많은 권한을 전제로 하는 15개 문서와 스크립트 묶음인데, 릴리스 태그가 없고 README의 설치 명령도 버전이나 커밋을 지정하지 않습니다. 도입한다면 검토한 커밋을 기록하고 포크로 고정해 두는 것이 최소한의 관리로 보입니다.

**한계와 반론: 블로그의 성과는 하네스의 것이지 이 스킬의 것이 아닙니다.** 스타 7.6만 개와 "Cloudflare가 실제로 쓴다"는 인상은 블로그의 수치에서 옵니다. 하지만 그 수치를 만든 것은 SQLite에 상태를 남기는 오케스트레이터, 서로 다른 모델의 교차 검증, 전용 중복 제거 에이전트, 저장소 간 추적, 원본 코드에서 통과해야 하는 PoC 테스트 같은 장치들이고, 이들은 공개되지 않았습니다. 블로그는 "하네스 자체도 곧 따라 나오기를 바란다"고 적었지만, 필자가 GitHub 검색으로 확인한 범위에서는 2026-11-20 기준 cloudflare 조직에 해당 저장소가 보이지 않습니다. 공개된 스킬이 얼마나 잘 찾는지에 대한 수치는 README의 "약 절반" 한 줄뿐입니다. 또 하나의 반론은 절차의 강제력입니다. 블로그의 하네스에서는 평범한 코드가 인용된 파일과 경로의 존재를 기계적으로 확인하고, 검증자는 스스로 발견을 등록할 수 없습니다. 스킬에서는 같은 규칙이 문장으로 적혀 있을 뿐이어서, 부모 에이전트가 긴 세션 끝에 단계를 건너뛰어도 형식이 맞으면 검증기는 통과합니다. 스킬 문서가 정교해질수록(지침만 1,778줄) 에이전트가 그것을 끝까지 정확히 따를 가능성은 오히려 따로 검증해야 할 문제가 됩니다. 사용자 프로필 삭제 보고(#128)가 사실이라면 바로 이 간극에서 생긴 사고입니다.

**실무에 주는 의미: 그대로 도입하기보다 읽고 가져다 쓰는 자료로 보는 편이 맞습니다.** 필자의 판단으로는 지금 상태에서 이 스킬의 가치는 세 층으로 나뉩니다. 첫째, 보안 리뷰 프롬프트를 직접 쓰는 팀에게는 후보 통과 기준, 심각도 기준점, 안티패턴 목록이 바로 가져다 쓸 수 있는 문장입니다. 둘째, 자체 파이프라인을 설계하는 팀에게는 블로그의 조언이 실용적입니다. 최소한의 하네스는 정찰, 탐색, 검증 단계를 데이터베이스에 두고 스스로 발견을 등록할 수 없는 검증기를 따로 두는 것이며, 다음 단계는 그것이 없어서 느려질 때만 만들라는 것입니다. 셋째, 스킬을 실제로 돌려 보려는 팀은 격리된 컨테이너나 VM에서, 신뢰하는 저장소를 대상으로, `quick`과 좁은 범위부터 시작하고, 결과의 `needs_validation` 비율과 사용한 에이전트 호출 수를 먼저 재 보는 순서가 안전해 보입니다.

**앞으로 지켜볼 점.** 첫째, 관리자의 활동 재개 여부입니다. 열린 PR 84개 중 Windows 지원, 산출물 존재 확인, 환경 격리 확인처럼 실사용에 직결되는 것들이 병합되는지를 보면 이 저장소가 "공개 후 방치"인지 "큰 개편 사이의 공백"인지 판단할 수 있습니다. 2026-09-10의 전면 개편이 두 달의 공백 뒤에 한 번에 들어왔다는 이력은 후자의 가능성도 남깁니다. 둘째, 하네스 공개 여부입니다. 영속 상태와 교차 모델 검증이 공개되면 이 스킬은 그 입문 단계로 위치가 분명해집니다. 셋째, 문서로만 있는 절차(승격, 환경 격리)가 실행 가능한 스크립트로 바뀌는지입니다. 그 전까지는 "스킬이 요구하는 안전 조건"과 "내 환경이 실제로 보장하는 조건"을 사용자가 직접 맞춰 봐야 합니다.

<!-- EDITOR_NOTE: 운영자가 직접 써 본 경험이나 의견을 여기에 추가하세요. (예: 실제 저장소에 quick 프로필로 돌려 본 결과, needs_validation 비율, 소요 시간과 비용) -->

## 이런 분께 추천

- 코딩 에이전트용 보안 리뷰 프롬프트나 사내 스킬을 직접 쓰고 있고, 검증된 판정 규칙과 공격 유형 문서를 참고하고 싶은 보안 담당자
- 자체 취약점 탐색 파이프라인을 설계하면서 발견 스키마, 커버리지 관리, 독립 검증 구조의 구체적인 예를 찾는 팀
- 격리된 Linux 환경과 병렬 서브에이전트를 쓸 수 있고, 자기 저장소를 주기적으로 깊게 점검해 보려는 개발자
- 에이전트가 낸 보안 발견을 이슈 트래커에 넣기 전에 형식을 기계적으로 검사하고 싶은 경우

## 이런 경우엔 다른 도구

- **PR마다 변경분을 빠르게 검사하고 싶다면:** diff 기반 리뷰어(예: Claude Code Security Reviewer)나 규칙 기반 SAST가 비용과 시간 면에서 맞습니다. 이 스킬은 주기적인 전체 점검 쪽에 가깝습니다.
- **의존성의 알려진 취약점을 찾는 것이 목적이라면:** 네트워크를 쓰지 않는 이 스킬의 범위 밖입니다. 의존성 검사 도구를 쓰는 것이 맞습니다.
- **Windows에서 그대로 쓰려 한다면:** 검증 스크립트가 동작하지 않는 문제가 열려 있습니다(2026-11-20 기준). 격리된 Linux 환경을 따로 준비해야 합니다.
- **업스트림의 버그 수정과 지원이 필요한 운영 환경이라면:** 현재 유지보수 상태로는 포크를 직접 관리할 여력이 있을 때만 권할 수 있습니다.
- **신뢰할 수 없는 외부 저장소를 감사해야 한다면:** 대상 저장소의 에이전트 설정이 먼저 읽히는 문제를 스스로 통제할 수 있어야 합니다.

## 참고 링크

- [GitHub 저장소 / README](https://github.com/cloudflare/security-audit-skill) · [LICENSE](https://github.com/cloudflare/security-audit-skill/blob/main/LICENSE) · [커밋 이력](https://github.com/cloudflare/security-audit-skill/commits/main) · [PR #12 (2026-09-10 전면 개편)](https://github.com/cloudflare/security-audit-skill/pull/12) · [이슈 트래커](https://github.com/cloudflare/security-audit-skill/issues)
- [SKILL.md](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/SKILL.md) · [RECONNAISSANCE.md](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/RECONNAISSANCE.md) · [HUNTING.md](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/HUNTING.md) · [ATTACK-CLASSES.md](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/ATTACK-CLASSES.md) · [AI-AND-LLM.md](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/AI-AND-LLM.md) · [VALIDATION-AND-REPORTING.md](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/VALIDATION-AND-REPORTING.md)
- [report-schema.json](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/report-schema.json) · [validate-findings.cjs](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/validate-findings.cjs) · [validate-coverage-ledger.cjs](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/validate-coverage-ledger.cjs) · [validate-findings.test.cjs (예제 3의 픽스처)](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/validate-findings.test.cjs)
- [Cloudflare 블로그: Build your own vulnerability harness (2026-06-18)](https://blog.cloudflare.com/build-your-own-vulnerability-harness/)
- [Skills CLI (skills.sh)](https://skills.sh)
- 비교 대상: [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review) · [trailofbits/skills](https://github.com/trailofbits/skills)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
