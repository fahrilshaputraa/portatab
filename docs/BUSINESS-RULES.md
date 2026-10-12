
# PortaTap — Business Rules

**Status:** Approved baseline for MVP
**Scope:** Tenant operations, ordering, payments, inventory, promotions, subscriptions, and themes

## 1. General Principles

1. PortaTap serves multiple businesses through a shared SaaS platform.
2. A tenant represents one subscribed business.
3. A tenant may operate multiple branches.
4. Every tenant-owned operation must enforce tenant and branch authorization.
5. Financial transactions must preserve historical records.
6. The backend is the source of truth for pricing, authorization, payment status, inventory, and order transitions.
7. Frontend validation is supplementary and never replaces backend validation.

## 2. Tenant and Membership Rules

- A user may belong to multiple tenants.
- Each tenant membership has an assigned role and status.
- Branch access is determined by explicit branch membership or another approved access policy.
- A user must not access a tenant or branch solely by changing a URL, form field, or request parameter.
- Platform administrators have separate platform-level permissions.
- A platform administrator is not automatically the owner of a tenant.
- Subscription status and tenant operational status are separate concepts.

Recommended membership states:

- `INVITED`
- `ACTIVE`
- `SUSPENDED`
- `REVOKED`

Implementation must enforce valid membership transitions.

## 3. Branch Rules

- Every branch belongs to exactly one tenant.
- Products, tables, orders, and inventory must be associated with the correct branch.
- A branch must not reference a product owned by another tenant.
- A disabled branch must not accept new orders.
- Historical transactions must remain available according to retention and access policies.
- Cross-branch reporting is available only to authorized users.

## 4. Product and Pricing Rules

- Products belong to a tenant.
- Products may be available in multiple branches.
- Branches may have different product prices and availability.
- Product variants represent selectable product options.
- The backend calculates the final authoritative product price.
- A product's current price does not change historical order items.
- Each order item stores a snapshot of product name, variant, unit price, quantity, discount, and subtotal.
- Unavailable or inactive products must not be added to a new order.
- Price and availability must be validated again at checkout.
- A product cannot be sold at a branch unless the product is authorized for that branch.

For a variant with a price delta:

`Final unit price = branch product price + variant price delta`

If explicit branch-specific variant pricing is implemented, the agreed override rule takes precedence.

The final price must never be accepted solely from a browser-submitted amount.

## 5. Table and QR Rules

- Each table belongs to one branch.
- A QR token identifies an intended table and branch.
- QR tokens do not grant access to owner or staff dashboards.
- A disabled table must not accept new orders.
- QR token rotation must invalidate the old token according to the implemented policy.
- A customer may place multiple independent orders using the same table QR.
- Each checkout creates a new order.
- A table session may group orders belonging to one visit, but does not merge their payment records.
- Table session expiration and reopening behavior must follow an explicitly configured policy.

## 6. Checkout Rules

At checkout, the backend must:

1. Validate the branch and table.
2. Validate product and variant availability.
3. Recalculate prices and applicable discounts.
4. Validate promotion eligibility.
5. Validate stock availability where stock tracking is enabled.
6. Calculate the final order amount.
7. Create a new order and order-item snapshots.
8. Reserve stock atomically where stock reservation is required.
9. Create the appropriate payment record or payment flow.
10. Return the confirmed result to the client.

A failed checkout must not leave partial orders, duplicate reservations, or inconsistent financial records.

Repeated client submissions must not accidentally create duplicate orders when the same logical request is retried. Use an appropriate idempotency strategy where necessary.

## 7. Order Status Rules

The standard order statuses are:

- `PENDING`
- `CONFIRMED`
- `PREPARING`
- `READY`
- `COMPLETED`
- `REJECTED`
- `CANCELLED`

Recommended normal transitions:

```text
PENDING --> CONFIRMED
PENDING --> REJECTED
PENDING --> CANCELLED

CONFIRMED --> PREPARING
CONFIRMED --> CANCELLED

PREPARING --> READY

READY --> COMPLETED
```

Any additional transition must be explicitly defined, authorized, and tested.

Invalid transitions must be rejected by the backend.

Each important transition should record:

- Previous status.
- New status.
- Actor, if applicable.
- Timestamp.
- Reason, when applicable.

