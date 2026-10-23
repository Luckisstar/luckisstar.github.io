---
layout: default
title: "[오픈소스 소개] ShellCheck: 셸 스크립트의 실수를 미리 잡아주는 정적 분석 도구"
description: "bash·sh 스크립트의 흔한 실수를 실행 전에 잡아 주는 정적 분석 도구 ShellCheck의 주요 경고(SC 코드), 에디터·CI 연동, 실무 팁을 정리했습니다."
date: 2026-10-20
categories: [opensource]
---

# [오픈소스 소개] ShellCheck: 셸 스크립트의 실수를 미리 잡아주는 정적 분석 도구

- **저장소:** [koalaman/shellcheck](https://github.com/koalaman/shellcheck) · [shellcheck.net](https://www.shellcheck.net)
- **라이선스:** GPL v3
- **언어:** Haskell
- **현황 (2026-10-20 기준):** GitHub 스타 약 4만 개, 최신 릴리스 v0.11.0 (2025년 8월)

## 한 줄 요약

**bash/sh 스크립트를 실행하기 전에 읽어서, 따옴표 누락·잘못된 조건문·실패를 삼키는 코드 같은 흔한 실수를 SC 코드와 함께 알려주는 린터(정적 분석 도구)**입니다.

## 어떤 문제를 푸나

셸은 관대한 언어입니다. 문법이 조금 틀려도 일단 실행되고, 문제는 대개 이상한 동작이나 알아보기 힘든 에러 메시지로 나타납니다.

- `rm -rf $dir/*` 같은 코드는 `$dir`가 비어 있거나 공백을 포함할 때 전혀 다른 경로를 지울 수 있습니다.
- `cd build` 가 실패해도 스크립트는 멈추지 않고, 다음 명령을 엉뚱한 디렉터리에서 실행합니다.
- `local out=$(cmd)` 는 `cmd` 가 실패해도 항상 성공으로 끝나서 `set -e` 가 동작하지 않습니다.

이런 문제는 테스트 환경에서는 멀쩡하다가, 파일 이름에 공백이 들어오거나 디렉터리가 없을 때 같은 특정 조건에서만 터집니다. ShellCheck는 스크립트를 실행하지 않고 코드만 읽어서 이런 위험 지점을 미리 짚어 줍니다.

README가 밝히는 목표는 세 가지입니다.

1. 초보자가 겪는, 셸이 알아보기 힘든 에러만 내는 **문법 실수**를 설명합니다.
2. 중급자가 겪는, 셸이 직관과 다르게 동작하는 **의미상의 문제**를 짚어 줍니다.
3. 숙련자의 잘 돌아가던 스크립트도 나중에 깨뜨릴 수 있는 **미묘한 함정과 경계 조건**을 알려줍니다.

## 핵심 개념 / 동작 원리

### 파싱 후 규칙 검사

ShellCheck는 스크립트를 실제로 실행하지 않습니다. 먼저 셸 문법으로 파싱해 구문 트리를 만들고, 그 트리 위에서 수백 개의 규칙을 검사합니다. 기본으로 켜져 있는 데이터 흐름 분석(extended analysis)은 변수에 어떤 값이 들어갈 수 있는지까지 추적해 더 많은 문제를 찾습니다.

```
script.sh
   │  파싱 (문법 오류는 SC1xxx)
   ▼
구문 트리 + 데이터 흐름 분석
   │  규칙 검사 (SC2xxx, SC3xxx)
   ▼
지시자/.shellcheckrc/옵션으로 필터링
   │
   ▼
출력 (tty, gcc, json1, checkstyle, diff, quiet)
```

### 방언(dialect)에 따라 다른 조언

같은 코드라도 어떤 셸로 실행하느냐에 따라 경고가 달라집니다. 매뉴얼의 예시가 이를 잘 보여줍니다.

```sh
(( area = 3.14*r*r ))
```

- `#!/bin/sh` (또는 `-s sh`): `(( .. ))` 는 POSIX 표준이 아니라고 경고합니다.
- `#!/bin/bash` (또는 `-s bash`): bash는 소수 연산을 지원하지 않는다고 경고합니다.
- `#!/bin/ksh` (또는 `-s ksh`): ksh는 소수 연산을 지원하므로 경고하지 않습니다.

셸 종류는 `shell` 지시자, shebang(첫 줄의 `#!`), 파일 확장자(`.bash/.bats/.dash/.ksh`) 순서로 판단합니다. `-s` 옵션에 쓸 수 있는 값은 `sh`, `bash`, `dash`, `ksh`, `busybox` 입니다. 여기서 `sh` 는 시스템의 sh가 아니라 POSIX sh를 뜻하며, 이식성 문제를 경고합니다.

### SC 코드 체계

모든 경고에는 `SC` 로 시작하는 네 자리 코드가 붙고, 코드마다 위키 페이지(`https://www.shellcheck.net/wiki/SC2086` 형태)가 있어 문제 코드, 수정 코드, 이유, 예외 상황을 설명합니다. 소스 코드 기준으로 대략 이렇게 나뉩니다.

| 범위 | 의미 | 예 |
|---|---|---|
| SC1xxx | 파서가 내는 문법 관련 문제 | SC1091 (source 파일을 따라가지 못함) |
| SC2xxx | 주요 분석 규칙 (따옴표, 조건문, 명령 오용 등) | SC2086, SC2155 |
| SC3xxx | 선택한 셸에서 지원되지 않는 기능 (이식성) | `sh` 에서 bash 전용 문법 사용 |

### 심각도(severity) 4단계

각 경고는 `error`, `warning`, `info`, `style` 중 하나의 심각도를 가집니다. `-S`(`--severity`)로 최소 심각도를 정하면 그보다 낮은 경고는 보고하지 않습니다. 기본값은 `style` 로, 모든 경고가 다 나옵니다.

자주 보는 코드의 심각도는 v0.11.0 소스 기준으로 다음과 같습니다.

| 코드 | 내용 | 심각도 |
|---|---|---|
| SC2068 | `$@` 배열 확장에 따옴표 없음 | error |
| SC2046 | `$(...)` 명령 치환에 따옴표 없음 | warning |
| SC2155 | 선언과 대입을 한 줄에 해서 종료 코드가 가려짐 | warning |
| SC2164 | `cd` 실패 처리 없음 | warning |
| SC2034 | 사용하지 않는 변수 | warning |
| SC2086 | 변수에 따옴표 없음 | info |
| SC2162 | `read` 에 `-r` 없음 | info |
| SC1091 | source 파일을 따라가지 못함 | info |
| SC2181 | `$?` 로 간접 검사 | style |
| SC2006 | 백틱 명령 치환 | style |

눈여겨볼 점은 가장 유명한 경고인 SC2086이 `info` 라는 것입니다. CI에서 `-S warning` 을 걸면 SC2086이 통째로 빠집니다. 이 부분은 실무 팁에서 다시 다룹니다.

### 종료 코드

CI에 넣기 쉬운 이유는 종료 코드가 명확하기 때문입니다.

| 코드 | 의미 |
|---|---|
| 0 | 모든 파일 검사 완료, 문제 없음 |
| 1 | 모든 파일 검사 완료, 문제 있음 |
| 2 | 일부 파일을 처리하지 못함 (파일 없음 등) |
| 3 | 잘못된 문법으로 호출 (알 수 없는 플래그 등) |
| 4 | 잘못된 옵션으로 호출 (알 수 없는 포매터 등) |

## 주요 기능

### 잡아내는 문제의 종류

README의 "Gallery of bad code"는 카테고리별로 예시를 보여줍니다. 일부만 옮기면 이렇습니다.

**따옴표(Quoting)**

```sh
echo $1                           # 따옴표 없는 변수
find . -name *.ogg                # 따옴표 없는 find/grep 패턴
rm "~/my file.txt"                # 따옴표 안의 ~ 는 홈으로 바뀌지 않음
for f in "*.ogg"                  # 잘못 따옴표 친 for 루프
echo 'Path is $PATH'              # 작은따옴표 안에서는 변수 치환 안 됨
trap "echo Took ${SECONDS}s" 0    # trap 문자열이 너무 일찍 확장됨
```

**조건문(Conditionals)**

```sh
[[ $foo==0 ]]                     # 공백이 없어 항상 참
[[ -n "$foo " ]]                  # 리터럴 때문에 항상 참
[[ $foo =~ "fo+" ]]               # =~ 오른쪽 정규식에 따옴표
[ $1 -eq "shellcheck" ]           # 문자열을 숫자 비교
[ $n && $m ]                      # [ ] 안에서 &&
[ grep -q foo file ]              # $(..) 없이 명령 사용
```

이 밖에도 자주 오용되는 명령, 초보자의 흔한 실수(`var = 42`, `$foo=42` 등), 스타일, 데이터·타입 오류, 견고성(robustness), 이식성(portability) 카테고리가 있습니다.

### 사용 방법

- **웹:** [shellcheck.net](https://www.shellcheck.net)에 붙여넣으면 바로 결과가 나옵니다. 항상 최신 git 커밋과 동기화되어 있습니다.
- **터미널:** `shellcheck yourscript`
- **에디터:** Vim(ALE, Neomake, Syntastic), Emacs(Flycheck, Flymake), Sublime(SublimeLinter), VS Code([vscode-shellcheck](https://github.com/timonwong/vscode-shellcheck)), Pulsar 등. 그 외 에디터는 GCC 호환 출력(`-f gcc`)으로 연결할 수 있습니다.
- **빌드·CI:** 종료 코드를 정석대로 쓰므로 `shellcheck` 한 줄을 빌드 단계에 넣으면 됩니다.

### 출력 형식 (`-f`)

| 형식 | 용도 |
|---|---|
| `tty` | 사람이 읽는 기본 출력 (색상, 위키 링크 포함) |
| `gcc` | `파일:줄:열: 종류: 메시지` 형태. 에디터의 빌드 오류 목록과 연동 |
| `checkstyle` | Checkstyle 호환 XML. IDE, 빌드 모니터링 시스템용 |
| `diff` | 자동 수정 가능한 항목을 unified diff로 출력. `git apply` 나 `patch -p1` 로 적용 |
| `json1` | 웹/도구 연동용 JSON. 탭은 1글자로 계산 |
| `json` | `json1` 의 레거시 버전 (탭 폭 8) |
| `quiet` | 출력 없이 종료 코드만. 첫 문제에서 처리 중단 |

Vim에서는 `:set makeprg=shellcheck\ -f\ gcc\ %` 로 설정하면 `:make` 로 검사하고 `:cnext` 로 다음 오류로 이동할 수 있습니다.

### 자주 쓰는 옵션

| 옵션 | 설명 |
|---|---|
| `-S`, `--severity` | 최소 심각도 (`error`, `warning`, `info`, `style`) |
| `-s`, `--shell` | 셸 방언 지정 (`sh`, `bash`, `dash`, `ksh`, `busybox`) |
| `-e`, `--exclude` | 특정 코드 제외 (`-e SC2059,SC2034`) |
| `-i`, `--include` | 지정한 코드만 보고 (exclude보다 우선) |
| `-x`, `--external-sources` | 명령줄에 지정하지 않은 `source` 파일도 따라감 |
| `-P`, `--source-path` | source 파일 검색 경로 (`SCRIPTDIR` 사용 가능) |
| `-a`, `--check-sourced` | source한 파일의 경고도 함께 보고 |
| `-o`, `--enable` | 선택 검사 켜기 (`-o all` 은 전부) |
| `--list-optional` | 사용 가능한 선택 검사 목록 |
| `--extended-analysis=false` | 데이터 흐름 분석 끄기 (아주 큰 스크립트용) |
| `--norc`, `--rcfile` | 설정 파일 무시 / 특정 설정 파일 사용 |
| `-W` | tty 출력의 위키 링크 개수 (0이면 끔) |

환경 변수 `SHELLCHECK_OPTS` 에 기본 플래그를 넣어 두면 매 실행마다 앞에 붙습니다.

```sh
export SHELLCHECK_OPTS='--shell=bash --exclude=SC2016'
```

### 선택 검사(optional checks)

기본으로 꺼져 있는, 주관적이거나 스타일에 가까운 검사들입니다. 예를 들어 `require-variable-braces`(`$VAR` 대신 `${VAR}`), `add-default-case`(`case` 문에 기본 분기 추가), `quote-safe-variables`, `check-unassigned-uppercase`, `check-extra-masked-returns` 등이 있습니다. 정확한 목록은 사용하는 버전에서 `shellcheck --list-optional` 로 확인합니다.

위키는 C의 `-Wall` 처럼 전부 켜는 것을 권하지 않습니다. 선택 검사는 "더 포괄적인" 것이 아니라 "더 주관적인" 것이고, 서로 충돌할 수도 있기 때문입니다.

### 지시자(directive)와 설정 파일

경고를 끄거나 동작을 바꾸는 방법은 범위에 따라 여러 단계가 있습니다.

| 범위 | 방법 |
|---|---|
| 명령 하나 | 바로 위에 `# shellcheck disable=SC2059` |
| 파일 전체 | shebang 바로 다음, 첫 명령 앞에 지시자 |
| 실행 한 번 | `shellcheck -e SC2059 myscript` |
| 프로젝트/사용자 전체 | `.shellcheckrc` 에 `disable=SC2059` |

지원하는 지시자 키는 `disable`, `enable`, `external-sources`, `source`, `source-path`, `shell`, `extended-analysis` 입니다.

## 설치와 시작

README에 나온 설치 명령 중 대표적인 것들입니다.

```bash
brew install shellcheck              # macOS (Homebrew)
sudo apt install shellcheck          # Debian / Ubuntu
dnf install ShellCheck               # Fedora
pacman -S shellcheck                 # Arch Linux
conda install -c conda-forge shellcheck
```

Windows는 `choco install shellcheck`, `winget install --id koalaman.shellcheck`, `scoop install shellcheck` 중 하나를 씁니다. 설치 없이 Docker로 돌릴 수도 있습니다.

```bash
docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable myscript
```

배포판 패키지는 버전이 오래된 경우가 많습니다. 최신 버전이 필요하면 GitHub Releases의 사전 빌드 바이너리를 받습니다. Linux 바이너리는 정적 링크라서 의존성이 없습니다.

```bash
scversion="stable" # 또는 "v0.11.0", "latest"
wget -qO- "https://github.com/koalaman/shellcheck/releases/download/${scversion?}/shellcheck-${scversion?}.linux.x86_64.tar.xz" | tar -xJv
cp "shellcheck-${scversion}/shellcheck" /usr/bin/
shellcheck --version
```

첫 실행은 간단합니다.

```bash
shellcheck deploy.sh                 # 사람이 읽는 출력
shellcheck -f gcc scripts/*.sh       # 한 줄짜리 출력
shellcheck -f diff deploy.sh | git apply   # 자동 수정 적용
```

`-f diff` 는 자동 수정 정보가 있는 경고(예: SC2086의 따옴표 추가)에만 적용됩니다. 적용 전에 diff를 한 번 눈으로 보는 것을 권합니다.

## 실전 예제

### 예제 1. 자주 걸리는 경고 TOP 7

각 항목을 "문제 코드 → 수정 코드 → 이유" 순서로 정리했습니다. 내용은 각 SC 코드의 위키 페이지를 따릅니다.

#### SC2086: 변수에 따옴표를 쳐라

```sh
# 문제
echo $1
for i in $@; do :; done
```

```sh
# 수정
echo "$1"
for i in "$@"; do :; done   # 또는 for i; do
```

**이유:** `echo $1` 은 "첫 번째 인자를 출력"처럼 보이지만 실제로는 "첫 번째 인자를 IFS(공백, 탭, 줄바꿈)로 쪼개고, 각 조각을 glob(와일드카드)으로 확장한 뒤, 결과를 출력"합니다. 공백이나 `*` 가 든 입력에서 깨집니다.

옵션 문자열을 일부러 쪼개고 싶다면 따옴표를 빼는 대신 배열을 씁니다.

```bash
options=(-j 5 -B)
[[ $debug == "yes" ]] && options=("${options[@]}" -d)
make "${options[@]}" file
```

있을 수도 없을 수도 있는 인자에는 `${var:+...}` 패턴이 깔끔합니다.

```bash
bash ${debug:+"-x"} script
```

`$( )` 안은 새 문맥이라 그 안의 변수는 따로 따옴표를 쳐야 한다는 점도 위키가 짚습니다.

#### SC2046: 명령 치환에도 따옴표를

```sh
# 문제
ls -l $(getfilename)
```

```sh
# 수정: 결과가 파일 하나일 때
ls -l "$(getfilename)"

# 수정: 줄 단위로 여러 개일 때
getfilename | while IFS='' read -r line
do
    ls -l "$line"
done
```

**이유:** 따옴표 없는 `$(...)` 도 단어 분리와 glob 확장을 거칩니다. 데이터에 따옴표나 이스케이프를 넣어서 고치려 하면 안 되고, 치환 자체를 따옴표로 감싸야 합니다. `gcc $(pkg-config --libs openssl)` 처럼 일부러 쪼개야 하는 경우는 `read -ra args < <(...)` 로 배열에 담거나 지시자로 끕니다.

#### SC2155: 선언과 대입을 분리하라

```bash
# 문제
local foo="$(mycmd)"
export bar="$(othercmd)"
```

```bash
# 수정
local foo
foo=$(mycmd)

bar="$(othercmd)"
export bar
```

**이유:** `local`/`export`/`readonly` 자체의 종료 코드가 `mycmd` 의 종료 코드를 덮어씁니다. 그래서 `mycmd` 가 실패해도 항상 성공으로 보이고, 조건문·`set -e`·trap이 제대로 동작하지 않습니다. 위키의 예시가 명확합니다.

```bash
$ f() { local foo=$(false) && echo "error was hidden"; }; f
error was hidden
$ f() { local foo; foo=$(false) && echo "error was hidden"; }; f
```

`export foo=bar` 처럼 오른쪽이 리터럴이면 경고하지 않습니다.

#### SC2164: `cd` 실패를 처리하라

```sh
# 문제
cd generated_files
rm -r *.c
```

```sh
# 수정
cd generated_files || exit
rm -r *.c

# 함수 안에서는 return
func(){
  cd foo || return
  do_something
}
```

**이유:** 경로 오타, 디렉터리 없음, 권한, 깨진 심볼릭 링크 등으로 `cd` 는 실패할 수 있고, 그러면 이후 명령이 엉뚱한 디렉터리에서 실행됩니다. 삭제 명령이 이어지면 치명적입니다. 메시지를 남기고 싶으면 `cd foo || { echo "Failure"; exit 1; }` 처럼 씁니다.

참고로 스크립트 어딘가에 `set -e` 가 있으면 이 경고는 나오지 않습니다. 위키는 이것이 문제를 반드시 막아주는 것은 아니라고 덧붙입니다.

#### SC2181: `$?` 대신 명령을 직접 검사하라

```sh
# 문제
make mytarget
if [ $? -ne 0 ]
then
  echo "Build failed"
fi
```

```sh
# 수정
if ! make mytarget
then
  echo "Build failed"
fi
```

**이유:** 명령과 상태 검사가 떨어져 있으면, 나중에 누가 그 사이에 `echo "make finished"` 한 줄만 넣어도 `echo` 의 상태를 비교하게 됩니다. 또 `set -e` 스크립트에서는 실패 처리 코드에 도달하기 전에 종료됩니다. 출력도 받고 싶다면 `if ! output=$(mycommand); then` 형태를 씁니다.

#### SC2162: `read` 에는 `-r` 을

```sh
# 문제
read name
```

```sh
# 수정
IFS= read -r name
```

**이유:** `-r` 없이 `read` 하면 백슬래시를 이스케이프 문자로 해석해 입력이 변형됩니다. `IFS=` 까지 붙이면 앞뒤 공백이 잘리는 것도 막을 수 있어 가장 안전합니다.

#### SC1091: source한 파일을 따라가지 못함

```sh
# 문제 (경고 발생)
source lib/common.sh
```

```sh
# 수정 1: 파일 위치를 알려준다
# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"

# 수정 2: 접근할 수 없는 파일이면 무시
# shellcheck source=/dev/null
source /etc/some-runtime-config
```

**이유:** ShellCheck는 기본적으로 명령줄에 지정한 파일만 엽니다. 원래 신뢰할 수 없는 스크립트를 검사하는 원격 서비스로 시작했기 때문입니다. 실제 개발 환경에서는 `-x` 나 `.shellcheckrc` 의 `external-sources=true` 로 켜도 안전하다고 매뉴얼이 설명합니다. 경로가 `"$dir/file"` 처럼 동적이면 SC1090이 대신 나옵니다.

### 예제 2. 지시자로 경고 끄기

```sh
#!/bin/bash
# 파일 전체에 적용: shebang 바로 다음, 첫 명령 앞
# shellcheck disable=SC2034

hexToAscii() {
  # 이 명령 하나에만 적용
  # shellcheck disable=SC2059
  printf "\x$1"
}

# 여러 코드를 한 번에, 이유는 끝에 주석으로
# shellcheck disable=SC2116,SC2086 # 공백 정리용으로 의도한 코드
hash=$(echo ${hash})

# 여러 줄에 적용하려면 중괄호 그룹으로 묶는다
# shellcheck disable=SC2016
{
  echo 'Modifying $PATH'
  echo 'PATH=foo:$PATH' >> ~/.bashrc
}
```

알아두면 좋은 규칙입니다.

- 지시자는 **완전한 명령** 앞에만 쓸 수 있습니다. `else` 앞이나 `case` 의 개별 분기(`-v)`) 앞은 안 됩니다.
- `command1; command2; command3` 처럼 한 줄에 이어 쓴 경우 지시자는 첫 명령에만 적용됩니다.
- 함수 정의, 루프, `case` 문 같은 복합 명령 앞에 쓰면 그 블록 전체에 적용됩니다.
- 범위 지정(`disable=SC3000-SC4000`)과 전체 끄기(`disable=all`, 0.8 이상)도 됩니다.
- 위키는 지시자를 쓸 때 **이유를 주석으로 남기라고** 권합니다. 짧으면 같은 줄 끝에, 길면 위 줄에 씁니다.

### 예제 3. `.shellcheckrc` 로 프로젝트 규칙 정하기

저장소 루트에 `.shellcheckrc` 를 두면 하위의 모든 스크립트에 파일 전체 지시자처럼 적용됩니다. ShellCheck는 스크립트 디렉터리부터 부모 디렉터리를 거슬러 올라가며 `.shellcheckrc` 또는 `shellcheckrc` 를 찾고, 없으면 `~/.shellcheckrc`, 그다음 `$XDG_CONFIG_HOME/shellcheckrc` 를 봅니다. 처음 찾은 파일 하나만 씁니다.

```sh
# .shellcheckrc

# source 경로를 검사 대상 스크립트 기준으로 찾는다
source-path=SCRIPTDIR
source-path=SCRIPTDIR/lib

# source한 파일을 열어도 된다 (-x 와 같은 효과)
external-sources=true

# 선택 검사 켜기
enable=require-variable-braces
enable=check-unassigned-uppercase

# [ ! -z foo ] 를 허용 (-n 사용 권고 끄기)
disable=SC2236
```

주의할 점이 두 가지 있습니다.

- Snap으로 설치한 경우 샌드박스가 숨김 파일을 막으므로 점 없는 `shellcheckrc` 를 씁니다.
- Docker로 돌릴 때는 컨테이너에 마운트된 파일만 보이므로 `~/.shellcheckrc` 는 읽히지 않습니다.

### 예제 4. pre-commit과 GitHub Actions 연동

**pre-commit** 은 README에 공식 훅이 나와 있습니다. `.pre-commit-config.yaml` 에 추가합니다.

```yaml
repos:
-   repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
    -   id: shellcheck
#       args: ["--severity=warning"]  # 필요하면 error/warning만
```

**GitHub Actions** 의 Ubuntu 러너에는 ShellCheck가 미리 설치되어 있어서 바로 실행할 수 있습니다. 위키의 기본 예시를 조금 다듬었습니다.

```yaml
name: ShellCheck
on: [push, pull_request]

jobs:
  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run ShellCheck
        run: |
          shellcheck --version
          find . -type f -name "*.sh" -exec shellcheck -f gcc {} +
```

기존 경고가 많은 저장소라면 PR에서 **새로 생긴 경고만** 보고하는 Red Hat의 differential-shellcheck 액션도 위키에 소개되어 있습니다. SARIF 형식으로 PR에 바로 표시됩니다.

{% raw %}
```yaml
name: Differential ShellCheck
on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: redhat-plumbers-in-action/differential-shellcheck@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```
{% endraw %}

Makefile에 넣는 방법도 간단합니다. 경고가 있으면 종료 코드 1로 빌드가 실패합니다.

```makefile
check-scripts:
	shellcheck myscripts/*.sh
```

## 실무 팁 & 자주 겪는 문제

- **CI에서는 버전을 고정합니다.** README도 권하는 부분입니다. 러너에 깔린 버전이나 `latest` 를 쓰면, 새 버전이 새 경고를 추가했을 때 코드 변경 없이 빌드가 깨질 수 있습니다. pre-commit은 `rev` 로, 바이너리는 릴리스 태그로 고정합니다.
- **`-S warning` 의 함정.** SC2086(따옴표 누락)은 `info` 입니다. 심각도를 `warning` 으로 올리면 가장 중요한 경고 중 하나가 사라집니다. 노이즈를 줄이고 싶다면 심각도를 올리기보다 특정 코드를 `disable` 하는 편이 안전합니다.
- **도입 초기에는 단계적으로.** 오래된 저장소에 처음 적용하면 경고가 수백 개 나옵니다. `-S error` 로 시작해 점차 낮추거나, 새로 바뀐 파일만 검사하거나, differential-shellcheck처럼 새 경고만 막는 방식이 현실적입니다.
- **shebang 없는 라이브러리 파일.** source용 파일은 shebang이 없어서 셸 종류를 알 수 없습니다. 파일 맨 위에 `# shellcheck shell=bash` 를 넣거나 `-s bash` 로 지정합니다.
- **SC2034가 오탐처럼 보일 때.** `${!name}` 같은 간접 참조로만 쓰는 변수는 의도적으로 경고합니다. 버리는 값은 `_` 자체나 `_` 로 시작하는 이름(0.7.2보다 새 버전)을 쓰면 경고가 나오지 않습니다.
- **`set -e` 는 만능이 아닙니다.** SC2155, SC2181 위키가 보여주듯 `local x=$(cmd)` 처럼 종료 코드가 가려지면 `set -e` 도 소용없습니다. ShellCheck 경고를 고치는 것이 `set -e` 를 제대로 동작하게 만드는 길이기도 합니다.
- **아주 큰 스크립트에서 느릴 때.** 수천 줄짜리 자동 생성 스크립트라면 `# shellcheck extended-analysis=false` 나 `--extended-analysis=false` 로 데이터 흐름 분석을 꺼서 CPU·메모리 사용을 줄일 수 있습니다. 대신 일부 검사는 빠집니다.
- **지원하지 않는 함수 정의.** 매뉴얼의 호환성 섹션에 따르면 함수 본문은 `{ ...; }` 또는 `( ... )` 여야 하고, 이름에 `[]*=!` 가 들어가면 `function` 키워드 뒤에서만 인식합니다. 흔하지는 않지만 특이한 스크립트에서 엉뚱한 경고가 나오면 확인해 봅니다.
- **한국어 출력은 없습니다.** 메시지는 영어로만 나오지만, SC 코드로 위키를 찾으면 예시 코드가 함께 있어 이해하기 어렵지 않습니다.

> master 브랜치 매뉴얼에는 `.editorconfig` 의 `shellcheck.*` 키 지원과 `--files-from` 옵션이 추가되어 있습니다. v0.11.0 매뉴얼에는 없는 내용이라 다음 릴리스부터 쓸 수 있을 것으로 보입니다.

## 비슷한 도구와 비교

ShellCheck와 같은 일을 하는 도구는 사실상 드물고, 대부분 **역할이 달라서 함께 쓰는** 관계입니다.

| 도구 | 하는 일 | ShellCheck와의 관계 |
|---|---|---|
| **ShellCheck** | 정적 분석: 버그 가능성, 이식성, 스타일 경고 | 기준 |
| **shfmt** ([mvdan/sh](https://github.com/mvdan/sh)) | 포매터: 들여쓰기·줄바꿈 등 코드 모양 정리. Go로 작성, POSIX sh·bash·zsh·mksh 지원 | 보완 관계. 모양은 shfmt, 의미는 ShellCheck. `shfmt -d` 로 CI에서 포맷 검사, 백틱을 `$(...)` 로 바꾸는 것도 자동 처리 |
| **bash -n** | bash가 명령을 실행하지 않고 읽기만 하는 문법 검사 | 문법이 맞는지만 확인. 따옴표 누락, `cd` 실패 처리 같은 의미상 문제는 못 잡음 |
| **checkbashisms** | `/bin/sh` 스크립트에 섞인 bash 전용 문법 검출 | ShellCheck도 `sh` 모드에서 SC3xxx로 비슷한 이식성 경고를 냄 (매뉴얼이 직접 비교) |

추천 조합은 `shfmt` 로 포맷을 맞추고 `shellcheck` 로 분석하는 것입니다. 둘 다 pre-commit과 CI에 넣기 쉽습니다.

## 장점과 한계

**장점**

- 설치가 쉽고, 거의 모든 패키지 매니저와 Docker, 웹으로 쓸 수 있습니다.
- 경고마다 SC 코드와 위키 페이지가 있어 "왜 문제인지"와 "어떻게 고치는지"를 바로 배울 수 있습니다.
- 셸 방언에 맞춘 조언을 해서 sh 이식성 문제까지 잡습니다.
- 종료 코드와 출력 형식이 잘 정리되어 있어 에디터, CI, pre-commit 연동이 간단합니다.
- 일부 경고는 `-f diff` 로 자동 수정까지 됩니다.

**한계**

- 정적 분석이라 런타임에 결정되는 값(동적 source 경로, 간접 참조 변수)은 추적하지 못합니다. 지시자로 알려줘야 합니다.
- zsh, fish는 지원하지 않습니다. `-s` 로 고를 수 있는 것은 sh, bash, dash, ksh, busybox뿐입니다.
- 일부 경고는 맥락상 불필요할 수 있어, 팀마다 `.shellcheckrc` 를 다듬는 과정이 필요합니다.
- 소스에서 빌드하려면 Haskell 툴체인과 2GB 메모리가 필요합니다. 다만 대부분은 사전 빌드 바이너리를 쓰면 되므로 큰 문제는 아닙니다.
- 메시지는 영어로만 제공됩니다.

## 이런 분께 추천 / 이런 경우엔 다른 도구

**추천**

- 배포, 빌드, 운영 자동화를 셸 스크립트로 작성하는 모든 분
- "왜 공백 있는 파일명에서만 깨지지?" 같은 문제를 자주 겪는 분
- 팀 저장소의 스크립트 품질을 pre-commit과 CI로 관리하고 싶은 분
- `/bin/sh` 로 돌아가야 하는 이식성 있는 스크립트를 만드는 분

**다른 도구가 나은 경우**

- 코드 모양(들여쓰기, 줄바꿈)만 통일하고 싶다면 shfmt를 함께 쓰거나 우선 씁니다.
- zsh나 fish 스크립트라면 ShellCheck 대상이 아닙니다.
- 스크립트가 수백 줄을 넘어 복잡한 로직과 자료구조를 다룬다면, 린터보다 Python 같은 언어로 옮기는 것을 고민해 볼 때입니다.

## 참고 링크

- [ShellCheck GitHub 저장소 / README](https://github.com/koalaman/shellcheck)
- [ShellCheck 매뉴얼 (shellcheck.1.md)](https://github.com/koalaman/shellcheck/blob/master/shellcheck.1.md)
- [위키: Ignore (경고 무시 방법)](https://github.com/koalaman/shellcheck/wiki/Ignore)
- [위키: Directive (지시자와 .shellcheckrc)](https://github.com/koalaman/shellcheck/wiki/Directive)
- [위키: Optional (선택 검사)](https://github.com/koalaman/shellcheck/wiki/Optional)
- [위키: GitHub Actions](https://github.com/koalaman/shellcheck/wiki/GitHub-Actions)
- [위키: SC2086](https://www.shellcheck.net/wiki/SC2086) · [SC2046](https://www.shellcheck.net/wiki/SC2046) · [SC2155](https://www.shellcheck.net/wiki/SC2155) · [SC2164](https://www.shellcheck.net/wiki/SC2164) · [SC2181](https://www.shellcheck.net/wiki/SC2181) · [SC2162](https://www.shellcheck.net/wiki/SC2162) · [SC1091](https://www.shellcheck.net/wiki/SC1091) · [SC2034](https://www.shellcheck.net/wiki/SC2034)
- [shellcheck-precommit](https://github.com/koalaman/shellcheck-precommit)
- [shfmt (mvdan/sh)](https://github.com/mvdan/sh)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
