# Integrated Document Environment

## Common Task Rule

* 모호한 부분이나 정보가 부족한 부분이 있다면 절대 추정하지 않고 사용자에게 질의한다.
* 사용자와의 인터렉션이나 사고과정 출력은 한국어 경어체로 한다.
* 작업 중 사용자의 명시적인 언급이나 암시적으로 프로젝트 전역에 적용해야 하는 규칙을 발견하면 이 문서에 추가한다.

## Git Commit Rule

* 커밋에 Co Author를 포함하지 않는다.
* 커밋 메세지는 한글로 작성한다.
* 커밋은 반드시 기능단위로 분리하여 원자적으로 커밋한다.

## Git Worktree Rule

* Worktree를 만들어 작업할 때는 반드시 `.worktrees` 디렉토리 아래에 생성한다.
* Worktree를 생성하는 경우 git ignore된 `.env`를 worktree로 복사한다.

## Dependency Rule

* 사용하는 도구나 의존성의 버전은 `latest`를 사용하지 않고 명시적인 최신 또는 LTS 버전을 사용한다.

## Application Entry Point Rule

* 모든 애플리케이션의 진입점은 해당 애플리케이션 package의 `cmd` 디렉터리에 둔다.

## README Rule

* `README.md`에 문서화된 기능, 기술 스택, 디렉토리 구조, 설정, 실행·검사·빌드·배포 방법이 변경되면 같은 작업에서 `README.md`를 반드시 함께 수정한다.

## API Path Rule

* API Path는 `/api/v(version)` prefix를 가진다.
    * e.g. `/api/v1/health`

## Web Path Rule

* 각 페이지는 각각의 path를 가진다
* 절대 하나의 path에 여러 기능을 분기로 렌더링하지 않눈다.
