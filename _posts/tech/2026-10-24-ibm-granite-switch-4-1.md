---
layout: default
title: "[기술 소개] IBM Granite Switch 4.1: 어댑터를 합쳐 한 엔드포인트에서 채팅·판단·음성인식까지"
description: "IBM Granite Switch 4.1이 기본 모델, aLoRA 어댑터 2개, 음성인식 인코더를 한 체크포인트로 합치는 방식과 KV 캐시 재사용 원리, aLoRA 원 논문의 수치, vLLM 호출 예제, 한계를 정리했습니다."
date: 2026-10-24 00:59:30 +0900
categories: [tech]
---

# [기술 소개] IBM Granite Switch 4.1: 어댑터를 합쳐 한 엔드포인트에서 채팅·판단·음성인식까지

- **발표:** IBM Granite 팀(Kate Soule, Subhajit Chaudhury, Hendrik Strobelt, Luis A Lastras), 2026년 10월 15일 Hugging Face 커뮤니티 글. 모델 카드상 출시일은 2026년 10월 14일
- **원문:** [발표 글](https://huggingface.co/blog/ibm-granite/granite-switch-4-1) · [모델 카드 granite-switch-4.1-30b](https://huggingface.co/ibm-granite/granite-switch-4.1-30b) · [GitHub generative-computing/granite-switch](https://github.com/generative-computing/granite-switch) · [aLoRA 원 논문 arXiv:2504.12397](https://arxiv.org/abs/2504.12397)
- **한눈에 (2026-10-24 기준):** Granite 4.1 30B 기본 모델에 aLoRA 어댑터 2개(`decision`, `guardian-core`)와 470M 음성인식 모델을 합친 단일 체크포인트. 어댑터 때문에 늘어난 파라미터는 +3.89%(BUILD.md). 라이선스는 모델과 코드 모두 Apache-2.0, gated 아님.
- **주의:** 음성 입력은 저장소 문서가 **알파(alpha)** 라고 밝힌 기능으로, 영어만 지원하고 음성 모델과 LLM이 함께 학습되지 않은 단순 연결(cascade) 방식입니다. 실행 요구 버전 폭이 좁습니다(Transformers 5.16~5.17.0, vLLM 0.26 이상 0.28 미만, 모델 카드 기준).

## 한 줄 요약

**IBM이 기본 모델 하나에 "필요할 때만 켜지는" 어댑터와 음성인식 인코더를 미리 합쳐 배포했고, 어댑터가 기본 모델의 KV 캐시를 그대로 이어 쓰기 때문에 채팅 도중 판단이나 안전성 검사로 전환해도 긴 문맥을 다시 계산하지 않습니다.**

## 배경

LoRA(저랭크 적응, Low-Rank Adaptation)는 기본 모델 가중치를 고정한 채 작은 행렬만 학습해 모델을 특화하는 방법입니다([LoRA 논문 소개](/papers/2026/10/24/lora.html)). 어댑터 여러 개를 한 서버에 올려 두고 요청마다 골라 쓰는 멀티 LoRA 서빙도 vLLM 같은 엔진에서 이미 흔합니다.

문제는 **한 대화 안에서** 어댑터를 바꿀 때입니다. aLoRA 원 논문(arXiv:2504.12397)은 이렇게 설명합니다. LoRA는 Q·K·V 가중치를 바꾸므로, 기본 모델이 만든 KV 캐시(이전 토큰의 키·값을 저장해 두는 캐시)를 LoRA가 쓸 수 없고, 어댑터를 바꿀 때마다 전체 입력을 모든 층에 다시 통과시켜야 합니다. 문맥이 길수록, 평가용 어댑터를 여러 개 붙일수록 이 재계산 비용이 커집니다.

IBM Research는 이 문제를 풀기 위해 2025년 4월 **Activated LoRA(aLoRA)** 를 발표했고(arXiv 최초 제출 2025-04-16, 최신 v5 2025-10-02, 모델 카드는 NeurIPS 2025 발표로 소개), 2026년 6월 4일 [Granite Libraries와 Granite Switch 프로젝트](https://research.ibm.com/blog/granite-libraries-project-switch)를 공개했습니다. 이번 4.1은 그 Switch 방식으로 만든 "기본 구성 포함" 체크포인트입니다.

| 날짜 | 사건 | 출처 |
|---|---|---|
| 2025-04-16 | aLoRA 논문 arXiv 제출, 구현을 Hugging Face PEFT에 기여 | [arXiv:2504.12397](https://arxiv.org/abs/2504.12397) |
| 2025-11-26 | vLLM에서 기본 모델과 aLoRA 간 프리픽스 캐시 재사용 구현 논문(MIT·IBM) | [arXiv:2512.17910](https://arxiv.org/abs/2512.17910) |
| 2026-06-04 | Granite Libraries, Granite Switch 프로젝트 공개 | [IBM Research 블로그](https://research.ibm.com/blog/granite-libraries-project-switch) |
| 2026-10-14 | granite-switch-4.1-8b, -30b 모델 공개 | 모델 카드, HF API `createdAt` |
| 2026-10-15 | Granite Switch 4.1 발표 글 | [HF 블로그](https://huggingface.co/blog/ibm-granite/granite-switch-4-1) |

## 핵심 내용

### 1. 무엇이 한 체크포인트에 들어 있나

30B 모델 카드와 `BUILD.md`에 적힌 구성은 다음과 같습니다.

| 구성 요소 | 역할 | 세부 (BUILD.md, 모델 카드 기준) |
|---|---|---|
| Granite 4.1 30B | 기본 모델, 일반 채팅 | 밀집(dense) 디코더, 64층, 컨텍스트 131,072 토큰, 12개 언어(한국어 포함) |
| `guardian-core` aLoRA | 안전성 판정(유해성, 탈옥, 욕설, 폭력, 성적 내용, 사회적 편향 등) | rank 16, Q·K·V·O 투영에 적용, 출력은 `{"score": "yes"}` 또는 `"no"` |
| `decision` aLoRA | 범용 판단: 상태와 선택지를 주면 선택지별 확률 반환 | rank 64, 어텐션과 MLP 7개 모듈에 적용, 한 번의 순전파로 답 |
| Granite Speech 5.0 TurboCTC | 음성을 텍스트로 변환 | 470M, 영어, 비자기회귀 conformer CTC 인코더 |

파라미터 수는 기본 모델 28,865,728,512개에서 합친 뒤 29,989,814,272개로 **+3.89%** 늘었습니다(BUILD.md). 발표 글은 세 기능을 합쳐도 "기본 모델 단독과 거의 같은 VRAM"을 쓴다고 표현합니다. 같은 구성의 8B 버전(`granite-switch-4.1-8b`)이 있고, 음성 없이 Granite Libraries 어댑터 전체를 넣은 `-preview` 체크포인트(30B, 8B, 3B)도 따로 있습니다.

### 2. 어떻게 전환하나: 제어 토큰과 스위치 층

모델 카드는 방식을 **coarse-grained expert switching**(굵은 단위 전문가 전환)이라고 부릅니다. MoE(전문가 혼합, Mixture of Experts)가 토큰마다 층마다 전문가를 고르는 것과 달리, 여기서는 **연속된 토큰 구간 전체에 하나의 어댑터가 모든 층에 걸쳐** 켜집니다.

1. 채팅 템플릿에 `adapter_name`을 넘기면 템플릿이 `<|decision|>`(토큰 id 100353) 같은 제어 토큰을 넣습니다.
2. 가벼운 스위치 층(일반 어텐션)이 제어 토큰을 감지해 위치별 어댑터 번호(예: `[0, 0, 0, 2, 2, ...]`)를 만듭니다.
3. 모든 디코더 층이 이 번호를 보고 해당 위치에만 그 어댑터의 LoRA 가중치를 더합니다.

모델 카드가 꼽는 성질은 네 가지입니다. 각 어댑터는 기본 모델의 KV 캐시만 보고 다른 어댑터의 내부 상태는 보지 않으며(KV cache normalization), 어댑터끼리 공동 학습하지 않고 따로 개발·배포하며, 체크포인트 하나가 Transformers와 vLLM에서 변환 없이 돌고, 어댑터 선택은 채팅 템플릿만으로 이뤄집니다.

### 3. 왜 전환 비용이 사라지나: aLoRA의 원리

aLoRA의 아이디어는 단순합니다. **어댑터 가중치를 "호출 지점 이후" 토큰에만 적용합니다.** 원 논문의 식 (6)은 호출 위치 이전 토큰의 키·값에는 기본 가중치를, 이후 토큰에만 LoRA로 보정한 가중치를 씁니다. 그러면 호출 지점 이전의 모든 내부 상태가 기본 모델과 같아지고(논문 명제 1), 기본 모델이 이미 계산한 KV 캐시를 그대로 이어 쓸 수 있습니다.

논문은 재사용 패턴을 셋으로 나눕니다.

- 기본 모델이 생성한 답을 어댑터가 검사 (예: 답변 품질 평가)
- 어댑터가 입력을 먼저 검사한 뒤 그 캐시를 기본 모델이 이어 받아 생성 (예: 입력 안전성 검사 후 답변)
- 여러 어댑터가 같은 캐시를 공유 (예: 한 답을 여러 기준으로 동시 평가). 논문은 이 경우의 이득이 가장 크다고 봅니다.

Granite Switch 4.1의 `decision` 어댑터가 정확히 이 구조를 씁니다. 어댑터 문서에 따르면 상태(state)는 첫 번째 사용자 턴으로 **고정된 기본 모델**에서 계산되고, 어댑터는 질문 턴의 `### DECISION` 표지에서 켜집니다. 그래서 같은 상태에 대해 질문을 여러 개 던져도 상태 부분의 KV 캐시는 한 번만 계산됩니다. 발표 글은 일반 채팅 요청과 판단 요청이 "공유된 프리픽스 캐시"를 쓴다고 강조합니다.

대가도 있습니다. 논문은 aLoRA가 LoRA보다 **더 높은 rank가 필요할 때가 있다**고 밝힙니다. LoRA는 문맥 토큰의 키·값까지 바꿔 필요한 정보를 압축해 둘 수 있지만, aLoRA는 그럴 수 없기 때문이라는 설명입니다. 또 aLoRA는 선택적으로 적용되므로 기본 가중치에 병합(merge)할 수 없습니다. 어댑터가 생성한 토큰의 캐시는 다른 어댑터나 기본 모델이 재사용할 수 없다는 점도 논문이 적어 둔 제약입니다.

### 4. 음성은 같은 엔드포인트의 "앞단 변환"

음성인식은 별도 서버 없이 같은 vLLM 프로세스에서 돌지만, 구조는 단순 연결입니다. 저장소의 [AUDIO.md](https://github.com/generative-computing/granite-switch/blob/main/docs/AUDIO.md)에 따르면 오디오를 작은 ASR(자동 음성 인식) 모델이 텍스트로 바꾸고, 그 전사문을 일반 텍스트 토큰으로 프롬프트에 끼워 넣습니다. 문서 스스로 이를 알파로 표시하고, 음성 인코더 임베딩을 학습된 투영으로 LLM에 직접 넣는 방식은 이후 업그레이드라고 설명합니다.

- 긴 오디오는 기본 120초 창, 5초 겹침으로 잘라 전사한 뒤 합칩니다(`config.json`의 `asr_chunk_length_s`, `asr_chunk_overlap_s`).
- 한 요청에 오디오 클립은 기본 최대 32개입니다.
- ASR 모델은 설정으로 바꿀 수 있습니다. 문서는 다국어가 필요하면 `openai/whisper-small` 등을 예로 듭니다.
- ASR을 CPU로 돌리면 GPU 메모리를 KV 캐시에 모두 줄 수 있지만, 전사가 몇 배 느려진다고 문서가 적고 있습니다(노트북 CPU에서 실시간의 약 3배 속도로 측정).

### 5. 직접 조합할 수도 있다

4.1 체크포인트는 IBM이 고른 어댑터를 미리 넣은 "기본 구성"이고, `granite-switch` 도구로 직접 조합할 수 있습니다. 모델 카드는 이 체크포인트를 다시 만드는 명령을 공개합니다.

```bash
python -m granite_switch.composer.compose_granite_switch \
  --base-model ibm-granite/granite-4.1-30b \
  --adapters ibm-granite/granitelib-guardian-r1.0 ibm-granite/granitelib-core-r1.0 \
  --include-adapters guardian-core decision \
  --enable-audio \
  --output ./granite-switch-4.1-30b
```

서빙 쪽에서는 IBM이 만든 SWITCH 커널이 vLLM 백엔드에 들어 있습니다. [SWITCH_KERNELS.md](https://github.com/generative-computing/granite-switch/blob/main/docs/SWITCH_KERNELS.md)는 기본 가중치와 모든 어댑터의 A 행렬을 한 행렬로 쌓아 GEMM 한 번으로 처리하고, 어댑터마다 자기 rank로만 확장 연산을 하도록 바꿨다고 설명합니다. 이 커널은 Granite Switch 아키텍처 전용이며 다른 모델의 vLLM LoRA 경로를 대체하지는 않는다고 명시돼 있습니다.

## 성능과 비교

공개된 수치는 대부분 IBM 자체 측정입니다. 측정 주체와 조건을 함께 정리합니다.

| 항목 | 수치 | 측정 주체·조건 |
|---|---|---|
| aLoRA 평가기 속도 | LoRA 대비 최대 35배 | aLoRA 논문 그림 3, vLLM, 기본 모델과 프롬프트 길이에 따라 다름 |
| aLoRA 정확도 | LoRA와 차이 중앙값 0.0%, 평균 0.6%p LoRA 우위(p=0.8) | aLoRA 논문 그림 4, Llama 3.2 1B/3B, Llama 3.1 8B, Mistral 7B, 7개 SFT 과제 |
| vLLM 교차 캐시 재사용 | 종단 지연 최대 58배, 첫 토큰 시간 100배 이상 단축 | arXiv:2512.17910(MIT·IBM), 표준 LoRA 대비 |
| SWITCH 커널 디코드 | Punica 대비 1.21~1.38배(같은 rank), 최대 5.9배(rank-512 하나 섞임) | IBM, Granite 4.1 3B, H100 1장, 배치 32 |
| `decision` Decision Index | 전체 50.1 (Tools 76.5, Language 58.6, Arts 26.4 등) | IBM, Decision Index v0.3 공개 fast 부분집합 1,068행, 호스팅 vLLM |
| Doom 플레이 | 초당 60~100회 판단 (Jev 공개 수치 초당 10회) | IBM 발표 글, 커스텀 어댑터를 붙인 3B 모델 |

몇 가지는 비교 근거가 약합니다. 발표 글은 `guardian-core`가 안전 관련 판단 과제에서 Jev 1.13, Microsoft-Decision-1, GPT-Luna-Decisions, Clef-Flash보다 "평균적으로" 낫다고 하지만 본문에는 수치표가 없고, 비교는 [granitelib-evals Space](https://huggingface.co/spaces/ibm-granite/granitelib-evals)로 안내합니다. 5단계 RAG 워크플로 "경주"에서 Granite-Switch-4.1-30B(aLoRA 4개)가 Jev-27B보다 "훨씬 빨랐다"는 내용도 구체적인 시간 없이 서술만 있습니다. Doom 비교에서 Jev의 초당 10회는 [typesafe.ai 블로그](https://typesafe.ai/blog/introducing-system-one-models-and-jev)의 공개 수치를 인용한 것으로, 같은 하드웨어에서 잰 값인지는 밝혀져 있지 않습니다.

## 써 볼 수 있나

**라이선스와 접근 (2026-10-24 기준):** 30B, 8B 체크포인트와 음성 모델 모두 Apache-2.0, gated 아님(HF API 확인). GitHub 저장소도 Apache-2.0, 스타 115개, 2026-10-22 마지막 push.

**요구 사항 (모델 카드 기준):** Python 3.9 이상, PyTorch 2.11.0 이상, Transformers 5.16 이상 5.17.0 이하, vLLM(선택) 0.26.0 이상 0.28.0 미만. 발표 글은 vLLM은 플러그인으로, llama.cpp는 네이티브로 지원한다고 적고 있습니다. 30B bf16 가중치는 약 300억 파라미터이므로 단일 소비자용 GPU로는 어렵고, 8B 버전이 현실적인 시작점으로 보입니다(필자 판단).

아래는 모델 카드 예제를 줄인 것입니다. 하나의 vLLM 서버에서 요청 필드 하나로 어댑터를 바꿉니다. **필자는 GPU 환경이 없어 실행하지 않았습니다.**

```bash
pip install -e ".[vllm]"   # granite-switch 저장소에서
python -m vllm.entrypoints.openai.api_server \
  --model ibm-granite/granite-switch-4.1-30b --port 8000
```

```python
from openai import OpenAI
from transformers import AutoTokenizer

MODEL_ID = "ibm-granite/granite-switch-4.1-30b"
client = OpenAI(base_url="http://localhost:8000/v1", api_key="unused")
tok = AutoTokenizer.from_pretrained(MODEL_ID)
label_ids = [tok(l, add_special_tokens=False)["input_ids"][0] for l in "ABC"]

resp = client.chat.completions.create(
    model=MODEL_ID,
    messages=[
        # 상태 턴: 기본 모델에서 계산되어 일반 채팅과 프리픽스 캐시를 공유
        {"role": "user", "content": "State:\nMy payouts have failed three times. ..."},
        # 질문 턴: ### DECISION 표지에서 decision aLoRA가 켜짐
        {"role": "user", "content": "### DECISION\nQuestion:\nWhich team should handle this ticket?\n\n"
                                    "Options:\nA: Payout failures\nB: Login and account access\nC: Something else\n\n"
                                    "Reply with exactly one option label."},
    ],
    extra_body={
        "chat_template_kwargs": {"adapter_name": "decision"},  # "guardian-core"로 바꾸면 안전성 판정
        "logprob_token_ids": label_ids,                        # vLLM 확장 필드
    },
    max_completion_tokens=1, logprobs=True, top_logprobs=1, temperature=0,
)
```

모델 카드가 밝힌 주의점: 상태 턴과 일반 채팅 요청의 토큰이 같아야 프리픽스 캐시가 공유되므로 시스템 프롬프트를 넣지 않습니다. vLLM은 `logprob_token_ids`를 요청당 128개로 제한하므로, 선택지가 128개를 넘으면 128개씩 나눠 같은 프롬프트로 여러 번 요청한 뒤 softmax를 한 번에 계산합니다. `decision`에는 아직 Mellea 인트린식(intrinsic) 함수가 없어 위처럼 저수준으로 호출해야 하고, `guardian-core`는 Mellea의 `guardian_check`로 호출할 수 있습니다.

## 한계와 논란

- **음성은 알파이고 단순 연결입니다.** 영어 전용, 소문자·구두점 없는 전사, LLM과 공동 학습 안 됨. 모델 카드는 "잘못 전사된 단어가 모델이나 어댑터의 응답을 조용히 바꿀 수 있다"고 경고합니다. "한 모델이 음성을 이해한다"기보다 "한 프로세스 안에 ASR이 붙어 있다"에 가깝습니다.
- **벤치마크 대부분이 자체 측정이고 일부는 수치가 없습니다.** Guardian 비교와 RAG 경주는 수치표 없이 서술만 있습니다. 모델 카드에는 OpenASR 리더보드 "가장 빠름" 주장 옆에 날짜를 넣으라는 작성용 주석(TODO)이 그대로 남아 있습니다.
- **`decision` 확률은 보정된 분류기가 아닙니다.** 모델 카드는 학습하지 않은 도메인에서 선택지 확률을 "판단을 돕는 사전 정보로 보고, 인증된 분류로 다루지 말라"고 권합니다. Decision Index 전체 50.1점 중 Arts 26.4, Knowledge 32.4처럼 영역 편차도 큽니다.
- **안전 범위가 좁습니다.** 이 체크포인트에는 Guardian Library의 사실성 탐지·교정, 정책 가드레일 어댑터가 들어 있지 않다고 모델 카드가 명시합니다.
- **의존성 버전 폭이 좁습니다.** Transformers 마이너 버전 두 개, vLLM 마이너 버전 두 개만 지원 범위입니다. 사용자 정의 아키텍처(`GraniteSwitchForCausalLM`)라 일반 서빙 스택에 바로 올리기 어렵습니다.
- **aLoRA 고유의 제약이 있습니다.** 더 높은 rank가 필요할 수 있고(논문), 기본 가중치에 병합할 수 없으며, 어댑터 생성 구간의 캐시는 재사용되지 않습니다.

## 인사이트

**왜 지금 중요한가.** 에이전트 파이프라인은 "답을 쓰는 호출"보다 "판단하는 호출"이 훨씬 많아지고 있습니다. 이 도구를 부를까, 이 답이 근거에 맞나, 이 입력이 안전한가 같은 짧은 판단을 매번 별도 모델(별도 엔드포인트)에 보내면 같은 긴 문맥을 여러 번 prefill해야 합니다. Granite Switch는 이 문제를 모델 구조 차원에서 풉니다. 필자가 보기에 핵심은 어댑터 합성 자체보다 **"판단 호출의 비용이 문맥 길이가 아니라 질문 길이에 비례하게 만든다"** 는 점입니다. [KV 캐시와 추측 디코딩](/tech/2026/10/24/kv-cache-speculative-decoding.html)이 한 요청 안의 생성 비용을 줄이는 기술이라면, aLoRA는 서로 다른 "모델" 사이에서 캐시를 넘겨 쓰게 해 요청 간의 중복 비용을 줄입니다.

**블로그의 기존 글과의 연결.** [LoRA 논문 소개](/papers/2026/10/24/lora.html)에서 본 LoRA의 장점은 "기본 모델 하나에 작은 어댑터를 갈아 끼운다"였습니다. aLoRA는 그 장점을 한 대화 안으로 끌고 들어오면서, LoRA가 원래 갖던 "병합하면 추론 비용 0"이라는 성질은 포기합니다. 즉 LoRA가 "배포 시점의 모듈성"이었다면 aLoRA는 "실행 시점의 모듈성"이고, 대가로 rank와 병합 불가를 치르는 교환입니다. 또 [프롬프트 캐싱](/tech/2026/10/24/prompt-caching.html)과 비교하면, 상용 API의 프롬프트 캐싱은 같은 모델 안에서 같은 프리픽스를 재사용하지만, aLoRA는 **가중치가 다른 모델 사이**에서 프리픽스를 재사용한다는 점이 다릅니다.

**실무에 주는 의미.** 자체 호스팅으로 RAG나 고객 지원 파이프라인을 운영하면서 생성 모델 옆에 분류기·안전성 검사기·라우터를 따로 띄우고 있다면, 이 구조가 직접적인 대안입니다. 다만 도입 판단은 두 가지로 갈립니다. 첫째, 판단 호출이 긴 공유 문맥 위에서 여러 번 일어나는 워크로드여야 이득이 큽니다. 문맥이 짧거나 판단이 한 번뿐이면 별도 소형 분류기와 차이가 작습니다. 둘째, 기본 모델을 Granite로 고정하는 결정입니다. 어댑터는 특정 기본 모델 가중치에 묶이므로, 기본 모델을 바꾸면 어댑터를 모두 다시 학습해야 합니다. 프롬프트 설계에서도 바뀌는 점이 있습니다. 캐시를 공유하려면 상태(문맥)를 앞에, 지시를 뒤에 두는 "late prompting" 구조로 요청을 짜야 하며, 시스템 프롬프트 하나만 달라져도 공유가 깨집니다.

**한계와 반론.** "채팅, 판단, 음성을 한 엔드포인트에서"라는 제목은 사실이지만 무게가 다릅니다. 판단 쪽은 논문과 커널까지 갖춘 기술이고, 음성 쪽은 문서가 스스로 알파라고 부르는 ASR 앞단 연결입니다. 또 발표의 비교 대상(Jev, Microsoft-Decision-1 등)은 대부분 폐쇄형 "판단 모델"이고, 비교 수치가 본문에 없거나 하드웨어 조건이 다릅니다. "판단 모델" 시장이 막 형성되는 중이라 공통 벤치마크(Decision Index 같은)의 신뢰도도 아직 검증 단계로 보입니다.

**앞으로 지켜볼 점.** (1) 발표 글이 예고한 Mellea Adapter SDK가 나와 제3자가 aLoRA 어댑터를 학습해 조합할 수 있게 되는지(2026-10-24 기준 예정). (2) 기본 모델과 aLoRA 간 캐시 재사용이 Granite Switch 전용 백엔드를 넘어 vLLM 본류에 들어가는지. arXiv:2512.17910의 구현은 별도 브랜치였습니다. (3) 음성이 단순 연결에서 학습된 투영 방식으로 바뀌는지. 이 세 가지 중 (2)가 가장 중요하며, 이것이 풀리면 aLoRA는 Granite만의 기능이 아니라 어떤 오픈 모델에도 쓸 수 있는 서빙 패턴이 됩니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [Granite Switch 4.1: Chat, Decisions, and Speech from One Endpoint (Hugging Face, 2026-10-15)](https://huggingface.co/blog/ibm-granite/granite-switch-4-1)
- [granite-switch-4.1-30b 모델 카드](https://huggingface.co/ibm-granite/granite-switch-4.1-30b)
- [granite-switch-4.1-8b 모델 카드](https://huggingface.co/ibm-granite/granite-switch-4.1-8b)
- [generative-computing/granite-switch (GitHub)](https://github.com/generative-computing/granite-switch)
- [Audio Input (Alpha) 문서](https://github.com/generative-computing/granite-switch/blob/main/docs/AUDIO.md)
- [SWITCH kernels 문서](https://github.com/generative-computing/granite-switch/blob/main/docs/SWITCH_KERNELS.md)
- [Activated LoRA: Fine-tuned LLMs for Intrinsics (arXiv:2504.12397)](https://arxiv.org/abs/2504.12397)
- [Efficient Multi-Adapter LLM Serving via Cross-Model KV-Cache Reuse with Activated LoRA (arXiv:2512.17910)](https://arxiv.org/abs/2512.17910)
- [Decision 어댑터 README (granitelib-core-r1.0)](https://huggingface.co/ibm-granite/granitelib-core-r1.0/blob/main/decision/README.md)
- [Guardian Core 어댑터 README (granitelib-guardian-r1.0)](https://huggingface.co/ibm-granite/granitelib-guardian-r1.0/blob/main/guardian-core/README.md)
- [Granite Libraries and Project Switch (IBM Research, 2026-06-04)](https://research.ibm.com/blog/granite-libraries-project-switch)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
