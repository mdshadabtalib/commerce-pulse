# MASTER BUILD PROMPT

## Production-Grade E-Commerce Intelligence & Sales Forecasting Platform

You are a senior software architect, data engineer, data analyst, ML
engineer, DevOps engineer, cybersecurity engineer, and product engineer
working together.

Build a production-ready, commercially deployable E-Commerce
Intelligence & Sales Forecasting Platform from the ground up.

This is NOT a college demo, prototype, mockup, or static dashboard.

The final system must be designed as a real-world SaaS/product that can
be deployed to production and used by actual businesses.

Do not take shortcuts. Do not use fake functionality. Do not leave
critical features as TODOs, placeholders, mock APIs, hardcoded results,
or simulated backend responses.

When a requirement is technically ambiguous, choose the most
production-appropriate approach, document the decision, and implement it
consistently.

------------------------------------------------------------------------

# 1. PRODUCT VISION

Build a multi-user business intelligence platform that allows e-commerce
businesses to connect/import their sales data and obtain actionable
insights about:

-   Revenue
-   Profit
-   Orders
-   Products
-   Customers
-   Customer segments
-   Customer lifetime value
-   RFM analysis
-   Sales trends
-   Product performance
-   Category performance
-   Geographic performance
-   Discounts
-   Returns
-   Inventory-related indicators
-   Sales forecasting
-   Anomaly detection
-   Business KPIs
-   Automated reports
-   Actionable recommendations

The system should transform raw business data into:

DATA → CLEANING → STORAGE → ANALYSIS → ML → VISUALIZATION → INSIGHTS →
BUSINESS ACTIONS

------------------------------------------------------------------------

# 2. PRIMARY USERS

Design the application around multiple roles.

## Organization Owner

Can: - Create/manage organization - Invite employees - Manage billing -
Manage integrations - Manage organization settings - Access all
analytics - Manage permissions

## Admin

Can: - Manage users - Manage datasets - Manage integrations - Manage
dashboards - Manage reports - Access analytics

## Analyst

Can: - Import datasets - Run analyses - Create dashboards - Generate
reports - Configure metrics - Explore data

## Viewer

Can: - View permitted dashboards - View reports - View permitted
analytics

Implement proper RBAC.

Never rely only on frontend authorization. Every sensitive permission
must also be enforced server-side.

------------------------------------------------------------------------

# 3. MULTI-TENANCY

The application must support multiple businesses/organizations.

Organization A must never be able to access Organization B's: -
Customers - Orders - Products - Dashboards - Reports - Files - API
credentials - Analytics

Every organization-owned database record must have appropriate
tenant/organization ownership.

Implement tenant isolation at the application and database/query level.

Never trust an organization ID supplied directly by the frontend.

Derive organization context from the authenticated user's
permissions/session/token.

Add automated tests specifically designed to detect cross-tenant data
leakage.

------------------------------------------------------------------------

# 4. CORE TECHNOLOGY STACK

Use a modern, maintainable production architecture.

## Frontend

Use: - Next.js - TypeScript - React - Tailwind CSS - shadcn/ui or an
equivalent accessible component system - Recharts/ECharts for
visualization - React Query/TanStack Query where appropriate - Zod for
frontend validation

Build a responsive interface for desktop, tablet, and mobile. Desktop is
the primary analytics experience.

## Backend

Use: - Python - FastAPI - Pydantic - SQLAlchemy - Alembic

Structure the backend using clear separation between: - API -
Authentication - Authorization - Business logic - Data access -
Analytics - ML - Background jobs - Integrations

Do not place the entire application inside one huge file.

## Database

Use PostgreSQL.

Design a normalized transactional schema with appropriate indexes and
constraints.

Use migrations through Alembic.

Do not manually modify production schemas.

## Cache / background processing

Use: - Redis - Celery or an equivalent reliable background job system

Long-running operations must not block HTTP requests.

Examples: - Dataset processing - Large CSV imports - Forecast
generation - Report generation - Scheduled analytics - Email delivery -
Integration synchronization

## Object storage

