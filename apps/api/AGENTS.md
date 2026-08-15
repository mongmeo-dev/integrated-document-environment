# API 작업 규칙

## 폴더 구조

API는 도메인별 모듈 구조를 사용하며, 각 도메인 안에서 HTTP, 유스케이스, 영속성 책임을 분리한다.

```text
apps/api/
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
├── scripts/
│   └── export_openapi.py
├── src/
│   └── ide_api/
│       ├── __init__.py
│       ├── cmd/
│       │   ├── __init__.py
│       │   ├── api.py                 # FastAPI 애플리케이션 진입점
│       │   └── worker.py              # Celery worker 애플리케이션 진입점
│       ├── core/
│       │   ├── config.py              # 애플리케이션 설정
│       │   ├── database.py            # DB engine 및 session
│       │   ├── exceptions.py          # 공통 예외와 변환 규칙
│       │   ├── logging.py             # 로깅 설정
│       │   └── security.py            # 인증·인가 공통 기능
│       ├── api/
│       │   ├── dependencies.py        # 인증, DB session 등 공통 Depends
│       │   └── v1/
│       │       └── router.py           # v1 도메인 router 조립
│       ├── domains/
│       │   ├── system/
│       │   ├── documents/
│       │   ├── changes/
│       │   ├── formatting/
│       │   ├── impacts/
│       │   ├── evidence/
│       │   └── approvals/
│       ├── infrastructure/
│       │   ├── object_storage.py
│       │   ├── openai.py
│       │   ├── celery.py
│       │   └── redis.py
│       └── workers/
│           └── tasks/
└── tests/
    ├── conftest.py
    ├── unit/
    │   └── domains/
    ├── integration/
    │   ├── api/
    │   └── repositories/
    └── fixtures/
```

위 구조는 목표 구조다. 아직 필요하지 않은 디렉터리와 파일을 미리 만들지 않고, 실제 기능을 추가할 때 함께 생성한다.

## 도메인 모듈

도메인 모듈은 필요한 파일만 가진다.

- `router.py`: HTTP 요청·응답, 상태 코드, FastAPI 의존성 처리
- `schemas.py`: Pydantic 요청·응답 모델
- `models.py`: SQLAlchemy 영속 모델
- `service.py`: 유스케이스, 업무 규칙, 트랜잭션 경계
- `repository.py`: 데이터 조회와 저장
- `tasks.py`: 해당 도메인의 비동기 작업

단순한 도메인에 사용하지 않는 계층이나 빈 파일을 추가하지 않는다. 프로젝트 전역의 `routers`, `services`, `models`, `repositories` 디렉터리는 만들지 않는다.

## 의존성 방향

기본 요청 흐름은 다음과 같다.

```text
router → service → repository → SQLAlchemy
                    └──────────→ infrastructure
```

- `cmd/api.py`는 애플리케이션 생성, middleware 설정, 최상위 router 연결만 담당한다.
- API server, worker, scheduler, CLI 등 모든 애플리케이션 진입점은 `cmd`에 둔다.
- Router에서 SQLAlchemy session이나 query를 직접 다루지 않는다.
- Repository에 업무 규칙을 넣지 않는다.
- Service는 FastAPI의 `Request`, `Response`, `HTTPException`에 의존하지 않는다.
- 트랜잭션은 service의 유스케이스 단위로 관리한다.
- 한 도메인은 다른 도메인의 repository를 직접 호출하지 않고 공개된 service를 통해 협력한다.
- 외부 서비스와 SDK 구현은 `infrastructure`에 두고 도메인 로직에서 격리한다.

## API와 테스트

- 모든 API path는 루트 규칙에 따라 `/api/v1` prefix를 사용한다.
- API version router는 `api/v1/router.py`에서 조립한다.
- 단위 테스트는 도메인 service와 업무 규칙을 검증한다.
- 통합 테스트는 HTTP 계약, DB repository, 외부 시스템 adapter 경계를 검증한다.
- 테스트 파일은 검증 대상의 도메인 구조를 따라 배치한다.
