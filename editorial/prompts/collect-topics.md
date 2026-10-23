# 주제 수집 절차 (매주 월요일 자동 실행)

목표: 다음 한 주 동안 쓸 만한 글 주제 후보 **6개**(논문 2, 기술 2, 오픈소스 2)를 찾아 `editorial/backlog.yml`에 추가하는 PR을 하나 연다.
운영자는 이 PR을 보고 원하지 않는 항목의 status를 `rejected`로 바꾼 뒤 병합한다. 병합된 `approved` 항목이 글 작성 대기열이 된다.

## 0. 준비

1. `CLAUDE.md`를 읽고 블로그의 카테고리, 문체, 사실성 기준을 파악한다.
2. 이미 다룬 주제를 확인한다: `_posts/*/*.md`의 title, `editorial/backlog.yml`의 모든 항목(상태 무관), 열린 PR 제목(`gh pr list --state open` 가능하면).
   - 같은 프로젝트, 같은 논문, 같은 발표는 다시 제안하지 않는다. `rejected` 항목도 다시 제안하지 않는다.
3. 오늘 날짜(한국 시간)를 `TZ=Asia/Seoul date +%F`로 확인한다. 이하 “최근”은 오늘 기준 14일 이내를 뜻한다.

## 1. 후보 찾기

카테고리별로 아래 출처를 우선 살핀다. 접속이 안 되는 출처는 건너뛰고, 대신 웹 검색으로 같은 종류의 최신 정보를 찾는다.

**논문 (papers)**
- Hugging Face Daily Papers: https://huggingface.co/api/daily_papers (최근 7일, upvotes 많은 순)
- arXiv 최신 목록: https://arxiv.org/list/cs.AI/recent , https://arxiv.org/list/cs.CL/recent , https://arxiv.org/list/cs.LG/recent
- 기준: 실무 개발자에게 의미 있는 결과(에이전트, 코딩, RAG, 추론, 효율화, 평가 방법 등), 원문이 공개됨, 가능하면 코드 공개

**기술 (tech)**
- 주요 AI 회사 공식 발표: Anthropic, OpenAI, Google DeepMind, Meta AI, Mistral, Hugging Face 블로그 등
- 개발자 커뮤니티 화제: GeekNews https://news.hada.io , Hacker News https://hn.algolia.com/api/v1/search?tags=front_page
- 기준: 새 모델, 플랫폼, 표준(프로토콜), 개발 도구의 중요한 변화. 공식 1차 자료가 있어야 함. 루머나 2차 기사만 있는 주제는 제외

**오픈소스 (opensource)**
- GitHub Trending (주간): https://github.com/trending?since=weekly
- 최근 생성/급상승 저장소: `gh search repos --created ">$(date -d '-30 days' +%F)" --sort stars --limit 30` (gh 사용 가능 시)
- 큰 릴리스: 많이 쓰이는 프로젝트의 메이저 버전 출시
- 기준: 개발자가 실제로 도입을 검토할 만한 도구, README와 문서가 충실함, 최근 활동이 있음. 단순 목록(awesome-*), 튜토리얼 모음, 강의 저장소는 제외

## 2. 선별

후보를 모은 뒤 카테고리별로 2개씩 고른다. 우선순위:
1. 한국 개발자에게 실용적인가 (도입, 학습, 의사결정에 도움)
2. 1차 자료가 충분해 깊이 있는 글(동작 원리, 예제, 비교, 인사이트)을 쓸 수 있는가
3. 시의성 (최근 화제, 최근 출시)
4. 블로그 기존 글과 겹치지 않으면서 연결점이 있는가 (예: 이전 글의 대안 도구, 후속 연구)
5. 카테고리 안에서 주제가 한쪽으로 쏠리지 않는가

각 후보의 sources URL은 실제로 열리는지 확인한다(`curl -sIL -o /dev/null -w '%{http_code}' URL`, 200이어야 함).

## 3. backlog.yml에 추가

`editorial/backlog.yml`의 `items:` 끝에 추가한다(기존 항목은 수정하지 않음). `items: []`라면 리스트로 바꾼다.

```yaml
  - id: 영문-소문자-슬러그
    category: opensource
    title: "가제: 한국어로"
    why: "지금 다룰 이유 1~2문장 (수치나 날짜 근거 포함)"
    angle: "글에서 강조할 관점이나 인사이트 방향"
    sources:
      - https://github.com/owner/repo
      - https://공식-문서
    proposed_at: YYYY-MM-DD
    status: approved
```

- id는 기존 글 슬러그, backlog의 다른 id와 겹치지 않게 한다.
- 시의성이 특히 높은 항목은 `priority: high`를 추가한다(주당 최대 2개).

## 4. PR 열기

- 브랜치: `topics/YYYY-MM-DD`
- 커밋 메시지: `Propose N topics for week of YYYY-MM-DD`
- PR 제목: `[주제 후보] YYYY-MM-DD 주간 N건`
- PR 본문(한국어):
  - 맨 위 안내: “원하지 않는 항목은 status를 `rejected`로 바꾼 뒤 병합해 주세요. 병합된 approved 항목은 화·목요일에 하나씩 글로 작성됩니다.”
  - 후보 표: 카테고리 | 가제 | 추천 이유 | 핵심 출처 링크
  - 검토했지만 제외한 주요 후보 3~5개와 제외 이유(짧게)
- PR은 병합하지 않는다. main에 직접 푸시하지 않는다.

후보가 기준을 충족하지 못해 6개를 채우지 못하면 찾은 만큼만 제안하고 PR 본문에 이유를 적는다. 하나도 없으면 PR을 열지 않는다.