Use S3-compatible object storage for: - Uploaded datasets - Generated
reports - Export files - Other large objects

Do not store large files directly inside PostgreSQL.

------------------------------------------------------------------------

# 5. ARCHITECTURE

Use a modular architecture similar to:

Frontend ↓ API Gateway / Reverse Proxy ↓ FastAPI Backend ↓ Service Layer
↓ PostgreSQL Redis Object Storage Background Workers ↓ Analytics / ML
Pipeline ↓ Dashboard/API visualization layer

The system must be horizontally scalable.

Avoid unnecessary microservices initially.

Prefer a modular monolith + workers architecture unless there is a clear
reason to split services.

The architecture must allow future extraction of services without
rewriting the entire application.

------------------------------------------------------------------------

# 6. AUTHENTICATION

Implement secure authentication.

Support: - Email/password registration - Login - Logout - Email
verification - Password reset - Password change - Session/token
management - Optional MFA architecture - Secure session expiration -
Refresh token rotation where applicable

Passwords must NEVER be stored in plaintext.

Use a modern password hashing algorithm such as Argon2id.

Implement: - Rate limiting - Login brute-force protection - Secure
cookies where applicable - CSRF protection where applicable - Secure
token handling - Session invalidation

Do not store authentication tokens in insecure browser storage
unnecessarily.

------------------------------------------------------------------------

# 7. SECURITY

Treat security as a first-class requirement.

Protect against: - SQL injection - XSS - CSRF - SSRF - Broken access
control - IDOR - Authentication bypass - Privilege escalation - File
upload attacks - Malicious CSV/XLSX content - Path traversal - Command
injection - Credential leakage - Sensitive data exposure - Rate-limit
abuse - Mass assignment - Unsafe deserialization

Never construct SQL using unsafe string concatenation.

Validate all user input.

Validate uploaded files by: - Extension - MIME type - File signature
where appropriate - Size - Schema - Content

Do not blindly execute uploaded content.

Never expose database credentials, API secrets, encryption keys,
internal stack traces, password reset tokens, or private integration
credentials in API responses or frontend code.

------------------------------------------------------------------------

# 8. DATA MODEL

Design appropriate entities including, where applicable:

-   User
-   Organization
-   OrganizationMember
-   Role
-   Permission
-   Customer
-   Product
-   Category
-   Order
-   OrderItem
-   Payment
-   Refund
-   Return
-   Address
-   Dataset
-   DatasetColumn
-   ImportJob
-   Dashboard
-   DashboardWidget
-   SavedReport
-   Forecast
-   ForecastRun
-   Anomaly
-   CustomerSegment
-   Integration
-   APIKey
-   AuditLog
-   Notification
-   Subscription
-   UsageRecord

Use: - Primary keys - Foreign keys - Unique constraints - Check
constraints - Proper indexes - Created/updated timestamps - Soft
deletion only where appropriate

Do not blindly use soft deletion for every entity.

------------------------------------------------------------------------

# 9. DATA INGESTION

The platform must support importing data from:

Phase 1: - CSV - Excel/XLSX - JSON

Architecture for future integrations: - Shopify - WooCommerce - Amazon -
Razorpay - Stripe - Google Analytics - Meta Ads - Other e-commerce
platforms

Do not claim an integration works unless it actually works.

For every import: 1. Upload file 2. Validate file 3. Detect schema 4.
Detect columns 5. Identify data types 6. Detect missing values 7. Detect
duplicates 8. Detect invalid records 9. Show validation report 10. Allow
mapping 11. Import valid data 12. Record invalid rows 13. Generate
import summary 14. Store import history

Never silently discard bad records.

------------------------------------------------------------------------

# 10. DATA QUALITY ENGINE

Build a reusable data quality layer.

Detect: - Missing values - Duplicate records - Invalid dates - Negative
quantities - Invalid prices - Impossible discounts - Invalid customer
IDs - Invalid product IDs - Currency inconsistencies - Outliers -
Referential integrity problems

Provide a data quality score.