### Cashier decision

- Cashier acceptance is required before a normal pending order enters the kitchen workflow.
- Cashier rejection must record a reason where appropriate.
- A late order remains pending until an authorized decision is made.
- Late status is metadata, not an independent order status.

### Cashier response timers

- At three minutes without cashier action, issue a warning.
- At five minutes, mark the order as late.
- Do not automatically cancel an order because the cashier did not respond.
- Use server-side time as the authoritative source.
- Notification processing must avoid duplicate warnings.

## 8. Payment Rules

Payment status and order status are separate.

Standard payment statuses:

- `UNPAID`
- `PENDING`
- `PAID`
- `FAILED`
- `EXPIRED`

A payment attempt is distinct from the overall order.

### Cash payments

- Cash is marked paid only after an authorized staff member confirms receipt.
- The amount received must be reconciled against the required amount.
- A cashier must not be able to confirm payment for an unauthorized branch.
- Duplicate confirmation must not create duplicate financial effects.

### Digital payments

- Digital payment success must be verified by the backend using trusted provider information.
- Browser redirects, screenshots, and customer claims are not sufficient evidence.
- Provider webhook signatures or equivalent verification mechanisms must be checked.
- Duplicate provider events must be handled idempotently.
- Out-of-order events must not incorrectly downgrade a successful payment.
- Uncertain payment outcomes must be reconciled before making unsafe inventory or order decisions.

### Kitchen eligibility

- A digital order must not be forwarded to the kitchen until its payment is verified as `PAID`.
- A cash order may be forwarded before payment only when the tenant's approved payment policy permits it.
- Kitchen notifications must follow the same eligibility rules.
- Payment verification and kitchen forwarding must not rely solely on client-side state.

## 9. Rejection and Cancellation Rules

- Rejecting an unpaid order does not create a refund.
- A successful digital payment followed by order rejection requires a refund case.
- If payment status is uncertain, reconcile the provider outcome before resolving the case.
- Stock reservations may be released only when doing so is safe under the payment and preparation state.
- An order that has started preparation must not automatically restore consumed stock.
- Cancellation and rejection reasons should be recorded.
- Financial history must not be deleted to simplify cancellation handling.

## 10. Refund Rules

Refund statuses:

- `REQUESTED`
- `APPROVED`
- `PROCESSING`
- `SUCCEEDED`
- `FAILED`
- `REJECTED`
- `CANCELLED`

Rules:

- Customers request refunds through the cashier or authorized staff workflow in the MVP.
- Refunds are managed centrally through the staff dashboard.
- Refund permissions and approval limits must be enforced on the backend.
- Every refund must reference the original payment.
- A refund must not exceed the refundable amount.
- Pending or in-progress refunds must be accounted for when calculating remaining refundable balance.
- Multiple concurrent refund requests must not exceed the permitted total.
- Cash refunds are marked successful only after the cash is actually returned.
- Digital refunds must follow the payment provider's supported process.
- A refund failure must remain visible for follow-up.
- A successful original payment remains historically `PAID` after a refund.
- Refund completion and order completion are separate concepts.

The initial MVP should prioritize full refunds. Partial refunds require explicit amount validation and appropriate reporting.

The exact refund approval threshold must be configured as an approved business policy.

## 11. Inventory Rules

Inventory is managed per branch and product.

Conceptual fields:

- `on_hand`: physical stock currently recorded.
- `reserved`: stock reserved for eligible orders.
- `available`: `on_hand - reserved`.

Rules:

- Stock quantities must not become negative.
- Reservation must be atomic under concurrent checkout.
- The same order must not reserve the same stock twice.
- A valid rejection or cancellation may release a reservation when payment status is safe.
- When preparation begins, the approved stock-consumption policy must be applied consistently.
- Consumed stock must not be automatically restored without an explicit rule.
- Every stock adjustment must create an auditable stock movement.
- Manual stock changes require an authorized actor and a reason.
- Product stock tracking may be disabled for products that do not use inventory tracking.

Reservation expiration is not assumed. Its duration and reconciliation policy must be explicitly approved before production.

## 12. Customer Promotions

Customer promotions apply to food and beverage orders.

Supported promotion types may include:

