---
layout: default
title: "[기술 소개] Claude Haiku 5.5: 서브에이전트용 소형 모델과 캐시 가격이 바꾸는 에이전트 비용"
description: "Claude Haiku 5.5의 가격 구조(100K 토큰 경계), 벤치마크 측정 조건, 4.5에서 옮길 때 깨지는 설정, 같은 날 내린 Sonnet 5.5 캐시 읽기 가격을 정리하고 GPT-6 Luna·Gemini Flash와 비교해 오케스트레이터-서브에이전트 비용을 계산했습니다."
date: 2026-10-24 00:44:00 +0900
categories: [tech]
---

# [기술 소개] Claude Haiku 5.5: 서브에이전트용 소형 모델과 캐시 가격이 바꾸는 에이전트 비용

- **발표:** Anthropic, 2026년 10월 7일
- **원문:** [공식 발표](https://www.anthropic.com/news/claude-haiku-5-5) · [모델 문서](https://platform.claude.com/docs/en/models/haiku-5-5/overview) · [가격 문서](https://platform.claude.com/docs/en/about-claude/pricing) · [시스템 카드(PDF)](https://www.anthropic.com/document/claude-haiku-5-5-system-card)
- **한눈에 (2026-10-24 가격 문서 기준):** 모델 ID `claude-haiku-5-5`. 프롬프트 100,000토큰 이하에서 입력 $0.10, 출력 $0.50, 캐시 읽기 $0.01(모두 100만 토큰당). Anthropic은 Haiku 4.5보다 평균 약 75% 싸다고 밝혔습니다. 같은 날 Sonnet 5.5의 캐시 읽기 가격을 $0.20에서 $0.10으로 내렸습니다.
- **주의:** (1) 프롬프트가 100,000토큰을 넘는 요청은 **캐시 읽기를 포함해 모든 단가가 5배**가 됩니다. (2) 같은 텍스트가 Haiku 4.5보다 약 30% 많은 토큰으로 계산됩니다. (3) `temperature`·`top_p`·`top_k`, 응답 미리 채우기(prefill), `budget_tokens`를 보내면 오류가 납니다. (4) 벤치마크는 모두 Anthropic 자체 측정이며, 최대 effort 조건입니다.

## 한 줄 요약

**Haiku 5.5는 "큰 모델이 지휘하고 작은 모델이 잡일을 맡는" 에이전트 구조에서 작은 모델 쪽 비용을 Haiku 4.5의 약 10분의 1 단가로 낮추면서, 컴퓨터 사용과 터미널 작업 점수를 크게 끌어올린 소형 모델입니다.** 다만 100K 토큰 경계의 가격 절벽과 바뀐 토크나이저 때문에, 실제 절감폭은 작업의 컨텍스트 길이와 캐시 구조에 따라 크게 달라집니다.

## 배경

에이전트 시스템에서 비용의 대부분은 "생각하는 모델"이 아니라 **반복되는 짧은 일**에서 나옵니다. 긴 문서에서 숫자 하나 찾기, 검색 결과 요약, 대화 압축(compaction), 분류와 라우팅 같은 일입니다. 그래서 많은 팀이 큰 모델을 오케스트레이터(orchestrator, 계획하고 일을 나누는 모델)로, 작은 모델을 서브에이전트(subagent, 나뉜 일을 처리하는 모델)로 두는 구조를 씁니다.

Anthropic도 발표문에서 Haiku 5.5의 자리를 이렇게 정의합니다. 요약, 압축, 데이터베이스 질의, 분류처럼 빠르고 반복적인 작업을 맡고, 코딩 작업에서 Opus 5.5와 Sonnet 5.5의 **서브에이전트**로 잘 어울린다는 것입니다. 동시에 "Sonnet 5.5와 Opus 5.5가 복잡한 에이전트 코딩에는 여전히 더 나은 선택"이라고 분명히 적었습니다.

직전 세대인 Haiku 4.5는 입력 $1, 출력 $5였습니다. 이번 가격은 100K 이하 프롬프트 기준으로 정확히 10분의 1입니다.

## 핵심 내용

### 1. 가격 구조: 100K 토큰 경계

| 100만 토큰당 (USD) | Haiku 5.5 (≤100K) | Haiku 5.5 (>100K) | Haiku 4.5 | Sonnet 5.5 |
|---|---|---|---|---|
| 입력 | $0.10 | $0.50 | $1.00 | $2.00 |
| 5분 캐시 쓰기 | $0.125 | $0.625 | $1.25 | $2.50 |
| 1시간 캐시 쓰기 | $0.20 | $1.00 | $2.00 | $4.00 |
| 캐시 읽기 | $0.01 | $0.05 | $0.10 | $0.10 |
| 출력 | $0.50 | $2.50 | $5.00 | $10.00 |

(가격 문서, 2026-10-24 기준) 가격 문서는 경계 규칙을 이렇게 설명합니다. 프롬프트 길이는 **캐시 읽기와 캐시 쓰기를 포함한 모든 입력 토큰**으로 계산하고, 요청 하나하나를 따로 판정합니다. 경계를 넘은 요청은 일부가 캐시 적중이어도 높은 단가를 냅니다. Opus 5.5와 Sonnet 5.5를 포함한 다른 최신 모델은 1M 컨텍스트 전체를 같은 단가로 받으므로, **길이별 가격은 Haiku 5.5만의 특징**입니다. Batch API는 입력·출력 50% 할인입니다.

"평균 약 75% 절감"은 발표문 각주의 계산입니다. 100K 이하 요청은 90% 싸고 100K 초과 요청은 50% 싸며, Haiku 4.5 요청의 90%가 100K 이하였고, 새 토크나이저 때문에 같은 작업에 토큰이 조금 더 든다는 점을 반영한 값이라고 설명합니다.

### 2. 모델 사양

| 항목 | 값 (모델 문서 기준) |
|---|---|
| 컨텍스트 / 최대 출력 | 1M 토큰 / 128K 토큰 (Batch API 베타 300K) |
| 생각 방식 | adaptive thinking 기본 켜짐, `effort` 기본값 `medium` (low~max 5단계) |
| 입력 | 텍스트, 이미지 |
| 지식 기준일 | 2026년 6월 |
| 최소 캐시 길이 | 512토큰 (Haiku 4.5는 4,096토큰) |
| 은퇴 | 2027년 10월 7일 이전에는 은퇴하지 않음 |
| 제공처 | Claude API, Amazon Bedrock, Google Cloud, Microsoft Foundry 등 |

Haiku 계열에서 effort 설정을 처음 지원합니다. 문서는 대부분의 작업을 `medium`으로 시작하고, `low`는 짧은 도구 작업과 단순 대량 요청에 쓰되 긴 에이전트 프롬프트에서는 검색이나 확인을 건너뛸 가능성이 커진다고 안내합니다. 최소 캐시 길이가 4,096에서 512토큰으로 줄어든 것도 서브에이전트처럼 짧은 프롬프트를 많이 보내는 구조에 유리합니다.

### 3. Haiku 4.5에서 옮길 때 깨지는 것

"What's new" 문서와 마이그레이션 가이드가 "Breaking"으로 표시한 변경입니다.

- `thinking`의 `budget_tokens`(수동 확장 사고)는 오류를 냅니다. `{"type": "adaptive"}`로 바꿔야 합니다.
- `temperature`, `top_p`, `top_k`를 보내면 오류가 날 수 있습니다. 빼야 합니다.
- `messages`를 assistant 턴으로 끝내는 미리 채우기(prefill)는 오류를 냅니다. user 턴으로 끝내야 합니다.
- 컴퓨터 사용 도구 `computer_20250124`는 오류를 냅니다. Claude API에서는 `computer_toolset_20260801`로 바꿔야 합니다.
- thinking 블록을 되돌려 보내면서 이전 턴이나 `system`, `tools`를 바꾸면 thinking 블록이 무효가 됩니다. 대화를 추가 전용으로 유지해야 합니다.

동작 변경도 비용에 영향을 줍니다. 응답이 thinking 블록으로 시작할 수 있어 첫 블록을 답으로 읽는 코드는 `type`으로 골라야 하고, **이전 턴의 thinking 블록이 모두 컨텍스트에 남아 입력 토큰으로 계산**됩니다(Haiku 4.5는 마지막 턴 것만 유지). Haiku 4.5에서 Priority Tier를 약정한 조직은 Haiku 5.5에서 지원되지 않으니 따로 계획해야 합니다.

### 4. 같은 날 바뀐 것: Sonnet 5.5 캐시 읽기 절반, 구독자 API 크레딧

- **Sonnet 5.5 캐시 읽기:** $0.20에서 $0.10으로 50% 인하. Anthropic은 캐시 읽기가 에이전트 작업 토큰의 큰 비중을 차지하므로 "대부분의 에이전트 작업에서 약 20% 저렴해진다"고 설명합니다. 가격 문서상 Opus 5.5와 Sonnet 5.5의 캐시 읽기는 기본 입력가의 0.05배로, 다른 모델의 0.1배보다 낮습니다.
- **월간 API 크레딧:** Max 5x에 월 $100, Max 20x에 $200, Team에 최대 $500(사용자 간 공유)을 Claude Platform용으로 제공합니다(발표문 기준).
- **SDK:** Python·TypeScript SDK에 컴퓨터 사용과 브라우저 사용 지원을 베타로 추가했습니다.

## 성능과 비교

### Anthropic이 공개한 벤치마크와 측정 조건

| 벤치마크 | Haiku 5.5 | Haiku 4.5 | GPT-6 Luna | Sonnet 5.5 |
|---|---|---|---|---|
| OSWorld 2.1 오프라인 부분집합 (부분 점수) | 72.4% | 15.7% | 48.9% | 83.9% |
| Terminal-Bench 4.0 | 39.2% | 0.0% | 16.4% | 70.6% |
| FrontierCode 1.1 (Main) | 46.4% | - | 42.4% | 52.1% (xhigh) |
| Humanity's Last Exam (도구 없음 / 있음) | 45.9% / 57.4% | 10.2% / 18.7% | - | 56.9% / 64.5% |
| GDPval-AA v2.1 | 1620 | 735 | 1437 | 1840 |

(발표문과 시스템 카드 표 8.1.A 기준) 시스템 카드에 적힌 조건을 함께 봐야 합니다.

- **공통:** Haiku 5.5는 adaptive thinking **최대(max) effort**, 기본 샘플링, 5회 평균입니다. 기본값인 `medium`에서의 점수가 아닙니다.
- **OSWorld 2.1:** 108개 과제 중 공식 오프라인 목록의 **82개**만 썼고, 가상 머신에 인터넷이 없습니다. 72.4%는 부분 점수(체크포인트별 점수 평균)이고, 모든 체크포인트를 통과한 **엄격 통과율은 37.1%**입니다. Haiku 4.5는 고정 사고 예산에 서버 측 압축 없이 돌려 조건이 다릅니다. GPT-6 Luna는 Anthropic이 OpenAI API로 같은 82개 과제를 OpenAI의 압축 기능과 함께 실행했습니다.
- **Terminal-Bench 4.0:** 66개 과제, 과제당 10회(660회), 표준오차 ±1.9점. Claude Code `--bare` 모드, 인터넷 차단. 안전장치가 요청을 막은 시행이 1.8%(660회 중 12회) 있었고 모두 실패로 계산했습니다. GPT-6 Luna의 16.4%는 Anthropic이 아니라 **공개 리더보드**(Codex CLI, max effort) 수치입니다.
- **GDPval-AA:** Artificial Analysis의 평가로, 44개 직업의 실제 업무를 다루는 점수 체계입니다.

정리하면, 경쟁 모델 수치는 일부는 Anthropic이 직접 돌렸고 일부는 리더보드에서 가져왔으며, 하네스도 서로 다릅니다. 같은 조건의 제3자 비교는 2026-10-24 기준 확인하지 못했습니다.

### 비슷한 가격대 모델의 공식 가격

| 100만 토큰당 (USD) | Claude Haiku 5.5 | GPT-6 Luna | Gemini 3.5 Flash-Lite | Gemini 3.8 Flash |
|---|---|---|---|---|
| 입력 | $0.10 (≤100K) | $0.10 | $0.30 | $0.75 (2026-12-31까지) |
| 캐시 입력 | $0.01 | $0.01 | $0.03 (+저장료) | $0.075 (+저장료) |
| 출력 | $0.50 | $0.50 | $2.50 | $3.75 (2026-12-31까지) |
| 긴 프롬프트 | 100K 초과 시 전 항목 5배 | 272K 초과 시 입력·캐시 2배, 출력 1.5배 | - | 2027-01-01부터 입력 $1.50, 출력 $7.50 |

(각 사 공식 문서, 2026-10-24 기준: Anthropic 가격 문서, OpenAI GPT-6 Luna 모델 문서, Google Gemini API 가격 문서) **Haiku 5.5와 GPT-6 Luna는 기본 단가가 똑같습니다.** 차이는 긴 프롬프트 규칙입니다. Luna는 272K를 넘어야 할증이 붙고 배율도 낮지만, Haiku 5.5는 100K에서 5배가 됩니다. 토크나이저가 회사마다 달라 같은 텍스트의 토큰 수가 다르므로, 100만 토큰당 단가만으로 실제 비용을 비교할 수는 없습니다.

## 실무에서 쓰는 법

### 예제 1. 오케스트레이터가 부르는 Haiku 5.5 서브에이전트

공식 문서의 프롬프트 캐싱·effort 예제를 바탕으로 쓴 코드입니다. **API 키가 없는 환경이라 직접 실행하지는 못했습니다.** 여러 질문이 같은 긴 문서를 공유할 때, 문서 블록에 캐시 지점을 두면 두 번째 질문부터 문서 부분은 캐시 읽기 단가($0.01)로 처리됩니다.

```python
import anthropic

client = anthropic.Anthropic()
SHARED_DOC = open("annual_report.txt").read()  # 여러 하위 질문이 공유하는 긴 자료

def haiku_subagent(question: str) -> str:
    resp = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=4096,                       # thinking 토큰도 여기에 포함됨
        output_config={"effort": "low"},       # 짧은 추출 작업이라 low
        system="Extract exact figures. Quote the sentence each figure came from.",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": SHARED_DOC,
                 "cache_control": {"type": "ephemeral"}},  # 문서까지를 캐시
                {"type": "text", "text": question},
            ],
        }],
        # temperature, top_p, top_k는 넣지 않음 (Haiku 5.5에서 오류)
    )
    u = resp.usage
    print(u.input_tokens, u.cache_creation_input_tokens,
          u.cache_read_input_tokens, u.output_tokens)
    # 응답이 thinking 블록으로 시작할 수 있으므로 type으로 고른다
    return next(b.text for b in resp.content if b.type == "text")
```

`usage`의 네 값을 기록해 두면, 아래 예제처럼 실제 캐시 적중률과 100K 경계 초과 여부를 확인할 수 있습니다.

### 예제 2. 비용 계산: 경계 안과 밖

가격 문서의 단가로 필자가 계산한 예시입니다(토크나이저 차이는 무시, 캐시 쓰기 비용 제외).

| 상황 | 토큰 구성 | 요청 1회 비용 |
|---|---|---|
| A. Haiku 5.5 서브에이전트 | 캐시 읽기 35K + 새 입력 5K + 출력 2K | $0.00185 |
| A'. 같은 구성을 Haiku 4.5로 | 위와 같음 | $0.0185 |
| B1. Haiku 5.5, 프롬프트 95K | 캐시 읽기 90K + 새 입력 5K + 출력 2K | $0.0024 |
| B2. Haiku 5.5, 프롬프트 105K | 캐시 읽기 100K + 새 입력 5K + 출력 2K | $0.0125 |

A와 A'는 정확히 10배 차이입니다. 토크나이저 때문에 Haiku 5.5에서 토큰이 30% 늘어난다고 가정해도 A는 약 $0.0024로, 여전히 약 8분의 1입니다. 눈여겨볼 것은 B1과 B2입니다. 프롬프트가 10K 늘었을 뿐인데 요청 비용이 **약 5.2배**가 됩니다. 컨텍스트가 계속 자라는 에이전트 루프에서 Haiku 5.5를 쓴다면, 100K 직전에서 압축하거나 일을 쪼개는 것이 가격 설계의 일부가 됩니다.

### 예제 3. Sonnet 5.5 캐시 인하의 실제 효과

| 오케스트레이터 턴 (Sonnet 5.5) | 토큰 구성 | 인하 전 | 인하 후 | 변화 |
|---|---|---|---|---|
| 긴 에이전트 턴 | 캐시 읽기 145K + 새 입력 3K + 출력 1K | $0.0450 | $0.0305 | -32% |
| 짧은 턴 | 캐시 읽기 35K + 새 입력 5K + 출력 2K | $0.0370 | $0.0335 | -9% |

인하 효과는 **캐시 읽기 비중**에 달려 있습니다. 긴 컨텍스트를 매 턴 다시 읽는 오케스트레이터에서는 30% 넘게 줄지만, 출력이 많은 짧은 호출에서는 10% 안팎입니다. Anthropic의 "약 20%"는 그 사이의 평균적인 에이전트 작업을 가정한 값으로 보입니다.

## 한계와 논란

- **자체 측정, 최대 effort 기준입니다.** 발표된 점수는 모두 max effort입니다. 기본값 `medium`이나 비용을 아끼려고 쓰는 `low`에서는 점수가 낮을 수 있고, max effort는 thinking 토큰을 더 쓰므로 "싼 모델"의 이점이 일부 줄어듭니다. 발표문의 effort별 그래프는 OSWorld, GDPval-AA, HLE 세 가지에만 있습니다.
- **비교 조건이 고르지 않습니다.** Haiku 4.5는 고정 사고 예산과 서버 측 압축 없이 돌렸고, GPT-6 Luna의 Terminal-Bench 점수는 다른 하네스(Codex CLI)의 리더보드 값입니다. Haiku 4.5의 Terminal-Bench 0.0%는 "하나도 못 풀었다"는 뜻이라, 이 벤치마크가 이 체급에는 매우 어렵다는 점도 고려해야 합니다.
- **OSWorld 72.4%는 부분 점수입니다.** 모든 체크포인트를 통과한 비율은 37.1%이고, 인터넷이 필요한 26개 과제는 빠졌습니다. Sonnet 5.5(엄격 통과 48.8%)와의 차이는 부분 점수보다 엄격 통과율에서 더 작게 보이지만, 여전히 실제 업무를 맡기기엔 실패가 잦은 수준입니다.
- **100K 경계는 에이전트에 불리할 수 있습니다.** 1M 컨텍스트를 지원한다는 문구와 달리, 100K를 넘는 순간 모든 단가가 5배가 됩니다. 캐시 적중도 경계 판정에서 빠지지 않습니다.
- **마이그레이션 비용이 있습니다.** 샘플링 파라미터와 prefill을 쓰던 코드는 오류가 나므로, "모델 ID만 바꾸면 된다"고 기대하면 안 됩니다. thinking 블록 누적으로 입력 토큰도 늘어납니다.
- **안전장치 거절을 처리해야 합니다.** 안전 분류기가 요청을 거절하면 `stop_reason: "refusal"`이 오고, Haiku 5.5는 서버 측 대체 모델(fallback)이 없습니다. Terminal-Bench에서 1.8% 시행이 이 때문에 멈췄습니다. 사이버보안 관련 작업은 Haiku 4.5보다 제한이 강해졌다고 발표문이 밝힙니다.
- **고객사 인용은 홍보 자료입니다.** 발표문의 Asana, HubSpot, AlphaSense, Box, Rogo, Cognition 사례는 각 사가 자체 평가로 밝힌 내용이고 방법이 공개되지 않았습니다.

## 인사이트

**오케스트레이터-서브에이전트 구조에서 소형 모델의 역할이 바뀌고 있습니다.** 예전에는 소형 모델이 "답이 단순한 일"에만 쓰였다면, 이제는 컴퓨터 사용과 터미널 작업처럼 여러 단계를 밟는 일도 맡길 수 있는 수준으로 올라왔습니다(OSWorld 부분 점수 15.7% → 72.4%). 그래도 Anthropic 스스로 복잡한 코딩은 큰 모델 몫이라고 선을 그었습니다. 필자가 보기에 실용적인 분업은 이렇습니다. **오케스트레이터는 계획과 최종 판단, 서브에이전트는 범위가 좁고 결과를 검증하기 쉬운 일.** 문서에서 숫자 하나 찾기, 검색 결과 요약, 대화 압축, 분류처럼 오케스트레이터가 결과를 빠르게 확인할 수 있는 일이 Haiku 5.5에 맞습니다. 검증하기 어려운 일을 작은 모델에 맡기면 아낀 비용보다 오케스트레이터의 재확인 비용이 더 커질 수 있습니다.

**캐시 가격이 에이전트 비용의 주 변수가 됐습니다.** 이번 발표에서 가장 큰 가격 변화는 사실 Haiku의 단가보다 Sonnet 5.5의 캐시 읽기 인하일 수 있습니다. 긴 에이전트 루프에서는 매 턴 전체 컨텍스트를 다시 읽으므로 토큰의 대부분이 캐시 읽기입니다. 예제 3에서 보듯 같은 가격 인하가 긴 턴에서는 32%, 짧은 턴에서는 9%로 효과가 달라집니다. [프롬프트 캐싱 소개](/tech/2026/10/24/prompt-caching.html)에서 다룬 "접두사를 바꾸지 않는 설계"가 이제는 성능 최적화가 아니라 가격 설계의 중심이라는 뜻입니다. [CarryOn 논문](/papers/2026/10/24/pack-light-carryon.html)이 토큰을 51.9% 줄였는데 비용은 35.9%만 줄었던 것도 같은 이유입니다. 캐시 읽기가 싸질수록 "컨텍스트를 줄이는 것"의 금전적 가치는 작아지고, "컨텍스트를 바꾸지 않는 것"의 가치는 커집니다.

**그런데 Haiku 5.5에서는 이 공식이 100K에서 뒤집힙니다.** Sonnet·Opus는 컨텍스트를 길게 유지하고 캐시로 읽는 전략이 유리하지만, Haiku 5.5는 100K를 넘는 순간 캐시 읽기까지 5배가 됩니다. 그래서 같은 하네스라도 모델별로 압축 정책을 달리 둘 필요가 있습니다. 예를 들어 오케스트레이터(Sonnet)는 압축을 늦게 하고, 서브에이전트(Haiku)는 90K 근처에서 압축하거나 새 서브에이전트로 넘기는 식입니다. CarryOn이 컨텍스트를 약 65K 토큰에서 안정시켰다는 결과는 이런 경계 아래에서 일하는 하네스가 가능하다는 근거로 읽을 수 있습니다. 압축 자체를 Haiku 5.5에 맡기는 것은 Anthropic이 직접 제안한 용도이기도 합니다.

**한계와 반론: 가격 경쟁은 이미 평준화됐습니다.** GPT-6 Luna가 같은 기본 단가($0.10/$0.50, 캐시 $0.01)를 내걸고 있어, 이 체급에서 단가는 차별점이 아닙니다. 남는 차이는 긴 프롬프트 규칙(100K 5배 대 272K 2배), 토크나이저 효율, 같은 조건에서의 실제 성능인데, 마지막 것은 아직 제3자 비교가 없습니다. 도입을 판단할 때는 발표된 표보다 자기 작업으로 `usage`를 기록하며 돌린 비교가 훨씬 중요합니다.

**앞으로 지켜볼 점.** (1) 같은 하네스에서 Haiku 5.5와 GPT-6 Luna, Gemini Flash 계열을 비교한 제3자 평가. (2) `medium`·`low` effort에서의 벤치마크 점수. 서브에이전트는 대부분 낮은 effort로 돌기 때문입니다. (3) 100K 경계가 유지되는지. 다른 최신 모델처럼 1M 전체 단일 가격으로 바뀌면, 소형 모델로 긴 문서를 통째로 처리하는 구조가 다시 유리해집니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [Introducing Claude Haiku 5.5 (Anthropic, 2026-10-07)](https://www.anthropic.com/news/claude-haiku-5-5)
- [Claude Haiku 5.5 모델 문서](https://platform.claude.com/docs/en/models/haiku-5-5/overview)
- [What's new in Claude Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/whats-new-haiku-5-5)
- [Claude Haiku 5.5 마이그레이션 가이드](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide)
- [Claude 가격 문서](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude 모델 개요](https://platform.claude.com/docs/en/about-claude/models/overview)
- [프롬프트 캐싱 문서](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Effort 파라미터 문서](https://platform.claude.com/docs/en/build-with-claude/effort)
- [Claude Haiku 5.5 시스템 카드 (PDF)](https://www.anthropic.com/document/claude-haiku-5-5-system-card)
- [GPT-6 Luna 모델 문서 (OpenAI)](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [Gemini API 가격 (Google)](https://ai.google.dev/gemini-api/docs/pricing)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