Example: Data Quality Score: 94% Completeness: 97% Validity: 95%
Consistency: 92% Uniqueness: 99%

Allow users to inspect errors.

------------------------------------------------------------------------

# 11. ETL / ELT PIPELINE

Build reliable processing pipelines.

Pipeline:

Raw Data ↓ Validation ↓ Normalization ↓ Cleaning ↓ Transformation ↓
Business Rules ↓ Database ↓ Analytics Tables ↓ ML Features

Make processing: - Repeatable - Idempotent - Observable - Retryable

A failed job must not corrupt existing data.

Use transactions where appropriate.

Do not duplicate records when the same dataset is accidentally processed
twice.

------------------------------------------------------------------------

# 12. ANALYTICS ENGINE

Implement reusable analytics services.

## Sales KPIs

Calculate: - Gross revenue - Net revenue - Profit - Profit margin -
Orders - Units sold - Average order value - Average selling price -
Discount amount - Return rate - Refund amount - Growth rate

Support: - Daily - Weekly - Monthly - Quarterly - Yearly

comparison.

------------------------------------------------------------------------

# 13. SALES ANALYTICS

Provide: - Revenue trends - Profit trends - Order trends - Units sold -
Category performance - Product performance - Geographic performance -
Payment method analysis - Discount analysis - Return analysis

Support filters: - Date range - Product - Category - Brand - Location -
Customer segment - Order status

All dashboard filters must update dependent visualizations correctly.

------------------------------------------------------------------------

# 14. CUSTOMER ANALYTICS

Calculate: - New customers - Returning customers - Repeat purchase
rate - Average customer spend - Purchase frequency - Customer lifetime
value - Retention - Cohort analysis

Implement customer cohorts based on first purchase date.

------------------------------------------------------------------------

# 15. RFM SEGMENTATION

Implement: - Recency - Frequency - Monetary

Calculate appropriate scores.

Create configurable customer segments such as: - Champions - Loyal
Customers - Potential Loyalists - New Customers - Promising - At Risk -
Can't Lose Them - Hibernating - Lost

Do not hardcode arbitrary thresholds without documenting them.

Allow segmentation configuration to evolve.

Display: - Customer count - Revenue contribution - Average order value -
Purchase frequency - Recommended action

------------------------------------------------------------------------

# 16. PRODUCT ANALYTICS

Identify: - Best-selling products - Most profitable products -
Lowest-performing products - High-revenue/low-profit products -
Low-revenue/high-margin products - Products with high return rates -
Products heavily dependent on discounts

Create a product profitability matrix.

------------------------------------------------------------------------

# 17. INVENTORY ANALYTICS

Where inventory data exists, support: - Current inventory - Stock
turnover - Days of inventory - Stock-out indicators - Slow-moving
products - Fast-moving products - Inventory value

If inventory data is unavailable, clearly label these features as
unavailable instead of inventing values.

------------------------------------------------------------------------

# 18. GEOGRAPHIC ANALYTICS

Analyze performance by: - Country - State - City - Region

Provide: - Revenue - Profit - Orders - Customers - AOV

Use map visualizations only when geographic data quality is sufficient.

------------------------------------------------------------------------

# 19. SALES FORECASTING

Implement a forecasting pipeline.

Start with strong baselines: - Naive forecast - Moving average -
Seasonal naive

Then evaluate more advanced models where sufficient data exists: -
Exponential smoothing - ARIMA/SARIMA - Prophet - Gradient boosting /
XGBoost

Do not automatically use complex ML if a simpler model performs better.

Forecast: - Revenue - Orders - Units sold

Support: - 7-day - 30-day - 60-day - 90-day

forecasts where enough historical data exists.

------------------------------------------------------------------------

# 20. FORECAST VALIDATION

Never present a forecast without evaluating it.

Use time-series appropriate validation.

Calculate metrics such as: - MAE - RMSE - MAPE/SMAPE where appropriate

Compare candidate models.

Store: - Model - Training period - Validation period - Parameters -
Metrics - Data version - Prediction horizon

Display forecast confidence/uncertainty intervals where supported.

