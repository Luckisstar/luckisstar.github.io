---
layout: default
title: "[기술 소개] Agent Skills, Linux Foundation 산하 AAIF로: MCP에 이은 두 번째 에이전트 표준 기증"
description: "Anthropic이 Agent Skills 표준을 AAIF에 기증한 내용과 SKILL.md 명세, 점진적 공개 방식, MCP와의 역할 분담, skills-ref 검증 예제, 스킬 공급망 보안 쟁점을 정리했습니다."
date: 2026-10-24 00:45:56 +0900
categories: [tech]
---

# [기술 소개] Agent Skills, Linux Foundation 산하 AAIF로: MCP에 이은 두 번째 에이전트 표준 기증

- **발표:** Anthropic, 2026년 10월 22일
- **원문:** [공식 발표](https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation) · [명세 저장소 agentskills/agentskills](https://github.com/agentskills/agentskills) · [엔지니어링 블로그(2025-10-16)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- **한눈에 (2026-10-22 공식 발표 기준):** 70개 이상 에이전트 플랫폼이 통합, 공개된 스킬 100만 개, 설치 약 2.8억 회(nearly 280 million). 수치는 모두 Anthropic이 밝힌 값이며 집계 방법은 공개되지 않았습니다.
- **주의:** 스킬은 지시문과 함께 실행 가능한 스크립트를 담을 수 있어, 출처를 확인하지 않은 스킬 설치는 공급망 위험이 됩니다. 공식 보안 가이드는 아직 로드맵 단계입니다(아래 "한계와 논란" 참고).

## 한 줄 요약

**Anthropic이 `SKILL.md` 폴더 형식의 에이전트 확장 표준 Agent Skills를 MCP와 같은 재단(AAIF)에 넘겨, 에이전트 생태계의 "도구 연결(MCP)"과 "절차 지식(Skills)" 표준이 한 지붕 아래 모이게 됐습니다.**

## 배경

Agent Skills는 Anthropic이 2025년 10월 16일 Claude의 기능으로 처음 공개했습니다. 당시 엔지니어링 블로그는 Claude Code 같은 범용 에이전트가 강력해질수록 "도메인별 전문 지식을 조합 가능하고, 확장 가능하며, 이식 가능한 방식으로 갖춰 줄 방법"이 필요해졌다고 설명했습니다. 이번 발표문도 같은 맥락으로, Claude Code가 일반 지식 업무는 잘 했지만 실제 업무에 필요한 절차적 지식(procedural knowledge)이 부족한 경우가 많았다고 적고 있습니다.

이후 흐름을 1차 자료의 날짜로 정리하면 다음과 같습니다.

| 날짜 | 사건 | 출처 |
|---|---|---|
| 2025-10-16 | Claude에 Skills 기능 출시, 엔지니어링 블로그 공개 | [Introducing Agent Skills](https://www.anthropic.com/news/skills) |
| 2025-12-09 | MCP를 AAIF에 기증, AAIF 설립(Anthropic·Block·OpenAI 공동 설립) | [MCP 기증 발표](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation) |
| 2025-12-18 | Agent Skills를 개방형 표준으로 공개, 조직 단위 관리와 파트너 스킬 디렉터리 추가 | [Skills for organizations](https://claude.com/blog/organization-skills-and-directory) |
| 2026-10-22 | Agent Skills 표준을 AAIF에 기증 | [공식 발표](https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation) |

AAIF(Agentic AI Foundation)는 2025년 12월 MCP 기증 발표에서 "Linux Foundation 산하의 directed fund"로 소개됐고, Google, Microsoft, AWS, Cloudflare, Bloomberg가 지원한다고 밝혔습니다. 당시 창립 프로젝트는 MCP, Block의 goose, OpenAI의 AGENTS.md였습니다. Agent Skills는 Anthropic이 이 재단에 넘기는 두 번째 표준입니다.

## 핵심 내용

### 1. 무엇을 넘겼나: 이름, 로고, GitHub 조직, 도메인

발표문에 따르면 Anthropic은 Agent Skills의 **이름과 로고, GitHub 조직(`agentskills`), `agentskills.io` 도메인**을 AAIF에 기증합니다. 표준을 쓰거나 기여하는 데 AAIF 가입은 필요하지 않습니다.

유지보수는 Anthropic, Google, OpenAI 등 여러 회사의 엔지니어가 회사 대표가 아닌 **개인 자격**으로 맡고, 리드 메인테이너는 David Soria Parra와 Mahesh Murag입니다. Mahesh Murag는 2025년 10월 엔지니어링 블로그의 공동 저자 중 한 명이기도 합니다.

명세 저장소의 라이선스는 README 기준으로 코드(참조 라이브러리 등)가 Apache 2.0, 문서가 CC-BY-4.0입니다(2026-10-24 확인).

### 2. 표준의 실체: `SKILL.md`가 든 폴더 하나

[명세](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx)는 짧습니다. 스킬은 최소한 `SKILL.md` 파일 하나를 가진 디렉터리이고, 나머지는 권장 관례입니다.

```
skill-name/
├── SKILL.md          # 필수: 메타데이터 + 지시문
├── scripts/          # 선택: 실행 가능한 코드
├── references/       # 선택: 문서
├── assets/           # 선택: 템플릿, 리소스
└── ...               # 그 밖의 파일이나 디렉터리
```

`SKILL.md`는 YAML 프런트매터(front matter, 파일 머리의 메타데이터 블록)와 마크다운 본문으로 이뤄집니다. 명세가 정한 필드는 6개뿐입니다.

| 필드 | 필수 | 제약 (명세 원문 기준) |
|---|---|---|
| `name` | 예 | 1~64자, 소문자·숫자·하이픈만, 하이픈으로 시작·끝 불가, `--` 불가, 상위 디렉터리 이름과 일치 |
| `description` | 예 | 1~1024자. 무엇을 하는지와 언제 쓰는지를 함께 적도록 권장 |
| `license` | 아니요 | 라이선스 이름 또는 동봉한 라이선스 파일 참조 |
| `compatibility` | 아니요 | 1~500자. 대상 제품, 필요한 시스템 패키지, 네트워크 접근 등 환경 요구사항 |
| `metadata` | 아니요 | 문자열 키와 문자열 값의 맵. 명세에 없는 속성을 클라이언트가 저장하는 용도 |
| `allowed-tools` | 아니요 | 미리 승인된 도구 목록(공백 구분). **실험적**이며 구현마다 지원이 다름 |

본문 형식에는 제한이 없습니다. 명세는 단계별 지시, 입력과 출력 예시, 흔한 예외 상황을 권장 섹션으로 들고, `SKILL.md`는 500줄 이하로 유지하고 자세한 내용은 별도 파일로 빼라고 권합니다.

### 3. 핵심 설계: 점진적 공개(progressive disclosure)

스킬이 "폴더 하나"로 충분한 이유는 로딩 방식에 있습니다. 명세와 [클라이언트 구현 가이드](https://github.com/agentskills/agentskills/blob/main/docs/client-implementation/adding-skills-support.mdx)는 세 단계를 정의합니다.

| 단계 | 불러오는 것 | 시점 | 토큰 비용 (가이드 기준) |
|---|---|---|---|
| 1. 카탈로그 | `name`과 `description` | 세션 시작 | 스킬당 약 50~100 |
| 2. 지시문 | `SKILL.md` 본문 전체 | 스킬을 활성화할 때 | 5,000 미만 권장 |
| 3. 리소스 | 스크립트, 참고 문서, 에셋 | 지시문이 참조할 때 | 경우에 따라 다름 |

가이드의 설명대로, 스킬 20개를 설치해도 처음부터 20개 지시문 전부의 토큰을 내지 않고 실제로 쓰는 것만 불러옵니다. 엔지니어링 블로그는 파일 시스템과 코드 실행 도구가 있는 에이전트라면 "스킬에 묶을 수 있는 컨텍스트의 양이 사실상 무제한"이라고까지 표현했습니다.

여기서 활성화를 결정하는 주체는 대부분 **모델 자신**입니다. 가이드는 "대부분의 구현이 하네스 쪽 키워드 매칭이 아니라 모델의 판단에 의존한다"고 적고 있습니다. 그래서 `description`이 사실상 스킬의 검색 키워드 역할을 합니다. 명세가 `description`에 "언제 쓰는지"를 반드시 넣으라고 권하는 이유입니다.

### 4. 클라이언트 구현 관례: `.agents/skills/`와 신뢰 확인

명세는 스킬 폴더 **안**의 형식만 정하고, 스킬을 **어디에** 두는지는 정하지 않습니다. 대신 구현 가이드가 관례를 정리해 두었습니다.

- 프로젝트 단위는 `<project>/.agents/skills/`, 사용자 단위는 `~/.agents/skills/`를 클라이언트 간 공유 경로로 함께 스캔하라고 권합니다. 가이드는 이 경로를 "널리 채택된 관례"로 소개합니다.
- 이름이 겹치면 **프로젝트 단위가 사용자 단위를 덮어쓰는** 것이 기존 구현의 공통 관례라고 합니다.
- 프로젝트 단위 스킬은 방금 클론한 오픈소스처럼 신뢰할 수 없는 저장소에서 올 수 있으므로, **사용자가 신뢰한다고 표시한 폴더에서만 불러오는** 신뢰 확인을 고려하라고 권합니다.
- 컨텍스트 압축(오래된 대화를 요약하거나 잘라내는 것) 때 스킬 지시문은 지우지 말라고 권합니다. 지시문이 사라지면 오류 없이 성능만 조용히 떨어지기 때문입니다.

### 5. 다음 단계: 버전 릴리스, 제안 절차, 보안 가이드

발표문은 첫 로드맵으로 **버전이 붙은 릴리스, 공식 제안 절차, 스킬을 쓰고 설치하는 사람을 위한 보안 가이드**를 제안했다고 밝혔습니다. 명세 변경에 대한 의견은 프로젝트 Discord에서 받습니다.

이 세 항목은 현재 상태와 맞물려 있습니다. 2026-10-24 기준 명세 저장소에는 git 태그가 없고, 명세 문서에도 버전 번호가 없습니다. 기여 가이드(CONTRIBUTING.md)는 제안을 GitHub Discussions로 받되 "명세에 더하기는 빼기보다 훨씬 쉽다, 의심스러우면 넣지 말라"는 높은 기준을 적어 두었습니다.

## 성능과 비교

벤치마크가 있는 발표가 아니므로, 채택 현황과 MCP와의 비교를 정리합니다.

**채택 현황**

| 지표 | 값 | 기준·측정 주체 |
|---|---|---|
| 통합한 에이전트 플랫폼 | 70개 이상 (ChatGPT, Cursor, GitHub Copilot, VS Code 등) | Anthropic 발표, 2026-10-22 |
| 공개된 스킬 | 100만 개 | Anthropic 발표, 2026-10-22 |
| 설치 | 약 2.8억 회 | Anthropic 발표, 2026-10-22 |
| 공식 클라이언트 쇼케이스 등재 | 46개 | 명세 저장소 `docs/snippets/clients.jsx`, 마지막 커밋 2026-08-09 |

쇼케이스(46개)와 발표(70개 이상)의 차이는 집계 기준이 다르기 때문으로 보입니다. 기여 가이드에 따르면 쇼케이스는 "지금 공개적으로 스킬을 발견하고 실행할 수 있는" 제품이 PR로 신청해야 등재됩니다. 쇼케이스에는 Gemini CLI, OpenCode, OpenHands, Goose, Kiro, Junie, Roo Code, Spring AI 등이 올라 있습니다.

**MCP와의 역할 분담**

| 구분 | MCP | Agent Skills |
|---|---|---|
| 다루는 것 | 외부 시스템과의 연결(도구, 데이터) | 작업 절차와 도메인 지식 |
| 형태 | 클라이언트·서버 프로토콜, 언어별 SDK | `SKILL.md`가 든 폴더 |
| 실행 위치 | 별도 서버 프로세스 | 에이전트 자신의 컨텍스트와 실행 환경 |
| 컨텍스트 비용 관리 | (MCP 발표 기준) Tool Search 등 별도 기능으로 대응 | 명세 자체가 3단계 점진적 공개 |
| AAIF 기증 | 2025-12-09 | 2026-10-22 |

표의 MCP 항목은 Anthropic의 MCP 기증 발표와 일반적으로 알려진 특징 기준입니다. 2025년 10월 엔지니어링 블로그는 스킬이 "외부 도구와 소프트웨어가 얽힌 복잡한 워크플로를 가르쳐 MCP 서버를 보완"하는 방향을 탐색하겠다고 적었고, 2025년 12월 파트너 발표에서 Zapier는 "스킬은 일을 어떻게 해야 하는지 알고, Zapier MCP 도구가 그것을 실행한다"고 설명했습니다. 둘은 경쟁이 아니라 "무엇을 할 수 있나(MCP)"와 "어떻게 해야 하나(Skills)"로 나뉜다고 보는 것이 자연스럽습니다.

## 써 볼 수 있나

명세 저장소의 참조 라이브러리 `skills-ref`로 스킬을 검증해 볼 수 있습니다. README는 이 라이브러리가 **데모 목적이며 운영 환경용이 아니라고** 명시합니다. 아래 예제는 필자가 2026-10-24에 저장소를 클론해 Python 가상환경에서 `pip install -e .`로 설치하고 직접 실행한 결과입니다.

**예제 1. 최소한의 스킬 만들기**

```markdown
---
name: release-notes
description: Drafts Korean release notes from merged pull requests. Use when the user asks for release notes, a changelog, or a summary of changes since the last tag.
license: Apache-2.0
compatibility: Requires git and the gh CLI
metadata:
  author: example-team
  version: "0.1"
---

# Release notes

1. Find the previous tag with `git describe --tags --abbrev=0`.
2. Run `scripts/list_prs.sh <tag>` to list merged PRs since that tag.
3. Group the PRs into Features, Fixes, and Chores, then write the notes in Korean.
```

이 파일을 `release-notes/SKILL.md`로 저장하고, 본문이 참조하는 `release-notes/scripts/list_prs.sh`를 함께 둡니다. 폴더 이름과 `name`이 같아야 합니다. 스킬의 실제 동작(에이전트가 이 지시를 따라 릴리스 노트를 쓰는지)은 확인하지 않았고, 아래 검증 도구의 동작만 확인했습니다.

**예제 2. 검증과 카탈로그 생성**

```bash
$ skills-ref validate release-notes
Valid skill: release-notes

$ skills-ref to-prompt release-notes
<available_skills>
<skill>
<name>
release-notes
</name>
<description>
Drafts Korean release notes from merged pull requests. Use when ...
</description>
<location>
/.../release-notes/SKILL.md
</location>
</skill>
</available_skills>
```

`to-prompt`의 출력이 바로 1단계 카탈로그입니다. README는 이 XML 형식이 Anthropic 모델에 권장되는 형식이고, 다른 클라이언트는 모델에 맞게 달리 구성해도 된다고 설명합니다.

**예제 3. 규칙 위반 확인**

```bash
$ skills-ref validate Bad_Skill
Validation failed for Bad_Skill:
  - Skill name 'Bad_Skill' must be lowercase
  - Skill name 'Bad_Skill' contains invalid characters. Only letters, digits, and hyphens are allowed.
```

(출력의 `description` 일부와 경로는 지면 때문에 줄였습니다.) 참고로 구현 가이드는 클라이언트가 이름 규칙 위반 정도는 경고만 하고 스킬을 불러오는 "관대한 검증"을 권합니다. 즉 `validate`를 통과하지 못해도 클라이언트에 따라서는 동작할 수 있으므로, 이식성을 원한다면 작성 단계에서 엄격하게 검증하는 편이 안전합니다.

**비용과 조건:** 표준 자체와 참조 라이브러리는 무료이며, 사용이나 기여에 AAIF 가입이 필요 없습니다(발표 기준). 실제로 스킬을 돌리는 비용은 각 에이전트 제품의 요금제를 따릅니다.

## 한계와 논란

- **보안 가이드가 아직 없습니다.** Anthropic 엔지니어링 블로그는 악성 스킬이 "환경에 취약점을 들이거나 Claude가 데이터를 유출하고 의도하지 않은 행동을 하도록 지시할 수 있다"고 경고하고, 신뢰할 수 있는 출처의 스킬만 설치하고 그렇지 않으면 동봉 파일과 스크립트, 외부 네트워크 접속 지시를 직접 감사하라고 권합니다. 표준 차원의 보안 가이드는 이번 로드맵에서야 제안된 상태입니다.
- **서명이나 출처 증명 같은 장치가 명세에 없습니다.** 명세의 필드는 6개뿐이고, 무결성 검증이나 게시자 확인에 해당하는 필드는 없습니다(2026-10-24 명세 기준). 100만 개라는 공개 스킬 수는 생태계의 크기이면서 동시에 감사해야 할 대상의 크기이기도 합니다.
- **`allowed-tools`는 실험적입니다.** 스킬이 쓸 도구를 미리 승인하는 필드라 권한 모델의 핵심이 될 수 있지만, 명세가 "구현마다 지원이 다르다"고 밝혀 클라이언트 간 동작이 같다고 기대할 수 없습니다.
- **채택 수치는 자체 발표입니다.** 70개 플랫폼, 100만 스킬, 2.8억 설치는 Anthropic이 밝힌 값이고, "설치"를 무엇으로 셌는지(다운로드, 활성화, 중복 포함 여부)는 공개되지 않았습니다.
- **명세에 버전이 없습니다.** 지금까지 클라이언트들은 버전 번호 없는 문서와 쇼케이스를 기준으로 맞춰 왔습니다. 버전 릴리스가 도입되면 기존 스킬의 호환성 표기 방식이 바뀔 수 있습니다.

## 인사이트

**왜 지금 중요한가.** MCP 기증 때와 구조가 같습니다. 한 회사가 만든 형식이 경쟁사 제품(ChatGPT, Cursor, GitHub Copilot)까지 퍼진 뒤, 상표·도메인·저장소라는 "통제 지점"을 중립 재단으로 옮긴 것입니다. 기술은 바뀌지 않았지만, 이제 다른 회사가 이 표준에 투자해도 Anthropic이 방향을 일방적으로 바꿀 위험이 줄었습니다. 경쟁사 엔지니어들이 개인 자격으로 메인테이너에 참여한다는 점은 이 중립성이 형식만은 아니라는 신호로 보입니다. 필자의 판단으로는, 에이전트 생태계의 표준 경쟁이 "어느 회사 형식이 이기나"에서 "같은 재단 안에서 어떻게 역할을 나누나"로 넘어가고 있습니다. AAIF에는 이제 도구 연결(MCP), 저장소 안내문(AGENTS.md), 절차 지식(Agent Skills)이 함께 있습니다.

**실무에 주는 의미.** 팀이 에이전트에게 반복해서 설명하는 절차(배포 순서, 리뷰 기준, 사내 문서 양식)가 있다면, 특정 제품의 설정 파일 대신 `SKILL.md` 폴더로 정리해 저장소에 넣는 쪽이 이식성이 높아졌습니다. 이때 두 가지를 권합니다. 첫째, 경로는 클라이언트 전용 디렉터리보다 구현 가이드가 소개한 `.agents/skills/`를 우선 고려합니다. 둘째, `description`을 신경 써서 씁니다. 활성화를 모델이 판단하므로 "무엇을 하는가"만 있고 "언제 쓰는가"가 없는 설명은 호출되지 않는 스킬이 됩니다. 반대로 에이전트 제품을 만드는 쪽이라면, 구현 가이드의 신뢰 확인(신뢰하지 않은 저장소의 프로젝트 스킬을 자동으로 불러오지 않기)과 컨텍스트 압축 시 스킬 보호는 표준 문서가 이미 권하는 내용이므로 기본값으로 갖추는 것이 좋겠습니다.

**블로그의 기존 글과의 연결.** [OpenHands 소개](/opensource/2026/10/20/openhands.html)에서 다룬 OpenHands도 Agent Skills 공식 쇼케이스에 등재된 클라이언트입니다. 그 글이 "에이전트를 어떻게 운영하나"를 다뤘다면, 이 표준은 "운영하는 에이전트에게 팀의 지식을 어떤 형식으로 넘기나"에 해당합니다. 에이전트 런타임은 여러 개를 섞어 쓰더라도 스킬 폴더는 하나로 유지할 수 있다는 점이 실용적인 공통분모입니다.

**한계와 반론.** 이 표준의 강점인 단순함은 그대로 약점이기도 합니다. 스킬은 본질적으로 "에이전트가 읽고 따르는 마크다운과 스크립트"이므로, 프롬프트 인젝션(prompt injection, 입력 속 지시문으로 모델을 조종하는 공격)과 공급망 공격이 같은 통로로 들어옵니다. 성숙한 패키지 생태계가 갖춘 서명이나 출처 증명 같은 장치가 Agent Skills 명세에는 아직 없습니다. 또한 명세가 형식만 정하고 활성화 판단은 모델에 맡기기 때문에, 같은 스킬이라도 클라이언트와 모델에 따라 호출 여부와 결과가 달라질 수 있습니다. "한 번 만들면 어디서나 동작한다"는 이식성은 파일 형식 수준의 약속이고, 결과의 동일성까지 보장하지는 않는다고 보는 것이 정확합니다.

**앞으로 지켜볼 점.** (1) 로드맵의 보안 가이드가 권고 문서에 그칠지, 서명이나 게시자 확인 같은 명세 필드로 이어질지. (2) 첫 버전 릴리스가 나올 때 `allowed-tools`가 실험 단계를 벗어나는지. 이 필드가 확정되면 스킬이 권한 경계까지 표현하게 됩니다. (3) AAIF 안에서 MCP와 Skills를 잇는 공식 연결 방식(예를 들어 스킬이 필요한 MCP 서버를 선언하는 방법)이 논의되는지. 세 가지 중 첫 번째가 가장 중요하며, 이것이 나오기 전까지는 외부 스킬을 코드 의존성과 같은 수준으로 검토하는 것이 안전합니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [Donating Agent Skills to the Agentic AI Foundation (Anthropic, 2026-10-22)](https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation)
- [agentskills/agentskills: 명세, 문서, 참조 라이브러리 저장소](https://github.com/agentskills/agentskills)
- [Agent Skills 명세 원문](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx)
- [How to add skills support to your agent (클라이언트 구현 가이드)](https://github.com/agentskills/agentskills/blob/main/docs/client-implementation/adding-skills-support.mdx)
- [Equipping agents for the real world with Agent Skills (Anthropic 엔지니어링 블로그, 2025-10-16)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Introducing Agent Skills (Anthropic, 2025-10-16)](https://www.anthropic.com/news/skills)
- [Skills for organizations, partners, the ecosystem (Claude 블로그, 2025-12-18)](https://claude.com/blog/organization-skills-and-directory)
- [Donating the Model Context Protocol and establishing the Agentic AI Foundation (Anthropic, 2025-12-09)](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
