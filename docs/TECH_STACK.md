# Integrated Document Environment 기술 스택

- 상태: Phase1 기술 스택 결정
- 기준 문서: [`../PRD.md`](../PRD.md)
- 작성일: 2026-08-15

## 1. 설계 방향

Phase1은 FastAPI 기반 모듈러 모놀리스와 비동기 문서 처리 worker로 구현한다. API와 worker는 도메인 규칙을 공유하되 실행 process와 Docker image는 분리한다.

마이크로서비스, 범용 BPM engine, Elasticsearch와 graph database는 Phase1에 도입하지 않는다. PostgreSQL을 업무 데이터, 감사 이력, 검색과 문서 관계의 기준 저장소로 사용한다.

## 2. 기술 스택

| 영역 | 선정 기술 |
|---|---|
| Web | Next.js static export, React, TypeScript |
| UI | Chakra UI |
| Server state | TanStack Query |
| API client 생성 | OpenAPI Generator의 `typescript-axios` |
| API | Python 3.14, FastAPI, Pydantic |
| ORM 및 transaction | SQLAlchemy 2.x, psycopg 3 |
| DB migration | Alembic |
| 비동기 처리 | Celery |
| 업무 데이터 | PostgreSQL |
| 작업 queue 및 cache | Redis |
| 전문 검색 | PostgreSQL Full Text Search |
| 벡터 검색 | pgvector |
| 파일 저장 | Naver Cloud Object Storage |
| AI | OpenAI Responses API, Structured Outputs, Embeddings API |
| DOCX 분석 | OOXML package 직접 분석, lxml, python-docx 보조 사용 |
| DOCX rendering | version과 font를 고정한 LibreOffice headless |
| PDF 처리 | PyMuPDF, pikepdf, qpdf |
| 시각 비교 | OpenCV |
| 스캔 PDF OCR | CLOVA OCR |
| Python 의존성 관리 | Poetry |
| Web package manager | pnpm |
| Python lint 및 format | Ruff |
| Frontend lint 및 format | Biome |
| 테스트 | pytest, Testcontainers, Playwright |

OpenAI 호출에는 공식 Python SDK를 사용한다. LangChain이나 LlamaIndex 같은 범용 AI orchestration framework는 도입하지 않는다. 생성 모델과 embedding 모델의 정확한 ID는 실행 환경의 설정으로 관리하고, 각 생성 결과에 실제 모델 ID와 prompt version을 기록한다.

## 3. 서버 구조

FastAPI application은 다음 의존 방향을 유지한다.

```text
router -> application service -> domain rule -> repository -> PostgreSQL
```

라우터가 ORM 객체를 직접 변경하거나 승인 상태를 전이해서는 안 된다. 승인, 후보 처리, 오래됨 상태와 완료 gate는 application service와 domain rule에서 처리한다.

승인 처리에는 PostgreSQL transaction과 row lock을 사용한다. 완료된 승인 단계와 감사 이력은 수정하지 않고 후속 event를 append한다. Redis는 queue와 일시적 cache에만 사용하며 승인 상태나 문서 상태의 source of truth로 사용하지 않는다.

### 3.1 Web API client

FastAPI가 생성하는 OpenAPI specification을 API 계약의 단일 기준으로 사용한다. Web의 request/response type과 Axios client는 OpenAPI Generator의 `typescript-axios` generator로 생성한다.

```text
FastAPI schema
  -> openapi.json
  -> OpenAPI Generator (typescript-axios)
  -> generated API client
  -> React Query hooks
  -> page/component
```

Web page와 component는 codegen 산출물이나 Axios를 직접 호출해서는 안 된다. 모든 server state 접근은 codegen client를 감싼 React Query query 또는 mutation hook을 통해 수행한다.

- 생성된 type과 API 함수는 수작업으로 수정하지 않는다.
- React Query wrapper에서 query key, cache policy, invalidation과 화면용 오류 변환을 관리한다.
- domain별 query key factory를 두어 같은 resource에 일관된 key를 사용한다.
- component에는 API DTO를 그대로 확산하지 않고 필요한 경우 wrapper 경계에서 화면 model로 변환한다.
- codegen 산출물은 수작업 source와 구분하여 Biome lint/format에서는 제외하고 TypeScript type check에는 포함한다.
- CI에서는 OpenAPI specification으로 client를 다시 생성한 뒤 repository 상태가 달라지면 실패시켜 API와 Web 계약 불일치를 차단한다.

## 4. 인증과 접근 통제

서비스는 내부망에만 배포한다. Phase1에는 Keycloak이나 OIDC를 도입하지 않는다.

내부망 접근만으로는 승인 사용자와 변경자를 식별할 수 없으므로 application 자체 계정과 session 인증을 사용한다.

- 관리자가 사내 사용자 계정을 생성하며 self-signup은 제공하지 않는다.
- 비밀번호는 Argon2id로 hashing한다.
- 인증에는 HttpOnly, Secure, SameSite cookie와 server-side opaque session을 사용한다.
- session의 기준 데이터와 사용자 상태는 PostgreSQL에 저장한다.
- 승인과 흐름 변경 시 인증된 사용자 ID를 감사 이력에 기록한다.
- 문서 단계 승인은 현재 단계의 지정 담당자에게만 허용한다.

추후 외부 identity 연동이 필수가 되면 NCP의 OIDC 사용 여부를 별도로 결정한다. Phase1에는 범용 identity provider abstraction이나 OIDC 의존성을 미리 추가하지 않는다.

## 5. 파일 저장과 무결성

