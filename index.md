---
layout: default
title: Home
---

# 안녕하세요 👋

**Luckisstar**의 GitHub Pages에 오신 것을 환영합니다.

## 카테고리

- [📄 논문 소개]({{ "/papers.html" | relative_url }}) ({{ site.categories.papers | size }})
- [🛠 기술 소개]({{ "/tech.html" | relative_url }}) ({{ site.categories.tech | size }})
- [📦 오픈소스 소개]({{ "/opensource.html" | relative_url }}) ({{ site.categories.opensource | size }})
- [About]({{ "/about.html" | relative_url }})

## 최근 글

<ul>
  {% for post in site.posts limit:10 %}
    <li>
      <span>{{ post.date | date: "%Y-%m-%d" }}</span> —
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>
