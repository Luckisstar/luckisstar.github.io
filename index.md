---
layout: default
title: Home
---

# 안녕하세요 👋

**Luckisstar**의 GitHub Pages에 오신 것을 환영합니다.

- [About](./about.html)

## 최근 글

<ul>
  {% for post in site.posts %}
    <li>
      <span>{{ post.date | date: "%Y-%m-%d" }}</span> —
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>
