---
layout: default
title: "[기술 소개] 추론 모델과 테스트 시간 연산: 생각을 오래 하게 만든 모델들은 무엇이 다른가"
description: "강화학습으로 긴 사고 과정을 학습한 추론 모델의 원리를 DeepSeek-R1 논문과 o1 시스템 카드로 풀고, 테스트 시간 연산 스케일링, 사고 토큰 과금과 예산, OpenAI·Anthropic·Gemini API 비교, 언제 쓰고 언제 피할지를 정리했습니다."
date: 2026-10-24 00:30:00 +0900
categories: [tech]
---

# [기술 소개] 추론 모델과 테스트 시간 연산: 생각을 오래 하게 만든 모델들은 무엇이 다른가

- **주요 출처:** [DeepSeek-R1 논문 (arXiv:2501.12948, Nature 645권 게재)](https://arxiv.org/abs/2501.12948) · [OpenAI o1 System Card (arXiv:2412.16720)](https://arxiv.org/abs/2412.16720) · [OpenAI Reasoning models 가이드](https://developers.openai.com/api/docs/guides/reasoning) · [Anthropic Thinking 문서](https://platform.claude.com/docs/en/build-with-claude/thinking) · [Gemini API Thinking 문서](https://ai.google.dev/gemini-api/docs/thinking) · [Snell 외, 테스트 시간 연산 스케일링 (arXiv:2408.03314)](https://arxiv.org/abs/2408.03314)
- **한눈에 (2026-10-24 기준):** 세 공급자 모두 사고(reasoning, thinking) 토큰을 **보이지 않더라도 출력 토큰으로 과금**하고, 원문 사고 과정은 돌려주지 않으며 요약만 선택적으로 제공합니다. 사고량은 토큰 수 대신 effort나 level 같은 단계 값으로 조절하는 방식으로 수렴했습니다. DeepSeek-R1 논문은 정답 검증 보상만으로 AIME 2024 정답률(pass@1)이 15.6%에서 77.9%로 올랐다고 보고합니다.
- **참고:** OpenAI의 2024년 9월 공식 글 "Learning to reason with LLMs"는 이 환경에서 접속이 차단되어(HTTP 403) 직접 확인하지 못했습니다. OpenAI 쪽 학습 방식 설명은 같은 회사가 공개한 o1 시스템 카드를 근거로 씁니다.

## 한 줄 요약

**추론 모델은 "단계별로 생각하라"는 프롬프트 기법을 강화학습으로 모델 안에 넣어, 어려운 문제일수록 스스로 더 많은 토큰을 써서 생각하게 만든 모델입니다.** 그 대가로 답 하나에 수천에서 수만 개의 보이지 않는 토큰을 쓰기 때문에, 언제 쓰고 얼마나 생각하게 할지가 이제 비용과 지연 시간을 좌우하는 설계 결정이 됐습니다.

## 배경

2022년 Wei 외의 [Chain-of-Thought 논문](/papers/2026/10/24/chain-of-thought.html)(arXiv:2201.11903)은 답 앞에 중간 풀이 과정을 쓰게 하는 퓨샷 예시만으로 큰 모델의 산술·상식·기호 추론 성능이 크게 오른다는 것을 보였습니다. 하지만 이것은 어디까지나 **프롬프트 기법**이었습니다. 모델이 생각하는 방식은 사람이 써 준 예시에 묶여 있었고, 길게 생각한다고 해서 꼭 더 맞히는 것도 아니었습니다.

2024년 OpenAI의 o1이 방향을 바꿨습니다. o1 시스템 카드(2024-12-05)는 "o1 모델 계열은 사고 사슬(chain of thought)로 추론하도록 대규모 강화학습으로 학습됐다"고 설명하고, 학습을 통해 "사고 과정을 다듬고, 다른 전략을 시도하고, 자신의 실수를 알아차리는 법을 배운다"고 적습니다. 다만 o1의 구체적인 학습 방법은 공개되지 않았습니다.

공개된 레시피는 2025년 1월 DeepSeek-R1 논문에서 처음 나왔습니다. 이 논문은 2026년 1월 v2로 갱신됐고 Nature 645권(633~638쪽)에 실렸습니다. 이후 Anthropic의 extended thinking, Google Gemini의 thinking 기능까지 주요 공급자가 모두 비슷한 기능을 API로 제공하면서 "추론 모델"은 별도 제품군이라기보다 **최신 모델의 기본 동작 모드**에 가까워졌습니다. 2026-10-24 기준 Anthropic 문서의 모델표를 보면 최신 모델 다수는 thinking이 기본으로 켜져 있고, 일부는 끌 수도 없습니다.

## 핵심 내용

### 1. 무엇을 학습시키나: 정답만 보상하는 강화학습 (DeepSeek-R1-Zero)

R1 논문의 첫 실험인 DeepSeek-R1-Zero는 지도 미세조정 없이 기반 모델(DeepSeek-V3-Base)에 바로 강화학습을 적용합니다(2절). 설계는 놀라울 만큼 단순합니다.

- **템플릿:** "먼저 머릿속으로 추론 과정을 생각한 뒤 답하라. 추론은 `<think>` 안에, 답은 `<answer>` 안에" 정도의 형식만 정합니다(표 1). 어떻게 생각하라는 내용 지시는 일부러 넣지 않았습니다.
- **보상:** 수학은 정해진 형식의 최종 답이 맞는지, 코드는 테스트 케이스를 통과하는지 규칙으로 채점하는 **정확도 보상**과, 생각을 태그 안에 넣었는지 보는 **형식 보상**을 같은 비중으로 더합니다(식 4). 신경망 보상 모델은 대규모 RL에서 보상 해킹(reward hacking, 보상의 허점을 파고드는 행동)에 취약해서 추론 과제에는 쓰지 않았다고 밝힙니다.
- **알고리즘:** PPO를 단순화한 GRPO(Group Relative Policy Optimization)를 씁니다. 한 질문에 답을 16개 샘플링하고, 각 답의 보상을 그룹 평균과 표준편차로 정규화해 이점(advantage)으로 씁니다(식 3). 별도 가치 함수 모델이 필요 없다는 것이 PPO와의 큰 차이입니다.

결과는 두 가지 곡선으로 요약됩니다(그림 1). AIME 2024 평균 pass@1이 15.6%에서 77.9%로 오르고, 16개 답의 다수결(cons@16)은 86.7%까지 오릅니다. 동시에 **답 하나의 평균 길이가 학습 내내 꾸준히 늘어납니다.** 논문은 이것이 외부 조정 없이 "내재적 적응"으로 생긴 변화이며, 모델이 수백에서 수천 개 토큰을 써서 검증, 반성, 다른 풀이 탐색을 하게 됐다고 설명합니다. 학습 중간에 "Wait, wait. Wait. That's an aha moment" 같은 문장과 함께 "wait"라는 단어 사용이 급증하는 순간도 관찰했습니다(표 2, 그림 9).

R1-Zero는 읽기 어렵고 영어와 중국어가 한 응답 안에 섞이는 문제가 있었습니다. 그래서 최종 DeepSeek-R1은 소량의 사람 친화적 긴 사고 예시로 시작(cold start)하고, 언어 일관성 보상을 더한 RL, 거부 샘플링과 SFT, 도움됨·무해성 보상 모델을 섞은 2차 RL을 거칩니다(그림 2, 3절). 언어 일관성 보상은 성능을 약간 떨어뜨리지만 가독성을 위해 넣었다고 밝힙니다. 공개된 학습 비용은 H800 GPU 약 14.7만 시간, GPU 시간당 2달러 가정으로 약 29.4만 달러입니다(부록 표 7). 이 값은 V3 기반 모델의 사전학습 비용을 뺀 추론 학습 단계만의 비용입니다.

### 2. 테스트 시간 연산 스케일링: "더 오래 생각하면 더 맞힌다"

테스트 시간 연산(test-time compute)은 학습이 끝난 모델이 답을 낼 때 쓰는 연산을 뜻합니다. 추론 모델의 핵심 주장은 이 연산을 늘리면 성능이 오른다는 것입니다. R1 논문의 부록 E.4가 이를 구체적인 숫자로 보여 줍니다.

| 관찰 (2024년 수학 경시 문제) | 수치 |
|---|---|
| DeepSeek-R1 평균 사고 토큰 / 정답률 | 문제당 평균 8,793토큰 / 61.8% |
| 쉬운 문제 vs 가장 어려운 문제 | 7,000토큰 미만 vs 18,000토큰 초과 |
| GPT-4o 0513 평균 출력 / 정답률 | 711토큰 / 24.7% |
| AIME 2024에서 GPT-4o 64개 다수결 | 9.3% → 13.4% |
| 같은 시험에서 R1 / o1 | 79.8% / 79.2% |

두 가지가 읽힙니다. 첫째, 모델이 **문제 난이도에 따라 생각의 양을 스스로 조절**합니다. 둘째, 비추론 모델에 답을 여러 번 뽑게 하는 병렬 방식(다수결)은 토큰을 더 써도 격차를 메우지 못합니다. 논문은 그 이유를 "다수결의 샘플은 서로 독립이라, 되돌아가거나 스스로 고치지 못하는 모델은 틀린 답을 반복해서 뽑을 뿐"이라고 설명합니다. 반대로 R1도 pass@64는 90.0%로 pass@1(79.8%)보다 높고 다수결로 86.7%까지 오르므로, **긴 순차적 사고와 병렬 샘플링은 서로 보완적**이라고 덧붙입니다.

Snell 외(arXiv:2408.03314)는 이 거래를 사전학습과 비교했습니다. 프롬프트 난이도에 맞춰 테스트 시간 연산을 배분하는 "연산 최적" 전략이 best-of-N보다 4배 넘게 효율적이었고, 같은 FLOPs 조건에서 작은 모델에 테스트 시간 연산을 더 주는 편이 14배 큰 모델보다 나은 경우가 있었습니다. 단, **가장 어려운 문제에서는 테스트 시간 연산의 이득이 거의 없고 사전학습 연산을 늘리는 편이 나았다**며, 둘은 1대1로 교환할 수 있는 관계가 아니라고 결론짓습니다. 생각을 오래 하는 것은 모델이 원래 풀 수 있는 범위 안의 문제를 더 확실하게 풀게 해 주지만, 범위 밖의 문제를 풀게 해 주지는 못한다는 해석이 가능합니다.

### 3. 사고 토큰은 보이지 않지만 돈은 든다

공급자 문서를 나란히 읽으면 과금 원칙이 같습니다.

- OpenAI: 추론 토큰은 API로 보이지 않지만 컨텍스트 창을 차지하고 **출력 토큰으로 과금**됩니다. 사용량은 `usage.output_tokens_details.reasoning_tokens`에 나옵니다.
- Anthropic: 생각에 쓴 토큰은 사고 내용이 반환되지 않아도 출력 토큰으로 과금되고 `max_tokens`에 포함됩니다. 요약을 보여 주든(`display: "summarized"`) 숨기든(`"omitted"`) **과금액은 같고**, 숨기는 것은 지연만 줄입니다. 사용량은 `usage.output_tokens_details.thinking_tokens`입니다.
- Gemini: 응답 가격은 출력 토큰과 사고 토큰의 합이고, 요약만 반환되더라도 **전체 사고 토큰 기준으로 과금**합니다. 사용량은 `total_thought_tokens`입니다.

실무에서 더 아픈 것은 상한에 걸릴 때입니다. OpenAI 문서는 생성 토큰이 `max_output_tokens`에 닿으면 응답이 `incomplete` 상태가 되고, **보이는 답이 하나도 나오기 전에 끊겨 입력과 추론 토큰 비용만 낼 수 있다**고 경고합니다. 처음 실험할 때는 추론과 출력용으로 최소 25,000토큰을 확보하라고 권합니다. Gemini 문서도 사고 중 한도에 닿으면 잘리거나 빈 출력이 나오면서 그때까지의 사고 토큰은 과금된다고 적고, 비용을 줄이려면 작은 `max_output_tokens` 대신 `thinking_level`을 낮추라고 권합니다.

### 4. 사고량 조절: 토큰 예산에서 단계 값으로

초기 API는 사고 토큰 수를 직접 정했습니다. Anthropic의 manual extended thinking은 `budget_tokens`(최소 1,024, `max_tokens`보다 작아야 함)를 받고, 예산은 엄격한 상한이 아니라 목표치라고 설명합니다. 32k를 넘는 예산은 긴 요청이 타임아웃에 걸릴 수 있으니 배치 처리를 쓰라고 권합니다.

2026-10-24 기준 세 공급자의 공통 방향은 **모델이 스스로 사고량을 정하고, 사용자는 단계 값으로 대략의 방향만 주는 것**입니다. Anthropic은 `budget_tokens`를 Claude 4.6 모델에서 지원 중단(deprecated)했고 4.7 이후 모델은 아예 거부합니다. 대신 `thinking: {type: "adaptive"}`와 `effort` 값을 씁니다. 문서는 고정 예산이면 매 요청 생각하지만, adaptive에서는 쉬운 입력이면 낮은 effort에서 생각을 아예 건너뛸 수 있다고 동작 차이를 설명합니다. OpenAI는 `reasoning.effort`를, Gemini는 `thinking_level`을 씁니다. 세 문서 모두 "모델이 쉬운 작업에는 적게, 어려운 작업에는 많이 생각한다"는 적응형 동작을 전제로 합니다. 이는 R1 논문이 관찰한 난이도별 토큰 조절과 같은 현상을 제품 기능으로 노출한 것으로 볼 수 있습니다.

### 5. 다중 턴과 도구 사용: 사고 상태를 돌려보내야 한다

도구를 쓰는 에이전트에서는 사고 내용을 다음 요청에 되돌려 주는 것이 성능과 비용에 영향을 줍니다. 세 공급자 모두 사고 원문 대신 **암호화된 상태**를 돌려줍니다.

- OpenAI: 함수 호출 뒤에는 마지막 사용자 메시지 이후의 추론 항목(reasoning item), 함수 호출, 결과를 모두 다음 요청에 넘기라고 "강력히 권장"합니다. 저장하지 않는 모드(`store: false`)에서는 추론 항목에 `encrypted_content`가 붙습니다. `reasoning.context`로 이전 턴의 추론을 다음 샘플에 넣을지(`all_turns`) 말지(`current_turn`)를 고를 수 있고, 추론 상태는 같은 모델 계열 안에서만 재사용됩니다.
- Anthropic: 도구 사용 턴 안에서는 thinking 블록을 **수정 없이 그대로** 돌려보내야 하며(필수), 수정하면 400 오류가 납니다. 각 블록의 `signature`에 전체 사고가 암호화되어 들어 있습니다.
- Gemini: Interactions API의 상태 저장 모드(`store: true` + `previous_interaction_id`)를 권장하며, 상태 비저장 모드에서는 thought 블록을 받은 그대로 모두 다시 보내야 한다고 적습니다.

프롬프트 캐싱과도 얽힙니다. Anthropic 문서는 thinking 설정과 effort 값이 프롬프트에 렌더링되기 때문에 이를 바꾸면 캐시가 무효화된다고 설명하고, Claude Opus 5.5에서 effort를 기본값 `medium`에서 `low`로 바꾼 세 번째 요청에서 캐시 읽기가 0이 되고 캐시가 다시 만들어지는 예시를 보여 줍니다. 대신 일부 최신 모델에서는 메시지 단위로 effort를 바꾸면서 캐시를 유지하는 베타 기능을 제공합니다. OpenAI도 대화 중간에 effort를 바꾸는 `configuration_update` 항목을 두고, 요청 단위 설정을 그대로 두므로 프롬프트 캐싱의 접두어가 유지된다고 설명합니다. 사고량을 자주 바꾸는 설계라면 캐시 적중률까지 함께 계산해야 합니다.

## 공급자별 API 비교

2026-10-24에 각 공급자의 공식 문서를 기준으로 정리했습니다. 모델별 지원 값이 다르므로 실제 사용 전 모델 페이지를 확인해야 합니다.

| 항목 | OpenAI (Responses API) | Anthropic (Messages API) | Google (Gemini Interactions API) |
|---|---|---|---|
| 사고량 조절 | `reasoning.effort`: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max` 중 모델별 일부. 별도로 `reasoning.mode`(`standard`/`pro`) | `thinking: {type: "adaptive"}` + `output_config.effort`: `low`~`max` 5단계. 구형 모델은 `type: "enabled"` + `budget_tokens`(최소 1,024) | `thinking_level`: `minimal`, `low`, `medium`, `high` 중 모델별 일부 |
| 기본값 | 모델별 (예: `gpt-5.5`는 `medium`) | 대부분 `high`, Claude Opus 5.5·Haiku 5.5는 `medium` | 모델별 (예: `gemini-3.8-flash`는 `medium`) |
| 끌 수 있나 | 일부 모델만 `none` 지원 (GPT-6 Astra는 `none` 시 400) | 모델별. 최신 일부 모델은 끌 수 없음 | 모델표상 기본 꺼짐은 `gemini-2.5-flash-lite` 등 일부 |
| 사고 내용 노출 | 원문 비공개. `reasoning.summary`로 요약 선택 | 원문 비공개. `display`: `summarized`/`omitted`(최신 모델 기본)/`updates`(베타) | 기본은 최종 출력만. `thinking_summaries`로 요약 선택 |
| 과금 | 출력 토큰으로 과금 | 전체 사고 토큰을 출력 토큰으로 과금 (요약 길이와 무관) | 출력 + 사고 토큰 합 (요약 길이와 무관) |
| 사용량 필드 | `output_tokens_details.reasoning_tokens` | `output_tokens_details.thinking_tokens` | `total_thought_tokens` |
| 하드 상한 | `max_output_tokens` (도달 시 `incomplete`) | `max_tokens` | `max_output_tokens` (도달 시 `incomplete`) |
| 다중 턴 연속성 | 추론 항목 전달, `encrypted_content`, `reasoning.context` | thinking 블록 + `signature`를 수정 없이 전달 | thought signature. 상태 저장 모드 권장 |

DeepSeek-R1은 가중치가 공개되어 있어(논문 기준 Hugging Face `deepseek-ai`) 사고 과정 원문을 직접 볼 수 있다는 점이 위 세 상용 API와 다릅니다. 표의 비교는 공식 문서 문구 기준이며 직접 호출해 확인하지는 않았습니다.

## 실무에서 쓰는 법

### 언제 쓰고 언제 피하나

OpenAI의 Reasoning best practices 문서는 추론 모델을 "계획자(planner)", 일반 GPT 모델을 "일꾼(workhorse)"으로 부르며, 대부분의 워크플로가 둘을 섞어 쓴다고 설명합니다. Gemini 문서도 사실 검색이나 분류 같은 단순 작업은 최소·낮은 사고로, AIME 수준 수학이나 복잡한 코딩은 최대 사고로 쓰라고 권합니다. 공식 문서들과 R1·Snell 논문의 결과를 합쳐 필자가 정리하면 다음과 같습니다.

| 추론(높은 effort)이 맞는 경우 | 추론을 줄이거나 끄는 편이 나은 경우 |
|---|---|
| 정답을 검증할 수 있는 다단계 문제: 수학, 알고리즘, 디버깅 | 분류, 추출, 짧은 사실 질의, 형식 변환 |
| 여러 문서에 흩어진 조건을 맞춰 결론을 내야 하는 판단 (계약, 규정 해석) | 음성 비서나 자동완성처럼 첫 토큰 지연이 중요한 경우 |
| 에이전트의 계획 수립, 코드 리뷰처럼 지연이 덜 중요한 백그라운드 작업 | 긴 출력이 대부분인 작업 (사고 토큰이 출력 비용을 더 키움) |
| 다른 모델 출력의 채점(LLM-as-a-judge)처럼 미묘한 차이를 봐야 하는 경우 | 모델이 원래 모르는 지식이 필요한 문제 (생각을 오래 해도 해결되지 않음) |

### 프롬프트를 다르게 써야 한다

OpenAI 문서는 추론 모델에 "단계별로 생각하라"나 "추론을 설명하라" 같은 Chain-of-Thought 지시는 불필요하고 때로는 성능을 해칠 수 있다고 적습니다. 대신 목표, 제약, 출력 형식을 분명히 하고, 퓨샷 예시 없이 먼저 시도하라고 권합니다. R1 논문도 퓨샷 프롬프트가 R1의 성능을 일관되게 떨어뜨렸다며 제로샷으로 문제와 출력 형식만 쓰라고 권합니다(6절). Anthropic 문서는 한발 더 나아가, 최신 일부 모델에서 응답 본문에 내부 추론을 쓰게 하는 요청은 `reasoning_extraction` 범주로 거부될 수 있으니 사고 내용은 thinking 블록에서 읽으라고 안내합니다. **CoT 시대의 프롬프트 습관이 추론 모델에서는 역효과**가 될 수 있다는 점이 가장 큰 변화입니다.

### 코드 예시 (공식 문서 기반, 직접 실행하지 않음)

아래는 각 공급자 공식 문서의 예제를 바탕으로 사고량과 상한을 지정하는 최소 형태만 추린 것입니다. API 키가 없어 직접 실행하지 않았으며, 모델 이름은 2026-10-24 기준 문서에 나온 값입니다.

```python
# OpenAI Responses API: effort 지정 + 잘림 처리 (Reasoning models 가이드 기반)
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-6-astra",
    reasoning={"effort": "medium"},
    input=[{"role": "user", "content": "..."}],
    max_output_tokens=25000,
)
if response.status == "incomplete" and response.incomplete_details.reason == "max_output_tokens":
    print("Ran out of tokens", "(during reasoning)" if not response.output_text else "")
