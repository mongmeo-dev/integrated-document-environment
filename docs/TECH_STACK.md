# Integrated Document Environment 기술 스택

- 상태: Phase1 기술 스택 결정
- 기준 문서: [`tasks/phase1_prd/PRD.md`](tasks/phase1_prd/PRD.md)
- 작성일: 2026-08-19

## 1. 설계 방향

Phase1은 FastAPI 기반 모듈러 모놀리스와 비동기 문서 처리 worker로 구현한다. API와 worker는 도메인 규칙을 공유하되 실행 process와 Docker image는 분리한다. PostgreSQL은 업무 데이터와 감사 이력의 기준 저장소이며, 원본과 산출 파일은 object storage에 저장한다.

문서의 정본은 진입점 `.tex`, 자산, 참고문헌, 스타일 파일로 이루어진 LaTeX 프로젝트 번들이다. Web에서 이 정본을 편집하고 PDF 미리보기를 검토한다. 컴파일 PDF는 정본으로부터 재현되는 파생 검토·승인 산출물이며 편집 원본이 아니다.

DOCX는 불변의 import-only 입력이다. DOCX를 LaTeX 프로젝트로 자동 일방향 변환한 뒤 변환 차이를 사람의 사유 있는 명시적 검토로 해결한다. 자동 변환 또는 AI 판단만으로 변환을 수락하지 않는다. PDF는 보존·참조·분석 입력으로 지원하지만 주 편집 경로나 PDF→LaTeX 변환 경로는 제공하지 않는다. 외부 편집은 더 이상 주 경로가 아니다.

마이크로서비스, 범용 BPM engine, Elasticsearch와 graph database는 Phase1에 도입하지 않는다.

## 2. 기술 스택

| 영역 | 선정 기술 |
|---|---|
| Web | Next.js standalone server, React, TypeScript |
| UI | CSS Modules |
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
| DOCX→LaTeX 변환 | Pandoc 3.10.2 |
| LaTeX 컴파일 | Tectonic 0.17.0 |
| PDF 참조·분석 | PyMuPDF, pikepdf, qpdf |
| 시각 비교 | OpenCV |
| 스캔 PDF OCR | CLOVA OCR |
| Python 의존성 관리 | Poetry |
| Web package manager | pnpm |
| Python lint 및 format | Ruff |
| Frontend lint 및 format | Biome |
| 테스트 | pytest, Testcontainers, Playwright |

OpenAI 호출에는 공식 Python SDK를 사용한다. LangChain이나 LlamaIndex 같은 범용 AI orchestration framework는 도입하지 않는다. 모델 ID와 prompt version은 실행 환경 설정으로 관리하고 생성 결과에 기록한다.

Pandoc은 정확히 `3.10.2`로 고정하고 DOCX를 LaTeX 프로젝트로 가져오는 단방향 변환기에만 사용한다. 변환 결과의 정본성은 사람의 변환 충실도 검토·확정 뒤에만 성립한다. Tectonic은 정확히 `0.17.0`, 한글 font는 Noto Sans CJK `20240730`으로 고정한다. production image build에서 compiler resource cache를 준비하고 runtime에는 `--untrusted --only-cached`로 실행하여 네트워크 없이 동일 번들과 고정 도구 버전으로 동일 PDF를 재현한다.

## 3. 서버 구조

FastAPI application은 다음 의존 방향을 유지한다.

```text
router -> application service -> domain rule -> repository -> PostgreSQL
```

라우터가 ORM 객체를 직접 변경하거나 승인 상태를 전이해서는 안 된다. 승인, 후보 처리, 변환 검토, 컴파일 상태, 완료 gate는 application service와 domain rule에서 처리한다. 승인 처리에는 PostgreSQL transaction과 row lock을 사용한다. 완료된 승인 단계와 감사 이력은 수정하지 않고 후속 event를 append한다. Redis는 queue와 일시적 cache에만 사용하며 승인 상태나 문서 상태의 source of truth로 사용하지 않는다.

### 3.1 Web API client

FastAPI OpenAPI specification을 API 계약의 단일 기준으로 사용한다. Web의 request/response type과 Axios client는 OpenAPI Generator의 `typescript-axios` generator로 생성한다.

```text
FastAPI schema -> openapi.json -> OpenAPI Generator -> generated API client -> React Query hooks -> page/component
```

Web component는 codegen 산출물이나 Axios를 직접 호출하지 않는다. 모든 server state 접근은 codegen client를 감싼 React Query hook을 통해 수행한다. 생성 type과 API 함수는 직접 수정하지 않으며, wrapper에서 query key, cache policy, invalidation과 화면용 오류 변환을 관리한다.

## 4. 문서 처리와 보존

원본 DOCX, 입력 PDF, LaTeX 프로젝트 번들, 컴파일 PDF, 변환·컴파일·검토 결과는 object storage의 별도 object로 보존한다. PostgreSQL에는 object key, SHA-256, 크기, MIME type, 등록 사용자, 등록 시각, 도구 버전과 문서 version 관계를 기록한다.

