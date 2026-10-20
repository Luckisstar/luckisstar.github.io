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

**HTML·CSS·JavaScript 없이 파이썬 코드만으로 데이터 앱을 만드는 프레임워크**입니다. 대시보드, 리포트, 챗봇 앱을 몇 주가 아니라 몇 분 만에 만들 수 있습니다.

## 왜 쓰나

- **파이썬답고 단순함:** 평소 쓰던 파이썬 스크립트에 몇 줄만 추가하면 됩니다.
- **빠른 프로토타이핑:** 만든 앱을 다른 사람이 바로 써보고 피드백을 줄 수 있습니다.
- **라이브 편집:** 코드를 저장하면 앱 화면이 즉시 갱신됩니다.
- **무료 배포:** [Community Cloud](https://streamlit.io/cloud)에 무료로 올려 공유할 수 있습니다.

## 빠르게 시작하기

```bash
pip install streamlit
streamlit hello      # 예제 앱이 브라우저에서 열리면 설치 완료
```

`streamlit_app.py` 파일을 만들고:

```python
import streamlit as st

x = st.slider("Select a value")
st.write(x, "squared is", x * x)
```

실행하면 슬라이더가 있는 웹 앱이 열립니다.

```bash
streamlit run streamlit_app.py
```

## 이런 걸 만들 수 있어요

- LLM·챗봇 앱
- 데이터 분석 대시보드
- 머신러닝 모델 데모
- 금융·비즈니스 리포트, 지도 시각화

다양한 예시는 [갤러리](https://streamlit.io/gallery)에서 볼 수 있고, 커뮤니티가 만든 [Streamlit Components](https://streamlit.io/components)로 기능을 확장할 수도 있습니다.

## 참고

현재 Streamlit은 **외부 기여자의 Pull Request를 일시적으로 받지 않습니다.** 버그 제보, 기능 요청, 이슈 투표, 커스텀 컴포넌트 제작으로 기여할 수 있습니다.

## 이런 분께 추천

- 분석 결과를 동료에게 인터랙티브하게 보여주고 싶은 데이터 분석가
- 모델 데모를 빠르게 만들어야 하는 머신러닝 엔지니어
- 웹 개발은 몰라도 파이썬은 아는 분

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
