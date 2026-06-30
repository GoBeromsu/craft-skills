<!--
PURPOSE: Skeletons for documenting a public API surface. Pick the one that matches the surface:
  - Doc-comment block  → for functions/methods/classes (in-code reference).
  - OpenAPI fragment    → for a REST HTTP endpoint (contract for external consumers).
Document the CONTRACT (inputs, outputs, errors, one example), not the implementation.
-->

## Doc-comment block (functions / methods)

```js
/**
 * {One line: what it does, stated as a contract — not how it works.}
 *
 * @param {Type} name - {meaning; required vs optional; valid range / units}
 * @param {Type} [optional=default] - {meaning when omitted}
 * @returns {Type} {what it represents, including the empty/zero case}
 * @throws {ErrorType} {the condition that triggers it}
 * @example
 *   {one short, real call → its result}
 */
```

Adapt the tag vocabulary to the language's documentation convention (JSDoc/TSDoc, Python
docstring `Args:`/`Returns:`/`Raises:`, Javadoc `@param`/`@return`/`@throws`, Go doc comment).
The four contract facts stay constant: **parameters, return, errors, one example.**

## OpenAPI fragment (REST endpoint)

```yaml
paths:
  /{resource}:
    {get|post|put|delete}:
      summary: {one line}
      parameters:
        - name: {param}
          in: {query|path|header}
          required: {true|false}
          schema: { type: {string|integer|...} }
          description: {meaning}
      requestBody:        # omit for GET/DELETE
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/{Model}' }
      responses:
        '200':
          description: {success case}
          content:
            application/json:
              schema: { $ref: '#/components/schemas/{Model}' }
        '4xx':
          description: {error case — what causes it}
```
