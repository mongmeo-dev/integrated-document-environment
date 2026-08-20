# Integrated Document Environment

## Common Task Rule

* 모호한 부분이나 정보가 부족한 부분이 있다면 절대 추정하지 않고 사용자에게 질의한다.
* 사용자와의 인터렉션이나 사고과정 출력은 한국어 경어체로 한다.
* 작업 중 사용자의 명시적인 언급이나 암시적으로 프로젝트 전역에 적용해야 하는 규칙을 발견하면 이 문서에 추가한다.
* Web UI는 어드민 대시보드보다 문서 워크벤치 구조를 우선하며, 개발팀이 문서·변경 영향·근거·승인 상태를 고밀도로 탐색할 수 있게 설계하되 기존 IDE 제품을 그대로 모방하지 않는다.
* 문서 작성·관리의 정본은 진입점 `.tex`, 자산, 참고문헌, 스타일 파일로 구성한 LaTeX 프로젝트 번들이며, 컴파일 PDF는 검토·승인용 파생 산출물이다. Web은 LaTeX 원본 편집과 PDF 미리보기를 주 흐름으로 제공한다. DOCX는 불변의 일방향 가져오기 입력으로만 지원하며 변환 차이는 사람이 사유와 함께 명시적으로 검토·확정한다. PDF는 참조·분석 입력으로 지원하되 주 편집 원본으로 취급하지 않는다.

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


## Browser Rule
* 브라우저를 사용한 test가 필요한 경우 `aside cli`를 우선적으로 사용한다.
