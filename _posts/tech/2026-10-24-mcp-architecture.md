---
layout: default
title: "[기술 소개] MCP 구조 해설: 호스트, 클라이언트, 서버와 세 가지 기본 요소"
description: "MCP 최신 명세(2026-07-28) 기준으로 호스트·클라이언트·서버 역할, JSON-RPC와 무상태 요청, stdio·Streamable HTTP 전송, tools·resources·prompts, 권한과 보안 고려를 정리하고 Python SDK 최소 서버를 직접 실행했습니다."
date: 2026-10-24 00:06:00 +0900
categories: [tech]
---

# [기술 소개] MCP 구조 해설: 호스트, 클라이언트, 서버와 세 가지 기본 요소

- **주요 출처:** [MCP 명세 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) · [명세 변경 내역](https://modelcontextprotocol.io/specification/2026-07-28/changelog) · [명세 저장소 modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol) · [Python SDK](https://github.com/modelcontextprotocol/python-sdk) · [Anthropic의 MCP 발표(2024-11-25)](https://www.anthropic.com/news/model-context-protocol) · [AAIF 기증 발표(2025-12-09)](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)
- **한눈에 (2026-10-24 기준):** 최신 명세 버전은 `2026-07-28`(2026-07-28 정식 공개)입니다. MCP는 2025-12-09부터 Linux Foundation 산하 AAIF(Agentic AI Foundation)의 프로젝트입니다. 공식 Python SDK 최신 릴리스는 v2.3.0(2026-10-02), TypeScript SDK는 v2.3.1(2026-10-05)입니다.
- **주의:** `2026-07-28` 명세는 큰 호환성 변경을 담고 있습니다. 연결 시작 때 주고받던 `initialize` 핸드셰이크와 `Mcp-Session-Id` 세션이 **삭제**됐고, Roots·Sampling·Logging 기능은 **사용 중단 예정(deprecated)**으로 바뀌었습니다. 2025년에 쓰인 튜토리얼 상당수가 옛 방식을 설명하므로, 이 글은 최신 명세를 기준으로 하고 바뀐 부분을 따로 표시합니다.

## 한 줄 요약

**MCP(Model Context Protocol)는 LLM 애플리케이션이 외부 도구와 데이터에 붙는 방식을 JSON-RPC 위의 한 가지 규약으로 통일한 개방형 프로토콜이며, 핵심은 "호스트가 통제하고, 클라이언트가 중계하고, 서버는 도구(tools)·자료(resources)·프롬프트(prompts)만 내놓는다"는 역할 분리입니다.**

## 배경

Anthropic은 2024년 11월 25일 MCP를 공개하며 문제를 이렇게 설명했습니다. 아무리 뛰어난 모델도 정보 사일로와 레거시 시스템에 갇힌 데이터로부터 고립돼 있고, **새 데이터 소스마다 따로 구현을 만들어야 해서** 연결된 시스템을 확장하기 어렵다는 것입니다. AI 애플리케이션이 n종, 외부 시스템이 m종이면 n×m가지 연동 코드가 필요한 상황을, 공통 프로토콜 하나로 n+m가지 구현으로 줄이자는 발상입니다.

명세는 영감의 출처로 LSP(Language Server Protocol)를 듭니다. LSP 덕분에 편집기마다 언어 지원을 따로 만들지 않아도 되듯, MCP는 AI 애플리케이션마다 도구 연동을 따로 만들지 않아도 되게 하려는 것입니다.

| 날짜 | 사건 | 출처 |
|---|---|---|
| 2024-11-25 | Anthropic이 MCP 공개. 명세와 SDK, Claude Desktop의 로컬 서버 지원, 오픈소스 서버 저장소(Google Drive, Slack, GitHub, Git, Postgres, Puppeteer) 함께 발표 | [발표문](https://www.anthropic.com/news/model-context-protocol) |
| 2025-03-26 | 명세 개정. HTTP+SSE 전송을 대체하는 Streamable HTTP 도입 | [명세 Streamable HTTP 절](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) |
| 2025-12-09 | MCP를 AAIF에 기증. AAIF는 Anthropic, Block, OpenAI가 공동 설립 | [기증 발표](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation) |
| 2026-07-28 | 명세 `2026-07-28` 정식 공개. 무상태(stateless) 코어, Multi Round-Trip Requests, 헤더 기반 라우팅, 공식 확장 체계 | [MCP 블로그](https://blog.modelcontextprotocol.io/posts/2026-07-28/) |

명세 저장소에는 지금까지 `2024-11-05`, `2025-03-26`, `2025-06-18`, `2025-11-25`, `2026-07-28` 다섯 개의 버전이 있습니다. 버전 이름이 곧 날짜이고, 하위 호환을 깨는 변경이 생길 때 새 날짜가 붙습니다.

채택 규모는 공식 발표 기준으로 2025-12-09에 활성 공개 서버 1만 개 이상, Python·TypeScript SDK 월간 다운로드 9,700만 회 이상이었고, ChatGPT, Cursor, Gemini, Microsoft Copilot, Visual Studio Code 등이 MCP를 채택했다고 밝혔습니다. 2026-07-28 명세 공개 글은 Tier 1 SDK 전체 월간 다운로드가 "5억 회에 가깝다"고 적었습니다. 모두 발표 주체가 밝힌 값입니다.

## 핵심 내용

### 1. 세 역할: 호스트, 클라이언트, 서버

명세의 [아키텍처 문서](https://modelcontextprotocol.io/specification/2026-07-28/architecture)는 MCP를 "클라이언트-호스트-서버 구조"로 정의합니다. 이름이 비슷해 헷갈리기 쉬우니 예를 들어 보겠습니다. Claude Desktop이나 VS Code 같은 앱이 **호스트**이고, 그 앱 안에서 GitHub 서버와 연결을 하나 맺을 때마다 **클라이언트**가 하나 생기며, GitHub 연동을 제공하는 프로그램이 **서버**입니다.

```
┌─────────────── 호스트 (AI 애플리케이션) ───────────────┐
│  LLM 호출, 사용자 동의 UI, 보안 정책                    │
│   ├─ 클라이언트 1 ──── stdio ────→ 서버 A (로컬 파일·Git)│
│   ├─ 클라이언트 2 ──── stdio ────→ 서버 B (로컬 DB)      │
│   └─ 클라이언트 3 ── Streamable HTTP ─→ 서버 C (원격 API)│
└──────────────────────────────────────────────────────┘
```

| 역할 | 하는 일 (명세 기준) |
|---|---|
| 호스트 | 클라이언트를 만들고 관리, 연결 권한과 수명 관리, 보안 정책과 사용자 동의 강제, LLM 연동, 여러 클라이언트의 컨텍스트 통합 |
| 클라이언트 | **서버 하나와만** 통신(1:1), 모든 요청에 프로토콜 버전과 기능 목록을 붙임, 서버 간 보안 경계 유지 |
| 서버 | tools, resources, prompts를 노출. 로컬 프로세스일 수도, 원격 서비스일 수도 있음 |

명세가 밝힌 설계 원칙 네 가지 중 세 번째가 이 구조의 핵심입니다. **"서버는 대화 전체를 읽을 수 없고, 다른 서버의 내부를 볼 수 없어야 한다."** 전체 대화 기록은 호스트에 남고, 서버는 필요한 정보만 받으며, 서버 간 상호작용은 호스트가 통제합니다. 나머지 원칙은 서버는 아주 쉽게 만들 수 있어야 하고(복잡한 조율은 호스트 몫), 조합 가능해야 하며, 기능을 점진적으로 추가할 수 있어야 한다는 것입니다.

### 2. JSON-RPC 2.0과 무상태 요청 (2026-07-28의 가장 큰 변화)

모든 메시지는 [JSON-RPC 2.0](https://www.jsonrpc.org/) 형식이고 UTF-8로 인코딩해야 합니다. 요청(`id`가 있음), 응답, 알림(`id`가 없음) 세 가지가 있습니다.

`2025-11-25`까지는 연결을 열면 먼저 `initialize` 요청으로 버전과 기능을 협상하고, 그 연결(세션)에 상태를 묶었습니다. `2026-07-28`부터는 이 핸드셰이크가 없습니다. 대신 **모든 요청이 `_meta` 안에 자기 프로토콜 버전과 클라이언트 기능 목록을 직접 싣습니다.**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "search_notes",
    "arguments": { "keyword": "호스트" },
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "io.modelcontextprotocol/clientInfo": { "name": "my-app", "version": "1.0" }
    }
  }
}
```

- `protocolVersion`과 `clientCapabilities`는 필수입니다. 빠지면 서버는 `-32602`(Invalid params)로 거절해야 합니다(아래 실행 예제에서 확인).
- 서버의 기능을 미리 알고 싶은 클라이언트는 새 메서드 `server/discover`를 호출합니다. 서버는 이 메서드를 **반드시** 구현해야 하지만, 클라이언트가 꼭 먼저 호출할 필요는 없습니다.
- 서버는 응답의 `_meta`에 `io.modelcontextprotocol/serverInfo`로 자기 이름과 버전을 밝히는 것이 권장됩니다. 명세는 clientInfo와 serverInfo가 **검증되지 않은 자기 신고 값**이므로 보안 판단에 쓰지 말라고 적어 두었습니다.

공식 블로그는 이 변화의 이유를 신뢰성과 확장성으로 설명합니다. 요청마다 필요한 정보가 다 들어 있으니, **어느 요청이든 일반 라운드 로빈 로드밸런서 뒤의 아무 서버 인스턴스에나 보낼 수 있고** 공유 세션 저장소가 필요 없습니다. 여러 호출에 걸친 상태가 필요하면, 서버가 도구 결과로 핸들(식별자)을 발급하고 모델이 다음 호출의 인자로 그 핸들을 넘기라고 권합니다. 블로그는 이것이 "전송 계층에 숨은 세션 상태보다 낫다, 모델이 핸들을 보고 도구 사이에 이어 줄 수 있기 때문"이라고 적었습니다.

옛 버전과의 호환은 클라이언트가 맡습니다. Python SDK 문서에 따르면 SDK의 `Client`는 기본 모드에서 먼저 `server/discover`를 보내 보고, 옛 서버가 이를 모르면 `initialize` 핸드셰이크로 되돌아갑니다.

### 3. 전송 방식: stdio와 Streamable HTTP

명세는 전송(transport)을 "메시지를 어떻게 담아 나르는가"만 정하는 바인딩으로 정의하고, 메시지의 의미는 전송과 무관하게 같다고 못 박습니다. 표준 전송은 두 가지입니다.

| 구분 | stdio | Streamable HTTP |
|---|---|---|
| 형태 | 클라이언트가 서버를 **하위 프로세스로 실행**하고 stdin/stdout으로 통신 | 서버가 독립 프로세스로 떠 있고 **하나의 HTTP 엔드포인트**(예: `https://example.com/mcp`)가 POST를 받음 |
| 메시지 구분 | 줄바꿈으로 구분된 JSON-RPC, 메시지 안에 줄바꿈 금지 | 메시지마다 별도 HTTP POST. 응답은 JSON 하나 또는 그 요청 전용 SSE(Server-Sent Events) 스트림 |
| 로그 | stdout에는 MCP 메시지 외 아무것도 쓰면 안 됨. 로그는 stderr로 | 진행 알림 등은 해당 요청의 SSE 스트림으로 |
| 메타데이터 | 본문 `_meta`에만 | 본문 `_meta` + `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name` 헤더 (게이트웨이가 본문을 파싱하지 않고 라우팅·인가 가능) |
| 취소 | `notifications/cancelled` 알림 | SSE 응답 스트림을 닫으면 취소 |
| 인증 | 명세의 인가(authorization) 절차를 따르지 말고 **환경 변수 등에서 자격 증명**을 가져옴 | OAuth 2.1 기반 인가 명세를 따르는 것이 권장(SHOULD) |
| 주로 쓰는 곳 | 로컬 도구(파일, Git, 로컬 DB) | 원격 서비스, 여러 사용자가 쓰는 서버 |

`2024-11-05`의 HTTP+SSE 전송은 `2025-03-26`부터 Streamable HTTP로 대체됐고, `2026-07-28`에서 공식 사용 중단 상태가 됐습니다. 또 `2026-07-28`의 Streamable HTTP는 서버 쪽 GET 스트림 엔드포인트와 세션을 없앴고, 오래 열어 두는 변경 알림은 `subscriptions/listen` 요청 하나로 받습니다.

### 4. 세 가지 기본 요소: 누가 쓰기로 결정하나

서버가 내놓는 기능은 세 가지이고, 명세는 이를 **"누가 통제하느냐"**로 구분합니다. 이 구분을 이해하면 무엇을 도구로, 무엇을 리소스로 만들지 판단하기 쉬워집니다.

| 요소 | 통제 주체 | 설명 | 예 | 주요 메서드 |
|---|---|---|---|---|
| Tools | **모델** | LLM이 스스로 발견하고 호출해 행동을 수행 | API POST 요청, 파일 쓰기, DB 질의 | `tools/list`, `tools/call` |
| Resources | **애플리케이션** | 클라이언트가 붙이고 관리하는 맥락 데이터. URI로 식별 | 파일 내용, git 기록, DB 스키마 | `resources/list`, `resources/read`, `resources/templates/list` |
| Prompts | **사용자** | 사용자가 골라 실행하는 템플릿 | 슬래시 명령, 메뉴 항목 | `prompts/list`, `prompts/get` |

같은 "노트 검색" 기능이라도, 모델이 대화 중 필요할 때 알아서 부르게 하려면 tool로, 사용자가 파일 선택기에서 골라 붙이게 하려면 resource로, `/요약` 같은 명령으로 실행하게 하려면 prompt로 만드는 식입니다. 명세는 이것이 사용자 인터페이스를 강제하지는 않으며, 구현이 자유롭게 정해도 된다고 덧붙입니다.

반대 방향, 즉 **서버가 클라이언트에 요청하는 기능**도 있습니다. 사용자에게 추가 정보를 묻는 Elicitation(폼 또는 URL 방식)이 대표적입니다. `2026-07-28`에서는 서버가 요청을 직접 보내는 대신, 결과로 `resultType: "input_required"`와 필요한 질문을 돌려주면 클라이언트가 답을 붙여 **원래 요청을 다시 보내는** MRTR(Multi Round-Trip Requests) 방식으로 바뀌었습니다. 서버가 클라이언트의 LLM을 빌려 쓰는 Sampling, 클라이언트가 작업 디렉터리를 알려 주는 Roots는 사용 중단 예정이 됐고, 명세는 각각 LLM 공급자 API를 직접 쓰거나 도구 인자·리소스 URI·서버 설정으로 대신하라고 권합니다. 최소 12개월은 계속 동작합니다.

### 5. 권한과 보안: 프로토콜이 강제하지 않는 것들

명세의 보안 절은 첫머리에서 **"MCP 자체는 이 보안 원칙을 프로토콜 수준에서 강제할 수 없다"**고 밝힙니다. 그래서 책임이 구현자, 특히 호스트에 있습니다.

- **사용자 동의와 통제:** 사용자가 모든 데이터 접근과 작업을 명시적으로 동의하고 이해해야 하며, 호스트는 사용자 데이터를 서버에 넘기기 전에 동의를 받아야 합니다.
- **도구는 임의 코드 실행입니다.** 호스트는 도구 호출 전에 사용자 동의를 받아야 하고, 도구 명세는 사람이 호출을 거부할 수 있는 "human in the loop"를 권합니다. 특히 도구의 동작을 설명하는 `annotations`는 **신뢰할 수 있는 서버에서 온 것이 아니면 신뢰하지 말아야** 합니다.
- **서버의 의무(MUST):** 모든 도구 입력 검증, 접근 제어, 호출 빈도 제한, 출력 정제
- **로컬 HTTP 서버:** `Origin` 헤더를 반드시 검증해 DNS 리바인딩 공격을 막고, 로컬에서는 `0.0.0.0`이 아닌 `127.0.0.1`에만 바인딩하라고 권합니다.
- **토큰 패스스루 금지:** 공식 [보안 모범 사례](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)는 MCP 서버가 자기에게 발급되지 않은 토큰을 받아 그대로 하위 API에 넘기는 것을 "명시적으로 금지된" 안티패턴으로 꼽습니다. 이 밖에 혼동된 대리인(confused deputy), SSRF, 상태 핸들 탈취, 로컬 서버 침해 같은 공격과 대응을 정리해 두었습니다.
- **stdio는 샌드박스가 아닙니다.** [로컬 서버 보안 가이드](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/local-server-security)는 클라이언트와 stdio 서버가 "하나의 신뢰 영역"을 공유하며, SDK는 둘 사이를 서로 방어하지 않는다고 설명합니다. 실제 보안 판단은 **실행 전**, 즉 무엇을 설치하고(출처) 어떻게 실행하느냐(격리)에서 일어납니다.

## 실무에서 쓰는 법

### 최소 서버: 도구, 리소스, 프롬프트 하나씩

공식 Python SDK README의 "A server in 15 lines" 예제와 SDK 문서의 프롬프트 예제를 합쳐, 세 요소를 하나씩 가진 서버를 만들었습니다. SDK v2부터 서버 클래스 이름은 `MCPServer`입니다(v1의 `FastMCP`에 해당).

```python
# server.py
from mcp.server import MCPServer

mcp = MCPServer("Notes")

NOTES = {"mcp": "MCP는 호스트, 클라이언트, 서버로 나뉜다."}


@mcp.tool()
def search_notes(keyword: str) -> list[str]:
    """Search notes whose title or body contains the keyword."""
    return [title for title, body in NOTES.items() if keyword in title or keyword in body]


@mcp.resource("notes://{title}")
def read_note(title: str) -> str:
    """Return the body of a note."""
    return NOTES.get(title, "")


@mcp.prompt()
def summarize_note(title: str) -> str:
    """Ask the model to summarize a note."""
    return f"다음 노트를 세 줄로 요약해 주세요: notes://{title}"


if __name__ == "__main__":
    mcp.run()  # 기본값은 stdio
```

README가 강조하듯 JSON Schema를 직접 쓰지 않았습니다. `keyword: str` 타입 힌트와 독스트링이 곧 도구의 스키마와 설명이 됩니다.

### 실행 결과: 선(wire) 위의 JSON-RPC를 직접 보기

아래는 필자가 2026-10-24에 Python 3.12 가상환경에 `mcp==2.3.0`을 설치하고, 위 서버의 stdin에 JSON-RPC를 한 줄씩 직접 써 넣어 얻은 출력입니다(가독성을 위해 정리하고 `_meta.serverInfo`는 생략). SDK가 감춰 주는 프로토콜이 실제로 어떻게 생겼는지 보려는 목적입니다.

**① `server/discover`: 서버가 지원 버전과 기능을 알림**

```json
{"jsonrpc": "2.0", "id": 1, "result": {
  "resultType": "complete",
  "supportedVersions": ["2026-07-28"],
  "capabilities": {
    "tools": {"listChanged": true},
    "resources": {"listChanged": true, "subscribe": true},
    "prompts": {"listChanged": true}},
  "ttlMs": 0, "cacheScope": "private"}}
```

**② `tools/list`: 타입 힌트에서 만들어진 스키마**

```json
{"jsonrpc": "2.0", "id": 2, "result": {
  "resultType": "complete",
  "tools": [{
    "name": "search_notes",
    "description": "Search notes whose title or body contains the keyword.",
    "inputSchema": {"type": "object",
      "properties": {"keyword": {"title": "Keyword", "type": "string"}},
      "required": ["keyword"], "title": "search_notesArguments"},
    "outputSchema": {"type": "object",
      "properties": {"result": {"type": "array", "items": {"type": "string"}, "title": "Result"}},
      "required": ["result"], "title": "search_notesOutput"}}],
  "ttlMs": 0, "cacheScope": "private"}}
```

**③ `tools/call`: 사람이 읽는 `content`와 기계가 읽는 `structuredContent`**

```json
{"jsonrpc": "2.0", "id": 3, "result": {
  "resultType": "complete",
  "content": [{"type": "text", "text": "mcp"}],
  "structuredContent": {"result": ["mcp"]},
  "isError": false}}
```

**④ `_meta` 없이 보낸 요청: 무상태 명세의 거절**

```json
{"jsonrpc": "2.0", "id": 6, "error": {
  "code": -32602,
  "message": "params._meta must be an object carrying the required 'io.modelcontextprotocol/protocolVersion' and 'io.modelcontextprotocol/clientCapabilities' envelope keys"}}
```

`resources/read`(`notes://mcp`)와 `prompts/get`(`summarize_note`)도 같은 방식으로 각각 노트 본문과 `role: "user"` 메시지를 돌려주는 것을 확인했습니다. 목록 응답의 `ttlMs`와 `cacheScope`는 `2026-07-28`에 추가된 캐시 힌트입니다. 명세는 `tools/list`의 순서를 결정적으로 유지하라고 권하는데, 도구 목록이 매번 같은 순서로 모델 컨텍스트에 들어가야 LLM 프롬프트 캐시 적중률이 오르기 때문입니다.

실제 사용에서는 이 JSON을 손으로 쓸 일이 없습니다. README의 클라이언트 예제처럼 `Client("http://localhost:8000/mcp")`로 연결하거나, 호스트 앱(Claude Desktop, VS Code 등)의 설정 파일에 서버 실행 명령을 등록합니다. 개발 중에는 README가 안내하는 `uv run mcp dev server.py`로 [MCP Inspector](https://github.com/modelcontextprotocol/inspector)를 띄워 모델 없이 도구를 시험할 수 있습니다(필자는 Inspector 실행은 확인하지 않았습니다).

### 비교: MCP, Agent Skills, 직접 API 연동

| 구분 | 직접 API 연동 | MCP 서버 | Agent Skills |
|---|---|---|---|
| 무엇을 담나 | 특정 앱 안의 연동 코드 | 도구, 리소스, 프롬프트 | 작업 절차와 지식(`SKILL.md` + 스크립트) |
| 재사용 범위 | 그 앱 하나 | MCP를 지원하는 모든 호스트 | Agent Skills를 지원하는 모든 에이전트 |
| 실행 위치 | 앱 프로세스 | 별도 프로세스(로컬) 또는 원격 서비스 | 에이전트 자신의 컨텍스트와 실행 환경 |
| 보안 경계 | 앱이 직접 관리 | 호스트의 동의 UI + 서버의 인가(HTTP는 OAuth) | 설치 전 출처 확인과 감사에 의존 |
| 표준 관리 | 없음 | AAIF (2025-12-09 기증) | AAIF (2026-10-22 기증) |

Agent Skills 열은 블로그의 [Agent Skills 글](/tech/2026/10/24/agent-skills-aaif.html)에서 정리한 명세 기준이고, 직접 API 연동 열은 일반적으로 알려진 특징 기준입니다.

## 한계와 논란

- **명세가 아직 빠르게 바뀝니다.** 2024년 11월 이후 약 20개월 동안 다섯 개 버전이 나왔고, 최신판은 연결 수명 주기 자체를 바꿨습니다. 명세는 `2026-07-28`부터 최소 12개월의 사용 중단 기간을 두는 정책을 도입했지만, 그 전에 만든 서버와 클라이언트는 이번에 마이그레이션 비용을 치러야 합니다. 공식 블로그도 세션 ID에 의존한 개발자에게는 "어느 정도 마이그레이션 비용이 있을 것"이라고 인정합니다.
- **도구 설명이 곧 공격 표면입니다.** 서버가 보내는 도구 이름과 설명을 모델은 지시문처럼 읽습니다. 공식 로컬 서버 보안 가이드는 이를 "설치 시점 검토로는 막을 수 없는 주입(injection) 표면"이라고 부르고, 도구 정의가 바뀌면 다시 묻는 클라이언트를 고르라고 권하면서도 **프로토콜이 이를 요구하지는 않는다**고 밝힙니다. 또 설정된 모든 서버가 같은 모델 컨텍스트를 공유하므로, 악성 서버 하나가 다른 서버의 도구 사용에까지 영향을 줄 수 있습니다.
- **보안의 대부분이 SHOULD입니다.** 사람이 도구 호출을 거부할 수 있어야 한다는 것, 민감한 작업 전 확인, 입력 표시는 대부분 권장 사항입니다. 같은 MCP 서버라도 어떤 호스트에서 쓰느냐에 따라 안전성이 달라집니다.
- **도구가 많을수록 컨텍스트를 먹습니다.** 각 도구의 이름, 설명, 스키마가 모델 컨텍스트에 들어가므로 서버를 많이 붙이면 토큰 비용과 도구 선택 정확도가 문제가 됩니다. Anthropic은 AAIF 기증 발표에서 수천 개 도구를 효율적으로 다루기 위한 Tool Search와 Programmatic Tool Calling을 API에 추가했다고 밝혔는데, 이는 프로토콜 바깥의 공급자별 기능입니다.
- **채택 수치는 자체 발표입니다.** 서버 1만 개, 월간 다운로드 9,700만 회(2025-12)와 약 5억 회(2026-07)는 각각 Anthropic과 MCP 메인테이너가 밝힌 값이며 집계 방법은 공개되지 않았습니다.

## 인사이트

**왜 지금 중요한가: "연결 규약"에서 "웹 워크로드"로.** 초기 MCP는 데스크톱 앱이 로컬 프로세스를 띄워 stdio로 대화하는 모습에 가까웠고, 그래서 연결 단위 세션과 서버가 먼저 말을 거는 양방향 구조를 택했습니다. `2026-07-28`은 이를 요청-응답 무상태 구조로 바꾸고, 메서드 이름을 HTTP 헤더로 올리고, 목록 응답에 캐시 힌트를 붙였습니다. 로드밸런서, API 게이트웨이, WAF, CDN 같은 기존 웹 인프라를 그대로 쓰겠다는 방향입니다. 필자의 판단으로는, 원격 MCP 서버가 SaaS 회사의 "또 하나의 공개 API"가 되는 흐름이 이번 명세로 굳어졌습니다. 반대로 Sampling과 Roots처럼 "서버가 호스트의 능력을 빌려 쓰는" 기능은 사용 중단 예정이 됐습니다. 서버는 더 단순한 HTTP 서비스로, 지능과 통제는 더 확실하게 호스트 쪽으로 모이는 셈입니다.

**실무에 주는 의미.** 서버를 만드는 쪽이라면 세 가지를 권합니다. 첫째, 무엇을 tool로 만들지 신중히 고릅니다. 명세의 통제 주체 구분대로, 모델이 판단해 부를 일만 tool로, 사용자가 붙일 자료는 resource로, 반복 작업 템플릿은 prompt로 나누면 모델 컨텍스트에 들어가는 도구 목록이 작아집니다. 둘째, 도구 목록 순서를 고정하고 설명을 안정적으로 유지합니다. 캐시 적중률뿐 아니라, 정의 변경 시 다시 묻는 클라이언트에서 불필요한 재승인을 줄입니다. 셋째, 세션 대신 명시적 핸들을 씁니다. 상태가 필요하면 도구 결과로 ID를 주고 다음 호출의 인자로 받는 방식이 새 명세의 권장이자, 수평 확장에도 유리합니다. 서버를 **쓰는** 쪽이라면, 로컬 stdio 서버 설치를 "샌드박스 없는 코드 실행 허가"로 보고 출처를 확인한 뒤 컨테이너 같은 격리 환경에서 돌리는 것이 공식 가이드의 권장입니다.

**블로그의 기존 글과의 연결.** [Agent Skills 글](/tech/2026/10/24/agent-skills-aaif.html)에서 MCP는 "무엇을 할 수 있나", Skills는 "어떻게 해야 하나"를 맡는다고 정리했습니다. 이번에 MCP 명세를 직접 읽어 보면 그 분담이 프로토콜 구조에 이미 들어 있습니다. MCP의 prompts가 "사용자가 고르는 템플릿"에 머무는 반면, Skills는 모델이 스스로 꺼내 읽는 절차 지식입니다. 흥미로운 점은 `2026-07-28` 명세의 확장 목록에 **"Skills over MCP"** 작업 그룹이 올라 있다는 것입니다. 명세는 이를 "MCP로 발견하고 소비하는 에이전트 워크플로용 구조화된 지시"로 소개합니다. 두 표준이 같은 재단 안에서 서로를 참조하기 시작한 신호로 보입니다. 또 같은 날 쓴 [컨텍스트 엔지니어링 글](/tech/2026/10/24/context-engineering.html)의 "도구 설계" 항목은 MCP 서버 작성자에게 그대로 적용됩니다.

**한계와 반론.** MCP의 약속은 "한 번 만들면 모든 호스트에서 동작"이지만, 보안과 사용자 경험의 핵심(동의 UI, 도구 정의 고정, 격리)은 호스트 구현에 맡겨져 있습니다. 따라서 "MCP를 지원한다"는 말만으로는 안전성을 판단할 수 없고, 호스트별로 도구 승인 방식과 정의 변경 감지 여부를 따로 확인해야 합니다. 또 무상태 전환은 서버 운영을 쉽게 하지만, 서버가 사용자 입력을 받아야 하는 흐름(Elicitation)은 "질문을 돌려주고 재요청을 기다리는" MRTR로 바뀌어 클라이언트 구현이 오히려 조금 복잡해졌습니다.

**앞으로 지켜볼 점.** (1) 주요 호스트(Claude, ChatGPT, VS Code, Cursor 등)가 `2026-07-28`을 언제 기본으로 쓰는지, 그리고 옛 서버로의 자동 폴백을 얼마나 오래 유지하는지. (2) 도구 정의 서명이나 고정(pinning)이 권장 사항에서 명세 요구 사항으로 올라오는지. 이것이 들어오면 공급망 공격에 대한 판단이 크게 바뀝니다. (3) Skills over MCP 작업 그룹의 결과물이 Agent Skills 명세와 어떻게 연결되는지입니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [MCP 명세 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
- [명세 변경 내역 (2025-11-25 → 2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [아키텍처](https://modelcontextprotocol.io/specification/2026-07-28/architecture) · [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) · [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [The 2026-07-28 Specification (MCP 블로그)](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
- [Security Best Practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices) · [Local Server Security](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/local-server-security)
- [modelcontextprotocol/modelcontextprotocol (명세 저장소)](https://github.com/modelcontextprotocol/modelcontextprotocol)
- [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) · [Python SDK 문서](https://py.sdk.modelcontextprotocol.io/)
- [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector)
- [Introducing the Model Context Protocol (Anthropic, 2024-11-25)](https://www.anthropic.com/news/model-context-protocol)
- [Donating the Model Context Protocol and establishing the Agentic AI Foundation (Anthropic, 2025-12-09)](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
