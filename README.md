# Integrated Document Environment

뉴다이브 임직원이 소프트웨어 의료기기 개발 과정의 GMP 문서를 검토하고 변경 영향, 제품·검증 근거와 승인 이력을 관리하기 위한 내부 문서 작업 환경입니다.

이 시스템은 LaTeX 프로젝트 번들(진입점 `.tex`, 자산, 참고문헌, 스타일 파일)을 정본으로 편집하고 컴파일된 PDF를 검토·승인하는 문서 작업 환경입니다. Web에서 LaTeX 원본을 편집하고 PDF 미리보기를 검토하며, 관련 문서·근거 후보와 승인 이력은 사람이 최종 확정합니다.

> 현재 저장소에는 Phase1 수직 슬라이스와 개발 환경이 포함됩니다. 전체 제품
> 요구사항은 [PRD](docs/tasks/phase1_prd/PRD.md), 기술 결정은
> [기술 스택 문서](docs/TECH_STACK.md)를 참고하십시오.

## 주요 원칙

- 등록된 원본 파일은 변경하거나 덮어쓰지 않습니다.
- LaTeX 프로젝트 번들은 편집 가능한 정본이고 컴파일 PDF는 재현 가능한 파생 검토·승인 산출물입니다.
- DOCX는 불변 원본으로 보존한 뒤 LaTeX 프로젝트로 한 번만 자동 변환합니다. 각 DOCX 기반 revision은 원본·LaTeX 정본·컴파일 PDF를 대조한 사람의 사유 기반 수락 없이는 확정되지 않습니다.
- PDF는 참조·분석 입력으로 보존하며 주 편집 원본이나 왕복 편집 형식으로 사용하지 않습니다.
- 수정안, 문서 관계, 영향과 근거는 사용자가 확정하기 전까지 후보입니다.
- DOCX 기반 최신 revision의 검토 대기·반려, 컴파일 오류 또는 미처리 후보가 있으면 완료와 산출을 차단합니다.
- AI는 후보 생성에만 사용하며 승인과 완료 여부를 결정하지 않습니다.
- 서비스는 뉴다이브 내부망에서만 제공합니다.

## 기술 구성

| 영역 | 기술 |
|---|---|
| API | Python 3.14, FastAPI, Pydantic, SQLAlchemy, Alembic |
| 비동기 처리 | Celery, Redis |
| 데이터베이스 | PostgreSQL, pgvector |
| Web | Next.js standalone server, React, TypeScript |
| UI 및 상태 | CSS Modules, TanStack Query |
| API client | OpenAPI Generator `typescript-axios` |
| AI | OpenAI Responses API, Structured Outputs |
| DOCX 변환 | Pandoc 3.10.2 |
| LaTeX 컴파일 | Tectonic 0.17.0 |
| 파일 저장 | Naver Cloud Object Storage |
| Python 도구 | Poetry, Ruff, pytest |
| Web 도구 | pnpm, Biome, TypeScript compiler |

## 디렉터리

```text
apps/
  api/                 FastAPI 도메인 API, migration, 통합 테스트
  web/                 Next.js LaTeX 편집·PDF 미리보기 문서 워크벤치와 생성 client
docs/
  TECH_STACK.md        기술 스택과 설계 결정
  tasks/phase1_prd/    Phase1 요구사항과 원천 작업 문서
design-system/
  integrated-document-environment/  Web UI 디자인 시스템과 화면별 규칙
fixture/
  sample-docs/         등록·검증 통합 테스트용 실제 DOCX 문서
```

## 개발 환경

### 요구 사항

