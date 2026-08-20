# Web

GMP 문서의 LaTeX 정본 편집, 컴파일 PDF 미리보기, DOCX import 변환 충실도 검토,
변경 검토, 영향·근거 확인, 승인과 완료를 하나의 문서 맥락에서 운영하는 Next.js
애플리케이션입니다. DOCX는 불변 import-only 입력이고 PDF는 참조·분석 입력입니다.

## 실행

저장소 루트에서 다음 명령을 사용합니다.

```bash
mise run dev:web
```

또는 이 디렉터리에서 직접 실행합니다.

```bash
pnpm dev
```

기본 주소는 <http://localhost:3000>이며 API 주소는
`NEXT_PUBLIC_API_BASE_URL`로 설정합니다.

## 주요 경로

- `/`: 내 작업
- `/documents/`: 문서 탐색과 등록
- `/documents/[documentId]/`: 문서 개요
- `/documents/[documentId]/validation/`: 원본 검증과 지원 범위 안내
- `/documents/[documentId]/import-review/`: DOCX 원본·LaTeX 정본·컴파일 PDF 대조와 사유 기반 인간 검토
- `/documents/[documentId]/changes/`: 변경 검토
- `/documents/[documentId]/workbench/`: LaTeX 정본 편집과 컴파일 PDF 미리보기
- `/documents/[documentId]/impact/`: 관계·영향
- `/documents/[documentId]/evidence/`: 제품·검증 근거
- `/documents/[documentId]/approvals/`: 순차 승인
- `/documents/[documentId]/completion/`: 최종 완료
- `/documents/[documentId]/history/`: 문서 감사 이력
- `/history/`: 전체 감사 이력

## 검사와 빌드

```bash
pnpm lint
pnpm typecheck
pnpm build
```

production build는 `output: "standalone"`을 사용합니다. Docker runtime은
`.next/standalone/server.js`를 포트 `8080`에서 실행합니다.

OpenAPI 계약 또는 생성 client가 변경되었는지는 다음 명령으로 확인합니다.

```bash
pnpm api:check
```