Clearly distinguish Actual vs Forecast.

Never present predictions as guaranteed future results.

------------------------------------------------------------------------

# 21. ANOMALY DETECTION

Detect unusual: - Revenue drops - Revenue spikes - Order spikes -
Product sales changes - Unusual refunds - Unusual discounts - Unusual
customer behavior

Use appropriate statistical/ML techniques.

Each anomaly should include: - Metric - Timestamp - Severity - Expected
value - Actual value - Detection method - Explanation

Do not fabricate anomaly explanations.

------------------------------------------------------------------------

# 22. BUSINESS INSIGHTS ENGINE

Do not simply display charts.

Generate actionable insights from calculated metrics.

Every generated insight must be based on actual calculated data.

Clearly distinguish: - Observed fact - Statistical relationship -
Hypothesis - Recommendation

Do not claim causation when the data only shows correlation.

------------------------------------------------------------------------

# 23. DASHBOARD

Build a premium analytics dashboard.

Main navigation: - Overview - Sales - Customers - Products - Inventory -
Forecasting - Anomalies - Reports - Data - Integrations - Settings

Dashboard should contain: - KPI cards - Trend charts - Tables -
Filters - Drilldowns - Comparison periods - Tooltips - Export
functionality

Avoid excessive visual clutter.

Currency must be configurable.

Do not hardcode INR.

Support architecture for: - INR - USD - EUR - GBP

------------------------------------------------------------------------

# 24. REPORTING

Allow users to generate: - PDF reports - CSV exports - Excel exports

Reports should include: - Date range - KPIs - Charts - Key insights -
Forecasts - Anomalies - Data quality warnings

Implement background report generation for large reports.

------------------------------------------------------------------------

# 25. SCHEDULED REPORTS

Allow organization admins to configure scheduled reports.

Examples: - Every Monday at 9 AM - Monthly business report - Daily sales
summary - Weekly anomaly report

Send reports through configurable email infrastructure.

Do not send emails directly from web requests if the operation can be
queued.

------------------------------------------------------------------------

# 26. ALERTING

Allow users to create alerts such as: - Notify me if revenue falls below
a threshold - Notify me if refunds exceed a threshold - Notify me if
sales fall significantly below forecast

Support: - Email - In-app notifications

Design the notification architecture so additional channels can be added
later.

------------------------------------------------------------------------

# 27. SEARCH AND FILTERING

Provide fast global filtering.

Users should be able to filter analytics by: - Date - Product -
Category - Customer - Location - Order status - Segment

Do not fetch entire datasets into the browser just to perform filtering.

Use server-side querying for large datasets.

------------------------------------------------------------------------

# 28. PERFORMANCE

Design for large datasets.

The system should remain usable when an organization has: - 100K
orders - 1M orders - 10M+ order records

Avoid: - N+1 queries - Unbounded API responses - Full-table scans where
avoidable - Browser-side processing of huge datasets - Unnecessary
database queries

Implement: - Pagination - Indexing - Aggregation - Caching - Query
optimization - Background jobs - Materialized views or analytical tables
where appropriate

Measure query performance.

------------------------------------------------------------------------

# 29. API DESIGN

Build documented REST APIs.

Use: - Versioning - Consistent response structures - Pagination -
Filtering - Sorting - Validation - Proper HTTP status codes - Error
handling

Generate OpenAPI documentation.

Never expose internal database implementation unnecessarily.

------------------------------------------------------------------------

# 30. API SECURITY

Implement: - Authentication - Authorization - Rate limiting - API key
management - Key rotation/revocation - Request validation - Audit
logging

API keys must be shown only when created and stored securely.

Do not store raw secrets unnecessarily.

------------------------------------------------------------------------

# 31. AUDIT LOGGING

Record security-sensitive actions.

Examples: - Login - Logout - Password change - User invitation - Role
change - Dataset upload - Dataset deletion - Integration creation - API
key creation - Report generation - Organization settings changes

Store: - User - Organization - Action - Timestamp - Relevant resource -
Request metadata where appropriate

