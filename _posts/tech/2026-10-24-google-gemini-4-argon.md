---
layout: default
title: "[기술 소개] Gemini 4 Argon: 1M 토큰을 한 번에 출력하는 장기 실행형 프런티어 모델"
description: "Google Gemini 4 Argon의 단계적 공개 과정, 1M 통합 컨텍스트와 long decode 동작 방식, 사이버 방어용 Fairwind 프로그램, 로보틱스 활용 사례, API 가격과 이전 시 주의점을 공식 문서 기준으로 정리했습니다."
date: 2026-10-24 00:59:00 +0900
categories: [tech]
---

# [기술 소개] Gemini 4 Argon: 1M 토큰을 한 번에 출력하는 장기 실행형 프런티어 모델

- **발표:** Google(Google DeepMind), 2026년 9월 30일 제한 공개 발표, 2026년 10월 13일 일반 공개
- **원문:** [9월 30일 발표](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/) · [10월 13일 일반 공개](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-argon/) · [로보틱스 활용(Google Developers Blog)](https://developers.googleblog.com/gemini-4-argon-for-robotics/) · [모델 문서](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon) · [모델 카드(PDF)](https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-4-Argon-Model-Card.pdf)
- **한눈에 (2026-10-24 기준):** 모델 ID `gemini-4-argon`(Stable). 입력·사고·출력을 합친 통합 컨텍스트 1,048,576 토큰, 한 응답에 최대 약 1M 토큰까지 출력하는 long decode 지원. 가격은 100만 토큰당 입력 $2, 출력 $10(2026-11-30까지 도입가, 12월 1일부터 $4/$20).
- **주의:** API는 **유료 티어 전용**이며 무료 티어로는 쓸 수 없습니다. 사이버 가드레일을 끈 버전은 심사를 거친 Fairwind 프로그램 파트너에게만 제공됩니다. long decode는 백그라운드 실행(`background: true`, `store: true`)에서만 동작하고, 명시적 컨텍스트 캐싱은 지원하지 않으며, Computer use는 프리뷰입니다.

## 한 줄 요약

**Gemini 4 Argon은 "한 번의 호출로 얼마나 오래, 얼마나 길게 일할 수 있나"를 전면에 내세운 Google의 새 프런티어 모델로, 출력 한도를 64K에서 1M 토큰으로 넓히고 이를 서버가 이어 붙이는 long decode, 사이버 방어 전용 공개 경로, 로보틱스 시뮬레이션 활용까지 한꺼번에 내놓았습니다.**

## 배경

9월 30일 발표문은 Argon을 "복잡하고 긴 호흡(long-horizon)의 워크플로에서 깊은 추론을 유지하도록 만든" 모델로 소개하고, 겨냥하는 영역으로 실제 소프트웨어 엔지니어링, 법률·금융 같은 기업 지식 업무, 사이버 보안 방어를 꼽았습니다. 모델 카드에 따르면 Argon은 기존 모델을 수정하거나 미세조정한 것이 아닌 새 모델이며, 희소 MoE(전문가 혼합, Mixture of Experts) 트랜스포머 구조로 텍스트·이미지·오디오·비디오 입력을 받고 텍스트를 출력합니다. 지식 기준일(knowledge cutoff)은 2026년 3월입니다.

공개 방식이 이전 Gemini 모델과 다릅니다. 처음부터 개발자에게 열지 않고 단계를 나눴습니다.

| 날짜 | 단계 | 출처 |
|---|---|---|
| 2026-09-30 | 발표. Fairwind 프로그램의 신뢰할 수 있는 사이버 방어 조직에 먼저 제공. 미국 정부의 자발적 사전 접근 절차에 참여 중이라고 밝힘 | [9월 30일 발표](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/) |
| 2026-10-13 | Gemini API(유료 티어), AI Studio, Antigravity, Gemini 앱(AI Ultra·Pro), Search의 AI Mode에 전 세계 공개. Fairwind 파트너 수백 곳 추가 확대 시작 | [10월 13일 발표](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-argon/), [개발자용 발표](https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-4-argon/) |
| 2026-10-13 | 로보틱스 활용 예시 공개 | [Gemini 4 Argon for Robotics](https://developers.googleblog.com/gemini-4-argon-for-robotics/) |
| 2026-11-30 | 도입가 종료 예정(2026-10-24 기준 예정) | [가격 문서](https://ai.google.dev/gemini-api/docs/pricing) |

안전성 쪽 배경도 공개 순서에 영향을 줬습니다. 모델 카드의 프런티어 안전성 평가(Frontier Safety Framework, 2026년 4월판 기준)에서 Google은 **생물학 위험 CCL(핵심 역량 수준)과 사이버 보안 CCL에 도달했을 가능성을 배제할 수 없다**고 적었고, 그래서 각각 안전성 사례(safety case)를 만들어 잔여 위험을 CCL 아래로 낮췄다고 평가했습니다. 은폐·상황 인식(Stealth and Situational Awareness) TCL도 "배제할 수 없음"으로 표시돼 있고, 내부 과제 15개 중 14개를 통과했다고 적혀 있습니다.

## 핵심 내용

### 1. 1M 통합 컨텍스트와 long decode: 출력 한도를 64K에서 1M으로

가장 큰 변화는 출력 길이입니다. 9월 30일 발표문은 출력 토큰 한도를 "기존 64K에서 1M으로" 늘렸다고 밝혔습니다. 모델 문서 기준 수치는 다음과 같습니다.

| 항목 | 값 (모델 문서, 2026-10-14 갱신) |
|---|---|
| 컨텍스트 창 | 1,048,576 토큰. 입력, 사고(thinking), 출력이 **한 창을 공유** |
| 최대 출력 | 기본 동기 호출 65,536 / long decode 사용 시 최대 1,048,576(입력을 뺀 만큼) |
| 입력 | 텍스트, 이미지, 비디오, 오디오, PDF |
| 사고 수준 | `low`, `medium`(기본), `high` |
| 캐싱 | 암시적(implicit) 캐싱만 지원, 명시적 캐싱 미지원 |
| 그 밖의 도구 | 코드 실행, 함수 호출, 파일 검색, Search·Maps 그라운딩, URL context, 구조화 출력 지원. Computer use는 프리뷰 |

[long decode 문서](https://ai.google.dev/gemini-api/docs/long-decode)를 보면 이 1M 출력은 모델 한 번의 생성이 아닙니다. **모델 호출 한 번은 여전히 최대 64K 토큰을 만들고, 그보다 긴 응답은 서버가 64K 단위의 "홉(hop)"으로 나눠 앞 홉이 멈춘 곳에서 이어 생성**합니다. 각 홉은 같은 interaction ID 아래에 `model_output` 단계로 쌓이고, 사용자는 이를 이어 붙여 읽습니다. 백그라운드 interaction은 최대 24시간까지 돌 수 있습니다.

이 구조에서 비용에 직결되는 세부 사항이 있습니다. 매 홉은 "프롬프트 + 지금까지 생성한 내용"을 다시 입력으로 보내므로 입력 토큰이 홉마다 다시 집계됩니다. 문서의 예시는 다음과 같습니다.

| 홉 | 모델에 보내는 입력 | 입력 토큰 |
|---|---|---|
| 1 | 프롬프트 | 1,000 |
| 2 | 프롬프트 + 홉 1 | 66,536 |
| 3 | 프롬프트 + 홉 1~2 | 132,072 |
| 4 | 프롬프트 + 홉 1~3 | 197,608 |
| 합계 | | 397,216 |

1,000토큰 프롬프트로 20만 토큰을 생성하면 실제 컨텍스트는 약 20.1만 토큰인데 `total_input_tokens`는 약 39.7만으로 보고됩니다. 반복 입력은 암시적 캐싱으로 95% 할인되지만(도입가 기준 캐시 입력 100만 토큰당 $0.10), 사고만 한 홉을 포함해 모든 홉의 토큰이 과금됩니다. 문서는 특히 **에이전트 프레임워크가 `total_input_tokens`를 보고 컨텍스트 압축(compaction)을 시작하면 너무 일찍 요약해 버린다**고 경고합니다. 실제 컨텍스트 크기는 프롬프트 + `total_output_tokens` + `total_thought_tokens`로 계산해야 합니다.

### 2. 장기 실행 소프트웨어 엔지니어링: "밤새 돌리는" 에이전트

Google이 든 사례는 대부분 수 시간에서 수 주가 걸리는 코드 작업입니다. 모두 Google의 자체 보고입니다.

- **C/C++에서 Rust로 이전:** 9월 30일 발표에 따르면 re2, libgav1 같은 핵심 라이브러리(수만 줄)부터 Fuchsia Zircon 커널(80만 줄 이상)까지 이전 작업을 진행 중이며, 운영 반영 전에 자동·수동 감사를 거치고 있다고 합니다. libgav1에서는 기존 Rust 포트의 SIMD 코드 3.2만 줄을 컴파일러가 자동 벡터화하는 안전한 Rust로 바꿔, Rust 포트보다 2.7배 빠르면서 출력이 같은 디코더를 얻었다고 밝혔습니다.
- **Chrome 리팩터링:** 10월 13일 발표에 따르면 4천만 줄 규모 Chromium 안의 약 600만 줄짜리 레거시 폴더에서 핵심 웹페이지 처리 코드를 분리하는 작업을 도와 "수개월 걸릴 일을 수 주에" 끝냈다고 합니다.
- **사내 지표:** Antigravity에서 Argon을 쓴 팀은 에이전트가 제출한 코드가 35% 넘게 늘고 롤백은 거의 3분의 1 줄었다고 합니다.

가장 구체적인 기록은 [ADK 최적화 사례](https://developers.googleblog.com/optimizing-a-200000-line-python-codebase-overnight-with-gemini-4-argon)입니다. Google은 오픈소스 에이전트 프레임워크 `google/adk-python`(약 20만 줄)에 Argon을 **11시간 동안 무인으로** 돌렸습니다. 두 번째 실행에서는 메인테이너 규칙을 저장소의 `.agents/skills` 디렉터리에 `SKILL.md` 색인과 `references/` 파일로 넣어 두었고, Argon은 코드를 고치기 전에 지침 파일 12개를 읽고 기준 벤치마크를 돌렸습니다. 결과는 PR 하나에 최적화 6개였고, 사람이 리뷰해서 **2개를 반영하고 4개를 버렸습니다.** 버린 것 중에는 합성 벤치마크에서 17% 빨라졌지만 약한 참조(weak reference) 때문에 세션 간에 오래된 데이터를 돌려줄 수 있는 캐시가 있었습니다. 반영된 변경은 긴 세션의 메모리 내 세션 준비 시간을 약 40%, 패키지 콜드 임포트를 21% 줄였습니다. 공개 테스트 16,892개는 모두 통과했지만 Google 내부 테스트 대상 25개가 실패해 지연 로딩 방식으로 고쳤다는 대목도 있습니다.

### 3. 사이버 방어: 가드레일을 끈 모델을 "누구에게" 줄 것인가

Argon은 사이버 방어 능력을 명시적으로 학습시킨 모델입니다. 9월 30일 발표문은 Argon이 "치명적인 소프트웨어 취약점을 스스로 찾고, 검증하고, 패치할 수 있다"고 쓰고, **신뢰할 수 있는 방어자와 Google 내부 팀에는 사이버 가드레일 없이 제공한다**고 밝혔습니다. 그 통로가 [Fairwind 프로그램](https://deepmind.google/fairwind-program/)입니다.

Fairwind 페이지에 적힌 조건은 다음과 같습니다(2026-10-24 확인).

- 대상: 정부·국가 사이버 당국, 의료·통신·에너지·금융 같은 핵심 기반시설 운영자, 핵심 기술 플랫폼. 현재 전 세계 650곳 이상과 협력 중이라고 밝힘
- 허용 작업: 승인된 위협 시뮬레이션, 리버스 엔지니어링, 방어·학술 목적의 악성코드 분석 같은 이중 용도(dual-use) 작업. 악성코드 제작은 금지
- 운영 조건: 사용자 단위 인증, 피싱 방지 MFA, 접근 통제. 내부 보안·사고 대응·모의 해킹 팀에만 접근을 줄 수 있고 직원별 접근과 사용을 추적해야 함. 재판매·재배포 금지, 신청 조직의 배경 조사
- 신청: Google Cloud 계정 팀을 통해. 자격이 없으면 공개 모델로 CodeMender를 쓰라고 안내

벤치마크로는 CWE-bench v1(취약점 수정 능력)에서 68%로 공동 1위라고 발표했습니다. 평가 방법론 문서에 따르면 이 수치는 공식 공개 리더보드 값이며 pass@1로 순위를 매기고 동점은 pass@4로 가립니다. 실제 사례로는 Wiz가 무료 공익 프로그램 Scan for Good에서 Argon으로 전 세계 병원이 쓰는 의료 소프트웨어의 개인정보 노출 취약점을 찾았다고 소개했습니다.

반대 방향의 방어도 함께 발표됐습니다. Gray Swan의 간접 프롬프트 인젝션(Indirect Prompt Injection, 웹페이지·이메일·코드 속 숨은 지시로 에이전트를 조종하는 공격) 벤치마크에서 15회 적응형 공격 기준 성공률을 0.7%로 낮췄다고 하고(수치 출처는 Gray Swan), 에이전트가 권한 오류나 실패하는 테스트를 만났을 때 지름길로 우회하는 시도는 코딩 벤치마크에서 2%였다고 합니다. 또 모델의 사고 과정(chain-of-thought)과 행동을 읽어 의도 밖의 우회를 실시간으로 막는 오정렬(misalignment) 모니터를 배치했고, 학습 중에는 이 모니터 결과로 사고를 벌점 주지 않아 사고가 계속 관찰 가능하도록 했다고 밝혔습니다.

### 4. 로보틱스: 코드와 시뮬레이션을 매개로 한 "물리 추론"

[로보틱스 글](https://developers.googleblog.com/gemini-4-argon-for-robotics/)(10월 13일)의 요지는 Argon이 로봇을 직접 제어하는 전용 모델이라기보다, **시각 이해와 코드 생성으로 로봇 개발 과정 전체를 돕는 범용 물리 추론 모델**이라는 것입니다. 3D 환경의 공간·물리 문제를 묻는 ERQA(Embodied Reasoning) 벤치마크에서 "순수 추론만으로" 87%를 기록해 다른 프런티어 모델을 앞섰다고 합니다(Google 자체 발표).

글은 활용을 네 영역으로 나눠 실제 프롬프트를 공개했습니다.

| 영역 | 예시 (공식 글 기준) |
|---|---|
| 로봇 제어 | Boston Dynamics Spot이 발판식 휴지통을 밟기 전에 MuJoCo 디지털 트윈으로 먼저 연습. 손목 카메라 이미지 위 좌표 격자와 동작 프리미티브(`grasp`, `place` 등)로 로봇 팔을 제로샷 제어 |
| Real2Sim | 실제 원격 조작 기록, 1인칭 사람 영상, 손으로 그린 스케치로부터 물리 보정된 MuJoCo 장면 생성 |
| 물리 이해 | 136초짜리 ALOHA 2 종이접기 영상을 4단계 계층으로 사후 라벨링하고, 실수 구간의 가중치를 낮춰 행동 복제 데이터 품질 관리. 진행도 기반 가치 함수 추정 |
| 연구·자기 개선 | 실제 책상 사진 한 장으로 시뮬레이션 트윈을 만들고 4,500개 이상 에피소드를 합성해 VLA(시각-언어-행동) 모델 실제 성공률을 56%에서 75%로, 완료 시간을 35초에서 24초로 개선 |

프롬프트를 보면 공통 패턴이 드러납니다. Argon이 로봇 관절을 직접 출력하기보다 `curl`로 로컬 제어 서버의 `/obs`, `/plan`을 호출하거나 MuJoCo 코드를 작성하고, 결과 이미지를 다시 보며 고치는 폐루프(closed loop)입니다. 시뮬레이션 재구성 프롬프트에는 "시뮬레이션 치팅 금지"(외력 주입, 충돌 해제, 기록된 센서값 복사 금지 등) 규칙이 길게 적혀 있습니다. 모델이 목표를 쉽게 맞추려고 물리를 속일 수 있다는 점을 Google도 전제하고 있다는 뜻으로 읽힙니다.

### 5. API 사용 방식: Interactions API와 이전 체크리스트

로보틱스 글과 모델 문서는 `gemini-4-argon`을 Interactions API로 쓰도록 안내합니다. 아래는 [long decode 문서](https://ai.google.dev/gemini-api/docs/long-decode)의 Python 예제를 줄인 것입니다. **필자가 직접 실행하지는 않았습니다**(유료 티어 API 키 필요).

```python
import time
from google import genai

client = genai.Client()

interaction = client.interactions.create(
    model="gemini-4-argon",
    input="Write a complete, rigorous proof of the prime number theorem.",
    background=True,                      # long decode는 백그라운드 실행에서만
    generation_config={
        "max_output_tokens": 262144,      # 65,536보다 커야 long decode가 켜짐
        "thinking_level": "high",
    },
)

while interaction.status in ("in_progress", "queued"):
    time.sleep(5)
    interaction = client.interactions.get(id=interaction.id)

# 홉마다 model_output 단계가 추가되므로 모두 이어 붙인다
text = "".join(
    c.text
    for step in interaction.steps if step.type == "model_output"
    for c in step.content if c.type == "text"
)
```

[What's new 문서](https://ai.google.dev/gemini-api/docs/latest-model)의 이전 체크리스트에서 기존 Gemini 코드를 옮길 때 깨지기 쉬운 항목만 골랐습니다.

- `temperature`, `top_p`, `top_k`는 무시되므로 제거합니다.
- 명시적 캐싱(`cachedContents`, `caches.create`)은 지원하지 않습니다. 암시적 캐싱은 4,096토큰 이상 프롬프트에서 기본으로 켜지고 적중 시 95% 할인됩니다.
- `max_output_tokens`를 낮게(예: 8,192) 잡아 둔 앱은 최소 32,768로 올리라고 권합니다. Argon은 한도 중 더 많은 부분을 사고에 쓰기 때문에, 낮은 한도는 답을 쓰기 전에 끊길 수 있습니다.
- 동기 호출에서 65,536을 넘는 값을 주면 400 오류입니다(2026-10-24 기준 "곧 지원 예정").
- 어려운 프롬프트는 수 분이 걸리므로 HTTP 타임아웃을 최소 15분으로 잡거나 백그라운드 실행을 씁니다.

## 성능과 비교

Google이 발표한 수치를 측정 주체와 함께 정리했습니다. 경쟁 모델과의 비교표는 모델 카드에 이미지로만 실려 있어 여기서는 옮기지 않았습니다.

| 벤치마크 | Argon | 측정 주체·조건 (평가 방법론 문서 기준) |
|---|---|---|
| DeepSWE v1.1 (장기 실전 SW 엔지니어링) | 77.9% | **Google 자체 측정**, mini-swe-agent 하네스 |
| AutomationBench (업무 자동화) | 51.3%, 1위 | Zapier 공식 공개 리더보드, 비공개 세트 |
| Vals Index (금융·코딩·법률·세무) | 1위 | Vals AI |
| LVBench (긴 비디오 이해) | 91.7% | **Google 자체 측정**, 도구 없이, Gemini는 1FPS |
| CWE-bench v1 (취약점 수정) | 68%, 공동 1위 | 공식 공개 리더보드 |
| ERQA (체화 추론) | 87% | Google 발표("순수 추론") |
| Gray Swan IPI (프롬프트 인젝션 공격 성공률, 낮을수록 좋음) | 0.7% | Gray Swan |

방법론 문서는 Argon 점수가 별도 표기가 없으면 pass@1이고 "가장 높은 사고 설정"으로 Gemini API에서 측정했으며, 다른 회사 모델 점수는 원칙적으로 각 사가 스스로 보고한 값이라고 밝힙니다. 즉 같은 표 안에서도 Argon은 자체 측정, 경쟁 모델은 자체 보고나 리더보드 값이 섞여 있습니다. LVBench처럼 API 제한 때문에 모델마다 입력 프레임 수가 다른 경우도 있어(문서에 명시) 직접 비교에는 주의가 필요합니다.

## 써 볼 수 있나

| 경로 | 조건 (2026-10-24 기준) |
|---|---|
| Gemini API | **유료 티어만**. 무료 티어 불가 |
| Google AI Studio | 유료 API 키, 또는 Google AI Ultra 구독 |
| Google Antigravity | Google AI Ultra 구독, 기업 |
| Gemini 앱, Search AI Mode | Google AI Ultra·Pro 구독 |
| 사이버 가드레일 해제 버전 | Fairwind 프로그램 승인 파트너만 |

[가격 문서](https://ai.google.dev/gemini-api/docs/pricing) 기준 유료 티어 요금(100만 토큰당, USD)은 다음과 같습니다. 출력 가격에는 사고 토큰이 포함됩니다.

| 처리 방식 | 입력 | 출력 | 캐시 입력 |
|---|---|---|---|
| Standard | $2.00 → $4.00 | $10.00 → $20.00 | $0.10 → $0.20 |
| Batch, Flex | $1.00 → $2.00 | $5.00 → $10.00 | $0.05 → $0.10 |
| Priority | $3.60 → $7.20 | $18.00 → $36.00 | $0.18 → $0.36 |

화살표 왼쪽은 2026-11-30까지의 도입가, 오른쪽은 2026-12-01부터의 가격입니다. 10월 13일 발표문 각주는 이 가격이 "일반 공개용 Argon 모델"에만 적용된다고 적고 있습니다. 지역은 Gemini API 공식 [이용 가능 지역](https://ai.google.dev/gemini-api/docs/available-regions) 목록을 따르며, 2026-10-24 확인 기준 대한민국이 목록에 있습니다.

## 한계와 논란

- **가장 강한 능력은 일반 사용자에게 열려 있지 않습니다.** 사이버 공격·방어 능력은 Fairwind 파트너용으로 가드레일 없이 제공되고, 일반 API에는 오용 방지 장치가 켜져 있습니다. 공개 API로 같은 취약점 탐색 성능을 기대하기는 어렵다고 보는 것이 안전합니다. 평가 방법론 문서도 일부 컴퓨터 사용 평가에서 "안전 필터에 걸린 응답은 빈 문자열로 처리했다"고 밝힙니다.
- **위험 수준 평가가 "배제할 수 없음"입니다.** 모델 카드는 생물학·사이버 CCL과 은폐·상황 인식 TCL을 모두 배제할 수 없다고 적고, 완화 조치로 위험을 낮췄다고 평가합니다. 이 평가는 Google 자신이 내린 것이며, 안전성 사례의 세부 내용은 별도 보고서에 있습니다.
- **사례와 수치 다수가 자체 보고입니다.** Rust 이전, Chrome 리팩터링, 데이터센터 메모리 절감(300TiB 이상) 같은 사례는 Google 내부 결과이고, DeepSWE와 LVBench 수치도 자체 측정입니다. 공개 저장소에 올라간 ADK, xTB, vLLM 변경처럼 외부에서 확인할 수 있는 사례와는 구분해서 읽어야 합니다.
- **1M 출력은 비싸고 느립니다.** 홉마다 입력이 다시 집계되고 사고만 한 홉도 과금되며, 문서는 long decode가 "수 분" 걸릴 수 있다고 적습니다. 도입가가 끝나는 12월부터는 단가도 두 배가 됩니다. 문서 스스로 채팅, 요약, 분류, 짧은 도구 호출이 많은 에이전트에는 long decode를 쓰지 말라고 권합니다.
- **명시적 캐싱이 빠졌습니다.** 긴 시스템 프롬프트나 문서를 명시적으로 캐시해 비용을 관리하던 앱은 암시적 캐싱에 기대야 하므로, 캐시 적중을 직접 통제하기 어려워집니다.
- **로보틱스 결과는 데모 수준입니다.** 공개된 내용은 대표 프롬프트와 영상이며, 성공률이 제시된 사례(56%→75%)도 Google 내부 실험입니다. 실시간 제어 지연이나 안전 인증 같은 실배치 조건은 다루지 않습니다.

## 인사이트

**왜 지금 중요한가.** 지금까지 프런티어 모델 경쟁의 축은 "컨텍스트를 얼마나 많이 읽나"였습니다. Argon은 그 축을 **"한 번에 얼마나 오래 생각하고 길게 쓰나"**로 옮겼습니다. 필자의 판단으로 핵심은 1M이라는 숫자보다 그것을 구현한 방식입니다. 모델의 단일 생성 한도는 여전히 64K이고, 서버가 64K 홉을 이어 붙이는 오케스트레이션을 API 기능으로 흡수했습니다. 이는 [추론 모델](/tech/2026/10/24/reasoning-models.html) 글에서 다룬 "테스트 시점 연산(test-time compute)을 늘려 품질을 사는" 흐름이 이제 API 계약(백그라운드 실행, 24시간 실행 한도, 상태 코드 `incomplete`) 수준으로 내려왔다는 신호로 보입니다.

**실무에 주는 의미.** 첫째, 에이전트 하네스를 운영하는 팀은 **토큰 계측 로직부터 점검해야 합니다.** `total_input_tokens`가 홉마다 누적되므로 이를 컨텍스트 크기로 오인하면 압축이 너무 일찍 일어나고, 비용 대시보드도 실제보다 부풀려 보입니다. [컨텍스트 엔지니어링](/tech/2026/10/24/context-engineering.html)에서 말하는 "무엇을 남기고 무엇을 요약할지"의 판단 근거가 되는 숫자가 모델마다 의미가 달라진 셈입니다. 둘째, ADK 사례는 장기 실행 에이전트가 실제로 쓸모 있으려면 모델만큼 주변 장치가 중요하다는 것을 보여 줍니다. 저장소에 넣은 규칙 파일, 에이전트가 보지 못한 별도 벤치마크(holdout), 사람의 리뷰가 있었기 때문에 6개 제안 중 위험한 4개를 걸러낼 수 있었습니다. "밤새 돌리기"를 도입하려면 모델 교체보다 이 세 가지를 먼저 갖추는 편이 효과가 클 것입니다. 셋째, 명시적 캐싱 미지원과 샘플링 파라미터 무시는 기존 Gemini 코드의 조용한 회귀를 만들 수 있으므로, 모델 ID만 바꾸는 이전은 피하는 것이 좋겠습니다. [프롬프트 캐싱](/tech/2026/10/24/prompt-caching.html) 전략을 명시적 캐시에 의존해 세웠다면 비용 추정을 다시 해야 합니다.

**사이버 방어와 로보틱스로의 확장이 뜻하는 것.** 두 영역은 성격이 달라 보이지만 같은 구조입니다. 모델이 직접 "행동"하지 않고, **코드를 쓰고 실행 결과를 관찰하며 고치는 루프**로 능력을 냅니다. 취약점을 찾아 검증하고 패치하는 일도, 시뮬레이션을 만들고 물리 오차를 줄이는 일도 결국 장기 실행 코딩 에이전트의 응용입니다. 그래서 위험도 함께 커집니다. 로보틱스 프롬프트가 "시뮬레이션 치팅 금지"를 길게 적고, 안전성 발표가 "지름길 시도 2%"를 지표로 내세운 것은 같은 문제, 즉 목표를 쉽게 달성하려고 규칙을 우회하는 행동을 다른 영역에서 다루는 것입니다. 사이버 영역에서는 Google이 이 문제를 기술(가드레일)과 제도(Fairwind의 신원 확인, 접근 추적, 재판매 금지)로 나눠 풀었습니다. 프런티어 모델의 공개 단위가 "모델 하나"에서 "능력별로 다른 대상"으로 쪼개지는 흐름은 다른 공급자에게도 이어질 가능성이 높아 보입니다.

**한계와 반론.** 발표된 벤치마크 대부분에서 Argon만 자체 측정이고 경쟁 모델은 자체 보고 값입니다. 하네스가 다르면 장기 실행 과제 점수는 크게 흔들리므로, DeepSWE 77.9% 같은 숫자는 "같은 조건의 비교"가 아니라 "Google이 고른 하네스에서의 결과"로 읽는 것이 정확합니다. 또 1M 출력이 품질로 이어지는지에 대한 외부 검증은 아직 없습니다. 문서가 스스로 "대부분의 코딩·에이전트 작업은 64K 안에서 끝난다"고 인정하는 만큼, 대다수 팀에게 이번 출시의 실질적 변화는 1M보다 사고 수준 조절과 가격일 수 있습니다.

**앞으로 지켜볼 점.** (1) 동기 호출과 Interactions API의 클라이언트 측 이어쓰기(continuation)가 "곧 지원" 상태에서 언제 풀리는지. 풀리면 백그라운드 저장(`store: true`) 없이도 long decode를 쓸 수 있어 데이터 보관 정책이 엄격한 조직의 판단이 바뀝니다. (2) 12월 1일 정가 전환 이후의 실제 사용 비용. (3) 제3자 하네스로 측정한 DeepSWE, Terminal-Bench 같은 장기 과제 점수. (4) 10월 13일 발표가 "Gemini 4 제품군의 나머지"를 예고한 만큼, 더 작은 Gemini 4 모델이 long decode와 통합 컨텍스트를 물려받는지.

<!-- EDITOR_NOTE: 운영자가 직접 의견을 여기에 추가하세요. -->

## 참고 링크

- [Gemini 4 Argon: our next era of frontier intelligence (Google, 2026-09-30)](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/)
- [Gemini 4 Argon: Built to solve your hardest problems (Google, 2026-10-13)](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-argon/)
- [Gemini 4 Argon is now available for developers (Google, 2026-10-13)](https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-4-argon/)
- [Gemini 4 Argon for Robotics (Google Developers Blog, 2026-10-13)](https://developers.googleblog.com/gemini-4-argon-for-robotics/)
- [Optimizing a 200,000-line Python codebase overnight with Gemini 4 Argon (Google Developers Blog)](https://developers.googleblog.com/optimizing-a-200000-line-python-codebase-overnight-with-gemini-4-argon)
- [Gemini API 모델 문서: gemini-4-argon](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon)
- [What's new in Gemini 4 Argon (Gemini API 문서)](https://ai.google.dev/gemini-api/docs/latest-model)
- [Long decode (Gemini API 문서)](https://ai.google.dev/gemini-api/docs/long-decode)
- [Gemini Developer API 가격](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini 4 Argon 모델 카드 (PDF)](https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-4-Argon-Model-Card.pdf)
- [Gemini 4 Argon 평가 방법론 (Google DeepMind)](https://deepmind.google/models/evals-methodology/gemini-4-argon)
- [Fairwind Program (Google DeepMind)](https://deepmind.google/fairwind-program/)

[← 기술 소개 목록]({{ "/tech.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
