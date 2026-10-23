---
layout: default
title: "[기술 소개] 함수 호출과 구조화된 출력: LLM이 JSON과 도구를 다루는 방식"
description: "OpenAI·Anthropic·Gemini 공식 문서로 도구 스키마(JSON Schema), 호출-실행-결과 반환 루프, strict 모드와 제약 디코딩, 병렬 호출, 도구 설계 팁, 프롬프트 인젝션에 따른 도구 오용 대응을 비교 정리했습니다."
date: 2026-10-24 00:16:00 +0900
categories: [tech]
---

# [기술 소개] 함수 호출과 구조화된 출력: LLM이 JSON과 도구를 다루는 방식

- **주요 출처:** [OpenAI Function calling](https://platform.openai.com/docs/guides/function-calling) · [OpenAI Structured model outputs](https://platform.openai.com/docs/guides/structured-outputs) · [Anthropic Tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) · [Anthropic Strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use) · [Anthropic Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) · [Gemini Function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- **한눈에 (2026-10-24 기준):** 세 공급자 모두 도구를 JSON Schema 계열 스키마로 정의하고, **모델은 도구를 직접 실행하지 않습니다.** 모델이 호출 요청을 구조화해 돌려주면 애플리케이션이 실행하고 결과를 다시 보냅니다. 스키마 준수를 보장하는 모드는 OpenAI와 Anthropic의 `strict: true`, Gemini의 `validated` 모드가 있습니다.
- **주의:** Anthropic의 일부 최신 모델(Claude Opus 5.5, Claude Sonnet 5.5, Claude Fable 5.1 등)은 특정 도구 호출을 강제하는 `tool_choice` 타입 `any`, `tool`을 지원하지 않아 400 오류를 냅니다(Anthropic 릴리스 노트 2026-09-01, 09-22, 09-28). 기존 코드를 옮길 때 확인이 필요합니다. 이 글의 코드는 공식 문서 예제를 옮긴 것이며 필자가 직접 실행하지는 않았습니다.

## 한 줄 요약

**함수 호출(function calling, tool calling)은 "모델이 무엇을 할지 구조화된 JSON으로 말하고, 실행은 애플리케이션이 하는" 계약이고, 구조화된 출력(structured outputs)은 그 JSON이 스키마를 벗어나지 않도록 디코딩 단계에서 막는 장치입니다.**

## 배경

LLM에게 외부 도구를 쓰게 하는 초기 방식은 프롬프트였습니다. [ReAct 소개](/papers/2026/10/24/react.html)에서 본 것처럼 2022년의 에이전트는 `Search[Milhouse]` 같은 자유 텍스트를 생성하고, 프로그램이 이를 정규식 등으로 파싱해 실행했습니다. 형식이 조금만 틀려도 파싱이 깨졌고, 도구를 언제 어떻게 쓸지는 퓨샷 예시에 의존했습니다. 같은 시기 [Toolformer 소개](/papers/2026/10/24/toolformer.html)는 도구 사용을 학습 데이터로 모델에 심는 길을 보여 줬습니다.

지금의 함수 호출 API는 이 두 흐름이 제품으로 굳은 형태입니다. OpenAI 문서는 함수 정의가 "모델이 학습한 문법으로" 시스템 메시지에 주입된다고 설명하고, Anthropic도 `tools`를 보내면 도구 정의로 특별한 시스템 프롬프트를 구성한다고 밝힙니다. 1차 자료로 확인한 주요 변화는 다음과 같습니다.

| 날짜 | 사건 | 출처 |
|---|---|---|
| 2023-11-06 | OpenAI, Chat Completions의 `functions` 파라미터를 `tools`로 대체 | OpenAI 변경 기록 |
| 2024-04-29 | OpenAI, `tool_choice: "required"` 추가 | OpenAI 변경 기록 |
| 2024-05-30 | Anthropic, 도구 사용 정식 출시(베타 헤더 불필요) | Anthropic 릴리스 노트 |
| 2024-06-06 | OpenAI, `parallel_tool_calls=false`로 병렬 호출 끄기 지원 | OpenAI 변경 기록 |
| 2024-08-06 | OpenAI, Structured Outputs 출시 | OpenAI 변경 기록 |
| 2024-10-03 | Anthropic, `disable_parallel_tool_use` 추가 | Anthropic 릴리스 노트 |
| 2025-11-14 | Anthropic, 구조화된 출력(JSON 출력, strict tool use) 베타 | Anthropic 릴리스 노트 |
| 2026-01-29 | Anthropic, 구조화된 출력 정식 출시, `output_format`을 `output_config.format`으로 이동 | Anthropic 릴리스 노트 |

## 핵심 내용

### 1. 도구 스키마: 이름, 설명, JSON Schema

세 공급자의 도구 정의는 거의 같은 뼈대를 씁니다.

| 필드 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| 종류 | `type: "function"` | (사용자 정의 도구는 생략) | `type: "function"` |
| 이름 | `name` | `name` | `name` |
| 설명 | `description` | `description` | `description` |
| 입력 스키마 | `parameters` (JSON Schema) | `input_schema` (JSON Schema) | `parameters` (OpenAPI 스키마의 부분집합) |
| 스키마 강제 | `strict: true` | `strict: true` | `tool_choice` 모드 `validated` |
| 기타 | `namespace`로 도구 묶기, `defer_loading` | `input_examples`, `defer_loading`, `cache_control` | |

OpenAI의 strict 모드 예제는 다음과 같습니다. 선택 필드인 `units`도 `required`에 넣고 타입에 `null`을 허용하는 방식에 주목할 만합니다.

```json
{
  "type": "function",
  "name": "get_weather",
  "description": "Retrieves current weather for the given location.",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City and country e.g. Bogotá, Colombia"
      },
      "units": {
        "type": ["string", "null"],
        "enum": ["celsius", "fahrenheit"],
        "description": "Units the temperature will be returned in."
      }
    },
    "required": ["location", "units"],
    "additionalProperties": false
  }
}
```

도구 정의는 공짜가 아닙니다. OpenAI는 호출 가능한 함수 정의가 컨텍스트 한도에 포함되고 입력 토큰으로 과금된다고 밝히고, Anthropic은 `tools`를 보내면 도구 정의와 별도로 도구 사용용 시스템 프롬프트가 추가된다고 모델별 토큰 수를 공개합니다(예: Claude Opus 5.5는 `tool_choice`가 `auto`·`none`일 때 286토큰).

### 2. 루프: 모델이 요청하고, 애플리케이션이 실행하고, 결과를 돌려준다

OpenAI 문서는 흐름을 5단계로 정리합니다. ① 도구 목록과 함께 요청 → ② 모델의 도구 호출 수신 → ③ 애플리케이션이 호출 입력으로 코드 실행 → ④ 도구 출력과 함께 두 번째 요청 → ⑤ 최종 응답(또는 추가 도구 호출) 수신. Anthropic 문서는 같은 구조를 `stop_reason`이 `"tool_use"`인 동안 도는 `while` 루프로 설명하고, Gemini 문서도 "모델은 함수를 직접 실행하지 않는다, 이름과 인자를 꺼내 애플리케이션에서 실행하라"고 명시합니다.

Anthropic 공식 예제(Python)의 핵심만 옮기면 이렇습니다.

```python
client = anthropic.Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and state, e.g. San Francisco, CA",
                }
            },
            "required": ["location"],
        },
    }
]
messages = [{"role": "user", "content": "What's the weather in San Francisco?"}]

# Claude replies with a tool_use block naming the tool and its arguments.
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    tools=tools,
    # Ask for at most one tool call in each turn.
    tool_choice={"type": "auto", "disable_parallel_tool_use": True},
    messages=messages,
)
tool_use = next(block for block in response.content if block.type == "tool_use")

# Run the tool, then send the result back in a tool_result block.
weather = "15 degrees Celsius, partly cloudy"  # your weather lookup goes here
messages += [
    {"role": "assistant", "content": response.content},
    {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": tool_use.id, "content": weather}
        ],
    },
]
followup = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "auto", "disable_parallel_tool_use": True},
    messages=messages,
)
```

공급자마다 메시지 모양은 다르지만 역할은 같습니다.

| 역할 | OpenAI (Responses API) | Anthropic | Gemini (Interactions API) |
|---|---|---|---|
| 모델의 호출 요청 | `function_call` 항목 (`call_id`, `name`, JSON 문자열 `arguments`) | `tool_use` 블록 (`id`, `name`, 객체 `input`), `stop_reason: "tool_use"` | `function_call` 단계 (`id`, `name`, `arguments`) |
| 애플리케이션의 결과 | `function_call_output` (`call_id`, `output`) | `tool_result` 블록 (`tool_use_id`, `content`, 실패 시 `is_error`) | `function_result` (`call_id`, `name`, `result`) |
| 추론 모델 주의점 | 도구 호출과 함께 나온 reasoning 항목도 결과와 함께 되돌려 보내야 함 | 사고(thinking) 블록을 그대로 되돌려 보냄 | SDK가 사고 서명(thought signature)을 자동 처리. 상태 없이 쓸 때는 받은 단계를 그대로 다시 보내야 함 |

OpenAI 문서는 결과를 보통 문자열(JSON, 오류 코드, 일반 텍스트 등 형식은 자유)로 넘기고, 반환값이 없는 함수(예: 이메일 전송)도 `"success"`처럼 성공·실패를 알리는 문자열을 돌려주라고 권합니다.

### 3. strict 모드와 제약 디코딩: 스키마를 "권고"에서 "보장"으로

strict 모드가 없으면 스키마는 모델에게 주는 강한 힌트일 뿐입니다. Anthropic 문서는 strict 없이 `passengers: int`를 요구해도 `"two"`나 `"2"`가 올 수 있다고 예를 듭니다. strict 모드는 이를 디코딩 단계에서 막습니다. Anthropic은 원리를 직접 밝힙니다. **JSON Schema를 문법(grammar)으로 컴파일하고, 모델의 토큰 샘플링을 스키마에 맞는 출력으로만 제한하는 "문법 제약 샘플링(grammar-constrained sampling)"**입니다. OpenAI도 strict 함수 호출이 내부적으로 Structured Outputs 기능을 활용한다고 설명합니다.

| 항목 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| 도구 입력 강제 | `strict: true` | `strict: true` | `tool_choice` 모드 `validated` |
| 최종 응답 강제 | `text.format`(Responses) 또는 `response_format`(Chat Completions)에 `json_schema` | `output_config.format`에 `json_schema` | 구조화된 출력(함수 호출과 병용 가능, Gemini 3 시리즈) |
| 스키마 요구 사항 | 모든 객체에 `additionalProperties: false`, 모든 필드를 `required`에, 선택 필드는 `null` 허용으로 | `additionalProperties: false` 필수 | OpenAPI 스키마 부분집합, 너무 크거나 깊은 스키마는 거부될 수 있음 |
| 기본값 | Responses는 가능하면 strict로 정규화, 불가하면 비strict로 대체. Chat Completions는 비strict | 비strict | `auto` |
| 대표 제한 | 객체 속성 총 5,000개, 중첩 10단계, enum 값 1,000개. `allOf`, `not`, `if/then/else` 미지원 | strict 도구 20개, 선택 파라미터 합계 24개, 유니언 타입 파라미터 16개. 재귀 스키마, `minimum`·`maxLength` 같은 수치·길이 제약 미지원. 컴파일 제한 시간 180초 | 문서에 수치 없음 |
| 첫 요청 지연 | 미세조정 모델은 새 스키마의 첫 요청에 처리 지연 | 새 스키마의 첫 요청에 문법 컴파일 지연, 컴파일된 문법은 마지막 사용 후 24시간 캐시 | 문서에 언급 없음 |

함수 호출과 구조화된 응답 중 무엇을 쓸지에 대해 OpenAI 문서의 기준은 명확합니다. **모델을 시스템의 도구, 함수, 데이터에 연결하는 것이면 함수 호출, 모델이 사용자에게 답하는 형식을 구조화하는 것이면 `json_schema` 응답 형식**입니다. 또 OpenAI는 JSON 모드(`json_object`)가 유효한 JSON만 보장하고 스키마 준수는 보장하지 않으므로, 가능하면 Structured Outputs를 쓰라고 권합니다.

"보장"에도 예외가 있습니다. Anthropic 문서는 세 가지를 듭니다. 안전상 거절(`stop_reason: "refusal"`)이면 거절 메시지가 스키마보다 우선하고, `max_tokens`에 걸리면 출력이 잘려 스키마를 어길 수 있으며, `enum`·`const` 문자열의 대소문자는 보장하지 않습니다. 그리고 OpenAI 문서는 **구조화된 출력도 내용상 실수를 할 수 있고**, 입력이 스키마와 전혀 무관하면 모델이 스키마를 채우려다 환각할 수 있다고 경고합니다. 형식이 맞는 것과 값이 맞는 것은 다른 문제입니다.

### 4. `tool_choice`와 병렬 호출

| 동작 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| 모델이 판단 (기본값) | `"auto"` | `{"type": "auto"}` | `auto` |
| 반드시 하나 이상 호출 | `"required"` | `{"type": "any"}` (일부 최신 모델 미지원) | `any` |
| 특정 도구 강제 | `{"type": "function", "name": ...}` | `{"type": "tool", "name": ...}` (일부 최신 모델 미지원) | `allowed_tools`에 하나만 지정하고 `any` |
| 호출 금지 | `"none"` | `{"type": "none"}` | `none` |
| 일부 도구만 허용 | `allowed_tools` | (도구 목록 자체로 제어) | `allowed_tools` |
| 병렬 호출 끄기 | `parallel_tool_calls: false` | `tool_choice` 안의 `disable_parallel_tool_use: true` | (함수 호출 문서에서 확인하지 못함) |

병렬 호출은 세 공급자 모두 지원합니다. Gemini는 독립적인 함수를 한 턴에 여러 개 부르는 병렬 호출과, 위치를 먼저 얻고 그 위치로 날씨를 묻는 식의 연쇄 호출(compositional function calling)을 구분해 설명합니다. Anthropic 문서는 실행 순서를 API가 정하지 않는다고 강조합니다. 읽기 전용이고 서로 독립적인 호출은 병렬로, 부작용이나 공유 상태, 순서 요구가 있는 호출은 순차로 실행하라고 권하고, 형식 규칙 두 가지를 둡니다. **모든 `tool_result`를 다음 사용자 메시지 하나에 모아 보내고, 그 메시지에서 텍스트보다 앞에 둘 것.** 앞선 호출이 실패해 일부를 실행하지 않았더라도 그 호출에 대해 `is_error: true` 결과를 돌려줘야 합니다.

OpenAI 문서에는 실무에서 걸리기 쉬운 단서도 있습니다. 미세조정 모델이 한 턴에 여러 함수를 부르면 그 호출들에는 strict 모드가 꺼집니다.

### 5. 도구 설계 팁: 세 문서가 공통으로 말하는 것

- **설명이 가장 중요합니다.** Anthropic은 상세한 설명을 "도구 성능에서 단연 가장 중요한 요소"라고 하며, 무엇을 하는지, 언제 써야 하고 언제 쓰지 말아야 하는지, 각 파라미터의 의미, 반환하지 않는 정보까지 도구당 3~4문장 이상 쓰라고 권합니다. OpenAI는 "인턴 테스트"를 제안합니다. 모델에게 준 정보만으로 사람 인턴이 함수를 제대로 쓸 수 있는지, 아니라면 인턴이 물을 질문의 답을 프롬프트에 넣으라는 것입니다.
- **잘못된 상태를 스키마로 막습니다.** OpenAI의 예처럼 `toggle_light(on: bool, off: bool)`은 둘 다 참인 잘못된 호출을 허용합니다. enum과 객체 구조로 표현할 수 없는 상태를 만들지 않는 것이 좋습니다.
- **모델이 채울 필요 없는 인자는 빼고, 코드가 할 일은 코드로.** 이미 아는 `order_id`를 모델에게 다시 채우게 하지 말고, 항상 연달아 부르는 함수는 하나로 합치라고 OpenAI는 권합니다. Anthropic도 `create_pr`, `review_pr`, `merge_pr`처럼 동작마다 도구를 만들기보다 `action` 파라미터를 둔 하나의 도구로 묶어 선택 모호성을 줄이라고 합니다.
- **도구 수를 작게 유지합니다.** OpenAI는 한 턴 시작 시점에 쓸 수 있는 함수를 20개 미만으로(가벼운 권고), Gemini는 활성 도구를 최대 10~20개로 유지하라고 권합니다. 도구가 많으면 세 공급자 모두 도구 검색(tool search)이나 지연 로딩으로 필요한 것만 불러오는 방식을 제공합니다.
- **이름에 네임스페이스를, 응답에는 신호만.** Anthropic은 여러 서비스에 걸친 도구라면 `github_list_prs`, `slack_send_message`처럼 서비스 접두어를 붙이고, 도구 응답에는 다음 단계 추론에 필요한 필드와 안정적인 식별자만 담으라고 합니다.
- **빠진 인자를 모델이 지어낼 수 있습니다.** Anthropic 문서는 위치 없이 "날씨 어때?"라고 물으면 모델(특히 Claude Sonnet)이 `"New York, NY"` 같은 값을 추측해 채울 수 있다고 예시합니다. 필수 정보가 사용자에게서만 나올 수 있다면, 비어 있을 때 되묻도록 설명이나 시스템 프롬프트에 적어 두는 편이 안전합니다.

### 6. 보안: 프롬프트 인젝션이 도구 오용이 되는 경로

함수 호출이 위험해지는 지점은 **모델이 신뢰할 수 없는 텍스트(웹 페이지, 이메일, 문서, 다른 도구의 결과)를 읽고 그 영향으로 도구를 호출할 때**입니다. OpenAI의 에이전트 안전 가이드는 프롬프트 인젝션(prompt injection)을 "신뢰할 수 없는 텍스트나 데이터 속 악의적 내용이 AI에 대한 지시를 덮어쓰려는 공격"으로 정의하고, 그 목적으로 이후 도구 호출을 통한 개인정보 유출, 의도와 다른 행동을 듭니다. OWASP의 LLM 위험 목록(2025)은 이를 "과도한 행위 능력(Excessive Agency)"으로 분류하며, 근본 원인을 **과도한 기능, 과도한 권한, 과도한 자율성** 세 가지로 정리합니다.

1차 자료의 권고를 실행 순서대로 모으면 다음과 같습니다.

1. **신뢰할 수 없는 입력을 높은 권한의 메시지에 넣지 않습니다.** OpenAI는 개발자 메시지가 사용자·어시스턴트 메시지보다 우선하므로, 신뢰할 수 없는 변수를 개발자 메시지에 직접 넣지 말고 사용자 메시지로 넘기라고 합니다.
2. **도구의 기능과 권한을 최소화합니다.** OWASP의 예처럼 문서를 읽기만 하면 되는데 수정·삭제까지 되는 확장을 붙이는 것이 "과도한 기능"입니다. 위험한 작업은 도구를 나누고, 위험한 쪽은 기본으로 노출하지 않습니다.
3. **구조화된 출력으로 데이터 흐름을 좁힙니다.** OpenAI는 단계 사이에 enum, 고정 스키마를 두면 공격자가 지시를 몰래 실어 나를 자유 텍스트 통로가 사라진다고 설명합니다. 다만 같은 문서는 이것이 위험을 "크게 줄이지만 완전히 없애지는 않는다"고 단서를 답니다.
4. **실행 전에 검증합니다.** Gemini 모범 사례는 "실행 전에 함수 호출을 검증하라"고 하고, MCP 명세도 서버가 모든 도구 입력을 검증하고 접근 제어와 호출 횟수 제한을 두어야 한다고 규정합니다. strict 모드는 형식을 보장할 뿐이므로, 금액 상한, 대상 계정, 경로 범위 같은 **의미 검증은 애플리케이션 코드의 몫**입니다.
5. **민감한 작업에는 사람의 확인을 둡니다.** OpenAI는 MCP 도구에 대해 읽기와 쓰기를 포함한 모든 작업에 승인을 켜 두라고 하고, MCP 명세는 도구 호출을 거부할 수 있는 사람이 항상 루프 안에 있어야 한다(SHOULD)고 적습니다.
6. **기록하고 평가합니다.** MCP 명세는 감사를 위한 도구 사용 로그를, OpenAI는 도구 호출 단위의 추적 평가(trace grading)를 권합니다.

## 비교: 공급자별 한눈에 보기

| 항목 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| 도구 정의 필드 | `parameters` | `input_schema` | `parameters` |
| 호출·결과 짝 맞추기 | `call_id` | `tool_use_id` | `call_id` |
| 스키마 보장 | `strict: true`(Responses는 가능하면 기본 적용) | `strict: true`(문법 제약 샘플링) | `validated` 모드 |
| 최종 응답 JSON | `text.format` / `response_format` | `output_config.format` | 구조화된 출력 |
| 강제 호출 | `required`, 특정 함수 지정 | `any`, `tool` (일부 최신 모델은 400 오류) | `any` + `allowed_tools` |
| 병렬 호출 | 지원, `parallel_tool_calls: false`로 끔 | 기본 켜짐, `disable_parallel_tool_use`로 끔 | 지원, 연쇄 호출도 별도 설명 |
| 자유 형식 입력 도구 | 커스텀 도구(CFG 문법: Lark, 정규식) | (해당 문서에 없음) | (해당 문서에 없음) |
| 공급자 실행 도구 | 웹 검색, 코드 실행, MCP 등 내장 도구 | 서버 도구(web_search, web_fetch, code_execution, tool_search) | Google 검색 등 내장 도구, 원격 MCP |

모든 항목은 2026-10-24에 각 공식 문서에서 확인한 내용입니다. 모델별로 지원 범위가 다를 수 있습니다.

## 한계와 논란

- **형식 보장은 의미 보장이 아닙니다.** strict 모드는 `passengers: 2`를 보장하지만 그 값이 맞는지는 보장하지 않습니다. OpenAI와 Anthropic 문서 모두 거절, 토큰 한도, 내용상 실수라는 예외를 명시합니다.
- **스키마 지원 범위가 공급자마다 다릅니다.** OpenAI strict는 재귀 스키마를 지원하지만 Anthropic은 지원하지 않고, Anthropic은 `minimum` 같은 수치 제약을 지원하지 않으며, Gemini는 OpenAPI 스키마의 부분집합을 씁니다. 여러 공급자를 쓰는 애플리케이션은 가장 좁은 공통 부분집합으로 스키마를 쓰거나, SDK의 스키마 변환 기능에 기대야 합니다. Anthropic SDK는 지원하지 않는 제약을 필드 설명으로 옮기는 변환을 제공합니다.
- **복잡한 스키마는 비쌉니다.** Anthropic 문서는 선택 파라미터 하나가 문법 상태 공간의 일부를 대략 두 배로 늘린다고 설명하며, 복잡도 한도에 걸리면 중요한 도구만 strict로 두라고 권합니다. "모든 도구를 strict로"라는 OpenAI의 권고와 실무에서 충돌할 수 있는 지점입니다.
- **API의 계약이 모델 세대마다 바뀝니다.** Anthropic의 강제 호출 미지원(일부 최신 모델), OpenAI의 GPT-6 Astra와 GPT-6.1 Sol이 도구 호출에 Responses API를 요구하는 점처럼, 같은 공급자 안에서도 모델을 바꾸면 도구 관련 코드가 깨질 수 있습니다.
- **도구 정의는 비용이자 캐시 키입니다.** 도구 정의는 입력 토큰으로 과금되고, 프롬프트 캐시의 맨 앞에 놓입니다. 도구를 요청마다 바꾸면 비용과 캐시 모두에서 손해를 봅니다([프롬프트 캐싱 소개](/tech/2026/10/24/prompt-caching.html) 참고).

## 인사이트

**왜 지금 중요한가: 함수 호출은 이제 "타입이 있는 인터페이스"입니다.** Anthropic 문서는 도구 사용을 "애플리케이션과 모델 사이의 계약"이라고 부르며, 이 계약 덕분에 모델이 "텍스트 생성기보다는 호출할 수 있는 함수처럼" 동작한다고 설명합니다. 그리고 "모델 출력에서 결정을 뽑으려고 정규식을 쓰고 있다면, 그 결정은 도구 호출이었어야 한다"는 기준을 제시합니다. 2022년 ReAct가 자유 텍스트를 파싱하던 시절과 비교하면, 지금의 변화는 세 단계로 정리할 수 있습니다. 도구 사용이 학습으로 모델에 들어갔고(공급자 문서의 "학습한 문법", "학습으로 내장된 스키마"), 호출이 구조화된 블록으로 분리됐으며, 그 구조를 strict 모드가 디코딩 단계에서 보장하게 됐습니다. 필자의 판단으로는, 이 덕분에 에이전트 개발의 어려움이 "모델이 형식을 지키게 하는 것"에서 "어떤 도구를 어떤 권한으로 주고, 결과를 어떻게 검증하는가"로 옮겨 갔습니다.

**실무에 주는 의미.** 첫째, **strict를 켜되 검증을 끄지 마세요.** strict는 파싱 오류와 재시도를 없애 주지만, 프롬프트 인젝션으로 조작된 "형식은 완벽한" 호출도 그대로 통과시킵니다. 실행 직전의 의미 검증(허용 범위, 대상, 금액)과 위험 작업의 사람 승인은 strict와 별개의 층으로 둬야 합니다. 둘째, **병렬 호출을 전제로 결과 처리 코드를 짜세요.** OpenAI 문서는 응답에 호출이 0개, 1개, 여러 개 올 수 있으니 여러 개라고 가정하라고 권하고, Anthropic은 병렬이 기본값입니다. 결과를 한 메시지에 모아 보내는 규칙을 어기면 이후 병렬성이 떨어진다고 Anthropic 문서는 설명합니다. 셋째, **도구 목록은 고정하고 허용 범위만 바꾸세요.** OpenAI의 `allowed_tools`는 도구 목록을 바꾸지 않고 호출 가능한 부분만 좁혀 프롬프트 캐시를 지키라는 목적으로 소개됩니다. 기능과 비용 양쪽에서 같은 결론이 나옵니다.

**블로그의 기존 글과의 연결.** [MCP 아키텍처 소개](/tech/2026/10/24/mcp-architecture.html)와 이 글은 같은 문제를 다른 층에서 다룹니다. 함수 호출은 **모델 API와 애플리케이션 사이**의 형식이고, MCP는 **애플리케이션과 도구 서버 사이**에서 도구 목록과 실행을 표준화하는 프로토콜입니다. MCP 명세(2025-06-18 버전)도 도구 입력을 `inputSchema`라는 JSON Schema로 정의하므로, MCP 서버의 도구는 거의 그대로 각 공급자의 함수 정의로 옮겨집니다. OpenAI와 Gemini가 원격 MCP를 내장 도구로, Anthropic이 MCP 커넥터를 제공하는 것도 이 호환성 위에 있습니다. 보안 권고도 겹칩니다. MCP 명세의 "서버는 모든 도구 입력을 검증하고, 클라이언트는 민감한 작업에 사용자 확인을 받아야 한다"는 규정은 앞의 6절과 같은 내용을 프로토콜 차원에서 요구한 것입니다. 한편 [Agent Skills 소개](/tech/2026/10/24/agent-skills-aaif.html)의 스킬은 "도구를 언제 어떤 순서로 쓰는가"라는 절차 지식을 담으므로, 도구 설명에 다 담기 어려운 사용 지침을 옮겨 둘 자리가 됩니다.

**한계와 반론.** 세 공급자의 형식이 비슷해 보여서 "어디서나 같은 도구 정의가 통한다"고 생각하기 쉽지만, 실제로는 스키마 부분집합, 강제 호출 지원, 병렬 호출 규칙, 추론 블록을 되돌려 보내는 방식이 모두 다릅니다. SDK의 스키마 변환 기능이나 MCP 같은 표준이 이 차이를 일부 흡수하지만, 필자의 판단으로는 strict 모드의 제약이나 거절 처리처럼 추상화로 감추기 어려운 차이가 남습니다. 또 OpenAI는 Responses API에서 strict를 기본으로 시도하는 반면 Anthropic은 strict 도구 수와 선택 파라미터에 한도를 두는 등, "스키마를 얼마나 강하게 강제할 것인가"에 대한 공급자들의 판단도 아직 수렴하지 않았습니다.

**앞으로 지켜볼 점.** (1) 강제 호출(`any`, `tool`)이 사라지는 흐름이 Anthropic의 다른 모델이나 다른 공급자로 번지는지. 그렇다면 "반드시 이 도구를 써라"는 요구는 strict와 프롬프트로 대신해야 합니다. (2) 수치·길이 제약 같은 의미 수준의 제약을 디코딩에서 보장하는 범위가 넓어지는지. 현재 Anthropic은 `minimum`, `maxLength`를 지원하지 않습니다. (3) 프롬프트 인젝션에 대한 모델 차원의 방어(OpenAI가 특정 모델을 간접 인젝션에 더 강하다고 권하는 것처럼)가 공개 평가로 검증되는지. 그 전까지는 권한 최소화와 실행 전 검증이 가장 확실한 방어입니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [OpenAI: Function calling](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI: Structured model outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [OpenAI: Safety in building agents](https://platform.openai.com/docs/guides/agent-builder-safety)
- [OpenAI: 변경 기록(Changelog)](https://platform.openai.com/docs/changelog)
- [Anthropic: Tool use with Claude](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Anthropic: How tool use works](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works)
- [Anthropic: Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [Anthropic: Strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use)
- [Anthropic: Parallel tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)
- [Anthropic: Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Anthropic: 릴리스 노트](https://platform.claude.com/docs/en/release-notes/overview)
- [Google: Gemini API Function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [OWASP: LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
- [Model Context Protocol 명세: Tools (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
