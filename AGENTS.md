
# AGENTS.md — PortaTap

## 1. Project Overview

PortaTap is a multi-tenant SaaS platform for food and beverage businesses.

The platform provides:

- QR-based customer ordering
- Menu and product management
- Multi-branch management
- Cashier and kitchen operations
- Payment processing and refunds
- Branch-level inventory management
- Customer promotions and vouchers
- SaaS subscriptions and billing
- Menu theme customization
- Sales reports
- Platform administration

The initial target market is small Indonesian F&B businesses, including small restaurants, cafes, and modern food stalls.

The product must remain easy to operate while maintaining reliable transaction processing, tenant isolation, and a maintainable architecture.

## 2. Approved Technology Stack

The following stack is approved for PortaTap.

### Backend

- Python
- Django
- Django Templates
- Django ORM
- Django Forms where appropriate
- Django authentication and permissions
- Django migrations
- Django REST Framework only when a genuine API requirement exists

Django is the primary application framework and the source of truth for business logic, authorization, data validation, and database operations.

Do not introduce Django REST Framework solely to reproduce interactions that Django Templates and HTMX can handle directly.

### Frontend

- HTML5
- Django Templates
- HTMX
- CSS
- Tailwind CSS for styling
- Vanilla JavaScript for selective browser interactions
- Alpine.js optionally for small client-side interactions

Django Templates and HTMX are the default approach for application interfaces.

### Database

- PostgreSQL
- Django ORM for normal database operations
- Django migrations for schema changes
- Database transactions and constraints for data integrity

### Asynchronous Processing and Realtime

Introduce these components only when required by the implementation:

- Redis for caching, coordination, or broker functionality
- Celery for background jobs
- Server-Sent Events (SSE) for suitable one-way realtime updates
- Django Channels and WebSockets when bidirectional realtime communication is necessary

Do not add infrastructure without a defined requirement.

## 3. Frontend Architecture Rules

### 3.1 Django Templates First

Use Django Templates for:

- Page layouts
- Navigation and sidebars
- Forms
- Tables
- Dashboards
- Order lists
- Product management
- Customer menu pages
- Kitchen display interfaces
- Subscription and administration pages

Prefer reusable template components and template inheritance.

Use `{% extends %}`, `{% include %}`, and custom template tags when they improve maintainability.

Avoid duplicating the same markup across multiple pages.

### 3.2 HTMX First for Server-Driven Interactions

Use HTMX for interactions that request server-side processing and return updated HTML.

Examples:

- Search and filtering
- Pagination
- Form submissions
- Modal content
- Product CRUD operations
- Order acceptance and rejection
- Order status updates
- Inventory adjustments
- Report filters
- Partial dashboard updates

Prefer returning rendered HTML fragments from Django views when the interaction only needs to update part of the current page.

Use appropriate HTMX attributes such as `hx-get`, `hx-post`, `hx-target`, `hx-swap`, and `hx-trigger`.

Do not create a separate JSON API for every interface interaction.

### 3.3 Selective Vanilla JavaScript

Use vanilla JavaScript when the interaction is primarily local to the browser or requires functionality that HTMX does not handle naturally.

Approved examples:

- Theme color previews
- Local cart interactions when appropriate
- Audio notifications
- Clipboard operations
- Keyboard shortcuts
- Client-side UI enhancements
- Browser event handling
- Integrations with specialized JavaScript libraries

JavaScript must not become a second implementation of backend business logic.

Do not trust browser-side values for authorization, pricing, payment verification, inventory availability, or other security-sensitive decisions.

### 3.4 Alpine.js

Alpine.js is optional.

Use it for small, local UI state when it makes the implementation clearer, such as:

- Dropdown visibility
- Simple tabs
- Lightweight modal state
- Small interactive controls

Do not introduce Alpine.js when a native HTML control or a simple HTMX interaction is sufficient.

Avoid maintaining the same state simultaneously in HTMX, Alpine.js, and custom JavaScript without a clear ownership rule.

### 3.5 Frameworks Not Approved as the Default

Do not introduce the following as the primary frontend architecture:

- React
- Next.js
- A separate React SPA
- A separate frontend application solely to render existing Django pages

A specialized frontend component may be evaluated when a concrete requirement cannot be handled reasonably with Django Templates, HTMX, and selective JavaScript.

Any major architecture change must be explained and approved before implementation.

## 4. Application Architecture

Use a modular Django monolith as the default architecture.

Organize code by business domain rather than placing all business logic in a single application or view module.

