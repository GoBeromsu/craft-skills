# Next.js App Router Folder Correction

Operator correction: a Next.js App Router codebase should not wait for a second call site
before centralizing domain state, logic, API calls, and types, and should not force early
sharing of page-only UI that merely looks alike across routes today. State and logic are
reused; UI is repeated. Colocate page-only UI in `app/<route>/_components/` — resist
unifying similar-looking page UI early, since domain UI that looks alike now typically
diverges as routes evolve independently, and early unification produces branch-heavy
components serving multiple unrelated callers. Put any state, logic, API call, or type that
spans more than one page (a business concept — session, user) in `features/<domain>/` from
its first usage, not its second — scattered domain logic is the main cost driver when a
domain rule changes and every copy has to be found by hand. Promote a page-local UI
component to the top-level `components/` only once a second page actually reuses it.
Dependencies run one way, `app/ → features/ → lib/`; no reverse import, no feature reaching
into another feature's internal path; all HTTP goes through one client,
`lib/api-client.ts`. Do not adopt FSD's full layers/slices/segments taxonomy for this
pattern — carry over only its unidirectional-dependency principle, since per-ticket
layer/slice/segment classification cost outweighs its benefit for a small or
lower-experience team.
