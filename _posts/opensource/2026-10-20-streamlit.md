---
layout: default
title: "[오픈소스 소개] Streamlit: 파이썬 스크립트를 몇 분 만에 웹 앱으로"
date: 2026-10-20
categories: [opensource]
---

# [오픈소스 소개] Streamlit: 파이썬 스크립트를 몇 분 만에 웹 앱으로

- **저장소:** [streamlit/streamlit](https://github.com/streamlit/streamlit) · [streamlit.io](https://streamlit.io) · [문서](https://docs.streamlit.io)
- **라이선스:** Apache 2.0
- **언어:** Python
- **현황 (2026-10-20 기준):** GitHub 스타 약 4.6만 개, 최신 릴리스 1.66.0 (10월 14일)

## 한 줄 요약

**HTML·CSS·JavaScript 없이 평범한 파이썬 스크립트만으로 대시보드, 데이터 도구, LLM 챗봇 같은 웹 앱을 만드는 프레임워크**입니다. 사용자가 무언가를 조작할 때마다 스크립트를 위에서 아래로 다시 실행하는 독특한 모델 덕분에 코드가 단순하지만, 그만큼 캐싱과 세션 상태를 이해해야 제대로 쓸 수 있습니다.

## 어떤 문제를 푸나

데이터 분석가나 ML 엔지니어가 결과물을 다른 사람에게 보여주려면 보통 이런 길을 거칩니다.

- 노트북(Jupyter)을 그대로 공유한다: 상대방이 코드를 실행할 줄 알아야 합니다.
- Flask/FastAPI로 백엔드를 만들고 React로 프론트엔드를 만든다: 웹 개발 지식과 시간이 많이 듭니다.
- BI 도구를 쓴다: 파이썬 모델이나 커스텀 로직을 붙이기 어렵습니다.

Streamlit은 이 간극을 메웁니다. `st.slider()` 를 호출하면 슬라이더가 화면에 생기고, 그 반환값이 곧 사용자가 고른 값입니다. 콜백 등록이나 HTTP 엔드포인트 설계 없이, 위에서 아래로 읽히는 스크립트 그대로 앱이 됩니다.

```python
import streamlit as st

x = st.slider("Select a value")
st.write(x, "squared is", x * x)
```

## 핵심 개념 / 동작 원리

### 1. 스크립트는 매번 처음부터 다시 실행된다

Streamlit의 가장 중요한 특징입니다. 공식 문서의 "Data flow" 설명에 따르면, 화면을 갱신해야 할 때 Streamlit은 **파이썬 스크립트 전체를 위에서 아래로 다시 실행(rerun)**합니다. 기본적으로 두 가지 경우에 일어납니다.

- 앱의 소스 코드를 수정했을 때
- 사용자가 위젯과 상호작용했을 때 (슬라이더 드래그, 텍스트 입력, 버튼 클릭 등)

```
 브라우저(클라이언트)          파이썬 서버
 ─────────────────          ─────────────
 슬라이더를 5→7로 변경  ──▶  스크립트 1행부터 재실행
                            x = st.slider(...)  # 7
                            무거운 계산 ...
 화면 갱신            ◀──   st.write(...) 결과 전송
```

위젯 함수는 "위젯을 그려라"와 "현재 값을 돌려줘라"를 동시에 합니다. 처음 실행에서는 기본값을, 사용자가 값을 바꾼 뒤의 재실행에서는 바뀐 값을 돌려줍니다. 그래서 일반 파이썬처럼 `if`, `for` 로 흐름을 짤 수 있습니다.

위젯에 `on_change` 나 `on_click` 콜백을 넘기면, 그 콜백은 **스크립트의 나머지보다 먼저** 실행됩니다.

### 2. 재실행 모델이 만드는 두 가지 문제

이 모델은 개발을 쉽게 만들지만, 캐싱 문서가 직접 꼽는 두 가지 문제가 생깁니다.

1. **느린 함수가 매번 다시 돈다.** CSV 로드, DB 쿼리, 모델 로드가 버튼 하나 누를 때마다 반복됩니다.
2. **객체가 매번 새로 만들어진다.** 일반 변수는 재실행마다 초기화되므로 카운터나 대화 기록을 유지할 수 없습니다.

공식 문서의 카운터 예시가 두 번째 문제를 잘 보여줍니다.

```python
count = 0
if st.button("Increment"):
    count += 1
st.write("Count = ", count)   # 몇 번을 눌러도 항상 1
```

버튼을 누를 때마다 스크립트가 다시 돌면서 `count = 0` 부터 시작하기 때문입니다.

### 3. 해결책: 캐싱과 세션 상태

| 구분 | 캐싱 (`st.cache_data`, `st.cache_resource`) | 세션 상태 (`st.session_state`) |
|---|---|---|
| 무엇을 기준으로 저장 | 함수 + 입력값 | 문자열 키 |
| 누가 공유 | 모든 사용자, 모든 세션 | 해당 세션(브라우저 탭) 하나 |
| 주 용도 | 비싼 계산·로드 결과 재사용 | 사용자별 진행 상태, 입력 기록 |
| 예 | 공용 데이터셋, ML 모델, DB 연결 | 카운터, 로그인 여부, 채팅 기록 |

여기서 **세션**은 앱을 보는 브라우저 탭 하나를 뜻합니다. 탭을 두 개 열면 세션도 두 개이고, 새로고침하면 세션 상태가 초기화됩니다.

### 4. 재실행 범위를 줄이는 장치

전체 재실행이 부담스러울 때 쓰는 도구들입니다.

- **폼(`st.form`):** 폼 안의 위젯은 값을 바꿔도 재실행하지 않고, 제출 버튼을 누를 때 한 번에 보냅니다.
- **프래그먼트(`@st.fragment`, 1.37.0부터):** 함수 단위로 묶어서, 그 안의 위젯을 조작하면 해당 함수만 다시 실행합니다. `run_every="10s"` 로 주기적 자동 갱신도 됩니다.
- **`on_change="ignore"`:** 일부 위젯은 값이 바뀌어도 재실행하지 않고, 다음 재실행 때 새 값을 전달합니다.

### 5. 클라이언트-서버 구조

`streamlit run app.py` 를 실행하면 파이썬 서버가 뜨고, 브라우저가 클라이언트가 됩니다. 서버는 Starlette 위에서 Uvicorn으로 돌며, 탭마다 WebSocket 연결을 하나씩 유지합니다. 이 구조에서 나오는 실무상 결과가 있습니다.

- 모든 사용자의 계산은 서버 한 대가 처리하므로 동시 사용자 수에 맞게 서버 크기를 잡아야 합니다.
- 앱은 사용자 PC의 파일에 접근할 수 없고, `st.file_uploader` 로 올린 파일만 다룹니다.
- `webbrowser` 처럼 외부 프로그램을 여는 코드는 사용자 PC가 아니라 서버에서 실행됩니다.
- 서버를 여러 대로 늘려 로드밸런싱하면 세션 고정(session affinity, sticky session)을 켜야 업로드 파일과 미디어가 제대로 동작합니다.

## 주요 기능

### 텍스트·데이터·차트

- `st.write` 는 문자열, 데이터프레임, 차트 등 무엇이든 알맞게 그려주는 만능 함수입니다. 변수나 값만 한 줄에 써도 화면에 출력되는 "매직(magic)" 기능도 있습니다.
- `st.dataframe`, `st.table`, 편집 가능한 표 `st.data_editor`
- `st.line_chart`, `st.bar_chart`, `st.scatter_chart`, `st.map` 같은 간단한 차트와 Altair, Plotly 등 외부 라이브러리 차트 표시
- `st.metric`, `st.json`, `st.image` 등

### 입력 위젯

`st.button`, `st.slider`, `st.selectbox`, `st.text_input`, `st.number_input`, `st.checkbox`, `st.color_picker`, `st.file_uploader` 등. 위젯에 `key` 를 주면 그 값이 `st.session_state[key]` 에 자동으로 연결됩니다.

### 레이아웃과 컨테이너

| 컨테이너 | 용도 |
|---|---|
| `st.sidebar` | 왼쪽 고정 패널. 필터·설정 컨트롤 |
| `st.columns` | 요소를 가로로 나란히. `st.columns([2, 1])` 처럼 비율 지정 |
| `st.tabs`, `st.expander`, `st.popover` | 접거나 겹쳐서 공간 절약 |
| `st.container` | 요소를 묶고, 스크립트 순서와 다른 위치에 그리기. `border=True`, `horizontal=True` 지원 |
| `st.empty` | 요소 하나짜리 자리 표시자. 교체·삭제 가능 |
| `st.dialog` | 모달 대화상자 |

주의할 점: `st.tabs`, `st.expander`, `st.popover` 는 기본적으로 **닫혀 있어도 안의 코드가 매번 실행**됩니다. 무거운 탭이 있다면 `on_change="rerun"` 으로 열림 상태를 추적하고 `.open` 일 때만 계산하는 지연 로딩을 쓸 수 있습니다.

### 상태와 실행 흐름 제어

- `st.session_state`: 세션별 딕셔너리. `st.session_state["k"]` 와 `st.session_state.k` 둘 다 됩니다.
- 콜백: `on_change`/`on_click` 과 `args`, `kwargs`
- `st.form`, `st.form_submit_button`: 입력을 모아 한 번에 제출
- `@st.fragment`: 부분 재실행
- `st.rerun()`: 즉시 재실행 요청

### 캐싱

- `@st.cache_data`: DataFrame, 리스트, 문자열 같은 **직렬화 가능한 데이터**를 반환하는 함수용. 결과를 pickle로 저장하고 **호출할 때마다 복사본**을 돌려주므로, 반환값을 수정해도 캐시가 오염되지 않습니다.
- `@st.cache_resource`: ML 모델, DB 연결처럼 **직렬화할 수 없거나 하나만 있어야 하는 자원**용. 복사하지 않고 **같은 객체를 모든 세션이 공유**합니다(싱글턴).

공통 옵션도 알아두면 좋습니다.

| 옵션 | 설명 |
|---|---|
| `ttl` | 캐시 유효 시간. `ttl=3600` 또는 `timedelta(hours=1)` |
| `max_entries` | 캐시 항목 최대 개수. 넘으면 가장 오래된 것부터 제거 |
| `show_spinner` | 계산 중 스피너 표시 여부나 문구 |
| `hash_funcs` | 기본으로 해시할 수 없는 타입의 해시 방법 지정 |
| `_param` | 매개변수 이름 앞에 `_` 를 붙이면 캐시 키에서 제외 |
| `persist="disk"` | (`cache_data`) 디스크에 저장 |
| `scope="session"` | (`cache_data`) 세션이 끊기면 캐시도 제거 |

캐시를 비울 때는 `load_data.clear()` 처럼 함수별로, 또는 `st.cache_data.clear()` 로 전체를 비웁니다. 1.16.0부터는 캐시 함수 안에 `st.success` 같은 Streamlit 명령을 넣어도 되고, 캐시가 적중하면 그 출력도 재생됩니다. `async def` 함수도 캐싱할 수 있습니다.

### 멀티페이지 앱

`st.Page` 와 `st.navigation` 이 현재 권장하는 방식입니다. 진입점 파일(entrypoint)이 라우터 역할을 하고, 각 페이지는 파이썬 파일이나 함수로 정의합니다. 세션 상태는 페이지 사이에서 유지됩니다. 예전 방식인 `pages/` 디렉터리 자동 인식도 여전히 있습니다.

### LLM 챗봇용 채팅 요소

- `st.chat_message("user" | "assistant")`: 아바타와 스타일이 적용된 메시지 컨테이너. 안에 차트, 표 등 어떤 요소든 넣을 수 있습니다.
- `st.chat_input`: 화면 하단의 채팅 입력창. 아직 보낸 메시지가 없으면 `None` 을 반환합니다. 1.66.0 소스 기준으로 `accept_file`, `file_type`, `max_chars` 같은 매개변수도 있습니다.
- `st.write_stream`: 제너레이터나 LLM SDK의 스트림을 받아 타자 치듯 출력하고, 완성된 전체 텍스트를 반환합니다.

### 비밀 값과 데이터 연결

- `st.secrets`: `.streamlit/secrets.toml` (프로젝트) 또는 `~/.streamlit/secrets.toml` (전역)을 읽습니다. 둘 다 있으면 프로젝트 파일이 우선합니다. 최상위 키는 환경 변수로도 노출됩니다.
- `st.connection`: SQL, Snowflake 등에 연결하고 캐싱까지 알아서 처리합니다. 접속 정보는 secrets의 `[connections.이름]` 섹션에서 읽습니다.

### 테스트와 확장

- `st.testing` 의 앱 테스트 프레임워크로 브라우저 없이 앱 동작을 테스트할 수 있습니다.
- 표준 위젯으로 부족하면 커스텀 컴포넌트(v1, v2)로 직접 프론트엔드를 붙이거나 커뮤니티 컴포넌트를 씁니다.

## 설치와 시작

공식 설치 문서 기준입니다. 1.66.0의 `pyproject.toml` 은 Python 3.11 이상을 요구합니다.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate.bat
pip install streamlit
streamlit hello                  # 예제 앱이 브라우저에 열리면 성공
```

`streamlit` 명령이 안 잡히면 `python -m streamlit hello` 로 실행합니다. macOS에서는 일부 의존성 설치를 위해 Xcode 명령줄 도구가 필요하다고 문서가 안내합니다.

앱 실행은 이렇게 합니다.

```bash
streamlit run streamlit_app.py
```

코드를 저장하면 브라우저 오른쪽 위에 재실행 안내가 뜨고, "Always rerun" 을 고르면 저장할 때마다 자동으로 갱신됩니다.

## 실전 예제

### 예제 1. CSV 업로드 대시보드 + 캐싱

CSV를 올리면 컬럼을 골라 필터링하고 차트를 그리는 대시보드입니다.

```python
import io

import pandas as pd
import streamlit as st

st.set_page_config(page_title="CSV 대시보드", layout="wide")
st.title("CSV 대시보드")


@st.cache_data(show_spinner="CSV를 읽는 중...")
def load_csv(raw: bytes) -> pd.DataFrame:
    # 업로드 객체 대신 bytes를 넘기면 내용이 같을 때 캐시가 재사용됩니다
    return pd.read_csv(io.BytesIO(raw))


@st.cache_data
def summarize(df: pd.DataFrame, group_col: str, value_col: str) -> pd.DataFrame:
    return df.groupby(group_col, as_index=False)[value_col].sum()


uploaded = st.sidebar.file_uploader("CSV 파일", type="csv")
if uploaded is None:
    st.info("왼쪽에서 CSV 파일을 올려 주세요.")
    st.stop()

df = load_csv(uploaded.getvalue())

numeric_cols = df.select_dtypes("number").columns.tolist()
other_cols = [c for c in df.columns if c not in numeric_cols]
if not numeric_cols or not other_cols:
    st.warning("숫자 컬럼과 범주 컬럼이 하나 이상씩 필요합니다.")
    st.stop()

group_col = st.sidebar.selectbox("그룹 기준", other_cols)
value_col = st.sidebar.selectbox("값", numeric_cols)

col1, col2, col3 = st.columns(3)
col1.metric("행 수", f"{len(df):,}")
col2.metric("합계", f"{df[value_col].sum():,.0f}")
col3.metric("그룹 수", df[group_col].nunique())

summary = summarize(df, group_col, value_col)
st.bar_chart(summary, x=group_col, y=value_col)

with st.expander("원본 데이터"):
    st.dataframe(df)
```

포인트는 이렇습니다.

- 사이드바에서 선택을 바꿀 때마다 스크립트 전체가 다시 돌지만, `load_csv` 와 `summarize` 는 입력이 같으면 캐시에서 바로 돌려줍니다.
- `st.cache_data` 는 복사본을 돌려주므로 아래에서 `df` 를 수정해도 캐시된 원본은 안전합니다.
- `st.stop()` 은 그 지점에서 이번 실행을 멈춥니다. 파일이 없을 때 이후 코드를 건너뛰는 데 유용합니다.
- 업로드 크기 기본 제한은 200MB이며 `server.maxUploadSize` 설정으로 바꿀 수 있습니다.

### 예제 2. 세션 상태 카운터와 폼

공식 문서의 카운터를 콜백과 폼으로 확장한 예입니다.

```python
import datetime

import streamlit as st

st.title("카운터")

# 1) 세션 상태는 "없을 때만" 초기화
if "count" not in st.session_state:
    st.session_state.count = 0
    st.session_state.history = []


# 2) 콜백은 스크립트 나머지보다 먼저 실행된다
def add(step: int):
    st.session_state.count += step
    st.session_state.history.append((datetime.datetime.now(), step))


c1, c2, c3 = st.columns(3)
c1.button("+1", on_click=add, args=(1,))
c2.button("-1", on_click=add, args=(-1,))
c3.button("초기화", on_click=lambda: st.session_state.update(count=0, history=[]))

st.metric("현재 값", st.session_state.count)

# 3) 폼: 안의 위젯을 바꿔도 제출 전에는 재실행하지 않는다
with st.form("bulk_add", clear_on_submit=True):
    step = st.number_input("한 번에 더할 값", value=10, step=1, key="bulk_step")
    memo = st.text_input("메모")
    submitted = st.form_submit_button("적용")

if submitted:
    add(int(step))
    st.success(f"{step} 만큼 더했습니다. 메모: {memo or '(없음)'}")

st.write("최근 변경", st.session_state.history[-5:])
```

콜백을 쓰는 이유가 중요합니다. `if st.button(...): count += 1` 로 쓰면 버튼 아래쪽 코드에만 새 값이 보이고, 버튼보다 위에 그려진 요소는 한 박자 늦게 갱신됩니다. 콜백은 재실행 시작 전에 상태를 바꾸므로 화면 전체가 일관된 값을 보여줍니다.

폼에는 제약이 있습니다. 폼 안에는 `st.button` 과 `st.download_button` 을 넣을 수 없고, 폼 안에 다른 폼을 넣을 수 없습니다. 또 `st.button` 과 `st.file_uploader` 는 세션 상태 API로 값을 설정할 수 없습니다.

### 예제 3. LLM 챗봇 UI

공식 튜토리얼 "Build a basic LLM chat app" 의 구조를 따른 예입니다. 먼저 API 없이 동작하는 버전입니다.

```python
import random
import time

import streamlit as st

st.title("Simple chat")

# 대화 기록은 세션 상태에 보관
if "messages" not in st.session_state:
    st.session_state.messages = []

# 재실행될 때마다 지금까지의 대화를 다시 그린다
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def response_generator():
    response = random.choice(["안녕하세요!", "무엇을 도와드릴까요?", "질문을 더 자세히 알려 주세요."])
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


if prompt := st.chat_input("메시지를 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.write_stream(response_generator())
    st.session_state.messages.append({"role": "assistant", "content": response})
```

실제 LLM을 붙일 때는 `response_generator()` 자리에 SDK의 스트리밍 응답을 넣습니다. 튜토리얼은 OpenAI SDK로 이렇게 합니다.

```python
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

with st.chat_message("assistant"):
    stream = client.chat.completions.create(
        model=st.session_state["openai_model"],   # 사용할 모델 이름
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
        stream=True,
    )
    response = st.write_stream(stream)
```

API 키는 `.streamlit/secrets.toml` 에 넣고 `.gitignore` 에 추가합니다.

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "YOUR_API_KEY"
```

이 예제가 재실행 모델을 잘 보여줍니다. 메시지를 보낼 때마다 스크립트가 처음부터 돌기 때문에, 기록을 `st.session_state.messages` 에 쌓아 두고 매번 루프로 다시 그리는 것입니다. SDK 클라이언트처럼 재사용할 객체는 `@st.cache_resource` 함수로 감싸 두면 재실행마다 새로 만들지 않습니다.

### 예제 4. 멀티페이지 앱과 로그인 분기

```
my_app/
├── streamlit_app.py
├── reports/
│   ├── dashboard.py
│   └── bugs.py
└── tools/
    └── search.py
```

```python
# streamlit_app.py
import streamlit as st

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def login():
    if st.button("Log in"):
        st.session_state.logged_in = True
        st.rerun()


def logout():
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()


login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
dashboard = st.Page("reports/dashboard.py", title="Dashboard",
                    icon=":material/dashboard:", default=True)
bugs = st.Page("reports/bugs.py", title="Bug reports", icon=":material/bug_report:")
search = st.Page("tools/search.py", title="Search", icon=":material/search:")

if st.session_state.logged_in:
    pg = st.navigation({
        "Account": [logout_page],
        "Reports": [dashboard, bugs],
        "Tools": [search],
    })
else:
    pg = st.navigation([login_page])

st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
pg.run()
```

규칙은 이렇습니다.

- `st.navigation` 은 한 번의 실행에서 한 번만, 진입점 파일에서만 호출합니다.
- 반환된 페이지는 직접 `.run()` 해야 실행됩니다.
- 딕셔너리로 넘기면 섹션 헤더가 생기고, `position` 매개변수로 메뉴를 사이드바나 상단에 둘 수 있습니다.
- 진입점에 넣은 요소(예: 공통 사이드바)는 모든 페이지에 공통으로 나타납니다.
- 넘기는 페이지 목록을 바꾸는 것만으로 권한별 메뉴를 만들 수 있습니다. 위 예에서 로그인 전에는 다른 페이지 URL로 들어와도 인식되지 않습니다.

## 실무 팁 & 자주 겪는 문제

- **"버튼을 눌렀는데 값이 유지되지 않아요."** 일반 변수는 재실행마다 초기화됩니다. 유지해야 하는 값은 `st.session_state` 에 넣고, `if "key" not in st.session_state:` 로 한 번만 초기화합니다.
- **`st.button` 의 반환값은 클릭 직후 한 번만 `True` 입니다.** 다음 재실행에서는 다시 `False` 가 됩니다. "버튼을 누르면 이후로 계속 보이는" 동작은 세션 상태 플래그로 만듭니다.
- **캐싱 선택 기준.** DB에 저장할 법한 데이터면 `cache_data`, 연결이나 모델처럼 저장할 수 없는 것이면 `cache_resource` 입니다. `cache_resource` 로 받은 객체를 수정하면 모든 사용자에게 영향을 주므로 스레드 안전성에 주의합니다.
- **해시할 수 없는 인자.** `UnhashableParamError` 가 나면 인자 이름 앞에 `_` 를 붙여 캐시 키에서 빼거나 `hash_funcs` 로 해시 방법을 알려줍니다. `_` 로 뺀 인자가 실제로 결과에 영향을 준다면 잘못된 캐시 결과가 나오니 조심합니다.
- **DB 결과는 `ttl` 을 꼭 겁니다.** 그렇지 않으면 서버가 재시작될 때까지 옛 데이터가 남습니다.
- **`st.cache_data` 와 pickle.** 반환값을 pickle로 저장하므로 신뢰할 수 없는 데이터를 캐시하지 않도록 문서가 경고합니다. 수억 행 규모의 아주 큰 데이터는 복사 비용 때문에 느려질 수 있어, 이 경우 `cache_resource` 를 고려하되 수정하지 않도록 합니다.
- **무거운 탭과 expander.** 닫힌 탭의 코드도 매번 실행됩니다. 지연 로딩(`on_change="rerun"` 과 `.open`)이나 캐싱을 씁니다.
- **일부만 자주 바뀌는 화면.** 실시간 지표 카드처럼 일부만 갱신하면 되는 곳은 `@st.fragment(run_every="5s")` 로 분리합니다.
- **세션 상태는 영구 저장소가 아닙니다.** 탭을 닫거나 서버가 재시작되면 사라집니다. 오래 남겨야 하는 데이터는 DB나 파일에 저장합니다.
- **secrets 파일은 커밋하지 않습니다.** 실행 중에 `secrets.toml` 을 새로 만들면 서버를 재시작해야 반영됩니다.
- **Community Cloud 배포.** GitHub 저장소를 연결해 배포하며, 의존성은 `requirements.txt`(저장소 루트나 진입점 파일과 같은 디렉터리), OS 패키지는 `packages.txt` 로 지정합니다. 비밀 값은 배포 시 "Advanced settings" 에 `secrets.toml` 내용을 붙여넣습니다. 앱은 저장소 루트에서 실행되므로 이미지 등 파일 경로는 루트 기준으로 씁니다. 회사 환경이라면 Docker, Kubernetes 배포 튜토리얼이나 Snowflake 배포를 검토합니다.
- **AI 코딩 에이전트를 쓴다면** 설치 문서가 안내하는 `streamlit skills` 명령으로 최신 API를 따르는 공식 에이전트 스킬을 설치할 수 있습니다.

## 비슷한 도구와 비교

| 항목 | Streamlit | Gradio | Dash | Panel |
|---|---|---|---|---|
| 만든 곳 | Streamlit (Snowflake) | Hugging Face 생태계 | Plotly | HoloViz |
| 라이선스 | Apache 2.0 | Apache 2.0 | MIT | BSD-3-Clause |
| 실행 모델 | 상호작용마다 스크립트 전체 재실행 (폼·프래그먼트로 범위 축소) | 이벤트가 발생하면 연결된 함수만 실행 | 입력·출력을 선언한 콜백 함수 실행 | 위젯과 함수를 반응형으로 연결 |
| 강점 | 가장 짧은 코드, 빠른 프로토타입, 채팅 요소 | ML 모델 데모, 입력→출력 인터페이스, Hugging Face Spaces 공유 | 세밀한 레이아웃과 Plotly 기반 시각화, 대규모 대시보드 | Jupyter 노트북 안팎에서 같은 코드 사용, 다양한 시각화 라이브러리 지원 |
| 학습 난이도 | 낮음 | 낮음 | 중간 (콜백 구조 이해 필요) | 중간 |
| 무료 호스팅 | Community Cloud | Hugging Face Spaces | 직접 호스팅 위주 | 직접 호스팅 위주 |

간단히 정리하면 이렇습니다.

- 데이터 앱이나 사내 도구를 가장 빨리 만들고 싶다면 Streamlit
- 모델 하나의 입력과 출력을 보여주는 데모라면 Gradio
- 상호작용이 많고 복잡한 프로덕션 대시보드라면 콜백으로 갱신 범위를 정밀하게 제어하는 Dash
- 노트북 작업을 그대로 앱으로 옮기고 싶다면 Panel

## 장점과 한계

**장점**

- 파이썬만 알면 됩니다. 위젯 호출 결과가 곧 값이라 코드가 일반 스크립트처럼 읽힙니다.
- 저장하면 바로 반영되는 개발 경험이 빠릅니다.
- 캐싱, 세션 상태, 멀티페이지, 채팅 요소, secrets, DB 연결까지 데이터 앱에 필요한 것이 기본 제공됩니다.
- Community Cloud로 GitHub 저장소에서 바로 무료 배포할 수 있고, 갤러리와 커뮤니티 컴포넌트가 풍부합니다.

**한계**

- **재실행 모델의 성능 한계.** 기본적으로 매 상호작용마다 스크립트 전체가 다시 돕니다. 앱이 커질수록 캐싱, 폼, 프래그먼트를 신경 써서 설계해야 하고, 잘못 설계하면 느려지고 상태 관리가 복잡해집니다.
- **서버 한 대가 모든 계산을 담당.** 세션마다 서버 메모리를 쓰므로 동시 사용자가 많은 서비스에는 용량 계획이 필요하고, 수평 확장 시 세션 고정이 필요합니다.
- **커스텀 UI 제약.** 제공되는 위젯과 레이아웃 안에서는 쉽지만, 픽셀 단위 디자인이나 복잡한 상호작용은 커스텀 컴포넌트(프론트엔드 코드)를 직접 만들어야 합니다.
- **상태가 휘발성.** 세션 상태는 탭을 닫거나 서버가 재시작되면 사라집니다.
- **외부 기여 일시 중단.** README에 따르면 현재 Streamlit 메인테이너 팀 외부의 Pull Request를 받지 않습니다. 버그 제보, 기능 요청, 이슈 투표, 스펙 의견, 커스텀 컴포넌트 제작, streamlit-extras 기여로 참여할 수 있습니다.

## 이런 분께 추천 / 이런 경우엔 다른 도구

**추천**

- 분석 결과를 동료가 직접 조작해 볼 수 있게 공유하고 싶은 데이터 분석가
- 모델 데모나 사내 LLM 챗봇 프로토타입을 빠르게 만들어야 하는 ML 엔지니어
- 웹 개발은 몰라도 파이썬은 익숙한 분
- 사내 운영 도구, 간단한 관리 화면을 하루 안에 만들고 싶은 팀

**다른 도구가 나은 경우**

- 많은 사용자가 쓰는 공개 서비스, 정교한 디자인과 SEO가 중요한 웹사이트라면 일반 웹 프레임워크(FastAPI/Django + React 등)
- 갱신 범위를 콜백 단위로 세밀하게 제어해야 하는 복잡한 대시보드라면 Dash
- 모델 하나의 입력·출력 데모를 Hugging Face에 올리는 것이 목적이라면 Gradio
- 노트북 중심으로 작업하면서 그대로 앱화하고 싶다면 Panel

## 참고 링크

- [Streamlit GitHub 저장소 / README](https://github.com/streamlit/streamlit)
- [Basic concepts (Data flow, 위젯, 레이아웃)](https://docs.streamlit.io/get-started/fundamentals/main-concepts)
- [Advanced concepts (캐싱, 세션 상태, 연결)](https://docs.streamlit.io/get-started/fundamentals/advanced-concepts)
- [Install Streamlit using command line](https://docs.streamlit.io/get-started/installation/command-line)
- [Client-server architecture](https://docs.streamlit.io/develop/concepts/architecture/architecture)
- [Caching overview](https://docs.streamlit.io/develop/concepts/architecture/caching)
- [Add statefulness to apps (Session State)](https://docs.streamlit.io/develop/concepts/architecture/session-state)
- [Using forms](https://docs.streamlit.io/develop/concepts/architecture/forms)
- [Working with fragments](https://docs.streamlit.io/develop/concepts/architecture/fragments)
- [Using layouts and containers](https://docs.streamlit.io/develop/concepts/app-design/layouts-and-containers)
- [Define multipage apps with st.Page and st.navigation](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation)
- [Build a basic LLM chat app](https://docs.streamlit.io/develop/tutorials/llms/conversational-apps)
- [Secrets management](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
- [Community Cloud: App dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) · [Status and limitations](https://docs.streamlit.io/deploy/streamlit-community-cloud/status)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
