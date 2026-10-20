---
layout: default
title: 기술 소개
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
