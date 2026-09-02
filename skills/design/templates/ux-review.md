# UX Review

```yaml
primary_operator: <role performing the task>
primary_action: <one action that completes the task>
evidence: <screenshot | interaction transcript | none>
screens_checked[]:
  - <screen or route, state, and evidence path or automation transcript reference>
violated_principles[]:
  - principle: <one of the seven UX review principles>
    screen_evidence: <screenshot path or automation transcript reference>
    repro_steps:
      - <step>
    fix: <smallest change that makes the principle check pass>
recommendation: <ship, block, or scoped follow-up with rationale>
```

List every checked screen even when `violated_principles[]` is empty.
Set `evidence: none` and state lower confidence in `recommendation` when browser interaction or screenshots are unavailable.
