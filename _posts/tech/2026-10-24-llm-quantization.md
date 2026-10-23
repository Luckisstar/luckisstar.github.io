---
layout: default
title: "[기술 소개] LLM 양자화 해설: GPTQ, AWQ, GGUF로 내 PC에서 모델 돌리기"
description: "비트 수와 메모리 계산, PTQ와 QAT, 가중치·활성값 양자화의 차이, GPTQ·AWQ·LLM.int8 원 논문 수치, GGUF K-quant 구조, 퍼플렉시티와 KLD로 품질 재는 법을 정리하고 Qwen2.5-1.5B로 직접 양자화해 측정했습니다."
date: 2026-10-24 00:24:00 +0900
categories: [tech]
---

# [기술 소개] LLM 양자화 해설: GPTQ, AWQ, GGUF로 내 PC에서 모델 돌리기

- **주요 출처:** [GPTQ (arXiv:2210.17323, ICLR 2023)](https://arxiv.org/abs/2210.17323) · [AWQ (arXiv:2306.00978, MLSys 2024)](https://arxiv.org/abs/2306.00978) · [LLM.int8() (arXiv:2208.07339, NeurIPS 2022)](https://arxiv.org/abs/2208.07339) · [llama.cpp 양자화 README](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md) · [llama.cpp 퍼플렉시티 README](https://github.com/ggml-org/llama.cpp/blob/master/tools/perplexity/README.md) · [GGUF 명세](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md) · [Hugging Face Transformers 양자화 문서](https://huggingface.co/docs/transformers/main/en/quantization/overview) · [vLLM 양자화 문서](https://docs.vllm.ai/en/latest/features/quantization/)
- **한눈에 (2026-10-24 기준):** 8B 모델은 FP16으로 약 16GB지만, llama.cpp README 기준 Llama-3.1-8B의 Q4_K_M 파일은 4.58GiB입니다. 이때 품질 손실은 퍼플렉시티 기준 약 3%(LLaMA 3 8B, 6.233에서 +0.175)입니다. 필자가 Qwen2.5-1.5B-Instruct로 직접 재 본 결과는 Q4_K_M에서 +4.1%(중요도 행렬 적용 시 +2.8%), Q2_K에서 +63%(적용 시 +39%)였습니다.
- **주의 (2026-10-24 기준):** 한때 표준 도구였던 [AutoGPTQ](https://github.com/AutoGPTQ/AutoGPTQ)(마지막 푸시 2025-04-11)와 [AutoAWQ](https://github.com/casper-hansen/AutoAWQ)(마지막 푸시 2025-05-11)는 둘 다 보관(archived) 상태입니다. Transformers 문서는 GPTQ에 GPT-QModel을, vLLM 문서는 AWQ에 llm-compressor를 권합니다. 옛 튜토리얼의 `pip install auto-gptq`나 `autoawq`를 그대로 따라 하지 않는 편이 좋습니다.

## 한 줄 요약

**양자화(quantization)는 모델 가중치를 16비트 실수 대신 8비트, 4비트 같은 적은 비트로 저장해 메모리와 대역폭을 줄이는 기법입니다.** 핵심 질문은 "몇 비트까지 줄이면 품질이 얼마나 떨어지는가"이고, GPTQ와 AWQ는 4비트에서도 손실을 작게 만드는 알고리즘, GGUF는 그 결과를 CPU와 노트북에서 돌리기 좋게 담는 파일 형식입니다.

## 배경

LLM의 토큰 생성은 계산보다 메모리에서 가중치를 읽어 오는 속도에 묶여 있습니다. GPTQ 논문은 생성 단계의 행렬-벡터 곱이 "대부분 메모리 대역폭에 묶인다(memory-bound)"고 짚었습니다. 토큰 하나를 만들 때마다 모든 가중치를 한 번씩 읽어야 하니, 가중치가 작아지면 메모리에 들어가는 모델이 커지는 동시에 생성 속도도 빨라집니다.

| 시점 | 사건 | 출처 |
|---|---|---|
| 2022-08 | 8비트 행렬 곱에서 이상치(outlier)를 분리 처리하는 LLM.int8() | Dettmers 외, arXiv:2208.07339 |
| 2022-10 | 2차 정보로 오차를 보정해 175B를 GPU 약 4시간에 3~4비트로 줄인 GPTQ | Frantar 외, arXiv:2210.17323 |
| 2023-05 | 4비트 NF4 형식으로 양자화된 모델 위에서 LoRA 학습을 하는 QLoRA | Dettmers 외, arXiv:2305.14314 |
| 2023-06 | 활성값을 보고 중요한 채널을 보호하는 AWQ, MLSys 2024 최우수 논문 | Lin 외, arXiv:2306.00978 |
| 2023-08 | llama.cpp가 GGML을 잇는 단일 파일 형식 GGUF 도입 | llama.cpp PR #2398 (2023-08-21 병합) |
| 2025 | AutoGPTQ, AutoAWQ 보관. 기능은 GPT-QModel, llm-compressor로 이동 | 각 저장소 |

llama.cpp README의 Llama 3.1 표를 보면 효과가 분명합니다. 원본 대비 Q4_K_M 크기는 8B가 32.1GB에서 4.9GB로, 70B가 280.9GB에서 43.1GB로, 405B가 1,625.1GB에서 249.1GB로 줄어듭니다(README 표의 원본은 32비트 기준 크기로 보입니다). 70B 모델이 48GB급 메모리에 들어가느냐 마느냐가 양자화로 갈립니다.

## 핵심 내용

### 1. 메모리 계산: 파라미터 수 × 비트 수 ÷ 8

가중치 메모리의 출발점은 단순합니다.

```text
가중치 바이트 ≈ 파라미터 수 × 비트 수 ÷ 8

8B 모델 FP16 : 8 × 10^9 × 16 / 8 = 16 GB
8B 모델 8비트 : 8 GB
8B 모델 4비트 : 4 GB  (실제로는 스케일 저장 비용 때문에 더 큼)
```

실제 파일이 계산보다 큰 이유는 스케일(scale) 때문입니다. 양자화는 실수 값들을 정수 격자에 맞추는 일이고, 원래 크기로 되돌리려면 "이 묶음의 1칸이 실수로 얼마인지"를 함께 저장해야 합니다. 가장 단순한 absmax 방식은 묶음의 최대 절댓값을 정수 최댓값에 맞춥니다.

```text
s   = max(|w|) / (2^(b-1) - 1)     # 묶음마다 하나의 스케일
w_q = round(w / s)                 # 정수로 저장
w'  = w_q × s                      # 계산할 때 복원 (오차 = w - w')
```

llama.cpp의 Q8_0은 가중치 32개마다 16비트 스케일 하나를 둡니다. 그래서 가중치당 비트 수(BPW, bits per weight)는 8 + 16/32 = 8.5가 되고, README 표의 Llama-3.1-8B Q8_0도 8.5008 BPW, 7.95GiB입니다. 같은 원리로 Q4_K_M은 4.8944 BPW이고, 8.03B × 4.8944 ÷ 8 ≈ 4.58GiB로 README 값과 맞습니다. 70B를 "4비트니까 35GB"로 계산하면 실제 43.1GB와 8GB 넘게 차이가 납니다. 계산할 때는 형식 이름의 비트가 아니라 BPW를 써야 합니다.

묶음 크기를 그룹(group) 또는 블록이라고 부릅니다. 묶음이 작을수록 이상치 하나가 망치는 범위가 줄어 품질은 좋아지지만 스케일 비용이 늘어납니다. GPTQ 논문 표 5 기준으로 그룹 1024는 약 0.02비트, 그룹 128은 약 0.15비트를 더 씁니다.

가중치 외에 KV 캐시(이전 토큰의 키·값을 저장해 두는 메모리)도 필요합니다. 토큰당 크기는 `2 × 층 수 × KV 헤드 수 × 헤드 차원 × 바이트 수`입니다. Qwen2.5-1.5B(28층, KV 헤드 2개, 헤드 차원 128)는 FP16에서 토큰당 28KiB이고, llama.cpp 로그도 2,048칸에 56MiB로 같은 값을 보여 줬습니다. 컨텍스트 8,192 토큰이면 약 224MiB입니다. 큰 모델에서는 이 값이 GB 단위가 되므로, GPTQ 논문도 3비트 OPT-175B 가중치 약 63GB에 KV 캐시 약 9GB를 더해 A100 80GB 한 장에 들어간다고 계산했습니다. KV 캐시 자체를 줄이는 기법은 [KV 캐시와 추측 디코딩 해설](/tech/2026/10/24/kv-cache-speculative-decoding.html)에서 다룹니다.

### 2. PTQ와 QAT

| 구분 | 학습 후 양자화(PTQ) | 양자화 인지 학습(QAT) |
|---|---|---|
| 하는 일 | 다 학습된 가중치를 나중에 줄임 | 학습 중에 양자화 오차를 보며 가중치를 조정 |
| 비용 | 분~시간 단위, 보정 데이터 조금 | 학습 비용 그대로 |
| 누가 하나 | 배포하는 쪽(사용자, 커뮤니티) | 모델을 만드는 쪽 |
| 예 | RTN, GPTQ, AWQ, GGUF K-quant | gpt-oss의 MXFP4, MiniMax-M3.1-Flash의 NVFP4 전문가 |

이 글에서 다루는 GPTQ, AWQ, GGUF는 모두 PTQ입니다. AWQ 논문은 QAT가 "높은 학습 비용 때문에 LLM에 확장하기 어렵다"는 이유로 PTQ를 택했다고 밝힙니다. RTN(round-to-nearest)은 위 absmax처럼 그냥 가장 가까운 정수로 반올림하는 기준선입니다.

최근에는 모델 제작사가 저정밀도 형식으로 직접 배포하는 사례가 늘었습니다. gpt-oss 모델 카드는 MoE 가중치를 MXFP4로 양자화한 상태로 사후 학습을 했다고 밝혔고, 그 덕에 120b가 80GB GPU 한 장, 20b가 16GB 메모리에 들어갑니다. [MiniMax-M3.1-Flash 소개](/tech/2026/10/24/minimax-m3-1-flash.html)에서 다룬 모델은 라우팅 전문가를 학습 중에 NVFP4로 양자화했습니다. 이런 모델은 이미 저정밀도에 적응해 있으므로, 공식 가중치를 다시 다른 방식으로 양자화하면 이점이 사라질 수 있습니다.

### 3. 가중치 양자화와 활성값 양자화

양자화 대상은 두 가지입니다. 흔히 `W4A16`처럼 적는데, 가중치(Weight) 4비트, 활성값(Activation, 층과 층 사이를 흐르는 중간 계산값) 16비트라는 뜻입니다.

- **가중치만(W4A16, W8A16):** 저장과 읽기만 줄고, 계산은 복원한 16비트로 합니다. 배치가 작은 생성 단계처럼 메모리 대역폭이 병목일 때 이득이 큽니다. GPTQ, AWQ, GGUF 대부분이 여기에 속합니다. vLLM INT4 W4A16 문서도 이 방식이 "초당 요청 수가 낮은 워크로드"에 특히 유용하다고 적었습니다.
- **가중치와 활성값 모두(W8A8):** INT8이나 FP8 텐서 코어로 행렬 곱 자체를 빠르게 합니다. 프리필(prompt 처리)이나 큰 배치처럼 계산이 병목일 때 유리합니다. vLLM 호환표 기준 FP8 W8A8은 Ada, Hopper 세대 GPU가 필요합니다.

활성값 양자화가 어려운 이유는 LLM.int8() 논문이 잘 보여 줍니다. 모델이 약 6.7B 규모를 넘으면 활성값에 매우 큰 이상치가 체계적으로 나타나는 "상전이"가 생기고, 시퀀스당 약 15만 개의 이상치가 단 6개 차원에 몰립니다. 이 차원들을 0으로 만들면 퍼플렉시티가 600~1,000% 나빠집니다. 논문은 이상치 차원만 16비트로 따로 곱하고 나머지 99.9% 이상을 8비트로 곱하는 혼합 정밀도 분해로 문제를 풀었습니다. 13B 기준 C4 퍼플렉시티는 FP32 12.45, LLM.int8() 12.45로 같았지만, 단순 absmax 8비트는 19.08로 무너졌습니다(표 1). 다만 6.7B 미만 모델에서는 FP16보다 느렸고, 속도 이득은 175B급 행렬 곱에서 약 2배였습니다. 메모리 절반이 주목적인 방식입니다.

### 4. GPTQ: 반올림 오차를 남은 가중치가 메운다

GPTQ는 층 하나의 출력이 원래와 최대한 같도록 가중치를 하나씩 양자화하면서, 생긴 오차를 아직 양자화하지 않은 가중치들을 조정해 메웁니다. 어느 방향으로 조정할지는 보정 데이터로 구한 2차 정보(헤시안 역행렬)로 정합니다. 보정 데이터는 C4에서 무작위로 뽑은 2,048토큰 구간 128개뿐입니다.

| OPT-175B, WikiText2 PPL | FP16 | 4비트 RTN | 4비트 GPTQ | 3비트 RTN | 3비트 GPTQ |
|---|---|---|---|---|---|
| 표 3 | 8.34 | 10.54 | 8.37 | 7.3e3 | 8.68 |

3비트에서 단순 반올림은 완전히 무너지지만 GPTQ는 8.68에 머뭅니다. 그룹 128을 쓰면 3비트도 8.45까지 좋아집니다(표 5). 양자화 시간은 OPT-175B 4.2시간, BLOOM-176B 3.8시간이었습니다(표 2). 메모리는 FP16의 326GB에서 3비트 약 63GB로 줄어, FP16에 80GB GPU 5장, LLM.int8()에 3장이 필요하던 모델이 1장에 들어갑니다. 속도는 3비트 커널로 A100에서 토큰당 230ms에서 71ms(3.24배), A6000에서 589ms에서 130ms(4.53배)로 빨라졌습니다(표 6). 논문은 또 "큰 모델일수록 양자화하기 쉽다"는 경향을 보고했습니다.

### 5. AWQ: 중요한 가중치는 활성값이 알려 준다

AWQ의 출발점은 가중치 중 0.1~1%만 보호해도 양자화 오차가 크게 준다는 관찰입니다. 중요한지 판단할 때 가중치 크기가 아니라 그 채널로 들어오는 활성값의 크기를 봅니다. OPT-6.7B를 INT3 그룹 128로 양자화하면 RTN 퍼플렉시티가 43.2인데, 활성값 기준 상위 1% 채널만 FP16으로 남기면 13.0으로 떨어집니다(그림 2).

다만 일부만 FP16으로 두면 하드웨어 효율이 나빠집니다. 그래서 AWQ는 중요한 채널의 가중치를 키우고 입력을 그만큼 줄이는 채널별 스케일링으로 같은 효과를 냅니다. 스케일 지수 α를 0~1 사이에서 격자 탐색할 뿐 역전파나 재구성을 하지 않아서, 보정 데이터에 과적합할 위험이 GPTQ보다 작다고 논문은 주장합니다.

| Llama-2-7B, WikiText PPL (표 4) | FP16 | RTN | GPTQ | GPTQ-R | AWQ |
|---|---|---|---|---|---|
| INT4 그룹 128 | 5.47 | 5.73 | 5.69 | 5.63 | 5.60 |
| INT3 그룹 128 | 5.47 | 6.66 | 6.43 | 6.42 | 6.24 |

4비트에서는 차이가 작고, 3비트에서 간격이 벌어집니다. Llama-2-70B INT4는 FP16 3.32 대비 AWQ 3.41이었습니다. 함께 공개한 추론 엔진 TinyChat은 Hugging Face FP16 구현보다 3배 넘게 빨랐다고 보고합니다.

### 6. GGUF와 K-quant, I-quant

GGUF는 알고리즘이 아니라 파일 형식입니다. 명세에 따르면 모델 실행에 필요한 텐서와 메타데이터(토크나이저, 채팅 템플릿, 구조 정보)를 키-값 형태로 한 파일에 담고, mmap(파일을 메모리에 직접 매핑하는 방식)으로 빠르게 불러오도록 설계됐으며, 이전 형식 GGML, GGJT를 잇습니다. 파일 이름 규칙은 `<BaseName><SizeLabel>...<Encoding>` 형태라 `...-Q4_K_M.gguf`처럼 양자화 방식이 이름 끝에 붙습니다.

GGUF 안에 담기는 양자화 유형은 크게 세 가족입니다.

| 가족 | 예 | 특징 |
|---|---|---|
| 기본형 | Q4_0, Q8_0 | 32개 블록마다 스케일 하나. 단순하고 빠름 |
| K-quant | Q2_K~Q6_K, Q4_K_M | 256개 단위 슈퍼블록 안에 하위 블록 스케일을 다시 양자화. `_S/_M/_L`은 텐서별 비트 혼합 정도 |
| I-quant | IQ1_S~IQ4_XS | 저비트 품질을 높이려는 형식. IQ1, IQ2, IQ3_XXS는 중요도 행렬 없이는 양자화가 거부됨 |

`_M` 같은 접미사는 "모든 텐서를 같은 비트로"가 아니라는 뜻입니다. 필자의 Qwen2.5-1.5B Q4_K_M 로그를 보면 대부분 q4_K인데, 출력층(`output.weight`)은 q6_K, 28층 중 14층의 `attn_v`와 `ffn_down`도 q6_K로 들어갔습니다. 이 모델은 출력층이 445MiB(FP16)로 커서, q6_K로 줄여도 182.57MiB가 전체 1,059.89MiB의 17%를 차지합니다. 그래서 같은 Q4_K_M인데도 Llama-3.1-8B(4.89 BPW)보다 높은 5.00 BPW가 나왔습니다. `--pure` 옵션은 이런 혼합을 끄고, `--leave-output-tensor`는 출력층을 원래 정밀도로 둡니다.

중요도 행렬(imatrix)은 보정 텍스트를 모델에 흘려 어떤 가중치가 출력에 크게 기여하는지 기록한 파일입니다. `llama-imatrix`로 만들고 `llama-quantize --imatrix`로 넘기면, 양자화할 때 중요한 가중치의 오차를 더 줄이도록 스케일을 고릅니다. 개념상 AWQ와 비슷하게 "활성값을 보고 중요도를 정한다"는 쪽입니다. 퍼플렉시티 README의 LLaMA 3 8B 표에서 Q4_K_M의 퍼플렉시티 증가는 imatrix 없이 0.175, WikiText imatrix로 0.151이었고, Q3_K_M은 0.657에서 0.503으로 줄었습니다.

### 7. 품질을 재는 법: 퍼플렉시티, KLD, 과제 벤치마크

퍼플렉시티(PPL, perplexity)는 모델이 정답 다음 토큰에 준 확률의 기하평균의 역수로, 낮을수록 좋습니다. 양자화 연구는 관례상 WikiText-2로 잽니다. 하지만 llama.cpp 퍼플렉시티 README는 몇 가지 함정을 분명히 적어 둡니다.

- 토크나이저가 다른 모델끼리는 퍼플렉시티를 비교할 수 없습니다.
- 미세조정 모델은 사람이 느끼는 품질이 좋아져도 퍼플렉시티가 더 높게 나올 수 있습니다.
- llama.cpp의 값은 계산 방식이 달라 다른 프로젝트의 값과 직접 비교할 수 없습니다.

그래서 README는 KL 발산(KLD, Kullback-Leibler divergence)을 함께 보라고 권합니다. 원본 모델과 양자화 모델이 토큰마다 내놓는 확률 분포 전체가 얼마나 다른지를 재는 값입니다. `--kl-divergence-base`로 원본의 로짓을 파일로 저장한 뒤 양자화 모델과 비교하는데, LLaMA 3 8B는 이 파일이 37GiB에 이릅니다. 같은 실행에서 "Same top p"(두 모델의 1순위 토큰이 같은 비율)도 함께 나옵니다.

| LLaMA 3 8B (README 표) | ΔPPL | KLD |
|---|---|---|
| q8_0 | 0.00265 | 0.00136 |
| q6_K | 0.0217 | 0.00545 |
| q4_K_M | 0.175 | 0.0313 |
| q4_0 | 0.469 | 0.0719 |
| q3_K_M | 0.657 | 0.1019 |
| q2_K (imatrix) | 2.42 | 0.331 |

F16 퍼플렉시티 6.233 기준이며 RTX 4090과 Epyc 7742에서 측정한 값입니다. 같은 README는 LLaMA 3 8B가 LLaMA 2 7B보다 양자화에 더 민감하다고 보고합니다. q4_K_M의 KLD가 0.0127에서 0.0313으로, q2_K의 퍼플렉시티 비율이 1.108에서 1.565로 커졌습니다. 필자의 판단으로는 더 많은 데이터로 오래 학습한 모델일수록 가중치에 정보가 촘촘히 담겨 비트를 줄일 여유가 적어지는 것으로 보이며, "예전 모델에서 Q3도 괜찮았다"는 경험을 새 모델에 그대로 옮기면 안 된다는 신호입니다.

퍼플렉시티와 KLD는 빠르고 재현 가능하지만, 코드 생성이나 수학 같은 실제 과제 성능을 직접 보여 주지는 않습니다. vLLM 문서도 양자화 후 `lm_eval`로 GSM8K 같은 과제를 돌려 정확도를 확인하는 절차를 안내합니다. 실무에서는 KLD로 후보를 좁히고, 내가 쓸 과제로 최종 확인하는 순서가 합리적입니다.

## 형식별 비교

| 방식 | 종류 | 비트 | 보정 데이터 | 주 실행 환경 | 도구 상태 (2026-10-24) |
|---|---|---|---|---|---|
| GPTQ | PTQ, 2차 정보 오차 보정 | 2/3/4/8 | 필요 | NVIDIA GPU (vLLM, Transformers) | AutoGPTQ 보관, GPT-QModel(Apache-2.0)·llm-compressor 활발 |
| AWQ | PTQ, 활성값 기반 채널 스케일 | 4 | 필요(소량) | NVIDIA GPU, MLX-LM | AutoAWQ 보관, llm-compressor로 이관 |
| bitsandbytes | 불러올 때 즉석 양자화 (LLM.int8, NF4) | 4/8 | 불필요 | NVIDIA GPU (vLLM 호환표 기준) | 활발(MIT). QLoRA 학습의 기본 |
| GGUF | 파일 형식 + K/I-quant | 약 2~8.5 BPW | 선택(imatrix) | CPU, Apple Silicon, 소비자 GPU | llama.cpp 활발(MIT, 약 13.2만 스타) |
| FP8 W8A8 | 가중치·활성값 8비트 부동소수점 | 8 | 선택 | Ada, Hopper GPU | llm-compressor(Apache-2.0) |
| MXFP4 등 | 제작사 배포 형식(QAT 포함) | 4 | 제작사가 처리 | 최신 GPU, 지원 엔진 | 모델마다 다름 |

Transformers 문서 표 기준으로 GGUF는 그 위에서 PEFT(LoRA 같은 경량 미세조정)를 할 수 없고, bitsandbytes는 할 수 있습니다. vLLM의 GGUF 지원은 문서 스스로 "매우 실험적이고 최적화가 덜 됐다"고 경고하며, 별도 플러그인(`vllm-gguf-plugin`)으로 옮겨졌습니다. GPU 서빙에는 GPTQ, AWQ, FP8 계열을, 로컬 실행에는 GGUF를 쓰는 역할 분담이 현재 생태계의 모습입니다.

## 실무에서 쓰는 법

### 직접 해 본 실험: Qwen2.5-1.5B-Instruct를 GGUF로 양자화

공식 FP16 GGUF(Qwen/Qwen2.5-1.5B-Instruct-GGUF)를 받아 llama.cpp(빌드 8670, Homebrew)로 여섯 가지 형식을 만들고, WikiText-2 테스트 세트 앞 100청크(약 5.1만 토큰)로 퍼플렉시티와 KLD를 쟀습니다. 환경은 Apple M4, 메모리 16GB, Metal 백엔드입니다(2026-10-24 측정).

```bash
# 1) 양자화 (README 2단계. 1단계 HF→GGUF 변환은 공식 F16 GGUF로 대신함)
llama-quantize q15-f16.gguf q15-Q4_K_M.gguf Q4_K_M

# 2) 원본 로짓 저장 후, 양자화 모델과 비교
llama-perplexity -m q15-f16.gguf -f wiki.test.raw --chunks 100 --kl-divergence-base base.kld
llama-perplexity -m q15-Q4_K_M.gguf -f wiki.test.raw --chunks 100 \
  --kl-divergence-base base.kld --kl-divergence

# 3) 속도 (프롬프트 512토큰 처리, 128토큰 생성, 3회 반복)
llama-bench -m q15-Q4_K_M.gguf -p 512 -n 128 -r 3
```

| 형식 | 크기 | BPW | PPL 비율 | KLD | 1순위 일치 | 생성 t/s |
|---|---|---|---|---|---|---|
| F16 | 3,389.80MiB | 16.00 | 1 (PPL 10.317) | 0 | 100% | 29.45 |
| Q8_0 | 1,801.09MiB | 8.50 | 1.0008 | 0.0004 | 98.7% | 47.74 |
| Q6_K | 1,390.67MiB | 6.56 | 1.0036 | 0.0044 | 96.0% | 측정 안 함 |
| Q4_K_M | 1,059.89MiB | 5.00 | 1.0410 | 0.0329 | 90.7% | 77.59 |
| Q4_0 | 1,011.16MiB | 4.77 | 1.0471 | 0.0594 | 87.8% | 측정 안 함 |
| Q3_K_M | 875.96MiB | 4.13 | 1.1210 | 0.1069 | 83.3% | 측정 안 함 |
| Q2_K | 712.33MiB | 3.36 | 1.6324 | 0.5032 | 67.2% | 81.37 |

중요도 행렬의 효과도 따로 쟀습니다. WikiText-2 학습 세트 100청크로 `llama-imatrix -m q15-f16.gguf -f wiki.train.raw --chunks 100 -o imatrix.gguf`를 돌린 뒤 `llama-quantize --imatrix imatrix.gguf ...`로 다시 만들었습니다. 파일 크기는 그대로이고 품질만 달라집니다.

| 형식 | PPL 비율 (없음 → imatrix) | KLD (없음 → imatrix) | 1순위 일치 |
|---|---|---|---|
| Q4_K_M | 1.0410 → 1.0282 | 0.0329 → 0.0271 | 90.7% → 91.4% |
| Q3_K_M | 1.1210 → 1.1027 | 0.1069 → 0.0916 | 83.3% → 84.6% |
| Q2_K | 1.6324 → 1.3882 | 0.5032 → 0.3381 | 67.2% → 72.5% |

비트가 낮을수록 효과가 커서, Q2_K는 퍼플렉시티 증가가 63%에서 39%로 줄었습니다. 그래도 Q4_K_M(imatrix 없음)보다는 훨씬 나쁩니다.

읽을 점은 네 가지입니다.

- **Q8_0, Q6_K는 사실상 무손실입니다.** 퍼플렉시티 차이가 0.4% 이내입니다.
- **Q4_K_M은 크기를 3분의 1 이하로 줄이면서 손실이 약 4%입니다.** 같은 4비트대인 Q4_0보다 파일은 48MiB 크지만 KLD는 절반 수준입니다. 비트 혼합과 K-quant 구조의 효과로 보입니다.
- **Q2_K는 작은 모델에서 쓰기 어렵습니다.** imatrix 없이 퍼플렉시티가 63% 늘고 1순위 토큰이 셋 중 하나꼴로 바뀝니다. README의 LLaMA 3 8B(비율 1.565, 56% 증가)보다 조금 더 나쁩니다.
- **생성 속도는 크기에 거의 비례합니다.** F16 대비 Q4_K_M은 크기 3.2분의 1, 생성 속도 2.6배입니다. 반면 프롬프트 처리 속도는 F16 1,155 t/s, Q4_K_M 1,012 t/s로 오히려 조금 느려졌습니다. 프롬프트 처리는 계산 병목이라 복원 비용이 드러나는 것으로, README의 Llama-3.1-8B 표(F16 923.49, Q4_K_M 821.81 t/s)와 같은 경향입니다.

한 가지 함정도 겪었습니다. 처음에는 더 작은 Qwen2.5-0.5B(은닉 차원 896)로 실험했는데, `llama-quantize`가 "ncols 896 not divisible by 256"이라는 경고와 함께 291개 텐서 중 145개를 q5_0이나 q8_0으로 대체했습니다. K-quant는 256개 단위 슈퍼블록을 쓰기 때문입니다. 그 결과 Q2_K가 5.20 BPW, Q3_K_M이 5.41 BPW로 Q4_0(5.37)보다 커지는 역전이 생겼습니다. 은닉 차원이 256의 배수가 아닌 모델에서는 형식 이름만 보고 크기와 품질을 판단하면 안 되며, 양자화 로그의 fallback 경고를 꼭 확인해야 합니다.

### Hugging Face Transformers에서 (문서 기반, 필자 미실행)

아래 코드는 Transformers bitsandbytes 문서의 두 예시(모델 불러오기, 계산 dtype 지정)를 합친 것이며, CUDA GPU가 없어 필자가 실행하지는 않았습니다. 불러올 때 즉석으로 4비트로 만드는 bitsandbytes 방식입니다.

```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
model = AutoModelForCausalLM.from_pretrained(
    "facebook/opt-350m", device_map="auto", quantization_config=quantization_config
)
```

GPTQ로 미리 양자화해 저장하려면 `GPTQConfig`를 씁니다. 문서는 "AutoGPTQ는 Transformers에서 더 이상 지원하지 않으니 GPT-QModel을 설치하라"고 안내하며, 175B 모델 양자화에 A100 한 장으로 약 4시간이 걸린다고 적었습니다.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, GPTQConfig

tokenizer = AutoTokenizer.from_pretrained("facebook/opt-125m")
gptq_config = GPTQConfig(bits=4, dataset="c4", tokenizer=tokenizer)
model = AutoModelForCausalLM.from_pretrained("facebook/opt-125m", device_map="auto", quantization_config=gptq_config)
```

### vLLM 서빙용 (문서 기반, 필자 미실행)

vLLM 문서는 llm-compressor로 W4A16 체크포인트를 만드는 예를 듭니다. AWQ는 같은 도구의 `AWQModifier`로 옮겨 왔습니다.

```python
from llmcompressor import oneshot
from llmcompressor.modifiers.quantization import GPTQModifier

recipe = GPTQModifier(targets="Linear", scheme="W4A16", ignore=["lm_head"])
oneshot(model=model, dataset=ds, recipe=recipe,
        max_seq_length=MAX_SEQUENCE_LENGTH, num_calibration_samples=NUM_CALIBRATION_SAMPLES)
model.save_pretrained(SAVE_DIR, save_compressed=True)
```

`lm_head`(출력층)를 양자화 대상에서 빼는 점이 llama.cpp가 출력층에 더 높은 비트를 주는 것과 같은 판단입니다.

## 선택 가이드

필자의 판단으로 정리하면 다음과 같습니다. 출발점은 "메모리 = 가중치 파일 + KV 캐시 + 런타임 여유"를 내 기기에 맞추는 것입니다.

| 상황 | 추천 | 이유 |
|---|---|---|
| Mac, CPU, 소비자 GPU | GGUF Q4_K_M부터 | 위 실험과 README 모두 손실 약 3~4%에 크기 3분의 1 |
| 메모리 여유 있음 | Q5_K_M, Q6_K, Q8_0 | Q6_K부터는 사실상 무손실 |
| 메모리가 빠듯함 | imatrix를 적용한 Q3_K_M이나 IQ 계열 | 3비트대는 imatrix 유무 차이가 큼 |
| 작은 모델(3B 이하) | Q4_K_M 이상 유지 | 작은 모델은 비트 감소에 민감. Q2_K는 피함 |
| NVIDIA GPU 서빙, 요청 적음 | W4A16 (GPTQ, AWQ via llm-compressor) | 대역폭 병목인 생성 단계에서 이득 |
| NVIDIA GPU 서빙, 요청 많음 | FP8 W8A8 (Ada, Hopper) | 계산 병목인 큰 배치와 프리필에서 이득 |
| 적은 GPU로 미세조정 | bitsandbytes NF4 + LoRA(QLoRA) | 양자화 모델 위에서 어댑터 학습 가능 |
| 제작사가 저정밀도로 배포 | 공식 가중치 그대로 | QAT 이점을 지키려면 재양자화하지 않음 |

같은 메모리라면 "큰 모델을 낮은 비트로"와 "작은 모델을 높은 비트로" 중 무엇이 나을지도 자주 나오는 질문입니다. GPTQ 논문은 큰 모델일수록 양자화가 쉽다고 보고했지만, 이 결론이 최신 모델의 4비트 이하 구간에도 그대로 성립하는지는 모델마다 직접 확인해야 합니다. 필자는 4비트 근처까지는 큰 모델 쪽이 유리하고, 3비트 아래로 내려가야 할 정도라면 한 단계 작은 모델의 Q4~Q6을 함께 비교해 보는 편이 안전하다고 봅니다.

## 한계와 논란

- **퍼플렉시티는 과제 성능이 아닙니다.** 이 글의 표 대부분은 WikiText 퍼플렉시티입니다. 긴 추론, 코드, 다국어처럼 확률 분포의 꼬리에 민감한 과제에서는 평균 지표보다 손실이 크게 나타날 수 있다는 지적이 있으며, KLD를 함께 보는 이유이기도 합니다.
- **보정 데이터 의존성.** GPTQ와 AWQ, imatrix는 모두 보정 텍스트를 씁니다. 영어 위키 텍스트로 보정한 모델이 한국어나 코드에서도 같은 품질을 낸다는 보장은 없습니다. AWQ가 과적합이 적다고 주장하는 것도 이 문제를 의식한 것입니다. 필자의 실험은 imatrix를 WikiText 학습 세트로 만들고 테스트 세트로 쟀으므로, 같은 분포 안의 평가라는 한계가 있습니다.
- **수치의 비교 가능성.** README가 경고하듯 llama.cpp 퍼플렉시티는 다른 프로젝트 값과 계산 방식이 다릅니다. 이 글의 GPTQ, AWQ 논문 표와 llama.cpp 표를 서로 직접 비교하면 안 됩니다. README의 속도 표(Llama-3.1-8B)는 측정 하드웨어가 명시되지 않아 절대값보다 형식 간 경향으로만 읽어야 합니다.
- **도구 생태계의 이동.** AutoGPTQ와 AutoAWQ가 2025년에 보관되면서, 2023~2024년의 많은 튜토리얼과 허브의 오래된 체크포인트 설명이 현재 도구와 맞지 않습니다. AutoAWQ를 설치하면 Transformers가 4.47.1로 내려간다는 경고도 Transformers 문서에 남아 있습니다.
- **재양자화 손실.** `llama-quantize --allow-requantize`는 이미 양자화된 파일을 다시 양자화하게 해 주지만, README는 품질이 크게 떨어질 수 있다고 경고합니다. 항상 16비트 원본에서 시작해야 합니다.

## 인사이트

**왜 지금 중요한가.** 양자화는 "연구 기법"에서 "모델 배포 형식의 일부"로 바뀌는 중입니다. 2022년에는 사용자가 GPTQ로 직접 모델을 줄였다면, 지금은 gpt-oss의 MXFP4나 MiniMax-M3.1-Flash의 NVFP4처럼 제작사가 처음부터 저정밀도로 학습하거나 배포합니다. 필자의 판단으로는 앞으로 오픈 모델을 고를 때 "몇 B인가"만큼 "어떤 정밀도로 배포되는가"가 중요한 사양이 될 것으로 보입니다. 같은 맥락에서 [MoE 해설](/tech/2026/10/24/mixture-of-experts.html)이 강조한 "MoE는 계산만 줄이고 메모리는 줄이지 않는다"는 약점을 실제로 메우는 것이 양자화입니다.

**실무에 주는 의미: 형식 이름 대신 세 숫자를 보라.** (1) BPW로 실제 메모리를, (2) KLD나 퍼플렉시티 비율로 원본 대비 손실을, (3) 내 과제의 정확도로 최종 품질을 확인해야 합니다. "4비트"라는 말 하나에 4.5~5.0 BPW의 차이, Q4_0과 Q4_K_M의 두 배 가까운 KLD 차이가 숨어 있습니다. 로컬 실행이라면 Q4_K_M을 기준점으로 두고, 메모리가 허락하는 만큼 위로 올리는 것이 가장 실패가 적은 전략으로 보입니다.

**블로그의 기존 글과의 연결.** [LoRA 논문 리뷰](/papers/2026/10/24/lora.html)에서 다룬 QLoRA는 이 글의 bitsandbytes NF4 위에 LoRA 어댑터를 얹는 방식이라, 양자화와 미세조정이 만나는 지점입니다. [Reflection AI Beam 소개](/tech/2026/10/20/reflection-beam.html)는 501B 모델을 4비트로 줄여도 가중치만 약 250GB라고 계산했는데, 이 글의 BPW 기준으로 보면 Q4_K_M급(약 4.9 BPW)에서는 300GB를 넘을 수 있습니다. "4비트 = 파라미터 수의 절반 바이트"라는 어림은 하한선으로 읽는 편이 안전합니다.

**한계와 반론.** 양자화가 "거의 공짜"라는 인상은 대부분 영어 퍼플렉시티와 8B 이상 모델에서 나온 것입니다. 작은 모델, 낮은 비트, 영어 밖의 언어에서는 손실이 커질 수 있고, 필자의 1.5B 실험에서도 Q2_K는 실사용이 어려운 수준이었습니다. 또 양자화는 메모리와 생성 속도를 개선하지만 프롬프트 처리 속도는 오히려 조금 느려질 수 있어, 긴 문서를 한 번에 넣는 RAG 같은 작업에서는 체감 이득이 기대보다 작을 수 있습니다.

**앞으로 지켜볼 점.** (1) MXFP4, NVFP4 같은 블록 스케일 4비트 부동소수점 형식이 오픈 모델의 기본 배포 형식이 될지. vLLM의 Marlin 커널은 이미 FP4를 지원 대상에 넣었습니다. (2) QAT로 배포된 모델을 GGUF로 옮길 때 품질이 얼마나 유지되는지. (3) llm-compressor처럼 GPTQ, AWQ, FP8을 한 도구로 묶는 흐름이 굳어지면서, 알고리즘 선택이 도구 선택과 분리되는지.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers (arXiv:2210.17323)](https://arxiv.org/abs/2210.17323)
- [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration (arXiv:2306.00978)](https://arxiv.org/abs/2306.00978)
- [LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale (arXiv:2208.07339)](https://arxiv.org/abs/2208.07339)
- [QLoRA: Efficient Finetuning of Quantized LLMs (arXiv:2305.14314)](https://arxiv.org/abs/2305.14314)
- [llama.cpp 양자화 README](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md) · [퍼플렉시티 README](https://github.com/ggml-org/llama.cpp/blob/master/tools/perplexity/README.md) · [imatrix README](https://github.com/ggml-org/llama.cpp/blob/master/tools/imatrix/README.md)
- [GGUF 명세 (ggml docs/gguf.md)](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md)
- Hugging Face Transformers 문서: [양자화 개요](https://huggingface.co/docs/transformers/main/en/quantization/overview) · [GPTQ](https://huggingface.co/docs/transformers/main/en/quantization/gptq) · [bitsandbytes](https://huggingface.co/docs/transformers/main/en/quantization/bitsandbytes)
- vLLM 문서: [양자화](https://docs.vllm.ai/en/latest/features/quantization/) · [INT4 W4A16](https://docs.vllm.ai/en/latest/features/quantization/int4/) · [GGUF](https://docs.vllm.ai/en/latest/features/quantization/gguf/)
- [llm-compressor AWQ 예제](https://github.com/vllm-project/llm-compressor/tree/main/examples/awq) · [GPT-QModel](https://github.com/ModelCloud/GPTQModel)
- [gpt-oss-120b 모델 카드](https://huggingface.co/openai/gpt-oss-120b) · [Qwen2.5-1.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
