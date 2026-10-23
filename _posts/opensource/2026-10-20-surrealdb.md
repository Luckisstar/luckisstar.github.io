---
layout: default
title: "[오픈소스 소개] SurrealDB: 문서, 그래프, 벡터를 한 엔진에 담은 멀티모델 데이터베이스"
description: "문서·그래프·벡터·키-값 데이터를 SurrealQL 하나로 다루는 멀티모델 DB SurrealDB의 구조, 권한과 실시간 쿼리, BSL 1.1 라이선스 주의점을 정리했습니다."
date: 2026-10-20
categories: [opensource]
---

# [오픈소스 소개] SurrealDB: 문서, 그래프, 벡터를 한 엔진에 담은 멀티모델 데이터베이스

- **저장소:** [surrealdb/surrealdb](https://github.com/surrealdb/surrealdb) · [surrealdb.com](https://surrealdb.com) · [문서](https://surrealdb.com/docs)
- **라이선스:** Business Source License 1.1 (코어 DB). SDK와 일부 라이브러리는 Apache 2.0 또는 MIT
- **언어:** Rust
- **현황 (2026-10-20 기준):** GitHub 스타 약 3.3만 개, 최신 릴리스 v3.3.4 (2026-10-19)

> **라이선스 먼저 확인하세요.**
> GitHub에는 라이선스가 "Other"로 표시됩니다. 실제로는 **BSL 1.1(Business Source License)**이고, 라이선스 파일 스스로 "오픈소스 라이선스가 아니다"라고 밝힙니다.
> 추가 사용 허가(Additional Use Grant)에 따라 운영 환경에서도 쓸 수 있지만, **SurrealDB를 "Database Service"로 제공하는 것은 금지**됩니다. 여기서 Database Service는 직원이나 계약자가 아닌 제3자가 스키마나 테이블을 만들고 관리할 수 있게 DB 기능을 제공하는 상품이나 서비스를 말합니다. 쉽게 말해 "SurrealDB 호스팅 서비스"를 팔면 안 되고, 내 앱의 백엔드로 쓰는 것은 괜찮다는 취지입니다.
> 변경일(Change Date)은 **2030-01-01**이며, 그날 또는 각 버전이 처음 공개된 지 4년이 되는 날 중 빠른 날에 **Apache 2.0**으로 전환됩니다. 법적 판단이 필요하면 원문과 [surrealdb.com/legal](https://surrealdb.com/legal)을 직접 확인하세요.

## 한 줄 요약

**문서(JSON), 그래프, 관계형, 키-값, 벡터, 지리 데이터를 하나의 쿼리 언어(SurrealQL)로 다루는 Rust 기반 데이터베이스**입니다. 인증과 행 단위 권한, 실시간 구독(Live Query)을 DB 안에 내장하고 있어서, 작은 앱이라면 별도 API 서버 없이 프런트엔드가 DB에 직접 붙는 구조도 만들 수 있습니다.

## 어떤 문제를 푸나

서비스를 키우다 보면 데이터 저장소가 하나씩 늘어나는 경우가 많습니다.

- 사용자와 주문은 PostgreSQL, 유연한 설정 데이터는 MongoDB에 둡니다.
- "친구의 친구가 산 상품" 같은 추천은 Neo4j 같은 그래프 DB가 편합니다.
- RAG(검색 증강 생성)용 임베딩은 벡터 DB에 따로 넣습니다.
- 실시간 알림을 위해 Redis Pub/Sub이나 WebSocket 서버를 또 붙입니다.
- 그리고 이 모든 것 앞에 권한을 검사하는 API 서버가 필요합니다.

저장소가 늘어날수록 데이터 동기화, 트랜잭션 경계, 운영 부담이 커집니다. SurrealDB는 이 모델들을 **한 엔진과 한 쿼리 언어**로 묶겠다는 접근입니다. 테이블에는 자유로운 JSON 문서를 넣고, 레코드끼리는 그래프 간선(edge)으로 잇고, 같은 테이블에 벡터 인덱스도 겁니다. JOIN 없이 `->`로 관계를 따라가는 것이 대표적인 특징입니다.

## 핵심 개념

### 네임스페이스, 데이터베이스, 테이블, 레코드

SurrealDB의 데이터는 `namespace > database > table > record` 계층으로 나뉩니다. 네임스페이스는 조직이나 테넌트, 데이터베이스는 앱 단위로 생각하면 됩니다. 3.3 기준으로 새 데이터 저장소를 만들면 `main` 네임스페이스와 `main` 데이터베이스가 기본으로 생깁니다(`--no-defaults`로 끌 수 있습니다).

### 레코드 ID

모든 레코드는 `테이블:아이디` 형태의 ID를 가집니다. 예를 들어 `person:tobie`, `article:surreal`처럼 씁니다. ID 자체가 테이블 정보를 담고 있어서 `SELECT * FROM person:tobie`처럼 바로 한 건을 가리킬 수 있고, 다른 레코드의 필드에 이 ID를 넣으면 그대로 **레코드 링크**가 됩니다. 테이블만 지정해 `CREATE`하면 무작위 ID가 생성됩니다.

### 그래프 간선과 `RELATE`

`RELATE person:aristotle->wrote->article:on_sleep`을 실행하면 `wrote`라는 **간선 테이블**에 `in`(출발), `out`(도착) 필드를 가진 레코드가 생깁니다. 양 끝 레코드에는 아무것도 저장되지 않고, 관계 정보는 간선 테이블에만 있습니다. 간선도 일반 레코드라서 `SET`으로 시각, 가중치 같은 속성을 붙일 수 있습니다.

조회할 때는 화살표로 따라갑니다.

- `->wrote->article`: 내가 쓴 글 (정방향)
- `<-wrote<-person`: 이 글을 쓴 사람 (역방향)
- `<->sister_of<->city`: 방향 구분 없이 양쪽 모두

### 스키마리스와 스키마풀

- **SCHEMALESS:** 아무 필드나 저장할 수 있습니다. 처음 쓰는 테이블은 `DEFINE` 없이 바로 `CREATE`해도 만들어집니다.
- **SCHEMAFULL:** `DEFINE FIELD`로 정의한 필드만 허용합니다. 타입(`string`, `datetime`, `record<user>`, `option<string>` 등), 기본값(`DEFAULT`), 검증(`ASSERT`), 읽기 전용(`READONLY`)을 지정할 수 있습니다.
- **COMPUTED 필드(3.x):** 조회할 때마다 계산되는 필드입니다. 2.x의 `<future>` 타입을 대체합니다.

같은 DB 안에서 테이블마다 섞어 쓸 수 있으니, 초기에는 스키마리스로 빠르게 만들고 안정되면 스키마풀로 굳히는 방식이 가능합니다.

### 시스템 사용자와 레코드 사용자

- **시스템 사용자:** `DEFINE USER`로 만드는 root, namespace, database 수준 사용자입니다. 역할(OWNER, EDITOR 등)로 권한을 받고, 테이블 `PERMISSIONS`의 제약을 받지 않습니다.
- **레코드 사용자:** `DEFINE ACCESS ... TYPE RECORD`로 정의한 가입/로그인 로직을 통해 들어오는 최종 사용자입니다. 이들이 테이블과 필드의 `PERMISSIONS` 규칙을 적용받습니다. 테이블에 `PERMISSIONS`를 생략하면 기본값이 `NONE`이라 레코드 사용자는 아무것도 못 합니다.

## 동작 원리

SurrealDB는 **쿼리 계층**과 **저장 계층**을 분리한 구조입니다. 쿼리 계층이 SurrealQL을 해석하고 인증, 권한, 인덱스, 트랜잭션을 처리하며, 저장 계층은 트랜잭션을 지원하는 키-값 저장소에 데이터를 씁니다.

```
 Browser / App / SDK / Studio
   │ WebSocket(RPC)  HTTP(/sql)  Postgres wire*
   ▼
 ┌──────────── SurrealDB node ─────────────┐
 │ Query layer                             │
 │  SurrealQL parser / planner             │
 │  Auth (DEFINE USER / ACCESS)            │
 │  PERMISSIONS (table, field, row)        │
 │  Indexes: unique, full-text, HNSW       │
 │  Live queries / events / changefeeds    │
 ├─────────────────────────────────────────┤
 │ Storage layer (transactional KV)        │
 │  memory | rocksdb | surrealkv | tikv    │
 │  indxdb (browser, WASM)                 │
 └─────────────────────────────────────────┘
   * --postgres-bind (3.3)
```

저장 엔진은 `surreal start`의 경로 인자로 고릅니다.

| 엔진 | 경로 예시 | 용도 |
|---|---|---|
| 메모리 (SurrealMX) | `memory` (기본값) | 테스트, 임시 작업. 3.3부터 `VERSION` 쿼리 미지원 |
| RocksDB | `rocksdb:/data/app.db` | 단일 서버 운영의 권장 선택지 |
| SurrealKV | `surrealkv://mydb` | 임베디드, 로컬 우선 앱. 메모리 사용이 적은 편 |
| TiKV | `tikv://...` | 분산 클러스터 |
| IndexedDB | `indxdb://...` | 브라우저(WASM) 임베디드 |

FoundationDB 지원은 3.0에서 제거되었습니다. 경로의 슬래시 개수도 의미가 있어서, `rocksdb:mydb`나 `rocksdb://mydb`는 실행 위치 기준 상대 경로이고 `rocksdb:/path`처럼 슬래시가 하나면 절대 경로입니다.

같은 Rust 코어가 **서버 프로세스**로도, 앱 안에 들어가는 **임베디드 라이브러리**로도 동작합니다. JavaScript에서는 `@surrealdb/wasm`(브라우저)과 `@surrealdb/node`(Node.js, Bun, Deno) 엔진 플러그인으로 임베디드 모드를 쓸 수 있습니다.

## 주요 기능

### 데이터 모델

- **문서 + 관계형:** 중첩 객체와 배열을 자유롭게 저장하고, 레코드 링크로 다른 레코드를 참조합니다.
- **그래프:** `RELATE`와 화살표 탐색, 재귀 탐색을 지원합니다. `TYPE RELATION IN user OUT post`로 간선 양 끝 테이블을 제한하고, `ENFORCED`로 존재하지 않는 레코드에 대한 간선 생성을 막을 수 있습니다.
- **벡터 검색:** HNSW 인덱스와 3.1부터 추가된 디스크 기반 DISKANN 인덱스를 제공합니다. 인덱스 없이 정확한 브루트포스 검색도 됩니다.
- **전문 검색:** `DEFINE ANALYZER`와 `FULLTEXT ANALYZER` 인덱스(BM25)를 씁니다. 3.3 릴리스 바이너리와 Docker 이미지에는 한국어, 일본어, 중국어 분리용 `SEGMENT` 토크나이저 사전이 들어 있습니다(그 대신 바이너리가 약 150MB 커졌습니다).
- **지리 데이터:** GeoJSON 형식의 점, 선, 폴리곤을 저장합니다.

### 백엔드 기능

- **인증:** 레코드 사용자 가입/로그인(`DEFINE ACCESS ... TYPE RECORD`), JWT, Bearer 접근 방식을 지원합니다.
- **행 단위 권한:** 테이블과 필드마다 `FOR select/create/update/delete WHERE ...` 규칙을 둡니다.
- **Live Query:** `LIVE SELECT`로 테이블 변경을 WebSocket으로 받아 봅니다. `DIFF` 모드는 JSON Patch 형식으로 변경분만 보냅니다.
- **이벤트와 함수:** `DEFINE EVENT`로 변경 시 후속 작업을 실행하고, `DEFINE FUNCTION`으로 재사용 함수를 만듭니다. 내장 JavaScript 함수도 쓸 수 있습니다.
- **ACID 트랜잭션:** 여러 테이블, 여러 행에 걸친 트랜잭션을 지원합니다.

### 접속 방식과 도구

- **프로토콜:** WebSocket RPC, HTTP REST(`/sql` 등), GraphQL, 3.3부터 Postgres wire 프로토콜(`--postgres-bind`)을 지원합니다. 3.3부터는 ISO GQL(Cypher 계열 그래프 쿼리 언어)도 기본으로 켜져 있습니다.
- **SDK:** JavaScript/TypeScript, Python, Rust, Go, .NET, Java, PHP 등. 문서 사이트에는 Kotlin, Swift 레퍼런스도 있습니다.
- **GUI:** 공식 시각 도구인 **Surrealist**가 있고, 현재 문서에서는 **SurrealDB Studio**([studio.surrealdb.com](https://studio.surrealdb.com))라는 이름으로 안내합니다. 쿼리 실행, 레코드 탐색, 스키마 관리, 2.x에서 3.x로의 마이그레이션 진단을 제공합니다.
- **MCP 서버:** README는 LLM과 AI 에이전트 연동용 MCP 서버를 기능으로 소개합니다.

### Community와 Enterprise

같은 코어지만 바이너리가 다릅니다. Enterprise는 라이선스 키가 있어야 시작되고, 여러 가용 영역에 걸친 장애 허용 클러스터, 오브젝트 스토리지 기반 확장, **분산 Live Query**, 감사 로그, FIPS 모드를 추가합니다. 중요한 점은 **Community에서 Live Query는 구독을 받은 노드에서 일어난 변경만 전달**한다는 것입니다. 그래서 Community의 Live Query는 단일 노드 배포에 맞습니다.

## 설치와 시작

### 1) CLI 설치

```bash
# macOS / Linux: 설치 스크립트 (런처 + DB 컴포넌트)
curl -sSf https://install.surrealdb.com | sh

# macOS: Homebrew (DB 단일 실행 파일)
brew install surrealdb/tap/surreal

# Windows (PowerShell)
iwr https://windows.surrealdb.com -useb | iex
```

여기서 함정이 하나 있습니다. 최근 설치 스크립트는 `surreal`을 **런처**로 설치하고, DB 명령은 `db` 컴포넌트 아래로 들어갔습니다. 그래서 문서 예시가 `surreal db start` 형태로 바뀌었습니다.

- **설치 스크립트로 설치:** `surreal db start`, `surreal db sql`을 씁니다. 예전처럼 `surreal start`를 쳐도 동작하지만 deprecation 경고가 나옵니다.
- **Homebrew, Chocolatey, Scoop, Docker:** DB 실행 파일이 그대로 들어 있어서 `db` 없이 `surreal start`를 씁니다.

런처는 여러 버전을 나란히 설치하고 고를 수 있습니다(`surreal install db@3.3.2`, `surreal use db@2`, `surreal upgrade`).

### 2) 서버 띄우기

```bash
# 메모리 모드, root 사용자 생성 (개발용)
surreal db start memory --user root --pass secret

# 디스크(RocksDB)에 저장
surreal db start --user root --pass secret rocksdb:/var/lib/surrealdb/app.db
```

기본 바인드 주소는 `127.0.0.1:8000`입니다. `--user`, `--pass`로 만든 root 사용자는 **데이터 저장소가 새로 만들어질 때만** 생성됩니다. 같은 저장소로 다시 시작하면서 비밀번호를 바꿔도 반영되지 않으니, 변경은 `ALTER USER`나 `DEFINE USER OVERWRITE`로 합니다.

Docker로 띄울 때는 이렇게 합니다. 이미지는 UID 65532인 비 root 사용자로 돌기 때문에 마운트한 디렉터리 권한을 맞춰야 합니다.

```bash
mkdir mydata
docker run --rm --pull always -p 8000:8000 \
  --user $(id -u) -v $(pwd)/mydata:/mydata \
  surrealdb/surrealdb:latest \
  start --user root --pass secret rocksdb:/mydata/mydatabase.db
```

### 3) 쿼리 실행

```bash
surreal db sql --endpoint http://127.0.0.1:8000 \
  --namespace main --database main \
  --username root --password secret
```

REPL이 뜨면 바로 SurrealQL을 입력할 수 있습니다. HTTP로 보내고 싶다면 `/sql` 엔드포인트에 `Surreal-NS`, `Surreal-DB` 헤더를 붙입니다.

```bash
curl -X POST -u "root:secret" \
  -H "Surreal-NS: main" -H "Surreal-DB: main" \
  -H "Accept: application/json" \
  -d "CREATE person:tobie SET name = 'Tobie'; SELECT * FROM person;" \
  http://localhost:8000/sql
```

GUI가 편하다면 SurrealDB Studio에서 `ws://127.0.0.1:8000`으로 연결하면 됩니다.

## 실전 예제

### 예제 1: 블로그 데이터를 그래프로 모델링하기

사용자, 글, 태그가 있고 "누가 썼는지", "누가 좋아했는지"를 간선으로 표현합니다.

```surql
-- 스키마: 사용자와 글은 스키마풀
DEFINE TABLE user SCHEMAFULL;
DEFINE FIELD name ON user TYPE string;
DEFINE FIELD email ON user TYPE string ASSERT string::is_email($value);
DEFINE INDEX user_email ON user FIELDS email UNIQUE;

DEFINE TABLE post SCHEMAFULL;
DEFINE FIELD title ON post TYPE string;
DEFINE FIELD body ON post TYPE string;
DEFINE FIELD tags ON post TYPE array<string>;
DEFINE FIELD created ON post TYPE datetime DEFAULT time::now() READONLY;

-- 간선 테이블: 양 끝 타입을 제한하고, 존재하는 레코드만 허용
DEFINE TABLE wrote TYPE RELATION IN user OUT post ENFORCED;
DEFINE TABLE likes TYPE RELATION IN user OUT post ENFORCED;
-- 같은 사람이 같은 글을 두 번 좋아하지 못하게
DEFINE INDEX unique_like ON likes FIELDS in, out UNIQUE;

-- 데이터
CREATE user:alice SET name = 'Alice', email = 'alice@example.com';
CREATE user:bob   SET name = 'Bob',   email = 'bob@example.com';
CREATE post:intro SET title = 'SurrealDB 첫걸음',
    body = '...', tags = ['db', 'rust'];

RELATE user:alice->wrote->post:intro;
RELATE user:bob->likes->post:intro SET at = time::now();
```

이제 JOIN 없이 관계를 따라갑니다.

```surql
-- Alice가 쓴 글 제목
SELECT ->wrote->post.title AS titles FROM user:alice;

-- 글마다 작성자 이름과 좋아요 수
SELECT
    title,
    <-wrote<-user.name AS author,
    count(<-likes) AS like_count
FROM post;

-- Bob이 좋아한 글을 쓴 사람들 (2단계 탐색)
SELECT ->likes->post<-wrote<-user.name AS authors FROM user:bob;
```

`TYPE RELATION ... ENFORCED`가 없으면 `RELATE`는 존재하지 않는 레코드를 가리키는 간선도 만들어 줍니다. 오타 하나로 유령 간선이 생기는 일을 막으려면 운영 스키마에서는 켜 두는 편이 안전합니다.

### 예제 2: 가입, 로그인, 행 단위 권한 (API 서버 없이)

레코드 사용자용 접근 방식을 정의하고, 글은 공개된 것과 내 글만 보이도록 권한을 겁니다.

```surql
DEFINE TABLE account SCHEMAFULL
    PERMISSIONS FOR select, update WHERE id = $auth.id;
DEFINE FIELD email ON account TYPE string;
DEFINE FIELD pass  ON account TYPE string;
DEFINE INDEX account_email ON account FIELDS email UNIQUE;

DEFINE ACCESS account ON DATABASE TYPE RECORD
    SIGNUP ( CREATE account SET email = $email,
             pass = crypto::argon2::generate($pass) )
    SIGNIN ( SELECT * FROM account WHERE email = $email
             AND crypto::argon2::compare(pass, $pass) )
    DURATION FOR TOKEN 15m, FOR SESSION 12h;

DEFINE TABLE note SCHEMALESS
    PERMISSIONS
        FOR select WHERE published = true OR owner = $auth.id
        FOR create, update, delete WHERE owner = $auth.id;
```

브라우저에서 JavaScript SDK로 가입하고 바로 쿼리합니다.

```ts
import { Surreal, Table } from 'surrealdb';

const db = new Surreal();
await db.connect('wss://db.example.com', {
  namespace: 'main',
  database: 'main',
});

// SIGNUP 절의 $email, $pass로 전달됩니다
await db.signup({
  namespace: 'main',
  database: 'main',
  access: 'account',
  variables: { email: 'me@example.com', pass: 'correct-horse' },
});

// 이 사용자의 권한 규칙이 적용된 결과만 돌아옵니다
const [notes] = await db.query('SELECT * FROM note');
```

- 비밀번호는 `$pass`로 서버에 그대로 전송되고 서버에서 argon2로 해시됩니다. 문서는 그래서 **반드시 HTTPS/WSS로 서비스하라**고 강조합니다. 클라이언트에서 해시해서 보내는 것은 대안이 되지 않습니다(그 해시가 곧 비밀번호가 되기 때문입니다).
- `UNIQUE` 인덱스가 없으면 같은 이메일로 두 번 가입할 수 있고, 로그인 시 두 계정이 동시에 매칭됩니다.
- 비밀번호 재설정 기능은 내장되어 있지 않습니다. 공식 문서는 백엔드가 일회용 토큰을 만들고 `SIGNIN` 블록에서 그 토큰을 검사하는 패턴을 소개합니다.

### 예제 3: Live Query로 실시간 대시보드 만들기

주문 테이블에 새 주문이 들어오면 화면에 바로 반영하는 예입니다. Live Query는 WebSocket 연결에서만 동작합니다.

```ts
import { Surreal, Table, gt } from 'surrealdb';

const db = new Surreal();
await db.connect('ws://127.0.0.1:8000', {
  namespace: 'main',
  database: 'main',
  authentication: { username: 'root', password: 'secret' },
});

// 관리형 Live Query: 재연결 시 SDK가 자동으로 다시 구독
const live = await db.live(new Table('orders'))
  .where(gt('amount', 100000));

live.subscribe((action, result, record) => {
  if (action === 'CREATE') console.log('새 주문', result);
  if (action === 'UPDATE') console.log('변경', record, result);
  if (action === 'DELETE') console.log('삭제', record);
});

// 화면을 떠날 때
// await live.kill();
```

SurrealQL로 직접 구독할 수도 있습니다. 이 방식은 재연결 시 자동 복구되지 않습니다.

```ts
const [id] = await db.query(
  "LIVE SELECT * FROM orders WHERE $event = 'CREATE'"
);
const created = db.liveOf(id);
created.subscribe((action, result) => console.log(action, result));
```

`$event = 'CREATE'`처럼 **서버 쪽에서 걸러야** 불필요한 알림이 오지 않습니다. 변경 내용만 받고 싶다면 `LIVE SELECT DIFF FROM orders;`를 씁니다.

### 예제 4: 벡터 검색으로 비슷한 문서 찾기

임베딩은 외부 모델(OpenAI, 로컬 모델 등)로 만들었다고 가정하고, 예시에서는 4차원으로 줄였습니다.

```surql
DEFINE TABLE doc SCHEMAFULL;
DEFINE FIELD title     ON doc TYPE string;
DEFINE FIELD embedding ON doc TYPE array<float>;
DEFINE INDEX doc_vec ON doc FIELDS embedding
    HNSW DIMENSION 4 DIST COSINE;

CREATE doc:a SET title = 'Rust 소유권 정리',   embedding = [0.9, 0.1, 0.0, 0.2];
CREATE doc:b SET title = 'Rust 비동기 입문',   embedding = [0.8, 0.2, 0.1, 0.3];
CREATE doc:c SET title = '김치찌개 레시피',     embedding = [0.0, 0.9, 0.8, 0.1];

LET $q = [0.85, 0.15, 0.05, 0.25];

SELECT id, title, vector::distance::knn() AS dist
FROM doc
WHERE embedding <|2|> $q
ORDER BY dist;
```

- `<|2|>`는 가장 가까운 2개를 찾는 KNN 연산자이고, 인덱스에 정의한 거리 함수(여기서는 COSINE)를 씁니다.
- `<|2, EUCLIDEAN|>`처럼 거리 함수를 쿼리에 직접 쓰면 인덱스 대신 **브루트포스**로 계산됩니다. 인덱스를 탔는지 헷갈린다면 이 부분부터 확인하세요.
- `vector::distance::knn()`은 검색 중에 계산한 거리를 다시 계산하지 않고 재사용합니다.
- 데이터가 메모리에 다 올라가지 않을 만큼 크다면 3.1부터 들어온 `DISKANN` 인덱스를 검토합니다. 단, WASM(브라우저)에서는 지원하지 않습니다.
- 3.x에서는 2.x의 `MTREE` 인덱스가 제거되었습니다. 예전 예제를 따라 하다가 에러가 나면 `HNSW`로 바꾸세요.

같은 테이블에 전문 검색 인덱스와 그래프 간선을 함께 둘 수 있어서, "벡터로 후보를 찾고, 그래프로 작성자나 관련 문서를 붙이는" 쿼리를 한 번에 쓸 수 있다는 점이 별도 벡터 DB 대비 장점입니다.

### 예제 5: Docker Compose로 스키마와 함께 띄우기

공식 문서의 Compose 구성입니다. 시작할 때마다 스키마 파일을 가져옵니다.

```yaml
# compose.yaml
services:
  surrealdb:
    image: surrealdb/surrealdb:v3.3.4   # 운영은 버전 고정 권장
    user: root          # named volume 쓰기 권한 문제 회피
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - surrealdb-data:/data
      - ./schema.surql:/schema.surql:ro
    command: start --import-file /schema.surql rocksdb:/data/app.db

volumes:
  surrealdb-data:
```

```bash
# .env
SURREAL_USER=root
SURREAL_PASS=secret
```

```surql
-- schema.surql : 매번 다시 실행되므로 IF NOT EXISTS 필수
DEFINE NAMESPACE IF NOT EXISTS app;
USE NS app;
DEFINE DATABASE IF NOT EXISTS main;
USE DB main;

DEFINE TABLE IF NOT EXISTS person SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS name ON person TYPE string;
```

- `command`에 `--user ${SURREAL_USER}`처럼 변수 치환을 쓰지 말고 환경 변수(`SURREAL_USER`, `SURREAL_PASS`)로 넘기는 것이 문서의 권장입니다. 치환이 비면 이름이 빈 root 사용자가 만들어집니다.
- 가져오기 파일에서 실패한 문장은 **로그 없이 건너뛰고** 서버는 정상 시작합니다. 스키마가 반영되지 않았다면 `IF NOT EXISTS`나 `OVERWRITE`를 빠뜨리지 않았는지 보세요.
- 3.3부터 시작 작업이 백그라운드로 돌기 때문에, 준비 완료 여부는 `/health`가 아니라 `/ready`로 확인해야 합니다.

## 실무 팁 & 자주 겪는 문제

**설치와 실행**

- `surreal start`에서 경고가 나오면 설치 스크립트로 설치한 런처입니다. `surreal db start`로 바꾸면 됩니다. 반대로 Homebrew 설치본에는 `db` 하위 명령이 없습니다.
- `Failed to create RocksDB directory`와 `Permission denied`는 대부분 경로 문제입니다. 컨테이너 안에서는 `rocksdb:/mydata/...`처럼 슬래시 하나로 **마운트한 디렉터리 아래 절대 경로**를 주고, 디렉터리 소유자를 `--user $(id -u)`나 `chown 65532`로 맞춥니다.
- 개발 중 컨테이너 안을 들여다봐야 하면 셸이 들어 있는 `surrealdb/surrealdb:latest-dev` 이미지를 씁니다.
- `--unauthenticated`는 인증을 끄는 옵션입니다. 로컬 실험 외에는 쓰지 마세요.

**스키마와 쿼리**

- 테이블 `PERMISSIONS`를 생략하면 `NONE`입니다. 레코드 사용자로 접속했는데 결과가 비어 있다면 권한부터 확인합니다. 반대로 시스템 사용자(root 등)는 테이블 권한을 무시하므로, 권한 테스트는 꼭 레코드 사용자로 해야 합니다.
- `record<author>` 타입 필드는 존재하지 않는 ID도 받아 줍니다. 막으려면 `ASSERT $value.exists()`를 붙입니다.
- `FOR select` 권한 절 안에서 데이터를 쓰면(예: 감사 로그 `CREATE`) 3.3부터는 정의는 되지만 읽을 때마다 실패합니다. 감사 로그는 `DEFINE EVENT`로 처리하세요.
- 3.3에서 `UPDATE`, `UPSERT`는 `WHERE`를 먼저 평가하고, 필드 절(`DEFAULT`, `VALUE`, `COMPUTED`)은 의존 순서대로 실행되도록 바뀌었습니다. 3.2에서 올라왔다면 부수 효과가 있는 쿼리를 다시 점검하세요.

**버전 업그레이드**

- 2.x에서 3.x로는 깨지는 변경이 많습니다. `<future>` → `COMPUTED`, `SEARCH ANALYZER` → `FULLTEXT ANALYZER`, `MTREE` 제거, `string::is::email` 같은 함수명이 `string::is_email`로 변경, 인스턴스 `--strict` 플래그 → `DEFINE DATABASE ... STRICT` 등입니다.
- 2.6 이상에서는 "V3 호환 내보내기"로 함수명 등을 자동 변환해 내보낼 수 있고, Studio의 마이그레이션 진단 기능이 할 일 목록을 만들어 줍니다.
- 3.2에서 3.3으로 올리면 첫 시작 때 데이터 마이그레이션이 적용되고, 그 뒤에는 **3.2가 그 저장소를 제대로 읽지 못합니다.** 업그레이드 전에 `surreal db export`로 백업하세요.

**운영**

- Community 버전에서 Live Query는 같은 노드의 변경만 받습니다. 여러 노드 뒤에 로드밸런서를 두고 Live Query에 의존하면 알림이 누락될 수 있습니다.
- Node.js 임베디드 엔진은 플랫폼별 네이티브 바이너리(약 45MB)를 optional dependency로 받습니다. `npm install --omit=optional` 같은 설정을 쓰는 CI에서는 엔진이 로드되지 않습니다.
- 서버 앱에서는 요청마다 연결하지 말고, 프로세스 시작 시 `Surreal` 인스턴스 하나를 만들어 재사용하는 것이 공식 권장입니다. 사용자별 세션이 필요하면 `db.newSession()`을 씁니다.

## 비슷한 도구와 비교

아래 비교는 각 제품의 일반적인 특성을 바탕으로 한 개략적인 정리입니다. 세부 기능은 버전과 확장에 따라 달라지니 도입 전에 각 문서를 확인하세요.

| 항목 | SurrealDB | PostgreSQL | MongoDB | Neo4j | Supabase |
|---|---|---|---|---|---|
| 기본 모델 | 문서+그래프+관계형+벡터 | 관계형 (JSONB 확장) | 문서 | 그래프 | PostgreSQL 기반 BaaS |
| 쿼리 언어 | SurrealQL (+GraphQL, GQL) | SQL | MQL, 집계 파이프라인 | Cypher | SQL, 자동 생성 REST/GraphQL |
| 관계 탐색 | `->` 그래프 탐색, 레코드 링크 | JOIN, 재귀 CTE | `$lookup` | 네이티브 그래프 탐색 | JOIN |
| 벡터 검색 | 내장 (HNSW, DISKANN) | pgvector 확장 | Atlas Vector Search 등 | 벡터 인덱스 지원 | pgvector |
| 인증/행 권한 | DB에 내장 | RLS (인증은 별도) | 앱에서 처리 | 역할 기반 | Auth + RLS 제공 |
| 실시간 | Live Query 내장 | LISTEN/NOTIFY, 논리 복제 | Change Streams | 제한적 | Realtime 서비스 |
| 임베디드/브라우저 | 가능 (Rust, WASM) | 일반적이지 않음 | 일반적이지 않음 | 일반적이지 않음 | 불가 |
| 라이선스 | BSL 1.1 | PostgreSQL License | SSPL (Community) | GPLv3 (Community) | Apache 2.0 등 |
| 성숙도/생태계 | 비교적 신생 | 매우 성숙 | 성숙 | 그래프 분야 성숙 | 빠르게 성장 |

- **PostgreSQL**은 수십 년간 검증된 안정성과 방대한 확장, 도구, 인력 풀이 강점입니다. 관계형 데이터가 중심이고 그래프 탐색이 가끔 필요한 정도라면 여전히 가장 무난한 선택입니다.
- **MongoDB**는 문서 모델과 운영 도구, 매니지드 서비스가 성숙했습니다. 관계 탐색이 많아질수록 `$lookup`이 복잡해지는데, 이 부분이 SurrealDB가 노리는 지점입니다.
- **Neo4j**는 깊은 그래프 분석, 그래프 알고리즘 라이브러리, Cypher 생태계에서 앞서 있습니다. 그래프가 주인공이라면 Neo4j가, 그래프가 여러 모델 중 하나라면 SurrealDB가 맞을 가능성이 큽니다.
- **Supabase**는 PostgreSQL 위에 인증, 스토리지, 실시간, 자동 API를 얹은 BaaS입니다. "DB가 곧 백엔드"라는 방향은 SurrealDB와 비슷하지만, 기반이 검증된 PostgreSQL이라는 점이 큰 차이입니다.

## 장점과 한계

**장점**

- 문서, 그래프, 벡터, 전문 검색을 한 쿼리 언어와 한 트랜잭션 안에서 다룰 수 있습니다.
- 레코드 ID와 화살표 문법 덕분에 관계 쿼리가 짧고 읽기 쉽습니다.
- 인증, 행 단위 권한, Live Query가 내장되어 있어 작은 앱은 API 서버를 크게 줄일 수 있습니다.
- 단일 Rust 바이너리라 설치가 간단하고, 같은 엔진을 서버, 임베디드, 브라우저(WASM)에서 쓸 수 있습니다.
- 스키마리스로 시작해 스키마풀로 점진적으로 굳힐 수 있습니다.
- 3.3 기준으로 한국어 형태소 분리 사전이 기본 바이너리에 포함되어 한국어 전문 검색을 시도해 보기 쉽습니다.

**한계**

- **라이선스:** BSL 1.1은 OSI 기준 오픈소스가 아닙니다. 내부 서비스 백엔드로 쓰는 데는 대체로 문제가 없지만, DB 기능을 제3자에게 서비스로 제공하는 사업이라면 상용 라이선스가 필요합니다.
- **변경 속도:** 2.x → 3.x처럼 깨지는 변경이 크고, 마이너 버전(3.2 → 3.3)에서도 동작 변화와 일방향 데이터 마이그레이션이 있습니다. 업그레이드 전 릴리스 노트와 마이그레이션 문서 확인이 필수입니다.
- **생태계와 인력:** PostgreSQL, MongoDB에 비해 ORM, 마이그레이션 도구, 운영 노하우, 커뮤니티 답변이 적습니다. 학습한 SurrealQL은 다른 DB로 그대로 옮기기 어렵습니다.
- **분산 기능의 에디션 차이:** 장애 허용 클러스터, 분산 Live Query, 감사 로그 등은 Enterprise 기능입니다. Community로 대규모 고가용성 구성을 하려면 제약을 먼저 확인해야 합니다.
- **"다 된다"의 함정:** 한 엔진이 여러 모델을 지원한다고 해서 각 분야 전문 DB만큼 깊은 기능이나 성능을 보장하지는 않습니다. 핵심 워크로드는 직접 벤치마크해 보는 것이 좋습니다.

## 이런 분께 추천

- 문서형 데이터와 관계(팔로우, 좋아요, 추천)가 함께 중요한 SNS, 커뮤니티, 협업 도구를 만드는 분
- RAG나 AI 에이전트 메모리처럼 **벡터 + 그래프 + 메타데이터**를 한곳에 두고 싶은 분
- 프런트엔드 중심 팀이라 인증, 권한, 실시간 기능을 DB에 맡기고 백엔드를 최소화하고 싶은 분
- 로컬 우선(local-first) 앱이나 엣지, 데스크톱 앱에 쿼리 기능이 풍부한 임베디드 DB가 필요한 분
- 사이드 프로젝트에서 새로운 데이터 모델링 방식을 실험해 보고 싶은 분

## 이런 경우엔 다른 도구

- 회계, 결제처럼 보수적인 관계형 데이터가 중심이고 검증된 운영 도구와 인력이 중요하다면 **PostgreSQL**이 안전합니다.
- 오픈소스 라이선스(OSI 승인)가 조직 정책상 필수라면 PostgreSQL, 또는 Apache AGE 같은 PostgreSQL 그래프 확장 조합을 검토하세요.
- 그래프 알고리즘(커뮤니티 탐지, 경로 분석 등)이 핵심이라면 **Neo4j** 쪽 생태계가 더 풍부합니다.
- 인증, 스토리지, 실시간까지 갖춘 매니지드 BaaS를 원하지만 SQL 기반을 선호한다면 **Supabase**가 맞습니다.
- 수십억 건 규모의 벡터 검색 전용 워크로드라면 전용 벡터 DB와 비교 벤치마크를 먼저 해 보세요.

## 참고 링크

- [GitHub 저장소](https://github.com/surrealdb/surrealdb)
- [LICENSE (BSL 1.1 원문)](https://github.com/surrealdb/surrealdb/blob/main/LICENSE)
- [라이선스 안내 저장소](https://github.com/surrealdb/license)
- [공식 문서](https://surrealdb.com/docs)
- [CLI 설치](https://surrealdb.com/docs/explore/cli/install)
- [surreal launcher 명령](https://surrealdb.com/docs/reference/cli/launcher)
- [surreal db start](https://surrealdb.com/docs/reference/cli/db/commands/start)
- [Docker로 실행](https://surrealdb.com/docs/running/docker)
- [저장 엔진](https://surrealdb.com/docs/build/embedding/storage-engines)
- [배포 모델](https://surrealdb.com/docs/manage/self-hosted/deployment-models)
- [DEFINE TABLE](https://surrealdb.com/docs/reference/query-language/statements/define/table)
- [DEFINE FIELD](https://surrealdb.com/docs/reference/query-language/statements/define/field)
- [RELATE](https://surrealdb.com/docs/reference/query-language/statements/relate)
- [DEFINE ACCESS ... TYPE RECORD](https://surrealdb.com/docs/reference/query-language/statements/define/access/record)
- [LIVE SELECT](https://surrealdb.com/docs/reference/query-language/statements/live-select)
- [벡터 인덱스](https://surrealdb.com/docs/learn/data-models/vector-search/vector-indexes)
- [HTTP 프로토콜](https://surrealdb.com/docs/reference/rest-api/http-protocol)
- [JavaScript SDK: 연결](https://surrealdb.com/docs/reference/javascript/concepts/connecting-to-surrealdb)
- [JavaScript SDK: Live Query](https://surrealdb.com/docs/reference/javascript/concepts/live-queries)
- [JavaScript SDK: 임베디드 엔진](https://surrealdb.com/docs/reference/javascript/concepts/embedded-engines)
- [2.x → 3.x 업그레이드](https://surrealdb.com/docs/build/migrating/from-old-surrealdb-versions/2x-to-3x)
- [3.2 → 3.3 업그레이드](https://surrealdb.com/docs/build/migrating/from-old-surrealdb-versions/32-to-33)
- [Enterprise Edition](https://surrealdb.com/docs/manage/enterprise/product/database-enterprise)
- [SurrealDB Studio](https://surrealdb.com/docs/explore/studio) · [Surrealist 저장소](https://github.com/surrealdb/surrealist)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
