---
layout: default
title: "[오픈소스 소개] OpenHands: 코딩 에이전트를 직접 운영하는 셀프 호스팅 관제 센터"
date: 2026-10-20
categories: [opensource]
---

# [오픈소스 소개] OpenHands: 코딩 에이전트를 직접 운영하는 셀프 호스팅 관제 센터

- **저장소:** [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) · [openhands.dev](https://openhands.dev) · [문서](https://docs.openhands.dev)
- **라이선스:** MIT
- **언어:** TypeScript (에이전트 서버는 Python)
- **현황 (2026-10-20 기준):** GitHub 스타 약 9.1만 개, 최신 릴리스 v1.28.1 (10월 19일)

## 한 줄 요약

**여러 AI 코딩 에이전트를 내 인프라에서 실행하고, 대화와 자동화를 한곳에서 관리하는 셀프 호스팅 플랫폼**입니다. 핵심 앱인 **Agent Canvas**에서 OpenHands 자체 에이전트는 물론 Claude Code, Codex, Gemini CLI, Pi, OpenCode 같은 다른 에이전트도 같은 화면에서 쓸 수 있습니다. 프로젝트 상태는 아직 **베타**입니다.

## 어떤 문제를 푸나

코딩 에이전트를 실무에 쓰기 시작하면 금방 이런 고민이 생깁니다.

- **어디서 돌릴까:** 내 노트북에서 돌리면 노트북을 덮는 순간 작업이 멈춥니다. 에이전트가 내 파일 전체를 건드릴 수 있다는 것도 부담입니다.
- **어떤 에이전트를 쓸까:** 팀원마다 Claude Code, Codex, Gemini CLI를 따로 쓰고, 설정과 기록이 제각각 흩어집니다.
- **반복 작업을 어떻게 맡길까:** "매일 아침 PR 요약해서 Slack에 올리기", "새 이슈가 오면 작은 작업으로 쪼개기" 같은 일은 사람이 매번 프롬프트를 넣는 방식으로는 오래 못 갑니다.
- **팀에서 어떻게 공유할까:** 코드 리뷰, 의존성 업데이트 같은 공용 작업은 개인 PC가 아니라 항상 켜진 서버에서 돌아야 합니다.

OpenHands는 이 문제를 "**UI(Agent Canvas)와 실행 환경(백엔드)을 분리**하고, 여러 백엔드와 여러 에이전트를 한 화면에서 바꿔 가며 쓰는 구조"로 풉니다. 예전 OpenHands(구 OpenDevin)가 단일 에이전트 웹앱이었다면, 지금의 OpenHands는 에이전트 운영 관제 센터에 가깝습니다.

## 핵심 개념 / 동작 원리

### 구성 요소

OpenHands는 여러 저장소로 나뉜 시스템입니다.

| 구성 요소 | 저장소 | 역할 |
|---|---|---|
| Agent Canvas | OpenHands/OpenHands | 브라우저 UI, 백엔드 선택, 로컬 스택 실행 |
| Agent Server / SDK | OpenHands/software-agent-sdk | 에이전트, 도구, 대화, 워크스페이스, REST API |
| Automation Server | OpenHands/automation | 스케줄(cron), 웹훅, 실행 기록, 작업 디스패치 |
| TypeScript Client | OpenHands/typescript-client | 브라우저에서 Agent Server API 호출 |

역할 분담이 명확합니다. **Automation Server는 "언제" 실행할지**, **Agent Server는 "무엇을" 실행할지** 정합니다. Agent Canvas는 화면만 담당하고 **샌드박스나 격리 기능은 제공하지 않습니다.** 격리는 백엔드를 어디에 두느냐(Docker, VM 등)로 결정됩니다.

### 구조 그림

`agent-canvas` 명령 하나로 띄우는 로컬 스택은 대략 이렇게 생겼습니다.

```
 브라우저
    │ http://localhost:8000
    ▼
 Ingress (127.0.0.1:8000, 경로로 분기)
    ├─ /*                → 정적 프론트엔드
    ├─ /api/*, /sockets  → Agent Server
    └─ /api/automation/* → Automation Server
                              │ 스케줄·웹훅
                              ▼
                        Agent Server가
                        대화 실행
```

Agent Canvas 하나가 **여러 Agent Server(백엔드)**에 연결할 수 있습니다. 예를 들어 팀 공용 VM에서는 코드 리뷰 자동화를 돌리고, 내 노트북에서는 개인 작업용 에이전트를 돌리면서 화면 왼쪽 아래 백엔드 전환기로 오가는 식입니다.

### 꼭 알아야 할 용어

- **백엔드(Backend):** 대화, 도구, 설정, 시크릿, 자동화를 실제로 실행하는 Agent Server입니다. 에이전트가 어떤 머신과 파일에 접근하는지가 여기서 정해집니다.
- **워크스페이스(Workspace):** 에이전트가 읽고 쓰는 폴더, 저장소, 컨테이너 마운트, 클라우드 샌드박스입니다.
- **ACP(Agent Client Protocol):** 코딩 에이전트와 stdio 위의 JSON-RPC로 대화하는 표준입니다. Agent Server가 Claude Code 같은 외부 에이전트의 CLI를 하위 프로세스로 띄우고 대화를 중계합니다. 이때 LLM 호출과 도구 실행은 외부 에이전트가 직접 합니다.
- **LLM 프로필 / Provider Connection:** OpenHands 자체 에이전트가 쓸 모델 설정입니다. API 키를 한 번 등록하고 여러 모델 프로필에서 재사용할 수 있습니다.
- **에이전트 프로필(Agent Profile):** 에이전트 종류와 모델 조합을 저장해 둔 재사용 설정입니다. 자동화에도 지정할 수 있습니다.

## 주요 기능

### 실행 환경(백엔드) 선택

- **로컬(npm/npx):** 가장 빠르지만 에이전트가 내 사용자 권한으로 호스트 파일 시스템에 접근합니다.
- **Docker:** 마운트한 디렉터리만 보이는 컨테이너 안에서 실행합니다. 노트북에서 쓸 때 권장되는 방식입니다.
- **대화별 Docker 컨테이너:** UI와 바깥 Agent Server는 호스트에 두고, 대화마다 강화된(hardened) 컨테이너를 따로 띄웁니다.
- **VM / 전용 머신:** 항상 켜 두는 팀 서버나 Mac Mini 같은 장비에 올립니다.
- **Kubernetes(Helm), Modal, DigitalOcean Managed Agents, OpenHands Cloud** 백엔드도 공식 가이드가 있습니다.

### 에이전트와 모델

- 기본 에이전트는 OpenHands 범용 에이전트이고, ACP로 Claude Code, Codex, Gemini CLI, Pi, OpenCode를 붙일 수 있습니다. 그 밖의 stdio ACP 서버도 **Custom**으로 연결할 수 있습니다.
- 모델은 직접 발급한 API 키(Anthropic, OpenAI, Google 등), OpenHands LLM API 키, OpenRouter, LiteLLM 프록시, Ollama나 LM Studio, vLLM 같은 OpenAI 호환 로컬 서버를 쓸 수 있습니다.
- **Model Router:** 작업마다 적절한 LLM 프로필로 라우팅하는 기능입니다.
- ACP 에이전트는 이미 로그인한 구독(예: Claude Pro/Max)을 그대로 재사용할 수 있습니다.

### 자동화(Automations)

- **스케줄 기반:** cron 일정에 맞춰 전체 OpenHands 대화를 실행합니다.
- **이벤트 기반:** GitHub 이벤트나 커스텀 웹훅으로 실행합니다. JMESPath 필터로 조건을 좁힐 수 있습니다.
- **프롬프트형 / 플러그인형 / 스크립트 번들형:** 자연어 프롬프트로 만들거나, 플러그인을 붙이거나, 결정적인 로직은 스크립트로 두고 판단이 필요한 부분만 에이전트에 맡길 수 있습니다.
- **미리 만든 자동화:** Issue to PR, GitHub PR Review Assistant, GitHub Repository Monitor, Slack Channel Monitor가 제공됩니다.
- **관리 기능:** 실행 기록과 상태(`PENDING`, `RUNNING`, `COMPLETED`, `FAILED` 등), 실행별 LLM 비용(USD), CSV/JSON 내보내기, 자동화 JSON 내보내기·가져오기, Git 동기화를 지원합니다.

### 커스터마이즈

- 저장소별 지침은 `AGENTS.md`, 재사용 지침은 Skills, 외부 도구는 MCP 서버, 패키지된 기능은 Plugins로 붙입니다.
- 대화 분기(branch), 내장 터미널과 브라우저, 파일 보기, 내장 OpenVSCode 편집기를 제공합니다.
- macOS, Windows, Linux용 **데스크톱 앱 프리뷰** 빌드도 있습니다. Node.js와 `uv`를 함께 묶어 배포해서 따로 설치할 필요가 없습니다.

## 설치와 시작

### 사전 준비

- npm/npx 방식: **Node.js 24 이상**, `npm`, **`uv`**(로컬 Agent Server 실행에 사용)
- Docker 방식: Docker Desktop(macOS/Windows) 또는 Docker Engine(Linux)
- 모델 접근 경로 하나: 제공자 API 키, OpenHands LLM 키, ACP 구독 로그인, 로컬 모델 서버 중 하나
- 에이전트가 작업할 폴더

```bash
node --version
npm --version
uv --version
```

### 방법 1: npm / npx (샌드박스 없음)

```bash
# 한 번만 써 보기
npx @openhands/agent-canvas

# 또는 전역 설치
npm install -g @openhands/agent-canvas
agent-canvas
```

브라우저에서 `http://localhost:8000`이 열립니다. 이 방식은 **에이전트가 내 파일 시스템 전체에 접근할 수 있으니** 신뢰하는 환경에서만 쓰세요. 로컬 리스너는 기본적으로 `127.0.0.1`에만 바인딩됩니다.

자주 쓰는 실행 옵션은 다음과 같습니다.

| 옵션 | 설명 |
|---|---|
| `-p`, `--port <port>` | ingress 포트 변경(기본 8000) |
| `--backend-only` | 백엔드만 실행(서버용) |
| `--frontend-only` | 프론트엔드만 실행(원격 백엔드 접속용) |
| `--public` | 공개 모드. `LOCAL_BACKEND_API_KEY` 필수 |
| `--info` | 버전과 스택 구성 출력 |

설정과 대화 기록은 `~/.openhands`에 저장됩니다. 업데이트는 `npm install -g @openhands/agent-canvas@latest`입니다.

### 방법 2: Docker 샌드박스 (권장)

공식 문서는 설정 저장용으로 **named volume**을 쓰는 방식을 안내합니다.

```bash
mkdir -p ~/projects

docker run -it --rm \
  -p 127.0.0.1:8000:8000 \
  -v openhands-data:/home/openhands/.openhands \
  -v ~/projects:/projects \
  ghcr.io/openhands/agent-canvas:latest
```

- Docker 이미지는 `http://localhost:8000/canvas`에서 열립니다.
- 에이전트는 마운트한 `/projects` 아래만 볼 수 있습니다.
- `127.0.0.1:` 접두사 덕분에 같은 네트워크의 다른 기기는 접근할 수 없습니다.
- `openhands-data` 볼륨은 `--rm`으로 컨테이너를 지워도 남습니다.

README의 빠른 시작은 `-v "$HOME/.openhands:/home/openhands/.openhands"` 바인드 마운트와 `-e AGENT_CANVAS_ALLOW_LAN_SESSION_KEY=true`를 함께 쓰는 예시를 보여 줍니다. 이 환경 변수는 세션 키를 HTML에 자동 주입해서 키 입력 없이 바로 쓰게 해 주는데, **포트를 127.0.0.1에만 열 때만** 쓰라고 안내합니다. 또 Linux에서 `~/.openhands`를 바인드 마운트하면 컨테이너 사용자(UID 10001)와 호스트 사용자(보통 UID 1000)가 달라 `unable to open database file` 오류가 날 수 있습니다. named volume을 쓰면 이 문제를 피할 수 있습니다.

### 방법 3: 소스에서 실행 (기여자용)

```bash
git clone https://github.com/OpenHands/OpenHands.git
cd OpenHands
npm install
npm run dev
```

### 첫 실행 마법사

처음 접속하면 4단계 설정 화면이 나옵니다.

1. **에이전트 선택:** OpenHands(기본), Claude Code, Codex, Gemini CLI, Pi, OpenCode
2. **백엔드 확인:** 기본은 로컬 `http://127.0.0.1:8000`
3. **LLM 설정:** 제공자와 모델 선택 후 API 키 입력
4. **미리 만든 워크플로로 시작:** 예: GitHub PR Review Copilot

작업할 폴더가 있다면 대화를 시작하기 전에 **Open Workspace**로 먼저 지정하세요.

## 실전 예제

### 예제 1: 대화마다 별도 Docker 컨테이너로 격리하기

여러 에이전트를 동시에 돌리거나, UI는 호스트에 두되 에이전트 실행만 격리하고 싶을 때 쓰는 방식입니다.

```bash
export OH_CONVERSATION_RUNTIME=docker
export OH_CONVERSATION_IMAGE=ghcr.io/openhands/agent-server:latest-python
agent-canvas
```

이렇게 띄우면 대화마다 바깥 Agent Server가 전용 컨테이너를 만들고, 그 안에서 또 하나의 Agent Server가 에이전트 루프와 도구를 실행합니다. 문서에 적힌 컨테이너 보안 설정은 다음과 같습니다.

- root가 아닌 호스트 사용자의 UID/GID로 실행
- 모든 Linux capability 제거(`--cap-drop ALL`), `no-new-privileges` 설정
- API는 `127.0.0.1`에만 공개하고, 대화별 세션 키로 인증
- 메모리, CPU, PID 개수 제한

자원 한도는 환경 변수로 조정합니다.

| 변수 | 기본값 | 의미 |
|---|---|---|
| `OH_CONVERSATION_CONTAINER_MEMORY` | `4g` | 컨테이너별 메모리 |
| `OH_CONVERSATION_CONTAINER_CPUS` | `2.0` | 컨테이너별 CPU |
| `OH_CONVERSATION_CONTAINER_PIDS_LIMIT` | `512` | 프로세스 수 제한 |
| `OH_CONVERSATION_CONTAINER_STARTUP_TIMEOUT` | `120` | 기동 대기(초) |
| `OH_CONVERSATION_IDLE_TTL_SECONDS` | `1200` | 유휴 시 정지(20분) |

격리가 제대로 되었는지 확인하려면, 대화에서 에이전트에게 `id`와 `printf 'PWD=%s\nHOME=%s\n' "$PWD" "$HOME"`을 실행하게 합니다. `PWD`는 `/workspace`, `HOME`은 `/var/openhands/.openhands`가 나와야 합니다. 호스트에서는 이렇게 확인합니다.

{% raw %}
```bash
docker ps --filter name=agent-server-conversation-
docker inspect <container-id> --format '{{json .Mounts}}'
docker inspect <container-id> \
  --format '{{.HostConfig.CapDrop}} {{.HostConfig.SecurityOpt}}'
```
{% endraw %}

주의할 점도 있습니다.

- `/workspace`는 호스트 디렉터리를 **읽기·쓰기로 바인드 마운트**합니다. 같은 워크스페이스를 쓰는 대화끼리는 파일을 공유하니, 동시에 작업시킬 때는 디렉터리나 git worktree를 나누세요.
- 기본적으로 에이전트는 컨테이너 안에서 Docker를 못 씁니다. `--privileged`로 열 수는 있지만 격리가 크게 약해집니다. 문서는 "더 안전한 중간 지점은 없다"고 명시합니다.

### 예제 2: 모델 설정하기 (API 키, 로컬 모델, SDK)

**직접 API 키 사용**

`Settings > LLM`의 `Basic` 탭에서 제공자와 모델을 고르고 키를 넣습니다. 같은 키를 여러 모델에 쓸 거라면 **Provider Connection**을 먼저 만들고 각 프로필에서 선택하면, 키 교체도 한 번에 끝납니다.

**Ollama, LM Studio 같은 로컬 모델**

`Advanced` 탭에서 설정합니다.

1. 서버의 `GET /v1/models`로 정확한 모델 ID를 확인합니다.
2. 모델 칸에 `openai/<모델 ID>`를 입력합니다.
3. Base URL을 입력합니다. **백엔드 기준으로** 접근 가능한 주소여야 합니다.

```bash
# 예: 호스트에서 Ollama의 OpenAI 호환 API 확인
curl http://localhost:11434/v1/models
```

Agent Canvas를 Docker로 돌리고 모델 서버는 호스트에 있다면 `127.0.0.1`은 컨테이너 자신을 가리킵니다. 이때는 `http://host.docker.internal:<포트>/v1`처럼 호스트 주소를 써야 합니다. LiteLLM 프록시는 모델 칸에 `litellm_proxy/<모델 이름>`을 넣습니다.

> 로컬 모델은 컨텍스트 길이와 도구 호출(tool use) 지원이 부족하면 에이전트 작업을 끝까지 해내지 못할 수 있습니다. 문서의 문제 해결 표도 이 경우 "더 성능 좋은 모델을 쓰라"고 안내합니다.

**SDK로 직접 에이전트 만들기**

UI 없이 Python 코드로 에이전트를 만들고 싶다면 `software-agent-sdk`를 씁니다. `openhands-sdk`와 `openhands-tools`는 같은 버전으로 함께 설치해야 합니다.

```bash
pip install -U openhands-sdk openhands-tools
```

```python
import os

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool

llm = LLM(
    model=os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", None),
)

agent = Agent(
    llm=llm,
    tools=[
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
    ],
)

conversation = Conversation(agent=agent, workspace=os.getcwd())
conversation.send_message("Write 3 facts about the current project into FACTS.txt.")
conversation.run()
```

모델 이름은 LiteLLM 규칙(`제공자/모델명`)을 따릅니다. 공식 예제를 그대로 옮긴 코드이며, 이 코드는 현재 디렉터리에서 실제로 셸 명령을 실행하니 테스트용 폴더에서 돌리세요.

### 예제 3: Claude Code를 ACP 에이전트로 연결하기

이미 Claude Code를 쓰고 있다면, 그 구독을 Agent Canvas에서 그대로 쓸 수 있습니다.

**설정 위치:** `Settings > Agent`

- **Agent:** `ACP` 선택
- **Preset:** `Claude Code`
- **Command:** 기본값 `npx -y @agentclientprotocol/claude-agent-acp`
- **Credentials:** 아래 설명 참고
- **Model:** `Agent default` 또는 목록에서 선택

다른 에이전트의 기본 명령은 이렇습니다.

| 에이전트 | 기본 실행 명령 |
|---|---|
| Codex | `npx -y @agentclientprotocol/codex-acp` |
| Gemini CLI | `npx -y @google/gemini-cli --acp` |
| OpenCode | `npx -y opencode-ai acp` |

**인증은 백엔드 위치에 따라 달라집니다.**

- **로컬 백엔드(내 PC에서 npm으로 실행):** Claude Code에 로그인되어 있으면 macOS 키체인이나 Linux의 `~/.claude/.credentials.json`에서 자동으로 찾아 씁니다. API 키를 따로 넣을 필요가 없습니다. 로그인과 API 키가 둘 다 있으면 **로그인이 우선**합니다.
- **Docker, VM, 클라우드 백엔드:** 깨끗한 컨테이너에는 내 로그인 정보가 없습니다. `ANTHROPIC_API_KEY`나 `CLAUDE_CODE_OAUTH_TOKEN`(Pro/Max OAuth 토큰)을 넣어야 합니다. Claude Code의 `claude setup-token` 명령으로 이런 장기 토큰을 발급할 수 있는 것으로 알려져 있지만, 정확한 절차는 Claude Code 문서에서 확인하세요.

입력한 자격 증명은 환경 변수 이름 그대로 **전역 시크릿**으로 저장되고(`Settings > Secrets`), Agent Server가 ACP 하위 프로세스에 환경 변수로 넘깁니다.

> **주의:** Claude OAuth 토큰을 쓸 때 `ANTHROPIC_BASE_URL`을 함께 설정하지 마세요. 공식 문서는 LiteLLM 등의 base URL이 섞이면 토큰 인증이 조용히 깨진다고 경고합니다.

설정을 바꿔도 이미 실행 중인 대화는 처음 시작한 에이전트를 계속 씁니다. 새 설정은 이후 시작하는 대화부터 적용됩니다.

### 예제 4: 자동화 만들기 (스케줄, PR 리뷰, 웹훅)

**스케줄 자동화는 대화로 만듭니다.** 새 대화에서 이렇게 요청하면, Automation Skill이 이름, 일정, 시간대, 작업 내용을 차례로 확인합니다.

```
Create an automation called "Daily GitHub Summary" that runs every
weekday at 9 AM Eastern.

It should:
1. Summarize PRs opened, merged, and reviewed in the last 24 hours
2. List any PRs that have been open for more than 3 days
3. Format as a clean markdown summary
4. Post to the #engineering Slack channel
```

Slack에 올리려면 Slack MCP 연동과 필요한 토큰(시크릿)이 **같은 백엔드**에 설정되어 있어야 합니다. 자동화는 실행할 때마다 새 샌드박스에서 전체 대화를 돌리고, 결과 대화는 대화 목록에 남아서 나중에 이어서 작업할 수도 있습니다.

**만든 자동화는 JSON으로 내보내 버전 관리할 수 있습니다.** `Automate` 화면의 메뉴에서 `Export`를 고르면 `<slug>.automation.json`이 내려받아집니다.

```json
{
  "version": 1,
  "kind": "automation",
  "spec": {
    "name": "Daily GitHub Summary",
    "trigger": {
      "type": "schedule",
      "schedule": "0 9 * * 1-5",
      "schedule_human": "Weekdays at 9:00 AM",
      "timezone": "America/New_York"
    },
    "enabled": true,
    "prompt": "Summarize the previous day's PRs and post to #engineering.",
    "repository": "openhands/docs",
    "model": "anthropic/claude-sonnet-4-5"
  }
}
```

가져온(import) 자동화는 **비활성 상태로 생성**되니, 내용을 검토한 뒤 켜면 됩니다.

**GitHub PR 리뷰 자동화 (로컬 백엔드)**

1. GitHub에서 fine-grained 개인 토큰을 만듭니다. 권장 권한은 `Contents`, `Issues`, `Pull requests` 읽기·쓰기, `Metadata` 읽기, 필요하면 `Actions`, `Checks` 읽기입니다. 저장소는 `Only select repositories`로 좁히는 것이 안전합니다.
2. `Customize > MCP Servers`에서 GitHub를 고르고 토큰을 붙여 넣습니다(시크릿 자동 생성 토글 켜기).
3. `Automate > Start from a proven workflow`에서 GitHub PR review를 고르면 미리 채워진 프롬프트로 설정 대화가 시작되고, 에이전트가 저장소, 리뷰 대상, 코멘트 방식 등을 물어보며 자동화를 만듭니다.

이 흐름은 GitHub MCP로 새 PR을 폴링하는 방식이라 클라우드 인프라 없이 로컬에서 돌아갑니다.

**이벤트 기반 자동화와 필터**

GitHub 이벤트(`pull_request.labeled`, `issue_comment.created` 등)나 커스텀 웹훅(Linear, Stripe, Slack 등)으로 실행할 수 있고, 조건은 JMESPath 필터로 지정합니다.

```
contains(pull_request.labels[].name, 'openhands')
icontains(comment.body, '@openhands')
glob(repository.full_name, 'myorg/*') && ref == 'refs/heads/main'
```

`icontains`, `glob`, `!`, `&&`, `||`는 OpenHands가 표준 JMESPath에 추가한 확장입니다. 참고로 공식 문서의 GitHub 이벤트 자동화 절차(GitHub App 설치, 팀 조직 생성, GitHub 조직 "Claim")와 웹훅 등록 예시는 **OpenHands Cloud** 기준으로 쓰여 있습니다. 셀프 호스팅 백엔드에서 GitHub 웹훅을 직접 받는 구성은 문서로 확인하지 못했으니, 로컬에서는 위의 MCP 폴링 방식부터 시작하는 것이 무난합니다.

### 예제 5: 팀 서버(VM)로 상시 운영하기

노트북을 덮어도 에이전트가 계속 일하게 하려면 VM에 올립니다. 1인 사용 기준으로 Ubuntu 24.04, 2 vCPU, 4 GB RAM이면 충분하다고 안내합니다.

**1) 먼저 방화벽부터 잠급니다.** 인바운드는 내 IP의 SSH(22)만 허용하고, 8000(ingress), 18000(Agent Server), 18001(Automation), 3001(정적 서버)은 외부에서 닿지 않아야 합니다.

