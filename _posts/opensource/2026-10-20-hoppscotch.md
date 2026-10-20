---
layout: default
title: "[오픈소스 소개] Hoppscotch: 가볍고 빠른 오픈소스 Postman 대안"
date: 2026-10-20
categories: [opensource]
---

# [오픈소스 소개] Hoppscotch: 가볍고 빠른 오픈소스 Postman 대안

- **저장소:** [hoppscotch/hoppscotch](https://github.com/hoppscotch/hoppscotch) · [hoppscotch.io](https://hoppscotch.io) · [문서](https://docs.hoppscotch.io)
- **라이선스:** MIT
- **언어:** TypeScript
- **현황 (2026-10-20 기준):** GitHub 스타 약 8.1만 개, 최신 릴리스 2026.9.0

## 한 줄 요약

**API 요청을 보내고 테스트하는 도구**입니다. Postman이나 Insomnia의 오픈소스 대안이며, 웹·데스크톱·CLI로 쓸 수 있고 직접 서버에 설치(셀프 호스팅)할 수도 있습니다.

## 주요 기능

- **가볍고 빠름:** 단순한 UI로 요청을 보내면 응답을 바로 확인할 수 있습니다.
- **다양한 프로토콜:** REST뿐 아니라 GraphQL, WebSocket, Server-Sent Events, Socket.IO, MQTT까지 지원합니다.
- **인증:** Basic, Bearer Token, OAuth 2.0, OIDC/PKCE
- **요청 편의 기능**
  - cURL 명령 가져오기
  - 10개 이상 언어·프레임워크용 코드 스니펫 생성
  - 요청 전에 실행되는 JavaScript 스크립트(Pre-Request Script)로 환경 변수나 타임스탬프 설정
- **컬렉션:** 요청을 폴더로 정리하고 파일이나 GitHub Gist로 내보내기·가져오기
- **팀 협업:** 팀, 공유 컬렉션, 역할 기반 권한 관리
- **PWA 지원:** 브라우저에서 앱처럼 설치해 오프라인으로도 쓸 수 있습니다.

## 빠르게 시작하기

- **웹:** [hoppscotch.io](https://hoppscotch.io)에 접속하면 설치 없이 바로 쓸 수 있습니다.
- **데스크톱 앱:** Windows, macOS, Linux용 [데스크톱 앱](https://docs.hoppscotch.io/documentation/clients/desktop) 제공
- **CLI:** 컬렉션을 터미널이나 CI에서 실행하는 [Hoppscotch CLI](https://github.com/hoppscotch/hoppscotch/tree/main/packages/hoppscotch-cli) 제공
- **셀프 호스팅:** 사내 서버에 설치하려면 [셀프 호스팅 문서](https://docs.hoppscotch.io/documentation/self-host/getting-started)를 참고하세요.

## 이런 분께 추천

- Postman이 무겁게 느껴지거나 로그인 없이 가볍게 API를 테스트하고 싶은 분
- API 데이터를 외부 클라우드에 두기 어려워 사내에 직접 설치해야 하는 팀
- WebSocket, MQTT 같은 실시간 프로토콜도 한 도구로 테스트하고 싶은 분

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
