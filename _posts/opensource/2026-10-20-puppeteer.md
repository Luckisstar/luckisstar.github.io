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
- **현황 (2026-10-20 기준):** GitHub 스타 약 9.6만 개

## 한 줄 요약

**JavaScript 코드로 브라우저를 사람처럼 조작하는 라이브러리**입니다. Google Chrome 팀이 관리하며, 페이지 열기, 클릭, 입력, 스크린샷, PDF 저장 같은 작업을 자동화할 수 있습니다.

## 무엇을 해주나

- **DevTools Protocol** 또는 **WebDriver BiDi** 표준으로 Chrome·Firefox를 제어합니다.
- 기본적으로 화면 없이(headless) 실행되므로 서버나 CI에서 쓰기 좋습니다.
- 주로 이런 곳에 씁니다.
  - 웹 앱 E2E 테스트
  - 웹페이지 스크린샷·PDF 생성
  - 웹 크롤링, 반복 작업 자동화
  - 페이지 로딩 성능 측정
- Puppeteer 기반 MCP 서버인 [chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp)를 쓰면 AI 에이전트가 브라우저를 조작하게 할 수도 있습니다.

## 빠르게 시작하기

```bash
npm i puppeteer        # 호환되는 Chrome까지 함께 내려받음
npm i puppeteer-core   # 브라우저 없이 라이브러리만 설치
```

최근 npm, pnpm, Yarn, Bun 등은 설치 스크립트를 기본으로 막기 때문에 Chrome이 자동으로 받아지지 않을 수 있습니다. 그럴 때는 아래 명령으로 직접 받으면 됩니다.

```bash
npx puppeteer browsers install
```

**예시: 페이지를 열고 검색 결과 제목 가져오기**

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

## 이런 분께 추천

- Node.js로 브라우저 테스트나 스크래핑을 하려는 분
- 웹페이지를 이미지·PDF로 자동 변환해야 하는 분
- 여러 브라우저(Chromium, Firefox, WebKit)를 함께 테스트해야 한다면 비슷한 도구인 Playwright도 같이 비교해보면 좋습니다.

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
