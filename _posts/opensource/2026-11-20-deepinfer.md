---
layout: default
title: "[오픈소스 소개] DeepInfer: DeepSeek가 공개한 V4.1-Flash 전용 대규모 추론 프레임워크"
description: "DeepInfer의 어텐션 DP·MoE EP 병렬 구조, DSpark 가변 길이 검증, SWA bounded replay, 배치 불변 추론을 README와 배포 Q&A로 정리하고, 오프라인 추론만 담긴 공개 범위와 vLLM·SGLang과의 관계를 짚었습니다."
date: 2026-11-20 14:00:00 +0900
categories: [opensource]
---

# [오픈소스 소개] DeepInfer: DeepSeek가 공개한 V4.1-Flash 전용 대규모 추론 프레임워크

- **저장소:** [deepseek-ai/DeepInfer](https://github.com/deepseek-ai/DeepInfer) · [배포 Q&A 문서](https://github.com/deepseek-ai/DeepInfer/blob/main/doc/inference_deployment_qa.md) · [예제 문서](https://github.com/deepseek-ai/DeepInfer/blob/main/examples/README.md)
- **라이선스:** Apache-2.0 (LICENSE 원문 확인). 서브모듈로 들어오는 커널 라이브러리(FlashMLA, DeepGEMM, DeepEP, DeepSelect)와 TileKernels, deepseek-recipe는 각 저장소 기준 MIT입니다.
- **언어:** Python, C++ (엔진 스케줄러). Linux, GCC 13 이상, Python 3.12, CUDA 13(NVIDIA) 또는 CANN 9.2(Ascend) 필요
- **현황 (2026-11-20 기준):** GitHub 스타 약 2.6만 개, 포크 약 3,200개. 저장소 생성 2026-10-16, 첫 커밋 2026-10-20. 릴리스와 태그는 아직 없고 `pyproject.toml`의 버전은 0.1.0(Beta 분류)입니다. `main` 브랜치 커밋은 6개로 마지막이 2026-11-03이며, 가장 최근 push(2026-11-19)는 `nv-dev` 브랜치에 있습니다.
- **도입 전 확인할 점:**
  - **이번 공개판은 오프라인(배치) 추론만 담고 있습니다.** README는 완전한 추론 서비스에 필요하지만 포함되지 않은 것으로 KV 캐시 시스템, VE/프리필/디코드 분리 배포, 데이터 병렬 복제본 사이의 로드 밸런싱을 명시합니다. API 서버도 없습니다.
  - 지원 모델은 DeepSeek-V4.1-Flash 하나, 지원 하드웨어는 NVIDIA SM100 GPU와 Huawei Ascend 950 NPU 두 가지입니다(`main` README 기준).
  - 설치는 소스 빌드뿐이고, 사전 빌드 패키지나 공식 Docker 이미지는 없습니다.
  - GitHub Issues가 꺼져 있고 Discussions만 열려 있습니다. 열린 PR이 228개이고, 지금까지 병합된 PR은 7개(`main` 2개, `nv-dev` 5개)입니다.
  - 이 글의 처리량·매출 수치는 모두 DeepSeek 자체 발표이며 제3자 검증은 확인하지 못했습니다.

## 한 줄 요약

**DeepInfer는 DeepSeek가 자사 대규모 서비스를 구동한다고 밝힌 추론 프레임워크로, 이번에 공개된 것은 DeepSeek-V4.1-Flash 한 모델을 NVIDIA SM100 GPU와 Huawei Ascend 950 NPU에서 오프라인으로 추론하는 엔진 부분입니다.** GPU 수십 장 이상의 클러스터에서 이 모델을 직접 서빙하려는 팀, 그리고 대형 MoE(전문가 혼합, Mixture of Experts) 모델의 서빙 설계를 코드와 운영 문서로 공부하려는 엔지니어에게 의미가 있습니다. 노트북이나 GPU 한두 장으로 써 볼 수 있는 도구는 아닙니다.

## 어떤 문제를 푸나

DeepSeek-V4.1-Flash는 모델 카드 기준 백본 파라미터 552B, 컨텍스트 최대 100만 토큰의 멀티모달 MoE 모델입니다. 가중치는 공개되어 있지만, 모델 저장소에 든 추론 코드는 스스로 "운영용이 아닌 참조 구현"이라고 밝힙니다(블로그의 [DeepSeek-V4.1-Flash-1017 글](/tech/2026/10/24/deepseek-v4-1-flash-1017.html) 참고). 이 크기의 모델을 많은 사용자에게 낮은 지연으로 서빙하려면 모델 코드만으로는 부족하고, 다음 문제를 풀어야 합니다.

- **전문가가 여러 GPU에 흩어져 있습니다.** MoE 층마다 라우팅 전문가 384개와 공유 전문가 1개가 있어(모델 카드) 한 GPU에 다 올릴 수 없고, 토큰을 전문가가 있는 GPU로 보내고 받는 통신과 부하 쏠림을 관리해야 합니다.
- **프리필과 디코드의 성격이 다릅니다.** 프리필(prefill, 입력 프롬프트를 처리해 KV 캐시를 만드는 단계)은 긴 입력을 한꺼번에 계산하고, 디코드(decode, 토큰을 하나씩 생성하는 단계)는 작은 계산을 아주 많이 반복합니다. 같은 구성으로 둘 다 잘하기 어렵습니다.
- **CPU가 일하는 동안 GPU가 놉니다.** 디코드 한 스텝마다 스케줄링과 후처리가 CPU에서 돌고, 그동안 GPU는 대기합니다.
- **같은 요청이 배치 구성에 따라 다른 결과를 냅니다.** 평가와 회귀 테스트에서 재현이 어렵습니다.

배포 Q&A 문서는 DeepSeek V4.1 Flash 추론 시스템의 설계 목표를 세 가지로 적습니다. 여러 제조사의 가속기 지원, 범용 하드웨어를 기준으로 한 프리필·디코드 구성(프리필은 GPU 8장짜리 일반 서버, 디코드는 GPU 64~128장짜리 슈퍼노드), 그리고 **KV 캐시를 72시간 넘게 보관해 캐시 적중 시 프리필 재계산을 줄이는 것**입니다. DeepInfer는 이 시스템의 엔진에 해당하고, 세 번째 목표를 맡는 KV 캐시 저장소와 로드 밸런서는 "내부 인프라와 강하게 결합되어 있어 아직 완전히 공개하지 않았다"고 같은 문서가 밝힙니다.

Q&A 문서는 규모도 언급합니다. 단일 클러스터가 하루 155조 토큰을 처리하고, GPU 시간당 매출이 38달러(비피크 가격 기준)라는 것입니다. 둘 다 DeepSeek 자체 발표이고 산출 근거는 공개되지 않았습니다.

## 핵심 개념

| 용어 | 설명 |
|---|---|
| DP | 데이터 병렬(Data Parallelism). 어텐션 부분을 GPU마다 복제하고 요청을 나눠 맡깁니다. Q&A 기준 DP 수와 EP 수를 같게 둡니다 |
| EP | 전문가 병렬(Expert Parallelism). MoE 전문가를 여러 GPU에 나눠 두고 토큰을 보내고 받습니다. 디코드에서 EP를 64~128로 크게 잡는 구성을 Q&A는 Wide-EP라고 부릅니다 |
| EPLB | 전문가 병렬 로드 밸런서(Expert-Parallel Load Balancer). 부하가 높은 전문가의 복제본(중복 전문가)을 두고 주기적으로 GPU 배치를 다시 정합니다 |
| CP | 컨텍스트 병렬(Context Parallelism). 긴 시퀀스 하나를 여러 GPU로 쪼갭니다. 엔진은 지원하지만 DeepSeek 운영에서는 쓰지 않는다고 합니다 |
| DSpark | 모델에 내장된 추측 디코딩(speculative decoding). 초안 토큰을 여러 개 만들고 신뢰도에 따라 검증할 토큰을 고릅니다 |
| SWA | 슬라이딩 윈도 어텐션(Sliding Window Attention). 최근 토큰 창만 보는 어텐션으로, 이 창의 KV 상태를 SWA KV 캐시라고 부릅니다 |
| CED | 인과 인코더-디코더(Causal Encoder-Decoder). 20층 인코더와 20층 디코더로 나눈 V4.1 구조로(모델 카드), 프리필 계산은 인코더 층에서만 일어납니다(Q&A) |
| VE | 비전 인코더(Vision Encoder). 이미지 입력을 임베딩으로 바꾸는 부분으로, 프리필·디코드와 따로 배포합니다 |

프리필과 디코드를 나눠 배포하는 이유를 Q&A는 TTFT(첫 토큰까지 시간)와 TBT(토큰 간 시간)를 단계별로 따로 조절하기 위해서라고 설명합니다.

## 동작 원리

### 전체 시스템과 공개 범위

Q&A 문서의 참조 아키텍처 그림을 텍스트로 옮기고, 각 구성 요소가 이번 공개에 들어 있는지 표시했습니다.

```
 [O] in this repo (engine)   [R] separate repo (deepseek-recipe)   [X] not in this release
 KV cache path: storage -> prefill engines -> decode engines -> storage

  User JSON <--> [R] DeepSeek Recipe <--> [X] Entrypoint <-------------------+
                                               |                             |
                                               v                             |
                                     [X] Prefill Load Balancer               |
                                               |                             |
                                               v                             |
  [X] VE Load Balancer <-- images --- [O] Prefill engines                    | output
           |                          EP2-8 / DP2-8, EPLB                    | tokens
           v                               ^    |                            |
  [O] Vision Encoder --- embeddings -------+    | request                    |
      (one GPU each)                            v                            |
                                     [X] Decode Load Balancer                |
                                               |                             |
                                               v                             |
                                      [O] Decode engines --------------------+
                                      EP64-128 / DP64-128, EPLB
                                               |
                                               | KV cache write-back
                                               v
               [X] External KVCache Storage (3FS) --- KV cache on hit ---> Prefill engines
```

즉 저장소에 든 것은 그림의 엔진 상자 안쪽(커널, 모델 실행, 샘플러, 배치 스케줄러, EPLB)입니다. 엔진 코드에는 일반(`NORMAL`), 프리필 전용(`PROMPT`), 디코드 전용(`COMPLETION`) 엔진 타입이 정의되어 있어, README가 P/D 분리에 대해 "필요한 엔진 기능은 대부분 이미 구현되어 있다"고 한 근거로 보입니다. 다만 그 사이를 잇는 진입점, 로드 밸런서, KV 캐시 전송·저장은 사용자가 만들어야 합니다.

요청과 응답을 API 형식과 토큰 열 사이에서 바꾸는 부분은 별도 저장소 [deepseek-recipe](https://github.com/deepseek-ai/deepseek-recipe)(MIT, Rust 구현과 Python 바인딩)로 공개되어 있습니다. Chat Completions, Responses, Messages API 요청을 하나의 대화 형식으로 바꾸고 모델 출력을 다시 각 형식으로 변환합니다.

### 엔진 내부

- **Python 계층:** `deepinfer.entrypoints.llm.LLM` 클래스가 오프라인 진입점입니다. `generate()`에 프롬프트와 `SamplingParams` 목록을 넘기면 내부에서 엔진의 `step()`을 반복 호출합니다. 이 파일을 포함해 `vendor/`를 뺀 23개 파일 머리말에 "Derived from vLLM; modified by DeepSeek"가 적혀 있습니다(필자가 clone해서 센 값).
- **C++ 계층:** 시퀀스 관리, 블록 관리, 스케줄러, 가변 길이 검증 로직이 `csrc/engine`에 있고 pybind로 Python에 연결됩니다.
- **커널:** FlashMLA(어텐션), DeepGEMM(행렬 곱), DeepEP(전문가 병렬 통신), DeepSelect(top-k), TileKernels와 저장소 안의 TileLang 커널을 씁니다. NVIDIA와 Ascend는 서브모듈이 일부 다릅니다(DeepEP-Ascend, DeepGEMM-Ascend).
- **구조화 출력:** 요구 사항 파일에 xgrammar가 고정되어 있고, 정규식·JSON 스키마·EBNF 문법을 받아 매 디코드 스텝에 허용 토큰 마스크를 적용합니다.

### 병렬 구성: 프리필은 좁게, 디코드는 넓게

Q&A가 밝힌 DeepSeek의 운영 구성은 다음과 같습니다(자체 발표).

| 단계 | 병렬 구성 | 이유 |
|---|---|---|
| 프리필 | EP2~8 / DP2~8, 메모리가 허락하는 가장 작은 값 | 프리필은 전문가당 배치가 이미 충분히 커서, 그룹이 작을수록 부하 균형이 좋고 NVLink 통신이 줄어듭니다 |
| 디코드 | EP64~128 / DP64~128, GPU가 허락하는 가장 큰 값 | Wide-EP가 MoE 부분의 스텝당 메모리 통신량을 줄이고 초당 토큰 수를 올립니다 |
| VE | 인스턴스당 GPU 1장 | 더 싼 GPU 권장 |

TP(텐서 병렬)는 통신 비용이 커서, CP는 DP보다 종단 간 최대 5% 느리고 전문가 부하 균형을 나쁘게 하는 경향이 있어 쓰지 않는다고 합니다. 배포 최소 단위는 프리필 1개와 디코드 1개이며, 프리필과 디코드의 GPU 비율이 실제로 약 1:1이어서 **효율적인 최소 단위는 프리필 GPU 64장과 디코드 GPU 64장**이라고 Q&A는 적습니다.

EPLB 설정값도 공개되어 있습니다. 프리필은 GPU당 중복 전문가 4개에서 시작해 최근 100스텝 통계로 1,000스텝마다 재배치하고, 디코드는 GPU당 중복 전문가 1개(EP64라면 반올림 후 GPU당 전문가 7개, 공유 전문가 제외), 1,000스텝 통계로 10,000스텝마다 재배치합니다. 가장 느린 랭크와 평균의 비율인 `moe_lb` 측정값은 프리필 1.074(EP4DP4)와 1.045(EP2DP2), 디코드 1.090이라고 합니다.

## 주요 기능

README의 기능 목록을 Q&A 문서의 설명과 묶어 정리했습니다.

### DSpark와 신뢰도 기반 가변 길이 검증

일반적인 추측 디코딩은 초안 토큰을 정해진 개수만큼 모두 검증합니다. DSpark는 초안 토큰마다 수락될 확률을 Confidence Head로 예측하고, 스케줄링할 때 **수락 가능성이 높은 토큰에만 검증 계산을 배분**합니다. Q&A에 따르면 운영에서는 초안 모델이 한 번에 5개를 만들고, 하드웨어 처리량 곡선과 토큰별 예상 수락률로 유효 처리량이 최대가 되는 앞부분 집합을 골라 검증합니다.

Open-PerfectBlend 데이터셋에서 고정 5개 검증과 비교한 Q&A의 표입니다(EP64/DP64 벤치마크 자료로 계산한 추정 처리량, DeepSeek 자체 발표).

| 동시 시퀀스 | 가변 검증 길이 | 수락 길이 (고정 → 가변) | 추정 처리량 tok/s/rank (고정 → 가변) | 차이 |
|---|---|---|---|---|
| 16 | 4.44 | 3.32 → 3.24 | 4,891 → 4,816 | -1.5% |
| 32 | 3.65 | 3.25 → 3.17 | 8,964 → 9,111 | +1.6% |
| 48 | 3.94 | 3.3 → 3.26 | 12,032 → 12,467 | +3.6% |
| 60 | 3.58 | 3.3 → 3.21 | 13,730 → 14,466 | +5.4% |
| 72 | 3.24 | 3.29 → 3.12 | 14,962 → 15,961 | +6.7% |
| 96 | 3.24 | 3.3 → 3.15 | 16,817 → 18,660 | +11.0% |

동시 시퀀스는 랭크(GPU)당 값이고, 고정 방식의 검증 길이는 항상 5입니다. Q&A는 운영 지점(랭크당 약 60개)에서 4~7% 이득이라고 요약합니다. 부하가 낮을 때(16개)는 오히려 1.5% 손해라는 점도 표에 그대로 나와 있습니다.

켜는 방법은 `DEEPINFER_ENABLE_MTP_VARLEN=1`이고, `DEEPINFER_USE_NEXTN_DECODE`가 최대 초안 길이(기본 5)를 정합니다. 0으로 두면 추측 디코딩이 꺼집니다.

### SWA bounded replay

캐시된 접두사 뒤에 이어서 계산하려면 SWA KV 캐시가 필요한데, 이것까지 SSD에 영구 보관하면 저장 비용이 커집니다. DeepInfer는 SWA KV 캐시가 없을 때 **최근 128토큰만 다시 계산해 근사 SWA KV 캐시를 복원**합니다. Q&A는 이로써 재계산 비용이 컨텍스트 길이와 층 수에 무관한 상수가 된다고 설명합니다.

디코더 쪽에도 같은 방식이 쓰입니다. 디코더 층의 SWA KV 캐시를 정확히 복원하려면 마지막 2,560토큰을 디코더 20층에 통과시켜야 하는데, 프롬프트의 마지막 128토큰만 다시 계산하고 그 결과는 디코드에만 쓰며 접두사 캐시에는 넣지 않습니다. Q&A는 이것이 전체 프리필 계산을 거의 절반으로 줄인다고 밝힙니다. README의 V4.1 기본 설정은 `DEEPINFER_YOCO_PREFILL_TRUNCATION_MODE=compact`와 `DEEPINFER_YOCO_PREFILL_KEEP_TOKENS=140`입니다.

### 비동기 스케줄링

디코드 한 스텝은 스케줄링, 순전파, 샘플링, 후처리 순서인데 스케줄링과 후처리는 CPU 작업이라 그동안 GPU가 쉽니다. DeepInfer는 GPU가 N번째 스텝의 순전파와 샘플링을 도는 동안 CPU가 N+1번째 스케줄링과 N-1번째 후처리를 겹쳐 실행합니다. Q&A는 이 방식이 SGLang과 NanoFlow의 기존 구현을 따른 것이라고 적고, README는 기본으로 켜져 있다고 밝힙니다.

### 배치 불변 추론과 결정적 샘플링

`DEEPINFER_BATCH_INVARIANT=1`을 주면 같은 요청이 어떤 요청들과 한 배치로 묶이든 모델 결과가 같게 유지됩니다. 여기에 가변 길이 검증을 끄고(`DEEPINFER_ENABLE_MTP_VARLEN=0`) `SamplingParams`에 고정 `seq_seed`를 주면 같은 입력 토큰과 샘플링 파라미터에 대해 같은 출력이 나옵니다. 두 기능 모두 README에 "NVIDIA only"로 표시되어 있습니다.

### 구조화 출력, 이미지 입력, 평가 스크립트

- **구조화 출력:** `SamplingParams`의 `so_args`에 `schema_type`(`regex`, `json`, `ebnf`)과 `schema`를 넘깁니다. Q&A에 따르면 운영에서는 문법 컴파일을 전용 머신에서 비동기로 하고, 요청은 엔진에 들어가기 전에 컴파일 결과를 받아 옵니다.
- **이미지 입력:** 오프라인 예제의 다섯 샘플 중 세 개가 이미지 입력입니다(1장, 3장, 5장).
- **평가:** `eval/`에 AIME 2026, HLE, GPQA Diamond용 오프라인 배치 평가가 있습니다. 생성과 채점이 분리되어 있고, V4.1 모델의 참고 Pass@1로 AIME 2026 99.9%, GPQA Diamond 93.4%, HLE-Full 42.6%를 제시합니다(DeepSeek 자체 측정). 문서는 이 값을 "배포가 올바르게 구성됐는지 확인하는 용도"라고 설명합니다.

### 저정밀도 연산

Q&A는 FP4를 쓰는 위치를 밝힙니다. 메인 KV(16채널당 스케일 하나, e4m3 스케일), 인덱서 KV(MXFP4), MoE 라우팅 전문가 가중치(MXFP4)입니다. SWA KV는 MXFP8 형식으로 토큰당 528바이트입니다.

## 설치와 시작

README에 있는 방법만 옮깁니다. **사전 빌드 패키지가 없어 소스에서 빌드해야 합니다.**

요구 사항은 Linux, GCC 13 이상, Python 3.12, CUDA 13(NVIDIA) 또는 CANN 9.2(Ascend)입니다. README는 빌드 전에 빈 Python 3.12 환경을 만들어 활성화하라고 안내합니다.

```bash
git clone https://github.com/deepseek-ai/DeepInfer.git
cd DeepInfer

# Use `ascend` instead for the Ascend platform
# Keep it exported in the environment where you run DeepInfer
export DEEPINFER_ACCELERATOR=nvidia
./build.sh
```

`build.sh`는 플랫폼별 요구 사항 파일을 설치하고(NVIDIA는 torch 2.13.0+cu132), NVIDIA에서는 NCCL을 2.32.3으로 다시 설치한 뒤, 서브모듈을 받아 커널 라이브러리를 빌드하고 마지막으로 DeepInfer 확장을 빌드합니다. 서브모듈 초기화는 스크립트가 직접 하므로 `--recursive` 없이 clone해도 됩니다.

오프라인 추론은 다음 한 줄입니다.

```bash
python examples/offline_inference.py
```

기본 체크포인트 `deepseek-ai/DeepSeek-V4.1-Flash-1017`은 첫 실행 때 Hugging Face 캐시로 내려받습니다. 로컬 사본을 쓰려면 `DEEPINFER_HF_MODEL_DIR=/path/to/DeepSeek-V4.1-Flash-1017`을 설정합니다.

## 실전 예제

> 아래 예제는 모두 저장소의 README, `examples/README.md`, 예제 스크립트를 바탕으로 했습니다. **DeepInfer는 NVIDIA SM100 GPU 여러 장이나 Ascend 950 NPU가 있어야 동작하므로, 이 글을 쓴 환경에서는 어느 예제도 실행하지 못했습니다.** 명령과 인자 이름은 2026-11-20 기준 `main` 브랜치 소스와 대조했습니다.

### 예제 1. 병렬 구성을 바꿔 가며 오프라인 추론하기

`examples/README.md`가 제시하는 세 가지 구성입니다.

```bash
python examples/offline_inference.py --ep 8
python examples/offline_inference.py --ep 2 --dp 8
python examples/offline_inference.py --ep 2 --cp 8
```

`--ep`의 기본값은 8입니다. 스크립트를 보면 `--dp`를 생략할 때 DP 크기는 `ep // cp`로 정해지고, DP 랭크마다 프로세스 하나가 뜹니다. 출력에는 샘플별 생성 텍스트와 함께 초안 토큰 수락률(`accept_rate`)과 디코드 퍼플렉시티(`decode_ppl`)가 찍힙니다. `--check_structured_output`을 붙이면 같은 LLM 인스턴스로 정규식, JSON, EBNF 구조화 출력 검사까지 이어서 수행합니다.

여러 노드에 걸칠 때는 `WORLD_SIZE`(노드 수)와 `RANK`(노드 번호) 환경 변수로 각 노드가 맡을 DP 랭크를 나눕니다.

### 예제 2. 정규식, JSON 스키마, EBNF로 출력 형식 강제하기

`examples/_structured_output.py`의 핵심 부분입니다. 프롬프트 문자열만 자리표시 문구로 바꿨습니다. `llm`은 예제의 `create_llm()`이 만든 `LLM` 인스턴스입니다.

```python
import json

from deepinfer.sampling_params import SamplingParams

json_schema = {
    "type": "object",
    "properties": {
        "color": {"type": "string", "enum": ["red", "green", "blue"]},
        "count": {"type": "integer", "enum": [1, 2, 3]},
    },
    "required": ["color", "count"],
    "additionalProperties": False,
}
cases = [
    ("first prompt", {"schema_type": "regex", "schema": r"[A-Z]{2}-[0-9]{3}"}),
    ("second prompt", {"schema_type": "json", "schema": json.dumps(json_schema)}),
    ("third prompt", {"schema_type": "ebnf", "schema": 'root ::= "answer=" ("yes" | "no") ";level=" [1-3]'}),
]
outputs = llm.generate(
    prompts=[prompt for prompt, _ in cases],
    sampling_params=[SamplingParams(temperature=0, max_tokens=128, so_args=so_args) for _, so_args in cases],
    use_tqdm=False,
)
```

원본 예제의 프롬프트는 일부러 형식과 무관한 요청(긴 이야기를 써 달라는 등)을 주고도 출력이 `AB-123` 같은 형식을 지키는지, 마지막 토큰이 정상적인 EOS인지 검사합니다. 예제 설정에서는 `generate()`가 문자열이 아니라 토큰별 출력 객체 목록을 돌려주므로, 텍스트는 `llm.get_tokenizer().decode(...)`로 직접 복원합니다.

### 예제 3. 평가 재현을 위한 결정적 샘플링

README의 안내를 그대로 조합한 것입니다. 환경 변수 두 개와 고정 시드가 필요합니다.

```bash
export DEEPINFER_BATCH_INVARIANT=1
export DEEPINFER_ENABLE_MTP_VARLEN=0
```

```python
from deepinfer.sampling_params import SamplingParams

params = SamplingParams(temperature=1.0, max_tokens=256, seq_seed=1234)
```

`seq_seed`를 주지 않으면 요청마다 64비트 난수 시드가 새로 뽑힙니다(`sampling_params.py`). 저장소의 회귀 테스트가 이 기능에 기대고 있습니다. 오프라인 예제는 NVIDIA에서 `DEEPINFER_BATCH_INVARIANT=1`을 기본으로 켜고 샘플마다 고정 시드를 주며, 퍼플렉시티 기준값을 샘플 단위로 정확히 일치하는지 비교합니다. 가변 길이 검증을 꺼야 한다는 조건 때문에, 재현성과 DSpark의 추가 이득은 함께 얻을 수 없습니다.

### 예제 4. 처리량 벤치마크와 파레토 곡선 그리기

단일 노드에서 벤치마크를 돌리기 전에 장치 환경 변수를 설정합니다.

```bash
export WORLD_SIZE=1 RANK=0
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

python examples/benchmark.py

# low latency: single-request decode (batch=1)
python examples/benchmark.py --decode_num_requests 1

# 128k context + YoCo truncation (nightly profile configuration)
python examples/benchmark.py --decode_num_requests 64 --context_length 131072 --yoco_clip
```

기본값은 디코드 요청 64개, 컨텍스트 32,768토큰, 비캐시 토큰 4,096개, 프리필 배치 32,768토큰입니다. 병렬 규모는 명령 인자가 아니라 환경에서 정해집니다(`ep_size = WORLD_SIZE × 보이는 장치 수`).

README의 성능 그래프는 스윕 스크립트로 재현합니다.

```bash
# decode: sweep decode_num_requests (8…256), nextn=3, plot scaled by a draft acceptance rate of 0.75
bash examples/sweep/run_sweep.sh decode ce-128k 131072 3 0.75

# prefill: sweep prefill_batch_size (4096…65536)
bash examples/sweep/run_sweep.sh prefill pe-128k 131072
```

결과는 `sweeps/<tag>/results.jsonl`과 `sweeps/<tag>/<mode>_pareto.png`로 저장됩니다. 숫자를 읽을 때의 주의점은 아래 "실무 팁"에 따로 적었습니다.

### 예제 5. 벤치마크 점수로 배포 검증하기

`eval/README.md`의 방법입니다. 데이터셋은 스크립트가 내려받지 않으므로 직접 JSONL로 준비해 `eval/data/` 아래에 두거나 `DATA_FILE`로 경로를 줍니다.

```bash
EP=8 N_SAMPLE=4 TAG=smoke bash eval/aime/run.sh            # smoke test
MODEL=/path/to/DeepSeek-V4.1-Flash-1017 bash eval/aime/run.sh   # local HF directory

# judge 서비스 없이 규칙 기반으로 다시 채점
python eval/score.py --out-dir eval/outputs/aime/<TAG> --judge rule
```

기본 채점은 LLM judge 서비스를 쓰며 `EVAL_JUDGE_BASE_URL`, `EVAL_JUDGE_API_KEY`, `EVAL_JUDGE_MODEL` 환경 변수가 필요합니다. AIME와 GPQA는 규칙 기반 채점도 가능하지만 HLE는 자유 서술 답이 많아 LLM judge만 지원합니다. `summary.json`의 `coverage_complete`가 `true`일 때만 Pass@1이 유효합니다.

## 실무 팁 & 자주 겪는 문제

Issues가 꺼져 있어 이슈 트래커 대신 README, 예제 문서, 소스 주석, Discussions를 바탕으로 정리했습니다.

- **`DEEPINFER_ACCELERATOR`는 빌드할 때만이 아니라 실행할 때도 export되어 있어야 합니다.** 확장의 플랫폼 빌드를 고르는 값이라고 평가 문서가 설명합니다.
- **불리언 환경 변수는 엄격하게 해석됩니다.** `0`, `1`, `false`, `true`(대소문자 무시)와 빈 문자열만 받고, 그 밖의 값은 오류가 납니다(`environ.py`, 2026-10-25 병합된 PR #218).
- **CUDA graph를 켠 상태에서 "CUDA error: an illegal memory access was encountered"가 나면** CUDA graph 메모리 부족일 수 있으니 `gpu_memory_utilization`을 낮춰 보라고 `LLM` 클래스 주석이 안내합니다.
- **`DEEPINFER_YOCO_PREFILL_KEEP_TOKENS`는 기본값이 0이라 절단 모드를 켤 때 반드시 직접 지정해야 합니다.** 값은 SWA 창 크기와 최대 되돌림 길이의 합 이상이어야 합니다. Q&A 기준 V4.1에서는 128 + 6 = 134가 하한이고 README의 권장값은 140입니다.
- **벤치마크의 디코드 처리량은 "전부 수락" 가정입니다.** `benchmark.py`가 출력하는 decode throughput은 실제 수락률과 무관하게 요청당 스텝마다 `1 + nextn`개 토큰이 나온다고 보고 계산합니다. `PROFILE=1`일 때의 스텝 시간은 프로파일러 오버헤드가 섞여 있어 처리량 계산에 쓰지 말라고 문서가 경고합니다.
- **Hopper 세대(H100, H200)는 지원 목록에 없습니다.** FlashMLA README는 2026-09-30 릴리스에서 Hopper 아키텍처 지원을 제거했다고 밝힙니다. Discussions에 H200 지원 계획을 묻는 글(#238)과 공식 Docker 이미지·서빙 레시피 로드맵을 묻는 글(#231)이 있지만, 2026-11-20 기준 저장소 소속 계정의 답변은 달려 있지 않습니다. SM90(Hopper), Ascend 910 계열, AMD ROCm 지원을 추가하는 커뮤니티 PR은 여러 개 열려 있으나 병합되지 않았습니다.
- **`nv-dev` 브랜치는 `main`과 다릅니다.** 2026-11-18~19에 SM120(RTX PRO 6000 Blackwell) 오프라인 추론을 추가하는 PR 5개(외부 기여자의 #289, #291과 협업자 계정의 후속 PR 3개)가 `nv-dev`에 병합됐습니다. 그 브랜치의 `README.sm120.md`에 따르면 SM120에서는 CP, 가변 길이 검증, 배치 불변 모드가 엔진 시작 때 거부됩니다. `main` README의 지원 하드웨어 목록에는 아직 반영되지 않았습니다.

## 비슷한 도구와 비교

DeepInfer README는 스스로 "원래 주로 vLLM 위에 만들어졌고 SGLang과 TensorRT-LLM에서 추가로 영감을 얻었다"고 밝힙니다. 그리고 vLLM과 SGLang도 각자 DeepSeek-V4.1-Flash를 지원합니다.

| 항목 | DeepInfer | vLLM | SGLang |
|---|---|---|---|
| 라이선스 | Apache-2.0 | Apache-2.0 | Apache-2.0 |
| 스타 | 약 2.6만 개 | 약 9.7만 개 | 약 3.9만 개 |
| 지원 모델 | DeepSeek-V4.1-Flash 하나 | Hugging Face의 200개 이상 모델 아키텍처 | LLM, 비전-언어, 디퓨전 모델 |
| V4.1-Flash | 기본 대상(1017 체크포인트) | 레시피 파일 있음(최소 vLLM 0.31.0, 1017 변형 포함) | `sglang serve` 명령 모음 있음(11개 중 10개가 unverified 표시) |
| 제공 형태 | 오프라인 추론 Python API와 예제 스크립트 | OpenAI 호환 API 서버, Anthropic Messages API, gRPC | `sglang serve`로 서버 실행 |
| 설치 | 소스 빌드(`./build.sh`) | `uv pip install vllm` | Docker 이미지 또는 `uv pip install --prerelease=allow sglang` |
| 하드웨어 | NVIDIA SM100, Ascend 950 | NVIDIA·AMD·Intel GPU, x86/ARM/PowerPC CPU, 플러그인으로 Ascend 등 | NVIDIA, AMD Instinct, Google TPU, Intel, Apple Silicon, Ascend 등 |
| P/D 분리 | 이번 공개에 미포함 | README 기능 목록에 프리필·디코드·인코드 분리 | 이 글에서 확인하지 않음 |
| 추측 디코딩 | DSpark + 신뢰도 기반 가변 길이 검증 | n-gram, suffix, EAGLE, DFlash. V4.1 레시피에 DSpark와 적응형 검증 | V4.1 명령에 `--speculative-algorithm DSPARK` |
| 문의 창구 | Discussions(Issues 꺼짐) | Issues, 포럼, Slack | Issues, Slack |

스타 수는 2026-11-20 `gh api` 조회값입니다. vLLM 열은 vLLM README와 저장소의 `recipes/models/deepseek-ai/DeepSeek-V4.1-Flash.yaml`, SGLang 열은 SGLang README와 저장소의 `deepseek-ai--DeepSeek-V4.1-Flash-1017.json` 명령 파일에서 확인한 내용만 적었습니다. **세 엔진의 성능을 같은 조건에서 비교한 공식 자료는 찾지 못했고, 이 표는 속도 비교가 아닙니다.** vLLM 레시피는 H100, H200, B200, GB200, GB300, MI300X 계열 등을 verified로 표시하고 있어, DeepInfer가 지원하지 않는 하드웨어에서 이 모델을 돌리려면 현재로서는 두 범용 엔진이 선택지입니다.

README의 Acknowledgments에 함께 언급된 TensorRT-LLM은 이 글에서 따로 조사하지 않았습니다.

## 장점과 한계

### 장점

- **운영 엔진의 실제 코드입니다.** 모델 저장소의 참조 구현과 달리 커널, 병렬 통신, 스케줄러, EPLB까지 서빙에 쓰이는 형태로 들어 있습니다. Q&A는 공개된 커널과 내부 버전의 종단 간 성능 차이가 최대 5%라고 밝힙니다(FlashMLA에 수작업 최적화 하나가 빠져 디코딩 커널이 5~10% 느림).
- **운영 수치가 붙은 설계 문서가 함께 옵니다.** 병렬 구성, EPLB 주기, 저장 서버 사양, 캐시 TTL, 오토스케일링 규칙까지 Q&A 문서에 구체적인 값으로 적혀 있습니다. 2026-11-03에 v0.2로 갱신됐습니다.
- **재현성 기능:** 배치 불변 추론과 결정적 샘플링은 평가와 회귀 테스트에 직접 쓸 수 있는 기능입니다.
- **두 가속기 지원:** 같은 엔진이 NVIDIA와 Huawei Ascend에서 돕니다.
- **Apache-2.0:** 수정과 상업적 사용에 제약이 적습니다. 모델 가중치는 별도로 MIT입니다.

### 한계

- **이것만으로는 서비스를 만들 수 없습니다.** KV 캐시 시스템, P/D 분리, 로드 밸런싱, API 서버가 없습니다. Q&A에서 가장 많은 분량을 차지하는 부분(KV 캐시 저장소, 프리필·디코드 로드 밸런서)이 바로 공개되지 않은 부분입니다.
- **모델과 하드웨어의 폭이 매우 좁습니다.** 모델 하나, 가속기 두 종류입니다. Q&A는 앞으로 나올 DeepSeek 모델의 추론 코드도 DeepInfer에 계속 공개하겠다고 하지만, 다른 회사 모델을 지원한다는 언급은 없습니다.
- **진입 규모가 큽니다.** README 벤치마크는 프리필 GPU 4장, 디코드 GPU 64장에서 측정했고, Q&A가 말하는 효율적인 최소 단위는 프리필 64장과 디코드 64장입니다.
- **프로젝트 운영이 닫혀 있습니다.** 릴리스와 태그가 없고, Issues가 꺼져 있으며, `main`에 병합된 PR은 2개입니다(2026-11-20 기준).
- **성능 수치는 모두 자체 측정입니다.** 벤치마크는 무작위 토큰으로 만든 합성 요청을 쓰는 오프라인 측정이고, Q&A 스스로 운영 환경의 로드 밸런싱이 "완벽하게 균형 잡힌 오프라인 벤치마크의 약 80%"에 이른다고 적습니다.

## 인사이트

**왜 지금 중요한가: 공개의 단위가 가중치에서 서빙 스택으로 넓어지고 있습니다.** [DeepSeek-V4.1-Flash-1017 글](/tech/2026/10/24/deepseek-v4-1-flash-1017.html)에서 필자는 가중치가 MIT로 풀렸어도 동봉 코드는 참조 구현이라 "운영 서빙은 오픈소스 엔진의 지원 상황을 따로 확인해야 한다"고 적었습니다. DeepInfer의 첫 커밋은 그 모델 발표(2026-10-17) 사흘 뒤입니다. 눈여겨볼 점은 V4.1의 구조 자체가 서빙 비용에 맞춰 설계됐다는 것입니다. CED는 프리필을 인코더 20층에서만 계산하게 하고, SWA bounded replay는 SWA KV를 SSD에 보관하지 않아도 되게 하며, DSpark의 Confidence Head는 스케줄러가 쓸 신호(초안 토큰별 예상 수락률)를 모델 쪽에서 내놓습니다. 필자의 판단으로는 이 저장소의 가장 큰 가치는 실행 파일이 아니라, 모델 구조와 추론 시스템을 함께 설계한 사례를 코드와 운영 수치로 확인할 수 있다는 점입니다.

**기존 글과의 연결.** 세 글과 직접 이어집니다. 첫째, [KV 캐시와 추측 디코딩 글](/tech/2026/10/24/kv-cache-speculative-decoding.html)은 추측 디코딩이 "연산 여유가 있는 상황에서만 이득"이라고 정리했습니다. 위 DSpark 표가 정확히 그 이야기입니다. GPU가 한가한 동시 16개에서는 5개를 다 검증하는 쪽이 낫고, 붐비는 96개에서는 덜 검증하는 쪽이 11% 낫습니다. 검증 길이를 부하에 따라 바꾸는 것은 고정된 γ를 쓰던 원 논문 방식에 "지금 연산이 얼마나 남는가"라는 변수를 넣은 것으로 볼 수 있습니다. 같은 글은 vLLM 문서를 인용해 배치 크기에 따라 결과가 달라질 수 있다는 한계를 짚었는데, DeepInfer의 배치 불변 추론은 그 문제에 대한 엔진 차원의 답입니다. 다만 결정적 샘플링에 가변 길이 검증을 꺼야 한다는 조건은 속도 기능과 재현성이 여전히 맞바꾸는 관계임을 보여 줍니다. 둘째, [MoE 해설 글](/tech/2026/10/24/mixture-of-experts.html)에 정리한 DeepSeek-V3의 배포 구성은 프리필 EP32, 디코드 EP320이었고 중복 전문가 배치를 주기적으로(예: 10분마다) 조정했습니다. V4.1에서는 프리필이 EP2~8로 훨씬 좁아지고 디코드는 EP64~128이며, 재배치 주기는 스텝 수(1,000 또는 10,000스텝)로 표현됩니다. "프리필은 좁게, 디코드는 넓게"라는 방향이 더 뚜렷해졌습니다. 셋째, [프롬프트 캐싱 글](/tech/2026/10/24/prompt-caching.html)에서 본 Anthropic과 OpenAI의 캐시 수명은 기본 5분~30분, 긴 옵션도 1시간~24시간 수준이었습니다. DeepSeek는 Q&A에서 에이전트 트래픽 3일, 챗봇 트래픽 7일의 TTL로 약 100PiB 규모 SSD에 KV 캐시를 보관한다고 밝힙니다(자체 발표). 모델 카드가 밝힌 대로 V4.1이 토큰당 전역 KV 캐시를 890바이트로 줄인 것이 이런 장기 보관의 전제로 보이고, 캐시 적중 입력 가격이 미스의 50분의 1(2026-10-24 가격 문서 기준)인 가격표의 배경도 여기서 짐작할 수 있습니다.

**한계와 반론: "프로덕션을 구동한다"와 "이것으로 프로덕션을 만들 수 있다"는 다릅니다.** README 첫 문장은 전자를 말하지만, 공개 범위는 후자에 미치지 못합니다. 빠진 세 가지(KV 캐시 시스템, P/D 분리, 로드 밸런싱)는 Q&A 문서에서 가장 공들여 설명한 부분이고, DeepSeek 서비스의 비용 구조를 만드는 핵심이기도 합니다. 성능 그래프도 주의해서 읽어야 합니다. README의 디코드 그래프는 초당 스텝 수를 실측한 뒤 "초안 3개, 토큰별 수락률 75%"라는 가정으로 스텝당 토큰 수 τ = 1 + 3 × 0.75 = 3.25를 곱한 값입니다(`plot_pareto.py`). 실제 수락률은 작업에 따라 달라지므로 이 그래프의 토큰 처리량은 측정값이 아니라 환산값입니다. 그래프에서 읽은 대략의 값은 요청 8개일 때 사용자당 약 325토큰/초, 256개일 때 GPU당 약 2.6만 토큰/초인데(필자 판독, 오차 있음), 두 값은 서로 다른 운영 지점이라 동시에 얻을 수 없습니다. 하루 155조 토큰과 GPU 시간당 38달러 역시 외부에서 검증할 방법이 없습니다. 또 스타 약 2.6만 개와 포크 약 3,200개라는 관심에 비해 `main`에 병합된 PR이 2개뿐이라는 점에서, 지금의 DeepInfer는 커뮤니티가 함께 만드는 프로젝트라기보다 내부 코드를 공개한 형태에 가깝다고 보입니다.

**실무에 주는 의미.** 필자의 판단으로는 대부분의 팀에게 DeepInfer는 "설치할 도구"가 아니라 "읽을 자료"입니다. DeepSeek-V4.1-Flash를 자체 서빙하려는 팀이라도 API 서버와 넓은 하드웨어 지원이 필요하면 vLLM이나 SGLang이 현실적인 출발점입니다. V4.1 전용 기능인 DSpark가 두 엔진의 설정 파일에, 디코더 SWA bounded replay가 SGLang 명령 파일(`--enable-decoder-swa-bounded-replay`)에 이미 등장한다는 점도 그 근거입니다. 반대로 다음 경우에는 직접 볼 가치가 있습니다. SM100 GPU 64장 이상을 가진 팀이 P/D 분리 구조를 설계할 때 Q&A의 병렬 구성과 EPLB 설정값을 출발점으로 삼는 경우, 추론 엔진 개발자가 비동기 스케줄링이나 가변 길이 검증 구현을 참고하는 경우, 그리고 평가 담당자가 배치 불변 모드로 재현 가능한 기준값을 만들고 싶은 경우입니다.

**앞으로 지켜볼 점.** (1) KV 캐시 저장소와 로드 밸런서가 공개되는지. 공개된다면 DeepInfer는 참고 자료에서 실제 서빙 스택으로 성격이 바뀝니다. (2) `nv-dev`의 SM120 지원이 `main`에 들어오는지, 그리고 Hopper와 Ascend 910 계열, AMD를 다루는 커뮤니티 PR을 받아들이는지. 지원 하드웨어가 넓어지는지가 사용자층을 결정합니다. (3) 첫 태그 릴리스와 Issues 개방 여부. (4) DeepInfer의 기법이 vLLM과 SGLang에 얼마나 빨리 반영되고, 같은 하드웨어에서 세 엔진을 비교한 제3자 측정이 나오는지.

<!-- EDITOR_NOTE: 운영자가 직접 써 본 경험이나 의견을 여기에 추가하세요. -->

## 이런 분께 추천

- NVIDIA SM100 GPU 수십 장 이상 또는 Ascend 950 클러스터에서 DeepSeek-V4.1-Flash를 대량 배치 추론(평가, 데이터 생성)하려는 팀
- 대형 MoE 모델의 P/D 분리, 전문가 병렬, 로드 밸런싱 설계를 실제 운영 수치와 함께 공부하려는 인프라 엔지니어
- 추측 디코딩 스케줄링, 비동기 배치 스케줄러, 배치 불변 커널 같은 엔진 내부 구현을 참고하려는 추론 프레임워크 개발자

## 이런 경우엔 다른 도구

- **OpenAI 호환 API 서버로 바로 서빙해야 한다면:** DeepInfer에는 서버가 없습니다. vLLM이나 SGLang의 DeepSeek-V4.1-Flash 설정을 먼저 확인하는 편이 빠릅니다.
- **H100, H200, AMD GPU처럼 지원 목록에 없는 하드웨어라면:** 현재 `main`에서는 동작을 기대할 수 없습니다.
- **DeepSeek 외의 모델을 서빙한다면:** 지원 모델이 하나뿐이므로 범용 엔진을 써야 합니다.
- **GPU가 몇 장뿐이거나 트래픽이 작다면:** 자체 서빙보다 DeepSeek API가 경제적일 가능성이 큽니다. Q&A가 말하는 효율적인 최소 단위가 GPU 128장입니다.

## 참고 링크

- [DeepInfer 저장소 / README](https://github.com/deepseek-ai/DeepInfer) · [LICENSE](https://github.com/deepseek-ai/DeepInfer/blob/main/LICENSE) · [CONTRIBUTING.md](https://github.com/deepseek-ai/DeepInfer/blob/main/CONTRIBUTING.md) · [Discussions](https://github.com/deepseek-ai/DeepInfer/discussions) · [Pull requests](https://github.com/deepseek-ai/DeepInfer/pulls)
- [DeepSeek V4.1 Flash Inference Deployment Q&A](https://github.com/deepseek-ai/DeepInfer/blob/main/doc/inference_deployment_qa.md) · [examples/README.md](https://github.com/deepseek-ai/DeepInfer/blob/main/examples/README.md) · [eval/README.md](https://github.com/deepseek-ai/DeepInfer/blob/main/eval/README.md) · [YoCo 검증 문서](https://github.com/deepseek-ai/DeepInfer/blob/main/examples/yoco/README.md) · [환경 변수 정의(environ.py)](https://github.com/deepseek-ai/DeepInfer/blob/main/deepinfer/environ.py)
- [nv-dev 브랜치의 README.sm120.md](https://github.com/deepseek-ai/DeepInfer/blob/nv-dev/README.sm120.md) · [SM120 지원 PR #289](https://github.com/deepseek-ai/DeepInfer/pull/289) · [Discussion #231 (Docker·서빙 레시피 로드맵 질문)](https://github.com/deepseek-ai/DeepInfer/discussions/231) · [Discussion #238 (H200 지원 질문)](https://github.com/deepseek-ai/DeepInfer/discussions/238)
- [deepseek-recipe](https://github.com/deepseek-ai/deepseek-recipe) · [FlashMLA](https://github.com/deepseek-ai/FlashMLA) · [DeepGEMM](https://github.com/deepseek-ai/DeepGEMM) · [DeepEP](https://github.com/deepseek-ai/DeepEP) · [TileKernels](https://github.com/deepseek-ai/TileKernels) · [DeepSelect](https://github.com/deepseek-ai/DeepSelect) · [3FS](https://github.com/deepseek-ai/3FS)
- [DeepSeek-V4.1-Flash-1017 모델 카드](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) · [DeepSeek-V4.1-Flash 모델 카드(구조 설명)](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)
- [vLLM](https://github.com/vllm-project/vllm) · [vLLM의 DeepSeek-V4.1-Flash 레시피](https://github.com/vllm-project/vllm/blob/main/recipes/models/deepseek-ai/DeepSeek-V4.1-Flash.yaml) · [SGLang](https://github.com/sgl-project/sglang) · [SGLang의 DeepSeek-V4.1-Flash-1017 명령 파일](https://github.com/sgl-project/sglang/blob/main/python/sglang/cli/_commands/deepseek-ai--DeepSeek-V4.1-Flash-1017.json)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
