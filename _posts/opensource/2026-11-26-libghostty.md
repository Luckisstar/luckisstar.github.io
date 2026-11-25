---
layout: default
title: "[오픈소스 소개] libghostty 1.0: Ghostty의 터미널 에뮬레이션 엔진을 안정된 C ABI 라이브러리로"
description: "Ghostty에서 떼어 낸 터미널 에뮬레이션 라이브러리 libghostty-vt 1.0의 구조(터미널 상태, 포매터, 렌더 상태, 이펙트 콜백), ABI 안정성 약속과 CI 검증 방식, 플랫폼 범위, C 예제 5개, JediTerm·xterm.js와의 차이를 정리했습니다."
date: 2026-11-26 07:00:00 +0900
categories: [opensource]
---

# [오픈소스 소개] libghostty 1.0: Ghostty의 터미널 에뮬레이션 엔진을 안정된 C ABI 라이브러리로

- **저장소:** [ghostty-org/ghostty](https://github.com/ghostty-org/ghostty) (Ghostty 앱과 같은 저장소) · [공식 문서](https://lib.ghostty.org/vt/) · [1.0 발표 글](https://mitchellh.com/writing/libghostty-1-0)
- **라이선스:** MIT. 1.0 발표 글 기준 의존성 트리에 카피레프트 코드가 없고, 모든 의존성을 버전·SPDX 라이선스·해시와 함께 기계가 읽을 수 있는 목록으로 제공합니다.
- **언어:** Zig로 작성, C ABI와 Zig API 제공. 빌드에는 Zig 0.17이 필요합니다.
- **현황 (2026-11-26 기준):** GitHub 스타 약 6.45만 개(Ghostty 앱과 라이브러리가 한 저장소라 앱 인기까지 합친 수치), 최신 릴리스 libghostty-vt 1.0.2 (2026년 11월 24일). 1.0.0은 2026년 11월 6일에 나왔고 이후 1.0.1(11월 11일), 1.0.2까지 버그 수정과 성능 개선 릴리스가 이어졌습니다.
- **도입 전 확인할 점:** **1.0이 된 것은 "libghostty" 전체가 아니라 첫 구성 요소인 `libghostty-vt`(터미널 시퀀스 파싱과 상태 관리)뿐입니다.** 화면 그리기(렌더링), 폰트, 창, PTY(가상 터미널 장치)는 여전히 쓰는 쪽이 직접 만들어야 합니다. Linux·FreeBSD용 미리 빌드한 패키지는 공식으로 제공하지 않으므로 소스에서 빌드하거나 배포판 패키지를 기다려야 하며, 이때 정확한 Zig 버전(1.0.x는 0.17.x)이 필요합니다. 스냅숏(터미널 상태 저장) 바이트 형식은 ABI 약속에 포함되지 않습니다.

## 한 줄 요약

**libghostty-vt는 "터미널 앱"이 아니라, 프로그램이 내보낸 바이트를 받아 화면·커서·스크롤백 상태로 바꿔 주는 "터미널 기능을 앱에 넣는 C 라이브러리"이고, 1.0부터 C ABI를 semver로 지킵니다.** IDE, 웹 콘솔, CI 로그 뷰어, 터미널 멀티플렉서, TUI 테스트 도구, 그리고 터미널을 내장하는 코딩 에이전트 도구를 만드는 개발자를 위한 라이브러리입니다.

## 어떤 문제를 푸나

Mitchell Hashimoto는 2025년 9월 글 [Libghostty Is Coming](https://mitchellh.com/writing/libghostty-is-coming)에서 문제를 이렇게 정리했습니다. 터미널 에뮬레이션은 Ghostty, iTerm2 같은 터미널 앱만 하는 일이 아닙니다. tmux 같은 멀티플렉서도 완전한 터미널 에뮬레이터이고, JetBrains IDE는 JediTerm, VS Code는 Xterm.js를 내장하며, GitHub Actions나 빌드 로그를 보여 주는 웹 서비스도 색상과 줄 지우기 정도를 흉내 내는 자체 구현을 갖고 있습니다. 대부분은 공유 라이브러리 없이 각자 만든 일회성 구현이라 불완전하고 느리다는 것이 그의 진단입니다.

구체적인 예로 그는 당시 JediTerm이 시퀀스의 중간 바이트(intermediate)를 잘못 처리해 "커서 모양 바꾸기" 시퀀스가 JetBrains 편집기에서 글자 하나를 삼키던 버그를 들었습니다. 1년 뒤 JetBrains는 [공식 블로그](https://blog.jetbrains.com/platform/2026/10/jetbrains-terminal-now-uses-ghostty/)에서 2026.3 버전부터 IDE 내장 터미널이 JediTerm 대신 libghostty로 동작한다고 밝혔습니다. JetBrains 글에 따르면 바뀐 뒤 달라진 점은 다음과 같습니다.

- Kitty 키보드 프로토콜 지원으로 Enter, Shift+Enter, Ctrl+Enter를 구분합니다. 글은 Claude Code, Codex 같은 CLI 에이전트와 fish, Neovim이 이 프로토콜을 쓴다고 설명합니다. 그래서 Shift+Enter가 반쯤 쓴 프롬프트를 보내 버리는 대신 줄바꿈이 됩니다.
- 다크/라이트 질의(`CSI ? 996 n`)에 IDE 테마로 답하고, 테마가 바뀌면 mode 2031로 알립니다.
- JediTerm이 무시하거나 잘못 읽던 제어 시퀀스 약 50개를 처리합니다. 예: ncurses가 같은 글자 7개 이상에 쓰는 REP, 콜론으로 구분한 SGR 색(`38:2::r:g:b`).
- 렌더링과 상위 기능은 여전히 IDE가 맡고, 파싱과 터미널 상태만 libghostty가 맡습니다.

이 사례가 libghostty-vt의 위치를 잘 보여 줍니다. **어려운 부분(시퀀스 해석과 상태 관리)은 한 곳에서 제대로 만들고, 그리기와 통합은 각 앱이 맡는 분업**입니다.

## 핵심 개념

| 개념 | 설명 |
|---|---|
| `GhosttyTerminal` | 터미널 하나의 상태(화면 격자, 커서, 스타일, 모드, 스크롤백). 불투명 핸들(opaque handle)로만 다룹니다 |
| VT write | `ghostty_terminal_vt_write()`로 프로그램이 쓴 원시 바이트를 넣습니다. 실패하지 않으며, 시퀀스나 UTF-8 문자가 두 번의 호출에 걸쳐 잘려도 이어서 해석합니다 |
| 포매터(formatter) | 현재 화면을 일반 텍스트 등으로 꺼내는 객체. 읽기 전용 도구와 에이전트가 TUI 화면을 읽을 때 씁니다 |
| 렌더 상태(render state) | 한 프레임을 그리기 위한 스냅숏. 바뀐(dirty) 행만 골라 셀 단위로 문자와 스타일을 읽습니다 |
| 이펙트(effect) | 벨, 창 제목 변경, 클립보드, 질의 응답처럼 터미널이 혼자 할 수 없는 일을 앱에 알리는 콜백. 공식 문서(main 브랜치, 2026-11-26 기준)에는 19종이 정리돼 있습니다 |
| 인코더(encoder) | 키·마우스·포커스·붙여넣기 이벤트를 프로그램이 이해하는 이스케이프 시퀀스로 바꿉니다. 터미널 객체 없이도 따로 쓸 수 있습니다 |

## 동작 원리

공식 문서의 설명을 그림으로 옮기면 다음과 같습니다.

```
 PTY / 녹화 파일 / 네트워크          (앱이 소유)
          │  원시 바이트
          ▼
 ghostty_terminal_vt_write()  ── 이펙트 콜백 ──▶ 앱: 벨, 제목, 클립보드,
          │                                        PTY로 질의 응답 쓰기
          ▼
 GhosttyTerminal (화면·커서·스크롤백 상태)
     │                         │
     ▼                         ▼
 포매터 → 텍스트           렌더 상태 → 앱의 렌더러(GPU, 웹, IDE UI)

 키보드·마우스 입력 → 인코더 → 이스케이프 시퀀스 → PTY
```

문서가 강조하는 설계 원칙은 세 가지입니다.

1. **부작용은 기본으로 꺼져 있습니다.** 이펙트 가이드는 "libghostty-vt에는 창도, 클립보드도, PTY도 없다"고 설명합니다. 콜백을 등록하지 않으면 상태를 직접 바꾸는 시퀀스만 처리하고, 질의도 무시합니다. 그래서 첫 터미널 가이드는 신뢰할 수 없는 데이터를 넣어도 기본 설정에서는 메모리 사용이 제한되고 부작용이 없다고 말합니다. 반대로 클립보드 읽기 같은 이펙트를 켜면 그만큼 위험 범위가 넓어진다고 경고합니다.
2. **스레드를 만들지 않습니다.** 한 핸들에 대한 호출은 스레드 안전하지 않고, 서로 다른 핸들 사이의 호출은 안전합니다. 콜백은 그 콜백을 일으킨 호출의 스레드에서 동기적으로 돌며, 콜백 안에서 같은 터미널에 다시 쓰면 안 됩니다.
3. **메모리는 바꿀 수 있는 할당자를 거칩니다.** 할당자를 받는 모든 함수에 `NULL`을 주면 기본 할당자(libc가 있으면 `malloc`/`free`)를 씁니다. 할당 실패는 크래시가 아니라 `GHOSTTY_OUT_OF_MEMORY` 같은 오류 값으로 돌아옵니다.

### ABI 안정성을 지키는 방법

1.0의 핵심은 기능 추가가 아니라 약속입니다. 발표 글과 [Stability 문서](https://lib.ghostty.org/vt/)가 설명하는 장치는 다음과 같습니다.

- 모든 객체는 불투명 핸들이고, 수백 개의 값은 소수의 열거형(enum) 키 기반 getter/setter로 읽고 씁니다. 그래서 새 값을 추가해도 새 심볼이 필요 없습니다.
- 새 헤더로 컴파일한 프로그램이 옛 라이브러리에 링크되면 크래시 대신 `GHOSTTY_UNSUPPORTED`를 받습니다.
- 몇 안 되는 공개 구조체는 자기 크기를 담고 있거나 예약 공간을 둬서 뒤에 필드를 붙일 수 있습니다. enum은 컴파일러마다 `int` 크기로 고정합니다.
- 마이너 릴리스는 새 함수, 새 타입, 새 enum 값, 크기 있는 구조체 끝의 새 필드만 추가할 수 있습니다. 동작을 바꾸려면 새 이름의 함수를 만들고 옛 함수는 다음 메이저 버전까지 `GHOSTTY_DEPRECATED`로 표시합니다.
- CI가 모든 변경을 Linux에서는 [libabigail](https://sourceware.org/libabigail/)로 커밋된 기준선과, macOS와 WebAssembly에서는 타입 목록(golden type manifest)과 비교합니다. ELF 플랫폼에서는 내보내는 모든 심볼에 버전을 붙여, 맞지 않는 라이브러리는 로더가 처음부터 거부합니다.

## 주요 기능

### 넓은 플랫폼 범위

발표 글 기준 CI에서 빌드하고 전체 단위 테스트와 예제까지 실행하는 플랫폼은 다음과 같습니다.

| 플랫폼 | 아키텍처 |
|---|---|
| Linux (glibc, musl) | x86_64, aarch64 |
| macOS 13+ | x86_64, aarch64 |
| iOS 13+ | aarch64 |
| FreeBSD | x86_64, aarch64 |
| Windows | x86_64 |
| Android | aarch64, x86_64, arm |
| WebAssembly | wasm32 (freestanding) |

여기에 빌드만 하고 테스트는 돌리지 않는 대상으로 베어메탈 riscv32·thumb, WASI, Windows arm64, illumos, 32비트 x86이 있습니다. SIMD를 끄면 libc 없이(freestanding) 빌드되며, 이것이 베어메탈 RISC-V·ARM에서 도는 방식이라고 발표 글 각주가 설명합니다.

### 플랫폼별 배포물

Linux·FreeBSD는 SONAME과 버전 심볼을 가진 공유 라이브러리, 정적 라이브러리, 헤더, pkg-config, CMake 설정을 받습니다. macOS·iOS는 Xcode와 Swift Package Manager에 바로 넣을 수 있는 XCFramework, Windows는 DLL과 import 라이브러리, Android는 Android 15 이상이 요구하는 16KB 페이지 크기를 지원하는 공유 라이브러리를 받습니다. WebAssembly는 속도용과 크기용 두 가지이며, 1.0.0 릴리스 파일을 직접 받아 확인해 보니 크기용 `ghostty-vt-1.0.0-small.wasm`은 844,279바이트, 속도용은 1,240,850바이트였습니다(SHA256SUMS로 무결성 확인).

### 기능 플래그로 줄이기

읽기 전용 뷰어만 필요하면 입력 인코딩, 검색, 선택, Kitty 그래픽 같은 하위 시스템을 빌드 플래그로 뺄 수 있고, 발표 글은 이렇게 하면 WebAssembly 모듈이 대략 절반이 된다고 설명합니다. 빠진 기능의 함수도 그대로 내보내고 `GHOSTTY_UNSUPPORTED`만 돌려주므로 호출 코드를 고칠 필요가 없습니다.

### 그 밖의 API

`example/` 디렉터리와 문서 기준으로 검색(찾기 막대처럼 일치 항목 이동), 선택(단어·줄·명령 출력 단위, OSC 133 프롬프트 표시 활용), Kitty 그래픽 프로토콜, 스크롤백 압축, 상태 스냅숏 저장과 복원, 셀 참조 추적, 붙여넣기 안전성 검사(bracketed paste) API가 있습니다.

## 설치와 시작

[Installing 문서](https://lib.ghostty.org/vt/) 기준 공식 경로는 소스 빌드, CMake, Zig 의존성, Windows 미리 빌드 zip, Apple용 XCFramework, WebAssembly 모듈, Nix flake입니다. 모든 빌드 경로에 Zig 0.17이 필요하고, Zig를 몰라도 됩니다.

릴리스 파일은 한 디렉터리(`https://release.files.ghostty.org/libghostty-vt/VERSION/`)에만 올라가며, 모든 파일에 minisign 서명이 붙습니다. 공식 문서의 소스 빌드 절차는 다음과 같습니다.

```sh
# 서명 확인(공개 키는 Ghostty 앱 릴리스와 같음)
minisign -V -P RWQlAjJC23149WL2sEpT/l0QKy7hMIFhYdQOFy0Z7z7PbneUgvlsnYcV -m SHA256SUMS
sha256sum --ignore-missing -c SHA256SUMS

tar -xzf libghostty-vt-1.0.2.tar.gz
cd libghostty-vt-1.0.2
zig build -Doptimize=ReleaseFast --prefix "$HOME/.local"
```

**주의:** 문서는 GitHub가 `vt-1.0.2` 태그로 자동 생성하는 압축 파일이 아니라 위 릴리스 tarball을 쓰라고 거듭 강조합니다. tarball에만 있는 `LIB_VERSION` 파일이 없으면 `zig build`가 라이브러리가 아니라 Ghostty 앱을 빌드합니다. Git 체크아웃에서 빌드할 때는 `-Demit-lib-vt`를 붙입니다.

필자는 이 환경에서 1.0.0 소스 tarball, 의존성 tarball, WebAssembly 모듈, Zig 0.17.0을 내려받아 체크섬이 공식 값과 일치하는 것까지 확인했지만, 실행 환경의 권한 정책 때문에 빌드와 예제 실행은 하지 못했습니다. **아래 예제는 모두 공식 문서와 `example/` 디렉터리의 코드를 바탕으로 했으며 직접 실행해 확인하지 않았습니다.**

## 실전 예제

### 예제 1. 가장 작은 프로그램: 바이트를 넣고 화면 읽기

공식 문서 첫 페이지의 예제입니다(오류 검사 생략은 원문 그대로). 80x24 터미널을 만들고 색상 시퀀스가 섞인 텍스트를 넣은 뒤 화면을 일반 텍스트로 꺼냅니다.

```c
#include <stdio.h>
#include <string.h>
#include <ghostty/vt.h>

int main(void) {
  GhosttyTerminal terminal;
  ghostty_terminal_new(NULL, &terminal, 80, 24);   // NULL = 기본 할당자

  const char *text = "Hello, \x1b[1;32mworld\x1b[0m!\r\n";
  ghostty_terminal_vt_write(terminal, (const uint8_t *)text, strlen(text));

  GhosttyFormatter formatter;
  ghostty_formatter_terminal_new(NULL, &formatter, terminal);
  uint8_t *buf = NULL;
  size_t len = 0;
  ghostty_formatter_format_alloc(formatter, NULL, &buf, &len);
  fwrite(buf, 1, len, stdout);
  putchar('\n');

  ghostty_free(NULL, buf, len);
  ghostty_formatter_free(formatter);
  ghostty_terminal_free(terminal);
  return 0;
}
```

설치한 라이브러리에 pkg-config로 링크하는 명령도 문서에 있습니다.

```sh
export PKG_CONFIG_PATH="$HOME/.local/lib/pkgconfig"
cc -o hello hello.c $(pkg-config --cflags --libs libghostty-vt) -Wl,-rpath,"$HOME/.local/lib"
./hello
```

문서에 따르면 출력은 `Hello, world!`입니다. 굵은 초록색 정보는 터미널 상태에 남아 있지만 기본 포매터가 일반 텍스트만 내보내기 때문에 보이지 않습니다. 문서는 PTY를 거치지 않는 데이터를 넣을 때 `\n`만으로는 커서가 줄 처음으로 돌아가지 않으므로 `\r\n`을 직접 넣어야 한다고 주의를 줍니다.

### 예제 2. TUI가 지금 보여 주는 화면을 텍스트로 읽기 (에이전트, CI 로그)

공식 문서는 libghostty-vt의 용도로 "TUI가 보여 주는 내용을 읽는 에이전트와 자동화"를 명시합니다. `c-vt-formatter` 예제는 커서 이동과 줄 지우기가 섞인 출력을 넣은 뒤, 최종 화면만 정리된 텍스트로 꺼냅니다. 로그를 그대로 저장하면 덮어쓴 줄과 이스케이프 코드가 섞이지만, 터미널 상태를 거치면 사람이 본 화면 그대로가 남습니다.

```c
// 3행을 쓴 뒤 커서를 돌아가 지우고 다시 쓰는 출력
const char *commands[] = {
  "Line 3: placeholder\r\n",
  "\033[3;1H",                 // CUP: 3행 1열로 이동
  "\033[2K",                   // EL: 줄 전체 지우기
  "Line 3: Overwritten!\r\n",
};
for (size_t i = 0; i < sizeof(commands) / sizeof(commands[0]); i++)
  ghostty_terminal_vt_write(terminal, (const uint8_t *)commands[i],
                            strlen(commands[i]));

GhosttyFormatter formatter;
ghostty_formatter_terminal_new(NULL, &formatter, terminal);

GhosttyFormatterFormat emit = GHOSTTY_FORMATTER_FORMAT_PLAIN;
ghostty_formatter_set(formatter, GHOSTTY_FORMATTER_OPT_EMIT, &emit);
bool trim = true;   // 줄 끝 공백 제거
ghostty_formatter_set(formatter, GHOSTTY_FORMATTER_OPT_TRIM, &trim);
```

원본 예제는 이어서 `GhosttyWriter` 콜백으로 결과를 stdout에 바로 흘려보냅니다. 스타일까지 필요하면 `c-vt-stream` 예제처럼 렌더 상태를 만들고 `ghostty_render_state_row_iterator_next_dirty()`로 바뀐 행만 돌며 셀별 문자열과 `GhosttyStyle`을 읽으면 됩니다.

### 예제 3. 실제 프로그램을 돌릴 때: 질의 응답을 PTY로 돌려주기

바이트를 넣고 결과만 읽을 때는 이펙트가 필요 없지만, 셸이나 Neovim을 실제로 돌리면 프로그램이 커서 위치나 색상 테마를 터미널에 묻습니다. 응답 콜백을 등록하지 않으면 그 질문은 답을 받지 못합니다. 아래는 헤더의 콜백 타입(`GhosttyTerminalWritePtyFn`)과 이펙트 가이드의 등록 방식을 합친 뼈대이며, `pty_fd`는 앱이 이미 열어 둔 PTY라고 가정합니다.

```c
static void on_write_pty(GhosttyTerminal t, void *userdata,
                         const uint8_t *data, size_t len) {
  int pty_fd = *(int *)userdata;
  write(pty_fd, data, len);   // 응답 바이트를 프로그램 쪽으로 돌려줌
}

ghostty_terminal_set(terminal, GHOSTTY_TERMINAL_OPT_USERDATA, &pty_fd);
ghostty_terminal_set(terminal, GHOSTTY_TERMINAL_OPT_WRITE_PTY,
                     (const void *)on_write_pty);
```

가이드가 정한 규칙을 지켜야 합니다. 콜백은 `vt_write` 도중에 동기적으로 불리므로 오래 걸리는 일을 하면 터미널 전체가 느려지고, 콜백 안에서 같은 터미널에 다시 쓰면 안 되며, 넘겨받은 버퍼는 콜백이 끝나면 무효가 되므로 필요하면 복사해야 합니다. 이 예제는 공식 예제 파일을 그대로 옮긴 것이 아니라 헤더와 가이드를 조합한 것이므로, 실제로는 `c-vt-effects` 예제를 기준으로 삼는 것이 안전합니다.

### 예제 4. Ctrl+C를 Kitty 키보드 프로토콜로 인코딩하기

JetBrains가 libghostty로 바꾼 가장 큰 이유 중 하나였던 Kitty 키보드 프로토콜은 인코더 API로 씁니다. `c-vt-encode-key` 예제를 줄인 것입니다.

```c
GhosttyKeyEncoder encoder;
ghostty_key_encoder_new(NULL, &encoder);
ghostty_key_encoder_set(encoder, GHOSTTY_KEY_ENCODER_OPT_KITTY_FLAGS,
                        &(uint8_t){GHOSTTY_KITTY_KEY_ALL});

GhosttyKeyEvent event;
ghostty_key_event_new(NULL, &event);
ghostty_key_event_set_action(event, GHOSTTY_KEY_ACTION_PRESS);
ghostty_key_event_set_key(event, GHOSTTY_KEY_C);
ghostty_key_event_set_mods(event, GHOSTTY_MODS_CTRL);
ghostty_key_event_set_unshifted_codepoint(event, 'c');

uint8_t buf[128];
size_t written = 0;
ghostty_key_encoder_encode(encoder, event, buf, sizeof(buf), &written);
// buf[0..written]를 PTY에 씀

ghostty_key_event_free(event);
ghostty_key_encoder_free(encoder);
```

실제 앱에서는 프로그램이 켠 키보드 모드에 맞춰 플래그를 정해야 하므로, 고정 값 대신 터미널 상태에서 설정을 가져오는 흐름이 필요합니다(이 부분은 공식 예제에 없어 확인하지 못했습니다).

### 예제 5. CMake 프로젝트에 붙이기

`dist/cmake/README.md`가 권장하는 방식은 `FetchContent`로 릴리스 tarball을 받아 빌드하는 것입니다. CMake가 내부에서 `zig build`를 부르므로 PATH에 Zig는 있어야 합니다.

```cmake
include(FetchContent)
FetchContent_Declare(ghostty
    URL https://release.files.ghostty.org/libghostty-vt/1.0.0/libghostty-vt-1.0.0.tar.gz
    URL_HASH SHA256=4a6ef758be721923e1969e7b81b443dcc92d8dd3fb5a39600c03a8817a753676
)
FetchContent_MakeAvailable(ghostty)

add_executable(myapp main.c)
target_link_libraries(myapp PRIVATE ghostty-vt)
```

해시는 공식 `SHA256SUMS` 파일에 있는 1.0.0 소스 tarball 값을 그대로 옮겼습니다. 이미 설치한 라이브러리를 쓸 때는 `find_package(ghostty-vt REQUIRED)`와 `ghostty-vt::ghostty-vt` 타깃을 씁니다.

## 실무 팁 & 자주 겪는 문제

- **Zig 버전은 마이너까지 맞아야 합니다.** 1.0.x는 Zig 0.17.x만 받고 0.16이나 0.18이면 빌드가 오류로 멈춥니다. 문서는 Zig 버전이 ABI 약속에 포함되지 않으며 라이브러리 버전마다 요구 Zig 버전이 달라질 수 있다고 밝힙니다.
- **오프라인 빌드에는 의존성 tarball을 씁니다.** 패키징 문서는 `--system ../libghostty-vt-1.0.0-deps`로 빌드하고, `ZIG_GLOBAL_CACHE_DIR`은 새 빈 디렉터리로 두라고 권합니다. Zig 0.17에서는 패키지 압축 파일이 남은 캐시를 쓰면 "reached unreachable code"로 빌드가 죽을 수 있다고 적혀 있습니다.
- **모든 `GhosttyResult`를 확인합니다.** 문서는 할당 실패를 포함한 모든 실패를 결과 값으로 돌려주고 라이브러리가 손상된 상태에 빠지지 않는다고 설명합니다. 예제 1처럼 오류 검사를 생략한 코드는 설명용입니다.
- **동적 링크라면 런타임 버전을 확인합니다.** 컴파일 시점에는 `GHOSTTY_VT_VERSION_AT_LEAST()`, 실행 시점에는 `ghostty_version()`과 `ghostty_build_info()`로 헤더와 로드된 라이브러리가 맞는지 비교하라고 Stability 문서가 안내합니다.
- **Windows는 gnu ABI 빌드입니다.** MSVC 프로그램도 import 라이브러리로 링크할 수 있고, DLL 이름에 메이저 버전이 없어 나란히 설치(side-by-side)는 지원하지 않습니다. arm64 zip은 빌드만 하고 실행 테스트는 하지 않는다고 문서에 적혀 있습니다.
- **1.0.x 패치에도 동작 수정이 있습니다.** 1.0.1은 OSC 133 프롬프트를 쓰는 셸에서 열 크기를 바꿀 때 오래된 프롬프트가 남던 문제를, 1.0.2는 여백(margin)이 있는 줄 삽입·삭제에서 소프트 줄바꿈이 깨지던 문제를 고쳤습니다. 릴리스 노트를 보고 최신 패치로 올리는 것이 좋습니다.

## 비슷한 도구와 비교

| 항목 | libghostty-vt | JediTerm | xterm.js | libvterm |
|---|---|---|---|---|
| 형태 | C 라이브러리(Zig 구현) | Java 라이브러리 | JavaScript 라이브러리 | C 라이브러리 |
| 렌더링 포함 | 아니요(렌더 상태만 제공) | 예(Swing) | 예(브라우저 DOM/캔버스) | 아니요 |
| 주 사용처 | JetBrains IDE(2026.3부터), Neovim 교체 PR, 웹(WASM) | JetBrains IDE(2026.3 이전) | VS Code 등 웹 기반 터미널 | Neovim 내장 터미널(현재) |
| Kitty 키보드 프로토콜 | 지원 | 미지원(JetBrains 글 기준) | 확인하지 않음 | 확인하지 않음 |
| ABI·API 안정성 정책 | semver, libabigail로 CI 검사 | 확인하지 않음 | 확인하지 않음 | 확인하지 않음 |

libghostty-vt와 JediTerm 열은 Ghostty 공식 문서와 JetBrains 공식 블로그 기준이고, xterm.js와 libvterm 열은 일반적으로 알려진 특징 기준입니다. 웹에서 xterm.js를 쓰던 프로젝트를 위해 [ghostty-web](https://github.com/coder/ghostty-web)이 xterm.js 호환 API를 가진 WASM 빌드를 제공한다고 발표 글이 소개합니다.

## 장점과 한계

### 장점

- 수년간 Ghostty 앱에서 쓰인 코어를 그대로 꺼낸 것이라, 기능 범위(Kitty 키보드·그래픽, OSC 133, 그래핌 클러스터링 등)가 처음부터 넓습니다.
- 런타임 의존성이 libc뿐이고, 필요하면 libc조차 없이 빌드됩니다. 스레드를 만들지 않고 할당자를 바꿀 수 있어 서버, 브라우저, 임베디드까지 같은 코드를 씁니다.
- ABI 약속이 문서화돼 있고 CI가 기계적으로 검사합니다. 서명된 tarball, 오프라인 빌드용 의존성 묶음, 라이선스 목록까지 갖춰 배포판 패키징을 처음부터 고려했습니다.
- 문서 기준 AFL++ 퍼징을 전용 머신 여러 대에서 상시 돌리며, 기본 설정에서 신뢰할 수 없는 입력을 넣어도 부작용이 없도록 설계했습니다.

### 한계

- 렌더링, 폰트, 창, PTY 관리가 빠져 있어 "터미널 하나 띄우기"는 여전히 상당한 작업입니다. 발표 글은 C 약 1,500줄짜리 [Ghostling](https://github.com/ghostty-org/ghostling)으로 완전한 터미널을 만들 수 있다고 하지만, 각주에서 여기서 말하는 "기능"과 "성능"은 libghostty-vt가 맡는 프로토콜 범위와 파싱 처리량·메모리에 한정된다고 스스로 밝힙니다.
- Linux용 공식 바이너리 패키지가 없고, 빌드에 특정 Zig 버전이 필요합니다. Zig가 1.0 전이라 이 요구는 당분간 계속될 것으로 보입니다.
- 스냅숏 바이트 형식은 ABI 약속 밖이라, 상태를 디스크에 저장했다가 다른 버전에서 복원하는 설계는 조심해야 합니다.
- 사용자 수(JetBrains 1,250만 명, "수천만 명")는 프로젝트와 JetBrains 연간 보고서를 근거로 한 추정치이고, 문서 스스로 사용량을 추적하지 않는다고 밝힙니다.

## 인사이트

**왜 지금 중요한가: 터미널이 다시 "앱 안의 부품"이 되고 있습니다.** 몇 년 전까지 터미널은 사람이 셸을 쓰는 창이었고, IDE나 웹 서비스에 넣는 터미널은 "대충 돌아가면 되는" 부가 기능이었습니다. 지금은 Claude Code, Codex 같은 CLI 에이전트가 터미널 위에서 돌고, 그 에이전트를 여러 개 띄우는 작업 공간 앱이 터미널을 대량으로 내장합니다. JetBrains 글이 전환 이유의 첫 문단에 AI 코딩 에이전트를 든 것은 우연이 아니라고 봅니다. Shift+Enter 한 번이 프롬프트 전송이냐 줄바꿈이냐를 가르는 상황에서는, 키보드 프로토콜과 테마 질의 같은 "사소한" 시퀀스 지원이 곧 제품 품질이 됩니다. 발표 글이 herdr, cmux 같은 에이전트용 도구가 자체 에뮬레이터 대신 libghostty 위에 만들어졌다고 소개하는 것도 같은 흐름입니다.

**블로그의 기존 글과의 연결: Orca와의 대비.** [Orca 소개 글](/opensource/2026/10/27/orca.html)에서 본 것처럼 Orca는 여러 에이전트를 워크트리별 터미널로 나란히 돌리고, 터미널 부분은 `node-pty`와 `@xterm/xterm`으로 만듭니다(첫 실행 때 Ghostty 설정을 가져올지 묻기도 합니다). Electron 앱이라면 xterm.js가 자연스러운 선택이지만, libghostty-vt는 같은 일을 네이티브 앱, 서버, 브라우저(WASM)에서 같은 코어로 할 수 있게 합니다. 필자의 판단으로는 에이전트 작업 공간 도구가 늘수록 "터미널 수십 개를 한 프로세스에서 가볍게 유지"하는 요구가 커지고, 발표 글의 "4코어·8GB 서버에서 셸이 출력 중인 터미널 1만 개" 실험(필자 Hashimoto 본인의 측정이며 재현 조건은 공개되지 않음)은 바로 그 요구를 겨냥한 수치로 읽힙니다. 같은 맥락에서 공식 문서가 용도로 꼽은 "TUI가 보여 주는 화면을 읽는 에이전트"는 예제 2처럼 원시 로그 대신 렌더된 화면을 모델에 넘기는 하네스 설계로 이어질 수 있습니다.

**실무에 주는 의미: 자체 ANSI 파서를 유지하고 있다면 교체 비용을 다시 계산할 때입니다.** 빌드 로그 뷰어, 웹 콘솔, TUI 테스트 도구처럼 "색만 대충 칠하는" 자체 구현을 가진 팀은 1.0 이전에는 API가 바뀔 위험 때문에 libghostty 도입을 미룰 이유가 있었습니다. 이제 ABI가 고정됐고 WASM 크기용 빌드가 1MB 미만이므로 그 이유가 많이 줄었습니다. 반대로 이미 xterm.js로 렌더링까지 해결한 웹 앱이라면 얻는 것이 파싱 정확도뿐이라 서두를 필요는 적어 보입니다.

**한계와 반론.** 첫째, "libghostty 1.0"이라는 이름과 달리 1.0이 된 것은 파싱과 상태 관리뿐입니다. 2025년 글이 예고한 GPU 렌더링, GTK 위젯, Swift 프레임워크 같은 다른 `libghostty-<x>` 라이브러리는 아직 없습니다. 둘째, 발표 글의 "2025년에 존재한 거의 모든 터미널보다 기능과 성능이 낫다"는 표현은 비교 대상과 측정 방법이 제시되지 않은 주장입니다. 셋째, 같은 저장소의 AI_POLICY.md는 외부 기여에 AI 사용을 반드시 밝히게 하고 저품질 AI 기여자를 공개 목록에 올린다고 정하고 있습니다. 라이브러리 사용에는 영향이 없지만, 에이전트로 패치를 만들어 기여하려는 팀이라면 미리 알아 둘 규칙입니다.

**앞으로 지켜볼 점.** Neovim의 libvterm 교체 PR은 발표 시점(2026-11-06)에 승인된 상태로 태그된 릴리스를 기다리고 있었습니다. 이것이 병합되고 주요 배포판이 `libghostty-vt` 패키지를 내놓으면 "Ghostty 프로젝트의 부산물"에서 "시스템 라이브러리"로 위치가 바뀝니다. 또 Zig 1.0 전까지 라이브러리마다 다른 Zig 버전을 요구하는 구조가 배포판 패키저에게 얼마나 부담이 되는지, 렌더링 라이브러리가 언제 나오는지가 다음 판단 지점입니다.

<!-- EDITOR_NOTE: 운영자가 직접 써 본 경험이나 의견을 여기에 추가하세요. -->

## 이런 분께 추천

- IDE, 웹 콘솔, 원격 세션, 세션 녹화·재생 도구에 터미널을 넣어야 하는 개발자
- 자체 ANSI 파서로 빌드 로그나 CI 출력을 그리고 있는데 깨지는 출력에 시달리는 팀
- TUI 프로그램의 화면을 텍스트로 읽어 테스트하거나 에이전트에 넘기려는 경우
- 터미널 앱이나 멀티플렉서를 새로 만들면서 시퀀스 해석은 검증된 코어에 맡기고 싶은 경우

## 이런 경우엔 다른 도구

- 그냥 좋은 터미널 앱이 필요하다면 라이브러리가 아니라 Ghostty 앱이나 쓰고 있는 터미널을 쓰면 됩니다.
- Electron이나 브라우저에서 렌더링까지 한 번에 해결하고 싶고 Zig 빌드를 들이고 싶지 않다면 xterm.js가 더 간단합니다. xterm.js API를 유지하면서 코어만 바꾸고 싶다면 ghostty-web을 검토할 만합니다.
- 빌드 도구 체인에 Zig를 추가할 수 없고 배포판 패키지도 없는 환경이라면, 패키지가 나올 때까지 기다리는 편이 낫습니다.

## 참고 링크

- [Libghostty 1.0 발표 글 (Mitchell Hashimoto, 2026-11-06)](https://mitchellh.com/writing/libghostty-1-0)
- [Libghostty Is Coming (2025-09-22)](https://mitchellh.com/writing/libghostty-is-coming)
- [libghostty-vt 공식 문서 (설치, 안정성, 이펙트, 릴리스 노트)](https://lib.ghostty.org/vt/)
- [ghostty-org/ghostty 저장소](https://github.com/ghostty-org/ghostty) · [PACKAGING-LIBGHOSTTY.md](https://github.com/ghostty-org/ghostty/blob/main/PACKAGING-LIBGHOSTTY.md) · [예제 디렉터리](https://github.com/ghostty-org/ghostty/tree/main/example)
- [The Terminal in JetBrains IDEs Now Runs on libghostty (JetBrains 블로그)](https://blog.jetbrains.com/platform/2026/10/jetbrains-terminal-now-uses-ghostty/)
- [Ghostling: 약 1,500줄 C로 만든 최소 터미널 예제](https://github.com/ghostty-org/ghostling)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
