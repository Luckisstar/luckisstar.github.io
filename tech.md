---
layout: default
title: 기술 소개
description: "새로 나온 AI 모델과 기술 소식을 한국어로 정리한 글 모음입니다."
permalink: /tech.html
---

# 기술 소개

{% if site.categories.tech %}
{% include post-list.html posts=site.categories.tech limit=1000 %}
{% else %}
아직 글이 없습니다.
{% endif %}

[← Home]({{ "/" | relative_url }})
