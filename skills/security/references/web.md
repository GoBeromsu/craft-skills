# Web Frontend Security

The browser will execute or render whatever you hand it as HTML, JS, or a URL — treat every rendering sink, storage location, and cross-origin request as adversarial by default.

## Hard rules

| Concern | Do / Use | Never |
|---|---|---|
| Session/auth token storage | `httpOnly` + `Secure` + `SameSite=Lax` (or `Strict`) cookie | `localStorage` / `sessionStorage` — any injected script can read it |
| Rendering untrusted content | Text nodes (auto-escaped), or a sanitizer allowlist (`DOMPurify`) immediately before a raw-HTML sink | `dangerouslySetInnerHTML` / `v-html` / `.innerHTML =` on unsanitized input |
| Third-party `<script>`/`<link>` tags | Pinned with Subresource Integrity (`integrity="sha384-…"`) | An unpinned `src="https://cdn…"` tag |
| Cross-origin embedding | `X-Frame-Options: DENY` or CSP `frame-ancestors 'none'` | No frame-control header at all |

## Cross-site scripting (XSS)

XSS is attacker-controlled data executing as script in another user's browser because it was rendered as HTML/JS instead of escaped text. Three classes: **reflected** (the payload bounces off a URL/query param straight into the response), **stored** (the payload persists in a database and renders for every viewer), **DOM-based** (a client-side script writes untrusted data into a dangerous sink without the server ever seeing it).

**Detect** — dangerous rendering sinks across React/Vue/Angular/vanilla:

```bash
grep -rnE 'dangerouslySetInnerHTML|v-html\s*=|\.innerHTML\s*=|bypassSecurityTrust(Html|Script|Style|Url)' \
  --include="*.tsx" --include="*.ts" --include="*.jsx" --include="*.js" --include="*.vue" . \
  | grep -v node_modules
```

Reading: every hit is a candidate sink, not an automatic finding — trace its input back to confirm it is sanitized, or comes from a source the user cannot influence. Zero hits, or every hit backed by a sanitizer call in the same expression, is a pass. Heuristic: a sink wrapped behind a custom sanitizer function the grep can't see through still reads as a hit and needs a manual check.

**Fix** — render untrusted content as text by default (framework auto-escaping); if raw HTML is genuinely required, sanitize immediately before the sink, not upstream where a later edit could drop the call.

```tsx
// SMELL — raw HTML from an API response goes straight into the DOM
function Comment({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

// CLEAN — sanitized at the sink
import DOMPurify from "dompurify";
function Comment({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />;
}
```

Grey zone: server-rendered markdown-to-HTML pipelines are a common false negative for the grep above — the sink lives inside a library, not your code. Check the markdown renderer's own sanitization setting explicitly.

## Content-Security-Policy (CSP) baseline

CSP is a response header that tells the browser which script/style/connection sources are allowed to load, so an injected `<script>` tag from an XSS bug has nowhere to execute from even if it lands in the DOM.

**Detect** — is a CSP header set at all:

```bash
curl -sI "${APP_URL}" | grep -i "content-security-policy"
```

Reading: no output is a fail — no CSP in place. A present header still needs `script-src` checked for `'unsafe-inline'`/`'unsafe-eval'`, either of which defeats most of the protection.

**Fix** — baseline policy, tightened per app:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'
```

Grey zone: an app depending on inline scripts/styles from a UI library needs per-script nonces or hashes instead of `'unsafe-inline'` — treat `'unsafe-inline'` as debt with a dated ticket, not a resting state.

## Token storage law

An access or session token readable by JavaScript is readable by any script an XSS bug manages to inject — token storage location is a second line of defense behind XSS prevention, never a replacement for it.

**Detect**:

```bash
grep -rnE 'localStorage\.(setItem|getItem)\([^)]*(token|jwt|session)' \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" . \
  | grep -v node_modules
```

Reading: any hit is a finding — move the value into an `httpOnly` cookie set by the server; the client sends it automatically and never needs to read the raw value.

**Fix**: `Set-Cookie: session=…; HttpOnly; Secure; SameSite=Lax` issued server-side.

## Cross-site request forgery (CSRF)

CSRF is an attack where a malicious page makes the victim's browser submit a state-changing request to your app, riding on the victim's already-authenticated session cookie. `SameSite=Lax` blocks most cross-site form/`fetch` submissions automatically, but stops being sufficient when the app sets `SameSite=None` for a legitimate cross-site embed, or exposes a state-changing action behind a plain `GET`.

**Detect** — state-changing routes to cross-check against CSRF middleware:

```bash
grep -rnE "@(app|router)\.(post|put|patch|delete)" --include="*.py" .
```

Reading: this only enumerates candidates — cross-check each against the app's CSRF-token check; a route with no matching guard and no `SameSite=Strict`/`Lax` cookie is a finding. Heuristic, expect false positives (routes fronted by a gateway that already injects the check).

**Fix**: synchronizer token pattern (server issues a per-session token, the form/AJAX call echoes it back, server compares) or double-submit cookie; a state-changing `GET` is never acceptable — GET must stay side-effect-free.

```ts
// CLEAN — verify the CSRF token before mutating state
app.post("/account/delete", csrfProtection, (req, res) => {
  deleteAccount(req.user.id);
  res.sendStatus(204);
});
```

## Clickjacking

Clickjacking layers your page inside an invisible attacker-controlled iframe to trick a user into clicking something they didn't intend.

**Detect**: same header check as CSP above — confirm `X-Frame-Options: DENY` or `frame-ancestors 'none'` is present; either is sufficient, both is redundant but harmless.

**Fix**: set the header at the reverse proxy or framework level for every response, not per-route.

## Subresource Integrity (SRI)

SRI is a cryptographic hash attribute on a `<script>`/`<link>` tag that makes the browser refuse to execute the file if a compromised CDN silently swaps its content.

**Detect**:

```bash
grep -rnE '<(script|link)[^>]*src=.*https?://' --include="*.html" . | grep -v 'integrity='
```

Reading: any hit is a third-party asset with no integrity pin — add the hash or self-host the asset. Zero hits is a pass.

**Fix**:

```html
<script src="https://cdn.example.com/lib.js"
        integrity="sha384-<hash>" crossorigin="anonymous"></script>
```
