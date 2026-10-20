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

**여러 AI 코딩 에이전트를 한곳에서 실행하고 자동화하는 셀프 호스팅 플랫폼**입니다. 핵심 앱인 **Agent Canvas**에서 OpenHands 자체 에이전트는 물론 Claude Code, Codex, Gemini CLI, OpenCode 같은 다른 에이전트도 함께 쓸 수 있습니다.

## 주요 기능

- **원하는 곳에서 실행:** 내 PC, Docker, 클라우드 VM, 회사 인프라 등 어디서든 에이전트를 돌릴 수 있습니다.
- **백엔드 전환:** 로컬, 원격, 클라우드 에이전트를 하나의 화면에서 바꿔가며 쓸 수 있습니다.
- **자동화:** 정해진 시간이나 웹훅 이벤트에 맞춰 에이전트를 실행합니다.
  - 예: 보고서를 만들어 Slack에 올리기, GitHub 이슈를 작은 작업으로 나누기
- **도구 연동:** Slack, GitHub, Linear, Notion 등과 연결
- **모델 자유:** 어떤 LLM이든 연결 가능
- **에이전트 자유:** ACP(Agent-Client Protocol)를 지원하는 에이전트라면 무엇이든 붙일 수 있습니다.

## 빠르게 시작하기

**방법 1: 바로 설치 (샌드박스 없음)**

```bash
npm install -g @openhands/agent-canvas
agent-canvas
```

Node.js 24 이상과 `uv`가 필요합니다. 이 방법은 에이전트가 **내 파일 시스템 전체에 접근할 수 있으니** 주의하세요.

**방법 2: Docker 샌드박스로 실행 (더 안전)**

```bash
export PROJECTS_PATH="$HOME/projects"
mkdir -p "$PROJECTS_PATH" "$HOME/.openhands"
docker run -it --rm \
  -p 127.0.0.1:8000:8000 \
  -e AGENT_CANVAS_ALLOW_LAN_SESSION_KEY=true \
  -v "$HOME/.openhands:/home/openhands/.openhands" \
  -v "${PROJECTS_PATH}:/projects" \
  ghcr.io/openhands/agent-canvas:1.28.1
```

실행 후 `http://localhost:8000`(Docker는 `/canvas`)으로 접속하면 됩니다. 대화마다 별도 컨테이너를 띄우는 방식도 지원합니다.

## 구조

```
Agent Canvas (화면) ──▶ Agent Server (에이전트 실행, REST API)
                         ▲
Automation Server ───────┘ (스케줄·웹훅으로 작업 시작)
```

Agent Canvas 하나로 여러 Agent Server에 연결해 오갈 수 있습니다. 예를 들어 팀 공용 서버에서는 코드 리뷰와 의존성 업데이트를 맡기고, 개인 노트북에서는 내 작업용 에이전트를 돌리는 식입니다.

## 이런 분께 추천

- 여러 코딩 에이전트를 한 화면에서 관리하고 싶은 분
- 노트북을 꺼도 에이전트가 계속 일하도록 서버에 올려두고 싶은 팀
- 반복적인 개발 작업(리포트, 이슈 정리, 의존성 업데이트)을 에이전트로 자동화하고 싶은 분

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
