# Testing E2E Reference

An e2e test earns its cost only by driving the real, user-visible path the way a user actually would — a slow or flaky one loses that trust immediately.

## Hard rules

### Selector law

| Concern | Do / Use | Never |
|---|---|---|
| Element selection | Role, accessible label, or a dedicated test id (`getByRole`, `getByLabelText`, `getByTestId`) | A css selector chain or xpath tied to DOM structure |

```bash
grep -rnE "querySelector|xpath|\.locator\(['\"]\.|css\(['\"]" --include='*.e2e.*' --include='*.spec.ts' <e2e-dir>
```

Pass: no output. Fail: any hit — a structural selector breaks on a harmless markup refactor, not on a real regression, and starts lying about what's actually broken.

### Auto-wait over sleep

| Concern | Do / Use | Never |
|---|---|---|
| Waiting for UI state | The framework's built-in auto-wait, or `waitFor(condition)` on the actual state you need | `sleep` / `waitForTimeout` / any fixed delay |

```bash
grep -rnE "waitForTimeout|sleep\(|time\.sleep" --include='*.e2e.*' --include='*.spec.ts' <e2e-dir>
```

Pass: no output. Fail: any hit — a fixed delay is either too short (flaky under load) or too long (slow always), and it is never the right duration for both.

### Test-data lifecycle

Each test creates the data it needs and cleans it up — no test relies on state left behind by another test, and no test relies on running before or after a specific sibling.

```bash
<test-runner> --shuffle   # e.g. pytest -p randomly, vitest --sequence.shuffle
# Playwright has no shuffle flag (--shard only partitions tests across machines, it doesn't randomize order) —
# compare a `--workers=1` run against the default multi-worker run instead, since parallel workers already interleave execution order
```

Pass: the shuffled run produces the same pass/fail result as the unshuffled run. Fail: a test fails only in some orderings — a hidden dependency on another test's leftover data or side effect.

### Flake triage protocol

1. First observed flake → quarantine it immediately (a `@flaky` tag or an explicit skip-with-reason marker) and open a tracked issue. Never let a flaky test keep running unflagged — it trains the team to ignore red.
2. Fix or delete it within a stated deadline (e.g., before the next release). An undated quarantine is a permanent leak in the suite's trustworthiness.
3. Never adopt automatic retries as the long-term fix for a specific known-flaky test.

```bash
grep -rnE "retries?\s*:\s*[1-9]|retry\s*=\s*[1-9]" <e2e-config-file>
```

Read: a nonzero retry count configured suite-wide with no linked flake-tracking issue is a suppressed problem, not a solved one — grey zone, judge by whether each retry-enabled suite (or test) has a tracked issue and a deadline; a small global retry count guarding against genuine infra blips (not code bugs) is acceptable when documented as such.

Quarantine tag syntax differs by framework but the shape is the same — a marker plus a reason, never a silent skip:

```python
@pytest.mark.xfail(reason="flaky: JIRA-1234 — race on cart total update")
def test_cart_total_updates_after_add():
    ...
```

```typescript
test.fixme("flaky: JIRA-1234 — race on cart total update", async ({ page }) => {
  ...
});
```

Both forms keep the test discoverable and its reason visible in CI output, unlike a commented-out test or a bare `.skip`.

### Setup through the API, not the UI

Seed prerequisite state — login, an existing account, an existing record — directly through the API or a DB seed call. Drive the UI only for the behavior actually under test. A checkout e2e test that also drives account signup through five UI screens pays that cost on every run and starts failing on someone else's unrelated signup bug.

Grey zone — no reliable grep for this; judge by reading the test's opening steps: do they merely reach a starting state that has nothing to do with what the test claims to verify? If yes, move that setup to an API call or fixture and start the UI interaction at the state under test.

```typescript
// SMELL — full UI signup just to reach a logged-in state
await page.goto("/signup");
await page.getByLabel("Email").fill("test@example.com");
await page.getByLabel("Password").fill("hunter2");
await page.getByRole("button", { name: "Create account" }).click();
// ...the test's actual subject begins only here

// CLEAN — seed the account via API, start the UI at the state under test
const user = await api.createUser({ email: "test@example.com" });
await page.goto("/login");
await loginAs(page, user);
```

### Browser/device matrix minimalism

Run the full e2e suite, on every commit, against one primary browser — the one closest to the majority of real users. Reserve a wider browser/device matrix (other browsers, mobile viewports) for a scheduled or pre-release CI job. Most e2e failures are behavior bugs that reproduce identically in any browser; running the full matrix on every commit multiplies suite time without multiplying the bugs actually caught.

### Navigation helpers are the one DAMP exception

The suite-level DAMP-over-DRY rule (see the main skill's naming/DAMP section) discourages extracting assertions or setup logic into shared helpers — but a *navigation* sequence (log in, reach a specific page) may be extracted even so. Extracting navigation centralizes the one-time cost of a UI-path change across every test that depends on it, while each test's own assertions stay inline and readable. The distinction: a navigation helper gets you *to* the starting state; it never decides what the test checks once there.

## Worked examples

```typescript
// SMELL — css selector + fixed sleep
await page.click(".btn.btn-primary.checkout-submit");
await page.waitForTimeout(2000);
expect(await page.textContent(".order-status")).toBe("Confirmed");
```

```typescript
// CLEAN — role selector + auto-wait on the actual state
await page.getByRole("button", { name: "Complete checkout" }).click();
await expect(page.getByTestId("order-status")).toHaveText("Confirmed");
```

The clean version survives a CSS refactor and fails only when the checkout flow itself breaks; the smell version does both in reverse.

```typescript
// SMELL — global retry papers over a genuine race condition
export default defineConfig({ retries: 3 });
```

```typescript
// CLEAN — fix the underlying wait; keep retries at zero once the suite is genuinely stable
export default defineConfig({ retries: 0 });
// wait on the real state the UI is transitioning to, instead of retrying the whole test
await expect(page.getByTestId("cart-count")).toHaveText("1");
```

A retry count hides which runs failed for a real reason; a fixed wait condition either passes for the right reason or fails loudly enough to investigate.

## Grey zones

- "Is this critical enough to deserve an e2e test at all?" — judge by whether a broken flow here would be a shipped incident (auth, checkout, data loss) versus a cosmetic regression better caught by a component or integration test.
- "Does this flaky test need a full rewrite or just a better wait condition?" — if the failure is timing-only (confirmed by the shuffle run passing when re-run alone), fix the wait condition first before rewriting the test.
- "Is this setup step part of the behavior under test, or just a prerequisite?" — if the test's name doesn't mention it, it's a prerequisite; seed it through the API.
