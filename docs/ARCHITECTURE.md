
# PortaTap — Architecture

**Status:** Approved baseline for MVP
**Backend:** Django
**Frontend:** Django Templates + HTMX
**Database:** PostgreSQL
**Architecture style:** Modular monolith

## 1. Purpose

This document defines the technical architecture of PortaTap.

PortaTap is a multi-tenant SaaS platform for food and beverage businesses. It supports QR ordering, menu management, cashier operations, kitchen workflows, payments, inventory, subscriptions, and menu customization.

The architecture prioritizes:

- Maintainability for a small development team.
- Secure tenant and branch isolation.
- Reliable financial and inventory transactions.
- Fast delivery of business features.
- Minimal unnecessary infrastructure.
- A clear path for future scaling.

## 2. Approved Technology Stack

### Backend

- Python
- Django
- Django ORM
- Django Templates
- Django Forms
- Django authentication and permissions
- Django migrations

Django is the primary application framework and source of truth for business logic.

Django REST Framework may be introduced for specific machine-readable API requirements, but it is not required for ordinary server-rendered pages or HTMX interactions.

### Frontend

- HTML5
- Django Templates
- HTMX
- CSS
- Tailwind CSS
- Vanilla JavaScript for selective browser interactions
- Alpine.js optionally for lightweight local UI state

React and Next.js are not part of the approved default architecture.

### Database

- PostgreSQL
- Django ORM for application persistence
- Database constraints and transactions for data integrity

### Optional Infrastructure

- Redis for caching, coordination, or background-job brokering.
- Celery for asynchronous processing.
- SSE for suitable one-way realtime updates.
- Django Channels and WebSockets when bidirectional realtime communication is justified.
- Object storage for uploaded product images and other media when required.

Optional infrastructure must not be introduced without a concrete use case.

## 3. High-Level Architecture

```text
Users
  |
  v
Web Browser
  |
  | HTTP / HTTPS
  | HTMX requests
  v
Django Application
  |
  +-- Authentication and Authorization
  |
  +-- Django Views and Forms
  |
  +-- Domain Services
  |
  +-- Django Templates
  |
  +-- Integration Adapters
  |     +-- Payment Provider
  |     +-- Email / Notifications
  |     +-- Object Storage
  |
  v
PostgreSQL

Optional:
Django Application --> Redis --> Celery Workers
Django Application --> SSE / Django Channels
```

The Django application renders HTML and handles business operations. HTMX requests update specific page fragments without requiring a separate frontend application.

## 4. Application Architecture

PortaTap uses a modular monolith.

A modular monolith is one deployable application organized into distinct business domains. It does not require each domain to run as a separate service.

Suggested Django applications:

| Application    | Responsibility                                       |
| -------------- | ---------------------------------------------------- |
| accounts       | User identity, memberships, invitations              |
| tenants        | Businesses, branches, tenant settings                |
| catalog        | Categories, products, variants, branch pricing       |
| tables         | Tables, QR tokens, table sessions                    |
| orders         | Orders, order items, order state transitions         |
| payments       | Payment attempts, provider integration, refunds      |
| inventory      | Stock balances and stock movements                   |
| promotions     | Customer promotions and redemptions                  |
| subscriptions  | Plans, subscriptions, invoices, SaaS vouchers        |
| themes         | Theme configuration, template registry, publications |
| notifications  | Notification events and delivery                     |
| reports        | Sales reports and exports                            |
| platform_admin | Platform-level administration                        |

Create applications incrementally as their responsibilities become necessary. Do not create empty applications merely to match this list.

## 5. Request Lifecycle

### 5.1 Normal page request

1. The browser sends an HTTP request.
2. Django resolves the URL.
3. Authentication and authorization are checked.
4. The view calls the appropriate domain service when business operations are required.
5. The application reads or updates PostgreSQL.
6. Django renders a template.
7. The browser receives the HTML response.

### 5.2 HTMX request

1. The browser initiates an HTMX request.
2. Django authenticates and authorizes the request.
3. Django validates the input.
4. Domain services execute the operation.
5. PostgreSQL changes are committed when successful.
6. Django returns an HTML fragment or an appropriate error response.
7. HTMX updates the designated target element.

Business logic must not depend on whether the request originated from a full-page form or HTMX.

### 5.3 External API request

For payment providers or other machine clients:

1. Receive and validate the request.
2. Authenticate the caller or verify the provider signature.
3. Validate payloads and identifiers.
4. Process the operation idempotently where required.
5. Persist the result.
6. Return the documented response format.

Do not expose internal business operations as public APIs unless there is a real requirement.

## 6. Frontend Strategy

### Django Templates

Use templates for page layouts, forms, navigation, tables, dashboards, customer menus, and operational interfaces.

Use template inheritance and reusable components to avoid duplicated markup.

### HTMX

Use HTMX for server-driven interactions, including:

- Search and filtering.
- Pagination.
- CRUD forms.
- Modal content.
- Order acceptance and rejection.
- Inventory adjustments.
- Partial dashboard refreshes.
- Report filters.

Prefer HTML fragment responses when only part of the current page must change.

### Vanilla JavaScript

Use JavaScript for local browser behavior, including:

- Theme previews.
- Audio notifications.
- Clipboard operations.
- Keyboard interactions.
- Specialized UI libraries.
- Browser APIs that cannot be handled naturally by HTMX.

JavaScript is not the authority for financial calculations, permissions, inventory validation, or order state transitions.

### Alpine.js

Alpine.js is optional for simple local interactions such as dropdowns, tabs, and modal visibility.

Do not introduce multiple state-management mechanisms for the same interaction without a clear reason.

