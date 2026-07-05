# Personal dev skills lazycodex comparison matrix

Source basis: `backups/distill/lazycodex-distill-report.md` (G008), clean-room summary of `code-yeongyu/lazycodex` at `dac44057c70eedbdbca5afaeb1d16502e518fbdc`.

| Leaf | 배울 점 | 우리가 나은 점 | 채택·보류 결정 |
|---|---|---|---|
| `frontend` | 얇은 `SKILL.md`가 작업 유형을 먼저 나누고 세부 규칙은 필요할 때만 읽게 하는 flat router 구조. | craft는 5-key frontmatter, 현재형 recipe, 출처 분리(`CHANGELOG.md`/`PROVENANCE.md`)가 더 명확하다. | **채택:** 한 파일 안의 짧은 라우팅 표와 Phase 0 표면 게이트. **보류:** upstream 문장, 강한 브랜드성 톤, upstream reference tree 복제. |
| `frontend` | description에 “랜딩 페이지”, “접근성”, “visual QA”처럼 실제 호출 문구를 촘촘히 넣는 방식. | craft는 description을 trigger로 쓰라는 규약이 이미 있어 과한 본문 지시를 frontmatter에 넣지 않아도 된다. | **채택:** trigger-dense description. **보류:** description에 workflow 단계나 upstream 표현을 넣는 방식. |
| `frontend` | 디자인, 성능, 접근성을 서로 다른 검증 표면으로 분리해 완료 조건을 흐리지 않는 구조. | craft는 프로젝트 내부 디자인 계약과 repo-local 검증 명령을 우선할 수 있어 상표·브랜드 토큰 복제 위험이 낮다. | **채택:** 디자인 계약, 성능 증거, 접근성 증거를 별도 체크로 둔다. **보류:** Apple/Stripe/Linear 등 브랜드 디자인 시스템·카피·로고·이미지 지시문 복제. |
| `frontend` | 외부 디자인·UI 지식 DB를 router 뒤에 숨겨 필요할 때만 참조하는 progressive disclosure. | craft는 외부 데이터셋 편입 없이 프로젝트 문서와 실제 브라우저 증거로 충분한 기본 레시피를 만들 수 있다. | **보류:** UI 데이터셋, CLI, NOTICE 텍스트, 외부 template 편입. **채택:** “먼저 표면을 고르고 필요한 증거만 모은다”는 구조만. |
| `backend` | lazycodex에는 backend leaf가 없지만, 언어/표면별 reference를 분리하는 패턴은 API·DB·auth·worker 표면에도 맞다. | craft는 backend를 programming의 generic code 규칙과 분리해 API 계약, migration 안전, secret/auth, queue, observability만 다룰 수 있다. | **채택:** Phase 0 boundary gate와 backend 표면별 라우팅. **보류:** lazycodex의 특정 stack 선호표(Pydantic/httpx2/axum/gin/sqlc/Bun/Biome 등)와 스크립트/template. |
| `backend` | 품질 기준을 사용자 표면과 검증 표면으로 나누는 접근. | craft는 데이터 손실·인증 우회·운영 관측성처럼 backend 고유 실패 모드를 완료 조건에 직접 넣을 수 있다. | **채택:** API boundary, DB migration, auth/secret, background job, observability evidence. **보류:** generic TDD/type/LOC 규칙 중복; 그 영역은 `programming`에 남긴다. |
| `programming` | 언어 게이트를 먼저 두고, code smell을 skill activation/refactor trigger로 쓰는 방식. | craft programming은 이미 Python/TypeScript에 집중하고 workflow reference를 항상 읽게 해 context 비용과 범위를 낮춘다. | **채택:** trigger 밀도 보강, Phase 0 surface handoff, code-smell trigger 표준화. **보류:** Rust/Go 전면 편입, 언어별 reference 세분화, 실행 스크립트·bootstrap template. |
| `programming` | language-specific README/reference tree로 확장 가능한 구조. | craft는 단일 `python.md`/`typescript.md`와 shared workflow로 과잉지시를 줄이고 Fable-5 감사 방향(필요한 지시만 남김)에 맞는다. | **부분 채택:** “언어를 먼저 고른다”는 게이트를 유지하고 frontend/backend 분기만 추가. **보류:** reference 숲 확장, stack별 선호표 복제. |
| `programming` | leaf별 research matrix를 남겨 바로 편입하지 않고 판단을 기록하는 방식. | craft는 비교 서사를 recipe 밖에 격리해 SKILL.md를 현재형 작동 지시로 유지한다. | **채택:** 이 matrix를 편입 판단의 유일한 비교 서사 위치로 둔다. **보류:** SKILL.md 본문에 upstream 이름·역사·비교 설명을 넣는 방식. |
| all leaves | upstream root는 MIT지만 frontend attribution에는 Apache-2.0, MIT 하위 출처와 상표 고지가 섞여 있다. | craft는 아이디어-only 채택과 출처 표기를 분리할 수 있다. | **복사 금지:** license/NOTICE 전문, ATTRIBUTION 문구, upstream 문장·톤, 저자·프로젝트 고유명 운영어, 브랜드 디자인 내용, 특정 stack 선호표, scripts/templates. **채택:** 패턴 아이디어만 재작성. |