DOCX, PDF, 이미지와 기타 근거 파일의 binary는 PostgreSQL이 아닌 Naver Cloud Object Storage에 저장한다. PostgreSQL에는 object key, SHA-256, 크기, MIME type, 등록 사용자, 등록 시각과 문서 version 관계를 기록한다.

- 원본 object는 덮어쓰거나 변경하지 않는다.
- 외부 편집 결과와 승인 산출물은 매번 별도 object로 생성한다.
- 등록 시 계산한 SHA-256으로 이후 무결성을 검증한다.
- Redis에는 원본 문서나 승인 산출물을 저장하지 않는다.

## 6. 문서 검사

### 6.1 DOCX

DOCX 서식 검사는 OOXML 구조 검사와 시각 비교를 모두 수행한다.

- style, run property, font, 크기와 색상
- paragraph 간격과 line spacing
- table, cell, section과 margin
- header, footer, image와 relationship
- 고정된 LibreOffice 및 font 환경에서 생성한 page rendering

LibreOffice rendering만으로 서식 동일성을 판정하지 않는다. OOXML 구조 검사만으로도 완료 처리하지 않는다.

### 6.2 PDF

PDF는 객체 수준 검사와 동일 rendering engine으로 생성한 page image 비교를 모두 수행한다.

- page 크기와 회전
- font와 색상
- text 및 image object
- annotation과 embedded resource
- page별 image difference

자동 검사 결과와 별도로 사용자의 시각 비교 완료 기록이 있어야 한다. 미해결 차이가 있으면 단계 승인, 최종 완료와 승인 산출을 차단한다.

### 6.3 실행 격리

업로드된 문서는 신뢰할 수 없는 입력으로 취급한다. 문서 처리 container에는 다음 제한을 적용한다.

- non-root user
- read-only root filesystem
- 임시 저장 공간 제한
- CPU, memory와 실행 시간 제한
- 기본 outbound network 차단
- 압축 해제 크기 및 ZIP bomb 검사
- 암호화 또는 손상 파일의 사전 거부

## 7. AI 처리

OpenAI는 수정안, 문서 관계, 변경 영향과 제품·검증 근거의 후보만 생성한다. 승인, 오래됨 상태, 완료 gate와 권한 판정에는 AI 출력을 직접 사용하지 않는다.

AI worker는 자유 형식 응답 대신 Structured Outputs와 Pydantic schema를 사용한다. 후보에는 최소한 다음 정보를 저장한다.

- 입력 문서와 version
- 관련 문서 및 위치
- 후보 내용과 제안 이유
- 원문 근거 위치
- OpenAI model ID
- prompt version
- 생성 시각
- 사용자 확정 또는 거절 결과
- 요청 ID, token 사용량과 오류 기록

GMP 문서의 전체 내용을 불필요하게 전송하지 않고 처리에 필요한 chunk 또는 page만 전송한다. API request 본문, 문서 원문과 model 응답 원문은 일반 application log에 기록하지 않는다. OpenAI API key는 AI worker에만 제공한다.

## 8. Dockerizing

Web은 Next.js static export로 생성한 `out/` 디렉터리를 Naver Cloud Object Storage에 업로드하고 CDN으로 제공할 수 있어야 한다. Web에는 Next.js server runtime을 요구하는 기능을 사용하지 않는다. `NEXT_PUBLIC_API_BASE_URL`은 static export build 시점에 주입하며 환경별 산출물을 별도로 생성한다.

배포 platform과 배포 도구는 이 문서에서 고정하지 않는다. 다음 Docker image를 제공한다.

```text
web-static
api
worker-document
worker-ai
worker-ocr
```

각 image는 다음 원칙을 따른다.

- version이 고정된 dependency와 reproducible build
- multi-stage build
- non-root runtime user
- application source와 runtime dependency만 포함
- health check endpoint 제공
- 설정과 secret은 image에 포함하지 않고 환경 변수 또는 mounted secret으로 주입
- 동일 source revision으로 생성된 image에 동일 release identifier 부여

## 9. 개발 품질 기준

Python 의존성은 Poetry의 `pyproject.toml`과 lock file로 관리한다. 운영 image는 lock file에 고정된 의존성만 설치한다.

Ruff를 Python lint와 formatter의 단일 도구로 사용한다.

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest
```

자동 수정은 개발 과정에서 다음 명령으로 수행한다.

```bash
poetry run ruff check --fix .
poetry run ruff format .
```

Frontend의 lint와 format에는 Biome만 사용한다.

```bash
pnpm exec biome check .
pnpm exec biome format --write .
```

Web 의존성은 pnpm의 `package.json`과 `pnpm-lock.yaml`로 관리한다. 개발, CI와 Docker build에서 같은 pnpm version을 사용하며 운영 image는 `pnpm install --frozen-lockfile`로 고정된 의존성만 설치한다.

Biome는 TypeScript type checker가 아니므로 type check는 TypeScript compiler로 수행한다. Frontend는 Biome 검사, type check와 test를 모두 통과해야 한다.

API 계약 검증에는 다음 과정이 포함되어야 한다.

```text
OpenAPI schema 생성
-> typescript-axios client 재생성
-> 변경 여부 검사
-> TypeScript type check
-> React Query wrapper test
```

API 계약과 client type을 frontend에서 수작업으로 중복 정의하지 않는다.

## 10. Phase1에서 도입하지 않는 항목

- Django
- Keycloak
- 필수 OIDC 연동
- LangChain 또는 LlamaIndex
- Elasticsearch
- Neo4j 또는 별도 graph database
- Temporal 또는 범용 BPM engine
- 배포 platform 및 배포 도구의 신규 선정
- IDE 내부 DOCX/PDF 편집기
