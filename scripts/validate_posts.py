#!/usr/bin/env python3
"""블로그 글 형식 검증. 사용법: python3 scripts/validate_posts.py [글 경로 ...]

경로를 주지 않으면 _posts 아래 모든 글을 검사한다. 오류가 하나라도 있으면 종료 코드 1.
STRICT_SINCE 이후 날짜의 글에는 CLAUDE.md의 새 기준(시각 포함 date, 필수 섹션, 인사이트 등)을 적용한다.
"""
import datetime as dt
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRICT_SINCE = dt.date(2026, 10, 24)
KST = dt.timezone(dt.timedelta(hours=9))

CATEGORIES = {
    "papers": ("논문 소개", ["한 줄 요약", "왜 이 연구가 필요한가", "제안 방법", "주요 결과", "한계", "인사이트", "참고 링크"]),
    "tech": ("기술 소개", ["한 줄 요약", "배경", "핵심 내용", "한계와 논란", "인사이트", "참고 링크"]),
    "opensource": ("오픈소스 소개", ["한 줄 요약", "어떤 문제를 푸나", "동작 원리", "설치와 시작", "실전 예제",
                                "비슷한 도구와 비교", "장점과 한계", "인사이트", "참고 링크"]),
}
PLACEHOLDERS = ["YYYY-MM-DD", "YYYY년", "owner/repo", "](https://)", "arxiv.org/abs/)", "XXXX.XXXXX", "N개", "vX.Y.Z"]
FOOTER_RE = re.compile(r'^\[← (.+) 목록\]\(\{\{ "/([a-z]+)\.html" \| relative_url \}\}\) · \[Home\]\(\{\{ "/" \| relative_url \}\}\)$')
ALLOWED_LIQUID = re.compile(r'\{\{ "/[a-z]*(\.html)?" \| relative_url \}\}')


def parse_front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if kv:
            v = kv.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] == '"':
                v = v[1:-1]
            fm[kv.group(1)] = v
    return fm, text[m.end():]


def parse_date(raw):
    m = re.match(r"^(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}:\d{2}) ([+-]\d{4}))?$", raw or "")
    if not m:
        return None, False
    if m.group(2):
        when = dt.datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%Y-%m-%d %H:%M:%S %z")
        return when, True
    return dt.datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=KST), False


