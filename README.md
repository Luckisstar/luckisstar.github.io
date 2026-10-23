# luckisstar.github.io

AI 논문, 최신 기술, 오픈소스 프로젝트를 한국어로 소개하는 블로그: https://luckisstar.github.io

## 글 발행 흐름

| 요일 (KST) | 누가 | 무엇을 |
|---|---|---|
| 월 07:00 | Claude (자동) | 주제 후보 6개를 `editorial/backlog.yml`에 추가하는 PR `[주제 후보] …` 생성 |
| 월~화 | 운영자 | 원하지 않는 후보의 status를 `rejected`로 바꾸고 PR 병합 |
| 화·목 07:00 | Claude (자동) | 승인된 주제 하나를 조사해 글을 쓰고 PR `[글] …` 생성 |
| 수시 | 운영자 | 글 PR을 읽고(필요하면 EDITOR_NOTE 자리에 의견 추가) 병합하면 게시 |

- 작성 기준: [`CLAUDE.md`](CLAUDE.md)
- 절차: [`editorial/prompts/`](editorial/prompts/) · 템플릿: [`editorial/templates/`](editorial/templates/)
- 검증: `python3 scripts/validate_posts.py` (PR마다 GitHub Actions에서도 실행)