Do not log passwords, tokens, API secrets, or sensitive credentials.

------------------------------------------------------------------------

# 32. OBSERVABILITY

Implement: - Structured logging - Error tracking - Application metrics -
Health checks - Background-job monitoring - Database monitoring -
Request timing

Provide health endpoints such as: - /health - /ready

Distinguish: - Application healthy - Database unavailable - Redis
unavailable - Worker unavailable

Do not expose sensitive diagnostic information publicly.

------------------------------------------------------------------------

# 33. ERROR HANDLING

Every API must have consistent error responses.

Example:

{ "error": { "code": "INVALID_DATASET", "message": "The uploaded dataset
contains invalid date values.", "request_id": "..." } }

Never expose raw stack traces to users.

Generate request IDs for troubleshooting.

------------------------------------------------------------------------

# 34. FRONTEND UX

The application should feel like a professional SaaS product.

Include: - Loading states - Empty states - Error states - Skeleton
loaders - Confirmation dialogs - Toast notifications - Accessible
forms - Keyboard navigation - Responsive layouts

Never show a blank screen when data is unavailable.

Explain errors in human-readable language.

------------------------------------------------------------------------

# 35. ACCESSIBILITY

Follow modern accessibility practices.

Target WCAG 2.2 AA where practical.

Ensure: - Keyboard navigation - Proper labels - Sufficient contrast -
Screen-reader-friendly controls - Accessible charts where possible -
Focus states - Semantic HTML

------------------------------------------------------------------------

# 36. DATA PRIVACY

Treat customer/business data as sensitive.

Implement: - Data minimization - Encryption in transit - Encryption at
rest where supported - Secure backups - Access controls - Data deletion
workflows - Export workflows - Audit logging

Design the system so privacy requirements can be adapted to applicable
jurisdictions.

Do not claim legal compliance with GDPR, India's DPDP Act, HIPAA, PCI
DSS, or any other framework unless the actual implementation and
organizational processes satisfy the relevant requirements.

------------------------------------------------------------------------

# 37. DATA RETENTION

Provide configurable retention architecture.

Support deletion/export workflows.

When deleting an organization: - Confirm intent - Protect against
accidental deletion - Process deletion safely - Remove associated data
according to retention policy - Record appropriate audit events

Do not immediately hard-delete critical production data without
safeguards.

------------------------------------------------------------------------

# 38. BACKUPS AND RECOVERY

Design: - Automated database backups - Backup retention - Restore
procedures - Disaster recovery documentation

Define realistic: - RPO - RTO

Test restoration procedures.

A backup that has never been restored/tested must not be considered
reliable.

------------------------------------------------------------------------

# 39. PAYMENTS / SUBSCRIPTIONS

If monetization is implemented, design subscription architecture for: -
Free/trial - Starter - Professional - Enterprise

Track: - Subscription - Plan - Usage - Billing status - Limits

Do not implement fake payment processing.

If using a payment provider, use its official production APIs and
webhook verification.

Never trust payment status sent from the frontend.

------------------------------------------------------------------------

# 40. USAGE LIMITS

Support plan-based limits such as: - Number of users - Dataset size -
Number of imports - Data retention - Report generation - API requests -
Forecast runs

Enforce limits server-side.

------------------------------------------------------------------------

# 41. IMPORT IDEMPOTENCY

A user accidentally uploading the same file twice must not silently
duplicate business data.

Implement: - File hashing - Import IDs - External IDs where available -
Idempotency keys - Duplicate detection

Provide clear import status.

------------------------------------------------------------------------

# 42. TESTING

Testing is mandatory.

## Unit Tests

For: - Analytics calculations - Revenue calculations - Profit
calculations - RFM calculations - Forecast metrics - Validation -
Business rules

## Integration Tests

For: - Database - Authentication - Imports - APIs - Background jobs -
Tenant isolation

## End-to-End Tests

Test critical flows:

Register → Verify → Login → Create Organization → Upload Dataset →
Validate → Import → View Dashboard → Generate Forecast → Generate Report

Also test: - Unauthorized access - Cross-tenant access - Invalid
uploads - Duplicate imports - Failed jobs - Expired sessions -
Permission restrictions

Do not declare production readiness while critical tests are failing.

------------------------------------------------------------------------

# 43. SECURITY TESTING

Include automated tests for: - IDOR - Authentication bypass -
Authorization bypass - SQL injection - XSS - CSRF - File upload
vulnerabilities - Rate limiting - Tenant isolation

Use dependency vulnerability scanning.

Keep dependencies updated.

------------------------------------------------------------------------

# 44. CI/CD

Create CI/CD pipelines.

Every pull request should run:

Lint ↓ Type checking ↓ Unit tests ↓ Integration tests ↓ Security checks
↓ Build

Production deployment should require successful checks.

Do not automatically deploy untested code to production.

------------------------------------------------------------------------

# 45. ENVIRONMENT MANAGEMENT

Provide separate: - Development - Testing - Staging - Production

Never commit: - Passwords - API keys - Database credentials - Secret
keys - OAuth secrets - Encryption keys

Provide a safe .env.example.

------------------------------------------------------------------------

# 46. DATABASE MIGRATIONS

All schema changes must use migrations.

Never require manually editing production tables.

Test migrations both: - Upgrade - Rollback where appropriate

------------------------------------------------------------------------

# 47. DOCKERIZATION

Provide production-ready Docker configuration.

Include: - Frontend container - Backend container - Worker container -
PostgreSQL - Redis

For development, provide Docker Compose.

Use non-root containers where practical.

Keep images minimal.

------------------------------------------------------------------------

# 48. DEPLOYMENT

Provide deployment documentation for a realistic production environment.

Document: - DNS - HTTPS - Environment variables - Database - Redis -
Object storage - Worker - Reverse proxy - Logging - Backups -
Monitoring - Scaling - Rollback

Use HTTPS in production.

Configure secure headers.

------------------------------------------------------------------------

# 49. DATABASE OPTIMIZATION

Analyze query plans for important analytics queries.

Add indexes based on actual access patterns.

Avoid blindly indexing every column.

For high-volume analytics, consider: - Aggregation tables - Materialized
views - Partitioning - Read replicas - Caching

Only introduce complexity when justified.

------------------------------------------------------------------------

# 50. ML MODEL GOVERNANCE

Every ML model must record: - Model type - Version - Training data
period - Feature set - Training timestamp - Validation metrics -
Hyperparameters - Prediction horizon

Avoid silent model changes.

If a new model performs worse, do not automatically replace the
production model.

------------------------------------------------------------------------

# 51. ML FAILURE HANDLING

If there is insufficient data for forecasting:

Do NOT generate fake predictions.

Instead display:

Forecast unavailable.

At least the required amount of historical data is needed for a reliable
forecast.

Similarly, if customer segmentation cannot be meaningfully calculated,
explain why.

The application must prefer honest absence of results over fabricated
intelligence.

------------------------------------------------------------------------

# 52. DATA VISUALIZATION PRINCIPLES

Charts must be meaningful.

Avoid: - 3D charts - Excessive decoration - Misleading axes -
Unnecessary pie charts - Inconsistent scales

Provide: - Clear labels - Units - Date ranges - Comparison periods -
Tooltips - Legends

Every important visualization should answer a business question.

------------------------------------------------------------------------

# 53. INTERNATIONALIZATION

Design for future support of: - Multiple currencies - Time zones - Date
formats - Number formats - Languages

Never assume: - INR - India Standard Time - DD/MM/YYYY

throughout the codebase.

Use organization-level configuration.

------------------------------------------------------------------------

# 54. API DOCUMENTATION

Generate complete API documentation.

For every endpoint document: - Purpose - Authentication - Permissions -
Request - Response - Validation - Errors - Example

------------------------------------------------------------------------

# 55. PROJECT STRUCTURE

Use a clean repository structure similar to:

ecommerce-intelligence/ ├── frontend/ ├── backend/ ├── worker/ ├──
analytics/ ├── ml/ ├── infrastructure/ ├── database/ ├── tests/ ├──
docs/ ├── scripts/ ├── docker/ ├── .github/ ├── .env.example ├──
docker-compose.yml ├── README.md └── LICENSE

Adapt the structure where a better architecture is justified.

Do not create unnecessary folders simply to make the project appear
sophisticated.

------------------------------------------------------------------------

# 56. DOCUMENTATION

Create professional documentation covering: - Product overview -
Architecture - Installation - Environment setup - Database setup -
Migrations - Development - Testing - Deployment - Production
configuration - Security - Data model - API - Analytics methodology -
Forecasting methodology - Troubleshooting - Backup and recovery -
Contribution guidelines

------------------------------------------------------------------------

# 57. SAMPLE DATA

Provide a realistic synthetic dataset for development/testing.

It should contain enough records to demonstrate: - Seasonality - Repeat
customers - Product differences - Discounts - Returns - Geographic
variation - Customer segments - Trends - Outliers

Clearly mark it as synthetic.

Never present synthetic results as real business data.

------------------------------------------------------------------------

# 58. DEMO MODE

Create an optional demo organization containing synthetic data.

The demo must be isolated from production customer data.

Demo mode must never expose real credentials or production information.

------------------------------------------------------------------------

# 59. ADMINISTRATION

Build an admin interface for: - Users - Organizations - Imports - Jobs -
System health - Plans - Usage - Audit logs - Feature flags

Protect administrative functionality with strict permissions.

------------------------------------------------------------------------

# 60. FEATURE FLAGS

Design a feature-flag system for safely enabling/disabling: - New
analytics - Forecasting models - Integrations - Beta features

Do not hardcode feature availability throughout the application.

------------------------------------------------------------------------

# 61. BUSINESS METRIC DEFINITIONS

Create a centralized metric-definition layer.

For example: - Revenue - Profit - AOV - Customer Lifetime Value -
Retention - Churn - Return Rate - Profit Margin

Every metric must have a documented definition.

This prevents the frontend, SQL queries, and ML pipeline from
calculating the same KPI differently.

------------------------------------------------------------------------

# 62. CRITICAL BUSINESS RULE

Never hide data problems.

If the input data is incomplete or unreliable:

1.  Detect it.
2.  Explain it.
3.  Quantify the impact where possible.
4.  Warn the user.
5.  Avoid presenting misleading analytics.

Data quality must take priority over attractive dashboards.

------------------------------------------------------------------------

# 63. FINAL QUALITY GATE

Before considering the project complete, perform a production-readiness
review.

## Functional

-   Authentication works
-   Authorization works
-   RBAC works
-   Multi-tenancy works
-   Imports work
-   Analytics work
-   Dashboards work
-   Forecasting works
-   Reports work
-   Notifications work
-   Exports work

## Security

-   No known critical vulnerabilities
-   No secrets committed
-   Tenant isolation verified
-   Authorization tested
-   File uploads secured
-   Rate limiting enabled
-   Secure headers configured

## Reliability

-   Background jobs retry safely
-   Failed imports do not corrupt data
-   Database backups exist
-   Restore process documented
-   Monitoring exists
-   Error tracking exists

## Performance

-   Large datasets tested
-   Slow queries identified
-   Important queries indexed
-   Pagination implemented
-   Dashboard response times measured

## Data/ML

-   Metrics validated
-   Forecasting validated
-   Model performance recorded
-   Insufficient-data cases handled
-   No fabricated predictions
-   Anomalies explain their basis

## Deployment

-   Production environment documented
-   HTTPS configured
-   Environment variables documented
-   Database migrations tested
-   Docker build works
-   CI/CD works
-   Rollback procedure documented

------------------------------------------------------------------------

# 64. DEFINITION OF DONE

Do NOT say "Project completed" until all of the following are true:

1.  Application builds successfully.
2.  Frontend runs successfully.
3.  Backend runs successfully.
4.  Database migrations execute successfully.
5.  Authentication works.
6.  RBAC works.
7.  Tenant isolation has automated tests.
8.  Dataset import works.
9.  Data validation works.
10. Core analytics are mathematically verified.
11. Dashboard uses real backend data.
12. Forecasting uses actual historical data.
13. Forecast accuracy is evaluated.
14. Reports work.
15. Background jobs work.
16. Error handling works.
17. Security tests pass.
18. CI pipeline passes.
19. Production Docker configuration works.
20. Documentation is complete.
21. No critical TODOs remain.
22. No fake/mock production functionality remains.
23. No credentials or secrets are committed.
24. Production deployment procedure is documented.
25. Backup and recovery procedures are documented.

If any critical item fails, explicitly report it as incomplete.

------------------------------------------------------------------------

# 65. DEVELOPMENT PROCESS

Follow this implementation order:

Phase 1 --- Architecture + repository + development environment

Phase 2 --- Authentication + organizations + RBAC + multi-tenancy

Phase 3 --- Database schema + migrations

Phase 4 --- Data ingestion + validation + ETL

Phase 5 --- Core analytics engine

Phase 6 --- Dashboard

Phase 7 --- Customer/RFM analytics

Phase 8 --- Product/profitability analytics

Phase 9 --- Forecasting

Phase 10 --- Anomaly detection

Phase 11 --- Reports + exports + alerts

Phase 12 --- Integrations

Phase 13 --- Billing/subscriptions

Phase 14 --- Security hardening

Phase 15 --- Testing + performance testing

Phase 16 --- Observability + deployment

Phase 17 --- Production-readiness audit

Do not attempt to implement everything blindly in one step.

After each phase: 1. Implement. 2. Run tests. 3. Inspect failures. 4.
Fix failures. 5. Review architecture. 6. Update documentation. 7.
Continue only when the phase is stable.

------------------------------------------------------------------------

# 66. IMPORTANT IMPLEMENTATION RULES

-   Do not fabricate APIs.
-   Do not fabricate ML results.
-   Do not fabricate analytics.
-   Do not hardcode business metrics.
-   Do not use placeholder buttons for core functionality.
-   Do not silently ignore errors.
-   Do not skip validation.
-   Do not expose secrets.
-   Do not trust frontend authorization.
-   Do not assume input data is clean.
-   Do not use mock data in production paths.
-   Do not claim an integration is complete unless it works.
-   Do not claim regulatory compliance without verification.
-   Do not optimize prematurely.
-   Do not introduce microservices without a real architectural reason.
-   Do not sacrifice security for development speed.
-   Do not sacrifice data correctness for visual appearance.

------------------------------------------------------------------------

# 67. OUTPUT EXPECTATION

At the end of development, provide:

1.  Complete source code
2.  Database schema
3.  Database migrations
4.  API documentation
5.  Frontend application
6.  Backend application
7.  Worker/ETL system
8.  Analytics engine
9.  ML/forecasting pipeline
10. Tests
11. Docker configuration
12. CI/CD configuration
13. Environment example
14. Synthetic dataset
15. Production deployment guide
16. Security documentation
17. Architecture documentation
18. Backup/recovery documentation
19. Troubleshooting guide
20. Professional README

The README must explain: - What the platform does - Key features -
Architecture - Technology stack - Screenshots/placeholders for
screenshots - Local setup - Environment variables - Database setup -
Running tests - Deployment - Security - Analytics methodology -
Forecasting methodology

------------------------------------------------------------------------

# 68. FINAL INSTRUCTION

Build this as a real product, not as a tutorial project.

Prioritize:

Correctness \> Security \> Reliability \> Maintainability \> Performance
\> UX \> Visual polish

The system should be capable of evolving from a small deployment into a
scalable SaaS platform.

Whenever a shortcut would compromise correctness, security, data
integrity, or production reliability, do not take the shortcut.

If a requirement cannot safely or realistically be implemented with the
selected architecture, stop and explain the technical constraint before
implementing an unsafe workaround.

At every stage, ask:

"Would I trust this system with a real company's business data?"

If the answer is no, improve the implementation before proceeding.
