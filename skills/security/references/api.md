# API and Server Security

Every handler is a trust boundary — parse and authorize before touching a request's data, whether it came from a browser, another internal service, or a queue message.

## Hard rules

| Concern | Do / Use | Never |
|---|---|---|
| Query construction | Parameterized query / ORM query builder | String concatenation or f-string/template-literal building of SQL |
| Shell invocation | `subprocess.run([...], shell=False)` / `execFile` with an argv array | `shell=True` / `child_process.exec()` with interpolated input |
| Object access by ID | Fetch scoped to the caller (`WHERE owner_id = :caller_id`) | Fetch by ID alone, trusting the caller's claim |
| Outbound URL fetch | Allowlisted destinations only | `fetch` / `requests.get` on a raw user-supplied URL |
| Deserialization of untrusted data | `json.loads` / `yaml.safe_load` / a schema-validated parser | `pickle.load`, `yaml.load()` without `SafeLoader`, `eval`/`exec` |

## Injection family

### SQL injection

SQL injection is untrusted input reaching a database query as executable SQL syntax instead of as a bound parameter value.

**Detect** (Python):

```bash
grep -rnE "\.(execute|executemany)\(\s*(f['\"]|.*%\s*\(|.*\+\s*[a-zA-Z_])" --include="*.py" .
```

**Detect** (TypeScript/Node):

