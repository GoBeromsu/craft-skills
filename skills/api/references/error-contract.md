# Error contract

Expose business and application failures as stable, machine-readable problem documents. Keep protocol failures that occur before application handling outside this contract.

## Problem document

Return RFC 7807 `ProblemDetail` fields plus one application code:

| Field | Purpose |
|---|---|
| `type` | Stable URI that identifies the problem category |
| `title` | Short, human-readable category title |
| `status` | HTTP status code |
| `detail` | Safe, request-specific explanation |
| `instance` | Request or resource instance identifier when safe to expose |
| `code` | Stable domain or system error code for client behavior |

Do not wrap this object in a success-style envelope. `detail` explains the current request but clients branch on `code` and `status`, not prose.

## Code ownership

Each domain defines its own `ErrorCode` enum. Use three uppercase letters, an underscore, and three digits: `MEM_001`, `ORD_014`, or `PAY_021`. Reserve `SYS_xxx` for cross-cutting system conditions, such as unexpected persistence availability or an uncategorized application failure. Allocate codes deliberately; do not recycle a retired code for a new meaning.

Keep the mapping adjacent to the domain failure definition, not spread through controllers. The exception mapper or error middleware converts the typed failure once at the HTTP boundary.

## Mapping rules

| Failure source | Response | Logging |
|---|---|---|
| Expected validation or domain failure | Problem document with its owned code | Contextual event at appropriate severity |
| Authentication or authorization failure handled by the application | Problem document with owned code when the API exposes one | Security-relevant context without credentials |
| Unknown exception or any 5xx | Sanitized system problem with `SYS_xxx` | Diagnostic error log with request correlation |
| Transport/server rejection before application handling, such as 431 | Server/framework behavior | Do not document as an application error contract |

Never include a stack trace, SQL query, secret, file path, or implementation-specific class name in `detail`. Attach those only to server-side diagnostics with request correlation.

## Contract example

```json
{
  "type": "https://api.example.com/problems/member-not-found",
  "title": "Member not found",
  "status": 404,
  "detail": "No member exists for the supplied identifier.",
  "instance": "/api/v1/members/123",
  "code": "MEM_001"
}
```

The URI is illustrative: choose the public API host from deployment configuration, not a hard-coded environment value.
