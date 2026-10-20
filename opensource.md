---
layout: default
title: 오픈소스 소개
permalink: /opensource.html
---

# 오픈소스 소개

{% if site.categories.opensource %}
<ul>
  {% for post in site.categories.opensource %}
    <li><span>{{ post.date | date: "%Y-%m-%d" }}</span> — <a href="{{ post.url | relative_url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>
{% else %}
아직 글이 없습니다.
{% endif %}

[← Home]({{ "/" | relative_url }})