- Fixed amount discount.
- Percentage discount.
- Minimum order amount.
- Maximum discount.
- Validity window.
- Usage quota.
- Per-customer usage limit.
- Branch restrictions.
- Product or category restrictions.

Rules:

- Promotion eligibility must be calculated on the backend.
- The backend determines the final discount amount.
- Redemption must be recorded against the applicable order.
- Quota consumption must be safe under concurrent requests.
- Duplicate redemption must be prevented.
- Promotion validity and limits must be checked at checkout.
- Promotion stacking must follow an explicit policy.
- The initial MVP should not stack multiple promotions unless specifically approved.

Customer promotions must not be confused with PortaTap subscription vouchers.

## 13. Subscription and SaaS Voucher Rules

- A subscription belongs to a tenant.
- A tenant's subscription determines its permitted plan features and limits.
- Subscription status is separate from tenant operational status.
- Invoice records preserve the price, discount, currency, and billing-period snapshot.
- Plan price changes must not alter historical invoices.
- SaaS voucher redemption must validate eligibility, validity, quota, and usage limits.
- Voucher redemption must be atomic where concurrent redemption is possible.
- Subscription payment records are separate from customer order payments.

Subscription states may include:

- `TRIALING`
- `ACTIVE`
- `PAST_DUE`
- `CANCELLED`
- `EXPIRED`

The grace period and post-expiration restrictions must be explicitly configured.

## 14. Theme and Template Rules

- Each tenant has a default menu theme.
- Theme configuration must be validated before publication.
- Draft changes must not unintentionally alter the currently published theme.
- Published themes should have traceable versions.
- Template eligibility must be checked against the tenant's subscription plan.
- Deactivating a template must not silently break existing published themes.
- Tenant-provided content must be escaped or sanitized appropriately.
- Arbitrary user-provided HTML or JavaScript must not be executed.
- Custom UI services must have explicitly agreed scope rather than implying unlimited custom development.

## 15. Notifications

Required notification events include:

- New order received by the cashier.
- Three-minute cashier warning.
- Five-minute late-order alert.
- Eligible order entering the kitchen.
- Order ready for service.

Rules:

- Notifications must not be emitted for unauthorized tenant or branch recipients.
- Duplicate processing must not generate unintended duplicate effects.
- Notification delivery failure must not silently invalidate a committed order.
- Browser audio is an enhancement, not the only notification mechanism.
- Kitchen notifications must follow payment eligibility rules.

Use durable event delivery or an outbox when required to prevent lost important notifications.

## 16. Reporting Rules

Reports must distinguish:

- Gross order value.
- Discounts.
- Net order value.
- Payment collected.
- Unpaid orders.
- Successful refunds.
- Cancelled and rejected orders.
- Product sales.
- Stock movements.
- Promotion redemptions.

Unpaid orders must not be counted as collected cash.

The definition of net sales must be consistent across reports. The initial proposal is completed order value after discounts, adjusted for successful refunds, with other accounting adjustments explicitly defined if required.

Reports must respect tenant and branch permissions.

## 17. Audit and Data Retention

Record important actions involving:

- Permissions and memberships.
- Order state changes.
- Payment confirmation.
- Refund approval and completion.
- Stock adjustments.
- Subscription changes.
- Voucher redemption.
- Theme publication.
- Platform administration.

Audit records must not expose secrets or unnecessary sensitive customer information.

Data retention, deletion, and privacy requirements must follow an explicitly approved policy and applicable regulations.

## 18. Conflict Resolution

When an implementation request conflicts with an established rule:

1. Identify the conflict.
2. Explain the effect on data integrity, security, money, or operations.
3. Do not silently weaken the existing rule.
4. Request a product decision when the requirement is ambiguous.
5. Update this document and relevant tests when the rule changes.

## 19. Production Readiness Decisions

The following decisions must be finalized before the corresponding production functionality is enabled:

- Payment provider and supported payment methods.
- Payment expiration and reconciliation policy.
- Refund approval thresholds.
- Stock reservation expiration.
- Subscription grace period and expiration behavior.
- Promotion stacking and redemption rules.
- Branch-specific variant pricing.
- Data retention and privacy policy.
- Load and performance targets.
- Recovery procedures for payment and inventory inconsistencies.
