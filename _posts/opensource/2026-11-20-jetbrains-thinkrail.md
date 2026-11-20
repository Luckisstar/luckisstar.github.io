---
layout: default
title: "[오픈소스 소개] ThinkRail: 워크트리와 스펙 그래프로 pi 에이전트를 감싼 JetBrains의 에이전트 IDE"
description: "JetBrains 인큐베이터 프로젝트 ThinkRail의 구조(pi 엔진 내장, 워크트리 작업 공간, SPEC.md 그래프와 spec 도구), 설치와 예제, 끌 수 없는 기본 텔레메트리와 샌드박스 부재, Orca·AGENTS.md와의 차이를 정리했습니다."
date: 2026-11-20 14:30:00 +0900
categories: [opensource]
---

# [오픈소스 소개] ThinkRail: 워크트리와 스펙 그래프로 pi 에이전트를 감싼 JetBrains의 에이전트 IDE

- **저장소:** [JetBrains/thinkrail](https://github.com/JetBrains/thinkrail) · [공식 사이트](https://thinkrail.ai/) · [공식 블로그](https://thinkrail.ai/blog/) (별도 문서 사이트는 아직 없고, 랜딩 페이지의 Docs 항목은 “Coming soon”입니다)
- **라이선스:** Apache-2.0 (LICENSE 저작권 표기: 2026 JetBrains s.r.o.). 내장 엔진인 pi는 별도 프로젝트이며 pi.dev 표기 기준 MIT 라이선스입니다.
- **언어:** TypeScript (Bun 런타임 위의 호스트, React 19 웹 UI, Electrobun 데스크톱 셸)
- **현황 (2026-11-20 기준):** GitHub 스타 약 8,400개, 포크 약 530개, 열린 이슈 191개, 커밋 약 860개. 저장소 생성일은 2026년 7월 8일, 최신 안정 릴리스는 v0.4.0 (2026년 11월 12일)이고 야간 빌드가 거의 매일 나옵니다(v0.5.0-nightly.7, 2026년 11월 19일). 조회 당일에도 push가 있는 활발한 프로젝트입니다.
- **도입 전 확인할 점 1, 성숙도:** **JetBrains의 “인큐베이터(incubator)” 등급 프로젝트이고 버전은 0.x입니다.** JetBrains는 인큐베이터 프로젝트를 자사가 개발하는 공식 프로젝트이되 “실험적이거나, 충분히 성숙하지 않았거나, 테스트·문서 같은 릴리스 품질이 부족한 것으로 간주되며 있는 그대로(as is) 제공된다”고 정의합니다. 알파·베타 같은 단계 표기는 README에 없고, 공식 블로그는 “개발 초기 단계”라고 밝힙니다.
- **도입 전 확인할 점 2, 텔레메트리:** **공식 배포 빌드는 기본 사용 이벤트(실행, 채팅 생성, 메시지 전송, 제공자 연결)와 오류 보고를 항상 전송하며, 이를 끄는 설정은 문서에 없습니다.** 끌 수 있는 것은 “추가 사용 데이터”뿐입니다(Settings → Privacy, `--no-analytics`, `THINKRAIL_NO_ANALYTICS=1`). README는 프롬프트, 코드, 파일, 자격 증명, 계정 정보는 포함하지 않고 무작위 설치 ID에만 묶인다고 설명합니다. 분석 서비스는 PostHog입니다.
- **도입 전 확인할 점 3, 권한:** **워크트리는 브랜치를 격리할 뿐 보안 샌드박스가 아닙니다.** 프로젝트 협업자가 직접 올린 이슈 #918은 “에이전트가 모든 셸 명령과 파일 수정을 사용자 권한으로 실행하고, 도구 호출마다 묻지 않는다”고 적고 있으며, OS 수준 샌드박스는 아직 제안 단계입니다(2026-11-20 기준 열린 이슈).
- **계정:** ThinkRail 자체 계정은 없습니다. 대신 모델 제공자가 필요합니다(JetBrains AI 로그인 또는 pi의 인증을 통한 다른 제공자, 직접 운영하는 OpenAI 호환 서버).

## 한 줄 요약

**ThinkRail은 코딩 에이전트 pi를 프로세스 안에 그대로 내장하고, 그 둘레에 git 워크트리 작업 공간, 편집기·diff·터미널, 그리고 에이전트가 읽고 고치는 `SPEC.md` 그래프를 붙인 오픈소스 에이전트 IDE입니다.** 직접 에이전트를 새로 만든 것이 아니라 “pi의 얇은 호스트”를 자처한다는 점이 특징입니다. pi를 이미 쓰거나 써 보려는 개발자, 그리고 에이전트 작업의 의도를 채팅 기록이 아니라 저장소 안의 문서로 남기고 싶은 팀이 살펴볼 만합니다.

## 어떤 문제를 푸나

ThinkRail의 제품 스펙(`goal-and-requirements.md`)은 문제를 세 가지로 적습니다.

- **병렬 에이전트의 충돌:** 한 작업 디렉터리에서 여러 에이전트가 서로의 변경, 그리고 사용자의 편집과 부딪힙니다.
- **리뷰의 어려움:** CLI에서는 diff를 읽고, 정확한 줄에 코멘트를 달고, 그 피드백을 에이전트에게 돌려주기가 번거롭습니다.
- **의도의 증발:** 채팅에서 내린 결정은 세션과 함께 사라지고, 다음 세션은 그것을 다시 추론하거나 뒤집습니다.

여기에 pi 고유의 사정이 더해집니다. pi는 스스로를 “최소한의 에이전트 하네스”라고 소개하며, 서브에이전트나 플랜 모드 같은 기능을 일부러 넣지 않고 확장으로 만들게 합니다. 공식 블로그의 소개 글은 이 유연함의 대가로 **신규 사용자는 pi를 다루는 법을 익히는 데 시간을 쓰고, 숙련자도 에이전트 주변 작업이 터미널에서는 거추장스럽다**고 진단합니다.

ThinkRail의 답은 세 갈래입니다. 작업 공간을 기본적으로 워크트리로 격리하고, 에이전트 둘레에 실제 IDE 화면(편집기, diff, 터미널, 리뷰)을 두고, 프로젝트의 의도를 코드 옆 스펙 그래프에 적어 세션이 끝나도 남게 합니다.

## 핵심 개념

| 개념 | 설명 |
|---|---|
| pi | ThinkRail이 내장한 코딩 에이전트. npm 패키지 `@earendil-works/pi-coding-agent`이며, 모델 목록, 시스템 프롬프트, 스킬·확장, 컴팩션(대화 요약 압축), 비용, 세션 상태를 소유합니다 |
| 프로젝트 | ThinkRail에 연 git 저장소 하나 |
| 워크스페이스 | 프로젝트에서 만든 `git worktree`. 자체 브랜치와 작업 디렉터리를 가지며 `~/.thinkrail/worktrees` 아래에 생깁니다 |
| Default | 프로젝트 폴더 자체에서 작업하는 내장 워크스페이스. 사용자가 명시적으로 골라야 들어갑니다 |
| 스펙 그래프 | YAML 머리말(frontmatter)의 `id`, `parent`, `depends-on` 등으로 서로 연결된 `SPEC.md` 문서들의 그래프 |
| `spec_*` 도구 | 에이전트가 스펙을 검색·탐색·생성·검증하는 전용 도구 8개 |
| 아티팩트 | 에이전트가 만든 설계 노트, 목업, 다이어그램, 보고서. 워크스페이스의 gitignore 대상 폴더 `.thinkrail/context/`에 쌓입니다 |
| 신뢰(trust) | 복제한 저장소가 에이전트에 주입할 수 있는 것(`.pi/` 설정, 확장, 스킬, 저장소가 정의한 MCP 서버)을 프로젝트 단위로 허용하는 절차 |

스펙 문서의 종류는 다섯 가지입니다. 제품 목표와 범위를 담는 `goal-and-requirements`(그래프의 뿌리), 시스템 전체 구조와 결정을 담는 `architecture-design`, 패키지 단위의 `module-design`, 디렉터리 단위의 `submodule-design`, 그리고 한 건의 작업용 임시 문서인 `task-spec`입니다.

## 동작 원리

README는 구조를 한 문장으로 요약합니다. “ThinkRail은 pi를 프로세스 안에서 돌리고 웹 UI로 연결하는 얇은 호스트”이며, pi가 모델·스킬·컴팩션·비용·세션 상태를 맡고 ThinkRail은 작업 공간 관리, GUI, 엔진과 GUI 사이의 계약을 맡습니다. 아키텍처 문서(`architecture.md`)는 이를 “세 개의 고리”라고 부릅니다.

```
 실행기 (둘 다 같은 호스트를 내장)
 ├─ apps/cli      thinkrail 명령 → 호스트 부팅 + 브라우저 열기
 └─ apps/desktop  Electrobun 셸 → 호스트 부팅 + 시스템 웹뷰 창
        │
        ▼
 ① 엔진 호스트 (packages/server)
    Bun.serve HTTP + WebSocket
    ├─ 채팅 하나당 프로세스 내 pi 세션 하나 (createAgentSession)
    ├─ 모든 세션에 묶어 넣는 확장: pi-spec-graph, pi-thinkrail-workflow,
    │   pi-todos, visualize, ask-user-question, web-access
    └─ 워크스페이스(git worktree), 리뷰, PR, 터미널, 아티팩트 관리
        │
        ▼
 ② 와이어 (packages/contracts): 타입이 붙은 버전 관리 프로토콜
        │
        ▼
 ③ UI 클라이언트 (apps/web): React 19 + Zustand + Tailwind v4
    Monaco 편집기 탭, 파일 트리, diff, 터미널, 채팅, Specs 트리
```

설계 원칙 가운데 눈에 띄는 것을 옮기면 다음과 같습니다.

1. **pi가 유일한 엔진입니다.** 두 번째 에이전트 런타임을 두지 않고, 호스트가 자체 에이전트 루프나 프롬프트 조립을 하지 않습니다. 스펙 문서는 `claude-agent-sdk`를 쓰지 않는다고 명시합니다.
2. **조립하지 않고 먹입니다(Influence by feeding).** 기능은 pi에 주는 것(프롬프트 맥락, 파일, pi의 스킬과 확장, 세션 시작 플래그)으로만 에이전트에 영향을 줍니다. 예를 들어 “스펙을 따르라”는 규칙도 호스트가 프롬프트에 끼워 넣는 것이 아니라 `pi-spec-graph` 확장이 pi의 `before_agent_start` 훅으로 시스템 프롬프트의 한 구획에 넣습니다.
3. **보여 주되 다시 계산하지 않습니다.** 토큰과 비용은 pi가 보고한 값을 그대로 표시합니다.
4. **사용자의 도구와 자격 증명을 씁니다.** git, GitHub, 모델 접근은 사용자의 `git`, `gh`, `central` CLI와 pi의 제공자 인증을 거치고, ThinkRail은 자체 계정이나 토큰을 갖지 않습니다.

스펙 그래프의 읽기 모델도 단순합니다. `packages/spec-graph` 스펙에 따르면 **파일 시스템이 유일한 진실의 원천**이고, 도구가 읽는 인덱스는 메모리 안의 파생 캐시입니다. 읽을 때마다 파일 목록을 다시 훑고 수정 시각과 크기가 바뀐 파일만 다시 파싱합니다. 검색은 임베딩이 아니라 단어 기반 순위(스펙 문서 표기로 BM25F)이며, 의미 검색은 명시적인 비목표입니다. 단어가 겹치지 않는 질문(바꿔 말하기, 다른 언어)은 에이전트가 질문을 여러 표현으로 바꿔 넣는 것으로 해결한다고 설명합니다.

한 가지 감수한 약점도 저장소의 `AGENTS.md`에 적혀 있습니다. pi를 하위 프로세스가 아니라 같은 프로세스에서 돌리기 때문에 제공자나 에이전트의 치명적 오류가 호스트 전체를 내릴 수 있고, 이 “크래시 격리 부재”는 받아들인 결정이라고 합니다.

## 주요 기능

### 워크트리 작업 공간과 정착(Settled) 선반

워크스페이스를 만들면 `~/.thinkrail/worktrees/<프로젝트>/workspace-1` 같은 별도 디렉터리에 브랜치가 체크아웃되고, 에이전트의 변경은 사용자가 병합을 요청할 때까지 원래 폴더에 닿지 않습니다. 기존 워크트리를 그대로 붙이거나, 채팅에서 “in a side workspace”라고 요청해 에이전트가 직접 옆 작업 공간과 채팅을 띄우게 할 수도 있습니다. PR이 병합되거나 닫히면, 또는 한 주 동안 조용하면 워크스페이스는 Settled 선반으로 옮겨지고, 다시 작업하면 돌아옵니다.

### 스펙 그래프와 Specs 도구

에이전트는 `spec_search`(질문에 답하는 구획을 단어 순위로 찾기), `spec_grep`, `spec_get`, `spec_graph`로 스펙을 읽고, `spec_create`, `spec_update`(머리말만 수정), `spec_delete`, `spec_validate`(끊어진 링크, 중복 id, 부모 순환 보고)로 구조를 관리합니다. 본문은 일반 `read`/`write`/`edit` 도구로 고칩니다. 사람은 오른쪽의 읽기 전용 Specs 도구에서 그래프를 트리로 보고, 검색 팔레트에 `#`과 질문을 치면 에이전트의 `spec_search`와 같은 순위로 구획을 찾습니다.

### 턴 단위 리뷰와 PR 흐름

실행이 무언가를 바꾸면 채팅 라운드 끝에 `3 files changed · +27 −4` 같은 요약과 Review turn 버튼이 붙습니다. 0.2.0 릴리스 글에 따르면 이 숫자는 에이전트의 도구 호출이 아니라 **호스트가 실행 시작과 종료 시점에 워크트리를 스냅샷으로 비교한 결과**라서 셸 명령이 바꾼 파일도 잡힙니다. 파일과 diff의 특정 줄에 코멘트를 모아 구조화된 맥락으로 채팅에 보낼 수 있고, 상단 바에서는 브랜치의 원격 상태와 PR 상태를 보며 Publish, Push, PR 열기, CI 확인, 병합까지 진행합니다. GitHub 연동은 사용자의 `gh` CLI를 거치므로 `gh`가 설치되고 로그인되어 있어야 합니다.

### 채팅, 계획, 서브에이전트

워크스페이스마다 모델이 다른 채팅을 여러 개 동시에 열 수 있고, 실행 중에 방향을 바꾸는 메시지나 후속 메시지를 대기열에 넣을 수 있습니다. 에이전트와 공유하는 TODO 계획은 에이전트가 갱신하고 사용자가 편집하며, 완료된 단계를 독립 리뷰어가 검토하게 할 수 있습니다. pi 본체에는 없는 서브에이전트와 백그라운드 명령도 ThinkRail이 묶어 넣는 확장으로 제공됩니다.

### 스킬, MCP, 확장

pi 스킬과 프로젝트 안의 스킬을 읽고, Claude·Codex 등 다른 에이전트용 스킬도 설정에서 켜면 가져옵니다. MCP 서버는 pi의 `mcp.json`이나 Settings → MCP servers에서 연결합니다. 서버가 읽기 전용으로 표시하지 않은 호출은 실행 전에 채팅에서 묻고(Deny, Allow once, Allow in this chat, Always allow), **저장소가 정의한 MCP 서버는 사용자가 승인하기 전까지 꺼져 있습니다.** “Always allow” 허용 기록은 저장소의 `.pi/mcp.json`이 아니라 프로젝트 레코드에 저장되어, 저장소가 스스로를 미리 승인한 채 배포할 수 없게 했다고 0.2.0 릴리스 글은 설명합니다.

### 그 밖의 기능

- 에이전트가 추측하는 대신 객관식 질문을 던지는 `ask_user_question`, Mermaid 다이어그램과 전후 비교 목업을 보여 주는 `visualize`
- 채팅·워크스페이스·파일·스펙·설정을 찾는 `⌘K` 팔레트, 파일 내용 검색(`⌘⇧F`)
- 저장소 없이 쓰는 채팅(채팅마다 임시 폴더), 필요해지면 “Continue in workspace”로 인계
- 로컬 음성 받아쓰기(v0.4.0 릴리스 노트 기준 NVIDIA Nemotron 음성 인식 모델을 사용자가 내려받아 호스트에서 실행)
- UI 언어: 영어, 일본어, 폴란드어, 러시아어, 중국어 간체, 스페인어, 중국어 번체(대만). **한국어는 기본 제공되지 않습니다.**

## 설치와 시작

README와 공식 랜딩 페이지에 있는 방법만 옮깁니다. **이 글을 쓰면서 데스크톱 앱과 CLI를 설치하거나 실행해 보지는 않았습니다.**

**데스크톱 앱:** [릴리스 페이지](https://github.com/JetBrains/thinkrail/releases)에서 플랫폼에 맞는 `thinkrail-desktop-*` 파일을 받습니다.

- macOS 14 이상(Apple Silicon, Intel): `thinkrail-desktop-darwin-arm64.dmg` 또는 `thinkrail-desktop-darwin-x64.dmg`
- Windows x64: 설치 ZIP 전체를 풀고 실행 파일 실행
- Linux x64, ARM64: tarball을 풀고 `installer` 실행. glibc 2.38 이상과 GTK 3, WebKitGTK 4.1 등이 필요하며 README는 Ubuntu 24.04 이상을 기준으로 안내합니다.

**명령줄(브라우저 UI):** 설치 스크립트가 플랫폼에 맞는 단일 실행 파일을 받아 SHA-256 체크섬을 검증하고 PATH에 올립니다. 스크립트 주석에 따르면 기본 설치 위치는 `~/.local/bin/thinkrail`입니다.

```bash
# macOS / Linux (Windows의 Git Bash 포함)
curl -fsSL https://raw.githubusercontent.com/JetBrains/thinkrail/main/install.sh | bash
```

```powershell
# Windows (cmd, PowerShell 공통)
powershell -c "irm https://raw.githubusercontent.com/JetBrains/thinkrail/main/install.ps1 | iex"
```

설치 후에는 `thinkrail`을 실행하고, 필요하면 프로젝트로 열 git 저장소를 인수로 줍니다.

```bash
thinkrail ~/code/my-repo
```

`thinkrail`은 PATH의 `git`과 모델 제공자를 요구합니다. 첫 실행 마법사가 제공자 연결과 프로젝트 선택을 안내하고, 0.3.0 릴리스 글에 따르면 이 마법사 안에 개인정보(추가 사용 데이터 공유) 질문도 들어 있습니다. 서명 상태는 플랫폼마다 다릅니다. README는 Windows 실행 파일은 JetBrains가 서명하고, **macOS CLI는 서명되었지만 아직 공증(notarize)되지 않았으며, Linux 산출물은 서명되지 않는다**고 밝힙니다.

## 실전 예제

아래 예제는 README, 공식 블로그, 저장소 안의 스펙과 스킬 문서를 바탕으로 정리했습니다. **ThinkRail을 이 글을 쓰는 환경에 설치하지 않았으므로 어느 예제도 직접 실행해 확인하지 못했습니다.** 명령 옵션은 저장소의 `apps/cli/src/args.ts`에 있는 도움말 원문과 `install.sh`를 읽어 대조했습니다.

### 예제 1. 특정 버전 고정 설치와 실행 옵션

팀에서 같은 버전을 쓰거나 야간 빌드를 시험할 때 쓰는 형태입니다. README의 명령 그대로입니다.

```bash
# 안정 채널의 특정 버전
curl -fsSL https://raw.githubusercontent.com/JetBrains/thinkrail/main/install.sh | bash -s -- --channel stable --version 0.3.1

# 야간 채널
curl -fsSL https://raw.githubusercontent.com/JetBrains/thinkrail/main/install.sh | bash -s -- --channel nightly
```

실행 옵션은 CLI 도움말(`thinkrail --help`) 원문 기준으로 다음과 같습니다.

```bash
thinkrail --port 24242 ~/code/my-repo   # 기본 포트 24242, 사용 중이면 빈 포트로 넘어감
thinkrail --no-open                      # 브라우저를 열지 않음
thinkrail --no-analytics                 # 이번 실행에서 추가 사용 분석만 끔
thinkrail update                         # 채널의 최신 빌드로 갱신
thinkrail uninstall                      # 실행 파일과 PATH 항목 제거 (~/.thinkrail 상태는 기본 유지)
```

**주의:** `--host`의 기본값은 `localhost`입니다. 아키텍처 문서는 “인증은 외부에 둔다”고 하며 앱 자체에는 로그인 화면이 없고 Tailscale의 접근 제어를 전제로 삼습니다. 따라서 `--host`로 다른 주소에 바인딩한다면 네트워크 수준에서 접근을 막아야 한다고 읽는 것이 안전합니다.

### 예제 2. 기존 저장소에 스펙 그래프 도입하기

스펙이 없는 저장소를 열었을 때의 흐름입니다. Welcome 화면의 “Set up project” 카드는 pi의 스킬 명령 `/skill:setting-up-a-project`를 채팅에 넣어 줍니다. 이 스킬은 저장소 상태를 보고 갈래를 정합니다.

| 상황 | 이어지는 스킬 |
|---|---|
| 스펙 없음, 빈 저장소 | `starting-a-new-project`: 사용자를 인터뷰해 `goal-and-requirements.md` 작성 |
| 스펙 없음, 실제 코드 있음 | `importing-a-codebase`: 코드와 에이전트 파일을 분석해 첫 스펙 그래프 초안 작성, 코드로 알 수 없는 의도만 질문 |
| 스펙 이미 있음 | 다시 만들지 않고 검토·확장만 제안 |

결과물은 평범한 마크다운입니다. 아래는 ThinkRail 저장소의 `packages/spec-graph/SPEC.md` 머리말 원문입니다.

```yaml
---
id: module-spec-graph
type: module-design
status: active
title: Spec-Graph pi extension
parent: architecture
depends-on: []
tags: [spec-graph, pi-extension]
---
```

`id`, `type`, `title`이 필수이고, `status`는 `draft`, `active`, `stale`, `done`, `deprecated` 가운데 하나입니다. 구조를 바꾼 뒤에는 에이전트가 `spec_validate`로 끊어진 링크와 중복 id를 점검하도록 스킬이 지시합니다. ThinkRail 저장소 자체가 이 방식으로 개발되며, 얕게 복제해 세어 보니 `SPEC.md` 파일이 122개였습니다(2026-11-18 커밋 기준).

### 예제 3. ThinkRail 없이 AGENTS.md만으로 스펙 주도 규칙 걸기

공식 블로그의 스펙 주도 개발 글은 ThinkRail을 쓰지 않더라도 `AGENTS.md`에 한 구획을 추가하는 것으로 시작할 수 있다고 하며 다음 문안을 예로 듭니다(원문 영어, `(...)`는 필자가 생략한 부분, 줄바꿈은 필자가 조정).

```markdown
This project is **spec-driven**: the specs are maintained alongside the code and are
the source of truth; (...) Specs are never generated from code.

**Read the specs before the code.** Start at `goal-and-requirements.md` (the goal and
scope) and `architecture.md` (topology, boundaries, invariants), then the nearest
`SPEC.md`.

- A `SPEC.md` sits **beside the code it describes** and covers one genuine module. (...)
- If the work in the project results in a code change that is against what is described
  in `SPEC.md`, confirm it should be done, and if yes, make both the code change and
  update `SPEC.md`. Never diverge silently.
```

이 방식은 AGENTS.md를 읽는 코딩 에이전트라면 어디서든 시도할 수 있습니다. 다만 `spec_*` 도구는 `pi-spec-graph` 확장이, Specs 트리와 `#` 검색은 ThinkRail이 제공하는 기능이라 문안만으로는 따라오지 않습니다.

### 예제 4. 워크스페이스 두 개로 병렬 작업하고 PR까지

공식 블로그의 Workspaces 글과 0.2.0, 0.3.0 릴리스 글의 절차를 이은 흐름입니다.

1. 프로젝트에서 **Start building**을 눌러 기준 브랜치를 고르고 작업 설명을 적습니다. 이 설명이 워크스페이스 이름이자 에이전트의 첫 프롬프트가 됩니다.
2. 같은 브랜치에서 워크스페이스를 하나 더 만들어 다른 작업을 맡깁니다. 블로그의 예는 “한 에이전트는 동작을 바꾸지 않는 변경을 구현하고, 다른 에이전트는 프로젝트 스펙을 갱신한다”입니다.
3. `⌘K`(또는 Shift 두 번)로 팔레트를 열면 입력을 기다리는 채팅이 먼저 나옵니다.
4. 실행이 끝나면 **Review turn**으로 그 턴의 변경 전체를 한 화면에서 읽고, 브랜치 diff에서는 변경 덩어리(hunk)마다 Keep, Revert, Ask agent about this hunk를 고릅니다.
5. 상단 바의 Remote와 Pull request 구획에서 Publish → Open PR → 체크 확인 → Merge PR 순으로 진행합니다. PR 설명은 계획, 커밋, 저장소의 PR 템플릿, 에이전트 초안 가운데 고를 수 있습니다.

**주의:** 0.3.0 릴리스 글은 아직 안 되는 것으로 로컬 병합과 GitLab에서의 리뷰 동작을 꼽습니다. GitLab은 MR 생성 페이지를 미리 채워 여는 수준입니다.

### 예제 5. 사내 게이트웨이나 로컬 모델 연결하기, 그리고 순수 pi에서 같은 도구 쓰기

Settings → Providers → Custom servers에서 OpenAI 호환 서버를 연결합니다. README가 드는 예는 LiteLLM, sglang, vLLM, Ollama, LM Studio, llama.cpp입니다. **Find models** 버튼이 서버의 모델과 기능을 나열하고, 서버 정보는 pi의 `models.json`에 저장되어 pi CLI에서도 같은 모델이 보입니다. 0.3.1 릴리스 글은 한계로 OpenAI chat-completions API만 지원하고 모델별 세부 조정 UI가 없다는 점을 듭니다.

반대 방향도 가능합니다. ThinkRail의 질문 도구와 시각화 도구는 일반 pi 패키지로 npm에 배포되어 있어, 터미널의 pi에 그대로 설치할 수 있습니다(README 명령).

```bash
pi install npm:@thinkrail/pi-ask-user-question   # 객관식 질문 도구
pi install npm:@thinkrail/pi-visualize           # 다이어그램, 미리보기
```

README는 `@thinkrail/pi-next-steps`도 함께 안내하지만, 2026-11-20에 npm 레지스트리를 조회했을 때 이 패키지는 아직 없었습니다(404). 저장소에는 첫 릴리스를 준비하는 변경 기록 파일이 있습니다.

## 실무 팁 & 자주 겪는 문제

- **텔레메트리의 범위를 정확히 알고 씁니다.** `--no-analytics`와 Settings → Privacy의 스위치는 “추가” 데이터만 끕니다. 저장소의 분석 스펙(`packages/server/src/analytics/SPEC.md`)에 따르면 기본 이벤트와 오류 보고는 프로젝트 키가 찍힌 배포 빌드에서 항상 켜져 있고, 첫 실행 대화상자의 추가 공유 스위치는 켜진 상태가 기본입니다. 같은 스펙은 전송 대상을 PostHog EU 엔드포인트로, 오류 보고를 메시지 본문 없이 분류 정보와 ThinkRail 자체 코드의 스택 프레임만 보내는 허용 목록 방식으로 설명합니다. 소스에서 직접 빌드한 실행 파일은 키가 없어 전송하지 않는다고 합니다.
- **신뢰하지 않는 저장소는 신뢰 부여 전에 살펴봅니다.** 신뢰하지 않은 프로젝트는 자체 `.pi` 설정, 확장, 스킬, 프롬프트, `SYSTEM.md`를 불러오지 않습니다. 다만 이것은 저장소가 에이전트에 주입하는 자원에 대한 통제이지, 에이전트가 실행하는 셸 명령에 대한 통제는 아닙니다.
- **프로젝트 폴더(Default)에서 직접 작업할 때는 저장하지 않은 변경에 주의합니다.** 공식 블로그는 이 방식이 “안전하지 않을 수 있다”며 저장하지 않은 변경을 에이전트가 지울 수 있다고 경고합니다.
- **pi 버전 차이를 염두에 둡니다.** ThinkRail은 자체 pi를 라이브러리로 내장하고(복제 시점 기준 1.5.2), 따로 설치한 pi와 `~/.pi` 폴더를 공유합니다. 공식 블로그는 내장 pi와 사용자의 pi 버전이 달라 스킬이나 확장이 제대로 동작하지 않을 수 있고, pi의 터미널 화면을 바꾸는 확장(테마 등)은 ThinkRail에서 동작하지 않는다고 안내합니다.
- **한국어 UI가 필요하면 직접 추가합니다.** Settings → Language에서 `en.json`을 받아 번역한 뒤 `~/.thinkrail/locales/ko.json`으로 저장하면 됩니다(README는 `de.json`을 예로 듭니다). 번역하지 않은 문자열은 영어로 남고, 에이전트의 답변과 도구 출력은 번역 대상이 아닙니다.
- **Homebrew 설치는 README에 없습니다.** 유지보수자는 이슈 #488 댓글에서 커뮤니티 기여자가 Homebrew 코어 cask 저장소에 데스크톱 앱을 올려 `brew install --cask thinkrail`로 설치할 수 있다고 밝혔고, formulae.brew.sh에서도 `thinkrail` cask(0.4.0, 2026-11-20 기준)가 조회됩니다. 다만 공식 탭이나 CLI용 formula는 없으며, 필자는 이 경로를 시험하지 않았습니다.
- **이슈 트래커에서 눈에 띄는 요청**(2026-11-20 기준 열린 이슈): 워크스페이스별 OS 수준 샌드박스(#918), 컨테이너 배포(#856), SSH 원격 워크스페이스(#1078), 편집기의 LSP(언어 서버) 연동 부재(#907), 기능별 공식 문서(#224). 도입 전에 자신에게 필요한 항목이 여기에 걸려 있는지 확인하는 편이 좋습니다.

## 비슷한 도구와 비교

| 항목 | ThinkRail | Orca | pi CLI 단독 |
|---|---|---|---|
| 정체 | pi를 내장한 에이전트 IDE | 여러 CLI 에이전트를 운영하는 데스크톱 작업 공간 | 터미널용 최소 에이전트 하네스 |
| 라이선스 | Apache-2.0 | MIT | MIT |
| 에이전트 | pi 하나(프로세스 내장) | Claude Code, Codex 등 이미 쓰는 CLI를 터미널에서 띄움 | pi 자신 |
| 격리 단위 | git 워크트리(샌드박스 아님) | git 워크트리(샌드박스 아님) | pi.dev에 언급 없음 |
| 권한 확인 | 셸·파일 도구는 묻지 않음, MCP 호출과 저장소 자원은 승인 절차 | 기본값이 각 에이전트의 확인 우회 플래그, Manual 전환 가능 | 권한 팝업 없음(컨테이너 실행이나 확장으로 구현하라고 안내) |
| 프로젝트 지식 | `SPEC.md` 그래프 + `spec_*` 도구 | 전용 계층은 확인하지 못함(띄운 에이전트 각자의 방식) | AGENTS.md, SYSTEM.md, 스킬 |
| 리뷰 | 턴 단위 리뷰, 줄 코멘트, 상단 바 PR 흐름 | 줄 코멘트를 묶어 에이전트에 전송 | 직접 |
| 데스크톱 셸 | Electrobun(시스템 웹뷰) 또는 브라우저 | Electron | 터미널 |
| 텔레메트리 | 기본 이벤트·오류 보고 상시, 추가분만 끌 수 있음 | 기본 켜짐, 끌 수 있음 | 이 글에서 확인하지 않음 |

Orca 열은 블로그의 [Orca 소개 글](/opensource/2026/10/27/orca.html)(2026-10-27 기준)에서 정리한 내용을 바탕으로 했고, pi 열은 pi.dev 첫 페이지(2026-11-20 조회)의 설명을 바탕으로 했습니다. ThinkRail 열의 “셸·파일 도구는 묻지 않음”은 협업자가 작성한 이슈 #918의 서술에 근거합니다.

## 장점과 한계

### 장점

- **엔진을 새로 만들지 않았습니다.** pi의 모델 인증, 스킬, 확장, 세션 기록을 그대로 쓰므로 pi CLI와 ThinkRail을 오가도 작업이 이어집니다. 사용자 정의 모델 서버도 pi의 `models.json`에 저장되어 양쪽에서 보입니다.
- **스펙 그래프가 파일일 뿐입니다.** 머리말이 붙은 마크다운이라 ThinkRail을 지워도 문서는 저장소에 남고, 다른 에이전트도 읽을 수 있습니다. `pi-spec-graph`는 ThinkRail에 의존하지 않는 독립 pi 패키지로 설계되어 있습니다.
- **리뷰 근거가 에이전트의 자기 보고가 아닙니다.** 턴 요약이 워크트리 스냅샷 비교에서 나오므로 셸 명령이나 포매터가 바꾼 파일도 포함됩니다.
- **저장소발 주입에 대한 방어가 구체적입니다.** 저장소가 정의한 MCP 서버의 항목별 승인(내용이 바뀌면 승인 만료), 프로젝트 신뢰 부여 전 `.pi` 자원 차단 같은 장치가 스펙에 명문화되어 있습니다.
- **자체 계정이 없고 로컬 모델을 쓸 수 있습니다.** OpenAI 호환 서버를 연결하면 사내 게이트웨이나 로컬 모델로만 돌릴 수 있습니다.
- **설계 문서가 공개되어 있습니다.** 제품 목표, 아키텍처 결정, 모듈 경계, 심지어 분석 이벤트 목록까지 저장소 안의 스펙으로 읽을 수 있어 동작을 검증하기 쉽습니다.

### 한계

- **샌드박스가 없습니다.** 에이전트는 사용자 권한으로 셸과 파일을 다루며, 격리는 브랜치 수준입니다. 병렬·백그라운드 실행이 많아질수록 이 위험은 커집니다.
- **기본 텔레메트리를 끌 수 없습니다.** 내용이 최소화되어 있고 설계가 공개되어 있지만, 전송 자체를 금지하는 환경에서는 공식 빌드를 쓰기 어렵습니다.
- **에이전트가 pi 하나로 고정됩니다.** Claude Code나 Codex 같은 다른 에이전트를 엔진으로 쓸 수 없고(스킬만 가져옴), 이는 비목표로 명시되어 있습니다.
- **0.x 인큐베이터입니다.** 저장소가 생긴 지 넉 달 남짓이고, 최근 안정 릴리스는 며칠에서 열흘 남짓 간격(v0.2.0 10월 18일, v0.3.0 10월 29일, v0.4.0 11월 12일), 야간 빌드는 거의 매일 나옵니다. 내장 pi에 대한 패치와 우회가 `pi-compatibility.md`에 따로 관리될 만큼 상위 프로젝트 변화에 민감합니다.
- **문서가 README와 블로그뿐입니다.** 기능별 사용 설명서가 없어, 세부 동작은 저장소의 스펙 문서(영어, 개발자용)를 읽어야 합니다.
- **IDE로서는 가볍습니다.** Monaco 편집기는 있지만 언어 서버 연동은 열린 요청 상태이고, 원격 실행(SSH, 컨테이너)도 아직 요청 단계입니다.
- **크래시 격리가 없습니다.** pi를 같은 프로세스에서 돌리는 설계라 치명적 오류가 호스트 전체에 영향을 줄 수 있습니다.

## 인사이트

**기존 글과의 연결: Orca가 “에이전트 밖에서 감싸는” 도구라면 ThinkRail은 “에이전트를 안에 품는” 도구입니다.** [Orca 소개 글](/opensource/2026/10/27/orca.html)에서 본 Orca는 터미널에서 CLI 에이전트 프로세스를 띄우고 터미널 제목과 훅으로 상태를 추측합니다. 그래서 어떤 에이전트든 붙일 수 있지만, 에이전트 내부에서 무슨 일이 일어났는지는 간접적으로만 압니다. ThinkRail은 반대로 엔진을 pi 하나로 고정하고 라이브러리로 내장합니다. 그 대가로 얻는 것이 턴 단위 변경 영수증, 구조화된 질문 카드, 서브에이전트별 비용 합산, 도구 호출 단위의 MCP 승인처럼 엔진의 이벤트를 직접 받아야만 만들 수 있는 화면입니다. 두 도구 모두 워크트리를 격리 단위로 쓰고 둘 다 그것이 보안 경계가 아니라는 같은 약점을 가집니다. 필자의 판단으로는 “이미 쓰는 여러 에이전트를 나란히 굴리고 싶다”면 Orca, “에이전트 하나를 깊게 들여다보며 리뷰하고 싶다”면 ThinkRail 쪽이 맞습니다.

**기존 글과의 연결: 스펙 그래프는 AGENTS.md를 대체하지 않고, 그 아래층을 채웁니다.** [AGENTS.md 글](/tech/2026/10/24/agents-md.html)에서 정리했듯 AGENTS.md는 필수 필드가 없는 평범한 마크다운이고, 에이전트가 시작할 때 통째로 읽는 “저장소 사용법”입니다. 스펙 그래프는 세 가지가 다릅니다. 첫째, 머리말의 `id`와 `parent`, `depends-on`으로 문서끼리 연결되어 기계가 검증할 수 있습니다(`spec_validate`). 둘째, 시작할 때 전부 읽는 것이 아니라 필요한 구획만 도구로 찾아 읽습니다. 스킬 문서는 이를 “조회는 작업에 비례하게”라고 표현하며, 문서화된 결정을 건드리지 않는 국소 작업은 스펙을 읽지 않아도 된다고 합니다. 셋째, 유지 책임이 에이전트에게도 있습니다. 경계나 결정을 바꾸는 변경은 같은 변경 안에서 스펙을 고쳐야 한다는 규칙이 항상 켜져 있습니다. ThinkRail 저장소 자신도 AGENTS.md(약 150줄)가 “어떤 스펙을 언제 읽을지”를 안내하고 세부는 스펙에 두는 2층 구조를 씁니다. [Agent Skills 글](/tech/2026/10/24/agent-skills-aaif.html)의 점진적 공개와 같은 발상을 프로젝트 지식에 적용한 셈입니다.

**한계와 반론: “스펙이 진실의 원천”이라는 주장은 스펙이 낡지 않을 때만 성립합니다.** 공식 블로그 스스로 과거에 문서화가 밀려난 이유를 “갱신이 번거롭고, 갱신되지 않은 문서는 혼란과 버그를 만든다”고 적습니다. ThinkRail의 답은 그 갱신을 에이전트에게 맡기는 것인데, 그러면 스펙의 정확성은 에이전트가 규칙을 지키는지에 달립니다. 도구가 검증하는 것은 끊어진 링크, 중복 id, 순환 같은 구조뿐이고, 스펙의 내용이 코드와 일치하는지는 검증하지 않습니다. `status: stale`이라는 상태값이 있다는 사실 자체가 어긋남을 사람이 표시해야 함을 보여 줍니다. 스펙 주도 개발이 실제로 결함이나 재작업을 줄인다는 측정 결과도 필자가 읽은 ThinkRail 자료에서는 찾지 못했습니다. 122개의 스펙을 유지하는 ThinkRail 저장소는 인상적인 사례지만, 도구를 만든 팀이 자기 도구로 자기 저장소를 관리한 결과라는 점은 감안해야 합니다.

**실무에 주는 의미: 격리와 통제를 구분해서 도입 판단을 해야 합니다.** ThinkRail이 통제하는 것은 “저장소가 에이전트에 무엇을 주입할 수 있는가”(신뢰 부여, MCP 승인)이고, 통제하지 않는 것은 “에이전트가 내 컴퓨터에서 무엇을 할 수 있는가”입니다. pi는 권한 팝업을 일부러 넣지 않고 컨테이너에서 돌리거나 확장으로 확인 절차를 만들라고 안내하는데, ThinkRail은 그 pi를 사용자 데스크톱에서 직접 실행합니다. 협업자의 이슈 #918이 지적하듯 README, 이슈, 웹 페이지, MCP 결과에 섞인 프롬프트 주입이 `~/.ssh` 같은 자격 증명에 닿는 것을 막는 장치는 현재 없습니다. 외부 저장소나 신뢰할 수 없는 입력을 다룬다면 ThinkRail 자체를 가상 머신이나 별도 계정에서 돌리는 편이 안전해 보입니다. 텔레메트리도 같은 맥락입니다. 수집 내용은 보수적으로 설계되어 있지만, 전송을 완전히 끌 수 없다는 사실은 보안 심사가 있는 조직에서 먼저 확인해야 할 항목입니다.

**앞으로 지켜볼 점:** 첫째, 샌드박스 제안(#918)이 받아들여져 기본 경로로 들어오는지입니다. 들어온다면 위의 가장 큰 약점이 사라집니다. 둘째, 인큐베이터 딱지입니다. JetBrains가 이 프로젝트를 공식 지원 제품으로 올릴지, 실험으로 남길지에 따라 장기 도입 판단이 달라집니다. 셋째, pi 의존입니다. 엔진을 하나로 고정한 설계는 pi의 방향이 바뀌면 그대로 영향을 받습니다. README가 예고한 “완전한 확장 지원”이 어떤 형태로 나오는지도 함께 볼 만합니다.

<!-- EDITOR_NOTE: 운영자가 직접 써 본 경험이나 의견을 여기에 추가하세요. -->

## 이런 분께 추천

- pi를 이미 쓰고 있고, 터미널 밖에서 diff 리뷰와 PR 흐름까지 한 화면에서 처리하고 싶은 개발자
- 에이전트와의 결정 사항을 채팅 기록이 아니라 저장소 안의 문서로 남기는 방식(스펙 주도 개발)을 시험해 보려는 팀
- 사내 LLM 게이트웨이나 로컬 모델만으로 에이전트 IDE를 돌려야 하는 환경
- 에이전트 IDE의 내부 설계를 공부하고 싶은 분(스펙과 아키텍처 결정이 모두 공개되어 있습니다)

## 이런 경우엔 다른 도구

- Claude Code, Codex 등 이미 쓰는 CLI 에이전트를 그대로 병렬로 굴리고 싶다면 [Orca](/opensource/2026/10/27/orca.html) 같은 작업 공간 도구가 맞습니다.
- 에이전트를 서버에서 운영하고 스케줄·웹훅으로 자동화하려면 [OpenHands](/opensource/2026/10/20/openhands.html) 같은 셀프 호스팅 플랫폼을 봅니다.
- 외부로 나가는 사용 통계를 전부 차단해야 하는 환경이라면 공식 빌드는 맞지 않습니다. 소스에서 직접 빌드하는 방법이 있지만 지원 범위 밖의 선택입니다.
- 언어 서버 기반 자동 완성과 리팩터링이 중심인 일상 편집기가 필요하다면 기존 IDE를 그대로 쓰고, ThinkRail은 에이전트 작업용으로만 곁에 두는 편이 현실적입니다.
- 안정성과 공식 지원이 우선인 조직이라면 인큐베이터 등급이 바뀔 때까지 지켜보는 것이 좋습니다.

## 참고 링크

- [GitHub 저장소 / README](https://github.com/JetBrains/thinkrail) · [릴리스](https://github.com/JetBrains/thinkrail/releases) · [v0.4.0 릴리스 노트](https://github.com/JetBrains/thinkrail/releases/tag/v0.4.0) · [LICENSE](https://github.com/JetBrains/thinkrail/blob/main/LICENSE)
- [제품 스펙 goal-and-requirements.md](https://github.com/JetBrains/thinkrail/blob/main/goal-and-requirements.md) · [아키텍처 architecture.md](https://github.com/JetBrains/thinkrail/blob/main/architecture.md) · [저장소 AGENTS.md](https://github.com/JetBrains/thinkrail/blob/main/AGENTS.md)
- [스펙 그래프 확장 SPEC.md](https://github.com/JetBrains/thinkrail/blob/main/packages/spec-graph/SPEC.md) · [spec-graph 스킬](https://github.com/JetBrains/thinkrail/blob/main/packages/spec-graph/skills/spec-graph/SKILL.md) · [프로젝트 설정 스킬](https://github.com/JetBrains/thinkrail/blob/main/packages/pi-thinkrail-workflow/skills/setting-up-a-project/SKILL.md)
- [분석(텔레메트리) 스펙](https://github.com/JetBrains/thinkrail/blob/main/packages/server/src/analytics/SPEC.md) · [CLI 스펙](https://github.com/JetBrains/thinkrail/blob/main/apps/cli/SPEC.md) · [설치 스크립트 install.sh](https://github.com/JetBrains/thinkrail/blob/main/install.sh)
- 공식 블로그: [Introducing ThinkRail](https://thinkrail.ai/blog/introducing-thinkrail/) · [ThinkRail Workspaces](https://thinkrail.ai/blog/thinkrail-workspaces/) · [ThinkRail Spec-Driven Development](https://thinkrail.ai/blog/thinkrail-sdd/) · [An agentic IDE that follows Pi's philosophy](https://thinkrail.ai/blog/thinkrail-pi-skills-and-desktop-apps/)
- 릴리스 글: [0.2.0](https://thinkrail.ai/blog/thinkrail-0-2-0-review-the-turn/) · [0.3.0](https://thinkrail.ai/blog/thinkrail-0-3-0-whole-loop-one-window/) · [0.3.1](https://thinkrail.ai/blog/thinkrail-0-3-1-release/)
- 이슈: [#918 워크스페이스별 샌드박스 제안](https://github.com/JetBrains/thinkrail/issues/918) · [#488 Homebrew](https://github.com/JetBrains/thinkrail/issues/488) · [#224 Docs](https://github.com/JetBrains/thinkrail/issues/224)
- [JetBrains의 GitHub 프로젝트 등급 설명(incubator 정의)](https://github.com/JetBrains#jetbrains-on-github) · [pi 공식 사이트](https://pi.dev/) · [Homebrew cask: thinkrail](https://formulae.brew.sh/cask/thinkrail)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