Suggested Django applications:

- `accounts`: users, memberships, authentication
- `tenants`: businesses, branches, tenant settings
- `catalog`: categories, products, variants, branch pricing
- `tables`: tables, QR codes, table sessions
- `orders`: orders, order items, status transitions
- `payments`: payment attempts, provider integration, refunds
- `inventory`: stock balances and stock movements
- `promotions`: customer discounts and redemptions
- `subscriptions`: plans, subscriptions, invoices, SaaS vouchers
- `themes`: templates, tenant themes, publications
- `notifications`: notifications and delivery mechanisms
- `reports`: reporting and exports
- `platform_admin`: platform-level administration

This list is a proposed domain boundary, not a requirement to create every application immediately.

Create applications when their responsibilities justify separation.

Keep related models, views, forms, URLs, services, templates, and tests organized within their appropriate domain.

Do not split the system into microservices without a demonstrated need.

## 5. Source of Truth and Documentation

Use these documents as the product and architecture references:

- `docs/PRD.md`: product requirements and acceptance criteria
- `docs/ERD.md`: database entities and relationships
- `docs/ARCHITECTURE.md`: technical architecture
- `docs/BUSINESS-RULES.md`: business rules and state transitions
- `docs/API-CONVENTIONS.md`: API conventions when APIs are introduced

Inspect the existing repository before assuming these files or any particular directory structure exist.

### 5.1 Framework reference — Django 6.1

The backend is built on **Django 6.1**. When unsure how a Django feature behaves, consult the official documentation for that exact version instead of relying on memory or a newer/older release:

- **Django 6.1 documentation (index):** https://docs.djangoproject.com/en/6.1/
- Models and the ORM: https://docs.djangoproject.com/en/6.1/topics/db/models/
- QuerySets and lookups: https://docs.djangoproject.com/en/6.1/ref/models/querysets/
- Migrations: https://docs.djangoproject.com/en/6.1/topics/migrations/
- Forms: https://docs.djangoproject.com/en/6.1/topics/forms/
- Class-based views and URLconfs: https://docs.djangoproject.com/en/6.1/topics/class-based-views/
- Authentication and permissions: https://docs.djangoproject.com/en/6.1/topics/auth/
- Testing: https://docs.djangoproject.com/en/6.1/topics/testing/
- Settings reference: https://docs.djangoproject.com/en/6.1/ref/settings/

Always pin behaviour to the version in `pyproject.toml`; do not assume a feature exists just because a newer documentation build mentions it.

If documentation conflicts with existing code or another approved decision:

1. Identify the conflict.
2. Explain its technical or business impact.
3. Avoid silently changing business behavior.
4. Update the relevant documentation after the decision is resolved.

Do not invent requirements or claim an unapproved architecture is already implemented.

## 6. Multi-Tenant Security

PortaTap serves multiple businesses from a shared application.

Every tenant-owned resource must be protected by server-side authorization.

Rules:

- Validate the authenticated user's tenant membership.
- Validate role and branch access for each protected operation.
- Scope database queries to the authorized tenant and branch.
- Never trust a tenant ID or branch ID supplied by the browser without authorization checks.
- Prevent cross-tenant access through pages, HTMX requests, exports, and background jobs.
- Do not rely on hidden buttons or frontend visibility as a security mechanism.
- Separate platform administrator permissions from tenant owner permissions.
- Apply CSRF protection to authenticated state-changing browser requests.
- Never expose passwords, API keys, payment secrets, or sensitive data in logs.

Use Django authentication and permission mechanisms rather than building a custom authentication system without a compelling requirement.

## 7. Business Logic and Transaction Boundaries

Keep important business rules in backend service functions or other explicit domain-level operations.

Django views should coordinate requests and responses rather than contain large amounts of duplicated transaction logic.

Use database transactions for operations that must succeed or fail together.

Use database constraints and locking where necessary to protect data integrity.

Avoid putting security-sensitive or financial business rules exclusively in templates or JavaScript.

## 8. Order Lifecycle

The standard order statuses are:

- `PENDING`
- `CONFIRMED`
- `PREPARING`
- `READY`
- `COMPLETED`
- `REJECTED`
- `CANCELLED`

Lateness is metadata, not a separate order status.

Order status and payment status must remain separate concepts.

Rules:

