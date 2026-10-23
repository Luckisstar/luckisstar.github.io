---
layout: default
title: "[오픈소스 소개] Lighthouse: 웹 페이지의 성능·접근성·SEO를 점수로 진단하는 자동 감사 도구"
description: "웹 페이지의 성능·접근성·권장사항·SEO를 점수로 진단하는 Lighthouse의 동작 원리, 성능 점수 가중치, CLI·Node·CI(LHCI) 활용법을 정리했습니다."
date: 2026-10-20
categories: [opensource]
---

# [오픈소스 소개] Lighthouse: 웹 페이지의 성능·접근성·SEO를 점수로 진단하는 자동 감사 도구

- **저장소:** [GoogleChrome/lighthouse](https://github.com/GoogleChrome/lighthouse) · [공식 문서 (developer.chrome.com)](https://developer.chrome.com/docs/lighthouse/overview/) · [저장소 docs/](https://github.com/GoogleChrome/lighthouse/tree/main/docs)
- **라이선스:** Apache 2.0
- **언어:** JavaScript
- **현황 (2026-10-20 기준):** GitHub 스타 약 3.1만 개, 최신 릴리스 v13.5.0 (9월 18일)

## 한 줄 요약

**URL 하나를 주면 실제 Chrome으로 페이지를 열어 성능, 접근성, 권장사항, SEO를 점검하고 점수와 개선 방법을 리포트로 만들어 주는 오픈소스 도구**입니다. Chrome 팀이 관리하며, Chrome DevTools의 Lighthouse 패널과 PageSpeed Insights의 "실험실 데이터"가 모두 이 엔진으로 돌아갑니다. 같은 엔진을 CLI, Node 모듈, CI에서도 그대로 쓸 수 있다는 점이 핵심입니다.

## 어떤 문제를 푸나

웹 페이지 품질 문제는 개발자 PC에서는 잘 드러나지 않습니다.

- 사무실 광랜과 최신 노트북에서는 빠른데, 사용자는 "느리다"고 합니다.
- 버튼에 접근성 이름이 빠졌거나 대비가 낮은 텍스트가 있어도 눈으로는 잘 모릅니다.
- `<title>`, `meta description`, `robots.txt` 같은 SEO 기본기를 배포마다 사람이 확인하기 어렵습니다.
- 어제 머지한 PR 하나가 번들 크기를 키워 LCP를 망쳤는데, 아무도 눈치채지 못합니다.

Lighthouse는 이런 점검을 **재현 가능한 자동 감사(audit)**로 바꿉니다. 기본 설정은 "중간급 모바일 기기 + 느린 4G" 환경을 흉내 내서 측정합니다. README FAQ의 표현을 빌리면, 4G 연결의 약 200달러짜리 중급 휴대폰을 쓰는 전형적인 모바일 사용자가 경험할 성능을 보여 줍니다. 그래서 "내 컴퓨터에서는 빠른데 점수가 낮다"는 일이 자주 생기는데, 이건 버그가 아니라 의도된 설계입니다.

또 README에 따르면 Lighthouse는 로컬 Chrome으로 감사를 돌리고, **리포트 결과를 원격 서버로 보내지 않습니다.** 사내 스테이징 서버나 로그인 뒤 페이지도 부담 없이 점검할 수 있습니다.

## 핵심 개념 / 동작 원리

### 구조

저장소의 [Architecture](https://github.com/GoogleChrome/lighthouse/blob/main/docs/architecture.md) 문서를 단순화하면 다음과 같습니다.

```
 lighthouse <url>
   │
   ▼
 Driver ── CDP / Puppeteer ──▶ Chrome (page load)
   │
   ▼
 Gatherers ─▶ Artifacts (trace, devtools log, DOM...)
   │
   ▼
 Audits (+ Computed Artifacts) ─▶ score per audit
   │
   ▼
 Categories (weighted) ─▶ LHR (JSON)
   │
   ▼
 Report renderer ─▶ HTML / JSON / CSV
```

| 구성 요소 | 역할 |
| --- | --- |
| **Driver** | Puppeteer와 Chrome DevTools Protocol(CDP, Chrome을 원격 제어하는 프로토콜)로 브라우저와 통신합니다. |
| **Gatherer** | 페이지에서 정보를 모읍니다. 주요 산출물은 `artifacts.json`, 성능 정보가 담긴 `trace.json`, 프로토콜 이벤트 기록인 `devtoolslog.json`입니다. |
| **Audit** | 하나의 기능·최적화·지표를 검사해 점수를 매기는 단위입니다. 예: "이미지에 `alt` 속성이 있는가". |
| **Category** | 여러 감사를 묶어 가중 평균으로 카테고리 점수를 냅니다. |
| **LHR** | Lighthouse Result. 모든 결과가 담긴 JSON 객체이며 HTML 리포트는 이걸로 그립니다. |

수집(gather)과 감사(audit)가 분리돼 있어서 `-G`로 수집만 하고, 나중에 `-A`로 저장된 결과에 감사만 다시 돌릴 수도 있습니다.

### 카테고리

v13 기본 설정(`core/config/default-config.js`)에 들어 있는 카테고리는 다음과 같습니다.

| 카테고리 ID | 내용 | 점수 방식 |
| --- | --- | --- |
| `performance` | 로딩 속도, 반응성, 레이아웃 안정성 | 지표 5개의 가중 평균 |
| `accessibility` | axe-core 기반 접근성 검사 | 감사별 가중치(심각도 기반) 평균 |
| `best-practices` | 보안, 콘솔 오류, 브라우저 호환성 등 | 모든 감사 동일 가중치 |
| `seo` | 검색 엔진 크롤링·색인 기본기 | 동일 가중치(구조화 데이터는 수동 검사) |
| `agentic-browsing` | AI 에이전트가 사이트를 잘 다룰 수 있는가 (llms.txt, WebMCP 등) | 통과 개수(분수) 표시, 아직 개발 중 |

두 가지 변화를 알아 두면 좋습니다.

- **PWA 카테고리는 없어졌습니다.** Chrome의 설치 기준 변경에 따라 Lighthouse 12.0.0(2024-04)에서 제거됐고, PWA 점검은 DevTools 문서 쪽으로 안내합니다. 오래된 블로그 글에 나오는 "PWA 배지"는 지금 버전에는 없습니다.
- **Agentic Browsing 카테고리가 생겼습니다.** 13.3.0(2026-05)에서 기본 설정에 추가됐고, 13.5.0에서는 Agent Resource Discovery(ARD) 감사가 더해졌습니다. 카테고리 설명에도 "아직 개발 중이며 바뀔 수 있다"고 적혀 있습니다.

### 성능 점수는 어떻게 계산되나

성능 점수는 지표 5개의 가중 평균입니다. 가중치는 v13 기본 설정 기준이며, 공식 문서의 Lighthouse 10 표와 같습니다.

| 지표 | 의미 | 가중치 |
| --- | --- | --- |
| **FCP** (First Contentful Paint) | 첫 텍스트·이미지가 그려진 시점 | 10% |
| **SI** (Speed Index) | 화면이 얼마나 빨리 채워지는지 | 10% |
| **LCP** (Largest Contentful Paint) | 가장 큰 콘텐츠가 그려진 시점 | 25% |
| **TBT** (Total Blocking Time) | 긴 작업 때문에 메인 스레드가 막힌 총 시간 | 30% |
| **CLS** (Cumulative Layout Shift) | 레이아웃이 예기치 않게 움직인 정도 | 25% |

TTI(Time to Interactive)는 가중치 0으로 숨겨져 있습니다. 즉 점수의 80%가 LCP, TBT, CLS에서 나옵니다. "JavaScript 실행량(TBT)과 레이아웃 흔들림(CLS)을 잡는 게 점수에 가장 크다"는 뜻입니다.

각 지표 값은 [공식 점수 문서](https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/)에 따라 HTTP Archive의 실제 사이트 데이터로 만든 로그 정규 곡선에 대입됩니다. 실제 사이트의 25번째 백분위 값이 50점, 8번째 백분위 값이 90점이 되도록 맞춰져 있습니다. 점수 색은 0~49 빨강(Poor), 50~89 주황(Needs Improvement), 90~100 초록(Good)입니다. 90점 위로는 곡선이 완만해서 1점 올리기가 점점 어려워집니다.

다른 카테고리는 더 단순합니다. Best Practices와 SEO는 감사마다 같은 가중치이고, Accessibility는 감사마다 가중치가 다릅니다. 접근성 감사는 통과/실패 둘 중 하나라서, 버튼 절반에만 이름이 있으면 "절반 점수"가 아니라 그 감사는 0점입니다.

### 실험실 데이터와 필드 데이터

Lighthouse를 이해할 때 가장 중요한 구분입니다.

| 구분 | 실험실(lab) 데이터 | 필드(field) 데이터 |
| --- | --- | --- |
| 출처 | Lighthouse가 통제된 환경에서 한 번 로드 | 실제 Chrome 사용자 기록 (CrUX, Chrome UX Report) |
| 장점 | 재현 가능, 디버깅에 유리, 배포 전 측정 가능 | 실제 사용자 경험 그대로 |
| 한계 | 실제 사용자 환경과 다를 수 있음 | 지표가 제한적, 트래픽이 적으면 데이터 없음 |
| 보는 곳 | DevTools, CLI, PSI 하단 | PageSpeed Insights 상단, CrUX |

PageSpeed Insights 문서는 필드 데이터가 **지난 28일**의 실제 사용자 경험이며, 세 가지 Core Web Vitals의 75번째 백분위가 모두 "Good"이면 평가를 통과한다고 설명합니다. 그리고 실험실 데이터는 "Lighthouse로 시뮬레이션 환경에서 분석"한 결과라고 밝힙니다. 즉 Lighthouse 점수는 **필드 Core Web Vitals 통과 여부와 같은 것이 아닙니다.** 실험실 점수로 원인을 찾고, 필드 데이터로 결과를 확인하는 식으로 함께 쓰는 게 맞습니다.

### 스로틀링(throttling)

스로틀링은 네트워크와 CPU를 일부러 느리게 만들어 느린 환경을 흉내 내는 것입니다. [throttling 문서](https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md)의 내용은 다음과 같습니다.

- **네트워크 기본값("Slow 4G"):** 지연 150ms, 다운로드 1.6Mbps, 업로드 750Kbps, 패킷 손실 없음. 대략 4G 하위 25%, 3G 상위 25% 수준입니다.
- **CPU 기본값:** 호스트 CPU의 **4배 감속**. 고성능 데스크톱을 중급 모바일 수준으로 내리는 값입니다.
- **방식(`--throttling-method`):**

| 값 | 이름 | 특징 |
| --- | --- | --- |
| `simulate` (기본) | 시뮬레이션 스로틀링 | 스로틀링 없이 한 번 로드한 뒤, Lantern이라는 시뮬레이터로 느린 환경의 결과를 계산합니다. 빠르고 결과 편차가 작습니다. |
| `devtools` | 요청 단위 스로틀링 | DevTools와 같은 방식으로 실제로 느리게 로드합니다. 트레이스와 지표가 일치합니다. |
| `provided` | 스로틀링 없음 | 외부에서 이미 네트워크를 제한했다고 가정합니다. |

시뮬레이션 방식이라서 DevTools에서 "View Original Trace"를 눌렀을 때 보이는 트레이스 수치와 리포트 지표가 다를 수 있습니다. 원본 트레이스는 시뮬레이션 전의 기록이기 때문입니다.

리포트 하단에는 `benchmarkIndex`("CPU/Memory Power")가 찍힙니다. 실행한 기기의 대략적인 CPU 성능 지표인데, 저사양 기기에서 4배 감속을 그대로 쓰면 과하게 느려지므로 이 값을 보고 `--throttling.cpuSlowdownMultiplier`를 조정할 수 있습니다.

### 세 가지 모드: user flow

v10부터 Lighthouse는 "첫 로드" 외에도 페이지의 전체 수명을 측정할 수 있습니다. [user-flows 문서](https://github.com/GoogleChrome/lighthouse/blob/main/docs/user-flows.md) 기준입니다.

| 모드 | 측정 대상 | 성능 점수 | 한계 |
| --- | --- | --- | --- |
| **Navigation** | 페이지 한 번의 로드 (기본) | 있음 | 폼 제출, SPA 전환은 못 봄 |
| **Timespan** | 사용자 상호작용이 포함된 임의 구간 | 없음 | LCP 같은 시점 지표, 접근성 없음 |
| **Snapshot** | 특정 순간의 페이지 상태 | 없음 | 네트워크·메인 스레드 분석 없음 |

여러 모드를 엮은 **멀티스텝 flow 리포트는 Node API와 Puppeteer로만** 만들 수 있습니다. DevTools는 각 모드를 단독으로만 실행합니다.

## 주요 기능

- **다양한 실행 경로:** DevTools 패널, CLI, Node 모듈, PageSpeed Insights, Chrome 확장 프로그램. 공식 문서는 특별한 이유가 없으면 확장 프로그램보다 DevTools를 쓰라고 권합니다.
- **출력 형식:** HTML(기본), JSON, CSV. 여러 형식을 동시에 낼 수 있습니다.
- **Lighthouse Viewer:** JSON 결과를 [온라인 뷰어](https://googlechrome.github.io/lighthouse/viewer/)에 끌어다 놓으면 HTML 리포트로 볼 수 있습니다. 공유 기능을 쓰면 내 GitHub 계정의 비밀 Gist로 저장됩니다.
- **프리셋:** `--preset=desktop`(데스크톱 점수 곡선과 화면 에뮬레이션), `perf`, `experimental`.
- **부분 실행:** `--only-categories`, `--only-audits`, `--skip-audits`.
- **인증 페이지:** Puppeteer로 로그인, `--extra-headers`로 인증 헤더 전달, DevTools에서 로그인 상태로 실행 등 여러 방법을 문서로 제공합니다.
- **확장성:** 사용자 정의 Gatherer·Audit을 만들 수 있고, 플러그인(`--plugins`)으로 카테고리를 추가할 수 있습니다. 예를 들어 CrUX 필드 데이터를 리포트에 넣는 커뮤니티 플러그인이 있습니다.
- **Performance Insights:** v13.0.0(2025-10)부터 기존 성능 감사 상당수가 DevTools Performance 패널과 공유하는 "insights" 감사로 바뀌었습니다. LCP 분해, 네트워크 의존성 트리 같은 항목이 여기에 속합니다.

## 설치와 시작

### DevTools에서 바로 쓰기

Chrome만 있으면 됩니다. 개발자 도구를 열고 **Lighthouse** 탭에서 모드(Navigation/Timespan/Snapshot), 기기(Mobile/Desktop), 카테고리를 고른 뒤 분석을 누릅니다. 로그인한 상태 그대로 측정되고, 쿠키를 지우지 않습니다.

### CLI 설치

README 기준으로 **Node 22 LTS 이상**이 필요합니다(13.5.0의 `package.json` `engines`는 `>=22.19`). 실행 기기에 Chrome도 설치돼 있어야 합니다.

```bash
npm install -g lighthouse

# 기본: ./<HOST>_<DATE>.report.html 생성
lighthouse https://example.com

# 끝나면 브라우저로 리포트 열기
lighthouse https://example.com --view
```

자주 쓰는 출력 조합입니다.

```bash
# JSON은 경로를 안 주면 stdout으로 나갑니다
lighthouse https://example.com --output json > report.json

# HTML과 JSON을 함께: ./reports/home.report.html, ./reports/home.report.json
lighthouse https://example.com --output html --output json --output-path ./reports/home

# 데스크톱 기준으로 측정
lighthouse https://example.com --preset=desktop

# 헤드리스로, 로그 없이
lighthouse https://example.com --quiet --chrome-flags="--headless"
```

처음 CLI를 실행하면 런타임 예외를 익명으로 보고해도 되는지 묻습니다. 거절해도 기능에는 영향이 없고, `--no-enable-error-reporting`으로 미리 끌 수 있습니다.

### Node 모듈로 쓰기

```bash
npm i -D lighthouse chrome-launcher
```

```js
// run.mjs
import fs from 'node:fs';
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

const chrome = await chromeLauncher.launch({chromeFlags: ['--headless']});
const options = {
  logLevel: 'info',
  output: 'html',
  onlyCategories: ['performance'],
  port: chrome.port,
};
const runnerResult = await lighthouse('https://example.com', options);

fs.writeFileSync('lhreport.html', runnerResult.report);   // HTML 문자열
console.log('URL:', runnerResult.lhr.finalDisplayedUrl);
console.log('Performance:', runnerResult.lhr.categories.performance.score * 100);

chrome.kill();
```

Node 모듈에서는 Chrome을 대신 띄워 주지 않습니다. `chromeFlags`, `outputPath`, `view` 같은 CLI 전용 플래그는 무시되고, 설정 객체는 세 번째 인자로 넘깁니다.

## 실전 예제

### 1. 모바일·데스크톱 점수를 한 번에 뽑아 표로 보기

배포 전에 주요 페이지 몇 개를 모바일과 데스크톱으로 각각 돌리고, `jq`로 카테고리 점수만 요약하는 셸 스크립트입니다.

```bash
#!/usr/bin/env bash
set -euo pipefail
URLS=("https://example.com/" "https://example.com/pricing")
mkdir -p reports

for url in "${URLS[@]}"; do
  name=$(echo "$url" | sed -E 's#https?://##; s#[/:]+#_#g')
  lighthouse "$url" --quiet --chrome-flags="--headless" \
    --output json --output-path "reports/${name}-mobile.json"
  lighthouse "$url" --quiet --chrome-flags="--headless" --preset=desktop \
    --output json --output-path "reports/${name}-desktop.json"
done

for f in reports/*.json; do
  jq -r --arg f "$f" '
    [$f] + ([.categories[] | (.score * 100 | floor | tostring)])
    | @tsv' "$f"
done
```

`.categories`에는 실행한 카테고리 순서대로 점수가 0~1 사이 값으로 들어 있습니다. 점수가 `null`이면 해당 카테고리 감사가 오류로 끝난 것이니 `runtimeError`와 각 감사의 `errorMessage`를 확인합니다.

### 2. 5번 돌려서 중앙값 run 고르기

성능 점수는 코드가 그대로여도 매번 조금씩 달라집니다. [variability 문서](https://github.com/GoogleChrome/lighthouse/blob/main/docs/variability.md)는 **5회 실행의 중앙값이 1회보다 두 배 안정적**이라고 설명하고, 이를 위한 `computeMedianRun` 함수를 제공합니다.

```js
// median.mjs
import {spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {computeMedianRun} from 'lighthouse/core/lib/median-run.js';

const require = createRequire(import.meta.url);
const lighthouseCli = require.resolve('lighthouse/cli');
const url = process.argv[2] ?? 'https://example.com';

const results = [];
for (let i = 0; i < 5; i++) {
  console.log(`run #${i + 1}`);
  const {status, stdout} = spawnSync('node', [
    lighthouseCli, url, '--output=json', '--quiet', '--chrome-flags=--headless',
  ], {maxBuffer: 200 * 1024 * 1024});
  if (status !== 0) continue;
  results.push(JSON.parse(stdout));
}

const median = computeMedianRun(results);
console.log('median performance:', median.categories.performance.score * 100);
for (const id of ['largest-contentful-paint', 'total-blocking-time', 'cumulative-layout-shift']) {
  console.log(id, median.audits[id].displayValue);
}
```

여기서 실행은 **순차로** 합니다. 같은 기기에서 동시에 여러 개를 돌리면 CPU 경쟁 때문에 결과가 왜곡된다고 문서가 분명히 경고합니다. JSON 출력에는 스크린샷이 들어가 꽤 커질 수 있어 `maxBuffer`를 넉넉히 잡았습니다.

### 3. 로그인 후 체크아웃 흐름을 user flow로 측정하기

Puppeteer로 로그인과 클릭을 진행하면서, 페이지 로드는 navigation, 상호작용 구간은 timespan, 결과 화면은 snapshot으로 측정합니다. 선택자와 URL은 대상 서비스에 맞게 바꿔야 합니다.

```js
// flow.mjs  (npm i -D lighthouse puppeteer)
import fs from 'node:fs';
import puppeteer from 'puppeteer';
import {startFlow} from 'lighthouse';

const browser = await puppeteer.launch();
const page = await browser.newPage();

// 1) 로그인은 측정 밖에서 처리
await page.goto('https://shop.example.com/login');
await page.locator('input[name=email]').fill(process.env.LOGIN_EMAIL);
await page.locator('input[name=password]').fill(process.env.LOGIN_PASSWORD);
await Promise.all([
  page.waitForNavigation(),
  page.locator('button[type=submit]').click(),
]);

const flow = await startFlow(page, {name: 'Checkout flow'});

// 2) 상품 페이지 로드: 성능 점수 포함
//    로그인 세션 유지를 위해 저장소 초기화를 끕니다
await flow.navigate('https://shop.example.com/products/42', {
  disableStorageReset: true,
});

// 3) 장바구니 담기 상호작용: TBT, CLS 등 측정
await flow.startTimespan({name: 'Add to cart'});
await page.locator('button.add-to-cart').click();
await page.waitForSelector('.cart-drawer.open');
await flow.endTimespan();

// 4) 열린 장바구니 상태의 접근성 점검
await flow.snapshot({name: 'Cart drawer'});

// 5) 클릭으로 시작되는 이동도 navigation으로 측정
await flow.navigate(async () => {
  await page.locator('a.checkout').click();
}, {name: 'Go to checkout'});

fs.writeFileSync('flow-report.html', await flow.generateReport());
fs.writeFileSync('flow-result.json', JSON.stringify(await flow.createFlowResult(), null, 2));
await browser.close();
```

문서의 팁도 함께 기억하면 좋습니다.

- timespan은 짧게, 한 가지 상호작용에만 집중합니다.
- 페이지 이동(하드 내비게이션)은 timespan이 아니라 navigation으로 측정합니다.
- timespan을 끝내기 전에 `waitForSelector` 등으로 전환이 끝났는지 꼭 기다립니다.
- 이동이 실패할 수 있다면 `try/catch`에서 `flow.dispose()`로 정리합니다.
- 데스크톱 기준으로 측정하려면 `startFlow(page, {config: desktopConfig})`를 씁니다(`import {startFlow, desktopConfig} from 'lighthouse'`).

### 4. Lighthouse CI로 PR마다 점수 회귀 막기

[Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)(`@lhci/cli`)는 공식 CI 도구입니다. 기본으로 URL마다 Lighthouse를 3번 돌리고, 결과에 기준(assertion)을 걸어 실패하면 빌드를 깨뜨립니다.

정적 사이트(예: 빌드 결과가 `./dist`) 기준 설정 파일입니다.

```js
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      staticDistDir: './dist',
      numberOfRuns: 5,
    },
    assert: {
      preset: 'lighthouse:recommended',
      assertions: {
        'categories:performance': ['warn', {minScore: 0.9}],
        'categories:accessibility': ['error', {minScore: 1}],
        'largest-contentful-paint': ['error', {maxNumericValue: 2500, aggregationMethod: 'median-run'}],
        'cumulative-layout-shift': ['error', {maxNumericValue: 0.1}],
        'resource-summary:script:size': ['warn', {maxNumericValue: 300000}],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

- 감사 ID 단위로 `minScore`(점수), `maxNumericValue`(수치), `maxLength`(지적 항목 수)를 걸 수 있습니다.
- `categories:<id>`로 카테고리 점수에도 기준을 걸 수 있습니다.
- 여러 run을 어떻게 합칠지는 `aggregationMethod`로 정합니다: `median`, `optimistic`(기본, 가장 통과하기 쉬운 값), `pessimistic`, `median-run`.
- 예전의 `budget.json`(성능 예산) 기능은 Lighthouse 12에서 코어에서 제거됐습니다. 대신 위처럼 `resource-summary:<type>:size|count` assertion으로 예산을 표현할 수 있습니다. 이 assertion의 크기 단위는 **바이트**입니다.
- `temporary-public-storage`는 이름처럼 **임시·공개** 저장소입니다. 리포트가 공개 URL에 올라가는 것이 싫다면 업로드를 빼거나 자체 LHCI 서버를 띄웁니다.

GitHub Actions 워크플로입니다. GitHub 상태 체크를 붙이려면 [Lighthouse CI GitHub App](https://github.com/apps/lighthouse-ci)을 설치하고 받은 토큰을 저장소 시크릿에 넣습니다.

{% raw %}
```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on: [push, pull_request]
jobs:
  lhci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - uses: actions/setup-node@v4
        with:
          node-version: 22.x
      - run: npm ci
      - run: npm run build
      - name: run Lighthouse CI
        run: |
          npm install -g @lhci/cli@0.15.x
          lhci autorun
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```
{% endraw %}

`lhci autorun`은 collect, assert, upload를 알아서 이어서 실행합니다. CLI 플래그로 덮어쓸 때는 `lhci autorun --collect.numberOfRuns=5`처럼 반드시 `=` 문법을 써야 합니다.

한 가지 주의할 점이 있습니다. 최신 `@lhci/cli`는 v0.15.1(2025-06)이고, 저장소 main 브랜치의 `packages/cli/package.json`은 아직 `lighthouse` 12.6.1에 의존합니다. 그래서 LHCI 결과는 최신 DevTools(13.x)와 감사 목록이나 수치가 조금 다를 수 있습니다. 같은 도구, 같은 버전끼리 비교하는 습관이 중요합니다.

### 5. 스로틀링을 끄거나 실제 네트워크 제한으로 바꾸기

로컬 개발 서버에서 "순수한 코드 변화"만 보고 싶거나, 시뮬레이션이 아닌 실제 느린 네트워크로 확인하고 싶을 때가 있습니다.

```bash
# 모든 스로틀링과 기기 에뮬레이션 끄기
lighthouse http://localhost:3000 \
  --screenEmulation.disabled --throttling-method=provided --no-emulatedUserAgent

# 저사양 CI 머신: CPU 감속을 4배에서 2배로 낮추기
lighthouse https://example.com --throttling.cpuSlowdownMultiplier=2

# 실제 트레이스와 지표를 일치시키는 DevTools 방식
lighthouse https://example.com --throttling-method=devtools
```

throttling 문서는 가장 정확한 방법으로 **패킷 단위 스로틀링**을 소개합니다. `@sitespeed.io/throttle`로 시스템 네트워크 전체를 제한하고, Lighthouse 자체 네트워크 제한은 끈 채 CPU 제한만 남기는 방식입니다(`sudo` 필요, 기기 전체 네트워크가 느려짐에 주의).

```bash
npm install -g @sitespeed.io/throttle
throttle 3gfast
lighthouse --throttling-method=devtools \
  --throttling.requestLatencyMs=0 \
  --throttling.downloadThroughputKbps=0 \
  --throttling.uploadThroughputKbps=0 \
  https://example.com
throttle --stop
```

## 실무 팁 & 자주 겪는 문제

| 증상 | 원인과 해결 |
| --- | --- |
| 내 PC에서는 빠른데 점수가 낮음 | 기본값이 느린 4G와 4배 CPU 감속입니다. 의도된 결과이며, 데스크톱 기준이 필요하면 `--preset=desktop`을 씁니다. |
| 실행할 때마다 점수가 다름 | A/B 테스트, 광고, 서버 응답 편차, 기기 성능, 확장 프로그램, 백신 등이 원인입니다. 여러 번 돌려 중앙값을 쓰고, 단일 run으로 결론 내지 않습니다. |
| DevTools 점수와 PSI 점수가 다름 | 실행 기기, 위치, 네트워크, Lighthouse 버전이 다릅니다. PSI는 구글 서버에서 돌기 때문에 기기 편차는 작지만 네트워크 경로가 다릅니다. |
| DevTools에서 점수가 유난히 낮음 | 확장 프로그램이 JavaScript를 주입하고 있을 수 있습니다. 시크릿 창이나 확장 없는 프로필에서 다시 돌립니다. |
| CI에서 결과가 들쭉날쭉 | 문서는 최소 2코어(4코어 권장), 2GB RAM(4~8GB 권장)을 권하고, Lambda 같은 FaaS와 AWS `t` 계열 같은 버스트형 인스턴스는 피하라고 합니다. 한 머신에서 동시 실행하지 말고, 여러 대로 수평 확장합니다. |
| 로그인 페이지가 측정 안 됨 | 기본 실행은 저장소를 초기화한 "새 사용자"입니다. Puppeteer로 로그인 후 `disableStorageReset: true`를 주거나, `--extra-headers`로 인증 헤더를 넘깁니다. `Cookie` 헤더를 직접 넣으면 다른 쿠키를 덮어쓸 수 있습니다. |
| Puppeteer로 띄운 Chrome에서 이상한 결과 | 문서 예제는 `--enable-automation` 기본 인자를 빼고(`ignoreDefaultArgs`), 800x600 기본 뷰포트를 쓰지 않도록(`defaultViewport: null`) 설정합니다. |
| 원인 분석용 원본 데이터가 필요함 | `--save-assets`로 트레이스와 DevTools 로그를 저장하고, 트레이스는 DevTools Performance 패널에서 엽니다. |
| JSON 파일이 너무 큼 | 전체 페이지 스크린샷 때문입니다. `--disable-full-page-screenshot`으로 줄입니다. |

점수 자체보다 **지표와 진단 항목**을 보는 습관이 더 중요합니다. 점수는 HTTP Archive 분포에 대한 상대 위치일 뿐이고, 실제로 고칠 대상은 "LCP 요소가 무엇이고 왜 늦게 그려졌는가" 같은 구체적인 항목입니다.

## 비슷한 도구와 비교

아래 비교에서 Lighthouse와 PSI의 관계는 공식 문서 기준이고, WebPageTest와 DevTools Performance 패널에 대한 설명은 일반적으로 알려진 내용 기준입니다. 세부 기능은 각 서비스에서 최신 정보를 확인하는 것이 좋습니다.

| 항목 | Lighthouse | PageSpeed Insights | WebPageTest | DevTools Performance 패널 |
| --- | --- | --- | --- | --- |
| 형태 | 오픈소스 엔진 (CLI, Node, DevTools) | 구글 웹 서비스 + API | 오픈소스 + 호스팅 서비스 | Chrome 내장 프로파일러 |
| 데이터 | 실험실 | 필드(CrUX 28일) + 실험실(Lighthouse) | 실험실(실제 기기·지역 선택) | 실험실(내 브라우저) |
| 네트워크 제한 | 기본 시뮬레이션 | Lighthouse와 동일 | 패킷 단위 스로틀링 | 요청 단위 스로틀링 |
| 점수 | 카테고리별 0~100 | Lighthouse 점수 + CWV 평가 | 자체 등급과 지표 중심 | 점수 없음 |
| 로컬·사내 페이지 | 가능 | 불가(공개 URL만) | 사설 인스턴스 필요 | 가능 |
| 강점 | 자동화, CI, 접근성·SEO까지 | 실제 사용자 데이터 확인 | 워터폴, 필름스트립, 다지역 비교 | 메인 스레드 단위 정밀 분석 |

정리하면, PSI는 "실제 사용자는 어떤가"를 보는 곳, Lighthouse는 "배포 전에 자동으로 막는" 도구, WebPageTest는 "실제 네트워크 조건에서 깊게 파는" 도구, Performance 패널은 "특정 긴 작업의 원인을 찾는" 도구에 가깝습니다. throttling 문서도 WebPageTest가 패킷 단위 스로틀링을 쓴다고 언급합니다.

## 장점과 한계

**장점**

- DevTools, PSI와 같은 엔진이라 팀원 누구나 같은 기준으로 이야기할 수 있습니다.
- 성능뿐 아니라 접근성, 보안 관련 권장사항, SEO 기본기까지 한 번에 점검합니다.
- 감사마다 "왜 중요한지, 어떻게 고치는지" 문서 링크가 붙어 있어 학습 도구로도 좋습니다.
- CLI, Node API, Lighthouse CI로 자동화가 쉽고, 결과를 JSON으로 받아 원하는 대로 가공할 수 있습니다.
- user flow로 SPA 전환이나 상호작용 중의 성능과 접근성도 측정할 수 있습니다.
- 결과가 외부로 전송되지 않아 사내 페이지에도 쓸 수 있습니다.

**한계**

- 실험실 측정이라 실제 사용자 경험(필드 데이터)을 대신하지 못합니다.
- 점수 편차가 있어 단일 실행 결과로 판단하면 오해하기 쉽습니다.
- 기본 시뮬레이션 스로틀링은 빠르고 안정적이지만, 문서 스스로 예외적인 경우 부정확할 수 있다고 인정합니다.
- 자동 접근성 검사는 사람이 해야 하는 점검(키보드 흐름, 스크린 리더 경험 등)을 모두 대신하지 못하며, 리포트에도 수동 확인 항목이 따로 있습니다.
- Chrome(Chromium) 전용입니다. Safari나 Firefox에서의 성능은 알려 주지 않습니다.
- 감사 목록과 점수 방식이 메이저 버전마다 바뀝니다(PWA 제거, budgets 제거, insights 전환 등). 버전이 다른 결과끼리 비교하면 안 됩니다.

## 이런 분께 추천 / 이런 경우엔 다른 도구

**추천**

- 프런트엔드 성능과 접근성을 PR 단계에서 자동으로 지키고 싶은 팀
- Core Web Vitals 개선 작업을 시작하면서 원인 후보를 빠르게 찾고 싶은 분
- 사내 스테이징이나 로그인 뒤 페이지를 외부 서비스 없이 점검해야 하는 분
- 접근성·SEO 기본기를 배포 체크리스트로 만들고 싶은 분
- Puppeteer로 이미 E2E 스크립트가 있어서, 같은 흐름에 성능 측정을 얹고 싶은 분

**다른 도구가 나은 경우**

- 실제 사용자 성능 추이가 궁금하다면 PageSpeed Insights의 필드 데이터, CrUX, 또는 RUM(Real User Monitoring) 도구가 맞습니다.
- 여러 지역·실제 기기·패킷 단위 네트워크로 깊이 비교해야 한다면 WebPageTest가 더 적합합니다.
- 특정 상호작용이 왜 느린지 함수 단위로 파고들어야 한다면 DevTools Performance 패널이 낫습니다.
- 정밀한 접근성 감사가 목적이라면 axe 같은 전용 도구와 수동 점검을 함께 쓰는 편이 좋습니다.

## 참고 링크

- [Lighthouse overview (developer.chrome.com)](https://developer.chrome.com/docs/lighthouse/overview/)
- [Lighthouse performance scoring](https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/)
- [About PageSpeed Insights](https://developers.google.com/speed/docs/insights/v5/about)
- [README (CLI 옵션 전체)](https://github.com/GoogleChrome/lighthouse/blob/main/readme.md)
- [Using programmatically](https://github.com/GoogleChrome/lighthouse/blob/main/docs/readme.md) · [Configuration](https://github.com/GoogleChrome/lighthouse/blob/main/docs/configuration.md)
- [User flows](https://github.com/GoogleChrome/lighthouse/blob/main/docs/user-flows.md) · [Puppeteer와 함께 쓰기](https://github.com/GoogleChrome/lighthouse/blob/main/docs/puppeteer.md) · [Authenticated pages](https://github.com/GoogleChrome/lighthouse/blob/main/docs/authenticated-pages.md)
- [Throttling](https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md) · [Variability](https://github.com/GoogleChrome/lighthouse/blob/main/docs/variability.md) · [Scoring](https://github.com/GoogleChrome/lighthouse/blob/main/docs/scoring.md)
- [Architecture](https://github.com/GoogleChrome/lighthouse/blob/main/docs/architecture.md)
- [Lighthouse CI Getting Started](https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/getting-started.md) · [LHCI Configuration](https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md)
- [Changelog](https://github.com/GoogleChrome/lighthouse/blob/main/changelog.md) · [v13.5.0 릴리스](https://github.com/GoogleChrome/lighthouse/releases/tag/v13.5.0)
- [Lighthouse Viewer](https://googlechrome.github.io/lighthouse/viewer/)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
