---
layout: default
title: "[기술 소개] Cohere Rerank 5: 재정렬과 핵심 구절 추출(Context Focus)을 한 번의 호출로"
description: "Cohere Rerank 5(Pro, Fast)의 Context Focus 구간 점수, 보정된 관련성 점수, API 사용법과 토큰 단위 가격을 공식 문서로 정리하고, 자체 지표 RCP-nDCG@10으로 잰 벤치마크를 읽을 때의 주의점을 짚었습니다."
date: 2026-11-20 10:30:00 +0900
categories: [tech]
---

# [기술 소개] Cohere Rerank 5: 재정렬과 핵심 구절 추출(Context Focus)을 한 번의 호출로

- **발표:** Cohere, 2026년 10월 21일
- **원문:** [공식 발표](https://cohere.com/blog/rerank-5) · [모델 문서](https://docs.cohere.com/docs/rerank) · [Rerank API 레퍼런스](https://docs.cohere.com/reference/rerank) · [릴리스 노트](https://docs.cohere.com/changelog/rerank-v5) · [가격 페이지](https://cohere.com/pricing)
- **한눈에 (2026-11-20 기준):**
  - 모델은 `rerank-v5.0-pro`(약 20억 파라미터)와 `rerank-v5.0-fast`(약 5억 파라미터) 두 가지이고, 컨텍스트 길이는 둘 다 32,768토큰입니다.
  - API 가격은 100만 토큰당 Pro $0.05, Fast $0.02입니다(발표문과 가격 페이지에서 같은 값 확인).
  - 새 기능은 두 가지입니다. 문서 안에서 질의와 관련된 구간을 점수와 함께 돌려주는 Context Focus, 그리고 0.7이면 "쓸모 있을 확률 70%"로 읽을 수 있다는 보정된(calibrated) 관련성 점수입니다.
  - 한국어는 문서가 꼽은 11개 중점 언어에 들어 있고, 발표문의 다국어 표에서 Pro 91.8점, Fast 89.9점입니다(Cohere 내부 평가 세트, 자체 발표).
- **주의 (2026-11-20 기준):**
  - **가중치가 공개되지 않은 유료 API 모델입니다.** 모델 문서는 아키텍처를 "Proprietary"로 적고 있습니다. 직접 운영하려면 Model Vault(GPU 시간당 과금)나 영업팀을 통한 프라이빗 배포를 써야 합니다.
  - **이 글의 벤치마크 수치는 모두 Cohere 자체 발표입니다.** 게다가 채점 지표도 Cohere가 만든 RCP-nDCG@10이고, Cohere는 5세대 모델을 이 지표에 맞춰 최적화했다고 밝혔습니다. 제3자 재현 결과는 이 글을 쓰는 시점에 확인하지 못했습니다.
  - 과금 단위가 토큰입니다. 가격 페이지의 FAQ와 가격 안내 문서에는 여전히 "검색 단위(search unit)" 설명이 남아 있어, 기존 Rerank 사용자는 비용 계산 방식을 다시 확인해야 합니다.

## 한 줄 요약

**Cohere가 문서를 다시 줄 세우는 것에 더해, 같은 호출에서 문서 속 핵심 구간까지 골라 주는 리랭커 Rerank 5를 정식 출시했습니다.** 순위 품질 향상보다 눈여겨볼 변화는 리랭커의 역할이 "정렬"에서 "LLM에 무엇을 얼마나 넣을지 정하는 관문"으로 넓어졌다는 점입니다.

## 배경

RAG(검색 증강 생성, Retrieval-Augmented Generation) 파이프라인은 보통 두 단계로 문서를 찾습니다. 먼저 키워드 검색이나 벡터 검색으로 후보를 넉넉히 가져오고, 그다음 리랭커(reranker, 재정렬 모델)가 후보를 질의와 하나씩 대조해 순서를 다시 매깁니다. Cohere 문서는 Rerank가 질의의 토큰과 문서의 토큰을 합쳐 한 입력으로 처리한다고 설명합니다. 문서를 미리 벡터로 바꿔 두는 임베딩 검색과 달리 질의 시점에 원문을 직접 읽기 때문에, 릴리스 노트의 표현대로 모델을 바꿔도 재색인이나 재임베딩이 필요 없습니다.

지금까지 리랭커의 출력은 사실상 "순서"였습니다. 발표문은 기존 리랭커의 점수가 정렬에만 쓸모가 있었고, 좋은 점수의 기준이 모델마다 달라 팀이 모델별로 기준값을 조정하고 업그레이드 때마다 다시 맞춰야 했다고 적습니다. 발표문이 기존 방식으로 전제하는 것도 점수와 무관하게 "상위 k개"를 고정으로 LLM에 넘기는 구성입니다.

발표문이 내세우는 문제의식은 비용입니다. "LLM이 읽는 토큰은 모두 돈을 내는 토큰이고, 어떤 토큰을 읽을지는 검색이 정한다"는 것입니다. 에이전트가 더 긴 문서를 대상으로 더 많이 검색하게 되면서, 검색 단계가 비용과 지연, 답변 품질을 함께 좌우하는 지렛대가 됐다는 설명입니다. Rerank 5는 Embed 5, Parse 5와 함께 Cohere의 5세대 검색 모델군을 이룹니다.

## 핵심 내용

### 1. 두 모델: Pro와 Fast

[모델 문서](https://docs.cohere.com/docs/rerank) 기준 사양입니다.

| 항목 | rerank-v5.0-pro | rerank-v5.0-fast |
|---|---|---|
| 파라미터 | 약 20억 | 약 5억 |
| 컨텍스트 | 32,768토큰(질의와 문서 합산) | 같음 |
| 용도 | 복잡하고 추론이 필요한 질의, 길거나 도메인 특화된 문서 | 지연과 처리량이 중요한 대량 검색, 에이전트 루프 |
| 입력 | 텍스트 전용. JSON, 표 같은 반정형 데이터는 YAML 문자열로 | 같음 |
| 출력 | 0~1 사이의 보정된 점수와 순위 | 같음 |
| Context Focus | 지원 | 지원 |
| 가격 | 100만 토큰당 $0.05 | 100만 토큰당 $0.02 |

언어는 100개 이상을 지원하며, 문서는 영어, 중국어, 한국어, 힌디어, 일본어, 스페인어, 독일어, 프랑스어, 아랍어, 러시아어, 포르투갈어에 중점을 두었다고 적고 있습니다. 두 모델은 엔드포인트와 요청 형식이 같아서 `model` 값만 바꾸면 됩니다.

### 2. Context Focus: 문서 안의 구간에 점수를 매긴다

Context Focus는 Rerank 요청에 `relevant_spans` 객체를 넣으면 켜지는 선택 기능이고, 기본값은 꺼짐입니다. [API 레퍼런스](https://docs.cohere.com/reference/rerank)의 정의는 다음과 같습니다.

| 필드 | 의미 |
|---|---|
| `mode` | `"enabled"` 또는 `"disabled"`. 필수 |
| `threshold` | 이 값보다 점수가 높은 구간만 응답에 포함. 기본값 0.1 |
| `max_spans` | 문서당 돌려줄 구간의 최대 개수. 지정하지 않으면 전부 반환 |

켜면 각 결과에 문서 단위 `relevance_score`와 함께 `relevant_spans` 목록이 붙습니다. 구간 하나는 `start`, `end`, `score`로 이루어집니다. `start`와 `end`는 **원문 문자열의 문자 위치(유니코드 코드포인트 기준)**이고 `[start, end)` 범위를 뜻합니다. 구간은 관련성이 높은 순서로 정렬되어 오며, 기준을 넘는 구간이 하나도 없으면 그 결과에서는 `relevant_spans` 필드 자체가 빠집니다.

눈여겨볼 점은 모델이 요약문을 새로 쓰지 않는다는 것입니다. 원문의 위치만 돌려주므로 LLM에 넘기는 텍스트는 항상 원문의 일부이고, 같은 오프셋으로 화면에서 근거를 강조 표시할 수도 있습니다. 문서는 기준값을 높일수록 더 많은 텍스트가 제거된다고 설명하고, 발표문은 이를 "다이얼"에 비유합니다.

### 3. 보정된 관련성 점수: 상위 k개 대신 기준값으로 자르기

발표문에 따르면 Rerank 5의 `relevance_score`는 요청이나 응답 형식의 변화 없이 "그 문서가 쓸모 있을 확률"로 읽을 수 있습니다. "쓸모 있을 가능성이 그렇지 않을 가능성보다 높다"의 경계는 Pro가 0.50, Fast가 0.45이고, BRIGHT, NanoBEIR, ViDoRe V3 전반에서 Pro의 기본 기준값은 0.47~0.53 사이에 머문다고 합니다.

Cohere는 이를 모델 학습에 쓰이지 않은 두 가지 사람 판정으로 확인했다고 밝혔습니다. 블라인드 평가자 패널(문서 2,262개, 5단계 척도에서 평균 "Useful" 이상이면 유용)과 NIST TREC Deep Learning 평가자(문서 20,646개, 0~3 척도에서 2 이상이면 유용)입니다. 결과는 ECE(기대 보정 오차, Expected Calibration Error. 점수와 실제 유용 비율의 평균 차이로 0이 완벽)로 요약됩니다.

| 모델 | ECE (사람 패널) | ECE (NIST) |
|---|---|---|
| Rerank 5 Pro | 0.058 | 0.057 |
| Rerank 5 Fast | 0.058 | 0.058 |
| Rerank 4 Pro | 0.384 | 0.309 |
| Voyage AI Rerank 3 | 0.234 | 0.307 |
| Voyage AI Rerank 3 Lite | 0.226 | 0.325 |

(Cohere 자체 측정. 낮을수록 좋음) 발표문은 예로 Voyage AI Rerank 3가 0.55 근처로 점수를 준 문서 중 사람 평가자가 유용하다고 본 것은 24%뿐이었다고 적었습니다.

점수가 확률처럼 읽히면 달라지는 것으로 발표문은 세 가지를 듭니다. 고정된 상위 k개 대신 기준값을 넘는 문서만 넘길 수 있고(좁은 질의는 적게, 넓은 질의는 많이), 기준을 넘는 문서가 없으면 에이전트가 질의를 다시 쓰거나 모른다고 답할 수 있으며, 도메인과 모델 크기가 달라도 기준값 하나를 유지할 수 있다는 것입니다.

### 4. 토큰 절감 실험 두 가지

Context Focus의 효과로 발표문이 제시한 실험은 두 종류입니다. 둘 다 Cohere 자체 실험입니다.

**(1) 답변 품질 대 제거 비율.** 후보 50개에서 상위 5개 문서를 고른 뒤 여러 기준값으로 텍스트를 걷어 내고, 남은 내용으로 Qwen3.5-9B가 답하고 Qwen3.5-35B가 채점했습니다. ViDoRe, UNICORN, BRIGHT-Pro, 에이전트형 QA에서 가져온 단일 턴 QA 데이터셋 30개(각 최대 500개 질의)의 평균입니다. 아래는 발표문 차트에서 읽은 값입니다.

| 제거 비율 | Rerank 5 Pro + Context Focus | RECOMP + bge-reranker-v2-m3 |
|---|---|---|
| 0% | 55% | 53% |
| 50% | 53% | 43% |
| 75% | 48% | 32% |
| 90% | 41% | 22% |
| 95% | 35% | 15% |

발표문의 "절반을 지워도 답변 품질 96% 유지"는 55%에서 53%로 2%p 내려간 것을 비율로 표현한 값이고, "4분의 3을 지우면 87% 유지"는 55%에서 48%로 7%p 내려간 것입니다. 발표문은 품질을 더 내주면 컨텍스트를 최대 10분의 1로 줄일 수 있다고 덧붙입니다.

**(2) 검색 에이전트.** 검색이 유일한 도구인 에이전트(glm-5-3-flash, 검색당 결과 5개)에게 검색 스택을 한 단계씩 쌓아 주며 17개 데이터셋(데이터셋당 질문 50개)에서 정확도와 과제당 총 토큰을 쟀습니다. BM25(단어 일치 기반의 전통적인 키워드 검색)에서 시작해, Rerank 5 Pro가 상위 100개를 재정렬하고, 그 위에 Context Focus를 켭니다.

| 구성 | 전체 17개: 정확도 / 과제당 토큰 | 심층 검색 6개: 정확도 / 과제당 토큰 |
|---|---|---|
| BM25 | 45.9% / 49.9만 | 38.7% / 45.8만 |
| + Rerank 5 Pro | 48.6% / 48.9만 | 44.0% / 43.5만 |
| + Context Focus (0.1) | 56.6% / 39.7만 | 49.7% / 35.3만 |
| + Context Focus (0.4) | 58.3% / 32.3만 | 52% / 27.2만 |

(발표문 차트의 값. 토큰은 실행 중 모든 LLM 호출의 입력, 출력, 추론 토큰을 더한 것이며 캐시된 토큰도 포함. 심층 검색 6개는 BrowseComp-Plus, MedBrowseComp, WebWalkerQA, SealQA, HERB, DRBench)

기준값 0.4에서 전체 스택은 BM25만 쓸 때보다 토큰을 35% 덜 쓰면서 정확도는 46%에서 58%로 올랐다는 것이 발표문의 요약입니다. 표에서 보이듯 이 실험에서는 재정렬만 더했을 때의 정확도 상승(2.7%p)보다 Context Focus를 켰을 때의 상승(8.0%p)이 더 큽니다.

### 5. 채점 지표 RCP-nDCG@10: Cohere가 만든 자

순위 품질 수치를 읽으려면 지표부터 알아야 합니다. nDCG(정규화 할인 누적 이득, 관련성이 높은 문서가 위쪽에 있을수록 점수가 높은 순위 지표)는 미리 만들어 둔 정답 판정(qrel)에 의존하는데, 판정되지 않은 문서는 실제로 관련이 있어도 틀린 것으로 처리됩니다. Cohere는 2026년 9월 30일 [별도 글](https://cohere.com/blog/rcp-ndcg)에서 이 문제를 다루며 RCP-nDCG@10(Rubric-Calibrated Preferences nDCG@10)을 내놓았습니다.

방식은 이렇습니다. 보정된 AI 판정 모델이 검색된 모든 문서를 평가합니다. 문서마다 모든 질의에 똑같이 적용되는 예/아니오 질문 5개에 답하고, 문서들을 묶음으로 서로 비교해 어느 쪽이 나은지도 추정한 뒤, 비교 결과로 순서를 정하고 질문 답변으로 질의 간에 공유되는 척도에 올립니다. 정답 목록에 없던 관련 문서도 점수를 받을 수 있게 하는 것이 목적입니다.

Cohere는 사람 평가로 이 지표를 검증했다고 밝혔습니다. 평가자 46명이 시스템 이름을 가린 채 상위 5개 결과를 비교했고, 판정이 난 289건의 대결에서 RCP-nDCG가 사람이 선호한 시스템을 고른 비율은 77%, 기존 nDCG는 52%였습니다(두 지표가 엇갈리는 대결을 일부러 많이 뽑은 표본). 방법론은 [논문(arXiv:2609.35739)](https://arxiv.org/abs/2609.35739)과 [코드 저장소](https://github.com/cohere-ai/rcp)(Apache-2.0)로 공개되어 있습니다. 다만 같은 글에서 Cohere는 5세대 Embed와 Rerank를 기존 nDCG가 아니라 이 지표에 맞춰 최적화했고, 그래서 "기존 nDCG로만 보면 항상 가장 강해 보이지는 않을 수 있다"고 적었습니다. 이 점은 아래 한계에서 다시 다룹니다.

## 성능과 비교

아래 수치는 모두 **Cohere가 직접 측정해 발표문에 실은 값**이고 지표는 RCP-nDCG@10입니다. 첫 표는 발표문의 막대 차트에서 읽은 값입니다.

| 벤치마크 | R5 Pro | R5 Fast | R4 Pro | Voyage 3 | Voyage 3 Lite | Qwen3 8B | Qwen3 0.6B |
|---|---|---|---|---|---|---|---|
| ViDoRe V3 (8개) | 92.2 | 90.6 | 89.5 | 90.6 | 87.9 | 85.1 | 75.3 |
| BEIR (13개) | 90.4 | 88.1 | 87.4 | 88.6 | 86.1 | 83.8 | 78.9 |
| BRIGHT (12개) | 82.2 | 77.5 | 69.8 | 76.4 | 69.4 | 69.8 | 58.4 |
| nanoMTEB (13개) | 87.3 | 85.1 | 82.3 | 83.9 | 80.7 | 82.1 | 77.9 |

(R5는 Cohere Rerank 5, R4는 Rerank 4, Voyage는 Voyage AI Rerank 3 계열, Qwen3는 Qwen3-Reranker. 괄호 안은 데이터셋 수)

- 발표문은 46개 데이터셋 중 Pro가 39개에서 1위, 43개에서 2위 이내라고 밝혔습니다.
- 격차가 가장 큰 곳은 추론이 필요한 검색을 재는 BRIGHT입니다. Pro는 Voyage AI Rerank 3보다 5.8점, 이전 세대 Rerank 4 Pro보다 12.4점 높습니다. 나머지 셋에서 가장 강한 외부 모델과의 격차는 ViDoRe V3 1.6점, BEIR 1.8점, nanoMTEB 3.4점입니다.
- Fast는 네 벤치마크 모두에서 이전 세대 주력인 Rerank 4 Pro를 넘습니다. Voyage AI Rerank 3와 비교하면 BRIGHT와 nanoMTEB에서는 앞서고, ViDoRe V3에서는 같고, BEIR에서는 0.5점 낮습니다.

**다국어 (Cohere 내부 평가 세트, 20개 언어 74개 데이터셋 중 발표문이 고른 6개 언어)**

| 모델 | 스페인어 | 프랑스어 | 독일어 | 아랍어 | 일본어 | 한국어 |
|---|---|---|---|---|---|---|
| Rerank 5 Pro | 91.2 | 90.5 | 90.6 | 89.7 | 89.4 | 91.8 |
| Rerank 5 Fast | 88.6 | 88.6 | 88.6 | 86.5 | 86.8 | 89.9 |
| Voyage AI Rerank 3 | 89.4 | 88.2 | 89.4 | 87.4 | 86.7 | 89.9 |
| Rerank 4 Pro | 88.6 | 88.1 | 88.6 | 87.5 | 89.3 | 89.8 |
| Voyage AI Rerank 3 Lite | 86.0 | 84.7 | 86.3 | 82.0 | 83.8 | 86.6 |
| Qwen3-Reranker-8B | 85.4 | 84.0 | 86.2 | 84.4 | 85.9 | 88.0 |
| Qwen3-Reranker-0.6B | 76.9 | 74.2 | 78.0 | 74.6 | 78.6 | 80.8 |

한국어에서 Pro는 Rerank 4 Pro보다 2.0점, Voyage AI Rerank 3보다 1.9점 높고, Fast는 Voyage AI Rerank 3와 같은 89.9점입니다. 발표문은 Pro가 비영어 19개 언어 중 14개에서 1위라고 밝혔습니다. 이 평가 세트는 공개 벤치마크가 아니라 Cohere 내부 세트라는 점을 감안해야 합니다.

**그 밖의 수치 (모두 자체 발표)**

- **파싱된 PDF:** PDF에서 추출한 텍스트 데이터셋 47개 평균에서 Pro 89.9, Fast 88.5, Voyage AI Rerank 3 88.4, Rerank 4 Pro 88.3. 문서 파싱에는 Gemini 1.5 Flash를 썼습니다.
- **처리량과 지연:** NVIDIA A100 GPU 한 장에서 1,000토큰 문서 기준 Fast는 초당 약 187개, Pro는 65개를 재정렬했습니다(2.9배). 요청당 문서 96개, 동시 요청 8개 조건의 요청 지연 중앙값은 차트 기준 Fast 4.1초, Pro 11.7초입니다. 요청 하나가 약 9.6만 토큰을 처리하는 부하 조건이므로, 문서가 짧거나 적은 일반적인 호출의 지연과는 다릅니다.

## 써 볼 수 있나

**접근 경로 (2026-11-20 기준, 모델 문서 기준):** Cohere API, Model Vault, Microsoft Foundry, Amazon SageMaker, OpenRouter(2026년 11월 4일 추가), North(Cohere의 업무용 AI 플랫폼), 그리고 영업팀 문의를 통한 VPC 또는 온프레미스 프라이빗 배포입니다. 모델 문서는 Context Focus에 대해 "Cohere API를 통해 제공된다"고만 적고 있어, 다른 경로에서의 지원 여부는 각 플랫폼에서 확인해야 합니다.

**가격 (2026-11-20 기준, [가격 페이지](https://cohere.com/pricing)):**

| 항목 | 가격 |
|---|---|
| Rerank 5 Pro | 100만 토큰당 $0.05 |
| Rerank 5 Fast | 100만 토큰당 $0.02 |
| 체험(Trial) 키 | 무료. 단 상용 목적 사용 불가 |
| Model Vault | GPU 종류와 복제본 수 기준 시간당 과금 |

감을 잡기 위한 어림 계산을 해 보면, 질의 한 번에 1,000토큰짜리 후보 100개를 재정렬할 때 문서 토큰만 약 10만 토큰이므로 Pro는 약 $0.005, Fast는 약 $0.002입니다. 이 계산은 필자가 문서 토큰만 단순 합산한 것이고, 질의 토큰이 문서마다 다시 세어지는지 같은 정확한 과금 토큰 산정 방식은 문서에서 확인하지 못했습니다. 실제 값은 응답의 `meta.billed_units.input_tokens`로 확인할 수 있습니다.

**속도 제한 ([문서](https://docs.cohere.com/docs/rate-limits) 기준):** Rerank 엔드포인트는 체험 키 분당 10회, 프로덕션 키 분당 1,000회입니다. 체험 키는 월 1,000회 호출로 제한됩니다.

**SDK:** 공식 Python SDK `cohere`는 PyPI 기준 7.3.2(2026-11-19 업로드, MIT, Python 3.10 이상)가 최신입니다. 7.3.0이 Rerank 5 출시일인 2026-10-21에 올라왔고, SDK 저장소(cohere-ai/cohere-python)의 v2 클라이언트에 `relevant_spans` 매개변수와 타입이 들어 있습니다. 빠른 시작 문서의 설치 명령은 `pip install -U cohere`입니다.

### 예제 1: Context Focus를 켠 호출 (발표문 예제)

아래는 발표문에 실린 예제를 그대로 옮긴 것입니다. **API 키가 없어 필자가 직접 실행하지는 않았습니다.**

```python
import os
import requests

query = "How much did card provisions rise in Q3?"

documents = [
    "Market update. Commercial real estate prices fell 6% this year as office "
    "vacancies climbed. Analysts expect refinancing pressure on landlords to "
    "persist into next year.",
    "Q3 credit quality. Net charge-offs held steady at 0.42% of average loans. "
    "Commercial real estate loans stood at $14.3 billion, or 9% of total loans. "
    "Office properties accounted for $2.1 billion of that balance. Card "
    "provisions rose $85 million on higher delinquencies.",
    "Q3 mortgage lending. Residential mortgage originations rose 11% as rates "
    "eased. The average loan-to-value ratio on new lending was 68%.",
]

response = requests.post(
    "https://api.cohere.com/v2/rerank",
    headers={"Authorization": f"Bearer {os.environ['CO_API_KEY']}"},
    json={
        "model": "rerank-v5.0-pro",
        "query": query,
        "documents": documents,
        "top_n": 2,
        "relevant_spans": {"mode": "enabled", "threshold": 0.4, "max_spans": 10},
    },
)
response.raise_for_status()

for result in response.json()["results"]:
    document = documents[result["index"]]
    print(f"{result['relevance_score']:.2f}  {document[:60]}...")
    for span in result.get("relevant_spans") or []:
        print(f"    {span['score']:.2f}  {document[span['start']:span['end']]}")
```

두 번째 문서는 대부분이 상업용 부동산 대출 이야기이고 질문의 답은 마지막 문장("Card provisions rose $85 million...")에만 있습니다. 문서 단위로 넘기면 네 문장이 모두 LLM에 들어가지만, 구간 단위로 넘기면 해당 문장만 들어갑니다. API 레퍼런스의 Python SDK 예제는 같은 내용을 `co.rerank(model=..., query=..., documents=..., top_n=3, relevant_spans={"mode": "enabled", "threshold": 0.1, "max_spans": 3})` 형태로 호출합니다.

### 예제 2: 기준값으로 거르고 구간만 이어 붙이기 (필자 작성)

응답을 LLM용 컨텍스트로 바꾸는 후처리의 한 가지 방법입니다. 공식 예제가 아니라 필자가 응답 형식에 맞춰 쓴 것입니다. **API는 호출하지 않았고, API 레퍼런스에 실린 샘플 응답 값을 넣어 로컬에서 실행해 동작을 확인했습니다.**

```python
DOC_THRESHOLD = 0.5   # 문서 단위 컷 (발표문이 말하는 Pro의 "유용할 가능성이 더 높다" 경계)
SPAN_THRESHOLD = 0.4  # 구간 단위 컷 (요청의 threshold로 지정해도 됨)

def focused_context(documents, results, doc_threshold, span_threshold):
    blocks = []
    for r in results:
        if r["relevance_score"] < doc_threshold:
            continue
        doc = documents[r["index"]]
        spans = [s for s in (r.get("relevant_spans") or []) if s["score"] >= span_threshold]
        if not spans:                          # 구간이 없으면 문서 전체를 넘긴다
            blocks.append(doc)
            continue
        spans.sort(key=lambda s: s["start"])   # 응답은 점수순이므로 원문 순서로 되돌린다
        blocks.append(" ".join(doc[s["start"]:s["end"]].strip() for s in spans))
    return blocks  # 빈 목록이면 질의를 다시 쓰거나 "모른다"고 답하게 한다
```

샘플 응답(문서 점수 0.84, 구간 `[0, 139)` 점수 0.9997과 `[139, 165)` 점수 0.338, 그리고 문서 점수 0.086인 두 번째 결과)을 넣으면 첫 문서의 첫 문장("Washington, D.C. ... is the capital of the United States.")만 남고, 두 번째 결과는 문서 단위 컷에서 걸러졌습니다. 확인 과정에서 알게 된 점 하나를 적어 둡니다. API 레퍼런스의 요청 예시와 샘플 응답은 문서 순서가 서로 맞지 않습니다. 응답의 `index: 2`에 딸린 구간 경계(139, 165)는 요청 예시의 세 번째 문서가 아니라 네 번째인 Washington, D.C. 문서의 문장 경계와 일치하며, 릴리스 노트 예제의 문서 순서로 놓으면 정확히 맞습니다. 문서의 샘플 출력은 설명용으로만 보는 편이 안전합니다.

### 도입할 때 확인할 설정

- **`max_tokens_per_doc`의 기본값은 4096입니다.** 컨텍스트 길이가 32,768토큰이어도, [모범 사례 문서](https://docs.cohere.com/docs/reranking-best-practices)에 따르면 Rerank 5에서는 긴 문서가 이 값으로 잘립니다. 긴 문서를 통째로 넣고 구간을 찾게 하려면 이 값을 올려야 합니다. 잘린 뒷부분에서는 구간이 나올 수 없을 것으로 보입니다(문서에 명시된 내용은 아니며 필자의 추론입니다).
- **요청당 문서 수:** Rerank 5는 한 요청에 최대 10,000개까지 받지만, API 레퍼런스는 성능을 위해 1,000개를 넘기지 말라고 권합니다.
- **반정형 데이터:** JSON이나 표는 YAML 문자열로 바꿔 넣으라고 권합니다. 긴 문자열은 잘리므로 키 순서가 중요하고, Python에서는 `yaml.dump(doc, sort_keys=False)`로 순서를 유지합니다.
- **한국어 오프셋:** 구간 위치는 유니코드 코드포인트 기준이므로 Python 문자열 슬라이싱에는 그대로 쓸 수 있습니다. 문자열 길이를 다르게 세는 언어나 바이트 단위로 자르는 코드에서는 변환이 필요할 수 있습니다(일반적인 주의 사항이며, Cohere 문서에 언어별 안내는 없습니다).

## 한계와 논란

- **수치의 출처와 자가 모두 Cohere입니다.** 측정 주체가 Cohere이고, 지표도 Cohere가 만든 RCP-nDCG@10이며, 모델도 그 지표에 맞춰 최적화했습니다. 사람 평가로 지표를 검증했다는 근거와 공개된 논문, 코드가 있지만, 기존 nDCG 기준 수치는 발표문 본문에 실려 있지 않습니다. 발표문이 링크한 전체 결과 스프레드시트는 필자의 환경에서 내려받기가 인증 오류(401)로 막혀 읽지 못했고, 이 글은 발표문 본문과 차트의 값만 사용했습니다.
- **비교 대상이 제한적입니다.** 외부 모델은 Voyage AI Rerank 3와 3 Lite, Qwen3-Reranker 8B와 0.6B 네 가지입니다. 발표문의 "시험한 모든 경쟁 모델을 앞섰다"는 이 범위 안의 이야기입니다.
- **텍스트만 받습니다.** 모델 문서의 알려진 한계 첫 줄입니다. 발표문은 시각 자료가 많은 문서에서의 강점을 내세우고 ViDoRe V3 점수를 제시하지만, 이미지를 직접 읽는 것이 아니라 텍스트로 바뀐 내용을 재정렬하는 것입니다. 실제 품질은 앞단의 파서에 좌우될 것으로 보입니다.
- **지시문으로 관련성 기준을 바꿀 수 없습니다.** 모델 문서는 Rerank 5가 "관련성 판단 방식을 바꾸는 지시(instruction)를 지원하지 않는다"고 적고 있습니다. "최신 문서를 우선하라" 같은 조건은 리랭커 밖에서 처리해야 합니다.
- **Context Focus가 잘 안 맞는 경우가 있습니다.** 문서에 따르면 Context Focus는 초점이 분명한 질의에 가장 잘 맞고, 요약처럼 넓은 요청에는 문서 전체가 필요하며, 표, 양식, 코드는 산문보다 깔끔하게 나뉘지 않습니다.
- **토큰 절감 실험의 조건이 좁습니다.** 답변 품질 실험의 답변 모델(Qwen3.5-9B)과 채점 모델(Qwen3.5-35B)은 이름으로 보아 비교적 작은 모델이고, 차트에 그려진 비교 대상은 "RECOMP + bge-reranker-v2-m3" 하나입니다. 에이전트 실험의 출발점은 BM25 단독이며, 벡터 검색이나 하이브리드 검색 위에서의 결과는 제시되지 않았습니다. 더 강한 답변 모델이나 더 좋은 1차 검색 위에서는 이득의 크기가 달라질 수 있습니다.
- **문서 간 불일치가 남아 있습니다.** 가격 페이지 FAQ와 가격 안내 문서는 Rerank가 "검색 수"로 과금된다고 설명하고, Rerank 개요 문서의 응답 예시에도 `search_units=1.0`이 찍혀 있습니다. 반면 Rerank 5의 가격은 토큰 단위이고 API 레퍼런스의 샘플 응답에는 `input_tokens`가 찍혀 있습니다. 또 모범 사례 문서의 "결과 해석" 절은 여전히 점수가 질의에 따라 달라지니 도메인 질의 30~50개로 기준값을 직접 구하라고 안내합니다. 이전 모델 기준의 설명이 남은 것으로 보이지만, 보정된 점수를 믿고 기준값을 정하기 전에 직접 확인해야 할 이유이기도 합니다.

## 인사이트

**왜 지금 중요한가.** 필자의 판단으로는 이번 출시의 핵심은 점수 몇 점이 아니라 리랭커의 출력이 바뀐 것입니다. 지금까지는 "순서"만 믿을 수 있었기에 파이프라인은 상위 k개를 통째로 넘겼습니다. Rerank 5는 "이 문서를 넣을지"(보정된 점수)와 "문서의 어디를 넣을지"(구간 점수)를 함께 돌려주겠다고 합니다. 블로그의 [컨텍스트 엔지니어링 글](/tech/2026/10/24/context-engineering.html)에서 공급자들의 방향이 "더 큰 창"이 아니라 "덜 넣기"로 모이고 있다고 정리했는데, 그 글에서 다룬 압축과 도구 결과 삭제가 이미 들어온 컨텍스트를 사후에 줄이는 기법이라면 Context Focus는 들어오기 전에 줄이는 쪽입니다. 요약을 새로 쓰지 않고 원문의 위치만 돌려주므로 압축 과정에서 내용이 바뀔 위험이 없다는 점도 다릅니다. 다만 빠뜨릴 위험은 그대로 남습니다.

**실무에 주는 의미.** RAG나 검색 에이전트를 운영하는 팀이라면 다음 순서로 시험해 볼 만합니다.

1. 모델만 바꾸고 순위 품질을 자체 평가 세트로 잽니다. 재색인이 필요 없으므로 비교 비용이 낮습니다. 한국어 문서라면 발표문의 91.8점은 Cohere 내부 세트의 값이므로 참고만 하고 자기 데이터로 확인합니다.
2. 고정 상위 k개를 기준값 방식으로 바꿔 봅니다. 발표문의 경계(Pro 0.50, Fast 0.45)에서 시작하되, 경계선에 있는 문서 수십 개를 직접 넣어 점수 분포를 확인합니다. Cohere 자신의 모범 사례 문서가 권하는 절차이기도 합니다.
3. Context Focus는 기본 기준값 0.1에서 시작해 답변 품질을 보면서 올립니다. Cohere의 실험에서도 제거 비율이 50%를 넘어가면 품질 하락이 빨라졌습니다(75%에서 7%p, 90%에서 14%p). 요약형 질의나 표, 코드가 많은 문서는 구간 대신 문서 전체를 넘기는 분기를 둡니다.
4. 지연 예산이 빠듯하면 Fast부터 봅니다. 자체 발표 기준으로 Fast는 이전 세대 Pro보다 순위 품질이 높고, Pro보다 처리량이 2.9배이며, 가격은 40% 수준입니다.

**블로그의 기존 글과의 연결.** [RAG 원 논문 글](/papers/2026/10/24/rag.html)에서 실무 RAG의 실패 지점으로 "정답 문서가 상위 K에 못 드는 문제"를 짚고 대응으로 재순위를 들었습니다. Rerank 5는 그 자리에 놓이는 부품입니다. 그런데 [LASAGNA 논문 글](/papers/2026/10/24/rag-compositionality-lasagna.html)이 보여 준 것은 RAG 기법을 따로 잰 이득이 전체 파이프라인에서는 그대로 더해지지 않는다는 점이었습니다. 그 논문에서 검색 기법 세 개의 예측 이득 +47%는 실제 +17%로 줄었고, 임베딩이 이미 좋은 후보를 가져오면 재순위화가 도울 여지가 줄어든다는 해석도 나왔습니다. Cohere의 에이전트 실험은 가장 약한 출발점인 BM25 위에 리랭커를 얹은 결과이므로, 이미 하이브리드 검색과 좋은 임베딩을 쓰는 팀이 같은 크기의 이득을 기대하기는 어렵다고 보는 것이 합리적입니다. 또 LASAGNA의 실험 설계에서 재순위화와 압축은 서로 다른 단계였는데, Context Focus는 이 둘을 한 호출로 합친 셈이라 단계 수와 지연을 줄이는 효과는 따로 평가할 가치가 있습니다.

**한계와 반론.** RCP-nDCG@10은 LLM 판정 모델을 쓰는 지표입니다. [LLM 평가 실무 글](/tech/2026/10/24/llm-evals.html)에서 정리했듯 모델 채점은 사람과의 일치도를 확인한 뒤에 확대해야 하고, Cohere는 46명 평가로 그 확인을 했다고 밝혔습니다. 그럼에도 "지표를 만든 회사가, 그 지표에 맞춰 모델을 최적화하고, 그 지표로 경쟁사와 비교한" 구조라는 점은 달라지지 않습니다. 정답 목록의 빈틈을 메운다는 문제의식은 타당해 보이지만, 판정 모델과 리랭커가 비슷한 종류의 관련성 판단을 공유할 때 생기는 유리함이 없는지는 외부 검증이 필요한 부분입니다. 격차의 크기도 구분해서 읽을 필요가 있습니다. BRIGHT의 5.8점이나 이전 세대 대비 12.4점은 큰 차이지만, ViDoRe V3 1.6점과 BEIR 1.8점은 그보다 훨씬 작습니다. RCP-nDCG 글에 따르면 질의 하나에서 두 시스템의 격차가 약 0.02보다 작을 때 사람 평가자와의 일치는 동전 던지기 수준이었습니다. 이 수치는 개별 질의에 대한 것이라 수백 개 질의의 평균 격차에 그대로 적용할 수는 없지만, 1~2점대 격차를 실제 서비스에서 체감할 우위로 단정하기는 어렵다는 것이 필자의 판단입니다.

**앞으로 지켜볼 점.** 첫째, 제3자 평가입니다. RCP-nDCG 글에는 MTEB(Massive Text Embedding Benchmark)의 주 관리자가 이 지표를 MTEB에 도입하게 되어 기대한다는 인용이 실려 있습니다. 실제로 반영되어 다른 회사 모델이 같은 자로 독립적으로 채점되면 이번 수치를 검증할 수 있게 됩니다. 둘째, 구간 점수의 품질을 따로 잰 평가입니다. 지금 공개된 것은 답변 품질이라는 간접 지표뿐이고, "돌려준 구간에 근거가 실제로 들어 있는가"를 직접 잰 수치는 없습니다. 셋째, 경쟁 리랭커들이 보정된 점수와 구간 반환을 따라오는지입니다. 따라온다면 리랭커 비교의 기준이 nDCG 한 줄에서 "같은 토큰 예산에서의 답변 품질"로 옮겨 갈 것으로 보입니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. 예: 실제 한국어 문서에서 Context Focus 기준값을 올렸을 때의 체감 품질, 기존 리랭커(상위 k개 고정)와의 비용 비교 경험. -->

## 참고 링크

- [Introducing Rerank 5: precise, efficient enterprise document retrieval (Cohere 공식 발표, 2026-10-21)](https://cohere.com/blog/rerank-5)
- [Cohere Rerank 모델 문서](https://docs.cohere.com/docs/rerank)
- [Rerank 개요 문서](https://docs.cohere.com/docs/rerank-overview)
- [Rerank API (v2) 레퍼런스](https://docs.cohere.com/reference/rerank)
- [Rerank 모범 사례](https://docs.cohere.com/docs/reranking-best-practices)
- [릴리스 노트: Announcing Cohere's Rerank 5 Models](https://docs.cohere.com/changelog/rerank-v5)
- [Cohere 가격 페이지](https://cohere.com/pricing) · [가격 안내 문서](https://docs.cohere.com/v2/docs/how-does-cohere-pricing-work) · [API 키와 속도 제한](https://docs.cohere.com/docs/rate-limits)
- [RCP-nDCG@10: A more complete way to measure retrieval relevance (Cohere, 2026-09-30)](https://cohere.com/blog/rcp-ndcg) · [논문 arXiv:2609.35739](https://arxiv.org/abs/2609.35739) · [코드 cohere-ai/rcp](https://github.com/cohere-ai/rcp)
- [cohere Python SDK (PyPI)](https://pypi.org/project/cohere/)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
