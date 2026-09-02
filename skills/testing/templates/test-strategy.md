# Test Strategy

| behavior_or_invariant | failure_mode | independent_oracle | cheapest_layer | why_cheaper_layers_insufficient | assertion | decision (add\|rewrite\|delete\|no-test) | justification |
|---|---|---|---|---|---|---|---|
| <named behavior or invariant> | <distinct failure mode> | <specification, contract, or recorded fixture> | <unit, component, integration, or e2e> | <why a cheaper layer cannot observe this failure, or `n/a`> | <public observable assertion> | <add, rewrite, delete, or no-test> | <for `no-test`, name pure delegation, type guarantee, or the higher contract test that covers it> |
