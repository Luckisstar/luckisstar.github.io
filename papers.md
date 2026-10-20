---
layout: default
title: 논문 소개
permalink: /papers.html
---

# 논문 소개

<ul>
  {% for post in site.categories.papers %}
    <li><span>{{ post.date | date: "%Y-%m-%d" }}</span> — <a href="{{ post.url | relative_url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>

[← Home]({{ "/" | relative_url }})
