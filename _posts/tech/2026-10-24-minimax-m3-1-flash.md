---
layout: default
title: "[기술 소개] MiniMax-M3.1-Flash: 희소 어텐션, QAT, 드래프트 헤드를 체크포인트에 기본 탑재한 MoE"
description: "MiniMax-M3.1-Flash의 공식 발표와 모델 카드, config 파일을 근거로 MSA 희소 어텐션, 양자화 인지 학습, 내장 DSpark 드래프트 헤드 설계와 하드웨어별 서빙 조건, 벤치마크 하네스 차이, 커뮤니티 라이선스 조건을 정리했습니다."
date: 2026-10-24 00:52:00 +0900
categories: [tech]
---

# [기술 소개] MiniMax-M3.1-Flash: 희소 어텐션, QAT, 드래프트 헤드를 체크포인트에 기본 탑재한 MoE

- **발표:** MiniMax, 2026년 10월 19일 (공식 블로그). Hugging Face 저장소는 2026-10-17 생성, 2026-10-23 마지막 수정
- **원문:** [공식 발표 블로그](https://www.minimax.io/blog/minimax-m31f) · [모델 카드(Hugging Face)](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash) · [MiniMax Sparse Attention 논문(arXiv:2606.13392)](https://arxiv.org/abs/2606.13392) · [가격 문서](https://platform.minimax.io/docs/pricing/overview) · [vLLM 레시피](https://recipes.vllm.ai/MiniMaxAI/MiniMax-M3.1-Flash)
- **한눈에 (2026-10-24 기준):** 총 약 428B, 토큰당 활성 23B의 멀티모달 MoE. 컨텍스트 최대 100만 토큰. API 가격은 100만 토큰당 입력 $0.15, 출력 $0.60, 캐시 입력 $0.015.
- **라이선스 주의:** 가중치는 MIT나 Apache 같은 표준 오픈소스 라이선스가 아니라 **MiniMax Community License**입니다. 무료 허용 범위는 비상업 목적이고, 상업적 사용 시 "Built with MiniMax M3.1-Flash" 표시와 MiniMax에 대한 통지가 필요하며, 연매출 2,000만 달러 초과 시 사전 서면 승인을 받아야 합니다. 군사 목적 사용도 금지됩니다(아래 "써 볼 수 있나" 참고).
- **공개 상태 메모:** 10월 19일 블로그는 "모델 가중치는 나중에 공개된다"고 적었지만, 2026-10-24 현재 Hugging Face 저장소에서 접근 승인 절차 없이 가중치(약 252GB)를 내려받을 수 있습니다.

## 한 줄 요약

**MiniMax-M3.1-Flash는 M3의 MoE 구조를 유지하면서 희소 어텐션을 모든 층으로 넓히고, 양자화를 학습 단계에 넣고, 추측 디코딩용 드래프트 헤드를 체크포인트에 함께 넣었습니다.** 추론 효율을 "서빙하는 쪽이 알아서 붙이는 최적화"가 아니라 "모델이 기본으로 갖고 나오는 속성"으로 만든 설계입니다.

## 배경

MiniMax는 M3를 플래그십으로 두고, 이번 M3.1-Flash를 "차세대 Flash 모델"로 소개했습니다. 공식 블로그에 따르면 익명으로 운영되며 200조 토큰 이상을 처리한 "Space Bunny"가 이 모델의 초기 버전이었고, 지능의 한계를 미는 Pro 모델은 나중에 나온다고 합니다.

블로그가 내세운 수치는 두 가지입니다. 이전 세대 대비 **온라인 추론이 약 3배 빨라지고, 에이전트 작업의 전체 사용 비용이 70% 낮아졌다**는 것입니다. 일상 사용에서 출력 속도가 초당 200토큰 이상, 중앙값(P50) 170토큰 이상이라고도 밝혔습니다. 측정 조건(하드웨어, 동시성, 입력 길이)은 공개되지 않았습니다.

가격 문서 기준(2026-10-24)으로 보면 비용 절감의 일부는 단가에서 옵니다.

| 모델 | 입력 | 출력 | 캐시 입력(읽기) |
|---|---|---|---|
| MiniMax-M3.1-Flash | $0.15 | $0.60 | $0.015 |
| MiniMax-M3 (입력 512K 이하, 50% 할인가) | $0.30 | $1.20 | $0.06 |

(100만 토큰당 USD, 표준 등급. M3는 512K 초과 입력이면 두 배)

입력과 출력은 M3의 절반, 캐시 읽기는 4분의 1입니다. 나머지는 아래에서 볼 모델 구조의 효율 개선에서 나온다는 것이 MiniMax의 설명입니다.

## 핵심 내용

모델 카드는 M3 대비 바뀐 점을 세 줄로 요약합니다. 희소 어텐션 전면 적용, 양자화 인지 학습, DSpark 추측 디코딩입니다. 세 가지 모두 **추론 비용을 줄이는 장치를 모델과 체크포인트 차원에서 미리 갖춰 둔다**는 공통점이 있습니다. 아래에서 공식 자료와 공개된 config 파일을 함께 봅니다. config 해석은 필자가 파일을 읽고 정리한 것이며, MiniMax가 각 값의 의미를 문서로 설명한 것은 아닙니다.

### 1. 모델 개요: 60층, 전문가 128개 중 4개

| 항목 | 값 | 출처 |
|---|---|---|
| 파라미터 | 총 약 428B, 토큰당 활성 23B | 모델 카드 |
| 입출력 | 텍스트·이미지·영상 입력, 텍스트 출력 | 모델 카드 |
| 컨텍스트 | 최대 1,000,000 토큰 | 모델 카드 |
| 층 수 | 60층, 앞 3개 층은 dense FFN, 나머지 57개 층이 MoE | config.json |
| 전문가 | 라우팅 전문가 128개 중 토큰당 4개 + 공유 전문가 1개 | config.json |
| 어텐션 헤드 | 쿼리 64개, KV 4개(GQA), 헤드 차원 128 | config.json |

[MoE(전문가 혼합)](/tech/2026/10/24/mixture-of-experts.html) 글에서 다룬 것처럼, 전체 파라미터는 크게 두고 토큰마다 일부 전문가만 계산하는 구조입니다. 428B 중 23B만 활성이므로 계산량은 20B대 모델 수준이지만, 가중치 전체는 메모리에 올려야 합니다.

### 2. 희소 어텐션: MSA를 모든 층에

M3.1-Flash는 MiniMax Sparse Attention(MSA)을 씁니다. 2026년 6월 공개된 MSA 논문의 설명은 이렇습니다. GQA(그룹 쿼리 어텐션) 위에 가벼운 **인덱스 분기**(Index Branch)를 두어 KV 블록마다 점수를 매기고, GQA 그룹별로 상위 k개 블록을 고릅니다. 그다음 **주 분기**(Main Branch)가 선택된 블록에 대해서만 정확한 블록 희소 어텐션을 계산합니다. 논문은 109B 규모 멀티모달 모델에서 MSA가 일반 GQA와 비슷한 성능을 내면서 100만 토큰 컨텍스트에서 토큰당 어텐션 계산량을 28.4배 줄였고, 전용 커널과 함께 H800에서 프리필 14.2배, 디코딩 7.6배의 실제 속도 향상을 냈다고 보고합니다.

M3.1-Flash에서 달라진 점은 적용 범위입니다. 모델 카드는 "처음 세 개의 전체 어텐션(full attention) 층을 희소 어텐션으로 바꿨다"고 적었고, config의 `sparse_attention_freq`도 60개 층 모두 1입니다. config에 적힌 블록 크기는 128토큰, 선택 블록 수(`sparse_topk_blocks`)는 16이며, 인덱스 헤드 4개와 로컬 블록 1개 설정이 있습니다. 필자의 해석으로는 쿼리 하나가 컨텍스트 길이와 상관없이 정해진 수의 블록만 보게 되므로, 100만 토큰에서 어텐션 비용이 길이에 비례해 늘지 않는 구조입니다. 대신 **모든 층이 근사(선택된 블록만 봄)이므로, 전체 어텐션 층이 하나도 남지 않은 상태에서 긴 문맥 품질이 유지되는지**는 사용자 작업으로 확인해야 할 부분입니다.

### 3. 양자화 인지 학습(QAT): FP4 전문가를 "학습된 그대로" 배포

[LLM 양자화](/tech/2026/10/24/llm-quantization.html) 글에서 다룬 일반적인 방식은 BF16으로 학습한 모델을 나중에 FP8이나 4비트로 줄이는 학습 후 양자화(PTQ)입니다. 이 경우 정밀도 손실은 배포하는 쪽이 감수합니다. M3.1-Flash는 **라우팅 전문가와 어텐션 경로를 학습 중에 양자화**했다고 밝힙니다. 모델이 낮은 정밀도에서의 오차를 학습 과정에서 보고 적응했다는 뜻입니다.

배포된 체크포인트의 `quantization_config`도 이 설계를 그대로 보여 줍니다.

| 부분 | 형식 (config 기준) |
|---|---|
| 라우팅 전문가(MoE) | NVFP4, 그룹 크기 16 |
| 그 밖의 선형 층 | MXFP8, 블록 크기 32 |
| 양자화 제외 | 전문가 라우터(gate), 임베딩, `lm_head`, 비전 타워, 멀티모달 프로젝터, DSpark 일부 |

그래서 저장소 전체가 약 252GB에 그칩니다. 428B를 BF16으로 저장했다면 850GB 이상이 필요했을 것입니다. 모델 카드는 "결과는 공식 가중치 기준이며, 제3자 양자화본은 다를 수 있다"고 따로 적어 두었습니다. 이미 4비트로 학습된 모델을 다른 방식으로 다시 양자화하면 QAT의 이점이 사라질 수 있다는 경고로 읽힙니다.

### 4. 내장 드래프트 헤드: DSpark 추측 디코딩

[KV 캐시와 추측 디코딩](/tech/2026/10/24/kv-cache-speculative-decoding.html) 글에서 설명했듯, 추측 디코딩은 가벼운 드래프트가 토큰 몇 개를 먼저 제안하고 본 모델이 한 번에 검증해 디코딩 속도를 올리는 기법입니다. 보통은 서빙하는 쪽이 별도 드래프트 모델을 고르거나 EAGLE 같은 헤드를 따로 학습해야 합니다.

M3.1-Flash는 **DSpark 드래프트 헤드를 체크포인트의 `dspark/` 폴더에 함께 넣었습니다**(약 2.3GB). 모델 카드에 따르면 DSpark는 이전 세대의 EAGLE 유사 MTP(다중 토큰 예측) 방식을 대체합니다. 공개된 `dspark/config.json`을 보면 구조를 어느 정도 짐작할 수 있습니다.

- 드래프트는 5개 층의 작은 트랜스포머이고, 어텐션은 4,096토큰 슬라이딩 윈도입니다.
- 본 모델의 3, 17, 31, 45, 59번째 층 은닉 상태를 입력 맥락으로 씁니다(`target_layer_ids`).
- 블록 크기 7(`dspark_block_size`), 마스크 토큰, 신뢰도 헤드(`enable_confidence_head`) 설정이 있습니다.

DSpark 알고리즘 자체를 설명한 공식 문서는 찾지 못했습니다. 참고로 같은 이름이 [DeepSeek-V4.1-Flash](/tech/2026/10/24/deepseek-v4-1-flash-1017.html) 기반 모델 카드에도 "반자기회귀(semi-autoregressive) 드래프트 생성과 신뢰도 기반 검증 일정"으로 등장합니다. 두 회사 구현의 관계는 어느 쪽 자료에도 설명이 없습니다.

서빙 쪽에서는 별도 드래프트 모델 경로가 필요 없습니다. vLLM 레시피는 `--speculative-config`에 `"method":"dspark"`만 지정하면 되고 드래프트 경로를 줄 필요가 없다고 설명합니다. 레시피 예시는 한 번에 3개 토큰을 추측하도록(`num_speculative_tokens: 3`) 설정합니다.

### 5. 하드웨어에 따라 "기본 탑재"가 달라진다

설계는 모델에 들어 있지만, 실제로 켜지는지는 하드웨어에 달려 있습니다. vLLM 레시피(vLLM 0.33.0 이상) 기준으로 정리하면 다음과 같습니다.

| 하드웨어 | 구성 | NVFP4 전문가 | DSpark | 비고 |
|---|---|---|---|---|
| NVIDIA Blackwell (GB200, GB300, B200, B300) | TP4 | FP4 텐서 코어에서 그대로 실행 | 사용 | KV 캐시도 NVFP4 |
| AMD MI355X | TP4 | 로드 시 MXFP8로 재양자화 | 사용 | ROCm 7.2 이상 |
| NVIDIA Hopper (H100, H200) | TP8, 노드 하나 전체 | Marlin 커널로 실행 | **사용 안 함** | 예시 설정은 최대 길이 262,144, 영상 입력 끔 |

FP4 텐서 코어가 없는 Hopper에서는 KV 캐시를 FP8로 두고, **DSpark 추측 디코딩이 켜지지 않으며**, 레시피 예시는 컨텍스트를 26만 토큰으로 제한하고 영상 입력을 끕니다. 아래는 레시피의 Hopper 예시 일부입니다(레시피 원문 발췌, 필자는 실행해 보지 않았습니다).

```bash
vllm serve MiniMaxAI/MiniMax-M3.1-Flash \
  --tensor-parallel-size 8 \
  --reasoning-parser minimax_m3 \
  --block-size 128 \
  --kv-cache-dtype fp8 \
  --attention-config '{"indexer_kv_dtype": "fp8"}' \
  --max-model-len 262144 \
  --limit-mm-per-prompt '{"video": 0}' \
  --moe-backend marlin
```

`--block-size 128`은 MSA의 희소·인덱스 캐시 때문에 필수라고 레시피는 밝힙니다. 즉 MiniMax가 말하는 "3배 빠른 추론"은 Blackwell급 하드웨어와 이 세 장치가 모두 켜진 조건을 전제로 할 가능성이 크고, H100·H200 같은 Hopper 서버에서는 같은 이득을 기대하기 어렵다고 보는 것이 안전합니다.

## 성능과 비교

### 모델 카드의 벤치마크 (MiniMax 자체 측정 위주)

| 벤치마크 | M3.1-Flash | 측정 조건 (모델 카드 평가 노트) |
|---|---|---|
| Automation-Bench v1.0.6 | 62.8 | 공개 600개 과제 |
| BankerToolBench | 76.2 | OpenCode 1.17.18, MiniMax-M2.7 판정 |
| Terminal Bench 4.0 | 38.1 | Codex 0.149.1 |
| DeepSWE v1.1 | 73.7 | mini-SWE-agent 2.4.5, 512K 컨텍스트 |
| NL2Repo-Bench | 61.2 | Claude Code 2.1.233, 512K 컨텍스트 |
| OSWorld 2.0 | 61.7 | 0808 Full 릴리스 |
| Agents' Last Exam | 29.6 | 공식 Overall 설정, 공식 리더보드 값 |
| CyberGym | 82.2 | Claude Code 2.1.263, 1M 컨텍스트 |
| HLE (도구 없음) | 43.4 | 텍스트 전용 2,158문항 |
| GDP.pdf AA | 20.8 | Artificial Analysis 값 그대로 |

같은 표에서 M3.1-Flash가 최고점인 항목은 Automation-Bench, BankerToolBench(Opus 5와 동률), LOCA-Bench 256K 정도이고, 대부분 항목에서는 Opus 5나 GPT-5.6 Sol이 앞섭니다. 예를 들어 Terminal Bench 4.0은 Opus 5가 51.8, DeepSWE v1.1은 DeepSeek V4.1 Flash-1017이 77.0입니다. 발표문의 표현대로 "최상위 모델 수준의 성능을 매우 낮은 과제 비용으로"가 정확한 요약으로 보입니다.

### 같은 모델, 다른 숫자: 두 회사 표 맞대 보기

MiniMax와 DeepSeek은 같은 주에 비슷한 경쟁 모델과 벤치마크로 표를 냈습니다. 같은 모델의 같은 벤치마크 점수를 두 표에서 나란히 놓으면 다음과 같습니다.

| 벤치마크 · 모델 | DeepSeek 1017 모델 카드 | MiniMax 모델 카드 |
|---|---|---|
| Agents' Last Exam · Opus 5 | 28.6 | 32.2 |
| Agents' Last Exam · GPT-5.6 Sol | 26.7 | 30.6 |
| HLE(도구 없음) · GPT-5.6 Sol | 44.5 | 49.5 |
| HLE(도구 없음) · DeepSeek V4.1 Flash | 36.8 (텍스트 전용 39.1) | 39.2 |
| Terminal Bench 4.0 · DeepSeek V4.1 Flash-1017 | 42.3 (Claude Code 하네스) | 42.3 (MiniMax 노트는 Codex 0.149.1) |

Agents' Last Exam은 MiniMax가 "공식 리더보드 값만" 썼다고 밝혔고, DeepSeek은 출처를 따로 적지 않았습니다. GPT-5.6 Sol의 HLE는 5점 차이가 납니다. Terminal Bench 4.0은 반대로, MiniMax 표가 자기 모델은 Codex로 재면서 DeepSeek 열에는 DeepSeek이 Claude Code로 잰 숫자와 같은 값을 둔 것으로 보입니다. MiniMax 노트가 DeepSeek 수치를 직접 재현했다고 밝힌 것은 OSWorld 2.0뿐입니다. **한 표 안의 열들이 같은 하네스와 같은 설정으로 측정됐다고 가정하면 안 된다**는 것이 이 비교의 결론입니다.

## 써 볼 수 있나

- **API:** MiniMax API, M Plan 구독, MiniMax Code(데스크톱 에이전트)에서 바로 쓸 수 있습니다. 가격은 위 표 참고(2026-10-24 기준).
- **가중치:** `hf download MiniMaxAI/MiniMax-M3.1-Flash`로 받을 수 있습니다(모델 카드). 권장 엔진은 SGLang, vLLM, TokenSpeed이고, Transformers, KTransformers, unsloth 지원은 "진행 중"입니다. 권장 샘플링은 `temperature=1.0`, `top_p=0.95`이며, 추론 강도는 채팅 템플릿의 `reasoning_effort`로 low, medium, high, xhigh, max 중에서 고릅니다.
- **하드웨어:** 위 표처럼 Blackwell 4장 또는 MI355X 4장, Hopper라면 8장이 기준입니다(vLLM 레시피 기준).
- **라이선스 (MiniMax Community License 원문 요약):**
  - 비상업적 목적의 사용, 복제, 수정, 배포는 무료로 허용됩니다.
  - 상업적 사용 시 관련 웹사이트, UI, 블로그, 소개 페이지, 제품 문서 중 하나에 "Built with MiniMax M3.1-Flash"를 눈에 띄게 표시해야 합니다.
  - 연매출 2,000만 달러(또는 상응 금액) 초과 제품·서비스는 api@minimax.io로 사전 서면 승인을 받아야 하고, 그 이하는 1회 통지 메일을 보내면 됩니다.
  - "상업적 사용"에는 유료 제품·서비스 제공, 이 모델 API를 상업적으로 사용하는 것, **파인튜닝 등으로 수정한 파생 모델을 상업 목적으로 배포하는 것**이 포함됩니다.
  - 부속서의 금지 용도에 군사 목적 지원, 미성년자 착취, 위해 의도의 허위 정보 생성 등이 있습니다.

필자의 판단으로는 사내 도구처럼 매출과 직접 연결되지 않는 용도도 "상업적 이익을 주된 목적으로 하는 사용"에 해당하는지 해석의 여지가 있으므로, 회사에서 도입한다면 법무 검토와 통지 절차를 먼저 거치는 편이 안전합니다.

## 한계와 논란

- **성능과 속도 수치가 대부분 자체 측정입니다.** "3배 빠른 추론", "비용 70% 절감", "200+ TPS"는 측정 조건이 공개되지 않았습니다.
- **비교표의 측정 조건이 열마다 다릅니다.** 위에서 본 것처럼 경쟁 모델 수치의 출처(자체 측정, 공식 리더보드, 상대 회사 발표값)가 섞여 있습니다.
- **DSpark의 알고리즘 문서가 없습니다.** 드래프트 헤드는 공개됐지만 수락률(acceptance rate)이나 속도 향상 수치, 학습 방법은 공식 자료에서 찾을 수 없었습니다.
- **하드웨어 종속성.** 설계의 이점(FP4 전문가, DSpark)이 Blackwell급에서만 온전히 나옵니다. Hopper에서는 추측 디코딩이 꺼지고 컨텍스트와 입력 종류도 줄어듭니다.
- **비표준 라이선스.** 이름은 "커뮤니티 라이선스"이지만 OSI 기준 오픈소스가 아니며, 상업 사용 시 표시와 통지 의무가 있습니다.
- **공개 시점 표기 불일치.** 공식 블로그(10-19)는 가중치를 "나중에" 공개한다고 했으나 Hugging Face 저장소는 그보다 앞선 10-17에 만들어졌고, 10-24 현재 가중치가 올라와 있습니다. 블로그가 갱신되지 않은 것으로 보입니다.

## 인사이트

**왜 지금 중요한가: 추론 최적화가 "서빙 엔진의 일"에서 "모델 출시물의 일부"로 이동하고 있다.** 지금까지 오픈 웨이트 모델은 BF16 가중치로 나오고, 양자화본은 커뮤니티가 만들고, 추측 디코딩용 드래프트는 서빙 엔진 쪽이 따로 준비하는 분업 구조였습니다. M3.1-Flash는 이 세 단계를 출시물 하나에 묶었습니다. 희소 어텐션은 학습 때부터 모든 층에 있고, 4비트 전문가는 학습된 그대로이며, 드래프트 헤드는 같은 폴더에 들어 있습니다. 같은 주에 나온 DeepSeek-V4.1-Flash도 FP4 KV 캐시와 DSpark를 모델 카드의 구조 설명에 포함했습니다. 필자의 판단으로는 "모델 공개"의 의미가 가중치 파일에서 "서빙 레시피까지 포함한 실행 단위"로 바뀌고 있습니다.

**실무에 주는 의미.** 이런 모델을 자체 호스팅할 때는 세 가지를 확인해야 합니다. 첫째, 자기 하드웨어에서 설계상의 이점이 실제로 켜지는지입니다. H100 서버라면 DSpark가 꺼지고 컨텍스트도 줄어드므로, 발표된 속도와 비용을 그대로 기대하면 안 됩니다. 둘째, 커뮤니티 양자화본을 쓰지 말고 공식 체크포인트를 쓰는 것입니다. QAT 모델을 다시 양자화하면 학습으로 얻은 정밀도 적응이 무의미해질 수 있습니다. 셋째, 1M 컨텍스트를 실제 작업 길이에서 시험하는 것입니다. 모든 층이 희소 어텐션이므로, "필요한 블록을 놓쳤을 때"의 실패가 긴 문서 작업에서 어떻게 나타나는지는 벤치마크 표로는 알 수 없습니다. API로만 쓴다면 이런 고민 없이 낮은 단가(캐시 입력 $0.015)의 이득을 그대로 얻을 수 있다는 점에서, 이 모델은 자체 호스팅보다 API 쪽이 먼저 매력적인 선택으로 보입니다.

**블로그의 기존 글과의 연결.** [LLM 양자화](/tech/2026/10/24/llm-quantization.html) 글이 PTQ와 QAT의 차이를 이론으로 설명했다면, 이 모델은 "QAT로 학습한 NVFP4 전문가 + MXFP8 나머지"라는 구체적인 배포 형태를 보여 주는 사례입니다. [KV 캐시와 추측 디코딩](/tech/2026/10/24/kv-cache-speculative-decoding.html) 글에서 추측 디코딩의 실무 난점으로 꼽히는 "어떤 드래프트를 쓸 것인가"는, 드래프트가 모델과 함께 배포되면 사라집니다. 다만 그만큼 드래프트의 품질을 사용자가 고를 수 없게 됩니다.

**앞으로 지켜볼 점.** (1) DSpark의 수락률과 실제 속도 향상을 다룬 기술 보고서나 제3자 측정. (2) Hopper에서 DSpark 지원이 추가되는지. 필자의 판단으로는 Hopper 서버를 가진 팀에게 이것이 자체 호스팅 판단을 가장 크게 바꿀 변수입니다. (3) 같은 하네스로 M3.1-Flash와 DeepSeek-V4.1-Flash-1017을 나란히 잰 독립 평가. 두 회사의 표가 서로 다른 조건의 숫자를 섞고 있어, 지금으로서는 두 모델의 우열을 공식 자료만으로 판단하기 어렵습니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [MiniMax M3.1 Flash: Redefining Agent Performance and Cost (MiniMax 블로그, 2026-10-19)](https://www.minimax.io/blog/minimax-m31f)
- [MiniMax-M3.1-Flash 모델 카드](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash)
- [MiniMax Community License 원문](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash/blob/main/LICENSE)
- [config.json](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash/blob/main/config.json) · [dspark/config.json](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash/blob/main/dspark/config.json)
- [MiniMax Sparse Attention (arXiv:2606.13392)](https://arxiv.org/abs/2606.13392)
- [MiniMax 가격 문서](https://platform.minimax.io/docs/pricing/overview)
- [vLLM 레시피: MiniMaxAI/MiniMax-M3.1-Flash](https://recipes.vllm.ai/MiniMaxAI/MiniMax-M3.1-Flash)
- [SGLang 쿡북: MiniMax-M3.1](https://docs.sglang.io/cookbook/autoregressive/MiniMax/MiniMax-M3.1)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
