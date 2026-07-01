# Admission receipt — hookify (2026-06-30)

Stage 0 scope gate (create). Five drop-questions, each defaulting to ✗.

| Q | Question | Verdict | Evidence |
|---|---|---|---|
| Q1 | Reusability | ✓ | 임의 repo에서 "컨벤션을 로컬 강제로 바꾸기"는 반복되는 work-craft 패턴이다. |
| Q2 | Ownership | ✓ | upstream 도구가 소유한 절차가 아니다 — 표면 선택·티어 판별은 사용자 측 방법론이다. |
| Q3 | Convention-not-artifact | ✓ | 특정 프로젝트 산출물이 아니라 이식 가능한 컨벤션/방법이다. 스타터 스크립트는 템플릿(플레이스홀더)일 뿐 특정 repo 결합 없음. |
| Q4 | Portability | ✓ | Claude Code · Codex · git 전반에 적용. 특정 호스트/스택에 묶이지 않음. |
| Q5 | Boundary-purity | ✓ | 엔지니어링 work-craft 경계 — bstack(개인/라이프)과 무관. |

```
ADMIT (all five ✓) → proceed to Harvest
```

Verdict: **ADMIT**. Routed destination: craft-skills `skills/hookify/` (flat).
