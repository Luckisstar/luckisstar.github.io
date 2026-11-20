---
layout: default
title: "[오픈소스 소개] HyperFrames: HTML로 쓰고 MP4로 렌더링하는, 에이전트용 영상 프레임워크"
description: "HTML과 data 속성으로 영상을 정의하고 headless Chrome과 FFmpeg로 프레임 단위 렌더링하는 HyperFrames의 컴포지션 구조, 결정적 렌더링 규칙, 애니메이션 어댑터, CLI 예제, Remotion과의 차이를 정리했습니다."
date: 2026-10-29 07:09:00 +0900
categories: [opensource]
---

# [오픈소스 소개] HyperFrames: HTML로 쓰고 MP4로 렌더링하는, 에이전트용 영상 프레임워크

- **저장소:** [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) · [문서](https://hyperframes.heygen.com/introduction) · [Playground(hyperframes.studio)](https://hyperframes.studio/)
- **라이선스:** Apache 2.0 (프레임워크, CLI, 스킬). 프로젝트에 넣는 폰트, 음악, 영상은 각자의 라이선스를 따른다고 FAQ에 명시되어 있습니다.
- **언어:** TypeScript (Node.js 22 이상 필요, 렌더링에는 FFmpeg 필요)
- **현황 (2026-10-29 기준):** GitHub 스타 약 7.5만 개, 포크 약 6,800개, 열린 이슈 73개. 최신 릴리스 v0.8.214 (2026년 10월 28일). npm 패키지 `hyperframes`는 2026년 3월 23일 첫 배포 이후 567개 버전이 올라왔고, 최근 1주(2026-10-21~27) 다운로드는 약 104만 회입니다.
- **도입 전 확인할 점:** **아직 1.0 이전(0.x)이고 릴리스가 하루에도 여러 번 나옵니다(2026-10-28 하루에만 v0.8.210~v0.8.214 다섯 개).** 사용자 정의 애니메이션 연결 인터페이스(`FrameAdapter`)는 문서 스스로 “실험적 v0 API”라고 밝힙니다. **CLI는 익명 사용 통계(텔레메트리)를 기본으로 보내며**, 명령 이름과 렌더 성능 외에 OS·CPU·메모리 같은 환경 정보와 CLI를 실행한 코딩 에이전트의 이름(`claude_code`, `codex` 등)도 포함됩니다. `HYPERFRAMES_NO_TELEMETRY=1` 또는 `npx hyperframes telemetry disable`로 끌 수 있습니다. 로컬 렌더링은 계정 없이 무료지만, Studio 데스크톱 앱, 클라우드 렌더링, HeyGen 음성·아바타는 HeyGen 계정이 필요합니다.

## 한 줄 요약

**HyperFrames는 영상을 HTML 파일로 정의하면, 렌더러가 headless Chrome에서 프레임을 하나씩 “찾아가(seek)” 캡처하고 FFmpeg로 MP4를 만들어 주는 프레임워크입니다.** 영상 제작사 HeyGen이 공개했으며, 사람이 직접 쓰기보다 Claude Code, Codex, Cursor 같은 코딩 에이전트가 HTML을 쓰고 사람은 결과를 고치는 흐름을 전제로 설계되었습니다. 제품 소개 영상, PR 설명 영상, 데이터 시각화 애니메이션을 코드로 반복 생산하려는 개발자와 자동화 파이프라인에 맞는 도구입니다.

## 어떤 문제를 푸나

코드로 영상을 만들려고 하면 보통 두 가지 벽을 만납니다.

- **화면 녹화 방식은 결과가 매번 다릅니다.** 브라우저 애니메이션을 실시간으로 재생하며 녹화하면, 컴퓨터가 느린 순간 프레임이 빠지고 같은 입력에서도 결과가 달라집니다. CI에서 회귀 테스트를 하거나 수백 개 버전을 찍어 내기 어렵습니다.
- **기존 코드 기반 영상 도구는 전용 작성 모델을 요구합니다.** 대표 도구인 Remotion은 영상을 React 컴포넌트로 씁니다. React를 쓰는 팀에는 자연스럽지만, 이미 있는 HTML 페이지, 디자인 시안, GSAP 애니메이션을 영상으로 옮기려면 컴포넌트로 다시 써야 합니다.

HyperFrames는 이 둘을 **“영상 = HTML 파일, 시간 = data 속성, 렌더링 = 프레임별 seek”** 으로 풉니다. 공식 문서의 표현으로는 렌더링은 영상을 “재생”하지 않고, “90번째 프레임은 어떻게 생겼나?”를 한 장씩 묻습니다. 그래서 느린 기계에서도 프레임이 빠지지 않고, 같은 입력은 같은 프레임을 냅니다. 그리고 결과물이 빌드 단계 없는 평범한 `index.html`이라 브라우저에서 바로 열어 보고 개발자 도구로 살펴볼 수 있습니다.

README가 제시하는 활용 예는 제품 출시 영상, 애니메이션 코드 diff와 내레이션이 들어간 PR 설명 영상, 차트 레이스와 지도 애니메이션, 자막이 들어간 소셜 영상, 문서나 PDF를 설명 영상으로 바꾸기입니다. ADOPTERS.md에는 tldraw가 “GSAP로 애니메이션한 코드 diff, 내레이션, 자막이 들어간 PR 설명 영상 자동 생성”에 쓴다고 적혀 있습니다.

## 핵심 개념

| 개념 | 설명 |
|---|---|
| 컴포지션 | 영상 하나를 기술하는 HTML. 바깥 요소에 `data-composition-id`가 있어야 합니다. 최상위는 `index.html`이고, 다른 컴포지션을 안에 넣을 수 있습니다 |
| 클립 | 시간 속성을 가진 요소. `<video>`, `<img>`, `<audio>`, 그리고 중첩 컴포지션(`<div data-composition-id>`)이 클립이 됩니다 |
| 시간 속성 | `data-start`(시작 초), `data-duration`(길이), `data-track-index`(편집기 레인). 타이밍은 스크립트가 아니라 HTML이 정합니다 |
| 타임라인 | 움직임은 **멈춘(paused)** GSAP 타임라인 등에 쓰고 `window.__timelines["<컴포지션 id>"]`에 등록합니다. 렌더러가 이 타임라인을 프레임마다 seek합니다 |
| 프레임 어댑터 | “N번째 프레임에서 애니메이션 상태는?”에 답하는 연결부. GSAP, CSS, WAAPI, Lottie, Three.js, Anime.js 등이 내장되어 있습니다 |
| 변수 | `data-composition-variables`로 선언한 값. 렌더 시 `--variables`나 `--batch`로 바꿔 같은 컴포지션에서 여러 버전을 뽑습니다 |
| 스킬 | 코딩 에이전트에게 위 규칙을 가르치는 Agent Skills 묶음. 핵심 4종(`/hyperframes`, `/hyperframes-cli`, `/hyperframes-registry`, `/media-use`)과 필요 시 설치하는 3종이 있습니다 |

초보자가 헷갈리기 쉬운 규칙도 문서에 명시되어 있습니다.

- **트랙은 레이어가 아닙니다.** `data-track-index`는 브라우저 편집기에서 몇 번째 줄에 그릴지만 정하고, 렌더러는 읽지 않습니다. 앞뒤 순서는 CSS `z-index`로 정합니다.
- **`data-start`에 다른 클립 id를 쓰면 “그 클립이 끝날 때”라는 뜻입니다.** `data-start="intro + 0.5"`, `data-start="intro - 0.5"`처럼 간격이나 겹침을 줄 수 있습니다. 같은 컴포지션 안에서만 참조됩니다.
- **스크립트로 미디어를 재생·정지·seek하거나 시간에 따라 클립을 숨기면 안 됩니다.** 프레임워크가 data 속성으로 이미 하고 있어서 서로 충돌합니다.
- **중첩 컴포지션 파일 경로는 프로젝트 루트 기준입니다.** 한 단계 깊은 파일에서도 `../compositions/foo.html`이 아니라 `compositions/foo.html`로 씁니다.

## 동작 원리

README와 패키지 목록을 기준으로 정리하면 파이프라인은 다음과 같습니다.

```
 index.html (+ compositions/*.html, assets/)
        │
        ▼
 ┌──────────────────┐  parse, lint, timing compile
 │ @hyperframes/core│  data-* attributes, variables
 └────────┬─────────┘
          ▼
 ┌──────────────────┐  headless Chrome (Puppeteer)
 │ @hyperframes/    │  for frame in 0..N:
 │ engine           │    time = floor(frame) / fps
 │                  │    adapters seek to time
 │                  │    capture pixels
 └────────┬─────────┘
          ▼
 ┌──────────────────┐  FFmpeg encode
 │ @hyperframes/    │  + audio mix from <audio>/<video>
 │ producer         │  → MP4 / WebM / MOV / GIF / PNG / HLS
 └──────────────────┘
```

공식 “Deterministic Rendering” 문서가 설명하는 프레임 하나의 처리 순서는 네 단계입니다.

1. **프레임 시계:** 엔진이 `time = floor(frame) / fps`를 정수 연산으로 계산합니다. 실제 시계는 보지 않습니다.
2. **Seek:** 프레임 어댑터가 `seekFrame(frame)`을 받아 모든 애니메이션, DOM 변화, 캔버스 그리기를 그 시점으로 옮깁니다. GSAP 타임라인은 재생되지 않고 멈춘 채로 seek만 됩니다.
3. **캡처:** Chrome의 `HeadlessExperimental.beginFrame`으로 픽셀을 한 번에 가져옵니다. 문서는 이것으로 “반쯤 그려진 프레임”이 없다고 설명합니다.
4. **인코딩:** FFmpeg가 프레임을 MP4로 묶고 `<audio>`, `<video>`의 소리를 섞습니다.

이 구조 때문에 컴포지션 작성자가 지켜야 할 규칙이 생깁니다. 문서가 꼽는 규칙은 **벽시계 금지(`Date.now()`, `requestAnimationFrame`, 타이머), 시드 없는 난수 금지, 렌더 도중 fetch 금지, 해상도와 fps 고정, 유한한 길이**입니다. 프레임마다 “이전 프레임에서 이어서” 계산하는 코드는 깨지고, 움직임은 반드시 시간만의 함수여야 합니다.

### 프레임 어댑터

코어 패키지의 런타임 어댑터 디렉터리(`packages/core/src/runtime/adapters`)에는 GSAP, CSS, WAAPI, Anime.js, Lottie, Three.js, TypeGPU, D3, Leaflet, Mapbox, MapLibre, Google Maps용 어댑터가 들어 있습니다. 라이브러리별 연결 방법은 스킬 참고 문서(`runtimes.md`)에 표로 정리되어 있습니다.

| 런타임 | HyperFrames가 다루는 방식 |
|---|---|
| GSAP | 멈춘 타임라인을 `window.__timelines`에 등록 |
| CSS `@keyframes` | 자동 탐지. 반복 횟수는 유한하게, `animation-fill-mode: both`, 요소에 `data-start` |
| WAAPI | `element.animate(…, { fill: "both" })` 후 `pause()` |
| Lottie | `autoplay: false`, `loop` 명시, 인스턴스를 `window.__hfLottie`에 push |
| Anime.js v4 | `autoplay: false`, `window.__hfAnime`에 push, 시드 난수 사용 |
| Three.js·캔버스 | `hf-seek` 이벤트의 `e.detail.time`으로 그리기, 루트에 `data-duration` |

직접 어댑터를 만들 때의 계약도 명시되어 있습니다. 유한한 프레임 수를 돌려줄 것, 앞으로·뒤로·임의 순서 seek를 모두 지원할 것, 같은 프레임에는 같은 상태를 낼 것, 프레임이 캡처되기 전에 비동기 작업을 끝낼 것, `destroy()`에서 자원을 정리할 것입니다.

### 재현성의 범위

“같은 입력, 같은 출력”에는 단서가 붙습니다. 엔진 문서는 **프레임 스케줄은 반복 가능하지만, 정확한 픽셀은 Chrome 버전, 폰트, 코덱, GPU, 호스트 환경에 따라 달라질 수 있다**고 적고 있습니다. 그래서 정확한 재현이 필요하면 Chromium 버전, 폰트 세트, FFmpeg 인코더를 고정하는 `--docker` 렌더를 권장합니다.

## 주요 기능

### CLI: 만들기부터 렌더링까지

`hyperframes` CLI 하나가 전 과정을 맡습니다. 공식 CLI 문서에 있는 주요 명령은 다음과 같습니다.

- `init`: 예제에서 프로젝트를 만듭니다. `--video`나 `--audio`를 주면 Whisper로 받아 적어 자막을 넣고, 새 프로젝트마다 에이전트용 `AGENTS.md`와 같은 내용의 `CLAUDE.md`를 만듭니다.
- `preview`: 핫 리로드되는 미리보기 서버와 브라우저 편집기를 띄웁니다(기본 포트 3002).
- `lint`: 브라우저 없이 HTML만 읽어 흔한 실수를 찾습니다. 예: GSAP를 쓰는데 스크립트가 없음(`missing_gsap_script`), `<video>`에 `muted`도 `data-has-audio`도 없음.
- `check`: 실제 브라우저에서 여러 시점을 샘플링해 런타임 오류, 넘침·잘림 같은 레이아웃 결함, WCAG AA 대비, 오디오 문제를 한 번에 검사합니다.
- `snapshot`: 전체 렌더 없이 특정 시점의 PNG만 찍습니다. 에이전트가 만든 결과를 눈으로 확인하는 용도입니다.
- `render`: MP4, MOV(ProRes), WebM(투명), GIF, PNG 시퀀스, HLS로 출력합니다.
- `capture`: 실제 웹사이트의 스크린샷, 에셋, 폰트를 작업 폴더로 가져와 에이전트가 참고하게 합니다.
- `doctor`: Node.js, FFmpeg, Chrome, Docker, 디스크 등 렌더에 필요한 환경을 점검합니다.

대부분 명령이 `--json`을 받고 기본적으로 비대화형이라, 에이전트나 CI가 결과를 기계적으로 읽기 쉽습니다. 이것이 README가 말하는 “agent-friendly”의 실체로 보입니다.

### 에이전트 스킬과 카탈로그

스킬은 일반적인 웹 지식에는 없는 HyperFrames 규칙(멈춘 타임라인 등록, 벽시계 금지 등)을 에이전트에게 가르칩니다. README 기준으로 `/hyperframes-registry` 스킬이 다루는 카탈로그에는 전환 효과, 오버레이, 타이틀, 자막, 차트, 지도, 3D 등 약 450개 블록과 컴포넌트가 있고, `npx hyperframes add data-chart`처럼 편집 가능한 소스로 설치됩니다.

### 렌더링 경로

같은 프로젝트를 여러 곳에서 렌더링할 수 있습니다. 로컬 CLI, Node 애플리케이션용 `@hyperframes/producer`, 저수준 캡처용 `@hyperframes/engine`, HeyGen이 운영하는 클라우드(`hyperframes cloud render`, HeyGen 크레딧 차감), 자기 계정에 배포하는 AWS Lambda와 Google Cloud Run입니다.

### 그 밖의 기능

- **변수와 일괄 렌더링:** 같은 컴포지션에 다른 텍스트·색을 넣어 여러 파일을 뽑습니다(예제 2).
- **투명 영상:** WebM(VP9 알파)과 MOV(ProRes 4444)로 다른 편집 도구에 얹을 오버레이를 만듭니다.
- **Studio:** 미리보기와 편집을 하는 브라우저 편집기, 그리고 에이전트 채팅까지 한 창에 묶은 데스크톱 앱(Mac, Windows 64비트, Linux)이 있습니다. 데스크톱 앱은 HeyGen 계정 로그인이 필요합니다.
- **오디오:** HeyGen 계정이 있으면 HeyGen 음성과 음악 카탈로그를, 없으면 로컬 Kokoro TTS와 번들된 효과음을 씁니다(FAQ 기준).

## 설치와 시작

README와 공식 Quickstart에 있는 방법만 옮깁니다. 요구 사항은 **Node.js 22 이상과 FFmpeg**입니다.

### 코딩 에이전트로 시작하기

Claude Code는 플러그인으로 설치합니다.

```bash
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes
```

다른 에이전트(Codex, Cursor, Gemini CLI, OpenCode 등)는 독립 스킬로 설치합니다. 대화형 선택 화면에서는 **Core Skills**만 고르면 됩니다.

```bash
npx skills add heygen-com/hyperframes
```

에이전트나 CI처럼 비대화형으로 설치할 때는 README가 다음 명령을 권합니다. 핵심 4종만 정확히 설치합니다.

```bash
npx hyperframes skills update
```

그다음 에이전트에게 README의 예시처럼 요청합니다.

```text
Using /hyperframes, create a 10-second product intro with a fade-in title,
a background video, and subtle background music.
```

### CLI로 직접 시작하기

```bash
npx hyperframes init my-video
cd my-video
npx hyperframes preview      # 브라우저 미리보기 (라이브 리로드)
npx hyperframes render       # MP4로 렌더링
```

`--output`을 생략하면 결과는 `renders/` 아래에 저장됩니다. 텔레메트리를 끄고 쓰려면 셸에 `HYPERFRAMES_NO_TELEMETRY=1`을 설정해 두면 됩니다.

## 실전 예제

> 아래 예제는 모두 공식 문서와 README의 예제를 바탕으로 했습니다. **이 글을 쓴 환경에서는 외부 패키지 실행이 허용되지 않아 직접 렌더링해 보지 못했습니다.** 플래그와 속성 이름은 2026-10-29 기준 저장소 문서(v0.8.214)와 대조했습니다.

### 예제 1. 3초짜리 타이틀 카드

제목이 0.5초 동안 나타났다가 2초 유지되고 0.5초 동안 사라지는 가장 작은 컴포지션입니다. 공식 “HyperFrames vs Remotion” 가이드의 예제입니다.

```html
<style>
  #stage { position: relative; width: 1280px; height: 720px; overflow: hidden; background: #0a0a0a; }
  .clip  { position: absolute; inset: 0; display: grid; place-items: center; }
  #title { font-size: 160px; font-weight: 800; color: #fff; opacity: 0; }
</style>

<div id="stage" data-composition-id="title-card" data-start="0"
     data-width="1280" data-height="720" data-duration="3" data-fps="30">
  <div id="card" class="clip" data-start="0" data-duration="3" data-track-index="0">
    <div id="title">HELLO</div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
  const tl = gsap.timeline({ paused: true });
  tl.to("#title", { opacity: 1, duration: 0.5, ease: "none" }, 0);
  tl.to("#title", { opacity: 1, duration: 2.0, ease: "none" }, 0.5);
  tl.to("#title", { opacity: 0, duration: 0.5, ease: "none" }, 2.5);

  window.__timelines = window.__timelines || {};
  window.__timelines["title-card"] = tl;
</script>
```

가이드가 강조하는 세 규칙은 이렇습니다. 보이는 요소는 `class="clip"`과 id, `data-start`, `data-duration`을 가질 것, 타임라인은 **멈춘 상태로** 만들 것, `window.__timelines`에 루트와 **같은 id**로 등록할 것입니다. 마지막을 빠뜨리면 움직임 없는 정지 화면이 나옵니다. 반대로 타임라인이 아예 없는 컴포지션은 루트에 `data-no-timeline`을 붙여야 합니다. 그렇지 않으면 렌더러가 타임라인을 기다리느라 매 렌더마다 기본 45초를 허비한다고 트러블슈팅 문서가 설명합니다.

### 예제 2. 고객사별 영상 여러 개를 한 번에 뽑기

같은 컴포지션에 이름과 제목만 바꿔 여러 파일을 만드는 경우입니다. 먼저 루트에 변수를 선언하고 스크립트에서 읽습니다(CLI 문서 예제).

```html
<html
  data-composition-variables='[
    {"id":"title","label":"Title","type":"string","default":"Hello"},
    {"id":"theme","label":"Theme","type":"enum","options":[
      {"value":"light","label":"Light"},
      {"value":"dark","label":"Dark"}
    ],"default":"light"}
  ]'
>
  <script>
    const vars = window.__hyperframes.getVariables();
    document.getElementById("hero").textContent = vars.title;
    document.body.dataset.theme = vars.theme;
  </script>
</html>
```

한 개만 바꿔 렌더링할 때는 `--variables`, 여러 개일 때는 행마다 변수 객체가 하나씩 든 JSON 배열을 `--batch`로 넘깁니다. 출력 파일 이름에 행의 값을 자리표시자로 쓸 수 있습니다.

```bash
npx hyperframes render --variables '{"title":"Q4 Report","theme":"dark"}' --output q4.mp4
```

```json
[
  { "name": "acme", "title": "Acme Pro" },
  { "name": "northstar", "title": "Northstar Pro" }
]
```

```bash
npx hyperframes render \
  --batch rows.json \
  --strict-variables \
  --output "renders/{name}.mp4"
```

`--strict-variables`는 선언되지 않았거나 타입이 틀린 값을 경고가 아닌 오류로 만듭니다. 주의할 점은 **변수로 바꿀 수 없는 것**입니다. 화면 크기, 루트 컴포지션의 전체 길이, 프레임 속도, 출력 형식은 스크립트가 돌기 전에 정해지므로 변수로 바꿔도 반영되지 않습니다. 문서는 일괄 렌더링의 동시 실행 수(`--batch-concurrency`, 기본 1)를 한 번 안정적으로 렌더링된 뒤에 늘리라고 권합니다.

### 예제 3. Three.js나 캔버스 그림을 영상에 넣기

라이브러리 고유의 `requestAnimationFrame` 루프는 쓸 수 없습니다. 대신 HyperFrames가 프레임마다 보내는 `hf-seek` 이벤트에서 시간 값만 받아 그 시점의 장면을 그립니다. 스킬 참고 문서(`runtimes.md`)의 seek 프로토콜 예제입니다.

```html
<script>
  function renderAt(t) {
    /* t초 시점의 장면을 t만으로 계산해 그린다 */
  }
  window.addEventListener("hf-seek", (e) => {
    renderAt(e.detail.time);
    // GPU 제출, 이미지 디코딩 같은 비동기 작업은
    // e.detail.waitUntil(promise)를 동기적으로 호출해 알린다
  });
  renderAt(0);
</script>
```

이 방식에서는 루트에 `data-duration`을 꼭 지정합니다. 큰 메시나 셰이더 컴파일처럼 준비가 오래 걸리는 작업은 `window.__hf.buildReady["<key>"]` 프로미스로 등록해 첫 프레임 캡처를 늦추라고 문서는 안내합니다. 기존 Three.js 코드를 옮길 때 가장 손이 많이 가는 부분은 “직전 프레임 상태에 조금씩 더하는” 물리·파티클 코드를 시간의 함수로 바꾸는 일일 것으로 보입니다.

### 예제 4. CI에서 검사하고 고정된 환경으로 렌더링하기

PR마다 영상을 다시 만들거나 영상 회귀 테스트를 한다면, 렌더링 가이드가 제시하는 순서대로 `lint`(정적 검사) → `check`(브라우저 검사) → `render`를 돌립니다. 기계마다 폰트와 Chrome 버전이 달라 픽셀이 미세하게 바뀌는 것을 막으려면 `--docker`를 씁니다.

```bash
npx hyperframes lint --json
npx hyperframes check --strict
npx hyperframes render --docker --output final.mp4
```

`check --strict`는 경고도 실패로 처리합니다. 문서에 따르면 Docker 렌더는 시작 비용이 있어 모든 최종 렌더에 필요한 것은 아니고, CI나 반복 가능한 운영 환경에서 쓰는 선택지입니다. 검토용으로 빠르게 볼 때는 `--quality draft`가 있습니다.

### 예제 5. 다른 편집 도구에 얹을 투명 자막 오버레이

자막이나 하단 자막바만 렌더링해 Premiere나 DaVinci Resolve 같은 편집 도구 위에 얹을 때는 투명 출력을 씁니다.

```bash
# 웹용 투명 오버레이 (VP9 + 알파)
npx hyperframes render --format webm --output overlay.webm

# 편집용 ProRes 4444 (알파 포함)
npx hyperframes render --format mov --output overlay.mov
```

투명하게 남길 영역에는 `html`, `body`, 전체 화면 배경을 칠하지 않아야 합니다. 렌더링 가이드는 결과를 확인할 때 알파 뒤를 항상 검게 보여 주는 플레이어를 믿지 말고, VP9 WebM은 알파를 아는 디코더를 명시해 프레임을 뽑아 보라고 권합니다.

```bash
ffmpeg -c:v libvpx-vp9 -i overlay.webm -frames:v 1 -pix_fmt rgba overlay-frame.png
```

MOV에서 `--prores-profile hq` 같은 4:2:2 프로파일을 고르면 알파가 없어져 투명 영역이 검게 나옵니다.

## 실무 팁 & 자주 겪는 문제

공식 트러블슈팅(Help), FAQ, 이슈 트래커(2026-10-29 기준 열린 이슈 목록)를 바탕으로 정리했습니다.

- **움직임이 없다:** 타임라인이 `paused: true`로 만들어졌는지, `window.__timelines`의 키가 `data-composition-id`와 정확히 같은지 먼저 봅니다.
- **렌더가 늘 45초쯤 더 걸린다:** 타임라인을 등록하지 않는 컴포지션인데 `data-no-timeline`이 빠진 경우입니다. `lint`가 `missing_data_no_timeline`으로 알려 줍니다.
- **GSAP 타임라인을 비동기 콜백 안에서 만들 때:** `document.fonts.ready.then(…)` 안에서 만들어도 되지만 **등록은 마지막에** 해야 합니다. 먼저 등록하면 빈 화면이 렌더링됩니다.
- **미리보기는 끊기는데 렌더는 괜찮다:** 정상입니다. 미리보기는 실시간 재생이라 하드웨어 영향을 받고, 렌더는 프레임별 seek라 느려도 프레임이 빠지지 않습니다.
- **미리보기와 렌더 결과가 다르다:** 폰트, 원격 미디어, 브라우저별 효과를 확인하고, 필요하면 `--docker`로 환경을 고정합니다. 프로젝트에 선언하지 않은 폰트는 렌더에서 기본 글꼴로 바뀔 수 있어 `@font-face`로 직접 선언해야 합니다.
- **영상 자르기 속성의 함정:** HTML 스키마 문서는 `data-media-start`와 `data-playback-start`를 읽는 구성 요소가 서로 다르다고 밝힙니다. 오디오 믹서는 `data-media-start`만 읽기 때문에, `<video>`에 `data-playback-start`만 쓰면 **화면은 잘렸는데 소리는 잘리지 않은** 결과가 나옵니다. `<video>`와 `<audio>`에는 `data-media-start`를 씁니다.
- **WSL2에서 느리다:** Chrome이 GPU에 닿지 못할 수 있다고 문서에 별도 항목이 있고, 열린 이슈에도 WSL2에서 렌더·check·snapshot마다 10초씩 기다리는 문제가 올라와 있습니다.
- **원격 미디어:** 이슈 트래커에 “원격 미디어 fetch가 실패하면 렌더에서 조용히 빠진다”는 버그가 열려 있습니다(2026-10-29 기준). 결정성 규칙상으로도 미디어는 프로젝트 안에 두는 편이 안전합니다.
- **macOS:** “XProtect가 렌더를 ‘악성 스크립트’로 막는다”는 보고가 아직 분류 전 상태로 열려 있습니다.

## 비슷한 도구와 비교

| 항목 | HyperFrames | Remotion | 화면 녹화 방식 |
|---|---|---|---|
| 작성 방식 | HTML, CSS, JS + data 속성 | React 컴포넌트(TypeScript) | 아무 웹 페이지 |
| 빌드 단계 | 없음(`index.html` 그대로) | 번들러 필요 | 없음 |
| 시간 제어 | 렌더러가 애니메이션을 멈추고 프레임마다 seek | 코드가 현재 프레임 번호를 읽어 값을 계산 | 실시간 재생을 녹화 |
| 결정성 | 규칙을 지키면 프레임 단위로 동일 | 프레임 번호의 순수 함수로 작성 | 기계 부하에 따라 프레임 손실 |
| 분산 렌더링 | AWS Lambda, Cloud Run, HeyGen 클라우드 | Remotion Lambda(성숙한 클라우드 렌더러) | 해당 없음 |
| 라이선스 | Apache 2.0 | 자체 라이선스(개인과 3인 이하 회사 무료, 4인 이상 유료) | 도구마다 다름 |

Remotion 열의 작성 방식, 시간 제어, Lambda 성숙도는 **HyperFrames 공식 비교 가이드의 설명 기준**이며, 라이선스는 [Remotion 공식 라이선스 페이지](https://www.remotion.pro/license)에서 확인했습니다(2026-10-29 기준: 개인과 3인 이하 회사는 무료, 4인 이상 회사나 협업은 Company License 필요). 화면 녹화 방식 열은 일반적으로 알려진 특징 기준입니다.

HyperFrames 비교 가이드에는 Claude Code에 같은 15초 출시 영상 요청을 한 번씩 맡긴 결과도 실려 있습니다. Remotion은 12분 30초, TypeScript 파일 10개(1,037줄), `node_modules` 약 950MB였고, HyperFrames는 11분 50초, HTML 파일 4개(822줄), 설치된 패키지 없음이었다고 합니다. **HeyGen이 직접 한 번씩만 돌린 측정**이라 가이드 스스로도 “한 번의 실행으로는 품질을 판단할 수 없다”고 적고 있습니다. 같은 가이드가 “Remotion이 더 잘하는 점”으로 더 긴 운영 이력, 더 많은 템플릿과 자료, 성숙한 Lambda, React 팀에 자연스러운 모델, 그리고 “프레임 번호의 순수 함수라 머릿속에 담기 더 쉽다”는 점을 인정하는 것은 눈여겨볼 만합니다.

## 장점과 한계

### 장점

- **기존 웹 자산을 거의 그대로 씁니다.** HTML 페이지, 디자인 시안, GSAP·Lottie 애니메이션을 컴포넌트로 다시 쓰지 않고 컴포지션으로 옮길 수 있습니다.
- **결정적 렌더링:** 프레임별 seek 구조라 느린 기계에서도 프레임이 빠지지 않고, Docker로 환경까지 고정하면 CI 회귀 테스트에 쓸 수 있습니다.
- **에이전트 친화적 CLI:** 비대화형 기본값, `--json` 출력, `lint`·`check`·`snapshot`으로 이어지는 검증 루프가 에이전트가 스스로 결과를 확인하게 돕습니다.
- **Apache 2.0:** 렌더당 비용이나 상업 사용 인원 제한이 없습니다.
- **출력 형식이 넓습니다:** MP4, 투명 WebM·MOV, GIF, PNG 시퀀스, HLS를 한 CLI에서 냅니다.

### 한계

- **규칙을 어기면 조용히 깨집니다.** 비교 가이드 스스로 “규칙(멈춘 타임라인, 벽시계 금지, 시드 없는 난수 금지)을 따르지 않으면 조용히 깨진다”고 인정합니다. `lint`와 `check`가 많은 경우를 잡지만, 시간 대신 직전 상태에 의존하는 코드는 사람이 봐야 합니다.
- **1.0 이전의 빠른 변화:** 하루 여러 번 릴리스가 나오고, `FrameAdapter`는 실험 API입니다. 운영 파이프라인에 넣으면 버전을 고정하고 올릴 때마다 회귀 확인이 필요합니다.
- **무거운 런타임 의존성:** Node.js 22, FFmpeg, Chrome이 필요하고, 렌더 시간은 브라우저 렌더링 비용을 그대로 따릅니다. FAQ의 측정 예(1920×1080, 300프레임에 9.8초, 비싼 CSS 선언 하나를 남기면 25초)는 측정 기계가 명시되어 있지 않습니다.
- **HeyGen 생태계와의 경계:** 프레임워크는 오픈소스지만 Studio 데스크톱 앱, 클라우드 렌더링, 음성·아바타는 HeyGen 계정과 크레딧으로 이어집니다. 텔레메트리도 기본으로 켜져 있습니다.
- **알려진 버그:** 원격 미디어 누락, 2GiB를 넘는 내보내기 파일, WSL2 지연 같은 문제가 열린 이슈로 남아 있습니다(2026-10-29 기준).

## 인사이트

**왜 지금 중요한가: 영상이 “에이전트가 생성하는 산출물” 목록에 들어오고 있습니다.** 코딩 에이전트는 이미 코드, 문서, 다이어그램을 만듭니다. 영상은 그동안 타임라인 편집기라는 GUI에 묶여 있어 에이전트가 손대기 어려웠는데, HyperFrames는 영상을 에이전트가 가장 잘 쓰는 형식(HTML)으로 바꿔 이 벽을 낮춥니다. 핵심은 렌더링 엔진 자체보다 **“형식은 에이전트가 이미 아는 것으로, 규칙은 스킬로 가르친다”** 는 설계 방향입니다. 이는 [D2 소개 글](/opensource/2026/10/20/d2.html)에서 본 “다이어그램을 텍스트로 정의하고 배치는 엔진에 맡긴다”는 흐름의 영상판이라고 볼 수 있고, 결과물이 텍스트라 Git diff와 PR 리뷰가 가능하다는 장점도 같습니다. npm 주간 다운로드가 약 104만 회(2026-10-21~27)라는 수치는 개발자가 직접 설치한 수뿐 아니라 에이전트와 CI가 `npx`로 반복 실행한 횟수가 섞여 있을 것으로 보여, 실제 사용자 규모로 읽을 때는 주의가 필요합니다.

**기존 글과의 연결: HyperFrames는 “Puppeteer 위에 만든 영상 전용 런타임”입니다.** 엔진 패키지는 실제로 Puppeteer에 의존합니다. [Puppeteer 소개 글](/opensource/2026/10/20/puppeteer.html)에서 다룬 스크린샷과 PDF 생성은 “지금 이 순간의 화면”을 찍는 일이었습니다. HyperFrames가 그 위에 더한 것은 시간 축입니다. 페이지의 모든 애니메이션 라이브러리를 멈추고 같은 시계로 seek하게 만드는 어댑터 계층이 이 프로젝트의 진짜 기술적 가치로 보입니다. 직접 Puppeteer로 스크린샷을 이어 붙여 영상을 만들던 팀이라면, 그 과정에서 겪던 프레임 누락과 애니메이션 동기화 문제를 이 계층이 대신 풀어 준다고 이해하면 됩니다. 또 스킬 배포 방식(플러그인, `npx skills add`, 핵심 세트와 필요 시 설치)은 [Agent Skills 표준 글](/tech/2026/10/24/agent-skills-aaif.html)에서 다룬 스킬 생태계가 실제 제품에서 쓰이는 사례입니다.

**한계와 반론: “결정적”이라는 말의 범위를 정확히 읽어야 합니다.** README는 “same input, same frames, same output”이라고 하지만, 엔진 문서는 픽셀이 Chrome, 폰트, 코덱, GPU에 따라 달라질 수 있다고 따로 적습니다. 즉 보장되는 것은 **프레임 스케줄의 결정성**이고, 픽셀 단위 동일성은 Docker로 환경을 고정했을 때의 이야기입니다. 그리고 이 결정성은 작성자가 규칙을 지킨다는 전제 위에 있습니다. 에이전트가 쓴 코드에 `Math.random()`이나 `Date.now()`가 하나 섞이면 렌더마다 결과가 달라지는데, 이것을 사람이 모든 프레임을 보며 찾기는 어렵습니다. 필자의 판단으로는 HyperFrames를 CI에 넣을 때 가장 먼저 할 일은 같은 커밋을 두 번 렌더링해 결과를 비교하는 단계를 파이프라인에 추가하는 것입니다. 또 Remotion 비교는 경쟁 제품을 만드는 쪽이 쓴 자료입니다. 단점도 인정하는 공정한 편이지만, 시간 측정은 한 번씩 돌린 결과이므로 도입 근거로 삼기보다 자기 과제로 직접 비교해 보는 것이 맞습니다.

**실무에 주는 의미: 영상이 “한 번 만드는 것”에서 “데이터로 찍어 내는 것”으로 바뀝니다.** 변수와 `--batch`, AWS Lambda 렌더를 조합하면 고객사별 온보딩 영상, 릴리스마다 자동 생성되는 변경 사항 영상, 대시보드 수치를 담은 주간 리포트 영상처럼 템플릿 하나에서 수백 개 버전을 만드는 파이프라인이 됩니다. 이때 비용 구조가 중요한데, Remotion은 4인 이상 회사에서 자동화 렌더에 렌더당 요금(공식 페이지 기준 $0.01, 월 최소 $100)을 매기는 반면 HyperFrames는 로컬과 자기 클라우드 렌더에 라이선스 비용이 없습니다. 대량 렌더를 계획하는 팀에게는 이 차이가 도구 선택의 결정적 요인이 될 수 있습니다. 다만 1.0 이전이라는 점을 감안해 CLI 버전을 고정(`npx hyperframes@0.8.214`처럼)하고 업그레이드는 별도 PR로 검증하는 운영이 필요해 보입니다.

**앞으로 지켜볼 점:** 첫째, 1.0과 함께 `FrameAdapter`와 HTML 스키마가 안정 API로 고정되는지입니다. 지금처럼 하루 여러 번 바뀌는 속도는 실험에는 좋지만 운영 파이프라인에는 부담입니다. 둘째, 오픈소스 프레임워크와 HeyGen 유료 기능(클라우드, 음성, 아바타, Studio 앱 로그인)의 경계가 어떻게 움직이는지입니다. 지금은 로컬 렌더가 완전히 무료이지만, 핵심 기능이 계정 쪽으로 옮겨 가는지 지켜볼 필요가 있습니다. 셋째, 에이전트가 쓴 영상의 품질 검증입니다. `check`의 레이아웃·대비 검사와 `snapshot --describe`(Gemini로 프레임 설명) 같은 기능은 “에이전트가 자기 결과를 눈으로 확인하는” 루프의 시작점인데, 이것이 얼마나 믿을 만해지는지가 사람의 검토 부담을 결정할 것입니다.

<!-- EDITOR_NOTE: 운영자가 직접 써 본 경험이나 의견을 여기에 추가하세요. -->

## 이런 분께 추천

- 제품 소개, 릴리스 노트, PR 설명 영상을 코딩 에이전트에게 맡겨 반복 생산하고 싶은 개발자
- 같은 템플릿으로 고객사별·데이터별 영상 수백 개를 렌더링해야 하는 팀
- 이미 HTML·CSS·GSAP 애니메이션 자산이 있고, 이를 React로 다시 쓰지 않고 영상으로 내보내고 싶은 경우
- Remotion의 회사 규모별 라이선스가 부담되는 4인 이상 조직

## 이런 경우엔 다른 도구

- **팀이 React와 TypeScript 중심이고 타입이 지정된 컴포지션 입력, 성숙한 클라우드 렌더러가 필요하다면:** Remotion이 더 오래 검증된 선택입니다.
- **사람이 타임라인에서 컷을 직접 편집하는 일이 대부분이라면:** 코드 기반 도구보다 일반 영상 편집 프로그램이 빠릅니다.
- **버전 변경 없이 몇 년 동안 그대로 돌아가야 하는 파이프라인이라면:** 1.0 이전인 지금은 버전 고정과 회귀 테스트 비용을 감수할 수 있는지 먼저 따져 봐야 합니다.

## 참고 링크

- [GitHub 저장소 / README](https://github.com/heygen-com/hyperframes) · [릴리스 노트](https://github.com/heygen-com/hyperframes/releases) · [LICENSE](https://github.com/heygen-com/hyperframes/blob/main/LICENSE) · [ADOPTERS.md](https://github.com/heygen-com/hyperframes/blob/main/ADOPTERS.md)
- [What is HyperFrames?](https://hyperframes.heygen.com/introduction) · [Quickstart](https://hyperframes.heygen.com/quickstart) · [FAQ](https://hyperframes.heygen.com/faq) · [Troubleshooting](https://hyperframes.heygen.com/help)
- [Compositions](https://hyperframes.heygen.com/concepts/compositions) · [Data attributes](https://hyperframes.heygen.com/concepts/data-attributes) · [Deterministic Rendering](https://hyperframes.heygen.com/concepts/determinism) · [Frame adapters](https://hyperframes.heygen.com/concepts/frame-adapters) · [Variables](https://hyperframes.heygen.com/concepts/variables)
- [Render from the command line](https://hyperframes.heygen.com/guides/rendering) · [CLI reference (telemetry 포함)](https://hyperframes.heygen.com/packages/cli) · [@hyperframes/engine](https://hyperframes.heygen.com/packages/engine) · [HTML schema](https://hyperframes.heygen.com/reference/html-schema)
- [Agent skills](https://hyperframes.heygen.com/guides/skills) · [Animation runtimes (스킬 참고 문서)](https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes/references/runtimes.md) · [Choose a rendering path](https://hyperframes.heygen.com/deploy/overview) · [Changelog](https://hyperframes.heygen.com/changelog)
- [HyperFrames vs Remotion (HeyGen 작성)](https://hyperframes.heygen.com/guides/hyperframes-vs-remotion) · [Remotion License](https://www.remotion.pro/license)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