def check(path):
    errors, warnings = [], []
    rel = os.path.relpath(path, ROOT)
    text = open(path, encoding="utf-8").read()

    m = re.match(r"^_posts/([a-z]+)/(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$", rel)
    if not m:
        return [f"파일 경로 형식 오류: _posts/<카테고리>/YYYY-MM-DD-<슬러그>.md 이어야 함"], warnings
    folder, file_date, _slug = m.groups()
    if folder not in CATEGORIES:
        errors.append(f"알 수 없는 카테고리 폴더: {folder}")
        return errors, warnings
    cat_name, required = CATEGORIES[folder]

    fm, body = parse_front_matter(text)
    if fm is None:
        return ["front matter(---) 없음"], warnings
    for key in ("layout", "title", "description", "date", "categories"):
        if not fm.get(key):
            errors.append(f"front matter에 {key} 없음")
    if fm.get("layout") and fm["layout"] != "default":
        errors.append("layout은 default 여야 함")
    if fm.get("categories") and fm["categories"] != f"[{folder}]":
        errors.append(f"categories는 [{folder}] 여야 함 (현재 {fm['categories']})")
    title = fm.get("title", "")
    if title and not title.startswith(f"[{cat_name}] "):
        errors.append(f"title은 '[{cat_name}] '로 시작해야 함")

    when, has_time = parse_date(fm.get("date"))
    if fm.get("date") and not when:
        errors.append(f"date 형식 오류: {fm.get('date')}")
    strict = bool(when) and when.astimezone(KST).date() >= STRICT_SINCE
    if when:
        if when.astimezone(KST).strftime("%Y-%m-%d") != file_date:
            errors.append(f"파일 이름 날짜({file_date})와 date({fm['date']})의 한국 시간 날짜가 다름")
        if when > dt.datetime.now(dt.timezone.utc):
            errors.append("date가 미래 시각이라 게시되지 않음")
        if strict and not has_time:
            errors.append("date에 시각과 +0900을 포함해야 함 (예: 2026-10-27 07:00:00 +0900)")

    desc = fm.get("description", "")
    if desc:
        if desc == title:
            errors.append("description이 title과 같음")
        if strict and not 50 <= len(desc) <= 200:
            warnings.append(f"description 길이 {len(desc)}자 (권장 70~160자)")

    lines = body.strip("\n").splitlines()
    h1 = next((l for l in lines if l.startswith("# ")), None)
    if not h1:
        errors.append("본문 H1(# 제목) 없음")
    elif strict and h1[2:].strip() != title:
        errors.append("본문 H1이 title과 다름")

    last = lines[-1].strip() if lines else ""
    fm_footer = FOOTER_RE.match(last)
    if not fm_footer or fm_footer.group(1) != cat_name or fm_footer.group(2) != folder:
        errors.append(f"마지막 줄이 '[← {cat_name} 목록]({{{{ \"/{folder}.html\" | relative_url }}}}) · [Home](...)' 형식이 아님")

    # Liquid: raw 블록 밖의 {{ }}, {% %}는 허용된 링크만
    if body.count("{% raw %}") != body.count("{% endraw %}"):
        errors.append("{% raw %}와 {% endraw %} 개수가 다름")
    outside = re.sub(r"\{% raw %\}.*?\{% endraw %\}", "", body, flags=re.S)
    outside = ALLOWED_LIQUID.sub("", outside)
    for token in ("{{", "{%"):
        if token in outside:
            ln = next(i for i, l in enumerate(text.splitlines(), 1) if token in ALLOWED_LIQUID.sub("", l) and "raw %}" not in l)
            errors.append(f"raw 블록 밖에 Liquid 구문 '{token}' 있음 ({ln}행 부근): {{% raw %}}로 감싸야 함")
            break

    fences = [l for l in lines if l.lstrip().startswith("```")]
    if len(fences) % 2:
        errors.append(f"코드 블록(```) 개수가 홀수({len(fences)})")

    if "—" in body:
        (errors if strict else warnings).append(f"em dash(—) {body.count('—')}개 사용")

    if strict:
        h2 = [l[3:].strip() for l in lines if l.startswith("## ")]
        for sec in required:
            if not any(h.startswith(sec) for h in h2):
                errors.append(f"필수 섹션 없음: ## {sec}")
        no_code = re.sub(r"```.*?```", "", body, flags=re.S)
        for ph in PLACEHOLDERS:
            if ph in no_code:
                errors.append(f"템플릿 자리표시자 남아 있음: {ph}")
        if "EDITOR_NOTE" not in body:
            warnings.append("인사이트 섹션 끝에 EDITOR_NOTE 주석이 없음")

    return errors, warnings


def main(argv):
    paths = argv or sorted(glob.glob(os.path.join(ROOT, "_posts", "*", "*.md")))
    stray = [p for p in glob.glob(os.path.join(ROOT, "_posts", "*.md"))]
    total_err = 0
    slugs = {}
    for p in stray:
        print(f"ERROR {os.path.relpath(p, ROOT)}: 카테고리 폴더 밖에 있는 글")
        total_err += 1
    for p in paths:
        p = os.path.abspath(p)
        rel = os.path.relpath(p, ROOT)
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-|\.md$", "", os.path.basename(p))
        if slug in slugs:
            print(f"ERROR {rel}: 슬러그 '{slug}'가 {slugs[slug]}와 중복")
            total_err += 1
        slugs[slug] = rel
        errors, warnings = check(p)
        for e in errors:
            print(f"ERROR {rel}: {e}")
        for w in warnings:
            print(f"WARN  {rel}: {w}")
        total_err += len(errors)
    print(f"\n{len(paths)}개 글 검사, 오류 {total_err}개")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
