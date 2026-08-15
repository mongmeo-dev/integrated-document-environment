# Integrated Document Environment

뉴다이브 임직원이 소프트웨어 의료기기 개발 과정의 GMP 문서를 검토하고 변경 영향, 제품·검증 근거와 승인 이력을 관리하기 위한 내부 문서 작업 환경입니다.

이 시스템은 DOCX/PDF 편집기를 제공하지 않습니다. 원본과 외부 편집 결과를 수집하고, 서식 차이와 관련 문서·근거 후보를 검토한 뒤 사람이 최종 확정하는 흐름을 제공합니다.

> 현재 저장소는 Phase1 구현을 위한 초기 애플리케이션과 개발 환경을 포함합니다. 전체 제품 요구사항은 [PRD](docs/tasks/phase1_prd/PRD.md), 기술 결정은 [기술 스택 문서](docs/TECH_STACK.md)를 참고하십시오.

## 주요 원칙

- 등록된 원본 파일은 변경하거나 덮어쓰지 않습니다.
- DOCX는 DOCX로, 텍스트 PDF는 PDF로만 외부 편집 결과를 재수집합니다.
- 자동 서식 검사와 사용자의 시각 비교를 모두 완료해야 합니다.
- 수정안, 문서 관계, 영향과 근거는 사용자가 확정하기 전까지 후보입니다.
- 미해결 서식 차이 또는 미처리 후보가 있으면 승인과 산출을 차단합니다.
- AI는 후보 생성에만 사용하며 승인과 완료 여부를 결정하지 않습니다.
- 서비스는 뉴다이브 내부망에서만 제공합니다.

## 기술 구성

| 영역 | 기술 |
|---|---|
| API | Python 3.14, FastAPI, Pydantic, SQLAlchemy, Alembic |
| 비동기 처리 | Celery, Redis |
| 데이터베이스 | PostgreSQL, pgvector |
| Web | Next.js static export, React, TypeScript |
| UI 및 서버 상태 | Chakra UI, TanStack Query |
| API client | OpenAPI Generator `typescript-axios` |
| AI | OpenAI Responses API, Structured Outputs, Embeddings API |
| 파일 저장 | Naver Cloud Object Storage |
| Python 도구 | Poetry, Ruff, pytest |
| Web 도구 | pnpm, Biome, TypeScript compiler |

## 디렉터리

```text
apps/
  api/                 FastAPI 애플리케이션과 OpenAPI schema
  web/                 Next.js 정적 Web 애플리케이션
docs/
  TECH_STACK.md        기술 스택과 설계 결정
  tasks/phase1_prd/    Phase1 요구사항과 원천 작업 문서
```

## 개발 환경

### 요구 사항

- [mise](https://mise.jdx.dev/)
- Docker

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
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`NEXT_PUBLIC_API_BASE_URL`은 정적 Web build 시 산출물에 포함되므로 환경별로 별도 build해야 합니다. 비밀값을 `NEXT_PUBLIC_*` 변수에 넣어서는 안 됩니다.

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

API를 실행합니다.

```bash
mise exec -- poetry -C apps/api run uvicorn ide_api.main:app --reload
```

Web 개발 서버를 실행합니다.

```bash
pnpm --dir apps/web dev
```

기본 주소는 다음과 같습니다.

- Web: <http://localhost:3000>
- API: <http://localhost:8000>
- API 문서: <http://localhost:8000/docs>
- 상태 확인: <http://localhost:8000/api/v1/health>

## API 계약과 codegen

FastAPI의 OpenAPI schema가 API 계약의 단일 기준입니다. Web의 DTO와 Axios client는 `typescript-axios` generator로 생성합니다.

```bash
pnpm --dir apps/web api:generate
```

생성 파일은 `apps/web/src/api/generated`에 저장하며 직접 수정하지 않습니다. Web의 page와 component는 생성된 client 또는 Axios를 직접 호출하지 않고, 반드시 TanStack Query query/mutation으로 래핑하여 사용합니다.

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

## 정적 Web 배포

Web은 Next.js server 없이 정적 파일로 배포합니다.

```bash
NEXT_PUBLIC_API_BASE_URL=https://api.example.internal \
  pnpm --dir apps/web build
```

산출물은 `apps/web/out/`에 생성됩니다. 이 디렉터리의 내용을 Naver Cloud Object Storage에 업로드하고 CDN origin으로 연결합니다. CDN과 Object Storage는 SPA fallback 대신 실제 생성된 경로와 `404.html`을 사용하도록 구성합니다.

API origin은 Web origin을 CORS 허용 목록에 포함해야 하며, 인증 cookie를 사용할 때는 HTTPS와 credential 전달 설정을 유지해야 합니다.

## Docker

API image:

```bash
docker build -t ide-api apps/api
docker run --rm -p 8000:8000 ide-api
```

Web image는 static export 결과를 비특권 nginx로 제공합니다. Object Storage/CDN 업로드 전 산출물 검증이나 컨테이너 기반 정적 배포에 사용할 수 있습니다.

```bash
docker build \
  --build-arg NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 \
  -t ide-web apps/web
docker run --rm -p 3000:8080 ide-web
```

배포 플랫폼, Kubernetes manifest와 배포 도구는 이 저장소에서 새로 고정하지 않으며 기존 배포 흐름을 따릅니다.
