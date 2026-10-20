---
layout: default
title: "[오픈소스 소개] LocalStack: 내 PC에서 돌리는 AWS 클라우드 에뮬레이터"
date: 2026-10-20
categories: [opensource]
---

# [오픈소스 소개] LocalStack: 내 PC에서 돌리는 AWS 클라우드 에뮬레이터

- **저장소:** [localstack/localstack](https://github.com/localstack/localstack) · [localstack.cloud](https://localstack.cloud) · [문서](https://docs.localstack.cloud)
- **언어:** Python
- **현황 (2026-10-20 기준):** GitHub 스타 약 6.5만 개, 마지막 릴리스 v4.14.0 (2026년 2월)

> **⚠️ 저장소가 보관(archived) 상태입니다.**
> LocalStack 팀은 개발을 하나의 통합 이미지로 합치면서 이 저장소를 **읽기 전용**으로 전환했습니다.
> 앞으로는 [LocalStack for AWS](https://www.localstack.cloud/pricing) 요금제를 통해 제공되며, 비상업적 용도로는 이 저장소와 같은 기능을 가진 **무료 Hobby 플랜**을 쓸 수 있다고 안내합니다.
> 버그 제보와 기능 요청은 [GitHub Discussions](https://github.com/orgs/localstack/discussions)와 Slack 커뮤니티에서 받습니다.

## 한 줄 요약

**AWS 서비스를 내 노트북이나 CI 안에서 흉내 내 주는 도구**입니다. 실제 AWS에 연결하지 않고도 Lambda, S3, DynamoDB 같은 서비스를 로컬에서 개발·테스트할 수 있습니다.

## 무엇을 해주나

- Docker 컨테이너 하나로 실행되는 클라우드 서비스 에뮬레이터입니다.
- Lambda, S3, DynamoDB, Kinesis, SQS, SNS, API Gateway, CloudFormation 등 많은 AWS 서비스를 지원합니다.
- AWS CDK나 Terraform으로 작성한 인프라도 로컬에서 시험해볼 수 있습니다.
- AWS 요금 걱정 없이 테스트할 수 있고, 인터넷 없이도 개발할 수 있습니다.

## 빠르게 시작하기

Docker가 설치되어 있어야 합니다.

```bash
# CLI 설치 (macOS / Linux)
brew install localstack/tap/localstack-cli
# 또는
python3 -m pip install localstack

# 실행
localstack start -d

# 서비스 상태 확인
localstack status services
```

AWS CLI 대신 `awslocal`(별도 설치)을 쓰면 요청이 자동으로 LocalStack으로 갑니다.

```bash
awslocal sqs create-queue --queue-name sample-queue
```

`sudo`나 root 계정으로 설치·실행하지 말라고 안내합니다.

## 이런 분께 추천

- AWS 기반 서비스를 개발하면서 테스트 비용과 시간을 줄이고 싶은 분
- CI에서 실제 AWS 없이 통합 테스트를 돌리고 싶은 팀
- AWS를 처음 배우면서 부담 없이 이것저것 시도해보고 싶은 분

단, 오픈소스 저장소는 더 이상 업데이트되지 않으니 새로 도입한다면 공식 사이트의 최신 배포 방식을 먼저 확인하세요.

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
