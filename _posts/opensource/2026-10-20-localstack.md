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
> LocalStack 팀은 개발을 하나의 통합 이미지로 합치면서 2026년 3월 이 저장소를 **읽기 전용**으로 전환했습니다. v4.14.0(2026-02-26)이 이 저장소의 마지막 릴리스이고, 이후 버전은 `2026.03`, `2026.10.0`처럼 날짜 기반 버전으로 나옵니다.
> 공식 블로그에 따르면 **2026년 3월 23일부터 최신 이미지는 인증 토큰(Auth Token)이 있어야 실행**됩니다. 비상업적 용도라면 이 저장소와 같은 기능을 가진 **무료 Hobby 플랜**을 쓸 수 있고, 상업적 용도는 유료 플랜이 필요합니다. 자세한 조건은 [요금제 페이지](https://www.localstack.cloud/pricing)를 확인하세요.
> CLI도 바뀌었습니다. 기존 `localstack` CLI와 `awslocal`, `tflocal`, `cdklocal`은 deprecated 되었고 새 CLI인 **`lstk`**로 대체되는 중입니다.
> 버그 제보와 기능 요청은 [GitHub Discussions](https://github.com/orgs/localstack/discussions)와 Slack 커뮤니티에서 받습니다.

## 한 줄 요약

**AWS 서비스를 내 노트북이나 CI 안에서 흉내 내 주는 도구**입니다. 실제 AWS 계정에 연결하지 않고도 Lambda, S3, DynamoDB, SQS 같은 서비스를 Docker 컨테이너 하나로 띄워서 개발하고 테스트할 수 있습니다.

## 어떤 문제를 푸나

AWS 기반 서비스를 만들다 보면 이런 순간이 자주 옵니다.

- Lambda 코드 한 줄을 고쳤는데, 배포하고 로그를 보기까지 몇 분씩 걸립니다.
- 통합 테스트를 돌릴 때마다 실제 AWS에 리소스를 만들었다 지우느라 비용과 시간이 듭니다.
- 팀원마다 개발용 AWS 계정과 권한을 나눠 주고 정리하는 일이 번거롭습니다.
- CI에서 테스트가 실제 클라우드 상태에 따라 가끔 실패합니다(이른바 flaky 테스트).
- Terraform이나 CDK 코드를 실제 계정에 적용하기 전에 "일단 돌아가는지"만 빨리 보고 싶습니다.

LocalStack은 AWS API를 로컬 컨테이너 안에서 에뮬레이션해서 이런 반복 작업을 내 컴퓨터 안으로 가져옵니다. AWS SDK나 CLI가 보내는 요청의 **목적지(엔드포인트)만 바꾸면** 코드는 거의 그대로 둘 수 있다는 점이 핵심입니다.

## 핵심 개념 / 동작 원리

### 하나의 게이트웨이, 포트 4566

LocalStack은 모든 AWS 서비스를 **하나의 HTTP 게이트웨이(기본 포트 4566)** 뒤에 둡니다. 요청 헤더와 서명 정보를 보고 어느 서비스로 갈지 판단합니다.

```
 앱 / AWS CLI / SDK / Terraform / CDK
              │  endpoint = :4566
              ▼
 ┌────────── LocalStack 컨테이너 ──────────┐
 │  Gateway (4566, 443)                    │
 │    ├─ S3      ├─ SQS     ├─ DynamoDB    │
 │    ├─ Lambda  ├─ SNS     ├─ IAM ...     │
 │  상태 저장: /var/lib/localstack          │
 └──────────────┬──────────────────────────┘
                │ docker.sock
                ▼
     Lambda 실행용 별도 컨테이너
```

### 꼭 알아야 할 용어

- **엔드포인트:** 기본값은 `http://localhost.localstack.cloud:4566`입니다. 이 도메인은 `127.0.0.1`로 해석되며, S3 가상 호스트 방식(`버킷이름.s3...`) 주소를 쓰기 위해 권장됩니다. 사내망 등에서 이 도메인이 막히면 `http://localhost:4566`을 씁니다.
- **가짜 자격 증명:** 액세스 키와 시크릿은 `test`처럼 아무 값이나 넣으면 됩니다. 기본 계정 ID는 `000000000000`, 기본 리전은 `us-east-1`입니다.
- **Docker 소켓 마운트:** Lambda처럼 실제 코드를 실행해야 하는 서비스는 LocalStack이 호스트의 Docker를 이용해 별도 컨테이너를 띄웁니다. 그래서 `/var/run/docker.sock`을 마운트합니다.
- **포트 4510~4559:** 일부 서비스(예: 데이터베이스 계열)가 추가 엔드포인트를 열 때 쓰는 외부 포트 범위입니다.
- **영속성(Persistence):** 기본적으로 컨테이너를 내리면 상태가 사라집니다. `PERSISTENCE=1`(유료 플랜 기능) 또는 스냅샷(`lstk snapshot`)으로 상태를 보존합니다.
- **Auth Token:** 2026년 3월 이후 최신 이미지는 라이선스 활성화를 위해 토큰이 필요합니다. 토큰이 없거나 활성화에 실패하면 시작 단계에서 종료됩니다.

## 주요 기능

### 서비스 에뮬레이션

- 요금제 페이지 기준으로 Hobby 30개 이상, Base 55개 이상, Ultimate 110개 이상의 서비스를 에뮬레이션합니다.
- Lambda, S3, DynamoDB, SQS, SNS, Kinesis, API Gateway, CloudFormation, Step Functions, Secrets Manager, SSM 등 자주 쓰는 서비스가 포함됩니다.
- 서비스별 지원 범위는 [기능 커버리지 문서](https://docs.localstack.cloud/references/coverage/)에서 API 단위로 확인할 수 있습니다. 예를 들어 Lambda 문서는 88개 작업 중 81개가 구현되어 있다고 밝힙니다.

### 개발 도구 연동

- **`lstk` CLI:** Go로 만든 새 CLI입니다. 브라우저 로그인, 컨테이너 시작·중지, 로그, 스냅샷, 진단(`doctor`)을 한 번에 처리합니다.
- **도구 프록시:** `lstk aws`, `lstk terraform`(별칭 `lstk tf`), `lstk cdk`, `lstk sam`이 각 도구를 LocalStack으로 향하게 해 줍니다.
- **SDK:** boto3, JavaScript, Java, Go, .NET 등 공식 SDK에서 엔드포인트만 바꾸면 됩니다. 최신 SDK는 `AWS_ENDPOINT_URL` 환경 변수를 인식합니다.
- **IaC:** Terraform, OpenTofu, CDK, SAM, Pulumi, Serverless Framework, Crossplane 연동 가이드가 있습니다.

### 상태 관리

- **스냅샷:** `lstk snapshot save`로 현재 상태를 `.snapshot` 파일로 저장하고 `lstk snapshot load`로 되살립니다.
- **Cloud Pods:** `pod:<이름>`으로 저장하면 LocalStack 플랫폼에 버전 관리되는 상태가 올라갑니다. 팀원이나 CI가 같은 초기 상태를 공유할 때 씁니다.
- **초기화 훅:** `/etc/localstack/init/ready.d` 같은 디렉터리에 스크립트를 넣어 두면 컨테이너가 준비될 때 자동으로 리소스를 만듭니다.

### 그 밖에

- **IAM 정책 검사:** `ENFORCE_IAM=1`로 IAM 정책을 실제로 평가합니다(유료 기능).
- **웹 앱:** `app.localstack.cloud`의 리소스 브라우저로 로컬 인스턴스의 리소스를 GUI로 볼 수 있습니다. 문서에 따르면 브라우저가 로컬 컨테이너와 직접 통신하고 데이터를 LocalStack 외부 서버로 보내지 않습니다.
- **Lambda 핫 리로딩, 원격 디버깅, 확장(Extensions) 마켓플레이스** 등을 제공합니다.

## 설치와 시작

Docker가 먼저 실행 중이어야 합니다. `sudo`나 root로 설치·실행하지 말라는 것이 공식 권고입니다.

### 1) 계정과 토큰 준비

[app.localstack.cloud](https://app.localstack.cloud)에서 가입하면 Auth Token을 받을 수 있습니다. 비상업적 개인 용도라면 Hobby 플랜이면 됩니다.

### 2) 권장 방법: `lstk`

```bash
# 설치 (둘 중 하나)
brew install localstack/tap/lstk
npm install -g @localstack/lstk

lstk --version

# 시작: 첫 실행 시 브라우저 로그인이 열리고
# 토큰은 시스템 키체인에 저장됩니다.
lstk start

# 상태 / 로그 / 중지
lstk status
lstk logs --follow --tail 100
lstk stop
```

`lstk start`는 에뮬레이터가 준비된 뒤에 반환되므로 예전처럼 `localstack wait`를 따로 쓸 필요가 없습니다. 대화형 터미널에서 그냥 `lstk`만 입력하면 터미널 UI가 뜹니다.

AWS CLI가 LocalStack을 바라보도록 프로필을 만들어 두면 편합니다.

```bash
# ~/.aws/config, ~/.aws/credentials 에 localstack 프로필 생성
lstk setup aws

aws --profile localstack s3 ls
# 또는
lstk aws s3 ls
```

### 3) 기존 `localstack` CLI를 쓰던 경우

기존 CLI도 아직 동작하지만 deprecated 상태입니다. 주요 명령은 이렇게 바뀝니다.

| 기존 | lstk |
|---|---|
| `localstack start -d` | `lstk start` |
| `localstack logs -f` | `lstk logs --follow` |
| `localstack status docker` | `lstk status` |
| `awslocal s3 ls` | `lstk aws s3 ls` |
| `tflocal apply` | `lstk tf apply` |
| `cdklocal deploy` | `lstk cdk deploy` |
| `localstack pod save` | `lstk snapshot save pod:<이름>` |
| `localstack state reset` | `lstk reset` |

기존 CLI에서 토큰을 설정하려면 `localstack auth set-token <토큰>`을 씁니다. 단, 이 명령은 Docker나 Docker Compose로 띄울 때는 효과가 없으니 그때는 환경 변수를 씁니다.

## 실전 예제

### 예제 1: Docker Compose로 팀 공통 환경 만들기

팀이 같은 설정을 공유하려면 Compose 파일이 가장 무난합니다. 아래는 공식 문서의 구성에 초기화 훅을 더한 형태입니다.

```yaml
# docker-compose.yml
services:
  localstack:
    container_name: "${LOCALSTACK_DOCKER_NAME:-localstack-main}"
    image: localstack/localstack:2026.10   # 버전 고정 권장
    ports:
      - "127.0.0.1:4566:4566"            # Gateway
      - "127.0.0.1:4510-4559:4510-4559"  # 외부 서비스 포트
    environment:
      - LOCALSTACK_AUTH_TOKEN=${LOCALSTACK_AUTH_TOKEN:?}
      - DEBUG=${DEBUG:-0}
      - SERVICES=s3,sqs,lambda,dynamodb
    volumes:
      - "${LOCALSTACK_VOLUME_DIR:-./volume}:/var/lib/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"
      - "./init-aws.sh:/etc/localstack/init/ready.d/init-aws.sh"
```

`${LOCALSTACK_AUTH_TOKEN:?}`는 변수가 비어 있으면 Compose가 바로 에러를 내도록 하는 문법입니다. 실행 전에 `export LOCALSTACK_AUTH_TOKEN=...`을 해 둡니다.

초기화 스크립트는 공식 문서 예시를 그대로 따랐습니다(컨테이너 안에서 `lstk`를 설치해 `lstk aws`를 쓰는 방식). 실행 권한(`chmod +x init-aws.sh`)과 shebang이 꼭 있어야 합니다. Python 스크립트(`.py`)는 실행 권한 없이도 LocalStack의 Python 인터프리터로 실행됩니다.

```bash
#!/bin/bash
# init-aws.sh : LocalStack이 준비되면 실행
npm install -g @localstack/lstk
lstk setup aws
lstk aws s3 mb s3://my-bucket
lstk aws sqs create-queue --queue-name my-queue
```

```bash
docker compose up -d

# 초기화 훅이 끝났는지 확인
curl -s localhost:4566/_localstack/init/ready | jq .completed

# 서비스 상태 확인
curl -s localhost:4566/_localstack/health | jq
```

같은 Compose 안의 **다른 컨테이너(앱)**에서 접근할 때는 `localhost`가 아니라 서비스 이름을 써야 합니다. 같은 사용자 정의 네트워크에 두고 `http://localstack:4566`을 엔드포인트로 지정합니다. 이때 S3는 가상 호스트 주소가 해석되지 않을 수 있으니 SDK에서 path-style 옵션을 켜는 편이 안전합니다.

> 이미지 태그 참고: `latest`와 `stable`은 정식 릴리스를 따라가고, `YYYY.MM`은 월간 패치를 받으며, `YYYY.MM.patch`는 완전히 고정됩니다. CI와 팀 환경에서는 태그를 고정하세요.

### 예제 2: S3, SQS, Lambda를 CLI로 엮어 보기

먼저 AWS CLI 환경 변수를 잡습니다. `lstk aws`를 쓰면 이 단계는 생략해도 됩니다.

```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost.localstack.cloud:4566
```

**S3: 버킷 만들고 파일 올리기**

```bash
lstk aws s3 mb s3://demo-bucket
echo "hello" > hello.txt
lstk aws s3 cp hello.txt s3://demo-bucket/
lstk aws s3 ls s3://demo-bucket/
```

**SQS: 큐에 메시지 넣고 꺼내기**

```bash
lstk aws sqs create-queue --queue-name jobs
lstk aws sqs send-message \
  --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/jobs \
  --message-body '{"task":"resize","id":1}'
lstk aws sqs receive-message \
  --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/jobs
```

**Lambda: 함수 만들고 SQS에 연결하기**

```python
# handler.py
import json

def handler(event, context):
    for record in event.get("Records", []):
        print("got:", record["body"])
    return {"statusCode": 200, "body": json.dumps("ok")}
```

```bash
zip function.zip handler.py

lstk aws lambda create-function \
  --function-name sqs-worker \
  --runtime python3.12 \
  --handler handler.handler \
  --zip-file fileb://function.zip \
  --role arn:aws:iam::000000000000:role/lambda-role

# 직접 호출 (AWS CLI v2는 --cli-binary-format 필요)
lstk aws lambda invoke --function-name sqs-worker \
  --cli-binary-format raw-in-base64-out \
  --payload '{"Records":[{"body":"test"}]}' out.json

# SQS → Lambda 트리거 연결
lstk aws lambda create-event-source-mapping \
  --function-name sqs-worker \
  --event-source-arn arn:aws:sqs:us-east-1:000000000000:jobs \
  --batch-size 1
```

역할 ARN은 형식만 검사하고 실제 존재 여부는 확인하지 않습니다. 그래서 IAM 역할을 따로 만들지 않아도 함수가 생성됩니다. 실제 AWS에서는 당연히 안 되는 동작이니, 권한 문제까지 검증하려면 `ENFORCE_IAM`을 켜거나 실제 계정에서 한 번 더 확인해야 합니다.

**Python 코드에서 쓰기 (boto3)**

```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost.localstack.cloud:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)
print(s3.list_buckets()["Buckets"])
```

### 예제 3: Terraform과 CDK를 로컬에 배포하기

**Terraform (`lstk terraform`)**

`lstk terraform`은 AWS provider 엔드포인트를 LocalStack으로 돌리는 `localstack_providers_override.tf` 파일을 자동으로 만든 뒤 `terraform`을 실행합니다. 기존 Terraform 코드를 고치지 않아도 됩니다.

```bash
lstk terraform init
lstk terraform plan
lstk tf apply -auto-approve

# OpenTofu를 쓴다면
LSTK_TF_CMD=tofu lstk terraform apply
```

`--region`, `--account` 같은 lstk 전용 플래그는 Terraform 액션보다 **앞에** 와야 합니다.

래퍼 없이 직접 설정하고 싶다면 provider 블록에 엔드포인트를 적습니다.

```hcl
provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_metadata_api_check     = true

  endpoints {
    s3     = "http://s3.localhost.localstack.cloud:4566"
    sqs    = "http://localhost:4566"
    lambda = "http://localhost:4566"
  }
}
```

`s3.localhost.localstack.cloud`가 해석되지 않는 환경이면 S3 엔드포인트를 `http://localhost:4566`으로 바꾸고 `s3_use_path_style = true`를 추가합니다. terraform-provider-aws 5.x 이상은 `AWS_ENDPOINT_URL_S3` 같은 환경 변수로도 엔드포인트를 지정할 수 있어서, 같은 코드를 실제 AWS와 LocalStack에 번갈아 쓰기 좋습니다.

**AWS CDK (`lstk cdk`)**

AWS CDK CLI 2.177.0 이상이 필요합니다.

```bash
npm install -g aws-cdk

mkdir /tmp/cdk-demo && cd /tmp/cdk-demo
lstk cdk init sample-app --language=javascript
lstk cdk bootstrap
lstk cdk deploy

lstk aws sns list-topics
```

문서에 적힌 주의점이 두 가지 있습니다.

- 스택 업데이트는 실패하거나 상태가 꼬일 수 있어서, 삭제 후 재배포를 권장합니다.
- Lambda 코드나 S3 콘텐츠 같은 **CDK 에셋 배포는 유료 플랜이 필요**합니다. Hobby 플랜으로 CDK를 쓰려면 이 점을 먼저 확인하세요.

### 예제 4: GitHub Actions에서 통합 테스트 돌리기

`lstk` 도입 이후 공식 문서는 기존 `LocalStack/setup-localstack` 액션이 lstk와 함께 지원되지 않는다고 안내하고, `run` 단계에서 `lstk`를 직접 쓰는 방식을 보여 줍니다. `ubuntu-latest` 러너에는 Docker, Node.js, AWS CLI가 이미 있으므로 `lstk`만 설치하면 됩니다.

{% raw %}
```yaml
# .github/workflows/integration.yml
name: integration
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      LOCALSTACK_AUTH_TOKEN: ${{ secrets.LOCALSTACK_AUTH_TOKEN }}
    steps:
      - uses: actions/checkout@v4

      - name: Install lstk
        run: npm install -g @localstack/lstk

      - name: Configure AWS profile
        run: lstk setup aws

      - name: Start LocalStack
        run: lstk start
        env:
          LOCALSTACK_DEBUG: "1"   # 컨테이너에는 DEBUG=1로 전달

      - name: Deploy infra
        run: lstk tf init && lstk tf apply -auto-approve

      - name: Run tests
        run: make test
        env:
          AWS_PROFILE: localstack

      - name: Show LocalStack logs
        if: always()
        run: lstk logs --verbose | tee localstack.log
```
{% endraw %}

- 토큰은 개인 토큰이 아니라 워크스페이스 단위의 **CI Auth Token**을 저장소 시크릿으로 넣는 것이 권장됩니다.
- `LOCALSTACK_` 접두사가 붙은 환경 변수는 접두사를 떼고 컨테이너로 전달됩니다(`LOCALSTACK_DEBUG` → `DEBUG`).
- 이미지 태그는 커맨드라인 대신 저장소에 `.lstk/config.toml`을 커밋해서 고정하는 방식을 권장합니다.

```toml
# .lstk/config.toml
[[containers]]
type = "aws"
tag  = "2026.10"
port = "4566"
env  = ["ci"]

[env.ci]
SERVICES = "s3,sqs,lambda"
EAGER_SERVICE_LOADING = "1"
```

- Windows 러너에서는 Docker가 네이티브로 지원되지 않아 LocalStack을 돌릴 수 없습니다.
- arm64용 Lambda는 GitHub Actions에서 배포가 까다로울 수 있습니다. 아키텍처와 무관한 코드라면 `LAMBDA_IGNORE_ARCHITECTURE=1`을 검토하세요.

### 자주 쓰는 환경 변수

| 변수 | 기본값 | 용도 |
|---|---|---|
| `LOCALSTACK_AUTH_TOKEN` | - | 라이선스 활성화 토큰 |
| `DEBUG` | `0` | `1`이면 자세한 로그 |
| `LS_LOG` | - | `trace`, `debug` 등 로그 레벨. `DEBUG`보다 우선 |
| `SERVICES` | - | 로드할 서비스 목록(나머지는 비활성화) |
| `EAGER_SERVICE_LOADING` | `0` | `1`이면 시작 시 서비스 미리 로드 |
| `PERSISTENCE` | `0` | 상태 영속화(유료) |
| `ENFORCE_IAM` | `0` | IAM 정책 평가(유료) |
| `GATEWAY_LISTEN` | `0.0.0.0:4566,...` | 게이트웨이 바인드 주소 |
| `LOCALSTACK_HOST` | `localhost.localstack.cloud:4566` | 응답 URL에 들어갈 호스트 |
| `LAMBDA_DOCKER_NETWORK` | `bridge` | Lambda 컨테이너 네트워크 |
| `LAMBDA_KEEPALIVE_MS` | `600000` | 실행 환경 유지 시간(10분) |
| `LAMBDA_IGNORE_ARCHITECTURE` | `0` | x86_64/arm64 설정 무시 |
| `S3_SKIP_SIGNATURE_VALIDATION` | `1` | `0`이면 presigned URL 서명 검증 |
| `SQS_ENDPOINT_STRATEGY` | `standard` | 큐 URL 형식 |

모든 변수는 `LOCALSTACK_PERSISTENCE=1`처럼 `LOCALSTACK_` 접두사를 붙여도 동작합니다.

## 실무 팁 & 자주 겪는 문제

**시작이 안 될 때**

- `Could not reach the LocalStack licensing server`(종료 코드 55)는 라이선스 문제가 아니라 **네트워크 문제**입니다. 시작 시 `api.localstack.cloud`, `assets.localstack.cloud`에 접속할 수 있어야 하니 방화벽과 프록시 허용 목록을 확인하세요.
- 사내 프록시가 TLS를 가로채는(Zscaler, Netskope 등) 환경이면 회사 CA를 이미지에 넣거나 마운트한 뒤 `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS`를 지정합니다. `SSL_NO_VERIFY=1`은 최후의 수단입니다.
- `The credentials defined in your environment are invalid`가 나오면 `LOCALSTACK_AUTH_TOKEN` 값이 맞는지 확인합니다.
- `ports are not available: ... 443`은 다른 프로세스가 443 포트를 쓰고 있다는 뜻입니다. `lsof -i :443`으로 찾습니다.
- Apple Silicon에서 SIGILL(종료 코드 252)로 죽으면 `OPENSSL_armcap=0`(lstk는 `LOCALSTACK_OPENSSL_armcap=0 lstk start`)로 우회할 수 있습니다.

**자세한 로그와 진단**

```bash
# 상세 로그로 시작 (lstk는 LOCALSTACK_ 접두사로 전달)
LOCALSTACK_DEBUG=1 LOCALSTACK_LS_LOG=trace lstk start

# 컨테이너 로그 확인
docker logs <container-id>

# 진단 번들 (지원 요청 시 첨부)
curl -s localhost:4566/_localstack/diagnose | gzip -cf > diagnose.json.gz
```

**네트워크와 주소**

- 다른 컨테이너에서 접근이 안 되면 같은 사용자 정의 네트워크에 있는지, 엔드포인트를 서비스 이름으로 썼는지 확인합니다.
- 다른 PC에서 접근하려면 포트를 `0.0.0.0`에 열어야 하지만, 공식 문서는 보안상 권하지 않습니다.
- `certificate is valid for *.localhost.localstack.cloud` 같은 x509 오류는 `AWS_ENDPOINT_URL=http://localhost:4566`으로 피할 수 있습니다.

**운영 팁**

- `docker compose`를 내린 뒤 Lambda 컨테이너가 남는다면 `stop_grace_period`와 `SHUTDOWN_TIMEOUT`을 **둘 다** 늘려야 합니다(예: `180s`, `180`).
- Docker Hub 풀 횟수 제한에 걸리면 `docker login`을 하거나, AWS 계정이 있다면 `public.ecr.aws/localstack/localstack-pro:latest`를 씁니다.
- Windows에서 IO가 느리면 볼륨을 WSL 리눅스 파일 시스템이나 Docker named volume으로 옮깁니다.
- Git Bash에서는 `/`로 시작하는 인자가 경로로 변환되니 `MSYS_NO_PATHCONV=1`을 설정합니다.
- 테스트마다 상태를 깨끗하게 시작하려면 `lstk reset`을 쓰고, 반대로 복잡한 초기 데이터가 필요하면 스냅샷으로 저장해 두고 불러오는 편이 빠릅니다.
- 표준 이미지는 실행 중 의존성을 내려받을 수 있어서 완전 오프라인 환경에서는 제한이 있습니다. 완전 오프라인(air-gapped) 이미지는 Enterprise 플랜에서 제공합니다.

## 비슷한 도구와 비교

| 항목 | LocalStack | moto | AWS SAM CLI (`sam local`) | 실제 AWS 개발 계정 |
|---|---|---|---|---|
| 형태 | Docker 컨테이너 에뮬레이터 | Python 라이브러리(서버 모드도 있음) | Lambda/API Gateway 로컬 실행 도구 | 진짜 클라우드 |
| 범위 | 여러 서비스를 하나의 엔드포인트로 | 많은 서비스의 API를 모킹 | 주로 Lambda 함수 실행 | 모든 서비스 |
| 언어 제약 | 없음(HTTP API) | 테스트 코드에 쓰기는 Python 중심 | 없음 | 없음 |
| IaC 연동 | Terraform, CDK, SAM 등 | 제한적 | SAM/CloudFormation 템플릿 | 전부 |
| 충실도 | 높은 편, 서비스별 차이 | API 응답 수준 모킹 | Lambda 런타임은 실제와 유사 | 100% |
| 비용 | 비상업 무료, 상업 유료 | 무료 오픈소스 | 무료 | 사용량 과금 |
| 오프라인 | 제한적(라이선스 확인 필요) | 가능 | 가능(이미지 받은 뒤) | 불가 |

- **moto**는 Python 단위 테스트에서 boto3 호출을 가로채는 용도로 가볍고 빠릅니다. 서비스 간 연동(예: SQS가 Lambda를 실제로 호출)까지 보려면 LocalStack 쪽이 맞습니다.
- **SAM CLI**는 Lambda 함수 하나를 로컬에서 돌려 보는 데 특화되어 있습니다. 함수가 호출하는 S3, DynamoDB까지 로컬로 두려면 LocalStack과 함께 쓰는 경우가 많습니다.
- **실제 AWS 개발 계정**은 충실도가 완벽하지만 피드백 속도와 비용, 계정 관리 부담이 있습니다. 최종 검증 단계로는 여전히 필요합니다.

## 장점과 한계

**장점**

- 엔드포인트만 바꾸면 기존 코드와 IaC를 거의 그대로 쓸 수 있습니다.
- 피드백이 빨라지고, 테스트 비용이 줄며, CI가 외부 클라우드 상태에 덜 흔들립니다.
- 스냅샷, 초기화 훅으로 재현 가능한 테스트 환경을 만들기 쉽습니다.
- `lstk` 하나로 시작, 인증, 도구 연동, 스냅샷을 처리할 수 있어 설치가 단순해졌습니다.

**한계**

- **오픈소스 저장소는 보관 상태**입니다. 이 저장소의 코드는 v4.14.0에서 멈췄고, 최신 기능과 보안 수정은 토큰이 필요한 통합 이미지로만 나옵니다. 공식 블로그는 커뮤니티 사용자에게 "인증 방식으로 옮기거나, 예전 태그에 고정하고 그 부담을 감수"하는 두 가지 길을 제시합니다.
- **무료 범위가 좁아졌습니다.** Hobby 플랜은 무료지만 상업적 사용이 금지되어 있습니다. 회사 업무라면 Base(라이선스당 월 39달러, 연간 결제 기준)부터 검토해야 합니다. 가격은 바뀔 수 있으니 공식 페이지를 확인하세요.
- **기능별 유료 구분:** 영속성, IAM 정책 강제, Lambda Layers, CDK 에셋 배포 등은 유료 플랜 기능입니다.
- **에뮬레이션 충실도:** 실제 AWS와 100% 같지 않습니다. 예를 들어 Lambda 응답 스트리밍은 지원하지 않고, IAM 역할은 존재 여부를 확인하지 않으며, 서비스별 미구현 API가 있습니다. 로컬 통과가 실제 환경 통과를 보장하지는 않습니다.
- **인터넷 의존:** 시작할 때 라이선스 서버 접속이 필요해서 폐쇄망에서는 Enterprise 오프라인 이미지가 아니면 쓰기 어렵습니다.
- **리소스 사용:** Lambda마다 컨테이너가 뜨므로 노트북 메모리와 CPU를 꽤 씁니다. `SERVICES`로 필요한 서비스만 올리는 습관이 도움이 됩니다.

## 이런 분께 추천 / 이런 경우엔 다른 도구

**추천**

- 서버리스(Lambda + SQS/SNS + S3 + DynamoDB) 구조를 로컬에서 빠르게 돌려 보고 싶은 개발자
- Terraform/CDK 코드를 실제 계정에 적용하기 전에 기본 동작을 확인하고 싶은 분
- CI에서 실제 AWS 없이 통합 테스트를 안정적으로 돌리고 싶은 팀(상업적 용도라면 유료 플랜 전제)
- 개인 학습이나 사이드 프로젝트로 AWS를 부담 없이 익히고 싶은 분(Hobby 플랜)

**다른 도구가 나은 경우**

- Python 단위 테스트에서 boto3 호출만 가볍게 막고 싶다면 **moto**가 더 간단합니다.
- Lambda 함수 하나만 로컬에서 디버깅하면 된다면 **SAM CLI**로 충분합니다.
- 무료 오픈소스만 써야 하는 회사 정책이 있다면, 보관된 v4.x 이미지에 고정하는 대신 moto나 서비스별 로컬 대체재(예: DynamoDB Local, MinIO)를 조합하는 방안을 검토해 보세요.
- 결제, 보안, 네트워크 정책처럼 실제 동작이 중요한 부분은 결국 **실제 AWS 개발 계정**에서 검증해야 합니다.

## 참고 링크

- [GitHub 저장소 (보관됨)](https://github.com/localstack/localstack)
- [설치 가이드](https://docs.localstack.cloud/aws/getting-started/installation/)
- [Auth Token](https://docs.localstack.cloud/aws/getting-started/auth-token/)
- [FAQ](https://docs.localstack.cloud/aws/getting-started/faq/)
- [lstk 개요](https://docs.localstack.cloud/aws/developer-tools/running-localstack/lstk/)
- [lstk 마이그레이션](https://docs.localstack.cloud/aws/developer-tools/running-localstack/lstk/migration/)
- [lstk 설정(config.toml)](https://docs.localstack.cloud/aws/developer-tools/running-localstack/lstk/configuration/)
- [lstk 스냅샷](https://docs.localstack.cloud/aws/developer-tools/running-localstack/lstk/snapshots/)
- [AWS CLI 연동](https://docs.localstack.cloud/aws/connecting/aws-cli/)
- [Terraform 연동](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)
- [AWS CDK 연동](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/aws-cdk/)
- [Deprecated 래퍼 스크립트 (awslocal, tflocal 등)](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/deprecated-wrapper-scripts/)
- [GitHub Actions](https://docs.localstack.cloud/aws/ci-pipelines/github-actions/)
- [설정 레퍼런스](https://docs.localstack.cloud/aws/capabilities/config/configuration/)
- [초기화 훅](https://docs.localstack.cloud/aws/customization/advanced/initialization-hooks/)
- [엔드포인트 접근(네트워킹)](https://docs.localstack.cloud/aws/customization/networking/accessing-endpoint-url/)
- [Lambda](https://docs.localstack.cloud/aws/services/lambda/)
- [요금제](https://www.localstack.cloud/pricing)
- [단일 이미지 전환 안내 (블로그)](https://blog.localstack.cloud/localstack-single-image-next-steps/)

[← 오픈소스 소개 목록]({{ "/opensource.html" | relative_url }}) · [Home]({{ "/" | relative_url }})
