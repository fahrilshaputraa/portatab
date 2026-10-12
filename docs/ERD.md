
erDiagram
    %% ==========================================
    %% 1. TENANT, USER, ROLE, ACCESS CONTROL
    %% ==========================================

    TENANTS ||--o{ BRANCHES : owns
    TENANTS ||--o{ MEMBERSHIPS : has
    USERS ||--o{ MEMBERSHIPS : joins
    ROLES ||--o{ MEMBERSHIPS : assigned
    MEMBERSHIPS ||--o{ BRANCH_MEMBERSHIPS : has
    BRANCHES ||--o{ BRANCH_MEMBERSHIPS : grants
    ROLES ||--o{ ROLE_PERMISSIONS : contains
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : assigned

    TENANTS {
        uuid id PK
        varchar name
        varchar slug UK
        varchar email
        varchar phone
        varchar status
        timestamptz created_at
        timestamptz updated_at
    }

    BRANCHES {
        uuid id PK
        uuid tenant_id FK
        varchar name
        varchar code
        text address
        varchar phone
        varchar timezone
        varchar status
        timestamptz created_at
        timestamptz updated_at
    }

    USERS {
        uuid id PK
        varchar name
        varchar email UK
        varchar password_hash
        varchar status
        timestamptz email_verified_at
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }

    ROLES {
        uuid id PK
        uuid tenant_id FK
        varchar name
        varchar code
        boolean is_system
        timestamptz created_at
    }

    PERMISSIONS {
        uuid id PK
        varchar code UK
        varchar description
    }

    ROLE_PERMISSIONS {
        uuid id PK
        uuid role_id FK
        uuid permission_id FK
    }

    MEMBERSHIPS {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        uuid role_id FK
        varchar status
        timestamptz invited_at
        timestamptz joined_at
        timestamptz created_at
    }

    BRANCH_MEMBERSHIPS {
        uuid id PK
        uuid membership_id FK
        uuid branch_id FK
        timestamptz created_at
    }

    %% ==========================================
    %% 2. CUSTOMER IDENTITY (OPTIONAL)
    %% ==========================================

    TENANTS ||--o{ CUSTOMERS : records
    CUSTOMERS ||--o{ CUSTOMER_ADDRESSES : has

    CUSTOMERS {
        uuid id PK
        uuid tenant_id FK
        varchar name
        varchar phone
        varchar email
        varchar status
        timestamptz created_at
    }

    CUSTOMER_ADDRESSES {
        uuid id PK
        uuid customer_id FK
        varchar label
        text address
        varchar notes
        timestamptz created_at
    }

    %% ==========================================
    %% 3. MENU, CATEGORIES, PRODUCTS, VARIANTS
    %% ==========================================

    TENANTS ||--o{ CATEGORIES : defines
    CATEGORIES ||--o{ PRODUCTS : groups
    TENANTS ||--o{ PRODUCTS : owns
    PRODUCTS ||--o{ PRODUCT_VARIANTS : has
    BRANCHES ||--o{ BRANCH_PRODUCTS : offers
    PRODUCTS ||--o{ BRANCH_PRODUCTS : configured_for
    BRANCH_PRODUCTS ||--o{ BRANCH_PRODUCT_VARIANTS : configures
    PRODUCT_VARIANTS ||--o{ BRANCH_PRODUCT_VARIANTS : priced_at

    CATEGORIES {
        uuid id PK
        uuid tenant_id FK
        varchar name
        text description
        int sort_order
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    PRODUCTS {
        uuid id PK
        uuid tenant_id FK
        uuid category_id FK
        varchar name
        text description
        varchar image_url
        varchar status
        int sort_order
        timestamptz created_at
        timestamptz updated_at
    }

    PRODUCT_VARIANTS {
        uuid id PK
        uuid product_id FK
        varchar name
        numeric price_delta
        boolean is_active
        int sort_order
        timestamptz created_at
    }

    BRANCH_PRODUCTS {
        uuid id PK
        uuid branch_id FK
        uuid product_id FK
        numeric price
        int on_hand
        int reserved
        boolean is_available
        boolean track_stock
        timestamptz updated_at
    }

    BRANCH_PRODUCT_VARIANTS {
        uuid id PK
        uuid branch_product_id FK
        uuid variant_id FK
        numeric price_override
        boolean is_available
        timestamptz updated_at
    }

    %% ==========================================
    %% 4. TABLES, QR, TABLE SESSIONS
    %% ==========================================

    BRANCHES ||--o{ TABLES : contains
    TABLES ||--o{ TABLE_SESSIONS : hosts
    CUSTOMERS o|--o{ TABLE_SESSIONS : starts
    TABLE_SESSIONS o|--o{ ORDERS : groups

    TABLES {
        uuid id PK
        uuid branch_id FK
        varchar table_number
        varchar name
        varchar qr_token UK
        varchar status
        timestamptz created_at
        timestamptz updated_at
    }

    TABLE_SESSIONS {
        uuid id PK
        uuid table_id FK
        uuid customer_id FK
        varchar status
        timestamptz started_at
        timestamptz ended_at
    }

    %% ==========================================
    %% 5. ORDERS AND ORDER ITEMS
    %% ==========================================

    BRANCHES ||--o{ ORDERS : receives
    TABLES o|--o{ ORDERS : identifies_table
    CUSTOMERS o|--o{ ORDERS : places
    USERS o|--o{ ORDERS : reviewed_by
    ORDERS ||--|{ ORDER_ITEMS : contains
    PRODUCTS o|--o{ ORDER_ITEMS : references
    PRODUCT_VARIANTS o|--o{ ORDER_ITEMS : selects
    ORDERS ||--o{ ORDER_STATUS_HISTORY : records

    ORDERS {
        uuid id PK
        uuid branch_id FK
        uuid table_id FK
        uuid table_session_id FK
        uuid customer_id FK
        uuid reviewed_by FK
        varchar order_number
        varchar order_status
        varchar payment_status
        varchar order_source
        numeric subtotal
        numeric discount_total
        numeric tax_total
        numeric service_charge
        numeric total
        text customer_note
        boolean is_late
        timestamptz pending_since
        timestamptz late_since
        timestamptz confirmed_at
        timestamptz rejected_at
        varchar rejection_reason
        timestamptz completed_at
        timestamptz created_at
        timestamptz updated_at
    }

    ORDER_ITEMS {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        uuid variant_id FK
        varchar product_name_snapshot
        varchar variant_name_snapshot
        numeric unit_price
        int quantity
        numeric discount_amount
        numeric subtotal
        text notes
        jsonb options_snapshot
        timestamptz created_at
    }

    ORDER_STATUS_HISTORY {
        uuid id PK
        uuid order_id FK
        uuid changed_by FK
        varchar from_status
        varchar to_status
        text reason
        timestamptz created_at
    }

    %% ==========================================
    %% 6. PAYMENTS AND PAYMENT ATTEMPTS
    %% ==========================================

    ORDERS ||--o{ PAYMENTS : has
    PAYMENTS ||--o{ PAYMENT_ATTEMPTS : attempts
    USERS o|--o{ PAYMENTS : confirms_cash

    PAYMENTS {
        uuid id PK
        uuid order_id FK
        uuid confirmed_by FK
        varchar method
        varchar provider
        varchar status
        numeric amount
        varchar currency
        varchar provider_reference
        varchar idempotency_key UK
        timestamptz paid_at
        timestamptz expired_at
        timestamptz created_at
        timestamptz updated_at
    }

    PAYMENT_ATTEMPTS {
        uuid id PK
        uuid payment_id FK
        varchar provider_reference
        varchar status
        text failure_reason
        jsonb provider_response
        timestamptz initiated_at
        timestamptz completed_at
    }

    %% ==========================================
    %% 7. REFUNDS
    %% ==========================================

    PAYMENTS ||--o{ REFUNDS : may_have
    USERS o|--o{ REFUNDS : requests
    USERS o|--o{ REFUNDS : approves

    REFUNDS {
        uuid id PK
        uuid payment_id FK
        uuid requested_by FK
        uuid approved_by FK
        varchar refund_number
        varchar status
        numeric amount
        varchar reason
        varchar provider_reference
        text failure_reason
        timestamptz requested_at
        timestamptz approved_at
        timestamptz completed_at
        timestamptz created_at
    }

    %% ==========================================
    %% 8. INVENTORY AND STOCK MOVEMENTS
    %% ==========================================

    BRANCH_PRODUCTS ||--o{ STOCK_MOVEMENTS : records
    ORDERS o|--o{ STOCK_MOVEMENTS : triggers
    USERS o|--o{ STOCK_MOVEMENTS : performs

    STOCK_MOVEMENTS {
        uuid id PK
        uuid branch_product_id FK
        uuid order_id FK
        uuid created_by FK
        varchar movement_type
        int quantity_delta
        int stock_after
        text reason
        varchar reference_type
        uuid reference_id
        timestamptz created_at
    }

    %% ==========================================
    %% 9. CUSTOMER PROMOTIONS AND VOUCHERS
    %% ==========================================

    TENANTS ||--o{ PROMOTIONS : creates
    PROMOTIONS ||--o{ PROMOTION_REDEMPTIONS : tracks
    ORDERS ||--o{ PROMOTION_REDEMPTIONS : applies
    CUSTOMERS o|--o{ PROMOTION_REDEMPTIONS : redeems

    PROMOTIONS {
        uuid id PK
        uuid tenant_id FK
        varchar code
        varchar name
        varchar discount_type
        numeric discount_value
        numeric min_order_amount
        numeric max_discount_amount
        int total_quota
        int per_customer_limit
        timestamptz starts_at
        timestamptz ends_at
        varchar status
        timestamptz created_at
    }

    PROMOTION_REDEMPTIONS {
        uuid id PK
        uuid promotion_id FK
        uuid order_id FK
        uuid customer_id FK
        numeric discount_amount
        varchar status
        timestamptz redeemed_at
    }

    %% ==========================================
    %% 10. SUBSCRIPTION PLANS AND BILLING
    %% ==========================================

    TENANTS ||--o{ SUBSCRIPTIONS : subscribes
    PLANS ||--o{ SUBSCRIPTIONS : defines
    SUBSCRIPTIONS ||--o{ SUBSCRIPTION_INVOICES : generates
    SUBSCRIPTION_INVOICES ||--o{ SUBSCRIPTION_PAYMENTS : paid_by
    SUBSCRIPTION_VOUCHERS ||--o{ SUBSCRIPTION_VOUCHER_REDEMPTIONS : tracks
    TENANTS ||--o{ SUBSCRIPTION_VOUCHER_REDEMPTIONS : redeems
    SUBSCRIPTIONS ||--o{ SUBSCRIPTION_VOUCHER_REDEMPTIONS : applies

    PLANS {
        uuid id PK
        varchar name
        varchar code UK
        numeric monthly_price
        int max_branches
        int max_accounts
        jsonb features
        varchar status
        timestamptz created_at
    }

    SUBSCRIPTIONS {
        uuid id PK
        uuid tenant_id FK
        uuid plan_id FK
        varchar status
        date current_period_start
        date current_period_end
        timestamptz trial_ends_at
        timestamptz cancelled_at
        timestamptz created_at
        timestamptz updated_at
    }

    SUBSCRIPTION_INVOICES {
        uuid id PK
        uuid subscription_id FK
        varchar invoice_number UK
        numeric normal_amount
        numeric discount_amount
        numeric total_amount
        varchar currency
        varchar status
        jsonb price_snapshot
        timestamptz issued_at
        timestamptz due_at
        timestamptz paid_at
    }

    SUBSCRIPTION_PAYMENTS {
        uuid id PK
        uuid invoice_id FK
        varchar provider
        varchar provider_reference
        numeric amount
        varchar status
        timestamptz paid_at
        timestamptz created_at
    }

    SUBSCRIPTION_VOUCHERS {
        uuid id PK
        varchar code UK
        varchar discount_type
        numeric discount_value
        int duration_months
        int quota
        int redemption_count
        timestamptz valid_from
        timestamptz valid_until
        varchar status
        timestamptz created_at
    }

    SUBSCRIPTION_VOUCHER_REDEMPTIONS {
        uuid id PK
        uuid voucher_id FK
        uuid tenant_id FK
        uuid subscription_id FK
        varchar status
        timestamptz redeemed_at
    }

    %% ==========================================
    %% 11. THEMES AND TEMPLATE PUBLICATIONS
    %% ==========================================

    TENANTS ||--o{ TENANT_THEMES : configures
    THEME_TEMPLATES ||--o{ TENANT_THEMES : uses
    TENANT_THEMES ||--o{ THEME_PUBLICATIONS : publishes
    TENANTS ||--o{ MEDIA_ASSETS : owns

    THEME_TEMPLATES {
        uuid id PK
        varchar template_key UK
        varchar name
        varchar version
        varchar minimum_plan
        varchar status
        jsonb default_configuration
        timestamptz created_at
    }

    TENANT_THEMES {
        uuid id PK
        uuid tenant_id FK
        uuid template_id FK
        jsonb draft_configuration
        varchar status
        timestamptz updated_at
        timestamptz created_at
    }

    THEME_PUBLICATIONS {
        uuid id PK
        uuid tenant_theme_id FK
        int version_number
        jsonb published_configuration
        varchar status
        timestamptz published_at
    }

    MEDIA_ASSETS {
        uuid id PK
        uuid tenant_id FK
        varchar file_url
        varchar media_type
        varchar original_filename
        bigint file_size
        timestamptz created_at
    }

    %% ==========================================
    %% 12. TENANT SETTINGS AND NOTIFICATIONS
    %% ==========================================

    TENANTS ||--o{ TENANT_SETTINGS : configures
    USERS ||--o{ NOTIFICATIONS : receives
    BRANCHES o|--o{ NOTIFICATIONS : scopes
    ORDERS o|--o{ NOTIFICATIONS : references

    TENANT_SETTINGS {
        uuid id PK
        uuid tenant_id FK
        varchar setting_key
        jsonb setting_value
        timestamptz updated_at
    }

    NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        uuid branch_id FK
        uuid order_id FK
        varchar event_type
        varchar title
        text message
        timestamptz read_at
        timestamptz created_at
    }

    %% ==========================================
    %% 13. AUDIT LOGS AND PLATFORM ADMIN
    %% ==========================================

    USERS o|--o{ AUDIT_LOGS : performs
    TENANTS o|--o{ AUDIT_LOGS : scopes
    USERS ||--o{ PLATFORM_ADMIN_MEMBERSHIPS : assigned
    PLATFORM_ADMIN_ROLES ||--o{ PLATFORM_ADMIN_MEMBERSHIPS : grants

    AUDIT_LOGS {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        varchar action
        varchar entity_type
        uuid entity_id
        jsonb before_data
        jsonb after_data
        varchar ip_address
        timestamptz created_at
    }

    PLATFORM_ADMIN_ROLES {
        uuid id PK
        varchar name
        varchar code UK
    }

    PLATFORM_ADMIN_MEMBERSHIPS {
        uuid id PK
        uuid user_id FK
        uuid role_id FK
        varchar status
        timestamptz created_at
    }