- Every customer checkout creates a new order.
- Different checkouts must not be merged into one order merely because they use the same table QR.
- Cashier acceptance and rejection must follow valid state transitions.
- A pending order receives a warning after three minutes.
- An order is marked late after five minutes without cashier action.
- A late order must not be automatically cancelled.
- Digital orders must not be forwarded to the kitchen until payment is verified as paid.
- Cash orders may be forwarded before payment only when the applicable business policy permits it.
- Record important status transitions and timestamps.
- Prevent duplicate submissions from creating unintended duplicate orders.

## 9. Payments and Refunds

Payment statuses are separate from order statuses.

The expected payment statuses include:

- `UNPAID`
- `PENDING`
- `PAID`
- `FAILED`
- `EXPIRED`

Rules:

- Cash is marked paid only after an authorized staff member confirms receipt.
- Digital payments require backend verification from the payment provider.
- Never treat a browser redirect or screenshot as sufficient proof of payment.
- Verify provider webhook authenticity.
- Process duplicate webhook events idempotently.
- Reconcile uncertain payment outcomes before releasing reservations or resolving related orders.
- Preserve payment history when a refund occurs.
- Enforce refund permissions and amount limits.
- Record refund reasons, approvals, provider references, and final outcomes.
- Handle payment retries without accidentally charging or recording the same successful transaction twice.

Use provider-supported payment and refund flows. Do not assume every provider supports identical capabilities.

## 10. Inventory

Inventory is tracked per branch and product.

The conceptual stock fields are:

- `on_hand`
- `reserved`
- `available = on_hand - reserved`

Rules:

- Prevent available stock from becoming negative.
- Reserve stock atomically during checkout.
- Handle concurrent checkout requests safely.
- Release reservations only when the applicable order and payment conditions allow it.
- Do not release reservations while payment status is uncertain.
- Record stock movements with relevant references, timestamps, and actors.
- Do not automatically restore consumed stock without an explicit business rule.
- Keep inventory changes auditable.

## 11. Products and Historical Snapshots

Products may have variants and branch-specific pricing.

Order items must preserve snapshots of transaction-relevant information, including:

- Product name
- Variant name and selected options
- Unit price
- Quantity
- Discount
- Subtotal

Historical transactions must not change when a product name, variant, price, or menu configuration is edited later.

The backend must calculate authoritative prices and discounts.

## 12. Database and Migrations

Use Django ORM for standard application persistence.

Rules:

- All schema changes must be represented by version-controlled Django migrations.
- Never edit production database schemas manually as a substitute for migrations.
- Use foreign keys, unique constraints, check constraints, and indexes where appropriate.
- Use database transactions for multi-step operations requiring consistency.
- Add indexes based on query patterns and measured requirements.
- Avoid destructive migrations without considering existing data.
- Keep model definitions, migrations, ERD, and tests aligned.
- Use timezone-aware datetimes and an explicitly configured timezone.
- Preserve required financial and transaction history.

Do not store relational business data in JSON fields merely to avoid designing an appropriate schema.

Use JSON fields when the data is genuinely flexible, such as theme configuration or provider-specific metadata.

## 13. HTMX and HTTP Conventions

For browser-driven interactions:

- Use appropriate HTTP methods.
- Use POST for state-changing actions.
- Validate and authorize every request on the server.
- Use CSRF protection.
- Return appropriate status codes.
- Return HTML fragments for partial updates where suitable.
- Return complete pages for ordinary navigation.
- Avoid coupling backend logic to the specific frontend fragment being rendered.
- Provide useful validation and error states.
- Prevent duplicate financial operations through server-side idempotency and validation.

HTMX is a communication mechanism, not an authorization or business logic layer.

## 14. UI and UX Standards

The interface must be simple, consistent, responsive, and accessible.

Prioritize:

- Clear visual hierarchy
- Obvious primary actions
- Readable order and payment statuses
- Consistent navigation
- Useful loading states
- Empty states
- Validation errors
- Success and failure feedback
- Mobile-friendly customer ordering
- Keyboard accessibility
- Clear confirmation for destructive or financial actions

Avoid unnecessary frontend complexity and excessive abstraction.

Use reusable Django template components and consistent styling conventions.

## 15. Realtime and Notifications

Use the simplest reliable mechanism that satisfies the requirement.

- Use HTMX polling for suitable low-complexity updates.
- Consider SSE for one-way server-to-browser events.
- Use WebSockets when bidirectional or low-latency communication justifies them.
- Use background jobs for tasks that should not block ordinary requests.

Notification processing must handle reconnects and duplicate events safely.

Browser sound notifications may require an initial user interaction to enable audio.

