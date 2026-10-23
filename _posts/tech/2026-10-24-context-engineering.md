---
layout: default
title: "[기술 소개] 컨텍스트 엔지니어링: 프롬프트 엔지니어링 다음, 에이전트에게 무엇을 보여 줄 것인가"
description: "Anthropic의 컨텍스트 엔지니어링 글과 Claude·OpenAI·Gemini 공식 문서, Chroma의 Context Rot 보고서를 바탕으로 시스템 프롬프트, 도구 설계, 예시, 적시 검색, 압축, 메모리, 서브에이전트 기법과 실무 체크리스트를 정리했습니다."
date: 2026-10-24 00:08:00 +0900
categories: [tech]
---

# [기술 소개] 컨텍스트 엔지니어링: 프롬프트 엔지니어링 다음, 에이전트에게 무엇을 보여 줄 것인가

- **주요 출처:** [Effective context engineering for AI agents (Anthropic 엔지니어링 블로그, 2025-09-29)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Context Rot (Chroma 기술 보고서, 2025-07-14)](https://www.trychroma.com/research/context-rot) · [Lost in the Middle (arXiv:2307.03172)](https://arxiv.org/abs/2307.03172) · Claude 문서 [Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing), [Compaction](https://platform.claude.com/docs/en/build-with-claude/compaction), [Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) · [OpenAI Compaction 가이드](https://developers.openai.com/api/docs/guides/compaction) · [Gemini Long context 가이드](https://ai.google.dev/gemini-api/docs/long-context)
- **한눈에 (2026-10-24 기준):** Chroma가 18개 모델을 시험한 결과 입력이 길어질수록 단순한 과제에서도 성능이 꾸준히 떨어졌습니다. Anthropic과 OpenAI는 둘 다 대화가 길어지면 서버가 이전 내용을 요약해 주는 압축(compaction) 기능을 API에 넣었습니다(Anthropic은 베타). Anthropic의 오래된 도구 결과 삭제(context editing)와 메모리 도구를 함께 쓴 자체 평가에서는 기준 대비 39% 개선이 보고됐습니다(자체 측정).

## 한 줄 요약

**컨텍스트 엔지니어링은 "어떤 문장으로 지시할까"를 넘어, 에이전트가 매 단계에서 보는 토큰 전체(시스템 프롬프트, 도구, 예시, 검색 결과, 대화 기록, 메모)를 원하는 결과가 나올 가능성이 가장 높은 "작고 신호가 강한" 집합으로 관리하는 일입니다.**

## 배경

### 프롬프트에서 컨텍스트로

Anthropic 글은 컨텍스트 엔지니어링을 프롬프트 엔지니어링의 "자연스러운 다음 단계"로 봅니다. 프롬프트 엔지니어링이 지시문을 쓰고 다듬는 일이라면, 컨텍스트 엔지니어링은 추론 시점에 모델에 들어가는 모든 정보, 프롬프트가 아닌 것까지 고르고 유지하는 일입니다.

차이가 커진 이유는 에이전트입니다. 한 번 묻고 답하는 분류·생성 과제에서는 좋은 프롬프트 하나면 충분했습니다. 하지만 도구를 반복 호출하며 몇 시간씩 일하는 에이전트는 매 턴 새 데이터(도구 결과, 파일 내용, 오류 메시지)를 만들어 내고, 그중 무엇을 다음 턴에 남길지 계속 정해야 합니다. 글은 이를 "컨텍스트를 모델에 넘길 때마다 일어나는 반복적인 큐레이션"이라고 표현합니다.

### 왜 "많이 넣으면 된다"가 아닌가

컨텍스트 창이 수십만에서 백만 토큰으로 커졌는데도 이 문제가 중요한 이유는, 긴 입력이 공짜가 아니라는 증거가 쌓였기 때문입니다.

| 출처 | 확인한 것 |
|---|---|
| [Lost in the Middle](https://arxiv.org/abs/2307.03172) (Liu et al., 2023) | 다문서 질의응답과 키-값 검색에서 관련 정보가 입력의 **처음이나 끝**에 있을 때 성능이 가장 높고, **중간**에 있으면 크게 떨어짐. 긴 컨텍스트용 모델에서도 마찬가지 |
| [Context Rot](https://www.trychroma.com/research/context-rot) (Chroma, 2025-07-14) | Anthropic·OpenAI·Google·Alibaba의 18개 모델에서, 입력 길이가 늘수록 성능이 일관되게 떨어짐. 방해 문장(distractor) 하나만 있어도 성능 하락. 대화 질의응답 LongMemEval에서는 관련 부분만 담은 약 300토큰 프롬프트가 약 11.3만 토큰 전체 프롬프트보다 모든 모델에서 훨씬 좋았음 |
| [Gemini Long context 가이드](https://ai.google.dev/gemini-api/docs/long-context) | 한 개의 정보를 찾는 시험은 정확도가 높지만, 여러 정보를 동시에 찾아야 하면 "같은 정확도로 동작하지 않는다" |

Anthropic 글은 여기에 구조적인 이유를 붙입니다. 트랜스포머에서는 모든 토큰이 다른 모든 토큰에 어텐션하므로 토큰이 n개면 n²개의 쌍 관계가 생기고, 컨텍스트가 길어질수록 이 관계를 붙잡는 능력이 "얇게 펴진다"는 것입니다. 또 학습 데이터에는 짧은 시퀀스가 더 흔해 긴 범위의 의존 관계를 다룰 경험이 적다고 설명합니다. 그래서 컨텍스트를 사람의 작업 기억처럼 **한정된 "어텐션 예산(attention budget)"**으로 다루라고 권합니다. 이 n² 구조의 출처인 트랜스포머 원 논문은 같은 날 쓴 [Attention Is All You Need 소개](/papers/2026/10/24/transformer.html)에서 다뤘습니다.

한 가지 짚어 둘 점이 있습니다. Chroma 보고서의 성능 저하는 바늘 찾기 변형, 반복 단어 따라 쓰기 같은 **통제된 실험 과제**에서 측정된 것이고, 하락 폭은 모델과 과제마다 달랐습니다. "context rot"은 실제 에이전트 작업에서 같은 크기로 나타난다는 측정이 아니라, 길이가 늘면 성능이 나빠지는 방향성이 모든 모델에서 관찰됐다는 의미로 읽는 것이 정확합니다.

## 핵심 내용

Anthropic 글의 지도 원칙은 한 문장입니다. **원하는 결과가 나올 가능성을 최대화하는, 가능한 가장 작은 고신호(high-signal) 토큰 집합을 찾아라.** 아래는 이 원칙을 컨텍스트의 구성 요소별로 적용한 것입니다.

### 1. 시스템 프롬프트: "적절한 고도"에서 쓰기

글은 시스템 프롬프트가 두 가지 실패 사이의 "적절한 고도(right altitude)"에 있어야 한다고 말합니다.

| 너무 낮음 | 적절한 고도 | 너무 높음 |
|---|---|---|
| 복잡한 if-else 규칙을 하드코딩. 깨지기 쉽고 유지보수가 어려움 | 행동을 이끌 만큼 구체적이되, 모델이 판단할 여지를 남긴 강한 휴리스틱 | 막연한 지침이나 공유된 맥락이 있다고 가정. 모델이 구체적인 신호를 받지 못함 |

실무 요령도 구체적입니다. 배경, 지시, 도구 안내, 출력 형식처럼 섹션을 나누고 XML 태그나 마크다운 제목으로 구분하되, 모델이 좋아질수록 형식의 중요성은 줄어들 수 있다고 덧붙입니다. 그리고 **가장 좋은 모델로 최소한의 프롬프트부터 시작해, 관찰된 실패에 맞춰 지시와 예시를 추가하라**고 권합니다. "최소"가 "짧음"을 뜻하지는 않는다는 단서도 붙어 있습니다.

긴 문서를 넣을 때는 배치도 중요합니다. Claude 공식 문서는 2만 토큰 이상의 긴 자료를 **프롬프트 위쪽**에, 질문을 **맨 끝**에 두라고 권하며 이렇게 했을 때 내부 시험에서 응답 품질이 최대 30% 올랐다고 밝힙니다. Gemini 가이드도 질문을 긴 컨텍스트 뒤에 두면 성능이 좋아진다고 적고 있습니다. Lost in the Middle의 "처음과 끝이 강하다"는 결과와 같은 방향입니다.

### 2. 도구: 에이전트와 세계 사이의 계약

도구는 정의(이름, 설명, 스키마)가 매 턴 컨텍스트에 들어가고, 결과도 컨텍스트로 돌아오므로 두 번 비용을 냅니다. Anthropic 글은 도구가 토큰 효율적인 정보를 돌려주고 효율적인 행동을 유도해야 한다며, 가장 흔한 실패로 **기능이 겹치는 비대한 도구 모음**을 꼽습니다. 판단 기준은 이렇습니다. "사람 엔지니어도 이 상황에서 어떤 도구를 써야 할지 확실히 말할 수 없다면, 에이전트도 마찬가지다."

같은 회사의 [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)(2025-09-11)는 더 구체적입니다.

- **API 엔드포인트를 그대로 감싸지 말 것.** 주소록이라면 전체를 돌려주는 `list_contacts`보다 `search_contacts`가 낫다고 예를 듭니다.
- **응답 형식을 고르게 할 것.** `response_format` 인자로 "concise"와 "detailed"를 선택하게 한 Slack 예에서, 상세 응답은 206토큰, 간결 응답은 72토큰이었습니다.
- **토큰 상한을 둘 것.** 페이지네이션, 범위 선택, 필터, 잘라내기를 조합하라고 권하며, Claude Code는 기본적으로 도구 응답을 25,000토큰으로 제한한다고 밝힙니다.
- **알아보기 쉬운 식별자를 쓸 것.** 암호 같은 UUID보다 자연어 이름이 검색 과제에서 환각을 줄였다고 합니다.

MCP 서버를 만든다면 이 원칙이 그대로 적용됩니다. MCP 명세가 `tools/list`의 순서를 고정하라고 권하는 것도 도구 정의가 매번 같은 모양으로 컨텍스트에 들어가야 캐시가 맞기 때문입니다([MCP 구조 해설](/tech/2026/10/24/mcp-architecture.html) 참고).

### 3. 예시: 규칙 목록 대신 대표 사례 몇 개

few-shot 예시는 여전히 강력한 모범 사례지만, Anthropic 글은 모든 예외 상황을 규칙처럼 나열해 프롬프트에 채워 넣는 것을 경계합니다. 대신 기대하는 행동을 잘 보여 주는 **다양하고 대표적인(canonical) 예시 몇 개**를 고르라고 합니다. 글의 표현으로는 LLM에게 예시는 "천 마디 말의 가치가 있는 그림"입니다. Claude 문서는 구체적으로 3~5개를 권하고, `<example>` 태그로 감싸 지시와 구분하라고 안내합니다.

### 4. 검색: 미리 넣기 대신 "적시(just-in-time)"에 꺼내 보기

많은 AI 애플리케이션은 추론 전에 임베딩 검색으로 관련 문서를 찾아 미리 넣습니다. Anthropic 글은 에이전트에게는 다른 방식이 점점 유리하다고 말합니다. 파일 경로, 저장된 쿼리, 링크 같은 **가벼운 식별자만 들고 있다가 필요할 때 도구로 불러오는 것**입니다.

예로 든 것이 Claude Code입니다. 큰 데이터를 다룰 때 전체를 컨텍스트에 올리지 않고, 목적에 맞는 쿼리를 쓰고 결과를 저장한 뒤 `head`, `tail` 같은 명령으로 필요한 부분만 봅니다. 사람이 모든 정보를 외우지 않고 파일 시스템, 받은편지함, 북마크로 찾아보는 것과 같습니다. 이때 폴더 구조, 이름 규칙, 타임스탬프 같은 **메타데이터 자체가 신호**가 됩니다. 글의 예처럼 `tests` 폴더의 `test_utils.py`와 `src/core_logic/`의 같은 이름 파일은 다른 의미입니다.

대가도 분명합니다. 실행 중 탐색은 미리 계산한 검색보다 느리고, 좋은 도구와 휴리스틱이 없으면 에이전트가 막다른 길에 컨텍스트를 낭비합니다. 그래서 글은 **혼합 전략**을 권합니다. Claude Code는 `CLAUDE.md` 파일을 처음부터 컨텍스트에 넣고, 나머지는 `glob`, `grep`으로 그때그때 찾습니다. 오래된 인덱스나 복잡한 구문 트리 문제를 피하는 방식이라고 설명합니다. 블로그의 [Agent Skills 글](/tech/2026/10/24/agent-skills-aaif.html)에서 다룬 3단계 점진적 공개(이름과 설명만 먼저, 본문은 쓸 때, 참고 자료는 필요할 때)도 같은 원리를 표준 형식으로 굳힌 것입니다.

### 5. 압축: 긴 작업의 첫 번째 지렛대

몇 시간짜리 작업은 결국 창을 넘습니다. Anthropic 글은 더 큰 창을 기다리는 것만으로는 컨텍스트 오염과 관련성 문제가 해결되지 않는다며, 장기 작업용 기법 세 가지(압축, 구조화된 노트, 서브에이전트)를 제시합니다. 그 첫째가 **압축(compaction)**, 즉 창이 거의 찬 대화를 요약해 새 창을 그 요약으로 시작하는 것입니다.

Claude Code의 예에서는 대화 기록을 요약할 때 아키텍처 결정, 해결되지 않은 버그, 구현 세부 사항은 남기고 중복된 도구 출력과 메시지는 버린 뒤, 요약과 함께 **가장 최근에 접근한 파일 5개**를 붙여 이어 갑니다. 핵심은 무엇을 남길지 고르는 것이며, 글은 압축 프롬프트를 복잡한 실제 기록으로 조정하되 **먼저 재현율(빠뜨리지 않기)을 최대화하고 그다음 정밀도(군더더기 빼기)를 올리라**고 권합니다. 가장 가벼운 압축은 **도구 결과 지우기**입니다. 한참 전에 호출한 도구의 원본 출력은 이미 쓰였다면 다시 볼 일이 거의 없습니다.

공급자들은 이를 API 기능으로 내놓았습니다(2026-10-24 기준).

| 기능 | 공급자 | 동작 | 주의 |
|---|---|---|---|
| Context editing: `clear_tool_uses_20250919` | Anthropic (베타, `context-management-2025-06-27`) | 입력이 `trigger`(기본 10만 토큰)를 넘으면 오래된 도구 결과부터 지우고 최근 `keep`(기본 3개) 쌍만 남김. `exclude_tools`로 예외 지정 | 지우면 그 지점부터 프롬프트 캐시가 무효화되므로 `clear_at_least`로 한 번에 충분히 지우라고 안내 |
| Context editing: `clear_thinking_20251015` | Anthropic (베타) | 이전 턴의 thinking 블록을 지울지, 몇 턴을 남길지 지정 | 남기면 캐시 유지, 지우면 그 지점에서 캐시 무효화 |
| Compaction | Anthropic (베타, 요청 시 압축은 `compact-2026-09-04`) | 서버에서 Claude가 이전 턴을 요약한 블록으로 대체. 요청 시 압축과 토큰 임계값 압축 두 방식 | 문서는 긴 대화의 주된 전략으로 압축을 권하고, 세밀한 제어가 필요할 때 context editing을 쓰라고 함 |
| Compaction | OpenAI Responses API | `context_management`에 `compact_threshold`를 주면 임계값을 넘을 때 서버가 압축. 또는 `/responses/compact`를 직접 호출 | 압축 결과는 사람이 읽을 수 없는 암호화된 항목. 반환된 창을 임의로 잘라내지 말라고 안내 |
| Context caching | Google Gemini | 긴 컨텍스트를 반복 질의할 때의 주된 최적화로 소개 | 압축이 아니라 같은 입력의 재전송 비용을 줄이는 기능 |

아래는 Claude 문서의 도구 결과 지우기 최소 예제입니다. 전략 타입만 지정하면 나머지는 기본값이 쓰입니다. **필자는 API 키 없이 작성해 이 요청을 실행하지 않았고**, 문서의 cURL 예제를 그대로 옮겼습니다.

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -H "anthropic-beta: context-management-2025-06-27" \
  -d '{
    "model": "claude-opus-5-5",
    "max_tokens": 4096,
    "messages": [
      { "role": "user", "content": "Search for recent developments in AI" }
    ],
    "tools": [
      { "type": "web_search_20250305", "name": "web_search" }
    ],
    "context_management": {
      "edits": [ {"type": "clear_tool_uses_20250919"} ]
    }
  }'
```

### 6. 노트와 메모리: 컨텍스트 밖에 적어 두기

두 번째 장기 기법은 **구조화된 노트(agentic memory)**입니다. 에이전트가 진행 상황을 컨텍스트 창 밖의 파일에 주기적으로 적고, 나중에 다시 읽어 옵니다. Claude Code의 할 일 목록이나 `NOTES.md` 파일이 그 예입니다. Anthropic 글은 Claude가 포켓몬 게임을 하는 실험에서, 메모리에 대한 별도 지시 없이도 수천 단계에 걸친 집계, 탐험한 지역 지도, 전투 전략을 노트로 남기고 컨텍스트가 초기화된 뒤에도 노트를 읽고 몇 시간짜리 작업을 이어 갔다고 소개합니다.

이를 API로 제공하는 것이 Claude의 [메모리 도구](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)(`memory_20250818`)입니다. 핵심은 **클라이언트 쪽 도구**라는 점입니다. Claude는 `/memories` 아래 파일에 대해 `view`, `create`, `str_replace`, `insert`, `delete`, `rename`을 요청할 뿐이고, 실제 저장은 개발자의 애플리케이션이 맡습니다. 그래서 문서는 경로 조작 공격(예: `/memories/../../secrets.env`)을 막는 일이 **개발자의 책임**이라고 경고하며, `pathlib`의 `resolve()`와 `relative_to()`를 쓰라고 권합니다. 아래는 그 권고대로 필자가 쓴 경로 검사 함수이며, 직접 실행해 결과를 확인했습니다(Python 3.12, 표준 라이브러리만 사용).

```python
from pathlib import Path
from urllib.parse import unquote

BASE = Path("./memory").resolve()          # /memories 가 실제로 매핑될 디렉터리

def to_real_path(virtual: str) -> Path:
    """Claude가 보낸 /memories/... 경로를 실제 경로로 바꾸고, 밖으로 나가면 거부한다."""
    v = unquote(virtual)                    # %2e%2e%2f 같은 인코딩 우회 대비
    if v != "/memories" and not v.startswith("/memories/"):
        raise ValueError(f"memory root 밖의 경로: {virtual}")
    real = (BASE / v.removeprefix("/memories").lstrip("/")).resolve()
    real.relative_to(BASE)                  # BASE 밖이면 ValueError
    return real

for p in ["/memories/progress.md", "/memories/../../secrets.env",
          "/memories/%2e%2e/%2e%2e/etc/passwd", "/etc/passwd"]:
    try:
        print("OK  ", p, "->", to_real_path(p).relative_to(BASE.parent))
    except ValueError as e:
        print("DENY", p)
```

```
OK   /memories/progress.md -> memory/progress.md
DENY /memories/../../secrets.env
DENY /memories/%2e%2e/%2e%2e/etc/passwd
DENY /etc/passwd
```

이 함수는 경로 검사만 보여 주는 예이며, 실제 메모리 핸들러(각 명령의 구현, 파일 크기 상한, 오래된 메모리 정리)는 문서의 SDK 도우미(`BetaLocalFilesystemMemoryTool` 등)를 참고해야 합니다.

메모리는 압축과 짝을 이룹니다. 메모리 도구 문서는 긴 에이전트라면 둘 다 쓰라고 권합니다. 압축은 활성 컨텍스트를 작게 유지하고, 메모리는 요약을 거쳐도 살아남아야 하는 정보를 보존한다는 것입니다. Claude 프롬프팅 문서는 여러 창에 걸친 작업에서 `progress.txt` 같은 자유 형식 진행 노트, `tests.json` 같은 구조화된 상태 파일, 그리고 git 기록을 함께 쓰라고 권하며, 최신 모델은 파일 시스템에서 상태를 잘 복원하므로 경우에 따라 **압축 대신 새 창으로 시작하는 편이 나을 수 있다**고까지 적고 있습니다.

### 7. 서브에이전트: 깨끗한 창에서 탐색하고 요약만 돌려받기

세 번째 장기 기법은 **서브에이전트**입니다. 주 에이전트는 큰 계획을 들고 있고, 특정 조사는 깨끗한 컨텍스트 창을 가진 서브에이전트에게 맡깁니다. Anthropic 글에 따르면 서브에이전트는 탐색에 수만 토큰을 쓰더라도 **1,000~2,000토큰 정도로 압축한 요약**만 돌려줍니다. 세부 탐색의 잡음이 주 에이전트의 컨텍스트를 오염시키지 않는 것이 핵심입니다.

같은 회사의 [멀티 에이전트 리서치 시스템](https://www.anthropic.com/engineering/multi-agent-research-system) 글(2025-06-13)은 Opus 4 주 에이전트와 Sonnet 4 서브에이전트 구성이 단일 Opus 4보다 내부 리서치 평가에서 90.2% 더 좋았다고 보고했습니다. 대가도 함께 밝혔습니다. 에이전트는 일반 채팅보다 약 4배, 멀티 에이전트 시스템은 약 15배의 토큰을 쓰며, 모든 에이전트가 같은 컨텍스트를 공유해야 하는 작업이나 병렬화할 부분이 적은 대부분의 코딩 작업에는 잘 맞지 않는다고 적었습니다.

Anthropic 글은 세 기법의 쓰임을 이렇게 나눕니다. 주고받기가 많은 대화형 작업에는 압축, 명확한 이정표가 있는 반복 개발에는 노트, 병렬 탐색이 이득인 복잡한 조사에는 멀티 에이전트입니다.

## 실무에서 쓰는 법: 체크리스트

공식 자료의 권고를 필자가 실무 순서로 묶었습니다.

**시스템 프롬프트와 예시**

- [ ] 가장 좋은 모델로 최소 프롬프트부터 시작해, 실제로 관찰한 실패에만 지시를 추가했는가
- [ ] if-else 규칙 나열 대신 판단 기준(휴리스틱)을 썼는가, 반대로 "알아서 잘" 같은 막연한 지시만 있지는 않은가
- [ ] 긴 자료는 위에, 질문은 맨 아래에 두었는가
- [ ] 예외 목록 대신 다양하고 대표적인 예시 3~5개를 태그로 구분해 넣었는가

**도구**

- [ ] 사람이 봐도 어떤 도구를 쓸지 헷갈리는 겹치는 도구가 없는가
- [ ] 목록 전체를 돌려주는 도구 대신 검색·필터·페이지네이션을 지원하는가
- [ ] 도구 응답에 토큰 상한이 있고, 간결/상세 형식을 고를 수 있는가
- [ ] 도구 정의의 순서와 내용이 요청마다 바뀌지 않아 캐시가 유지되는가

**검색**

- [ ] 처음부터 넣어야 하는 것(프로젝트 규칙, `CLAUDE.md` 같은 안내 파일)과 필요할 때 찾을 것(나머지 파일, 데이터)을 구분했는가
- [ ] 에이전트가 경로, 이름, 날짜 같은 메타데이터로 관련성을 판단할 수 있게 자료가 정리돼 있는가

**긴 작업**

- [ ] 대화형 장기 작업에 압축을 켰고, 요약 프롬프트가 결정 사항과 미해결 문제를 빠뜨리지 않는지 실제 기록으로 확인했는가
- [ ] 도구를 많이 쓰는 에이전트에 오래된 도구 결과 지우기를 적용했고, 캐시 무효화 비용을 감안해 한 번에 충분히 지우게 했는가
- [ ] 압축 뒤에도 살아남아야 할 정보(진행 상황, 테스트 상태)를 파일이나 메모리에 적게 했는가
- [ ] 메모리 저장소의 경로 검사, 크기 상한, 만료 정리를 구현했는가
- [ ] 서브에이전트는 병렬로 나눌 수 있고 공유 상태가 적은 조사에만 쓰고, 돌려받는 요약의 길이를 정했는가

## 한계와 논란

- **효과 수치의 상당수가 공급자 자체 측정입니다.** 메모리 도구와 context editing을 함께 쓴 39% 개선, context editing 단독 29% 개선, 100턴 웹 검색 평가에서 토큰 84% 절감은 모두 Anthropic의 [context management 발표](https://claude.com/resources/articles/context-management)(2025-09-29)에 나온 내부 평가 결과이며, 평가 세트는 공개되지 않았습니다. 긴 문서 질문을 맨 끝에 둘 때의 "최대 30%"도 Claude 문서의 내부 시험 결과입니다.
- **"Context rot"의 근거는 통제된 실험입니다.** Chroma 보고서는 18개 모델 모두에서 길이에 따른 하락을 보였지만, 과제가 바늘 찾기 변형과 반복 단어 따라 쓰기처럼 인위적입니다. 실제 에이전트 작업에서 몇 토큰부터 얼마나 나빠지는지는 작업과 모델에 따라 직접 측정해야 합니다.
- **압축은 정보를 잃습니다.** Anthropic 글 스스로 지나치게 공격적인 압축은 나중에 중요해질 미묘한 맥락을 잃게 한다고 경고합니다. OpenAI의 압축 결과는 암호화된 불투명 항목이라, 무엇이 남고 무엇이 빠졌는지 개발자가 직접 확인할 수 없습니다.
- **서브에이전트에 대한 반론이 있습니다.** Cognition의 Walden Yan은 [Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents)(2025-06-12)에서 "컨텍스트를 공유하라, 개별 메시지가 아니라 전체 에이전트 기록을 공유하라"와 "행동에는 암묵적 결정이 담기고, 충돌하는 결정은 나쁜 결과를 낳는다"는 원칙을 내세우며, 서로의 맥락을 모르는 병렬 서브에이전트가 충돌하는 가정을 하게 된다고 주장했습니다. Anthropic 리서치 글도 공유 컨텍스트가 필요한 작업과 대부분의 코딩에는 멀티 에이전트가 잘 맞지 않는다고 인정한 만큼, 두 주장은 적용 범위의 차이로 보는 것이 자연스럽습니다.
- **메모리는 새 공격 표면입니다(필자 의견).** 메모리 파일은 다음 세션의 컨텍스트로 자동으로 다시 읽힙니다. 한 번 들어온 프롬프트 인젝션이나 잘못된 사실이 메모리에 적히면 세션을 넘어 지속될 수 있습니다. 메모리 도구 문서는 민감 정보 필터링, 크기 상한, 만료 정리를 권하지만, 메모리 내용의 무결성 검증까지 다루지는 않습니다.

## 인사이트

**왜 지금 중요한가.** 프롬프트 엔지니어링이 "한 번의 호출"을 최적화했다면, 컨텍스트 엔지니어링은 "수백 번의 호출로 이뤄진 작업"을 최적화합니다. 이 차이가 커진 계기는 모델이 아니라 작업 길이입니다. 같은 모델이라도 도구를 50번 부르는 에이전트에서는 50번째 턴의 컨텍스트가 대부분 지난 도구 결과로 채워집니다. 필자의 판단으로는 2025~2026년 공급자들이 내놓은 기능(context editing, 서버 측 압축, 메모리 도구, 도구 검색)은 모두 같은 문제, 즉 **에이전트 루프에서 컨텍스트가 한 방향으로만 쌓이는 문제**에 대한 답입니다. 그리고 그 답의 방향은 "더 큰 창"이 아니라 "덜 넣기"로 수렴하고 있습니다.

**실무에 주는 의미: 성능 문제를 의심할 순서가 바뀐다.** 에이전트가 이상하게 행동할 때 많은 팀이 먼저 시스템 프롬프트 문구를 고칩니다. 하지만 위 자료들을 종합하면, 장기 작업에서는 그 턴에 실제로 모델이 본 컨텍스트 전체를 덤프해서 보는 것이 먼저입니다. 오래된 도구 결과가 대부분을 차지하고 있지는 않은지, 겹치는 도구 정의가 수십 개 붙어 있지는 않은지, 결정적인 정보가 긴 컨텍스트 한가운데 묻혀 있지는 않은지를 확인한 뒤에 프롬프트를 고치는 편이 효율적입니다. 이를 위해 에이전트 기록에 "매 턴의 입력 토큰 구성(시스템, 도구 정의, 도구 결과, 대화)"을 남겨 두기를 권합니다.

**블로그의 기존 글과의 연결.** 이번 주 글들은 같은 문제를 다른 층에서 다룹니다. [트랜스포머 원 논문](/papers/2026/10/24/transformer.html)의 O(n² · d)는 "토큰 하나를 더 넣는 비용이 0이 아니다"의 출발점이고, [MCP](/tech/2026/10/24/mcp-architecture.html)는 도구 정의와 결과가 컨텍스트로 들어오는 통로이며, [Agent Skills](/tech/2026/10/24/agent-skills-aaif.html)의 점진적 공개는 적시 검색을 표준 형식으로 만든 것입니다. [Chain-of-Thought 소개](/papers/2026/10/24/chain-of-thought.html)에서 다룬 추론 모델의 thinking도 컨텍스트를 쓰므로, Claude가 이전 턴의 thinking 블록을 지우는 전략(`clear_thinking_20251015`)을 따로 둔 것은 자연스러운 귀결로 보입니다.

**한계와 반론.** "컨텍스트 엔지니어링"이 새로운 기술인지, 정보 검색과 캐시 설계, 좋은 API 설계라는 오래된 원칙의 새 이름인지는 따져 볼 만합니다. 필자는 원칙 자체는 익숙하지만 **최적화 대상이 사람이 아니라 모델의 어텐션**이라는 점이 새롭다고 봅니다. 그래서 측정 방법도 달라야 하는데, 현재 공개된 근거는 공급자 내부 평가와 인위적 벤치마크가 대부분입니다. 같은 기법(예: 압축 대 새 창으로 재시작)의 효과가 작업마다 반대로 나올 수 있으므로, 공식 권고를 그대로 적용하기보다 자기 작업의 실제 기록으로 비교해 보는 것이 안전합니다.

**앞으로 지켜볼 점.** (1) 압축의 품질을 개발자가 검증할 방법이 생기는지. 특히 불투명한 압축 결과에서 무엇이 빠졌는지 알 수 있는지. (2) 모델이 스스로 컨텍스트 잔량을 인식하고 관리하는 기능이 일반화되는지. Claude 문서는 일부 모델이 남은 토큰 예산을 추적하는 "context awareness"를 갖췄다고 밝히고 있습니다. (3) 메모리의 무결성과 출처를 다루는 공통 규약이 나오는지. 세 번째가 나오기 전까지는 메모리 파일을 코드처럼 검토 대상에 넣는 것이 좋겠습니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [Effective context engineering for AI agents (Anthropic, 2025-09-29)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Writing effective tools for AI agents (Anthropic, 2025-09-11)](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [How we built our multi-agent research system (Anthropic, 2025-06-13)](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Managing context on the Claude Developer Platform (Anthropic, 2025-09-29)](https://claude.com/resources/articles/context-management)
- Claude 문서: [Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing) · [Compaction](https://platform.claude.com/docs/en/build-with-claude/compaction) · [Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) · [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [OpenAI: Compaction 가이드](https://developers.openai.com/api/docs/guides/compaction)
- [Gemini API: Long context](https://ai.google.dev/gemini-api/docs/long-context)
- [Context Rot: How Increasing Input Tokens Impacts LLM Performance (Chroma, 2025-07-14)](https://www.trychroma.com/research/context-rot)
- [Lost in the Middle: How Language Models Use Long Contexts (arXiv:2307.03172)](https://arxiv.org/abs/2307.03172)
- [Don't Build Multi-Agents (Cognition, 2025-06-12)](https://cognition.com/blog/dont-build-multi-agents)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