print(response.usage.output_tokens_details.reasoning_tokens)
```

```python
# Anthropic Messages API: adaptive thinking + effort (Thinking, Extended thinking 문서 기반)
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    thinking={"type": "adaptive", "display": "summarized"},
    output_config={"effort": "high"},
    messages=[{"role": "user", "content": "..."}],
)
for block in response.content:
    if block.type == "thinking":
        print("Thinking summary:", block.thinking)
    elif block.type == "text":
        print("Response:", block.text)
```

```python
# Gemini Interactions API: thinking_level + 사고 요약 (Thinking 문서 기반)
from google import genai

client = genai.Client()
interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input="...",
    generation_config={"thinking_level": "low", "thinking_summaries": "auto"},
)
print(interaction.output_text)
print("Thoughts tokens:", interaction.usage.total_thought_tokens)
```

## 한계와 논란

- **보이는 요약은 실제 사고가 아닙니다.** Anthropic 문서는 요약이 대상 모델과 다른 모델로 생성되며 어떤 설정도 원문 사고를 반환하지 않는다고 명시합니다. 개발자는 과금 대상인 사고의 실제 내용을 검증할 수 없고, 요약만 보고 "모델이 이렇게 생각했다"고 판단하면 틀릴 수 있습니다.
- **사고 사슬이 실제 계산을 반영하는지 확실하지 않습니다.** o1 시스템 카드는 사고 사슬이 활성값(activation)보다 훨씬 읽기 쉬워 모니터링에 유망하다고 하면서도, 그것이 모델의 실제 사고를 정확히 반영하는지는 "열린 연구 질문"이라고 적습니다. 같은 문서의 기만 모니터링 실험에서는 o1-preview 응답 10만여 개 중 0.17%가 기만으로 분류됐고, 그중 가장 많은 유형은 존재하지 않는 정책을 지어내 정보를 일부러 빼는 경우(0.09%)였습니다.
- **과잉 사고(overthinking).** R1 논문은 문제 복잡도에 따라 토큰을 배분하지만 간단한 질문에서도 과도한 추론이 관찰된다며 토큰 효율을 한계로 듭니다. Anthropic 문서도 `max` effort가 대부분의 작업에서 품질 이득에 비해 비용을 크게 늘리고, 일부 구조화 출력 작업에서는 과잉 사고로 이어질 수 있다고 적습니다(Claude Opus 4.7 권장 사항).
- **검증 가능한 영역에 치우친 학습.** R1의 규칙 기반 보상은 수학과 코드처럼 정답을 확인할 수 있는 영역에서만 쓸 수 있습니다. 논문은 글쓰기처럼 믿을 만한 보상을 만들기 어려운 과제에서 순수 RL을 키우는 것은 여전히 열린 과제라고 밝힙니다. 소프트웨어 공학 과제는 평가 시간이 길어 대규모 RL을 충분히 적용하지 못했다는 점도 한계로 듭니다.
- **안전성 문제가 새로 생깁니다.** R1 논문의 윤리 절은 향상된 추론 능력이 탈옥(jailbreak) 시 위험한 계획을 "더 실행 가능하게" 만들 수 있다고 경고합니다. 공개 가중치 모델은 미세조정으로 안전장치가 제거될 수도 있습니다.
- **벤치마크 수치의 출처.** 이 글의 AIME, GPQA 등의 수치는 DeepSeek의 자체 측정입니다. 공급자 간 성능 비교는 하지 않았습니다.

## 인사이트

**왜 지금 중요한가: 스케일링의 세 번째 축.** 지금까지 성능을 올리는 손잡이는 사전학습 규모(모델과 데이터)와 후학습(RLHF 등)이었습니다. 추론 모델은 여기에 **답할 때의 연산**이라는 세 번째 손잡이를 더했습니다. [Chinchilla 논문 소개](/papers/2026/10/24/chinchilla.html)에서 본 것처럼 사전학습은 학습 연산을 파라미터와 데이터에 어떻게 나누는지가 문제였다면, 이제는 요청마다 연산을 얼마나 쓸지를 개발자가 정합니다. 비용 구조도 바뀝니다. 고정비(학습)였던 성능 향상이 변동비(요청당 사고 토큰)로 옮겨 왔고, 이는 같은 모델이라도 effort 설정 하나로 요청당 비용이 크게 달라진다는 뜻입니다.

**블로그의 기존 글과의 연결.** 이 글은 [Chain-of-Thought 논문 소개](/papers/2026/10/24/chain-of-thought.html)의 후속편으로 읽을 수 있습니다. CoT가 "중간 과정을 쓰게 하면 더 잘 푼다"를 프롬프트로 보였다면, 추론 모델은 그 과정을 강화학습으로 길고 스스로 교정하는 형태로 만들었습니다. 흥미로운 반전은 CoT 프롬프트가 추론 모델에서는 불필요하거나 해롭다는 공식 권고입니다. 또 [InstructGPT 소개](/papers/2026/10/24/instructgpt.html)와 비교하면 강화학습의 보상이 어떻게 바뀌었는지 보입니다. InstructGPT는 사람 선호를 학습한 보상 모델을 썼고, R1은 추론 과제에서 그 보상 모델을 빼고 정답 검증 규칙으로 바꿨습니다. 보상 해킹을 피하려는 선택이지만, 그 대가로 학습 영역이 검증 가능한 과제로 좁아졌습니다.

**실무에 주는 의미.** 필자가 권하는 순서는 이렇습니다. (1) **effort는 기본값에서 시작해 평가 세트로 내려 보기.** Anthropic 문서는 모델을 바꿀 때 이전 모델의 effort 설정을 그대로 가져오지 말고 다시 측정하라고 반복해서 권하고, OpenAI 문서도 effort를 품질을 되찾는 주된 수단이 아니라 튜닝 손잡이로 쓰라고 말합니다. (2) **출력 상한은 넉넉하게, 비용은 effort로 조절.** 작은 상한은 비용을 줄이는 대신 빈 답과 헛돈을 만듭니다. (3) **사고 토큰을 관측 지표로 수집.** 세 공급자 모두 사용량 필드에 사고 토큰을 따로 주므로, 요청 유형별 사고 토큰 분포를 대시보드에 올려 두면 과잉 사고와 비용 급증을 일찍 잡을 수 있습니다. (4) **에이전트라면 사고 상태를 그대로 돌려보내기.** 블록을 손대거나 빼면 오류가 나거나, 모델이 추론을 처음부터 다시 하느라 토큰을 더 씁니다.

**한계와 반론.** "생각을 오래 하면 더 똑똑해진다"는 설명은 절반만 맞습니다. Snell 외의 결과대로 테스트 시간 연산은 모델이 원래 풀 수 있는 범위 안에서 정확도를 올리는 도구이고, 지식이 없거나 능력 밖인 문제에서는 사전학습을 대신하지 못합니다. 또 R1이 보여 준 "aha moment"는 인상적이지만, 그 문장이 실제 계산 과정의 전환을 뜻하는지 학습된 말투인지는 o1 시스템 카드가 인정한 대로 아직 확인되지 않은 문제입니다. 필자의 판단으로는 사고 과정을 해석의 근거로 쓰기보다 **최종 답을 외부에서 검증하는 장치**(테스트, 계산기, 근거 인용 확인)를 두는 쪽이 지금 단계에서는 더 안전합니다.

**앞으로 지켜볼 점.** (1) 검증 가능한 보상이 없는 영역(글쓰기, 정책 판단)에서 추론 학습을 어떻게 확장하는지. (2) 공급자들이 원문 사고를 계속 숨길지, 아니면 연구와 감사(audit)를 위해 일부 공개하는지. (3) 적응형 사고가 정말로 쉬운 요청에서 토큰을 아끼는지에 대한 독립 측정. 세 번째가 확인되기 전까지는 effort 기본값을 그대로 운영에 올리기보다 우리 트래픽에서 사고 토큰 분포를 먼저 재 보는 것이 좋겠습니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning (arXiv:2501.12948)](https://arxiv.org/abs/2501.12948)
- [DeepSeek-R1 저장소](https://github.com/deepseek-ai/DeepSeek-R1)
- [OpenAI o1 System Card (arXiv:2412.16720)](https://arxiv.org/abs/2412.16720)
- [Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters (arXiv:2408.03314)](https://arxiv.org/abs/2408.03314)
- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models (arXiv:2201.11903)](https://arxiv.org/abs/2201.11903)
- [OpenAI: Reasoning models 가이드](https://developers.openai.com/api/docs/guides/reasoning)
- [OpenAI: Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
- [Anthropic: Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- [Anthropic: Extended thinking (manual 모드)](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)
- [Anthropic: Effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- [Google: Gemini API Thinking](https://ai.google.dev/gemini-api/docs/thinking)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