**2) 설치하고 공개 모드로 실행합니다.**

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
sudo npm install -g @openhands/agent-canvas

# 강한 API 키를 만들어 파일로 보관
cat > ~/.agent-canvas.env <<EOF
export LOCAL_BACKEND_API_KEY="$(openssl rand -base64 32)"
EOF
chmod 600 ~/.agent-canvas.env
source ~/.agent-canvas.env

# 백엔드만 실행 (UI는 각자 노트북에서)
agent-canvas --backend-only --public
```

`--public` 모드에서는 키가 프론트엔드에 자동 주입되지 않고, 모든 `/api/*` 호출에 `X-Session-API-Key` 헤더가 필요합니다. 오래 운영할 서버라면 tmux보다 systemd 서비스로 등록하는 편이 낫습니다.

```ini
# /etc/systemd/system/agent-canvas.service
[Unit]
Description=Agent Canvas
After=network.target

[Service]
Environment=LOCAL_BACKEND_API_KEY=<your-key>
ExecStart=npx @openhands/agent-canvas --public
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now agent-canvas
```

**3) 내 노트북에서 접속합니다.** 가장 안전한 방법은 SSH 터널입니다.

```bash
# 노트북에서
ssh -L 8000:127.0.0.1:8000 user@your-vm
agent-canvas --frontend-only --port 3000
```

포트가 겹치지 않도록 로컬 프론트엔드는 다른 포트로 띄우고, `Manage Backends > Add Backend`에서 Host에 `http://localhost:8000`, API 키에 VM의 `LOCAL_BACKEND_API_KEY`를 넣습니다. 브라우저로 바로 접속해야 한다면 nginx와 Let's Encrypt로 HTTPS를 붙이거나(WebSocket/SSE 프록시 설정 필요), ngrok을 쓰고 팀 공유 시에는 ngrok Google OAuth 정책을 앞에 두는 방법이 문서에 있습니다.

## 실무 팁 & 자주 겪는 문제

**보안: 가장 먼저 읽어야 할 부분**

- 공식 문서는 **에이전트와 ACP 프로세스를 신뢰하지 않는 코드로 취급하라**고 합니다. 셸 명령 실행, 파일 읽기·쓰기, 연결된 도구 사용이 모두 가능합니다.
- npm/npx나 소스 실행은 **샌드박스가 없습니다.** 에이전트가 내 사용자 계정 권한으로 홈 디렉터리, SSH 키, 클라우드 자격 증명 파일에 접근할 수 있습니다. 노트북에서는 Docker 방식을 권장합니다.
- Docker라도 넓은 디렉터리 마운트, `--privileged`, 호스트 네트워크, Docker 소켓 마운트는 격리를 약하게 만듭니다.
- 서버를 외부에 열 때는 `--public`, 강한 `LOCAL_BACKEND_API_KEY`, 방화벽이나 VPN, HTTPS를 모두 갖추세요. 키는 백엔드 전체 권한이니 유출되면 즉시 교체합니다.
- 알려진 이슈로, 내장 OpenVSCode 편집기가 Canvas와 **같은 브라우저 origin**(`/vscode` 경로)에서 서비스됩니다. 그 origin에서 실행되는 스크립트는 브라우저 `localStorage`에 저장된 **모든 백엔드의 세션 API 키**를 읽을 수 있습니다([#16492](https://github.com/OpenHands/OpenHands/issues/16492)). 신뢰할 수 없는 편집기 확장은 설치하지 마세요.
- 자동화에 쓰는 GitHub 토큰은 필요한 저장소와 권한으로만 좁히고 만료일을 두세요.

**자주 겪는 문제**

| 증상 | 확인할 것 |
|---|---|
| `agent-canvas` 명령을 못 찾음 | `npm prefix -g`의 `bin`이 `PATH`에 있는지. 안 되면 `npx @openhands/agent-canvas` |
| 시작 실패 | `uv`/`uvx` 설치 여부. 설치 후 새 터미널 열기 |
| 포트 8000 사용 중 | `agent-canvas --port 3000` 또는 Docker `-p 127.0.0.1:3000:8000` |
| Docker 컨테이너가 재시작 반복 | `docker logs`에 `ERR_MODULE_NOT_FOUND`면 이미지 문제. 이전 태그로 고정 |
| 백엔드 연결 끊김 | `Manage Backends`에서 URL과 API 키 확인 |
| `LLM Provider NOT provided` | 제공자 필드와 모델 ID 접두사가 맞는지 |
| ACP 에이전트 인증 실패 | 백엔드가 Docker/VM이면 내 PC 로그인이 안 보임. API 키나 토큰 추가 |
| 파일이 엉뚱한 곳에 생김 | 대화 시작 전 `Open Workspace`, Docker는 `/projects` 아래인지 |
| MCP 설정이 안 보임 | `Settings`가 아니라 상단 `Customize > MCP Servers` |
| 자동화가 안 보임 | 활성 백엔드에 Automation Server가 있는지, 시크릿과 MCP가 같은 백엔드에 있는지 |

**운영 팁**

- npm/npx로 띄웠다면 터미널을 닫는 순간 로컬 백엔드도 멈춥니다. Docker, VM, 클라우드 백엔드는 따로 멈출 때까지 계속 돌아갑니다.
- 설정과 기록은 패키지 밖(`~/.openhands` 또는 `openhands-data` 볼륨)에 있어서, 업데이트나 삭제로 지워지지 않습니다. 완전히 지우려면 이 경로를 직접 삭제해야 합니다.
- Docker 이미지는 `latest` 대신 버전 태그(예: `1.28.1`)로 고정하면 깨진 릴리스를 피하기 쉽습니다.
- 같은 제공자의 ACP 대화를 한 컨테이너에서 동시에 돌리면 인증·설정 파일을 두고 경합할 수 있다는 점이 문서에 알려진 제약으로 적혀 있습니다.
- CI 스크립트에서 쓰는 별도 `openhands` CLI의 headless 모드(`openhands --headless -t "..."`)는 **항상 자동 승인 모드**로 실행됩니다. 격리된 러너에서만 쓰세요. 참고로 `openhands serve`는 예전 CLI GUI용이라 Agent Canvas만 설치해서는 동작하지 않습니다.

## 비슷한 도구와 비교

각 제품의 기능과 가격은 빠르게 바뀌므로 아래 표는 2026년 10월 기준의 대략적인 성격 비교입니다.

| 항목 | OpenHands (Agent Canvas) | Claude Code 단독 | Devin | GitHub Copilot coding agent |
|---|---|---|---|---|
| 형태 | 셀프 호스팅 UI + 에이전트 서버 | 터미널/IDE 중심 에이전트 CLI | 클라우드 SaaS 에이전트 | GitHub에 통합된 에이전트 |
| 라이선스 | MIT 오픈소스 | 상용 | 상용 | 상용(Copilot 구독) |
| 실행 위치 | 내 PC, Docker, VM, K8s, Cloud 중 선택 | 주로 내 PC | 벤더 클라우드 | GitHub 측 실행 환경 |
| 에이전트 선택 | 자체 에이전트 + ACP 에이전트 | Claude Code | Devin | Copilot |
| 모델 선택 | 거의 모든 LLM(BYO 키, 로컬 모델) | Anthropic 모델 중심 | 벤더가 결정 | GitHub이 제공하는 모델 중 선택 |
| 자동화 | 스케줄·웹훅·이벤트 내장 | 별도 스크립트나 CI 연동 필요 | 제품 내 기능 | 이슈 할당, PR 기반 흐름 |
| 운영 부담 | 직접 설치·보안 관리 | 낮음 | 낮음 | 낮음 |

- **Claude Code 단독**은 개발자 한 명이 터미널에서 빠르게 쓰기에 가장 간단합니다. OpenHands는 Claude Code를 대체하기보다 **Claude Code를 서버에서, 자동화와 함께, 다른 에이전트와 나란히** 돌리는 관리 계층으로 볼 수 있습니다.
- **Devin**과 **Copilot coding agent**는 실행 환경을 벤더가 관리해 주는 대신, 코드와 데이터가 벤더 인프라를 거칩니다. 데이터 위치와 모델 선택을 직접 통제해야 한다면 OpenHands 쪽이 유리합니다.
- 반대로 보안 설정, 업데이트, 서버 운영을 직접 할 여력이 없다면 관리형 서비스가 총비용 면에서 나을 수 있습니다.

## 장점과 한계

**장점**

- **MIT 라이선스**이고, Agent Canvas 로컬 배포는 무료입니다.
- 에이전트와 모델에 종속되지 않습니다. 구독 중인 Claude Code나 Codex를 그대로 가져올 수 있고, 로컬 모델도 붙일 수 있습니다.
- 노트북, Docker, VM, Kubernetes, 클라우드를 한 화면에서 오갈 수 있습니다.
- 스케줄·이벤트 자동화가 기본 내장되어 있고, JSON 내보내기와 Git 동기화로 자동화를 코드처럼 관리할 수 있습니다.
- SDK가 분리되어 있어서 UI 없이 Python으로 자체 에이전트를 만들 수도 있습니다.

**한계**

- **베타 단계**입니다. 릴리스가 매우 잦고(v1.28.x), 문서에도 "아직 노출되지 않음", "후속 작업으로 추적 중" 같은 표현이 자주 보입니다. 이미지가 깨져 배포된 경우에 대한 문제 해결 항목이 따로 있을 정도입니다.
- **보안 책임이 사용자에게 있습니다.** 기본 npm 실행은 샌드박스가 없고, 서버 공개 시 키 관리와 네트워크 통제를 직접 해야 합니다.
- **멀티 유저 기능은 유료입니다.** 공식 요금제 기준으로 무료는 로컬 배포와 커뮤니티 지원이고, 셀프 호스팅 Teams(월 499달러, 최대 10석, 자동화·멀티 유저 ID·RBAC 포함), Teams Plus(월 999달러, 최대 20석, SAML/SSO), Enterprise(맞춤 가격)가 있습니다. Teams 계열은 월 5,000세션 상한이 있습니다. FAQ도 오픈소스 버전은 여러 사용자가 한 인스턴스를 공유하는 멀티 테넌트 운영에 적합하지 않다고 안내합니다.
- 일부 기능(GitHub App 기반 이벤트 라우팅, 공유 자동화 대화 등)은 OpenHands Cloud 기준으로 문서화되어 있어, 셀프 호스팅에서 같은 경험을 얻으려면 추가 확인이 필요합니다.
- 에이전트 품질은 결국 연결한 모델에 크게 좌우됩니다. 작은 로컬 모델로는 복잡한 작업을 끝내기 어렵습니다.

## 이런 분께 추천 / 이런 경우엔 다른 도구

**추천**

- 여러 코딩 에이전트(OpenHands, Claude Code, Codex 등)를 한 화면에서 비교하며 쓰고 싶은 분
- 코드와 데이터를 회사 인프라 밖으로 내보내지 않고 에이전트를 돌려야 하는 팀
- PR 리뷰, 이슈 정리, 일일 리포트처럼 반복적인 개발 운영 작업을 자동화하고 싶은 팀
- 항상 켜진 서버(VM, Mac Mini)에 에이전트를 올려 두고 노트북과 분리해서 쓰고 싶은 분
- 자체 에이전트 제품을 만들기 위해 검증된 SDK와 서버 API가 필요한 개발자

**다른 도구가 나은 경우**

- 혼자 터미널에서 빠르게 코딩 도움만 받으면 된다면 **Claude Code 같은 CLI 에이전트 단독 사용**이 더 단순합니다.
- 서버 운영과 보안 관리를 맡을 사람이 없다면 **관리형 서비스**(OpenHands Cloud, Devin, Copilot coding agent 등)를 먼저 검토하세요.
- GitHub 이슈를 할당하면 PR이 오는 흐름만 필요하고 이미 Copilot을 쓰고 있다면 **Copilot coding agent**가 도입 비용이 낮습니다.
- 안정성이 최우선인 운영 환경이라면 베타가 끝날 때까지 작은 범위에서 먼저 시험해 보는 편이 좋습니다.

## 참고 링크

- [GitHub 저장소 README](https://github.com/OpenHands/OpenHands)
- [Self-Hosting 가이드 (저장소 docs/SELF_HOSTING.md)](https://github.com/OpenHands/OpenHands/blob/main/docs/SELF_HOSTING.md)
- [ACP 에이전트 가이드 (저장소 docs/ACP_AGENTS.md)](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md)
- [아키텍처 문서 (저장소 docs/architecture.md)](https://github.com/OpenHands/OpenHands/blob/main/docs/architecture.md)
- [Agent Canvas 개요](https://docs.openhands.dev/openhands/usage/agent-canvas/overview)
- [설치](https://docs.openhands.dev/openhands/usage/agent-canvas/setup)
- [첫 실행 설정](https://docs.openhands.dev/openhands/usage/agent-canvas/first-time-setup)
- [Docker로 실행](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/docker)
- [대화별 Docker 컨테이너](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/docker-execution)
- [VM / 셀프 호스팅](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/vm)
- [모델 설정](https://docs.openhands.dev/openhands/usage/agent-canvas/model-configuration)
- [ACP 에이전트](https://docs.openhands.dev/openhands/usage/agent-canvas/acp-agents)
- [자동화 개요](https://docs.openhands.dev/openhands/usage/automations/overview)
- [이벤트 기반 자동화](https://docs.openhands.dev/openhands/usage/automations/event-automations)
- [자동화 관리](https://docs.openhands.dev/openhands/usage/agent-canvas/managing-automations)
- [미리 만든 자동화](https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt-automations)
- [GitHub PR Review Assistant](https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt/github-pr-review)
- [문제 해결](https://docs.openhands.dev/openhands/usage/agent-canvas/troubleshooting)
- [FAQ](https://docs.openhands.dev/overview/faqs)
- [SDK Hello World](https://docs.openhands.dev/sdk/guides/hello-world)
- [CLI Headless 모드](https://docs.openhands.dev/openhands/usage/cli/headless)
- [요금제](https://openhands.dev/pricing)
- [Automation 서비스 저장소](https://github.com/OpenHands/automation)
- [Software Agent SDK 저장소](https://github.com/OpenHands/software-agent-sdk)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
