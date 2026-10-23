---
layout: default
title: 논문 소개
description: "AI·머신러닝 논문을 한국어로 요약하고 핵심 아이디어와 의미를 정리한 글 모음입니다."
permalink: /papers.html
---

# 논문 소개

<ul>
  {% for post in site.categories.papers %}
    <li><span>{{ post.date | date: "%Y-%m-%d" }}</span> — <a href="{{ post.url | relative_url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>

[← Home]({{ "/" | relative_url }})