- [mise](https://mise.jdx.dev/)
- Docker
- Pandoc 3.10.2
- Tectonic 0.17.0
- Noto Sans CJK 20240730

`mise.toml`에서 다음 도구 버전을 관리합니다.

- Node.js 24
- Python 3.14
- Poetry 2
- pnpm 11.20.0 (`package.json`의 `packageManager`로 고정)

### 설치

```bash
mise install
mise exec -- poetry -C apps/api install
corepack enable
pnpm --dir apps/web install --frozen-lockfile
```

루트의 `.env.example`을 참고하여 `.env`를 구성합니다. 애플리케이션 설정에는 다음 변수를 사용할 수 있습니다.

```dotenv
OPENAI_API_KEY=
IDE_CORS_ORIGINS=["http://localhost:3000"]
IDE_TECTONIC_ONLY_CACHED=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`NEXT_PUBLIC_API_BASE_URL`은 Web build 시 산출물에 포함되므로 환경별로 별도 build해야 합니다. 비밀값을 `NEXT_PUBLIC_*` 변수에 넣어서는 안 됩니다.

API production image는 Pandoc, Tectonic, Noto Sans CJK 및 컴파일 resource cache를 image build 시 고정하고 `IDE_TECTONIC_ONLY_CACHED=true`로 실행합니다. 로컬 직접 실행은 기본값 `false`를 사용해 필요한 Tectonic resource를 최초 컴파일 때 받을 수 있습니다.

### 로컬 인프라

API와 Web을 제외한 PostgreSQL 및 Redis는 Docker Compose로 실행합니다. PostgreSQL image에는 pgvector가 포함되어 있습니다.

```bash
docker compose up -d
docker compose ps
```

기본 연결 정보는 다음과 같습니다.

- PostgreSQL: `postgresql://ide:ide@localhost:5432/ide`
- Redis: `redis://localhost:6379/0`

데이터는 Docker named volume에 보존됩니다. 컨테이너만 종료하려면 `docker compose down`, 로컬 데이터를 함께 제거하려면 `docker compose down --volumes`를 실행합니다.

포트와 PostgreSQL 계정은 `.env`의 `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, `REDIS_PORT`로 변경할 수 있습니다.

## 로컬 실행

Web과 API 개발 서버를 함께 실행합니다.

```bash
mise run dev
```

각 개발 서버만 실행할 수도 있습니다.

```bash
mise run dev:web
mise run dev:api
```

기본 주소는 다음과 같습니다.

- Web: <http://localhost:3000>
- API: <http://localhost:8000>
- API 문서: <http://localhost:8000/docs>
- 상태 확인: <http://localhost:8000/api/v1/health>

### Web 작업 흐름

Web은 문서를 먼저 선택한 뒤 모든 검토 단계에서 같은 문서 맥락을 유지합니다.

- `/`: 현재 사용자의 문서 작업 큐
- `/documents/`: 문서 검색, 상태 필터와 등록
- `/documents/{documentId}/`: 문서 상태와 다음 작업
- `/documents/{documentId}/validation/`: 원본 입력 검증과 지원 범위 안내
- `/documents/{documentId}/import-review/`: DOCX 원본·LaTeX 정본·컴파일 PDF 대조와 사람의 사유 기반 결정
- `/documents/{documentId}/changes/`: 변경 요청과 수정안 결정
- `/documents/{documentId}/workbench/`: LaTeX 프로젝트 번들 원본 편집과 컴파일 PDF 미리보기
- `/documents/{documentId}/impact/`: 문서 관계와 변경 영향 검토
- `/documents/{documentId}/evidence/`: 제품·검증 근거 검토
- `/documents/{documentId}/approvals/`: 문서별 순차 승인
- `/documents/{documentId}/completion/`: 최종 완료 게이트와 승인 산출
- `/documents/{documentId}/history/`: 선택 문서 감사 이력
- `/history/`: 전체 문서 감사 이력

동적 문서 경로를 서버에서 처리하기 위해 Web production build는 Next.js
`standalone` 출력으로 실행합니다. Docker image는 생성된 `server.js`를
`0.0.0.0:8080`에서 실행합니다.

### 내부 사용자 준비

DB migration을 적용한 뒤 관리자가 내부 사용자 계정을 생성합니다. 외부 사용자
self-signup은 제공하지 않습니다.

```bash
mise exec -- poetry -C apps/api run alembic upgrade head
mise exec -- poetry -C apps/api run python -m ide_api.cmd.create_user \
  --email developer@neudive.com \
  --display-name "김개발"
```

비밀번호는 명령 실행 중 대화형으로 입력하며 DB에는 Argon2 hash만 저장됩니다.

## API 계약과 codegen

FastAPI의 OpenAPI schema가 API 계약의 단일 기준입니다. Web의 DTO와 Axios client는 `typescript-axios` generator로 생성합니다.

```bash
pnpm --dir apps/web api:generate
```

생성 파일은 `apps/web/src/api/generated`에 저장하며 직접 수정하지 않습니다. Web의
client component는 `apps/web/src/api/client.ts`가 제공하는 인증 포함 생성 client를
사용합니다.

API 변경 후 다음 검사를 수행하면 schema와 생성물의 불일치를 확인할 수 있습니다.

```bash
pnpm --dir apps/web api:check
```

## 품질 검사

API:

```bash
mise exec -- poetry -C apps/api run ruff check .
mise exec -- poetry -C apps/api run ruff format --check .
mise exec -- poetry -C apps/api run pytest
```

Web:

```bash
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web build
```

Web lint와 format에는 Biome만 사용합니다.

```bash
pnpm --dir apps/web format
```

## Web 배포

Web은 Next.js `standalone` 서버로 배포합니다.

```bash
NEXT_PUBLIC_API_BASE_URL=https://api.example.internal \
  pnpm --dir apps/web build
```

Docker image가 생성된 `server.js`를 실행합니다. API origin은 Web origin을 CORS 허용 목록에 포함해야 하며, 인증 cookie를 사용할 때는 HTTPS와 credential 전달 설정을 유지해야 합니다.

## Docker

API image:

```bash
docker build -t ide-api apps/api
docker run --rm -p 8000:8000 ide-api
```

Web image는 Next.js standalone 서버로 동적 문서 경로를 제공합니다.

```bash
docker build \
  --build-arg NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 \
  -t ide-web apps/web
docker run --rm -p 3000:8080 ide-web
```

배포 플랫폼, Kubernetes manifest와 배포 도구는 이 저장소에서 새로 고정하지 않으며 기존 배포 흐름을 따릅니다.
