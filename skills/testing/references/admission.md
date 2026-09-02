# Test Admission Reference

Use this table before adding, retaining, rewriting, or deleting a test.
Admit a test only when it names a behavior or invariant, covers a distinct failure mode, uses an independent oracle, and uses the cheapest layer that observes the failure.
Search existing evidence before adding a row and retain overlapping evidence only when it leaves a distinct residual risk.

| Pattern | Verdict | Why | What to do instead |
|---|---|---|---|
| Getter, setter, or pure delegation with no behavior beyond the dependency contract | Reject as `no-test` | The wrapper creates no distinct failure mode | Name the type guarantee, pure delegation, or higher contract test that covers the behavior |
| Assertion that a UI string contains implementation copy | Rewrite | The implementation text supplies the oracle and can lock in a wrong answer | Assert the limit or message rule from the specification or an approved fixture, as in [oss-hub PR #1130](https://github.com/JNU-SWCU/oss-hub/pull/1130) |
| File-exists, import-works, source-layout, or topology re-check | Reject as `no-test` | Topology is not a user or contract failure mode | Test the public behavior that the topology was intended to support |
| Fixture generator, source-string mutation, or checker-of-checker with no independent residual risk | Delete or rewrite | A meta layer protects test mechanics rather than a product or deployment contract | Call the public checker with counterfactual input when its contract is independently observable, otherwise delete the layer |
| Snapshot of unstable output | Rewrite or reject | Time, random ordering, generated identifiers, or incidental formatting makes the oracle nondiagnostic | Stabilize the output and assert a contract-relevant field or use an approved stable fixture |
| Real-clock or random-id dependence | Rewrite | The test can fail as time advances or as scheduling changes | Inject a fixed clock and deterministic identifiers, as in [oss-hub PR #1155](https://github.com/JNU-SWCU/oss-hub/pull/1155) and [SeeON-edge #445](https://github.com/SeniorAILab/SeeON-edge/issues/445) |
| Time or clock boundary | Admit | A boundary can fail despite ordinary values passing | Inject the clock and assert behavior immediately before, at, and after the boundary at the cheapest observable layer |
| Concurrency or ordering boundary | Admit | Race, ordering, or delivery semantics require assembled collaborators | Use deterministic synchronization and an integration layer when a unit cannot observe the boundary |
| State boundary | Admit | Empty, full, expired, transitioned, or rollback states have distinct risks | Construct the boundary state and assert the specified transition at the cheapest observable layer |
| API or schema contract boundary | Admit | Independently deployed consumers can observe incompatible payloads | Test the public contract against the schema, protocol, or approved fixture at the boundary layer |
| Error branch | Admit | A specified failure outcome can regress independently of the success path | Trigger the documented error condition and assert its public error contract at the cheapest observable layer |

Treat a checker as a valid test subject only when its public or deployment contract creates a distinct residual risk and the test uses an independent counterfactual oracle.
Do not add a separate checker that enforces this table because reviewable decision rows provide the evidence without another meta layer.
