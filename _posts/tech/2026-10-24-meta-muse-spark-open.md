---
layout: default
title: "[기술 소개] Meta Muse Spark Open: 816B MoE 오픈웨이트, 그러나 오픈소스 라이선스는 아니다"
description: "Meta가 공개한 816B/42B 활성 MoE 모델 Muse Spark Open의 구조, 1M 컨텍스트, 독립 배포를 전제한 안전 후학습과 벤치마크 측정 조건, 하드웨어 요구, Muse Model License 조항과 OSI 정의의 차이를 정리했습니다."
date: 2026-10-24 00:48:00 +0900
categories: [tech]
---

# [기술 소개] Meta Muse Spark Open: 816B MoE 오픈웨이트, 그러나 오픈소스 라이선스는 아니다

- **발표:** Meta (모델 카드 저자 표기: Meta Superintelligence Labs), 2026년 10월 15일
- **원문:** [Meta AI Research 발표](https://research.meta.ai/blog/muse-spark-open) · [PyTorch 블로그](https://pytorch.org/blog/muse-spark-open/) · [Hugging Face 모델 카드](https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B) · [개발자 문서](https://dev.meta.ai/resources/blog/build-with-muse-spark-open) · [평가 방법론 PDF](https://research.meta.ai/static/muse-spark-open-evaluation-methodology)
- **한눈에 (2026-10-24 기준):** 총 816B, 토큰당 활성 42B 파라미터의 MoE(전문가 혼합, Mixture of Experts) 모델로 전문가 256개 중 8개를 고릅니다. 추론 시 컨텍스트 1M 토큰, 입력은 텍스트·이미지·영상·오디오, 출력은 텍스트입니다. 시스템 가드레일 없이 단독 배포되는 상황을 전제로 추가 안전 후학습을 했다고 밝힙니다.
- **도입 전 확인할 사항:**
  - **비표준 라이선스입니다.** Muse Model License는 OSI 승인 오픈소스 라이선스가 아니며, 사용 정책(Usage Policy) 준수, "Built with Muse Spark Open" 표시 의무, 월 매출 기준 MaaS(Model as a Service) 별도 계약 조항, 분야별 사용 금지 조항을 담고 있습니다(아래 "라이선스" 절에서 원문 인용).
  - **Gated 가중치입니다.** Hugging Face에서 수동 승인(`gated: manual`) 방식이며, 법적 실명, 생년월일, 국가, 소속, 직함을 입력해야 하고 IP 기반 위치 정보가 수집됩니다. 18세 미만은 사용 대상이 아니라고 명시합니다.
  - **하드웨어 요구가 큽니다.** 모델 카드 기준 NVFP4는 GPU 메모리 700GB 이상, BF16은 2TB가 필요합니다.
  - 특정 국가에 대한 사용 제한 조항은 확인하지 못했습니다. 모델 카드는 무역 규제(trade compliance) 법규를 포함한 관련 법을 어기는 사용을 금지한다고만 적고 있습니다.

## 한 줄 요약

**Meta가 8월에 선보인 Muse Spark의 오픈웨이트 버전을 내놓으며 "가장 유능한 미국산 오픈웨이트 모델"이라고 소개했습니다.** 816B 규모 MoE에 1M 컨텍스트, 네이티브 멀티모달, 첫날부터 주요 추론 엔진 지원까지 갖췄지만, 라이선스는 사용 분야와 대형 MaaS 사업을 제한하는 자체 라이선스라 "오픈소스"와는 구분해서 봐야 합니다.

## 배경

PyTorch 블로그는 이번 공개가 "8월의 Muse Spark 출시를 기반으로" 하며, Muse Spark 1.3과 같은 베이스 모델을 공유한다고 설명합니다. 8월 5일 Meta AI Research 블로그에서는 터미널 코딩 에이전트 Muse Code(베타)와 그 기반 모델 Muse Spark 1.2를 발표했습니다. 이번 Muse Spark Open은 개발자 문서 표현대로 "Muse Spark의 오픈웨이트 버전"이고, Meta는 앞서 작은 dense 모델 Muse Glimmer를 공개한 적이 있다고 덧붙입니다.

발표문의 "미국산(US)"이라는 수식어에는 맥락이 있습니다. 블로그의 [Reflection AI Beam 글](/tech/2026/10/20/reflection-beam.html)에서 다뤘듯, 최근 몇 년간 내려받아 쓸 수 있는 상위 오픈 모델은 상당수가 중국산이었습니다. 실제로 Meta 자체 비교표에서도 Kimi K3, GLM 5.3 같은 모델이 여러 항목에서 Muse Spark Open보다 높습니다(아래 "성능과 비교" 참고). "가장 유능한"은 미국산이라는 범위 안에서의 주장으로 읽어야 정확합니다.

## 핵심 내용

### 1. 구조: 256개 전문가 중 8개를 쓰는 816B MoE

모델 카드에 공개된 구조는 다음과 같습니다.

| 항목 | 값 (모델 카드 기준) |
|---|---|
| 유형 | MoE 트랜스포머 + Perception Encoder |
| 파라미터 | 총 816B / 활성 42B |
| 레이어 | 62개, 은닉 차원 8192 |
| 어텐션 | GQA(그룹 쿼리 어텐션), Q 헤드 128개 / KV 헤드 16개, 헤드 차원 64, 게이트 어텐션, QK-norm |
| 전문가 | 256개, 토큰당 8개 활성(top-k 라우팅) |
| 어휘 | 202,048개, 입출력 임베딩 분리(각 약 1.66B) |
| Perception Encoder | 1.8B, 50 레이어, 14x14 패치, 희소 어텐션(4번째 레이어마다와 마지막 레이어만 전체 어텐션) |
| 컨텍스트 | 추론 시 1M 토큰 |
| 언어 | 100개 이상 언어 데이터로 학습 |

활성 비율은 42B/816B로 약 5%입니다. 토큰마다 전체 가중치의 일부만 계산하므로 연산량은 40B대 dense 모델에 가깝지만, **메모리에는 816B 전부를 올려야** 합니다. MoE의 이 비대칭이 아래 하드웨어 요구와 Mac Studio 두 대 구성의 배경입니다. MoE의 일반 원리는 [MoE 개념 글](/tech/2026/10/24/mixture-of-experts.html)에서 다룹니다.

참고로 Hugging Face API가 보고하는 safetensors 파라미터 합계는 약 8,220억 개(BF16 8,219억 + F32 1.3억)로, 816B 표기와 약간 다릅니다(2026-10-24 확인). 차이가 어디서 오는지는 공개 자료로 확인하지 못했습니다.

### 2. 독립 배포를 전제한 추가 안전 후학습

이번 공개에서 Meta가 가장 강조한 차별점입니다. 모델 카드와 PyTorch 블로그는 오픈웨이트 버전에 "시스템 가드레일 없이 단독 모델로 쓰일 때 오용에 더 견고하도록 추가 안전 후학습"을 했다고 적고 있습니다. API로 제공하는 모델은 서비스 쪽 필터와 모니터링이 함께 동작하지만, 가중치를 내려받은 사용자는 그런 계층 없이 모델을 돌릴 수 있기 때문입니다.

모델 카드가 밝힌 안전 평가 결과(모두 Meta 측정 또는 Meta가 인용한 값)는 다음과 같습니다.

- **사이버 보안:** 시스템 안전장치 없이 적응형 공격자가 API처럼 질의하는 조건에서, 내부 벤치마크 탈옥 시도의 99.2%, PolyGuard(사이버 부분), RedCode, CyberBench 2024를 합친 기준 94.8%를 거부했습니다. 같은 조건에서 Kimi K3는 75.5%, 70.2%였다고 합니다.
- **화학·생물:** SecureBio BioTIER 거부 벤치마크에서 유해 요청의 98% 이상, 내부 단일 턴 화학 벤치마크에서 99% 이상을 거부했습니다.
- **통제 상실:** MASK 정직성 98.1%, Agentic Misalignment 오작동률 0%.

동시에 모델 카드는 "이 평가는 시험 조건에서 공개 체크포인트를 특성화한 것이며, 하류 수정이 안전성을 떨어뜨릴 수 있고 공개 체크포인트의 결과를 수정된 모델에 그대로 적용해서는 안 된다"고 분명히 적습니다. 그리고 사용 사례에 맞는 가드레일을 갖춘 더 큰 AI 시스템의 일부로 배포하라고 "강하게 권고"합니다.

### 3. 에이전트용 출력 형식: 수신자를 지정하는 메시지

Hugging Face에 공개된 채팅 템플릿을 보면 모델 출력이 **수신자(recipient)** 단위로 나뉩니다. `self`(비공개 추론과 도구 계획), `commentary`(도구 호출 전후 사용자에게 보이는 중간 안내), 도구 이름, `user`(턴을 끝내는 최종 응답)입니다. PyTorch 블로그가 말한 "행동하기 전에 의도를 밝히는 별도의 commentary"가 이 구조입니다. 추론 강도는 `reasoning_effort`로 `low`, `medium`, `high`, `xhigh` 중 고르며 기본값은 `xhigh`입니다. 템플릿에는 도구 스키마를 나중에 불러오는 지연 로딩(`defer_loading`) 표기도 들어 있습니다.

모델 카드는 사용자 대상 애플리케이션에서 원시 사고 과정(chain-of-thought)을 노출하지 말고, 내부 어시스턴트 메시지를 사용자 조작으로부터 보호하라고 권합니다.

### 4. 첫날 생태계 지원

개발자 문서와 발표문 기준으로 공개 당일 지원 범위가 넓습니다.

- **추론 엔진:** SGLang, vLLM, TensorRT-LLM, Hugging Face Transformers, MLX, llama.cpp, Unsloth
- **정밀도:** Meta 제공 BF16(약 1.6TB)과 NVFP4(약 530GB, 전문가 가중치만 양자화), AMD의 FP8·MXFP4, Intel의 MXFP4·INT4, Unsloth의 GGUF(약 2비트까지)
- **추측 디코딩용 초안 모델:** SGLang용 DFlash V2, vLLM용 DSpark. 개발자 문서는 DFlash V2가 AMD MI355X 단일 요청에서 처리량 3.7배, 동시 16요청에서 2.9배라고 밝힙니다(정확도 변화 없음, 측정은 개발자 문서 기준).
- **커널:** PyTorch 블로그에 따르면 RoPE, RMSNorm, 양자화 등을 PyTorch 기반 커널 언어 Helion으로 구현해 NVIDIA GB300에서 하드웨어 전용 커널 대비 1.03~3.95배 빨랐고, AMD MI350에서 종단 간 처리량이 3% 올랐습니다.
- **후학습:** TorchTitan(SFT, LoRA, 강화학습), NVIDIA NeMo AutoModel, Hugging Face TRL, Fireworks AI와 Together AI의 관리형 학습 API
- **호스팅 API:** Baseten, Fireworks AI, Groq(제한 프리뷰), Modal, Nebius, OpenRouter, Together AI

## 성능과 비교

모델 카드의 비교표 중 일부입니다. Muse Spark Open은 `xhigh` 추론 강도, temperature 1.0, top_p 1.0으로 측정했습니다.

| 벤치마크 | Muse Spark Open | Qwen3.8-2.4T-A95B | GLM 5.3 | Kimi K3 | Mistral Large 4 |
|---|---|---|---|---|---|
| AA Intelligence Index | 39 | 40 | **45** | 44 | 38 |
| JobBench | **61.8** | 52.7 | 61.4 | 54.3 | - |
| MCP-Atlas | **89.2** | 84.5 | 84.2 | 82.3 | - |
| Toolathlon Verified | 72.8 | 72.5 | 73.0 | **76.5** | - |
| HLE-Diamond (도구 없음) | **26.1** | 17.3 | 16.4 | 22.2 | - |
| DeepSWE 1.1 | 60 | 57 | 67 | **68** | 62 |
| Terminal-Bench 2.1 | 76.4 | 82.0 | 83.9 | **85.0** | - |
| FORTRESS ARS (낮을수록 좋음) | **5.8** | 21.6 | 28.2 | 26.7 | - |
| FORTRESS ORS (낮을수록 좋음) | 17.4 | 12.8 | 3.2 | **2.7** | - |
| StrongREJECT v2 (낮을수록 좋음) | **0.5** | 65.6 | 62.9 | 66.6 | - |

**측정 주체가 항목마다 다릅니다.** 평가 방법론 PDF에 따르면 다음과 같습니다.

- AA Intelligence Index, GDPval-AA, SciCode, GPQA, Terminal-Bench 2.1 등은 Artificial Analysis 수치를 2026년 10월 7일에 가져왔습니다. Terminal-Bench 2.1은 Terminus 2 하네스 기준입니다.
- JobBench, Toolathlon 일부, MCP-Atlas(Scale AI 실행), HLE-Diamond(Scale AI)는 공식 리더보드 값입니다.
- DeepSWE와 SWE-Atlas-QnA는 **모델마다 다른 하네스**입니다. Muse Spark Open은 Meta의 Muse Code, GLM 5.3은 mini-swe-agent, Qwen3.8은 Claude Code, Kimi K3는 Kimi Code이며, Beam과 Mistral Large 4는 하네스를 밝히지 않은 자체 보고치입니다.
- **StrongREJECT v2는 Meta 내부 벤치마크**(202개 금지 행동)이고 모든 결과가 내부 실행입니다. OSWorld, 멀티모달 항목도 상당수 내부 실행입니다.
- 방법론 문서는 스스로 "타사 모델에 맞춰 튜닝하지 않은 설정이라 각 회사가 최적화한 성능을 반영하지 않을 수 있다"고 밝힙니다.

표에서 읽을 수 있는 것은 두 가지입니다. 첫째, Muse Spark Open은 **에이전트 도구 사용(JobBench, MCP-Atlas)과 도구 없는 지식 추론(HLE-Diamond)에서 강하지만**, 터미널·코딩 벤치마크와 종합 지수에서는 GLM 5.3, Kimi K3보다 낮습니다. 둘째, 안전 지표의 대가가 보입니다. 유해 응답 위험(ARS)은 가장 낮지만 **무해한 요청을 거부하는 비율(ORS)은 17.4로 표에서 가장 높습니다.** GLM 5.3(3.2), Kimi K3(2.7)보다 5배 이상 자주 무해한 요청을 거절한다는 뜻이므로, 정상 사용에서 과잉 거부가 실무 마찰이 될 수 있습니다.

## 써 볼 수 있나

**가중치 받기.** Hugging Face 저장소에서 접근 요청 양식을 제출하고 수동 승인을 받아야 합니다. 2026-10-24 기준 필자가 로그인 없이 확인한 결과 `README.md`와 `LICENSE.md`는 열리지만 `config.json`, 가중치, `USE_POLICY.md`는 접근이 막혀 있습니다.

**하드웨어.** 자료마다 수치가 조금씩 다릅니다.

| 구성 | 출처 | 요구 사항 |
|---|---|---|
| BF16 | 모델 카드 / 개발자 문서 | GPU 메모리 2TB / 가중치 약 1.6TB |
| NVFP4 | 모델 카드 | GPU 메모리 700GB 이상 |
| NVFP4 | 개발자 문서 | 가중치 약 530GB, Blackwell Ultra GPU 4장 또는 H200 8장 |
| NVFP4 + MLX | 발표문, 개발자 문서 | M5 Ultra Mac Studio 2대(각 512GB) 또는 256GB 4대 |
| GGUF 약 2비트 | 개발자 문서 | 시스템 RAM + VRAM 합계 약 300GB (표에는 256GB 구성으로 기재) |

모델 카드의 700GB와 개발자 문서의 530GB 차이는 KV 캐시 등 실행 여유분 포함 여부의 차이로 보이지만, 문서에 명시되지는 않았습니다.

**vLLM으로 띄우기 (개발자 문서 예시, 직접 실행하지 않음).** 필자는 해당 규모의 GPU가 없어 실행해 보지 못했습니다. 아래는 개발자 문서의 vLLM 명령에서 추측 디코딩 설정을 뺀 형태입니다.

```bash
vllm serve meta-models/Muse-Spark-Open-816B-A42B-NVFP4 \
    --tensor-parallel-size 4 \
    --enable-expert-parallel \
    --max-model-len 1048576 \
    --reasoning-parser muse \
    --tool-call-parser muse \
    --enable-auto-tool-choice
```

`--enable-expert-parallel`은 전문가들을 GPU에 나눠 싣는 설정이고, `--reasoning-parser`와 `--tool-call-parser`는 위에서 설명한 수신자 기반 출력 형식을 해석하기 위한 Muse 전용 파서입니다. 모델 카드가 권하는 샘플링 설정은 temperature 1.0, top_p 1.0, top_k 비활성입니다.

**가볍게 시험하려면** 위 호스팅 API 제공사를 쓰는 편이 현실적입니다. 가격은 제공사마다 다르며 이 글에서는 확인하지 않았습니다.

## 라이선스: "오픈웨이트"와 "오픈소스"의 간극

Meta 발표문은 이 라이선스를 "제한된 상업 조건(limited commercial terms)으로 많은 개발자가 무료로 쓸 수 있게 한다"고 소개합니다. PyTorch 블로그는 "Meta는 오픈소스를 사랑한다"며 이 모델을 "안전 측면에서 최고의 오픈소스 선택지"라고까지 표현합니다. 그러나 라이선스 원문을 읽으면 오픈소스 정의와는 거리가 있습니다. 아래 인용은 모두 [LICENSE.md](https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B/blob/main/LICENSE.md) 원문(2026-10-24 확인)이며, 해석은 필자의 독해일 뿐 법률 자문이 아닙니다.

**허용 범위는 넓게 시작합니다.** 전문(前文)은 MIT 라이선스와 비슷한 문장으로 사용, 복제, 수정(미세조정 포함), 파생물 생성, 증류, 배포, 재라이선스, 판매 권리를 부여하되 "다음 조건에 따라(subject to the following conditions)"라고 붙입니다.

**조건 1: 사용 정책이 라이선스의 일부입니다.**

> Licensee's use of the Software shall comply with the Usage Policy, which is hereby incorporated into this license and attached hereto as Exhibit A.

**조건 2: 표시 의무와 넓은 "파생물" 정의.**

> Licensee shall prominently display "Built with Muse Spark Open" in the user interface of each product or service that uses the Software or any Derivatives, or in the accompanying documentation, website, or settings menu. "Derivatives" means any AI model created, trained, modified (including fine-tuned), distilled, or otherwise improved using the Software or any outputs or results thereof.

**조건 3: 대형 MaaS 사업자는 별도 계약.**

> If the Licensee or any of its affiliates provide a third party with access to artificial intelligence models as a product or service, via API or a similar interface, where the third party receives outputs of such models ("Model as a Service"), and the aggregate gross revenue of the Licensee and its affiliates exceeds twenty (20) million US dollars (or the equivalent in other currencies) during any consecutive twelve (12) month period, the Licensee must notify Meta and enter into a separate written agreement with Meta before offering the Software or any Derivatives as part of that Model as a Service business.

같은 조항은 내부 사용, 연구, MaaS가 아닌 상업 활동, 그리고 자사 제품 기능의 구성요소로 쓰는 경우에는 이 조건이 적용되지 않는다고 명시합니다.

**사용 정책(Exhibit A)의 분야 제한.** 금지 목록에는 불법 행위, 괴롭힘 같은 일반 항목 외에 다음과 같은 **분야 단위** 제한이 들어 있습니다.

> Military, warfare, nuclear industries or applications, espionage, use for materials or activities that are subject to the International Traffic Arms Regulations (ITAR) ...

> Operation of critical infrastructure, transportation technologies, or heavy machinery

> Engage in the unauthorized or unlicensed practice of any profession including, but not limited to, financial, legal, medical/health, or related professional practices

또한 사용 정책은 "Muse Spark Open is not intended for individuals under the age of 18"이라고 적고, 사용 제한이나 안전장치를 의도적으로 우회·제거하는 행위도 금지합니다.

**OSI 정의와 비교하면.** OSI의 [오픈소스 정의(OSD)](https://opensource.org/osd) 6항은 "라이선스는 누구도 특정 활동 분야에서 프로그램을 쓰는 것을 제한해서는 안 된다(The license must not restrict anyone from making use of the program in a specific field of endeavor)"고 정합니다. 원자력 산업이나 중장비 운용 같은 분야 금지는 이 조항과 충돌하는 것으로 읽힙니다. AI 시스템에 대한 [OSI 오픈소스 AI 정의 1.0](https://opensource.org/ai/open-source-ai-definition)은 여기에 더해, 숙련자가 실질적으로 동등한 시스템을 만들 수 있을 만큼 상세한 **학습 데이터 정보**와 **학습 코드 전체**를 OSI 승인 조건으로 제공할 것을 요구합니다. 모델 카드의 학습 데이터 설명은 "공개 출처, 인터넷 크롤링, 제3자 구매, Meta 제품과 서비스에서 파생, 합성 데이터" 수준의 한 문단이고, 사전학습 코드나 데이터 목록은 공개되지 않았습니다. 따라서 Muse Spark Open은 가중치를 받을 수 있다는 의미의 **오픈웨이트**이지, OSI 기준의 오픈소스 AI는 아닙니다.

## 한계와 논란

- **과잉 거부.** 위 표의 FORTRESS ORS 17.4는 비교 모델 중 가장 높습니다. 독립 배포를 위해 강화한 안전 후학습이 정상 요청 거절로 이어질 수 있다는 신호로 보입니다.
- **안전 수치의 상당수가 자체 측정입니다.** StrongREJECT v2(0.5 대 타 모델 62.9~86.4)는 Meta 내부 벤치마크의 내부 실행 결과이고, 사이버 거부율 비교도 Meta의 시험 조건입니다. 발표문은 "전체 평가 보고서는 곧 공개"라고 했으며 2026-10-24 기준 예정 상태입니다.
- **미세조정 후 안전성은 보장되지 않습니다.** 모델 카드 스스로 하류 수정이 안전성을 떨어뜨릴 수 있다고 밝힙니다. TorchTitan, TRL, 관리형 API로 미세조정을 적극 지원하면서 동시에 안전성은 공개 체크포인트에만 해당한다는 구조입니다.
- **"오픈소스" 표현의 혼용.** PyTorch 블로그는 오픈소스라는 표현을 쓰지만 Meta 발표문과 모델 카드는 "open weights"와 "limited commercial terms"라고 씁니다. 같은 회사 자료 안에서도 용어가 엇갈립니다.
- **자료 간 수치 불일치.** 메모리 요구(700GB 대 530GB), 2비트 GGUF 구성(300GB 대 256GB), 파라미터 합계(816B 대 HF 메타데이터 약 822B)가 자료마다 다릅니다.

## 인사이트

**실무에 주는 의미: 합성 데이터에 쓰는 순간 라이선스가 따라옵니다.** 모델 카드는 활용 사례로 "하류 모델 개발을 위한 고품질 학습 데이터 생성"과 "LLM 심사자(LLM-as-a-judge)"를 명시합니다. 그런데 라이선스의 "파생물" 정의는 소프트웨어의 **출력이나 결과를 사용해** 학습하거나 증류한 모든 AI 모델을 포함합니다. 필자의 독해로는, 이 모델로 만든 합성 데이터로 자체 모델을 학습시키면 그 모델도 파생물이 되어 "Built with Muse Spark Open" 표시 의무와 사용 정책(분야 제한 포함)을 함께 지게 될 가능성이 큽니다. 같은 라이선스 4항은 "Meta는 출력물의 소유권을 주장하지 않는다"고 하지만, 출력물 소유권과 파생 모델에 대한 조건은 별개의 문제입니다. 사내 모델 학습 파이프라인에 이 모델을 교사(teacher) 모델로 넣으려는 팀이라면 법무 검토를 먼저 받는 것이 안전합니다. 또 하나, 2천만 달러 매출 조건은 "모델을 API로 제공하는 사업"에만 걸리므로, 자사 제품의 기능으로 쓰는 대부분의 기업은 해당하지 않지만 AI 플랫폼이나 모델 호스팅 회사는 정확히 그 대상입니다.

**왜 지금 중요한가: "단독 배포 전제 안전 후학습"이라는 기준.** 지금까지 오픈웨이트 모델의 안전성 논의는 주로 "공개해도 되는가"에 머물렀습니다. Muse Spark Open은 "가드레일 없는 환경에서 돌아갈 것을 전제로 모델 자체를 더 보수적으로 만든다"는 구체적인 설계 선택을 내놓았고, 그 결과를 같은 표 안에서 유해 응답 위험(ARS)과 과잉 거부(ORS)로 함께 보여 줬습니다. 필자의 판단으로는 이것이 이번 발표의 가장 정직한 부분입니다. 안전과 유용성이 교환 관계라는 것을 숫자로 드러냈기 때문입니다. 다만 미세조정 지원과 안전성 보장 범위 사이의 간극은 그대로 남습니다. 공개 후 몇 주 안에 안전 후학습을 걷어 낸 미세조정 버전이 나오는지가 이 접근법의 실효성을 가늠하는 첫 시험대가 될 것입니다. 사용 정책이 안전장치 제거를 금지하지만, 가중치가 배포된 뒤 이를 강제할 기술적 수단은 없습니다.

**블로그의 기존 글과의 연결.** [Reflection AI Beam 글](/tech/2026/10/20/reflection-beam.html)과 같은 날 소개하는 [Mistral Large 4](/tech/2026/10/24/mistral-large-4.html)가 이 모델 카드의 비교표에 함께 올라 있습니다. 다만 두 모델은 방법론 문서 기준 "가중치를 평가 시점에 널리 받을 수 없어" 자체 보고치만 인용됐으므로, 표의 빈칸과 숫자를 같은 조건의 비교로 읽으면 안 됩니다. 816B 총량과 42B 활성의 비대칭이 왜 "메모리는 크고 연산은 작은" 배포 특성을 만드는지는 [MoE 개념 글](/tech/2026/10/24/mixture-of-experts.html)과 함께 보면 이해가 쉽습니다. Mac Studio 두 대 구성이 가능한 것도 활성 파라미터가 작아 토큰당 읽어야 할 가중치가 적기 때문이라고 발표문은 설명합니다.

**한계와 반론.** "가장 유능한 미국산 오픈웨이트 모델"이라는 주장은 Meta 자체 표에서도 중국산 모델 둘(GLM 5.3, Kimi K3)이 종합 지수와 코딩 벤치마크에서 앞서는 상황에서 나온 것입니다. 국적이라는 범위를 빼면 이 모델의 강점은 에이전트 도구 사용, 멀티모달, 안전 지표로 좁혀집니다. 또 코딩 벤치마크 일부는 Meta 자체 하네스(Muse Code)로 측정됐고 경쟁 모델은 각자의 하네스를 썼으므로, 같은 날 소개하는 [Harness² 논문](/papers/2026/10/24/harness-squared.html)이 보여 준 것처럼 하네스 차이만으로도 점수가 크게 달라질 수 있다는 점을 감안해야 합니다.

**앞으로 지켜볼 점.** (1) 예고된 전체 안전 평가 보고서의 공개와, 외부 기관이 같은 체크포인트로 재현한 안전·과잉 거부 수치. (2) 공개 후 미세조정 파생 모델들에서 안전 후학습이 얼마나 유지되는지. (3) 파생물 조항과 분야 제한이 실제 기업 도입에서 어떻게 해석되는지, 특히 합성 데이터 용도에서의 관행. 세 번째가 정리되기 전까지는 연구와 내부 도구에서 먼저 써 보고, 제품이나 학습 파이프라인 투입은 라이선스 검토 뒤로 미루는 편이 안전해 보입니다.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [Introducing Muse Spark Open (Meta AI Research, 2026-10-15)](https://research.meta.ai/blog/muse-spark-open)
- [Muse Spark Is Now an Open-Weights Model (PyTorch 블로그, 2026-10-15)](https://pytorch.org/blog/muse-spark-open/)
- [Hugging Face 모델 카드 (gated)](https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B)
- [Muse Model License 원문 (LICENSE.md)](https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B/blob/main/LICENSE.md)
- [Build with Muse Spark Open (Meta 개발자 문서)](https://dev.meta.ai/resources/blog/build-with-muse-spark-open)
- [Muse Spark Open Evaluation Methodology (PDF)](https://research.meta.ai/static/muse-spark-open-evaluation-methodology)
- [Introducing Muse Code and Muse Spark 1.2 (Meta AI Research, 2026-08-05)](https://research.meta.ai/blog/introducing-muse-code-and-muse-spark-1-2)
- [The Open Source Definition (OSI)](https://opensource.org/osd)
- [The Open Source AI Definition 1.0 (OSI)](https://opensource.org/ai/open-source-ai-definition)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