```bash
grep -rnE '\.(query|execute)\(\s*`[^`]*\$\{' --include="*.ts" --include="*.js" . | grep -v node_modules
```

Reading: any hit concatenates or interpolates a variable directly into query text — a finding unless the driver explicitly parameterizes that placeholder syntax (check the call signature). Heuristic: misses queries built across several string-append lines before the `.execute()` call.

**Fix**: bind parameters through the driver/ORM, never string-build the query.

```python
# SMELL
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
# CLEAN
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

### Command injection

Command injection is untrusted input reaching a shell command as syntax rather than as a single opaque argument.

**Detect**:

```bash
grep -rnE 'shell\s*=\s*True|os\.system\(' --include="*.py" .
grep -rnE 'child_process\.(exec|execSync)\(' --include="*.ts" --include="*.js" . | grep -v node_modules
```

Reading: `shell=True`/`exec()` with any variable in the command string is a finding; a fully literal command string with no interpolation is a pass.

**Fix**: pass an argv list with no shell interpretation.

```python
# SMELL
subprocess.run(f"convert {filename} out.png", shell=True)
# CLEAN
subprocess.run(["convert", filename, "out.png"], shell=False)
```

### Path traversal

Path traversal is a request-derived filename reaching a filesystem call with no normalization, letting `../../etc/passwd`-style input escape the intended directory.

**Detect**:

```bash
grep -rnE '(open|readFile|readFileSync)\(\s*[^,")]*req\.' --include="*.py" --include="*.ts" --include="*.js" .
```

Reading: any hit passes request data into a file read with no visible normalization/allowlist step nearby — confirm the path is resolved and checked against a base directory before use.

**Fix**: resolve the path, then assert it stays under the intended root.

```python
base = pathlib.Path("/srv/uploads").resolve()
target = (base / user_filename).resolve()
if not target.is_relative_to(base):
    raise PermissionError("path escapes upload root")
```

## Authentication vs. authorization

Authentication answers "who is this caller"; authorization answers "may this caller do this to this object" — a handler that checks only the first is exploitable even with a fully working login system.

### IDOR (Insecure Direct Object Reference)

IDOR is a handler that fetches or mutates an object by an ID taken from the request without verifying the caller owns or is permitted to access that specific object.

**Detect** — object lookups with no visible owner/tenant filter nearby:

```bash
grep -rnE '(get_object_or_404|findById|find_by_id)\(' --include="*.py" --include="*.ts" .
```

Reading: this is a starting list, not a verdict — for each hit, confirm the surrounding function also checks `owner_id`/`tenant_id`/a permission predicate against the authenticated caller before returning or mutating the object. Grey zone: an admin-only handler legitimately skips the owner check but must instead check an explicit admin-role predicate — no check at all is still a finding.

**Fix**: scope every object fetch to the caller in the same query; don't fetch-then-check in application code, where a forgotten early return leaks the object.

```python
# SMELL — fetches by ID alone, no owner predicate
@app.get("/orders/{order_id}")
def get_order(order_id: OrderId):
    return db.get_order(order_id=order_id)  # any authenticated user can read any order

# CLEAN — scoped in the query itself
@app.get("/orders/{order_id}")
def get_order(order_id: OrderId, caller: CurrentUser):
    order = db.get_order(order_id=order_id, owner_id=caller.id)
    if order is None:
        raise HTTPException(404)
    return order
```

```ts
// CLEAN — Express/Node equivalent, scoped in the query
app.get("/orders/:orderId", requireAuth, async (req, res) => {
  const order = await db.orders.findFirst({
    where: { id: req.params.orderId, ownerId: req.user.id },
  });
  if (!order) return res.status(404).end();
  res.json(order);
});
```

## Rate limiting placement

Unlimited request volume turns a single bug (a slow query, an unauthenticated endpoint, a password-reset flow) into a denial-of-service or brute-force vector.

**Detect**: check whether authentication, password-reset, and any unauthenticated write endpoint sit behind a rate limiter.

```bash
grep -rniE "ratelimit|rate_limit|slowapi|express-rate-limit" . | grep -v node_modules | head -20
```

Reading: no hits at all in a codebase with public auth endpoints is a finding. Place the limiter at the gateway/edge for coarse global protection, and per-route for sensitive endpoints (login, password reset, signup) where the gateway default is too permissive.

## Server-Side Request Forgery (SSRF)

SSRF is the server being tricked into making an outbound HTTP request to an attacker-chosen destination — often reaching an internal-only service (a metadata endpoint, an internal admin panel) that the attacker could never reach directly.

**Detect**:

```bash
grep -rnE '(requests\.(get|post)|httpx\.(get|post)|fetch)\(\s*[a-zA-Z_]' --include="*.py" --include="*.ts" --include="*.js" .
```

Reading: any hit passes a variable — not a string literal — as the fetch target. Confirm the variable is checked against an allowlist of permitted hosts/schemes before the request fires. Zero hits, or every hit backed by an allowlist check, is a pass.

**Fix**: resolve and validate the destination against an allowlist before fetching; reject internal/link-local ranges (`127.0.0.0/8`, `169.254.0.0/16`, `10.0.0.0/8`, etc.) unless explicitly intended.

```python
# SMELL — no allowlist check on a user-controlled URL
resp = requests.get(user_supplied_url)

# CLEAN — validated against an allowlist before fetching
if urlparse(user_supplied_url).hostname not in ALLOWED_FETCH_HOSTS:
    raise ValueError("destination not in allowlist")
resp = requests.get(user_supplied_url)
```

## File upload rules

- Validate extension AND content (magic-byte sniff) — never trust the client-supplied MIME type alone.
- Cap size before reading the body into memory.
- Store uploads outside the web root, under a generated name — never the client-supplied filename.
- Re-encode images (strip EXIF, re-save through an image library) rather than serving the uploaded bytes verbatim.

## Unsafe deserialization

Deserializing untrusted bytes with a format that can reconstruct arbitrary objects or execute code (`pickle`, unrestricted YAML, `eval`) lets an attacker who controls the payload run code the moment it loads.

**Detect**:

```bash
grep -rnE 'pickle\.load\(|yaml\.load\(\s*[^,)]+\)\s*$|(^|[^.])eval\(|(^|[^.])exec\(' --include="*.py" .
```

Reading: `yaml.load()` with no explicit `Loader=yaml.SafeLoader` argument, any `pickle.load` on data that didn't originate from your own process, and any `eval`/`exec` on external input are all findings.

**Fix**: `yaml.safe_load(data)`; replace `pickle` for cross-boundary data with `json` or a schema-validated format; never `eval`/`exec` external input.
