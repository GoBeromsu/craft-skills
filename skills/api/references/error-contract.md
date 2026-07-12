# Error contract

## Incumbent contract gate

Inspect the published error responses before changing an existing API. Preserve its error shape, codes, and client-visible semantics unless an explicit version or migration scope names client compatibility and rollout behavior. Do not introduce a new error envelope as a cleanup.

Use the following defaults only for a greenfield API or an explicitly new API version. Keep transport failures that occur before application handling outside the application contract.

## Problem document

Expose business and application failures as RFC 7807 `ProblemDetail` with one application `code`.

| Field | Purpose |
|---|---|
| `type` | Stable URI identifying the problem category |
| `title` | Short human-readable category title |
| `status` | HTTP status code |
| `detail` | Safe request-specific explanation |
| `instance` | Request or resource instance identifier when safe |
| `code` | Stable domain or system code for client behavior |

Return the problem document directly. Clients branch on `code` and `status`, not `detail`.

## Code ownership and mapping

Each domain owns an `ErrorCode` enum using three uppercase letters, an underscore, and three digits, such as `MEM_001`; reserve `SYS_xxx` for cross-cutting system conditions. Allocate codes deliberately and never recycle a retired code. Keep the mapping beside the domain failure definition; exception middleware converts the typed failure once at the HTTP boundary.

| Failure source | Response | Logging |
|---|---|---|
| Expected validation or domain failure | Problem document with its owned code | Contextual event at appropriate severity |
| Application authentication or authorization failure | Problem document with an owned code when exposed | Security-relevant context without credentials |
| Unknown exception or any 5xx | Sanitized system problem with `SYS_xxx` | Diagnostic error log with request correlation |
| Transport/server rejection before application handling, such as 431 | Server/framework behavior | Outside the application contract |

Never include a stack trace, SQL query, secret, file path, or implementation-specific class name in `detail`; retain those only in correlated server diagnostics.