Do not play a kitchen notification for a digital order before its payment has been verified.

## 16. Subscription and Voucher Rules

Keep PortaTap subscription billing separate from customer food-order promotions.

Subscription records belong to tenants, not individual staff accounts.

Rules:

- Preserve invoice price and discount snapshots.
- Historical invoices must not change when a plan's price changes.
- Validate voucher eligibility, quota, validity, and redemption limits on the backend.
- Prevent duplicate or unauthorized voucher redemption.
- Keep subscription lifecycle separate from tenant operational status.
- Enforce plan limits on the backend.

## 17. Theme Customization

Tenant menu themes support configurable templates and visual settings.

Rules:

- Store theme drafts separately from published configuration.
- Publishing a theme must create a traceable publication version.
- Editing a draft must not unintentionally alter the current published theme.
- Validate configuration and template compatibility.
- Enforce subscription-plan restrictions on the backend.
- Do not execute arbitrary HTML or JavaScript uploaded by a tenant or stored in a database.
- Treat templates as controlled application code.
- Preserve compatibility with tenants using existing published templates.

Use JavaScript selectively for local live previews and interactions that benefit from immediate browser feedback.

## 18. Testing Requirements

Write or update tests for the behavior being changed.

Prioritize tests for:

- Tenant and branch authorization
- Authentication and permissions
- Order state transitions
- Payment verification and webhook idempotency
- Concurrent stock reservations
- Refund permissions and amount limits
- Subscription and voucher eligibility
- Theme draft and publication behavior
- HTMX form validation and response behavior
- Migration safety where relevant

Use the testing conventions already established in the repository.

Do not claim that tests pass unless they have been executed and verified.

Report tests that were not run and any known limitations.

## 19. Coding Workflow

### 19.0 Mandatory: no duplicate logic (always-on skill)

The `no-duplicate-logic` skill (`.commandcode/skills/no-duplicate-logic/`) is **always in
effect** for any work that creates or changes code. Its rules are mandatory, not optional:

- Never create a function, method, service, component, or helper that re-implements logic that
  already exists elsewhere. Duplication by **logic** is forbidden, not just duplication by name
  (e.g. do not add `user_pembelian` / `admin_pembelian` when a `pembelian` function exists —
  reuse and parameterize it).
- Search for existing implementations (grep `services/`, `selectors/`, `utils/`, `models.py`,
  `forms.py`) **before** writing anything new.
- Consolidate duplicated logic into one source of truth when you encounter it.
- Delete code that becomes unused; do not keep dead code, alias unused names, or add
  single-use abstractions.
- Run the skill's mandatory self-check before declaring any coding task done.

Before implementation:

1. Inspect the existing repository and relevant code.
2. Read applicable requirements and business rules.
3. Identify affected Django applications, models, views, templates, and tests.
4. Check whether existing components can be reused (see section 19.0).
5. Identify security, financial, and data-integrity implications.

During implementation:

1. Make the smallest coherent change.
2. Follow established coding conventions.
3. Keep business logic centralized.
4. Use HTMX before introducing unnecessary client-side state.
5. Use vanilla JavaScript selectively.
6. Add dependencies only when justified.
7. Update migrations and documentation when required.

After implementation:

1. Run relevant tests.
2. Run applicable formatting, linting, and build checks.
3. Review authorization and data-integrity implications.
4. Summarize changed files and behavior.
5. Report verification results and remaining risks honestly.

Do not perform broad refactors unrelated to the requested change.

## 20. Definition of Done

A change is complete when:

- The requested behavior matches approved requirements.
- Tenant isolation and permissions are preserved.
- Relevant tests pass, or unverified areas are explicitly reported.
- Migrations are included when schema changes are required.
- Documentation is updated when architecture or business rules change.
- No secrets or sensitive production data are introduced.
- The implementation does not introduce unnecessary frameworks or infrastructure.
- Known limitations and operational risks are documented.

## 21. Final Architecture Principle

PortaTap uses a Django-centered, server-rendered architecture.

Default interaction model:

Django Templates + HTMX + CSS

Selective enhancement:

Vanilla JavaScript, with Alpine.js optional.

Persistence:

Django ORM + PostgreSQL.

Background processing and realtime infrastructure must be introduced only when justified by actual requirements.

Prefer a coherent, secure, maintainable modular monolith over premature frontend separation or microservices.

All implementation decisions must support reliable transactions, strict tenant isolation, simple operations, and sustainable development by a small team.
