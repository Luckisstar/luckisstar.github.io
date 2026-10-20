---
layout: default
title: "[오픈소스 소개] Puppeteer: 코드로 Chrome·Firefox를 조종하는 브라우저 자동화 라이브러리"
date: 2026-10-20
categories: [opensource]
---

# [오픈소스 소개] Puppeteer: 코드로 Chrome·Firefox를 조종하는 브라우저 자동화 라이브러리

- **저장소:** [puppeteer/puppeteer](https://github.com/puppeteer/puppeteer) · [공식 문서 pptr.dev](https://pptr.dev)
- **라이선스:** Apache 2.0
- **언어:** TypeScript
- **현황 (2026-10-20 기준):** GitHub 스타 약 9.6만 개, 최신 릴리스 v25.14.0 (10월 14일)

## 한 줄 요약

**Node.js 코드로 실제 브라우저를 사람처럼 조작하는 라이브러리**입니다. Chrome 브라우저 자동화 팀이 직접 관리하며, 페이지 열기, 클릭, 입력, 스크린샷, PDF 저장, 네트워크 가로채기까지 브라우저로 할 수 있는 일 대부분을 스크립트로 만들 수 있습니다. 2026-10-20 기준 최신 버전은 `puppeteer` v25.14.0(2026-10-14 배포)입니다.

## 어떤 문제를 푸나

웹 페이지를 다루는 작업 중에는 HTTP 요청만으로는 해결되지 않는 일이 많습니다.

- JavaScript가 그려야 내용이 보이는 SPA(Single-Page Application) 페이지를 크롤링해야 할 때
- HTML 템플릿으로 만든 견적서·리포트를 **브라우저 렌더링 결과 그대로** PDF로 뽑아야 할 때
- 로그인, 폼 입력, 버튼 클릭이 이어지는 흐름을 매번 손으로 확인하기 번거로울 때
- 배포 후 주요 페이지가 깨지지 않았는지 스크린샷으로 남겨 두고 싶을 때

이런 일은 결국 "진짜 브라우저를 띄워서 조작"해야 합니다. Puppeteer는 브라우저를 별도 프로세스로 띄우고, 그 브라우저가 제공하는 자동화 프로토콜로 명령을 보내는 방식으로 이 문제를 풉니다. 공식 문서는 "브라우저에서 손으로 할 수 있는 일 대부분을 Puppeteer로 할 수 있다"고 설명합니다.

FAQ에 따르면 프로젝트의 목표는 Chrome DevTools Protocol과 WebDriver BiDi의 **레퍼런스 구현**이 되는 것이고, 원칙으로 속도(자동화 오버헤드가 거의 없음), 보안(브라우저 밖 프로세스에서 동작), 안정성, 단순함을 내세웁니다.

## 핵심 개념 / 동작 원리

### 구조

```
 Node.js 스크립트
   │  (Puppeteer API: launch, newPage, click...)
   ▼
 puppeteer-core
   │  CDP 또는 WebDriver BiDi (WebSocket/pipe)
   ▼
 브라우저 프로세스 (Chrome / Firefox)
   └─ BrowserContext ─ Page ─ Frame ─ Element
```

- **CDP(Chrome DevTools Protocol):** Chrome 개발자 도구가 브라우저와 통신할 때 쓰는 프로토콜입니다. Chrome을 자동화할 때 기본값입니다.
- **WebDriver BiDi:** W3C에서 표준화 중인 양방향 브라우저 자동화 프로토콜입니다. Firefox 자동화의 기본값이며, Chrome에서도 `protocol: 'webDriverBiDi'`로 쓸 수 있습니다. v23.0.0부터 Chrome과 Firefox 모두 정식 지원합니다.
- 공식 FAQ는 BiDi를 지원하더라도 **CDP 지원을 중단하지 않겠다**고 밝히고 있습니다. Chrome에만 있는 기능 때문입니다.

### 객체 계층

| 객체 | 역할 |
| --- | --- |
| `Browser` | 실행 중인 브라우저 하나. `puppeteer.launch()`나 `connect()`로 얻습니다. |
| `BrowserContext` | 쿠키·저장소가 분리된 세션 단위(시크릿 창과 비슷). |
| `Page` | 탭 하나. 대부분의 작업이 여기서 일어납니다. |
| `Frame` | 페이지 안의 iframe을 포함한 문서 단위. |
| `Locator` | "어떤 요소를 어떻게 찾을지"를 담은 객체. 자동 대기를 해 줍니다. |
| `ElementHandle` | 실제 DOM 요소를 가리키는 저수준 핸들. |

### `puppeteer`와 `puppeteer-core`

v1.7.0부터 두 패키지가 함께 배포됩니다.

| 패키지 | 성격 | 브라우저 다운로드 | 설정 파일·환경 변수 |
| --- | --- | --- | --- |
| `puppeteer` | 바로 쓰는 "제품" | 설치 시 Chrome for Testing 자동 다운로드 | 적용됨 |
| `puppeteer-core` | 순수 "라이브러리" | 하지 않음 | 무시됨 |

원격 브라우저에 `connect()`로 붙거나 브라우저를 직접 관리한다면 `puppeteer-core`를 쓰고, `executablePath` 또는 `channel`을 명시해야 합니다.

### 브라우저 버전이 고정되는 이유

Puppeteer 각 릴리스는 특정 브라우저 버전과 짝을 이룹니다. 프로토콜 구현이 브라우저 버전마다 달라질 수 있기 때문입니다. 그래서 기본으로는 **Chrome for Testing**(자동화용으로 배포되는 Chrome 빌드)을 내려받아 씁니다. 어느 버전이 짝인지는 저장소의 `packages/puppeteer-core/src/revisions.ts`에서 확인할 수 있습니다.

### Headless 모드

- 기본값은 화면 없이 도는 **Headless 모드**입니다(`headless: true`).
- v22 이전의 "옛 headless"는 이제 `chrome-headless-shell`이라는 별도 바이너리가 되었고, `headless: 'shell'`로 고를 수 있습니다. 일반 Chrome과 동작이 완전히 같지는 않지만 자동화 작업에서는 더 빠를 수 있습니다.
- 눈으로 보면서 디버깅하려면 `headless: false`로 띄웁니다.

## 주요 기능

### 페이지 조작

- **Locator API(권장):** `page.locator('button').click()`처럼 쓰면, 클릭 전에 요소가 뷰포트에 있는지, 보이는지, 활성화됐는지, 두 애니메이션 프레임 동안 위치가 안정적인지 자동으로 기다립니다.
- `fill()`은 입력 타입을 감지해서 `<input>`뿐 아니라 `<select>`도 채웁니다. `hover()`, `scroll()`, `wait()`도 있습니다.
- 함수로 로케이터를 만들어 "문단이 3개 이상 생길 때까지" 같은 임의 조건을 기다릴 수 있습니다.
- 요소 없이 바로 입력하려면 `page.mouse`, `page.keyboard`, `page.touchscreen`을 씁니다.
- Puppeteer가 만드는 입력 이벤트는 모두 **trusted 이벤트**(실제 사용자 입력과 같은 이벤트, `Event.isTrusted`가 true)이고 `mousedown`/`mouseup` 같은 동반 이벤트도 함께 발생합니다.

### 선택자 확장

CSS 선택자 외에 다음 문법을 지원합니다.

| 문법 | 의미 |
| --- | --- |
| `::-p-xpath(...)` | XPath |
| `::-p-text(...)` | 텍스트 내용으로 찾기 |
| `::-p-aria(...)` | 접근성 이름·역할로 찾기 |
| `pierce/` | Shadow DOM 안까지 관통 |
| `>>>`, `>>>>` | Shadow DOM 경계를 넘는 조합자 |

사용자 정의 선택자도 등록할 수 있습니다.

### 출력물 생성

- `page.screenshot()`: 페이지 스크린샷. `fullPage`, `clip`, `type`, `quality`, `omitBackground`, `encoding` 등의 옵션이 있습니다.
- `ElementHandle.screenshot()`: 특정 요소만 캡처. 요소가 가려져 있으면 스크롤해서 보이게 한 뒤 찍습니다.
- `page.pdf()`: 인쇄용 PDF. `format`, `margin`, `landscape`, `printBackground`, `displayHeaderFooter`, `headerTemplate`/`footerTemplate`, `pageRanges`, `scale`, `preferCSSPageSize`, 실험 기능인 `outline`(목차)과 `tagged`(접근성 태그 PDF) 옵션을 지원합니다. 기본적으로 폰트 로딩을 기다립니다.

### 네트워크

- `page.setRequestInterception(true)`로 모든 요청을 가로채 `continue()`, `abort()`, `respond()` 중 하나로 처리합니다.
- 여러 핸들러가 함께 가로챌 때를 위한 **Cooperative Intercept Mode**(우선순위 기반 처리)가 있습니다.
- 쿠키는 `browser.cookies()`, `browser.setCookie()`, `browser.deleteCookie()`로 직접 읽고 쓰며, `BrowserContext`에도 같은 메서드가 있습니다.

### 그 밖의 기능

- **성능 추적:** 타임라인 트레이스를 기록해 성능 문제를 분석할 수 있습니다.
- **Chrome 확장 프로그램 테스트**, 브라우저 안에서 Puppeteer 실행, 확장 프로그램 안에서 Puppeteer 실행 가이드가 따로 있습니다.
- **`@puppeteer/browsers`:** Chrome for Testing, ChromeDriver, Firefox 등을 내려받고 관리하는 CLI·라이브러리입니다.
- **WebMCP(실험):** 웹 페이지가 등록한 "도구"를 `page.webmcp`로 찾아 실행하는 실험 API입니다. Chrome 151 이상과 `--enable-features=WebMCP` 플래그가 필요합니다.
- Puppeteer 기반 MCP 서버인 [chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp)를 쓰면 AI 에이전트가 브라우저를 다루게 할 수도 있습니다.

## 설치와 시작

### 요구 사항

- Node.js 22.12 이상 (Puppeteer는 Node의 최신 maintenance LTS를 따릅니다)
- TypeScript를 쓴다면 5.0.1 이상
- Chrome for Testing: Windows x64, macOS x64/arm64, Debian/Ubuntu·openSUSE/Fedora x64/arm64
- 압축 해제용으로 Windows는 `tar.exe` 또는 PowerShell, macOS/Linux는 `unzip`이 필요합니다.

### 설치

```bash
npm i puppeteer        # Chrome for Testing + chrome-headless-shell 함께 다운로드
npm i puppeteer-core   # 라이브러리만 설치 (브라우저 다운로드 없음)
```

`puppeteer`를 설치하면 Chrome for Testing(macOS 약 170MB, Linux 약 282MB, Windows 약 280MB)과 `chrome-headless-shell`이 `~/.cache/puppeteer`에 내려받아집니다.

최근 npm(새 RFC 적용 시), pnpm, Yarn Berry, Bun, Deno는 의존성의 설치 스크립트를 기본으로 막습니다. 이 경우 브라우저 다운로드가 건너뛰어지고 실행 시 `Could not find Chrome (ver. ...)` 오류가 납니다. 해결 방법은 두 가지입니다.

```bash
# 1) 브라우저를 직접 설치
npx puppeteer browsers install
```

```json
{
  "allowScripts": {
    "puppeteer": true
  }
}
```

두 번째 방법은 npm 기준으로 `package.json`에 위 설정을 추가해 설치 스크립트를 다시 허용하는 것입니다.

### 첫 스크립트

```ts
import puppeteer from 'puppeteer';

const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.goto('https://developer.chrome.com/');
await page.setViewport({width: 1080, height: 1024});

await page.keyboard.press('/');                                   // 검색창 열기
await page.locator('::-p-aria(Search)').fill('automate beyond recorder');
await page.locator('.devsite-result-item-link').click();          // 첫 결과 클릭

const el = await page.locator('::-p-text(Customize and automate)').waitHandle();
console.log(await el?.evaluate(e => e.textContent));
await browser.close();
```

### 설정 파일

Puppeteer는 프로젝트 디렉터리부터 위로 올라가며 `.puppeteerrc.cjs`, `.puppeteerrc.json`, `puppeteer.config.js`, `package.json` 등에서 설정을 찾습니다. 환경 변수가 설정 파일보다 우선합니다. 예를 들어 Firefox도 함께 내려받으려면 다음처럼 씁니다(v23.0.0부터 지원).

```js
// .puppeteerrc.js
/** @type {import("puppeteer").Configuration} */
export default {
  chrome: {skipDownload: false},
  firefox: {skipDownload: false}, // 기본값은 true
};
```

다운로드 관련 설정을 바꾼 뒤에는 `npx puppeteer browsers install`을 다시 실행해야 반영됩니다.

## 실전 예제

### 1. HTML 템플릿을 A4 PDF 리포트로 만들기

서버에서 만든 HTML을 바로 PDF로 변환하고, 아래쪽에 페이지 번호를 넣는 예제입니다.

```ts
import puppeteer from 'puppeteer';

const html = `
  <html><body style="font-family: sans-serif">
    <h1>월간 리포트</h1>
    <p>본문 내용...</p>
  </body></html>`;

const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.setContent(html, {waitUntil: 'networkidle0'});

await page.pdf({
  path: 'report.pdf',
  format: 'A4',            // 기본값은 letter
  printBackground: true,   // 배경색·배경 이미지 출력
  margin: {top: '20mm', bottom: '20mm', left: '15mm', right: '15mm'},
  displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate:
    '<div style="font-size:9px;width:100%;text-align:center">' +
    '<span class="pageNumber"></span> / <span class="totalPages"></span>' +
    '</div>',
});

await browser.close();
```

`headerTemplate`과 `footerTemplate`에서는 `date`, `title`, `url`, `pageNumber`, `totalPages` 클래스를 가진 요소에 값이 채워집니다. `format`의 기본값이 미국 `letter` 용지라서, 국내 문서라면 `A4`를 꼭 지정하는 편이 좋습니다.

### 2. 전체 페이지 스크린샷과 요소 스크린샷

배포 후 랜딩 페이지 전체와 특정 영역을 이미지로 남기는 예제입니다.

```ts
import puppeteer from 'puppeteer';

const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.setViewport({width: 1440, height: 900});
await page.goto('https://example.com', {waitUntil: 'networkidle2'});

// 스크롤 영역까지 포함한 전체 페이지
await page.screenshot({path: 'full.png', fullPage: true});

// 특정 요소만
const header = await page.waitForSelector('h1');
await header?.screenshot({path: 'header.png'});

await browser.close();
```

`networkidle2`는 네트워크 연결이 2개 이하로 일정 시간 유지될 때까지 기다리는 옵션으로, 이미지가 늦게 뜨는 페이지에서 빈 화면이 찍히는 것을 줄여 줍니다.

### 3. 로그인 자동화와 쿠키 재사용

로그인 폼을 채워 제출하고, 받은 쿠키를 파일에 저장했다가 다음 실행에서 다시 넣어 로그인 과정을 건너뛰는 예제입니다. 선택자와 URL은 대상 사이트에 맞게 바꿔야 합니다.

```ts
import fs from 'node:fs/promises';
import puppeteer from 'puppeteer';

const browser = await puppeteer.launch();
const page = await browser.newPage();

try {
  // 저장된 쿠키가 있으면 먼저 복원
  const saved = JSON.parse(await fs.readFile('cookies.json', 'utf8'));
  await browser.setCookie(...saved);
} catch {
  // 처음 실행이면 로그인
  await page.goto('https://example.com/login');
  await page.locator('input[name=email]').fill(process.env.LOGIN_EMAIL);
  await page.locator('input[name=password]').fill(process.env.LOGIN_PASSWORD);
  await Promise.all([
    page.waitForNavigation(),
    page.locator('button[type=submit]').click(),
  ]);
  await fs.writeFile('cookies.json', JSON.stringify(await browser.cookies()));
}

await page.goto('https://example.com/dashboard');
console.log(await page.title());
await browser.close();
```

클릭과 `waitForNavigation()`을 `Promise.all`로 묶는 이유는, 클릭한 뒤에 대기를 시작하면 이미 이동이 끝나 버려 대기가 끝나지 않는 경쟁 상태가 생길 수 있기 때문입니다. 비밀번호는 코드에 넣지 말고 환경 변수로 넘깁니다.

### 4. 네트워크 가로채기: 이미지 차단과 API 응답 목킹

크롤링 속도를 높이려고 이미지·폰트를 막고, 테스트용으로 특정 API 응답을 가짜 데이터로 바꾸는 예제입니다.

```ts
import puppeteer from 'puppeteer';

const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.setRequestInterception(true);

page.on('request', req => {
  if (req.isInterceptResolutionHandled()) return;

  const type = req.resourceType(); // CDP 전용 API
  if (type === 'image' || type === 'font') {
    req.abort();
    return;
  }
  if (req.url().endsWith('/api/me')) {
    req.respond({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({name: '테스트 사용자'}),
    });
    return;
  }
  req.continue();
});

await page.goto('https://example.com');
await browser.close();
```

인터셉션을 켜면 **모든 요청이 멈추고** 핸들러가 `continue`/`abort`/`respond` 중 하나를 호출해야 진행됩니다. 처리가 끝난 요청을 다시 처리하면 `Request is already handled!` 예외가 나므로, 공식 가이드처럼 `isInterceptResolutionHandled()`를 먼저 확인하는 습관을 들이는 것이 좋습니다. `resourceType()`은 WebDriver BiDi에서는 지원되지 않습니다.

### 5. CI와 Docker에서 실행하기

Puppeteer는 Chrome for Testing과 의존성이 미리 설치된 공식 Docker 이미지를 GitHub Container Registry로 제공합니다.

```bash
docker pull ghcr.io/puppeteer/puppeteer:latest

docker run -i --init --cap-add=SYS_ADMIN --rm \
  ghcr.io/puppeteer/puppeteer:latest \
  node -e "$(cat path/to/script.js)"
```

- 이미지는 브라우저를 샌드박스 모드로 돌리도록 만들어져 있어서 `SYS_ADMIN` 권한이 필요합니다.
- `--init`(또는 직접 지정한 `ENTRYPOINT`)으로 init 프로세스를 두어야 Puppeteer가 띄운 하위 프로세스가 좀비로 남지 않습니다.
- 태그는 Puppeteer 버전과 맞춰져 있어서 `ghcr.io/puppeteer/puppeteer:<버전>`으로 고정할 수 있습니다.

GitHub Actions처럼 일반 리눅스 러너에서 직접 돌린다면 대략 이런 흐름입니다.

```yaml
# .github/workflows/e2e.yml
name: e2e
on: [push]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npx puppeteer browsers install
      - run: node scripts/smoke-test.mjs
```

러너 환경에 따라 아래 "자주 겪는 문제"의 샌드박스·의존성 문제가 생길 수 있으니, 막히면 공식 Docker 이미지를 쓰는 쪽이 가장 확실합니다.

## 실무 팁 & 자주 겪는 문제

공식 [Troubleshooting](https://pptr.dev/troubleshooting) 문서에서 실무에서 자주 만나는 항목을 골랐습니다.

| 증상 | 원인과 해결 |
| --- | --- |
| `Could not find Chrome` / `Could not find expected browser locally` | 설치 스크립트가 막혔거나 캐시 위치(`~/.cache/puppeteer`)가 다릅니다. `npx puppeteer browsers install`을 실행하거나, `PUPPETEER_CACHE_DIR` 환경 변수 또는 설정 파일의 `cacheDirectory`로 위치를 지정합니다. |
| 빌드 산출물을 다른 곳으로 옮기니 브라우저를 못 찾음 | 브라우저는 홈 디렉터리 캐시에 있기 때문입니다. `.puppeteerrc.js`에서 `cacheDirectory`를 프로젝트 안(`.cache/puppeteer`)으로 바꾸고 다시 설치합니다. |
| 리눅스에서 Chrome이 안 뜸 | 공유 라이브러리가 빠졌을 가능성이 큽니다. Chrome 바이너리에 `ldd`를 돌려 `not found`로 표시되는 라이브러리를 찾아 설치합니다. |
| `No usable sandbox!` | 호스트에 쓸 만한 샌드박스가 없습니다. Ubuntu 23.10 이상은 AppArmor 정책 때문에 생길 수 있습니다. `--no-sandbox`는 **완전히 신뢰하는 콘텐츠**에만 쓰고, 가능하면 샌드박스를 제대로 구성하라고 문서가 강하게 권합니다. |
| 읽기 전용 컨테이너에서 `chrome_crashpad_handler: --database is required` | Chrome이 설정·캐시를 쓸 곳이 없습니다. `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`을 `/tmp/.chromium`으로, `userDataDir`을 쓰기 가능한 경로로 지정합니다. |
| HTTP 사이트 이동 시 `net::ERR_BLOCKED_BY_CLIENT` | Chrome의 `HttpsFirstBalancedModeAutoEnable` 기능 때문입니다. `--disable-features=HttpsFirstBalancedModeAutoEnable` 인자로 끌 수 있습니다. |
| Windows에서 Chrome이 실행되지 않음 | 확장 프로그램 강제 정책과 Puppeteer 기본 인자 `--disable-extensions`가 충돌합니다. `enableExtensions: true`로 띄웁니다. |
| Alpine에서 타임아웃 | Chrome은 Alpine을 공식 지원하지 않으며, 문서에는 Alpine 3.20의 Chromium에서 타임아웃 문제가 있어 3.19로 내리면 해결된다고 적혀 있습니다. |
| `chrome-headless-shell`에서 GPU가 꺼짐 | `headless: 'shell'`과 함께 `args: ['--enable-gpu']`를 넘깁니다. |

디버깅 요령도 몇 가지 기억해 두면 좋습니다.

- `headless: false`와 `slowMo: 250`을 함께 주면 동작을 눈으로 따라갈 수 있습니다.
- 페이지 안의 `console.log`는 Node 터미널에 찍히지 않습니다. `page.on('console', msg => ...)`로 받아야 합니다.
- 프로토콜 수준까지 의심된다면 `env NODE_DEBUG="puppeteer:*" node script.js`로 내부 통신을 로그로 볼 수 있습니다. 로그에 민감한 정보가 들어갈 수 있으니 주의합니다.
- 직접 `element.click()`을 `page.evaluate`로 호출하면 untrusted 이벤트가 되어, 일부 사이트는 사람이 아닌 입력으로 판단할 수 있습니다. 가능하면 Locator나 `page.mouse`를 씁니다.
- SPA에서 History API로 URL만 바뀌는 것도 Puppeteer는 "내비게이션"으로 취급합니다.

## 비슷한 도구와 비교

| 항목 | Puppeteer | Playwright | Selenium |
| --- | --- | --- | --- |
| 주도 | Google Chrome 팀 | Microsoft | Selenium 프로젝트(커뮤니티, W3C WebDriver 표준 주도) |
| 언어 | JavaScript/TypeScript | JS/TS, Python, Java, .NET | Java, Python, C#, JS, Ruby 등 다수 |
| 브라우저 | Chrome, Firefox | Chromium, Firefox, WebKit | 주요 브라우저 전반(드라이버 사용) |
| 프로토콜 | CDP, WebDriver BiDi | 브라우저별 자체 프로토콜 연결 | WebDriver Classic, BiDi 확대 중 |
| 테스트 러너 | 없음(Jest 등과 조합) | 전용 러너 `@playwright/test` 내장 | 없음(각 언어 테스트 프레임워크와 조합) |
| 대규모 분산 실행 | 범위 밖 | 러너의 병렬·샤딩 기능 | Selenium Grid |
| 강점 | Chrome 최신 기능·CDP 직접 접근, 가벼운 API | 크로스 브라우저 E2E 테스트 생산성 | 언어·브라우저 폭, 오래된 생태계 |

공식 FAQ도 Selenium은 여러 언어 바인딩과 Selenium Grid 같은 대규모 오케스트레이션 도구를 제공하며 이는 Puppeteer의 범위 밖이라고 직접 설명합니다. Playwright 쪽 정보는 일반적으로 알려진 내용 기준이므로, 도입 전에는 각 공식 문서에서 최신 지원 범위를 확인하는 것이 좋습니다.

## 장점과 한계

**장점**

- Chrome 팀이 직접 관리해서 새 Chrome 기능과 CDP를 가장 빨리, 가장 직접적으로 쓸 수 있습니다.
- `npm i puppeteer` 하나로 검증된 브라우저까지 받아지므로 시작이 쉽습니다.
- PDF, 스크린샷, 네트워크 가로채기, 쿠키, 성능 트레이스처럼 "브라우저를 도구로 쓰는" 기능이 풍부합니다.
- Locator의 자동 대기 덕분에 타이밍 문제로 깨지는 스크립트가 줄어듭니다.
- 공식 Docker 이미지로 CI·서버 배포가 비교적 단순합니다.

**한계**

- 공식 API는 JavaScript/TypeScript뿐입니다.
- WebKit(Safari 엔진)은 지원하지 않습니다.
- 테스트 러너, 리포트, 병렬 실행 같은 E2E 테스트 편의 기능은 직접 조합해야 합니다.
- WebDriver BiDi로는 아직 일부 API(각종 emulate 계열, `resourceType()`, `createCDPSession()` 등)가 지원되지 않아 `UnsupportedOperation` 오류가 납니다.
- 브라우저 바이너리 크기(수백 MB)와 리눅스 의존성, 샌드박스 설정이 서버 환경에서 진입 장벽이 됩니다.

## 이런 분께 추천 / 이런 경우엔 다른 도구

**추천**

- Node.js 서버에서 HTML을 PDF·이미지로 바꾸는 기능이 필요한 분
- JavaScript로 렌더링되는 페이지를 크롤링하거나 반복 업무를 자동화하려는 분
- Chrome 전용 기능(CDP, 확장 프로그램, 성능 추적)을 깊게 다뤄야 하는 분
- AI 에이전트에게 브라우저 조작 능력을 붙이려는 분(chrome-devtools-mcp, WebMCP 실험 API)

**다른 도구가 나은 경우**

- Safari(WebKit)까지 포함한 크로스 브라우저 E2E 테스트를 체계적으로 돌려야 한다면 Playwright가 더 편합니다.
- Python, Java 등 다른 언어로 자동화해야 하거나 Selenium Grid 같은 대규모 분산 실행이 필요하다면 Selenium이 맞습니다.
- 정적 HTML만 긁으면 되는 크롤링이라면 브라우저 없이 HTTP 클라이언트와 HTML 파서로 하는 편이 훨씬 가볍습니다.

## 참고 링크

- [What is Puppeteer?](https://pptr.dev/guides/what-is-puppeteer)
- [Installation](https://pptr.dev/guides/installation) · [System requirements](https://pptr.dev/guides/system-requirements)
- [Configuration](https://pptr.dev/guides/configuration) · [Headless mode](https://pptr.dev/guides/headless-modes)
- [Page interactions](https://pptr.dev/guides/page-interactions)
- [Screenshots](https://pptr.dev/guides/screenshots) · [PDF generation](https://pptr.dev/guides/pdf-generation) · [PDFOptions API](https://pptr.dev/api/puppeteer.pdfoptions)
- [Request Interception](https://pptr.dev/guides/network-interception) · [Cookies](https://pptr.dev/guides/cookies)
- [Docker](https://pptr.dev/guides/docker) · [Debugging](https://pptr.dev/guides/debugging)
- [WebDriver BiDi support](https://pptr.dev/webdriver-bidi) · [WebMCP](https://pptr.dev/guides/webmcp)
- [@puppeteer/browsers](https://pptr.dev/browsers-api)
- [FAQ](https://pptr.dev/faq) · [Troubleshooting](https://pptr.dev/troubleshooting)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