- 입력 원본과 확정된 번들은 덮어쓰거나 변경하지 않는다.
- LaTeX 프로젝트는 진입점 `.tex`와 참조하는 자산·참고문헌·스타일 파일을 하나의 versioned bundle로 취급한다.
- DOCX 가져오기는 Pandoc으로 한 번만 수행하며 DOCX로 되돌려 쓰거나 PDF를 편집 원본으로 역변환하지 않는다.
- DOCX 변환 revision 검토, 컴파일 오류·경고와 사용자 결정에는 사용자, 시각, 사유 및 관련 version을 영구 감사 이력으로 남긴다.
- AI가 생성한 수정안·관계·영향·근거 후보는 사용자가 확정하기 전까지 advisory 상태다.
- 문서별 승인 단계·담당자·순서는 구성 가능하며, DOCX 기반 최신 revision의 검토 대기·반려, 컴파일 문제와 미처리 후보는 완료와 산출을 차단한다.

### 4.1 DOCX 변환 충실도 검토

Pandoc 변환 직후 원본 DOCX 다운로드, 생성 LaTeX 번들과 같은 revision의 컴파일 PDF를 한 화면의 변환 충실도 검토 자료로 제시한다. 검토자는 원본과 생성 결과를 대조한 뒤 해당 revision 전체를 수락 또는 반려하고 구체적인 사유를 기록한다. 수정이 필요하면 Web 정본 편집으로 새 revision을 생성하며 DOCX 기반 새 revision은 다시 검토 대기가 된다. 최신 revision이 검토 대기·반려이거나 사유 없는 결정이면 완료와 승인 PDF 산출의 조건을 충족하지 못한다.

이는 DOCX binary의 절대 동일성을 보장하는 요구가 아니다. 기준은 LaTeX 정본의 재현 가능성, 컴파일 PDF의 검토 가능성, 그리고 DOCX→LaTeX 변환 충실도에 대한 인간 검토다.

### 4.2 LaTeX 편집과 컴파일

Web은 LaTeX 소스 편집기와 같은 번들의 PDF 미리보기를 기본 작업 화면에 함께 제공한다. 편집 저장은 새 정본 version을 만들고 Tectonic worker가 해당 번들을 컴파일한다. PDF 미리보기에는 컴파일 대상 version, Tectonic `0.17.0`, 실행 결과, 오류·경고와 생성 시각을 표시한다.

Tectonic worker는 다음 제약을 적용한다.

- non-root user, read-only root filesystem, 작업별 임시 directory
- CPU, memory, 저장 공간 및 실행 시간 제한
- 기본 outbound network 차단과 허용된 번들 파일만 mount
- shell escape 및 임의 host 파일 접근 금지
- 컴파일러 image, Tectonic version, font·패키지 입력의 version 고정
- 실패 log와 source version을 보존하고 PDF를 승인 산출로 승격하지 않음

## 5. PDF 참조·분석

PDF는 텍스트 PDF와 스캔 PDF 모두 원본을 보존하고 텍스트 추출, OCR, 관계·영향·근거 분석의 입력으로 받을 수 있다. PDF는 LaTeX 정본을 대신하거나 in-web 편집·왕복 변환 대상이 아니다. PDF 분석 결과도 후보이며 사람의 검토·확정이 필요하다.

## 6. AI 처리

OpenAI는 수정안, 문서 관계, 변경 영향과 제품·검증 근거의 후보만 생성한다. 승인, 변환 차이 수락, 컴파일 성공 판정, 완료 gate와 권한 판정에는 AI 출력을 직접 사용하지 않는다. AI worker는 Structured Outputs와 Pydantic schema를 사용하며 입력 문서·version, 근거 위치, 모델 ID, prompt version, 생성 시각 및 사용자 결정을 기록한다.

## 7. 인증과 접근 통제

서비스는 내부망에만 배포한다. 관리자가 사내 사용자 계정을 생성하며 self-signup은 제공하지 않는다. 비밀번호는 Argon2id로 hashing하고 인증에는 HttpOnly, Secure, SameSite cookie와 server-side opaque session을 사용한다. 승인, 변환 검토와 흐름 변경 시 인증된 사용자 ID를 감사 이력에 기록한다.

## 8. Dockerizing

Web은 Next.js `standalone` output으로 실행한다. 정적 export를 요구하는 기능은 사용하지 않으며 Docker image는 생성된 `server.js`를 실행한다. 다음 image를 제공한다.

```text
web
api
worker-document
worker-latex
worker-ai
worker-ocr
```

각 image는 version이 고정된 dependency와 reproducible build, multi-stage build, non-root runtime user, 최소 runtime dependency, health check, 환경 변수 또는 mounted secret 주입을 따른다. 설정과 secret은 image에 포함하지 않는다.

## 9. 개발 품질 기준

Python 의존성은 Poetry lock file, Web 의존성은 pnpm lock file로 고정한다. CI에서는 OpenAPI specification으로 client를 재생성해 차이가 있으면 실패시킨다. Tectonic compiler image와 Pandoc version도 release metadata와 함께 고정하여 문서 번들과 컴파일 결과를 재현 가능하게 한다.

## 10. Phase1에서 도입하지 않는 항목

- IDE 내부 DOCX 또는 PDF 직접 편집기
- DOCX round-trip 또는 PDF→LaTeX 변환
- DOCX binary-format의 절대 동일성 보장
- 외부 편집 결과 재수집을 주 문서 편집 경로로 사용하는 방식
- AI 또는 시스템에 의한 변환 차이·승인의 무인 자동 확정
- Keycloak, 필수 OIDC 연동, LangChain, LlamaIndex, Elasticsearch, Neo4j, Temporal
