---
layout: default
title: 기술 소개
description: "새로 나온 AI 모델과 기술 소식을 한국어로 정리한 글 모음입니다."
permalink: /tech.html
---

# 기술 소개

{% if site.categories.tech %}
<ul>
  {% for post in site.categories.tech %}
    <li><span>{{ post.date | date: "%Y-%m-%d" }}</span> — <a href="{{ post.url | relative_url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>
{% else %}
아직 글이 없습니다.
{% endif %}

[← Home]({{ "/" | relative_url }})
