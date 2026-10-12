
# PortaTap — API Conventions

**Status:** Approved baseline for MVP
**Primary interaction model:** Django views and HTML responses
**Dynamic UI:** HTMX
**External integrations:** Explicit HTTP contracts

## 1. Purpose

This document defines HTTP conventions for PortaTap.

PortaTap primarily uses server-rendered Django pages and HTMX interactions. It does not require a JSON REST API for every frontend operation.

The conventions in this document cover:

- Browser navigation.
- HTMX requests and HTML fragments.
- Form submissions.
- Authentication and authorization.
- Validation and error handling.
- External provider webhooks.
- Optional JSON APIs.
- Idempotency and request tracing.

## 2. Endpoint Categories

Classify endpoints by their purpose.

### 2.1 Full-page endpoints

Return complete HTML documents.

Examples:

- `GET /owner/dashboard/`
- `GET /owner/products/`
- `GET /staff/orders/`
- `GET /menu/<public-token>/`

### 2.2 HTMX endpoints

Return HTML fragments or another documented response suitable for the requested interaction.

Examples:

- `GET /owner/products/table/`
- `GET /staff/orders/list/`
- `POST /staff/orders/<order-id>/accept/`
- `POST /staff/orders/<order-id>/reject/`

These are illustrative examples. Actual routes must follow the existing URL structure.

### 2.3 External integration endpoints

Used for server-to-server integrations.

Examples:

- Payment provider webhooks.
- Provider reconciliation callbacks, when supported.
- Other explicitly approved machine-client integrations.

These endpoints must use their documented machine-readable formats and authentication or signature verification.

### 2.4 Optional JSON API endpoints

Introduce JSON endpoints when required by a real integration or client application.

Do not create a separate JSON API merely to support ordinary Django Template and HTMX interactions.

## 3. HTTP Methods

Use HTTP methods according to their intended semantics.

| Method | Intended use                                              |
| ------ | --------------------------------------------------------- |
| GET    | Read data or render pages; must not mutate business state |
| POST   | Create resources or perform state-changing actions        |
| PUT    | Replace a resource representation when appropriate        |
| PATCH  | Partially update a resource when appropriate              |
| DELETE | Delete a resource when deletion is permitted              |

For ordinary HTML forms and HTMX interactions, GET and POST are generally sufficient.

Do not use GET for operations such as accepting an order, confirming payment, issuing a refund, or adjusting stock.

Financial operations must not be triggered by navigation or prefetching.

## 4. URL Conventions

Use readable, consistent, resource-oriented paths.

Prefer:

- `/owner/products/`
- `/owner/products/<product-id>/edit/`
- `/staff/orders/`
- `/staff/orders/<order-id>/accept/`
- `/staff/orders/<order-id>/reject/`
- `/staff/orders/<order-id>/refund-request/`

Use Django URL names for internal references rather than hardcoding paths throughout templates.

Example:

```python
path(
    "staff/orders/<uuid:order_id>/accept/",
    views.accept_order,
    name="accept_order",
)
```

Choose UUID converters or another identifier format consistent with the actual model.

Do not expose database identifiers as authorization tokens.

## 5. HTMX Request and Response Rules

### 5.1 Request handling

HTMX requests must use the same authentication, authorization, validation, and business logic as ordinary requests.

Do not treat an HTMX request header as proof of authorization.

Use Django's CSRF protection for state-changing requests.

### 5.2 HTML fragment responses

For successful partial updates:

1. Execute the operation.
2. Render the appropriate template fragment.
3. Return the fragment with the appropriate status code.
4. Allow HTMX to update the target element.

Example:

```python
return render(
    request,
    "staff/orders/_order_row.html",
    {"order": order},
)
```

Use the template structure appropriate to the actual project.

### 5.3 Full-page fallback

Where practical, forms and actions should remain understandable and usable without relying entirely on JavaScript.

Use progressive enhancement when reasonable.

