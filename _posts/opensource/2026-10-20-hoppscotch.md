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

**API 요청을 만들고 보내고 테스트하는 오픈소스 API 개발 도구**입니다. Postman, Insomnia의 대안으로, 브라우저에서 바로 쓰는 웹 앱, 데스크톱 앱, CI용 CLI를 제공하고 사내 서버에 직접 설치(셀프 호스팅)할 수도 있습니다.

## 어떤 문제를 푸나

API를 개발하거나 연동하다 보면 "이 엔드포인트에 이 헤더로 요청하면 뭐가 오지?"를 수없이 확인하게 됩니다. curl로도 되지만 요청이 수십 개로 늘고, 개발·스테이징·운영 환경을 오가고, 팀원과 같은 요청 모음을 공유해야 하면 금방 한계가 옵니다.

Postman 같은 GUI 도구가 이 문제를 풀어 주지만 다음과 같은 불편을 느끼는 경우가 많습니다.

- 앱이 무겁고 기능이 많아 단순한 요청 확인에도 시간이 걸린다.
- 요청·환경 변수 같은 API 데이터를 외부 클라우드에 올리기 어렵다(보안 정책).
- 팀 기능을 쓰려면 사용자 수만큼 비용이 든다.

Hoppscotch는 공식 FAQ의 표현대로 "Postman, Insomnia, Paw의 웹 기반 대안"을 목표로 합니다. 설치 없이 [hoppscotch.io](https://hoppscotch.io)에서 바로 쓸 수 있고, 필요하면 MIT 라이선스의 Community Edition을 Docker로 사내에 띄워 데이터를 직접 소유할 수 있습니다.

## 핵심 개념 / 동작 원리

### 클라이언트 구성

```
         ┌─ 웹 앱 (hoppscotch.io / PWA)
 사용자 ─┼─ 데스크톱 앱 (Tauri 기반)
         ├─ CLI (@hoppscotch/cli, CI용)
         └─ MCP 서버 (AI 에이전트용)
                 │
                 ▼  로그인 시 동기화
     Hoppscotch Cloud 또는 셀프 호스팅 서버
     (frontend / backend / admin + Postgres)
```

- **웹 앱:** 브라우저에서 동작합니다. 브라우저 안에서 요청을 보내므로 **CORS**(다른 출처의 요청을 브라우저가 막는 보안 정책) 제약을 받습니다.
- **데스크톱 앱:** 웹 클라이언트 위에 [Tauri](https://tauri.app)로 만든 앱입니다. CORS 제약을 받지 않습니다.
- **CLI:** 컬렉션을 터미널이나 CI에서 실행하고 테스트 결과를 종료 코드와 JUnit 리포트로 돌려줍니다.
- **MCP 서버:** AI 에이전트가 컬렉션·환경을 읽고 실제 요청을 보낼 수 있게 해 줍니다.

### 인터셉터: 웹 앱에서 CORS를 우회하는 방법

웹 앱에서 요청이 CORS에 막히면 **인터셉터**(요청을 브라우저 대신 보내 주는 중계 방식)를 고릅니다. 설정(Settings)의 Interceptors 항목에서 바꿉니다.

| 인터셉터 | 동작 방식 |
| --- | --- |
| Hoppscotch Agent | 내 PC에 설치하는 작은 앱. 요청을 로컬 네트워크 설정으로 대신 보냅니다. 문서가 대부분의 사용자에게 권장합니다. |
| Proxy (Proxyscotch) | 원격 프록시 서버를 거쳐 보냅니다. 공식 프록시 Proxyscotch를 직접 호스팅할 수도 있습니다. |
| Browser Extension | 브라우저 확장 프로그램이 요청을 가로채 보냅니다. |

### 작업 단위

| 개념 | 설명 |
| --- | --- |
| 요청(Request) | 메서드, URL, 파라미터, 헤더, 바디, 인증, 스크립트를 묶은 단위 |
| 컬렉션(Collection) | 요청을 폴더 구조로 정리한 묶음. 가져오기·내보내기의 단위 |
| 환경(Environment) | 변수 묶음. 개발/스테이징/운영처럼 값만 바꿔 같은 요청을 재사용 |
| 워크스페이스(Workspace) | 개인 워크스페이스와 팀 공유 워크스페이스. Owner/Editor/Viewer 역할 |

### 변수와 우선순위

변수는 `<<변수명>>`처럼 꺾쇠 두 개로 감싸 씁니다. 같은 이름이 여러 범위에 있으면 아래 순서로 결정됩니다(숫자가 작을수록 우선).

| 범위 | 우선순위 | 용도 |
| --- | --- | --- |
| Request | 1 | 요청 하나에만 쓰는 값(예: URL 경로 변수) |
| Collection | 2 | 컬렉션과 하위 폴더 공통 값(base URL, 기본 토큰) |
| Predefined | 3 | `$guid`, `$timestamp`, `$randomUUID` 같은 자동 생성 값 |
| Environment | 4 | 선택한 환경의 값 |
| Global | 5 | 어디서나 쓰는 값 |

변수 이름 색상으로 어느 범위에서 왔는지 구분할 수 있고, 풀리지 않는 변수는 빨간색으로 표시됩니다.

또 하나 중요한 구분은 **일반 변수와 시크릿 변수**입니다.

- **일반 변수:** 공유 워크스페이스에서는 서버에 동기화되어 팀원 모두가 값을 봅니다.
- **시크릿 변수:** 값이 서버에 절대 동기화되지 않고, 화면에서 `***`로 가려지며, 환경을 내보낼 때도 값이 빠집니다. 각자 실행 시점에 값을 채워야 합니다.

변수에는 처음 만들 때의 **Initial Value**와 실행 중 바뀌는 **Current Value**가 따로 있습니다.

## 주요 기능

### 프로토콜

- **REST**: 메서드, 쿼리 파라미터, 헤더, 바디(파일 업로드 포함), 응답 확인
- **GraphQL**: 쿼리 작성과 변수 사용
- **실시간(Realtime)**: WebSocket, Server-Sent Events, Socket.IO, MQTT

참고로 공유 워크스페이스에서 요청을 정리·협업하는 기능은 현재 REST에만 해당하고, GraphQL과 Realtime은 개인 워크스페이스에서만 쓸 수 있습니다.

### 인증

Inherit(상위 컬렉션 설정 상속), Basic Auth, Bearer Token, API Key, OAuth 2.0(Authorization Code, Client Credentials, Password Credentials, Implicit), Digest, AWS Signature, JWT를 지원합니다. 컬렉션 단위로 인증을 설정해 하위 요청이 상속하게 할 수 있습니다.

### 스크립트와 테스트

- **Pre-request Script:** 요청 전에 JavaScript를 실행해 변수를 만들거나 헤더를 바꿉니다.
- **Post-request Test:** 응답을 받은 뒤 검증 코드를 실행합니다.
- 스크립트 API는 세 가지입니다.
  - `pw`: 기존(Legacy) API. `pw.env.set`, `pw.expect(...).toBe`, `pw.test`
  - `hopp`: 새 실험(Experimental) API. `hopp.env`, `hopp.request.setHeader`, `hopp.response.body.asJSON()`, `hopp.cookies`, Chai.js 스타일 단언
  - `pm`: Postman 호환 계층. `pm.environment`, `pm.response.json()`, `pm.test`, `pm.sendRequest`
- 문서는 실험 샌드박스가 현재 기본값이지만 **앞으로 깨지는 변경이 예정되어 있으니 기존 스크립트를 새 API로 서둘러 옮기지 말라**고 안내합니다.

### 컬렉션 실행과 자동화

- **Runner:** 컬렉션 안의 요청을 순서대로 실행합니다. 요청 간 지연, 오류 시 중단, 응답 저장, 실행 중 바뀐 변수 유지 옵션이 있습니다.
- **CLI `hopp test`:** 같은 컬렉션을 터미널·CI에서 실행합니다. 반복 실행(`--iteration-count`), CSV 데이터 주입(`--iteration-data`), JUnit 리포트(`--reporter-junit`)를 지원합니다.
- **Mock 서버:** 코드 없이 목(mock) 서버를 만들어 정해진 응답, 상태 코드, 지연을 돌려줍니다. 기존 컬렉션에서 바로 만들 수도 있습니다.

### 가져오기와 공유

- Postman, Insomnia 컬렉션·환경, OpenAPI(파일 또는 URL), HAR 파일을 가져올 수 있습니다.
- Postman v2.0/v2.1 컬렉션은 pre-request·테스트 스크립트까지 실험적으로 가져옵니다(가져올 때 동의 필요).
- cURL 명령 가져오기, 여러 언어용 코드 스니펫 생성 기능이 있습니다.

### 그 밖의 기능

- 팀 워크스페이스, 역할 기반 권한, 공유 환경
- 히스토리, Spotlight 검색, 단축키, 테마 등 사용자 지정
- PWA(Progressive Web App)로 브라우저에서 앱처럼 설치
- AI 기능과 MCP 서버(Node.js 22 이상, `npm install -g @hoppscotch/mcp-server`)

## 설치와 시작

### 웹·데스크톱

- **웹:** [hoppscotch.io](https://hoppscotch.io)에 접속하면 바로 씁니다. 로그인은 동기화와 팀 기능이 필요할 때만 하면 됩니다.
- **데스크톱:** [다운로드 페이지](https://hoppscotch.com/download)나 문서의 링크에서 macOS(Apple Silicon/Intel), Windows(msi/포터블), Linux(deb/AppImage)용을 받습니다. 데스크톱 버전 번호는 연도 뒷자리를 쓰므로 `26.6.0`은 `2026.6.0` 릴리스의 데스크톱 빌드입니다.

### CLI

CLI는 현재 **알파** 단계입니다. Node.js v22 이상이 필요하고, 네이티브 모듈 빌드를 위해 `node-gyp` 관련 도구가 있어야 합니다.

```bash
# Debian/Ubuntu 계열 사전 준비
sudo apt-get install python g++ build-essential

# CLI 설치
npm i -g @hoppscotch/cli
hopp -v
```

Alpine은 `sudo apk add python3 make g++`, Windows·macOS는 node-gyp 설치 안내를 따르면 됩니다. Node.js 20을 계속 써야 한다면 CLI `v0.26.0`과 앱 `v2025.10.1` 조합을 쓸 수 있다고 문서에 적혀 있습니다.

### 셀프 호스팅 준비물

Community Edition(CE) 기준 요구 사항입니다.

- Docker v20 이상(Compose V2 권장), Git, Postgres 데이터베이스
- 빌드할 때 4코어·4GB RAM, 실행만 할 때는 1코어·2GB RAM 정도
- 직접 빌드한다면 Node.js v18 이상, npm v9 이상, pnpm v6 이상
- 로그인용 OAuth(Email, GitHub, Google, Microsoft) 중 하나 이상
- 팀 초대 메일을 보내려면 SMTP 설정(선택)

## 실전 예제

### 1. 환경 변수로 개발·운영 환경 전환하기

같은 요청을 환경만 바꿔 재사용하는 가장 기본적인 패턴입니다. 요청 URL과 헤더를 변수로 씁니다.

```
GET <<base_url>>/v1/users/<<user_id>>
Authorization: Bearer <<access_token>>
X-Request-Id: <<$guid>>
```

환경은 두 개를 만들어 둡니다.

| 변수 | dev 환경 | prod 환경 | 종류 |
| --- | --- | --- | --- |
| `base_url` | `https://dev-api.example.com` | `https://api.example.com` | 일반 |
| `user_id` | `1` | `1` | 일반 |
| `access_token` | (각자 입력) | (각자 입력) | 시크릿 |

오른쪽 위 환경 선택기만 바꾸면 같은 요청이 다른 서버로 갑니다. 토큰은 시크릿 변수로 두면 팀 워크스페이스에 공유해도 값이 서버로 올라가지 않습니다. `$guid`는 요청마다 새로 생성되는 미리 정의된 변수입니다.

CLI에서 쓰려면 앱에서 환경을 내보낸 JSON을 그대로 씁니다.

```json
{
  "name": "dev",
  "variables": [
    { "key": "base_url", "value": "https://dev-api.example.com" },
    { "key": "user_id", "value": "1" }
  ]
}
```

### 2. 로그인 토큰을 받아 다음 요청에 자동으로 넣기

로그인 API의 Tests 탭에서 응답의 토큰을 환경 변수에 저장하고, 이후 요청은 `<<access_token>>`으로 그 값을 씁니다. 문서가 안내하는 `pw` API로 작성했습니다.

```javascript
// [로그인 요청] Tests 탭
pw.test("로그인 성공", () => {
  pw.expect(pw.response.status).toBe(200);
  pw.expect(pw.response.body.access_token).toBeType("string");
});

// 다음 요청에서 <<access_token>>으로 사용
pw.env.set("access_token", pw.response.body.access_token);
```

요청 전에 값을 계산해야 할 때는 Pre-request Script 탭을 씁니다. 예를 들어 서명용 타임스탬프를 만들 수 있습니다.

```javascript
// [주문 조회 요청] Pre-request Script 탭
pw.env.set("req_ts", Date.now().toString());
```

새 `hopp` API로는 같은 일을 이렇게 씁니다. 다만 위에서 말했듯 아직 바뀔 수 있는 실험 API입니다.

```javascript
// Tests 탭 (hopp API)
hopp.test("주문 목록 응답 검증", () => {
  hopp.expect(hopp.response.statusCode).toBeLevel2xx();
  const data = hopp.response.body.asJSON();
  hopp.expect(data).to.have.property("items");
  hopp.expect(hopp.response.responseTime).to.be.below(500);
});
```

Postman에서 옮겨 온 스크립트라면 `pm.test`, `pm.expect`, `pm.environment.set`도 동작합니다. 단 `pm.collectionVariables`, `pm.iterationData`, `pm.execution.setNextRequest()`, `pm.visualizer`, `require()`는 아직 지원되지 않습니다.

### 3. CLI로 컬렉션을 CI에서 실행하기

앱에서 컬렉션과 환경을 JSON으로 내보내 저장소에 넣어 두고, 배포 파이프라인에서 API 회귀 테스트를 돌리는 예제입니다.

```bash
# 로컬 파일로 실행
hopp test -e env/dev.json collections/orders.json

# 요청 사이에 1초 지연, JUnit 리포트 생성
hopp test -e env/dev.json -d 1000 collections/orders.json \
  --reporter-junit reports/hopp-junit.xml

# CSV 데이터로 3회 반복 실행
hopp test collections/orders.json \
  --iteration-count 3 --iteration-data data/users.csv
```

`hopp test`는 컬렉션 구조 순서대로 요청을 실행하고, **실패한 단언이 하나라도 있으면 0이 아닌 종료 코드**를 반환합니다. 그래서 CI에서 별도 처리 없이 빌드 실패로 이어집니다. 2xx가 아닌 응답도 "유효한 응답"으로 보고 테스트 스크립트가 판단하므로, 상태 코드 검증은 스크립트에 직접 넣어야 합니다.

GitHub Actions 예시입니다.

```yaml
# .github/workflows/api-test.yml
name: api-test
on: [push]
jobs:
  api-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm i -g @hoppscotch/cli
      - run: >
          hopp test -e env/dev.json collections/orders.json
          --reporter-junit reports/hopp-junit.xml
```

파일을 내보내지 않고 클라우드나 셀프 호스팅 서버에 있는 컬렉션을 직접 실행할 수도 있습니다. 프로필의 Personal Access Tokens에서 토큰을 만들고, 컬렉션 Properties의 Details 탭에서 Collection ID를 확인합니다. "Run Collection" 메뉴의 CLI 탭에서 ID가 채워진 명령을 바로 복사할 수도 있습니다.

```bash
hopp test -e <environment_id> <collection_id> \
  --token "$HOPP_TOKEN" \
  --server https://hoppscotch.example.com
```

개인 워크스페이스의 컬렉션은 이 방식으로 실행할 수 없고, 팀 워크스페이스 컬렉션만 가능합니다. 시크릿 변수 값은 내보낸 파일에 들어가지 않으므로 OS 환경 변수로 주입하거나 CI에서 환경 파일에 값을 채워 넣는 방식을 쓰라고 문서가 권합니다.

### 4. Docker로 사내에 셀프 호스팅하기 (Community Edition)

**1단계: `.env` 작성.** 값을 따옴표로 감싸면 안 된다는 점에 주의합니다.

```bash
# Backend
DATABASE_URL=postgresql://hopp:hopp_pass@hoppscotch-db:5432/hoppscotch
DATA_ENCRYPTION_KEY=********************************
WHITELISTED_ORIGINS=http://localhost:3170,http://localhost:3000,http://localhost:3100,app://localhost_3200,app://hoppscotch

# Frontend
VITE_BASE_URL=http://localhost:3000
VITE_SHORTCODE_BASE_URL=http://localhost:3000
VITE_ADMIN_URL=http://localhost:3100
VITE_BACKEND_GQL_URL=http://localhost:3170/graphql
VITE_BACKEND_WS_URL=wss://localhost:3170/graphql
VITE_BACKEND_API_URL=http://localhost:3170/v1
ENABLE_SUBPATH_BASED_ACCESS=false
```

`DATA_ENCRYPTION_KEY`는 DB에 저장되는 민감 정보를 암호화하는 32자 키입니다. 실제 도메인으로 운영한다면 `localhost` 부분을 모두 바꿉니다.

**2단계: 컨테이너 실행.** Postgres가 먼저 떠 있어야 합니다. 서비스 세 개를 하나로 묶은 AIO(All-In-One) 이미지가 가장 간단합니다.

```bash
docker pull hoppscotch/hoppscotch
docker run -p 3000:3000 -p 3100:3100 -p 3170:3170 \
  --env-file .env --restart unless-stopped hoppscotch/hoppscotch
```

프런트엔드·백엔드·관리자 화면을 따로 운영하고 싶다면 `hoppscotch/hoppscotch-frontend`, `hoppscotch/hoppscotch-backend`, `hoppscotch/hoppscotch-admin` 이미지를 각각 3000, 3170, 3100 포트로 띄웁니다. Postgres까지 한 번에 띄우는 구성은 저장소의 `docker-compose.yml`에 프로필로 준비되어 있습니다(`docker compose --profile default up`).

**3단계: DB 마이그레이션.** 처음 띄운 뒤에는 테이블을 만들어야 합니다.

```bash
docker ps                                  # 컨테이너 ID 확인
docker exec -it <container_id> /bin/sh
pnpm exec prisma migrate deploy            # 컨테이너 안에서 실행
```

**4단계: 관리자 계정 만들기.** `http://localhost:3100`(관리자 대시보드)에 **처음 로그인한 사용자가 자동으로 관리자**가 됩니다. 설치 직후 바로 본인 계정으로 로그인해 두는 것이 안전합니다. 그다음 `http://localhost:3000`에서 앱을 씁니다.

데스크톱 앱을 셀프 호스팅 서버에 붙이려면 `ENABLE_SUBPATH_BASED_ACCESS=true`로 서브패스 접근을 켜고, 프런트엔드의 3200 포트(번들 서버)도 노출해야 합니다. 서브패스 모드의 AIO에서는 앱이 `/`, 관리자 화면이 `/admin`, 백엔드가 `/backend` 경로로 열립니다.

## 실무 팁 & 자주 겪는 문제

| 증상 | 원인과 해결 |
| --- | --- |
| 웹 앱에서 요청이 CORS 오류로 실패 | API가 `Access-Control-Allow-Origin` 헤더를 주지 않기 때문입니다. 데스크톱 앱을 쓰거나 Agent·Proxy·브라우저 확장 인터셉터를 켭니다. |
| localhost API가 안 됨 | 공식 FAQ는 CORS 설정 문제를 먼저 의심하라고 안내합니다. Agent 인터셉터나 데스크톱 앱이 가장 간단합니다. |
| 스크립트의 `fetch()`, `hopp.fetch()`, `pm.sendRequest()`가 이상하게 동작 | 웹 앱은 Agent 인터셉터, 데스크톱 앱은 Native 인터셉터를 쓰라고 문서가 권장합니다. |
| 회사망에서만 요청이 실패 | 방화벽이 브라우저가 아닌 연결을 막을 수 있습니다. 네트워크 관리자와 확인합니다. |
| CLI `TOKEN_EXPIRED` / `TOKEN_INVALID` | `--token`으로 넘긴 PAT가 만료되었거나 삭제되었습니다. 새 토큰을 발급합니다. PAT 만료 기간은 7/30/60/90일 또는 무기한 중에서 고릅니다. |
| CLI `INVALID_ID` | 컬렉션/환경 ID가 틀렸거나, 그 팀 워크스페이스의 멤버가 아니거나, 파일 경로가 없습니다. |
| CLI `INVALID_SERVER_URL` | `--server`에 백엔드가 아닌 프런트엔드 URL을 넣었거나 `http://`가 빠진 경우가 흔합니다. 응답이 JSON이 아니어도 이 오류가 납니다. |
| CLI가 환경 파일을 못 읽음 | CLI는 단일 환경 내보내기 형식, 옛 key-value 형식, 환경 ID만 지원합니다. **Bulk Environment 내보내기 형식은 지원하지 않습니다.** |
| 셀프 호스팅 시작 시 `Database migration not found` | DB에 테이블이 없는 상태에서 백엔드를 띄웠습니다. `docker run -it --entrypoint sh --env-file .env <이미지>`로 셸을 열고 `pnpm exec prisma migrate deploy`를 실행한 뒤 다시 띄웁니다. |
| rootless Docker, Podman, OpenShift에서 실행 실패 | 컨테이너가 기본으로 80번 포트를 쓰는데 1024 미만 포트는 non-root가 바인딩할 수 없습니다. `HOPP_ALTERNATE_PORT=8000`처럼 1024 이상 포트를 지정하고 GID 0으로 실행합니다. |

추가로 알아 두면 좋은 점입니다.

- 셀프 호스팅 인증은 secure HTTP 쿠키를 쓰므로 운영 환경에서는 TLS 인증서를 붙여 HTTPS로 서비스하는 것이 권장됩니다.
- 2023년 12월 릴리스부터 컨테이너는 표준 80/443 포트를 기본 지원하며, 3000/3100/3170 포트 방식은 앞으로 지원이 빠질 예정이라고 문서에 적혀 있습니다.
- 시크릿 변수는 환경을 복제(Duplicate)할 때도 값이 복사되지 않습니다.
- "Something went wrong" 오류는 브라우저 개발자 도구 Console 탭 내용을 함께 이슈로 보내면 원인 파악이 빠릅니다.

## 비슷한 도구와 비교

| 항목 | Hoppscotch | Postman | Insomnia | Bruno |
| --- | --- | --- | --- | --- |
| 라이선스 | MIT(CE), EE는 오픈 코어 | 상용(무료 플랜 있음) | 오픈소스(Kong 관리) | MIT |
| 형태 | 웹, 데스크톱, CLI | 데스크톱, 웹 | 데스크톱 | 데스크톱(오프라인 중심) |
| 설치 없이 사용 | 가능(브라우저) | 웹 버전은 로그인 필요 | 불가 | 불가 |
| 데이터 저장 | 브라우저 로컬, 클라우드, 셀프 호스팅 서버 | 주로 Postman 클라우드 | 로컬 또는 클라우드 동기화 | 로컬 파일(Git으로 관리) |
| 셀프 호스팅 | Docker로 CE 무료, EE 유료 | 제공 안 함 | 제공 안 함(일반적으로) | 서버가 필요 없는 구조 |
| CI 실행 | `hopp test` | Newman / Postman CLI | Inso CLI | Bruno CLI |
| 프로토콜 | REST, GraphQL, WebSocket, SSE, Socket.IO, MQTT | REST, GraphQL, gRPC, WebSocket 등 | REST, GraphQL, gRPC, WebSocket | REST, GraphQL 중심 |

Hoppscotch 열은 공식 문서 기준이고, 다른 도구 열은 일반적으로 알려진 내용이라 세부 기능과 요금제는 버전에 따라 다를 수 있습니다. 대략적으로 정리하면 이렇습니다.

- **Postman:** 기능 폭과 생태계가 가장 넓지만, 데이터가 클라우드 중심이고 팀 기능은 유료입니다.
- **Insomnia:** 데스크톱 중심의 깔끔한 도구로 gRPC 등 프로토콜 지원이 좋습니다.
- **Bruno:** 컬렉션을 일반 텍스트 파일로 저장해 Git으로 코드처럼 리뷰·버전 관리하고 싶은 팀에 맞습니다.
- **Hoppscotch:** 브라우저에서 즉시 쓰는 가벼움과 무료 셀프 호스팅 팀 서버가 핵심 차별점입니다.

## 장점과 한계

**장점**

- 설치 없이 브라우저에서 바로 쓰고, 화면이 단순해 배우기 쉽습니다.
- REST부터 GraphQL, WebSocket, SSE, Socket.IO, MQTT까지 한 도구에서 다룹니다.
- MIT 라이선스 CE를 Docker로 띄우면 팀 워크스페이스·공유 환경까지 무료로 사내에서 운영할 수 있습니다.
- 시크릿 변수가 서버로 동기화되지 않아 팀 공유와 보안의 균형을 잡기 좋습니다.
- Postman·Insomnia·OpenAPI 가져오기와 `pm` 호환 계층 덕분에 이전 비용이 낮습니다.
- CLI의 종료 코드와 JUnit 리포트로 CI에 쉽게 붙습니다.

**한계**

- 웹 앱은 CORS 제약이 있어 인터셉터나 데스크톱 앱을 추가로 준비해야 할 때가 많습니다.
- CLI는 아직 알파 단계이고, 새 `hopp` 스크립트 API는 실험 단계라 바뀔 수 있습니다.
- 공유 워크스페이스 협업은 현재 REST만 지원합니다.
- Postman의 일부 스크립트 기능(`pm.collectionVariables`, `setNextRequest` 등)은 아직 지원되지 않습니다.
- SAML SSO, 감사 로그, 고급 관리자 도구, 도메인 화이트리스트 같은 기업용 기능은 Enterprise Edition(문서 기준 사용자당 월 $19)에만 있습니다.
- 셀프 호스팅 시 Postgres, OAuth, SMTP, TLS, 마이그레이션을 직접 관리해야 합니다. CE는 분기별 릴리스를 스스로 업데이트하는 구조입니다.

## 이런 분께 추천 / 이런 경우엔 다른 도구

**추천**

- Postman이 무겁게 느껴지고 브라우저에서 가볍게 API를 확인하고 싶은 분
- API 데이터를 외부 클라우드에 둘 수 없어 사내에 무료로 팀 API 도구를 세우려는 팀
- WebSocket, MQTT, SSE 같은 실시간 프로토콜도 같은 도구로 테스트하려는 분
- 이미 만든 컬렉션을 CI에서 간단히 회귀 테스트로 돌리고 싶은 팀

**다른 도구가 나은 경우**

- 컬렉션을 코드와 같은 저장소에서 파일 단위로 리뷰·머지하고 싶다면 Bruno가 더 자연스럽습니다.
- gRPC 테스트가 중요하다면 gRPC를 지원하는 Postman이나 Insomnia를 먼저 확인해 보세요.
- Postman의 복잡한 스크립트(`setNextRequest` 기반 흐름 제어 등)와 모니터링·문서화 생태계에 깊이 의존하고 있다면, 이전 전에 호환 범위를 꼼꼼히 확인해야 합니다.

## 참고 링크

- [Setup](https://docs.hoppscotch.io/documentation/getting-started/setup) · [Clients](https://docs.hoppscotch.io/documentation/getting-started/clients)
- [Desktop App](https://docs.hoppscotch.io/documentation/clients/desktop/overview)
- [Hoppscotch CLI](https://docs.hoppscotch.io/documentation/clients/cli/overview) · [CLI Troubleshooting](https://docs.hoppscotch.io/documentation/clients/cli/troubleshooting)
- [MCP Server](https://docs.hoppscotch.io/documentation/clients/mcp-server/overview)
- [Environments](https://docs.hoppscotch.io/documentation/features/environments) · [Variables](https://docs.hoppscotch.io/documentation/features/variables)
- [Scripts](https://docs.hoppscotch.io/documentation/features/scripts) · [Runner](https://docs.hoppscotch.io/documentation/features/runner)
- [Authorization](https://docs.hoppscotch.io/documentation/features/authorization) · [Personal Access Token](https://docs.hoppscotch.io/documentation/features/pat)
- [Interceptor](https://docs.hoppscotch.io/documentation/features/interceptor) · [Importer](https://docs.hoppscotch.io/documentation/features/importer) · [Mock](https://docs.hoppscotch.io/documentation/features/mock)
- [Workspaces](https://docs.hoppscotch.io/documentation/features/workspaces)
- [Self-host 시작하기](https://docs.hoppscotch.io/documentation/self-host/getting-started) · [CE Prerequisites](https://docs.hoppscotch.io/documentation/self-host/community-edition/prerequisites) · [CE Install and build](https://docs.hoppscotch.io/documentation/self-host/community-edition/install-and-build) · [CE Setup and access](https://docs.hoppscotch.io/documentation/self-host/community-edition/setup-and-access)
- [Troubleshooting](https://docs.hoppscotch.io/documentation/getting-started/troubleshooting) · [FAQ](https://docs.hoppscotch.io/support/getting-started/faq)
- [docker-compose.yml (저장소)](https://github.com/hoppscotch/hoppscotch/blob/main/docker-compose.yml)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