## 7. Domain and Service Boundaries

Keep HTTP concerns separate from business operations.

Recommended responsibility split:

- Models: persistence, relationships, and suitable database-level validation.
- Views: request handling, authorization orchestration, and response rendering.
- Forms: user input validation and normalization.
- Domain services: business operations and state transitions.
- Selectors or query functions: reusable read queries when useful.
- Integration adapters: payment providers and other external systems.
- Templates: presentation only.
- Background tasks: operations that must run asynchronously.

Do not place complex payment, order, or inventory logic directly in templates or large view functions.

Do not introduce repository or service abstractions automatically when Django ORM and a focused service function are sufficient.

## 8. Multi-Tenant Data Model

A tenant represents one subscribed business.

A branch belongs to a tenant.

Users may belong to multiple tenants through memberships. Memberships determine tenant-level roles, while branch memberships determine which branches a user can access.

Tenant-owned records must be associated with the correct tenant directly or through a clearly defined relationship.

Rules:

- Validate tenant membership on every protected operation.
- Validate branch access for branch-scoped operations.
- Scope queries to authorized tenant and branch identifiers.
- Never treat a tenant ID supplied by the browser as proof of authorization.
- Enforce important uniqueness rules within the correct tenant or branch scope.
- Apply the same authorization rules to background jobs, exports, and external integrations.

Database row-level security may be considered as additional defense, but it does not replace application-level authorization.

## 9. Database and Transactions

PostgreSQL is the primary database.

Use Django migrations for schema changes.

Use database constraints for invariants that should remain true regardless of which application path performs a write.

Use `transaction.atomic()` for operations that require all-or-nothing persistence.

Use row locking or other appropriate concurrency controls for critical operations such as stock reservation and payment-related state transitions.

Avoid holding database transactions open while waiting for slow external HTTP calls.

When external side effects are required, persist the internal operation first where appropriate, then process the external action with retry and reconciliation mechanisms.

Use a transactional outbox when reliable delivery of important events becomes necessary.

## 10. Order, Payment, and Inventory Boundaries

Order status and payment status are separate.

A payment provider callback must not directly bypass order validation.

Digital orders may proceed to the kitchen only after backend verification confirms successful payment.

Inventory reservation and release must be atomic and must account for uncertain payment outcomes.

Store transaction snapshots for product names, variants, prices, quantities, and discounts.

Preserve historical payment and refund records.

Financial operations must be idempotent where retries could otherwise create duplicate effects.

## 11. Realtime and Background Processing

Start with ordinary HTTP requests and HTMX where they meet the requirement.

For updates that do not require instant delivery, polling may be sufficient.

Use SSE for appropriate one-way server-to-browser notifications.

Use Django Channels and WebSockets when bidirectional or lower-latency communication justifies the operational complexity.

Use Celery when jobs need asynchronous execution, retries, or independent workers.

Examples include:

- Sending emails.
- Processing background reports.
- Retrying notification delivery.
- Handling reconciliation tasks.
- Performing scheduled subscription operations.

Do not assume Redis, Celery, SSE, or WebSockets must all be installed for the initial MVP.

## 12. Security

- Enforce server-side authentication and authorization.
- Protect authenticated browser mutations with CSRF.
- Validate external input.
- Keep secrets outside source control.
- Verify payment-provider signatures.
- Prevent cross-tenant data access.
- Use secure cookie and HTTPS settings in production.
- Avoid exposing sensitive information in logs.
- Rate-limit sensitive endpoints where appropriate.
- Apply safe file-upload validation.
- Do not execute arbitrary user-provided HTML or JavaScript.

## 13. Observability

Use structured application logs where practical.

Record enough information to diagnose failed transactions without logging passwords, tokens, payment secrets, or unnecessary customer data.

Monitor:

- Application errors.
- Request latency.
- Database performance.
- Failed payment processing.
- Background-job failures.
- Notification delivery.
- Inventory consistency.
- Subscription billing failures.

Use correlation identifiers where useful for tracing a transaction across application logs and background processing.

## 14. Testing

Tests should cover:

- Domain business rules.
- Tenant and branch authorization.
- Order state transitions.
- Payment verification and idempotency.
- Concurrent inventory changes.
- Refund authorization and limits.
- Subscription and voucher rules.
- Template and HTMX interactions.
- Database constraints.
- Integration failure handling.

Use the testing conventions established by the repository. Pytest and pytest-django may be used if adopted by the project.

## 15. Deployment

The initial deployment may use a single Django application deployment with PostgreSQL.

Use a production-capable WSGI or ASGI server as appropriate.

Serve static files through an appropriate production static-file strategy or CDN.

Use separate processes for background workers only when background processing is introduced.

Keep development, testing, and production settings separate.

Do not use Django's development server as the production application server.

## 16. Architecture Evolution

Prefer the simplest architecture that satisfies current requirements.

Consider introducing additional infrastructure only when justified by measured limitations, security requirements, operational needs, or a new product capability.

Potential future improvements include:

- Dedicated worker processes.
- Object storage.
- Read replicas.
- Dedicated realtime infrastructure.
- Additional API interfaces.
- Specialized frontend components.
- Service separation when independent scaling or ownership becomes necessary.

Do not introduce microservices or a separate React frontend solely in anticipation of hypothetical future requirements.

## 17. Definition of Done

An architectural change is complete when:

- Responsibilities remain clearly separated.
- Security and tenant isolation are preserved.
- Database integrity is maintained.
- Relevant tests pass or unverified areas are documented.
- Architecture documentation reflects approved changes.
- New dependencies and infrastructure have a clear justification.