Do not make critical authorization or validation dependent on HTMX-specific client behavior.

### 5.4 Error responses

Use meaningful HTTP status codes.

Examples:

- `400 Bad Request`: malformed request.
- `401 Unauthorized`: authentication is missing or invalid for a machine API.
- `403 Forbidden`: the authenticated principal lacks permission.
- `404 Not Found`: resource does not exist or is intentionally concealed.
- `405 Method Not Allowed`: unsupported method.
- `409 Conflict`: conflicting state or duplicate operation.
- `422 Unprocessable Content`: may be used for documented validation responses.
- `429 Too Many Requests`: rate limit exceeded.
- `500 Internal Server Error`: unexpected server failure.

For browser forms, use Django's normal form-validation behavior and render useful validation messages.

For HTMX forms, return the appropriate fragment and status code. Ensure the client handles validation errors and server errors consistently.

Do not expose internal stack traces to the browser.

## 6. JSON Response Convention

JSON is used only for endpoints that explicitly require it.

Use a consistent response shape for project-owned JSON APIs.

Successful response example:

```json
{
  "data": {
    "id": "resource-identifier",
    "status": "success"
  }
}
```

Error response example:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request could not be processed.",
    "details": {
      "field": "A useful field-level validation message"
    }
  }
}
```

These examples define a proposed convention, not an existing implementation.

Do not return stack traces, database internals, secrets, or sensitive customer information.

Use appropriate HTTP status codes in addition to the response body.

## 7. Authentication and Authorization

### Browser endpoints

- Use Django authentication and the approved session-based authentication flow.
- Protect state-changing requests with CSRF.
- Enforce authorization in the backend.
- Validate tenant membership and branch access.
- Do not rely on hidden UI elements as an authorization mechanism.

### Machine APIs

If machine APIs are introduced, explicitly define the authentication mechanism for each client.

Do not assume browser session authentication is appropriate for every external integration.

### Public customer endpoints

Customer menu and checkout endpoints may allow unauthenticated customers, but must validate:

- Public menu or QR token.
- Branch and table status.
- Product availability.
- Order input.
- Promotion eligibility.
- Abuse and rate-limiting requirements.

Public access does not imply permission to access internal tenant records.

## 8. CSRF and CORS

For authenticated browser requests:

- Keep Django CSRF protection enabled.
- Ensure HTMX state-changing requests submit valid CSRF tokens.
- Do not disable CSRF globally to fix an individual endpoint.

CORS is only needed when a browser client must access an endpoint across origins.

Do not configure permissive CORS rules without a documented requirement.

Payment provider webhooks use their own documented signature or authentication mechanism; CSRF exemptions must be limited to the necessary endpoint and must not replace provider verification.

## 9. Validation and Data Handling

Validate all external input on the backend.

Use Django Forms or another appropriate validation layer for browser-submitted data.

Validation must cover:

- Required fields.
- Type and format.
- Length and range.
- Tenant and branch ownership.
- Valid state transitions.
- Product and variant availability.
- Price and discount calculations.
- Inventory constraints.
- Permission requirements.

Normalize data where appropriate.

Never trust client-submitted totals, discount amounts, payment status, or stock availability.

Use decimal-safe representations for financial values. Avoid binary floating-point arithmetic for authoritative money calculations.

## 10. Idempotency and Duplicate Requests

Operations that may be retried must not create unintended duplicate effects.

Apply appropriate idempotency or deduplication mechanisms to:

- Checkout retries.
- Payment creation.
- Payment provider webhooks.
- Refund requests and processing.
- Stock reservation.
- Voucher redemption.
- Subscription payment processing.

Use database constraints, transaction boundaries, and durable provider event identifiers where appropriate.

Do not assume that disabling a button in the browser prevents duplicate requests.

For supported payment operations, define the scope and lifetime of idempotency keys explicitly.

## 11. Payment Webhook Convention

Payment webhooks must be handled as external, untrusted input until verified.

Processing requirements:

1. Receive the provider request.
2. Verify its signature or equivalent authenticity mechanism.
3. Validate the provider event and transaction reference.
4. Identify the corresponding internal payment.
5. Handle duplicate event delivery safely.
6. Apply valid state transitions.
7. Persist the result consistently.
8. Trigger downstream effects only when appropriate.
9. Return the response required by the provider's contract.

Additional rules:

- Do not trust browser redirects as proof of payment.
- Do not downgrade a confirmed successful payment because of a stale or duplicate event.
- Do not assume all providers use the same webhook schema.
- Do not expose provider secrets in logs.
- Implement reconciliation for uncertain outcomes when supported by the provider.

Provider-specific behavior must live behind a clearly defined integration boundary.

## 12. Redirects and HTMX Navigation

Use ordinary HTTP redirects for normal browser navigation where appropriate.

For HTMX interactions, use a response strategy compatible with the installed HTMX version and desired navigation behavior.

Do not assume that every redirect response behaves identically in an HTMX request and a normal browser navigation.

Document any shared redirect helper or response convention introduced by the project.

## 13. Pagination, Filtering, and Sorting

List endpoints must validate filtering and sorting inputs.

Rules:

- Apply pagination to potentially large collections.
- Restrict sortable fields to an explicit allowlist.
- Scope results to authorized tenants and branches before returning data.
- Avoid exposing internal fields through arbitrary query parameters.
- Use consistent query parameter names where practical.

Example:

`/owner/orders/?status=PENDING&page=2`

The example is illustrative. Actual parameters should match the implemented view.

## 14. File Uploads

For uploaded files:

- Validate file type and size.
- Generate safe storage names.
- Do not trust the supplied filename or MIME type alone.
- Restrict executable content.
- Apply tenant ownership checks to media access.
- Use approved storage configuration.
- Avoid exposing private media through public URLs unintentionally.

## 15. Rate Limiting and Abuse Prevention

Apply rate limiting where appropriate, particularly for:

- Login and password-related flows.
- Public checkout.
- Promotion redemption.
- QR-accessible endpoints.
- Payment initiation.
- Webhook abuse protection.

Limits must be compatible with legitimate traffic and should be configured based on the endpoint's risk and expected usage.

Rate limiting is not a replacement for authorization or transaction integrity.

## 16. Logging and Observability

Logs should help diagnose failures without exposing secrets or unnecessary personal data.

Where useful, include:

- Request or correlation identifier.
- Endpoint or operation.
- Tenant identifier, when safe and appropriate.
- Relevant resource identifier.
- Outcome and error category.
- Processing duration.

Never log passwords, session secrets, payment credentials, full authorization headers, or unnecessary payment-sensitive data.

Record important financial and administrative actions through appropriate audit mechanisms.

## 17. API Versioning

Do not introduce versioned public APIs without an actual API consumer or compatibility requirement.

If a stable external API is introduced, define its versioning and deprecation policy before release.

Internal Django views and HTMX fragments may evolve with the application, but their template and client dependencies must remain consistent.

## 18. Testing Requirements

Test:

- HTTP methods and status codes.
- Authentication and authorization.
- Tenant and branch isolation.
- CSRF protection.
- Form validation.
- HTMX success and error behavior.
- Duplicate requests.
- Invalid state transitions.
- Payment webhook signature verification.
- Payment event idempotency.
- Rate limits where implemented.
- JSON response contracts for endpoints that expose JSON.

Do not claim an endpoint is secure merely because its UI hides unauthorized actions.

## 19. Definition of Done

An endpoint or integration is complete when:

- Its purpose and response format are clear.
- HTTP methods are appropriate.
- Input validation and authorization are enforced.
- Tenant and branch isolation are preserved.
- Errors are handled consistently.
- Duplicate requests cannot cause unintended effects.
- Relevant tests have been run or unverified areas are reported.
- Documentation reflects the implemented contract.
