---
layout: default
title: "[논문 소개] Chain-of-Thought Prompting: 예시에 풀이 과정을 넣으면 큰 모델이 추론한다"
description: "CoT 프롬프팅 원 논문의 few-shot 예시 구성, 모델 크기에 따른 창발, GSM8K 등 수치와 소거 실험을 정리하고, zero-shot CoT, self-consistency, 추론 모델로 이어진 흐름과 지금 CoT를 쓸 때와 안 써도 될 때를 다뤘습니다."
date: 2026-10-24 00:04:00 +0900
categories: [papers]
---

# [논문 소개] Chain-of-Thought Prompting: 예시에 풀이 과정을 넣으면 큰 모델이 추론한다

- **논문:** *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*
- **저자:** Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed H. Chi, Quoc V. Le, Denny Zhou (총 9명, Google Research Brain Team)
- **공개:** 2022년 1월 28일, arXiv:2201.11903 (cs.CL, cs.AI). NeurIPS 2022 발표. 이 글은 2023년 1월 10일 갱신된 v6을 기준으로 합니다.
- **링크:** [arXiv](https://arxiv.org/abs/2201.11903) · [PDF](https://arxiv.org/pdf/2201.11903) · [NeurIPS 2022 프로시딩](https://proceedings.neurips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract-Conference.html)

## 한 줄 요약

**few-shot 예시의 답 앞에 사람이 쓴 풀이 과정(chain of thought, 사고의 사슬)을 넣기만 해도, 약 1,000억 파라미터 이상의 모델은 수학·상식·기호 추론 성능이 크게 오른다는 논문입니다.** 미세 조정 없이 프롬프트만 바꿔 PaLM 540B가 GSM8K에서 당시 최고 기록을 넘었고, 이 아이디어는 이후 zero-shot CoT, self-consistency를 거쳐 오늘날의 "생각하는" 추론 모델로 이어졌습니다.

## 왜 이 연구가 필요한가

2020년 GPT-3 이후 few-shot 프롬프팅(입력-출력 예시 몇 개를 보여 주고 새 문제를 풀게 하는 방식)이 널리 쓰였지만, 논문은 이 방식이 **추론이 필요한 과제에서는 잘 통하지 않고, 모델을 키워도 크게 나아지지 않는다**는 기존 관찰(Rae et al., 2021)에서 출발합니다(1절).

한편 수학 문제에서는 최종 답에 이르는 자연어 풀이(rationale)를 생성하게 하면 도움이 된다는 연구가 있었지만, 이는 풀이가 달린 대규모 학습 데이터를 만들어 모델을 처음부터 학습하거나 미세 조정해야 했습니다. 저자들은 두 아이디어의 장점만 합칩니다. **풀이 데이터 수천 개를 만드는 대신, 프롬프트의 예시 몇 개에만 풀이를 붙이면 어떨까?**

## 제안 방법

### 1. 예시를 ⟨입력, 사고의 사슬, 출력⟩ 세 쌍으로

방법은 정말 이것 하나입니다. 표준 few-shot 프롬프트의 예시 답변에 중간 풀이를 덧붙입니다(그림 1).

```
[표준 프롬프팅]
Q: Roger has 5 tennis balls. He buys 2 more cans of tennis balls.
   Each can has 3 tennis balls. How many tennis balls does he have now?
A: The answer is 11.

[Chain-of-Thought 프롬프팅]
Q: Roger has 5 tennis balls. He buys 2 more cans of tennis balls.
   Each can has 3 tennis balls. How many tennis balls does he have now?
A: Roger started with 5 balls. 2 cans of 3 tennis balls each is 6 tennis balls.
   5 + 6 = 11. The answer is 11.
```

새 문제("식당에 사과가 23개 있었고 20개를 쓰고 6개를 더 샀다면?")에 대해 표준 프롬프트를 받은 모델은 "The answer is 27"이라고 틀렸고, CoT 프롬프트를 받은 모델은 "23 - 20 = 3 ... 3 + 6 = 9"라고 풀어 맞혔습니다.

### 2. 예시는 어떻게 만들었나

- **수학 문제용 8개:** 저자들이 직접 쓴 짧은 산수 문제 8개(나무 심기, 주차장의 차, 초콜릿, 막대사탕, 장난감, 서버실 컴퓨터, 골프공, 베이글)에 풀이를 붙였습니다(부록 표 20). GSM8K, SVAMP, ASDiv, MAWPS 모두에 **같은 8개를** 썼습니다.
- **객관식 AQuA용 4개:** 학습 세트에서 고른 4문제와 풀이(부록 표 21)
- **상식·기호 과제:** CSQA, StrategyQA는 학습 세트에서 무작위로 고른 예시에 풀이를 직접 썼고, 학습 세트가 없는 BIG-bench 과제는 평가 세트의 처음 10개를 예시로 쓰고 나머지로 평가했습니다.
- 저자들은 이 예시들이 **프롬프트 엔지니어링을 거치지 않았다**고 밝히고, 대신 견고성을 따로 실험했습니다(3.4절).

풀이는 방정식만이 아니라 "Roger started with 5 balls." 같은 자연어 문장으로 단계를 나눕니다. 이 자연어가 중요하다는 것이 뒤의 소거 실험(ablation)에서 드러납니다.

## 실험 설정

| 항목 | 내용 |
|---|---|
| 산술 추론 | GSM8K(초등 수학 서술형), SVAMP, ASDiv, AQuA(객관식 대수), MAWPS |
| 상식 추론 | CSQA, StrategyQA, BIG-bench Date Understanding·Sports Understanding, SayCan(로봇 지시를 행동 순서로) |
| 기호 추론 | 단어들의 마지막 글자 이어 붙이기, 동전 뒤집기 상태 추적 |
| 모델 | GPT-3(text-ada-001 ~ text-davinci-002, 논문은 InstructGPT 350M~175B에 해당한다고 "추정"), LaMDA(422M~137B), PaLM(8B, 62B, 540B), UL2 20B, Codex(code-davinci-002) |
| 디코딩 | 탐욕적 디코딩(greedy decoding, 매번 가장 확률 높은 토큰 선택) |
| 비교 대상 | 같은 예시에서 풀이만 뺀 표준 few-shot 프롬프팅, 그리고 미세 조정한 기존 최고 기록 |

## 주요 결과

### 1. 창발: 작은 모델에는 해롭고, 약 1,000억 파라미터부터 효과 (그림 4, 부록 표 2)

GSM8K 정답률(%)을 모델 크기별로 보면 결과가 극적입니다.

| 모델 | 크기 | 표준 | CoT |
|---|---|---|---|
| LaMDA | 420M | 2.6 | 0.4 |
| LaMDA | 8B | 3.2 | 1.6 |
| LaMDA | 137B | 6.5 | 14.3 |
| GPT-3 | 1.3B | 2.4 | 0.5 |
| GPT-3 | 175B | 15.6 | 46.9 |
| PaLM | 8B | 4.9 | 4.1 |
| PaLM | 62B | 9.6 | 29.9 |
| PaLM | 540B | 17.9 | **56.9** |
| Codex | | 19.7 | **63.1** |

논문은 CoT가 **모델 규모의 창발 능력(emergent ability)**이라고 정리합니다. 작은 모델에서는 오히려 성능이 떨어지는데, 저자들은 작은 모델이 "유창하지만 비논리적인" 풀이를 만들어 내기 때문이라고 설명합니다(3.2절). 참고로 GSM8K의 기존 최고 기록은 GPT-3 175B를 미세 조정하고 검증기(verifier)를 붙인 55%였으므로(Cobbe et al., 2021), PaLM 540B는 예시 8개짜리 프롬프트만으로 이를 넘었습니다.

### 2. 어려운 문제일수록 효과가 크다 (부록 표 3)

MAWPS를 난이도별로 나눠 보면 PaLM 540B 기준으로 한 단계짜리 문제인 SingleOp은 표준 94.1, CoT 94.1로 차이가 없었지만, 여러 단계가 필요한 MultiArith는 42.2에서 94.7로 뛰었습니다. 이미 잘 푸는 쉬운 문제에서 CoT는 이득이 없거나 아주 작다는 뜻이고, 이는 뒤의 "언제 써야 하나"와 직결됩니다.

### 3. 무엇이 효과를 내나: 소거 실험 (그림 5, 부록 표 6)

"그냥 출력이 길어져서", "방정식을 쓰게 해서" 좋아진 것은 아닌지 확인하려고 세 가지 변형을 시험했습니다. LaMDA 137B, GSM8K 기준입니다.

| 프롬프트 | GSM8K | 검증하려던 가설 |
|---|---|---|
| 표준 | 6.5 | |
| 방정식만 출력 | 5.4 | 수식으로 바꾸는 것만으로 충분한가 |
| 점(...)만 출력 (계산량만 늘림) | 6.4 | 토큰을 더 쓰는 것 자체가 효과인가 |
| 답 먼저, 풀이는 나중에 | 6.1 | 풀이가 지식을 끌어내는 것뿐인가 |
| **CoT** | **14.3** | |

세 변형 모두 표준과 비슷했습니다. 저자들의 결론은 효과가 **자연어로 중간 단계를 표현하는 것, 그리고 답보다 먼저 순서대로 추론하는 것**에서 온다는 것입니다. 특히 "답 먼저, 풀이 나중" 실험은 실무에서 중요합니다. 출력 형식을 "정답: X, 이유: ..."로 정하면 CoT의 효과가 사라질 수 있다는 뜻이기 때문입니다.

### 4. 누가 쓰든 대체로 통한다: 견고성 (그림 6, 부록 표 6)

같은 8문제에 대해 다른 공저자 2명이 각자 풀이를 쓰거나(GSM8K 15.5, 17.6), 일부러 간결하게 쓰거나(11.1), GSM8K 학습 세트에서 무작위로 8개를 뽑아 써도(12.6, 12.7, 12.6) 모두 표준(6.5)보다 크게 높았습니다. 편차는 있지만 특정 문체에 의존하지 않는다는 결과입니다.

### 5. 상식과 기호 추론, 그리고 길이 일반화 (그림 7·8, 부록 표 4·5)

- **상식:** PaLM 540B + CoT는 StrategyQA에서 75.6%로 기존 최고(69.4%)를 넘었고, 스포츠 이해에서는 95.4%로 "도움 없이 푼 스포츠 애호가"(84%)보다 높았습니다. 다만 CSQA는 78.1에서 79.9로 이득이 작았습니다.
- **기호:** 예시에는 두 단어짜리 이름만 보여 주고 네 단어짜리로 시험하는 OOD(분포 밖) 설정에서, PaLM 540B의 마지막 글자 잇기는 표준 0.0에서 CoT 63.0으로, 동전 뒤집기(4회)는 54.8에서 90.2로 올랐습니다. 표준 프롬프팅은 두 OOD 과제 모두 실패했습니다.

### 6. 틀린 풀이는 어떻게 틀렸나 (3.2절, 부록 D)

LaMDA 137B가 GSM8K에서 정답을 낸 50개를 보면, 우연히 맞힌 2개를 빼고는 풀이도 논리적으로 맞았습니다. 오답 50개 중 46%는 계산 실수나 한 단계 누락 같은 사소한 오류였고 54%는 문제 이해 자체가 틀린 큰 오류였습니다. 계산 실수가 많다는 점에 착안해 생성된 식을 Python으로 계산하는 외부 계산기를 붙이자 PaLM 540B의 GSM8K는 56.9에서 58.6으로 더 올랐습니다(부록 표 1).

## 한계

**저자가 밝힌 것 (6절)**

- 사람의 사고 과정을 흉내 낸다고 해서 신경망이 실제로 "추론"하는지는 답하지 않은, 열린 질문입니다.
- few-shot 예시 몇 개에 풀이를 다는 비용은 작지만, 같은 방식으로 미세 조정 데이터를 만들기에는 비쌉니다.
- 추론 경로가 맞다는 보장이 없어 맞는 답과 틀린 답 모두로 이어질 수 있습니다.
- 큰 모델에서만 효과가 나타나므로 실제 서비스에 쓰기에는 비용이 큽니다.

**읽으면서 발견한 것 (필자 의견)**

- 평가가 탐욕적 디코딩 한 번의 결과입니다. 같은 저자 그룹의 후속 연구(self-consistency)가 보여 주듯, 샘플링 방식만 바꿔도 수치가 크게 달라집니다.
- GPT-3 모델 크기는 OpenAI가 공개하지 않아 논문도 "추정"이라고 적었습니다. 창발 곡선의 가로축 일부가 정확하지 않을 수 있습니다.
- 창발이 "갑자기 나타나는 능력"인지, 정답률처럼 끊어지는 지표를 써서 그렇게 보이는 것인지는 이 논문이 다루지 않습니다.
- 표 6의 SVAMP CoT 값(36.7)은 본문 표 1·2의 37.5와 조금 다릅니다. 표 6은 예시 순서를 바꾼 5회 평균이라 생긴 차이로 보입니다.

## 인사이트

**이후 어떻게 발전했나: 세 갈래의 후속 연구.**

| 논문 | 핵심 | 대표 수치 (원문 기준) |
|---|---|---|
| [Self-Consistency](https://arxiv.org/abs/2203.11171) (Wang et al., 2022-03, ICLR 2023) | 탐욕적 디코딩 대신 풀이를 여러 개 샘플링하고 최종 답을 다수결로 정함 | PaLM-540B GSM8K 56.5 → 74.4(+17.9). 40개 샘플, 10회 평균 (표 2) |
| [Zero-shot CoT](https://arxiv.org/abs/2205.11916) (Kojima et al., 2022-05, NeurIPS 2022) | 예시 없이 답변 앞에 "Let's think step by step."만 붙임 | text-davinci-002 MultiArith 17.7 → 78.7, GSM8K 10.4 → 40.7 (표 1) |
| [DeepSeek-R1](https://arxiv.org/abs/2501.12948) (DeepSeek-AI, 2025-01) | 사람이 쓴 추론 예시 없이 순수 강화학습으로 추론 능력을 유도 | 초록: 자기 성찰, 검증 같은 추론 패턴이 학습 중 창발 |

Zero-shot CoT 논문은 실무자에게 특히 유용한 표를 남겼습니다. MultiArith에서 문구만 바꿔 본 결과(표 4)를 보면 "Let's think step by step."이 78.7, "Let's think about this logically."가 74.5였고, "Don't think. Just feel."은 18.8, "Abrakadabra!"는 15.5로 아무 문구 없는 zero-shot(17.7)과 비슷했습니다. 또 이 방법은 추론 문장을 먼저 생성한 뒤 "Therefore, the answer (arabic numerals) is"로 답만 다시 뽑는 **2단계 프롬프트**였다는 점도 기억할 만합니다. 같은 논문의 표 2에서 few-shot CoT(예시 8개)는 MultiArith 93.0, GSM8K 48.7로 zero-shot CoT보다 여전히 높았습니다. 예시를 정성 들여 만드는 것이 공짜 문구보다 낫다는 원 논문의 가치는 유지된 셈입니다.

Self-consistency는 "추론을 여러 번 시키면 더 잘한다", 즉 **추론 시점에 계산을 더 쓰면 정확도가 오른다**는 생각을 처음 수치로 보여 준 연구 중 하나입니다. 저자들은 계산 비용을 한계로 들면서도 5개나 10개 경로만으로 대부분의 이득을 얻을 수 있다고 적었습니다. 그리고 DeepSeek-R1 초록은 CoT 프롬프팅의 성공이 "사람이 주석을 단 대량의 시연에 크게 의존"한다고 지적하며, 그 의존을 강화학습으로 없앴다고 주장합니다. 원 논문의 "예시에 풀이를 보여 주면 큰 모델이 따라 한다"에서 "모델이 스스로 긴 풀이를 쓰도록 학습시킨다"로 축이 옮겨 간 것입니다.

**지금 프롬프트에 CoT를 언제 쓰고, 언제 안 써도 되나.** 2026-10-24 기준 주요 공급자의 공식 문서는 추론 모델에 대해 공통적으로 "직접 단계를 지시하지 말라"는 쪽입니다.

| 공급자 문서 | 추론(thinking) 모델에 대한 CoT 관련 권고 |
|---|---|
| [OpenAI Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices) | 모델이 내부적으로 추론하므로 CoT 프롬프트를 피하라. "think step by step"은 성능을 올리지 않을 수 있고 때로 해친다. zero-shot을 먼저, 필요하면 few-shot |
| [Claude Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) | 손으로 쓴 단계별 계획보다 "think thoroughly" 같은 일반적 지시가 더 나은 경우가 많다. 예시(multishot)는 thinking과 함께 써도 효과가 있다. 수동 CoT는 thinking이 꺼져 있을 때의 대안이며, 최근 일부 모델은 추론을 별도 태그로 써 달라는 요청을 거절할 수 있으니 thinking 기능과 effort 설정을 쓰라 |
| [Gemini Thinking](https://ai.google.dev/gemini-api/docs/thinking) | 대부분의 모델에서 thinking이 기본으로 켜져 있고, 단순 조회·분류는 낮게, 수학·고급 코딩·다단계 계획은 높게 `thinking_level`을 조절하라 |

여기에 연구 결과를 겹치면 필자는 다음과 같이 정리합니다.

- **CoT를 쓸 만한 경우:** thinking 기능이 없거나 꺼진 모델(비용 때문에 작은 모델을 쓸 때 포함)로 수학, 논리, 다단계 계산, 상태 추적을 시킬 때입니다. Sprague et al.의 메타 분석([To CoT or not to CoT?](https://arxiv.org/abs/2409.12183), ICLR 2025)은 100편 이상의 논문과 14개 모델·20개 데이터셋 실험을 바탕으로 CoT의 이득이 **주로 수학과 논리 과제에 집중**되고, MMLU에서는 문제나 답에 등호(=)가 없으면 CoT가 있으나 없으나 정확도가 거의 같다고 보고했습니다. 원 논문의 표 3(한 단계 문제엔 이득 없음)과 같은 방향입니다. 이때는 원 논문의 교훈대로 **풀이를 먼저, 답을 나중에** 쓰게 하고, 답은 `<answer>` 같은 태그로 분리해 파싱하는 편이 좋습니다.
- **안 써도 되는 경우:** 추론 모델(thinking이 켜진 모델)에는 "단계별로 생각하라"를 덧붙일 필요가 없고, 공식 문서는 오히려 해로울 수 있다고 말합니다. 대신 effort나 thinking 수준 같은 파라미터로 추론량을 조절합니다. 단순 분류, 추출, 사실 조회도 CoT의 이득이 작고 지연과 토큰 비용만 늘립니다.
- **오히려 해로운 경우:** [Mind Your Step (by Step)](https://arxiv.org/abs/2410.21333)은 인지심리학에서 "숙고하면 사람도 더 못하는" 것으로 알려진 과제 6개를 골라 시험했고, 그중 세 과제에서 CoT가 성능을 크게 떨어뜨렸다고 보고했습니다(o1-preview가 GPT-4o 대비 최대 36.3%p 낮음).
- **CoT보다 도구가 나은 경우:** 원 논문의 외부 계산기 실험, 그리고 Sprague et al.이 CoT가 기호 해석기(symbolic solver)를 쓰는 것보다 못하다고 보고한 점을 보면, 정확한 계산은 모델의 풀이보다 코드 실행 도구에 맡기는 편이 낫습니다.

**한계와 반론: 풀이를 믿어도 되나.** 원 논문은 CoT가 모델 동작을 들여다보는 "해석 가능한 창"이 된다고 했지만(2절), 단서를 붙였습니다("완전한 특성화는 열린 질문"). 이후 연구는 이 창이 생각보다 흐리다는 쪽입니다. [Lanham et al.](https://arxiv.org/abs/2307.13702)(2023)은 풀이에 일부러 오류를 넣거나 바꿔 써 보는 개입 실험에서, 과제에 따라 모델이 풀이에 크게 의존하기도 하고 거의 무시하기도 하며, **모델이 클수록 대부분의 과제에서 덜 충실한(unfaithful) 추론**을 한다고 보고했습니다. [Chen et al.](https://arxiv.org/abs/2505.05410)(2025)은 추론 모델이 프롬프트 속 힌트를 실제로 쓰고도 풀이에서 그 사실을 밝히는 비율이 대부분 20% 미만이었다고 보고했습니다. 실무적으로는 **풀이를 감사 기록으로 쓰되, 정답 검증의 근거로 쓰지는 말라**는 뜻으로 읽힙니다. 최종 답은 테스트, 계산 도구, 별도 검증 단계로 확인해야 합니다.

**블로그의 기존 글과의 연결.** [LiveMACE 소개](/papers/2026/10/20/livemace.html)는 결과(수익률)가 비슷해도 과정(도구 사용, 규칙 준수)이 다를 수 있으니 따로 측정하라는 논문이었습니다. CoT의 충실성 문제는 같은 질문을 추론 단계에 던집니다. 에이전트의 의사결정 기록(trace)을 평가할 때도, 모델이 써 놓은 "이유"와 실제 행동을 결정한 요인이 다를 수 있다는 점을 감안해야 합니다.

**앞으로 지켜볼 점.** 추론 모델의 thinking이 점점 기본값이 되면서, 개발자가 조절하는 대상이 "프롬프트 문구"에서 "추론량 파라미터(effort, thinking level)"로 옮겨 가고 있습니다. 다음에 볼 것은 (1) 추론량을 과제 난이도에 맞춰 자동으로 정하는 기능이 비용 대비 얼마나 정확한지, (2) 풀이의 충실성을 높이는 학습 방법이 나오는지입니다. 후자가 해결되기 전까지는 CoT를 성능 도구로는 쓰되 설명 도구로는 조심해서 쓰는 것이 안전합니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models (arXiv:2201.11903)](https://arxiv.org/abs/2201.11903)
- [NeurIPS 2022 프로시딩 페이지](https://proceedings.neurips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract-Conference.html)
- [Large Language Models are Zero-Shot Reasoners (arXiv:2205.11916)](https://arxiv.org/abs/2205.11916) · [코드](https://github.com/kojima-takeshi188/zero_shot_cot)
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models (arXiv:2203.11171)](https://arxiv.org/abs/2203.11171)
- [DeepSeek-R1 (arXiv:2501.12948)](https://arxiv.org/abs/2501.12948)
- [To CoT or not to CoT? (arXiv:2409.12183)](https://arxiv.org/abs/2409.12183)
- [Mind Your Step (by Step) (arXiv:2410.21333)](https://arxiv.org/abs/2410.21333)
- [Measuring Faithfulness in Chain-of-Thought Reasoning (arXiv:2307.13702)](https://arxiv.org/abs/2307.13702)
- [Reasoning Models Don't Always Say What They Think (arXiv:2505.05410)](https://arxiv.org/abs/2505.05410)
- [OpenAI: Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
- [Claude: Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Gemini API: Thinking](https://ai.google.dev/gemini-api/docs/thinking)

[← 논문 소개 목록]({{ "/papers.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
