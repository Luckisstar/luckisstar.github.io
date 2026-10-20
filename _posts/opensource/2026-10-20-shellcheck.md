---
layout: default
title: "[오픈소스 소개] ShellCheck: 셸 스크립트의 실수를 미리 잡아주는 정적 분석 도구"
date: 2026-10-20
categories: [opensource]
---

# [오픈소스 소개] ShellCheck: 셸 스크립트의 실수를 미리 잡아주는 정적 분석 도구

- **저장소:** [koalaman/shellcheck](https://github.com/koalaman/shellcheck) · [shellcheck.net](https://www.shellcheck.net)
- **라이선스:** GPL v3
- **언어:** Haskell
- **현황 (2026-10-20 기준):** GitHub 스타 약 4만 개, 최신 릴리스 v0.11.0 (2025년 8월)

## 한 줄 요약

**bash/sh 스크립트를 실행하기 전에 문법 오류와 흔한 실수를 찾아 알려주는 린터**입니다.

## 무엇을 잡아주나

ShellCheck의 목표는 세 가지입니다.

1. 초보자가 자주 하는 **문법 실수**와 알아보기 힘든 에러 메시지를 쉽게 설명
2. 중급자가 겪는 **이상하게 동작하는 코드**의 원인 짚어주기
3. 숙련자의 스크립트도 나중에 깨질 수 있는 **미묘한 함정** 알려주기

**잡아내는 실수 예시**

```sh
echo $1                       # 따옴표 없는 변수 (공백 있으면 깨짐)
rm "~/my file.txt"            # 따옴표 안의 ~는 홈 디렉터리로 바뀌지 않음
echo 'Path is $PATH'          # 작은따옴표 안에서는 변수가 치환되지 않음
[[ $foo==0 ]]                 # 공백이 없어서 항상 참
[ $n && $m ]                  # [ ] 안에서 && 사용
var = 42                      # 대입문에 공백
$foo=42                       # 대입할 때 $ 사용
var=(1, 2, 3)                 # 배열을 쉼표로 구분
sudo echo 'Var=42' > /etc/profile   # 리다이렉션은 sudo 권한으로 실행되지 않음
```

## 사용 방법

- **웹:** [shellcheck.net](https://www.shellcheck.net)에 스크립트를 붙여넣으면 바로 결과가 나옵니다.
- **터미널:** `shellcheck yourscript.sh`
- **에디터:** VS Code([vscode-shellcheck](https://github.com/timonwong/vscode-shellcheck)), Vim, Emacs, Sublime 등에서 실시간으로 경고를 볼 수 있습니다.
- **CI·빌드:** 경고가 있으면 0이 아닌 종료 코드를 돌려주므로, 빌드 단계에 한 줄만 추가하면 됩니다.

```makefile
check-scripts:
    shellcheck myscripts/*.sh
```

## 설치

```bash
brew install shellcheck        # macOS
sudo apt install shellcheck    # Debian / Ubuntu
pacman -S shellcheck           # Arch Linux
```

특정 경고를 무시하고 싶다면 파일 안에 주석으로 지정하거나 명령줄 옵션을 쓸 수 있습니다. 자세한 방법은 [위키](https://github.com/koalaman/shellcheck/wiki/Ignore)를 참고하세요.

## 이런 분께 추천

- 배포·운영 스크립트를 셸로 작성하는 모든 분
- 셸 문법이 헷갈려서 "왜 안 되지?"를 자주 겪는 분
- 팀 저장소의 스크립트 품질을 CI로 관리하고 싶은 분

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
