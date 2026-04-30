<div align="center">

# ✦ LUXORA BACKEND ✦

### Enterprise-Grade E-Commerce & Multi-Vendor Marketplace API

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Redis](https://img.shields.io/badge/Redis-7+-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Stripe](https://img.shields.io/badge/Stripe-Payments-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://stripe.com)
[![Firebase](https://img.shields.io/badge/Firebase-FCM-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)

---

```
╔══════════════════════════════════════════════════════════════╗
║   156 Python Files   ·   29,442 Lines of Code                ║
║   600 Functions      ·   237 Classes   ·   911 Imports       ║
║   22 API Modules     ·   31 Database Models                  ║
╚══════════════════════════════════════════════════════════════╝
```

*Built by the **Luxora Engineering Team** · April 30, 2026*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Database Models](#-database-models)
- [API Modules Reference](#-api-modules-reference)
- [Security System](#-security-system)
- [Core Infrastructure](#-core-infrastructure)
- [Configuration & Environment Variables](#-configuration--environment-variables)
- [Getting Started](#-getting-started)
- [Running the Application](#-running-the-application)
- [Database Migrations](#-database-migrations)
- [API Documentation](#-api-documentation)
- [Background Jobs](#-background-jobs)
- [File Storage](#-file-storage)
- [Email Service](#-email-service)
- [Push Notifications](#-push-notifications-firebase-fcm)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🌐 Overview

**Luxora Backend** is a production-ready, enterprise-grade RESTful API backend powering a full-featured multi-vendor e-commerce marketplace platform. Built on top of **FastAPI** with a clean **Domain-Driven Design (DDD)** architecture, it supports multi-role users (customers, vendors, admins), complete product lifecycle management, integrated payment processing, real-time push notifications, automated invoice generation, and sophisticated security mechanisms.

### Key Capabilities

| Category | Features |
|---|---|
| **Multi-Role Auth** | Customer, Vendor, Admin with OTP verification & JWT sessions |
| **Product Management** | Variants, Attributes, Images, Inventory Tracking |
| **Order Lifecycle** | Checkout → Payment → Fulfillment → Timeline Tracking |
| **Payments** | Stripe integration with Webhooks & Refund handling |
| **Vendor Ecosystem** | Vendor onboarding, approval workflow, analytics dashboard |
| **Security** | Brute-force detection, Rate limiting, Security headers, RBAC |
| **Notifications** | Firebase FCM push + Email notifications with HTML templates |
| **Invoicing** | Auto-generated PDF invoices via ReportLab |
| **Caching** | Redis-backed caching & session management |
| **Background Jobs** | Scheduled order auto-updates & notification cleanup |

---

## 🏗 Architecture

Luxora Backend follows a strict **layered / Domain-Driven Design** architecture to enforce separation of concerns and testability:

```
┌─────────────────────────────────────────────────────┐
│                  CLIENT / FRONTEND                   │
└─────────────────┬───────────────────────────────────┘
                  │  HTTP Request
┌─────────────────▼───────────────────────────────────┐
│               FASTAPI APPLICATION                    │
│   ┌─────────────────────────────────────────────┐   │
│   │  Middleware Stack                           │   │
│   │  • CORS  • RateLimit  • SecurityHeaders     │   │
│   └─────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────┐   │
│   │  API Layer  (app/api/v1/)                   │   │
│   │  Routes → Schema Validation → Deps inject  │   │
│   └──────────────────┬──────────────────────────┘   │
│                      │                               │
│   ┌──────────────────▼──────────────────────────┐   │
│   │  Domain / Service Layer  (app/domains/)     │   │
│   │  Business Logic · Auth · Order · Payments  │   │
│   └──────────────────┬──────────────────────────┘   │
│                      │                               │
│   ┌──────────────────▼──────────────────────────┐   │
│   │  Repository Layer  (app/domains/*/repo.py)  │   │
│   │  Data Access · SQLAlchemy ORM Queries       │   │
│   └──────────────────┬──────────────────────────┘   │
│                      │                               │
│   ┌──────────────────▼──────────────────────────┐   │
│   │  Infrastructure  (app/infrastructure/)      │   │
│   │  DB · Redis · Firebase · Email · Invoice    │   │
│   └──────────────────┬──────────────────────────┘   │
└─────────────────────┬───────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
   ┌─────▼──────┐          ┌──────▼─────┐
   │   MySQL    │          │   Redis    │
   │  Database  │          │   Cache    │
   └────────────┘          └────────────┘
```

**Request Flow:**
```
HTTP Request → Middleware → Router → Dependency Injection
    → Service Layer (business logic)
        → Repository (data access)
            → Database / Redis
                → Response serialized via Pydantic schema
```

---

## 📁 Project Structure

```
luxora-backend/
│
├── app/
│   ├── main.py                        # FastAPI application entry point
│   │
│   ├── api/
│   │   ├── deps.py                    # Shared dependencies (get_db)
│   │   ├── deps_auth.py               # Auth dependencies (get_current_user)
│   │   ├── router.py                  # Root router aggregator
│   │   │
│   │   ├── v1/                        # Version 1 API
│   │   │   ├── api.py                 # V1 router with all sub-routers
│   │   │   ├── addresses/             # Address management
│   │   │   ├── admin/                 # Admin operations
│   │   │   ├── analytics/             # Platform analytics (admin)
│   │   │   ├── attributes/            # Product attributes & variants
│   │   │   ├── auth/                  # Authentication & authorization
│   │   │   ├── brands/                # Brand management
│   │   │   ├── cart/                  # Shopping cart
│   │   │   ├── categories/            # Product categories (tree)
│   │   │   ├── coupons/               # Discount coupons
│   │   │   ├── customers/             # Customer profiles
│   │   │   ├── inventory/             # Inventory management
│   │   │   ├── invoice/               # PDF invoice generation
│   │   │   ├── notifications/         # Push & in-app notifications
│   │   │   ├── orders/                # Order lifecycle
│   │   │   ├── payments/              # Stripe payments
│   │   │   ├── products/              # Product catalog
│   │   │   ├── refunds/               # Refund processing
│   │   │   ├── returns/               # Return management
│   │   │   ├── reviews/               # Product reviews
│   │   │   ├── search/                # Product search
│   │   │   ├── users/                 # User profile & sessions
│   │   │   ├── vendor_analytics/      # Vendor-specific analytics
│   │   │   ├── vendors/               # Vendor management
│   │   │   └── wishlist/              # Wishlist
│   │   │
│   │   └── v2/                        # Version 2 API (scaffolded)
│   │       └── api.py
│   │
│   ├── core/
│   │   ├── admin_guard.py             # Admin route protection
│   │   ├── attack_detector.py         # Brute-force attack detection
│   │   ├── cache.py                   # Cache abstraction layer
│   │   ├── config.py                  # Pydantic Settings (env vars)
│   │   ├── exceptions.py              # Custom exception classes
│   │   ├── log_config.py              # Logging configuration
│   │   ├── logger.py                  # Structured event logger
│   │   ├── permissions.py             # RBAC permission system
│   │   ├── rate_limiter.py            # Redis-backed rate limiting
│   │   ├── security.py                # JWT generation & verification
│   │   ├── security_headers_middleware.py  # HTTP security headers
│   │   ├── storage.py                 # File storage utility
│   │   └── vendor_dependency.py       # Vendor auth dependency
│   │
│   ├── domains/                       # Business domain logic
│   │   ├── Wishlist/                  # repository.py + service.py
│   │   ├── addresses/
│   │   ├── admin/                     # + activity_service.py
│   │   ├── attributes/
│   │   ├── auth/                      # + login_history_service.py
│   │   │                              # + otp_service.py
│   │   │                              # + session_service.py
│   │   ├── brands/
│   │   ├── cart/
│   │   ├── categories/
│   │   ├── coupons/
│   │   ├── customers/
│   │   ├── inventory/
│   │   ├── invoice/
│   │   ├── notifications/
│   │   ├── orders/
│   │   ├── payments/
│   │   ├── products/
│   │   ├── reviews/
│   │   ├── search/
│   │   ├── users/
│   │   ├── vendor_analytics/
│   │   └── vendors/
│   │
│   ├── infrastructure/
│   │   ├── cleanup/
│   │   │   └── notification_cleanup.py   # Auto-deletes old notifications
│   │   ├── database/
│   │   │   ├── base.py                   # SQLAlchemy declarative base
│   │   │   └── session.py                # DB session factory (SessionLocal)
│   │   ├── email/
│   │   │   ├── renderer.py               # Jinja2 HTML email renderer
│   │   │   ├── service.py                # SMTP email service
│   │   │   └── templates/                # HTML email templates
│   │   ├── firebase/
│   │   │   ├── __init__.py
│   │   │   └── fcm.py                    # Firebase Cloud Messaging
│   │   ├── invoice/
│   │   │   ├── generator.py              # ReportLab PDF invoice generator
│   │   │   └── fonts/
│   │   ├── redis/
│   │   │   ├── cache.py                  # Redis cache operations
│   │   │   └── client.py                 # Redis client singleton
│   │   └── jobs/
│   │       └── order_scheduler.py        # Background order status updater
│   │
│   ├── middleware/
│   │   └── rate_limit_middleware.py      # Global rate limit middleware
│   │
│   ├── models/                           # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── admin_activity_log.py
│   │   ├── admin_profile.py
│   │   ├── base.py
│   │   ├── brand.py
│   │   ├── cart.py
│   │   ├── cart_item.py
│   │   ├── category.py
│   │   ├── coupon.py
│   │   ├── coupon_usage.py
│   │   ├── customer_profile.py
│   │   ├── inventory.py
│   │   ├── invoice.py
│   │   ├── login_history.py
│   │   ├── notification.py
│   │   ├── order.py
│   │   ├── order_item.py
│   │   ├── order_timeline.py
│   │   ├── payment.py
│   │   ├── product.py
│   │   ├── product_attribute.py
│   │   ├── product_image.py
│   │   ├── product_variant.py
│   │   ├── review.py
│   │   ├── review_helpful.py
│   │   ├── user.py
│   │   ├── user_address.py
│   │   ├── user_sessions.py
│   │   ├── vendor_profile.py
│   │   ├── wishlist.py
│   │   └── wishlist_item.py
│   │
│   └── webhooks/
│       └── stripe_webhook.py             # Stripe payment webhook handler
│
├── migrations/                           # Alembic DB migrations
├── scripts/
│   └── createadmin.py                    # Admin account seeder
├── uploads/
│   ├── brands/
│   └── products/
├── invoices/                             # Generated PDF invoices
├── Dummy Frontend/                       # Development frontend test client
├── .env                                  # Environment configuration
└── alembic.ini                           # Alembic migration config
```

---

## 🛠 Tech Stack

### Core Framework & Server

| Library | Purpose |
|---|---|
| **FastAPI** | High-performance async web framework |
| **Uvicorn / Gunicorn** | ASGI server |
| **Pydantic v2** | Data validation & settings management |
| **Python-Jose** | JWT token encoding/decoding (HS256) |
| **Passlib + Bcrypt** | Password hashing & verification |

### Database & ORM

| Library | Purpose |
|---|---|
| **SQLAlchemy 2.x** | ORM & database abstraction |
| **Alembic** | Database migration management |
| **MySQL** | Primary relational database |

### Caching & Sessions

| Library | Purpose |
|---|---|
| **Redis** | Caching, rate limiting, attack tracking, sessions |

### Payments

| Library | Purpose |
|---|---|
| **Stripe Python SDK** | Payment processing & webhooks |

### Notifications & Communication

| Library | Purpose |
|---|---|
| **Firebase Admin SDK** | FCM push notifications |
| **SMTP (smtplib)** | Transactional email delivery |
| **Jinja2** | HTML email template rendering |

### File Processing & Media

| Library | Purpose |
|---|---|
| **Pillow (PIL)** | Image processing & thumbnail generation |
| **ReportLab** | PDF invoice generation |

### Security & Middleware

| Library | Purpose |
|---|---|
| **Custom AttackDetector** | Redis-based brute-force detection & IP blocking |
| **RateLimitMiddleware** | Global API rate limiting |
| **SecurityHeadersMiddleware** | HTTP security headers (HSTS, CSP, etc.) |
| **CORSMiddleware** | Cross-origin request handling |

### Utilities

| Library | Purpose |
|---|---|
| **swagger-ui-bundle** | Custom Swagger UI documentation |
| **Threading** | Background scheduler (order auto-updates) |

---

## 🗄 Database Models

The platform uses **31 SQLAlchemy ORM models** mapped to MySQL tables:

### User & Auth Models

| Model | Description |
|---|---|
| `User` | Core user entity (all roles: customer, vendor, admin) |
| `AdminProfile` | Extended admin-specific profile data |
| `CustomerProfile` | Extended customer-specific profile data |
| `VendorProfile` | Vendor profile with business details & approval status |
| `UserAddress` | Saved shipping/billing addresses |
| `UserSession` | Active JWT session tracking |
| `LoginHistory` | Historical login records with IP & device |

### Product Models

| Model | Description |
|---|---|
| `Product` | Core product entity (title, description, price, vendor) |
| `ProductVariant` | Product variants (size, color combinations) |
| `ProductImage` | Product image gallery (multiple images per product) |
| `ProductAttribute` | Attribute definitions (e.g., "Size", "Color") |
| `ProductAttributeValue` | Attribute value entries (e.g., "Large", "Red") |
| `ProductAttributeMap` | Many-to-many variant ↔ attribute value mapping |
| `Brand` | Product brands |
| `Category` | Hierarchical product category tree |
| `Inventory` | Stock levels per product/variant per vendor |

### Commerce Models

| Model | Description |
|---|---|
| `Cart` | User shopping cart |
| `CartItem` | Individual items within a cart |
| `Order` | Order header with status, total, shipping info |
| `OrderItem` | Line items within an order |
| `OrderTimeline` | Chronological order status change history |
| `Payment` | Payment record linked to an order |
| `Invoice` | Generated invoice metadata |
| `Coupon` | Discount coupon definitions |
| `CouponUsage` | Coupon usage tracking per user |

### Engagement Models

| Model | Description |
|---|---|
| `Review` | Product reviews with ratings |
| `ReviewHelpful` | "Helpful" votes on reviews |
| `Wishlist` | User wishlist container |
| `WishlistItem` | Products saved to a wishlist |
| `Notification` | In-app notifications |

### Admin Models

| Model | Description |
|---|---|
| `AdminActivityLog` | Full audit trail of admin actions |

---

## 📡 API Modules Reference

All endpoints are versioned under `/api/v1/`. Authentication uses **Bearer JWT tokens** in the `Authorization` header.

**User Roles:**
- `customer` — Standard shopping user
- `vendor` — Seller with product & inventory access
- `admin` — Platform superuser with full access

---

### 🔐 Authentication (`409 lines · 12 endpoints`)

**Base path:** `/api/v1/auth/`

Handles all authentication flows including multi-step OTP verification, JWT token management, session control, and login history.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/register` | Register new user (customer or vendor) | No |
| `POST` | `/login` | Login with email + password → returns JWT | No |
| `POST` | `/verify-otp` | Verify OTP code sent after login | No |
| `POST` | `/resend-otp` | Resend OTP verification code | No |
| `POST` | `/forgot-password` | Request password reset | No |
| `POST` | `/reset-password` | Complete password reset with token | No |
| `POST` | `/refresh-token` | Refresh access token using refresh token | No |
| `POST` | `/change-password` | Change password (authenticated) | ✅ User |
| `POST` | `/logout` | Invalidate current session | ✅ User |
| `POST` | `/logout-all` | Invalidate all active sessions | ✅ User |
| `GET` | `/login-history` | Retrieve login history with IP & device | ✅ User |

**Registration schema supports role-based validation:**
- Vendor registration requires `business_name` and `business_address`
- Customer registration requires basic profile info
- Password strength validation enforced via Pydantic validators
- Phone number format validation

**Auth Architecture:**
```
Register → Email/OTP Verify → Login → JWT (Access + Refresh Tokens)
    → AuthService → OTPService → SessionService → LoginHistoryService
```

**JWT Configuration:**
- Algorithm: `HS256`
- Access token expiry: `30 minutes` (configurable)
- Refresh token expiry: `7 days` (configurable)
- Audience: `luxora-users`
- Issuer: `luxora-auth`

---

### 👤 Users (`82 lines · 4 endpoints`)

**Base path:** `/api/v1/users/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/me` | Get current user profile | ✅ User |
| `PUT` | `/me` | Update current user profile | ✅ User |
| `GET` | `/sessions` | List all active sessions | ✅ User |
| `DELETE` | `/sessions/{session_id}` | Revoke a specific session | ✅ User |

---

### 🛡 Admin (`296 lines · 9 endpoints`)

**Base path:** `/api/v1/admin/`

Full platform administration including vendor approval workflow and user management.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/pending-vendors` | List vendors awaiting approval | ✅ Admin |
| `PATCH` | `/approve-vendor/{vendor_id}` | Approve a vendor application | ✅ Admin |
| `PATCH` | `/reject-vendor/{vendor_id}` | Reject a vendor application | ✅ Admin |
| `PATCH` | `/deactivate-user/{user_id}` | Deactivate a user account | ✅ Admin |
| `GET` | `/users` | List all users with filters | ✅ Admin |
| `GET` | `/activity-log` | View admin action audit trail | ✅ Admin |
| `GET` | `/dashboard` | Platform dashboard overview | ✅ Admin |
| `GET` | `/orders` | View all platform orders | ✅ Admin |
| `GET` | `/vendors` | List all vendors | ✅ Admin |

All admin actions are automatically logged to `AdminActivityLog` with actor, action, and timestamp.

---

### 🏪 Vendors (`264 lines · 7 endpoints`)

**Base path:** `/api/v1/vendors/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/` | Create/update vendor profile | ✅ Vendor |
| `GET` | `/me` | Get own vendor profile | ✅ Vendor |
| `PUT` | `/me` | Update vendor profile | ✅ Vendor |
| `GET` | `/` | List all approved vendors | Public |
| `GET` | `/{vendor_id}` | Get public vendor profile | Public |
| `GET` | `/{vendor_id}/products` | Get vendor's product listings | Public |
| `PUT` | `/logo` | Upload vendor logo | ✅ Vendor |

---

### 📦 Products (`274 lines · 6 endpoints`)

**Base path:** `/api/v1/products/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/` | Create new product listing | ✅ Vendor |
| `GET` | `/` | List products (paginated, filterable) | Public |
| `GET` | `/{product_id}` | Get product detail with variants | Public |
| `PUT` | `/{product_id}` | Update product | ✅ Vendor (owner) |
| `DELETE` | `/{product_id}` | Delete product | ✅ Vendor (owner) |
| `POST` | `/{product_id}/images` | Upload product images | ✅ Vendor |

Products support SEO-friendly slugs, multiple images, variant management, and brand/category associations.

---

### 🗂 Categories (`436 lines · 10 endpoints`)

**Base path:** `/api/v1/categories/`

Supports **hierarchical category trees** (parent/child nesting).

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | List all categories (flat) | Public |
| `GET` | `/tree` | Get full category tree structure | Public |
| `GET` | `/{category_id}` | Get category details | Public |
| `GET` | `/{category_id}/children` | Get child categories | Public |
| `POST` | `/` | Create category | ✅ Admin |
| `PUT` | `/{category_id}` | Update category | ✅ Admin |
| `DELETE` | `/{category_id}` | Delete category | ✅ Admin |
| `POST` | `/{category_id}/image` | Upload category image | ✅ Admin |
| `GET` | `/products/{category_id}` | List products in category | Public |
| `GET` | `/search` | Search categories | Public |

---

### 🏷 Brands (`75 lines · 2 endpoints`)

**Base path:** `/api/v1/brands/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | List all brands | Public |
| `POST` | `/admin` | Create brand (admin only) | ✅ Admin |

---

### 🔧 Attributes (`218 lines · 9 endpoints`)

**Base path:** `/api/v1/attributes/`

Manages product specification attributes and variant attribute assignments.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | List all attributes | Public |
| `GET` | `/tree` | Get attribute tree with values | Public |
| `POST` | `/` | Create new attribute | ✅ Admin |
| `POST` | `/{attribute_id}/values` | Add value to attribute | ✅ Admin |
| `GET` | `/{attribute_id}/values` | List attribute values | Public |
| `DELETE` | `/{attribute_id}` | Delete attribute | ✅ Admin |
| `DELETE` | `/values/{value_id}` | Delete attribute value | ✅ Admin |
| `POST` | `/variants/{variant_id}/assign` | Assign attributes to variant | ✅ Vendor |
| `GET` | `/variants/{variant_id}` | Get variant attributes | Public |

---

### 📊 Inventory (`946 lines · 10 endpoints`)

**Base path:** `/api/v1/inventory/`

The most extensive module, handling stock management per vendor per product/variant with low-stock alerting.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/` | Create inventory record | ✅ Vendor |
| `GET` | `/` | List vendor inventory | ✅ Vendor |
| `GET` | `/{inventory_id}` | Get inventory item detail | ✅ Vendor |
| `PUT` | `/{inventory_id}` | Update stock level | ✅ Vendor |
| `GET` | `/low-stock` | List low-stock items | ✅ Vendor |
| `GET` | `/product/{product_id}` | Inventory by product | ✅ Vendor |
| `GET` | `/variant/{variant_id}` | Inventory by variant | ✅ Vendor |
| `GET` | `/admin/all` | All inventory (admin) | ✅ Admin |
| `PATCH` | `/admin/{inventory_id}` | Admin inventory override | ✅ Admin |
| `GET` | `/admin/low-stock` | Platform-wide low stock | ✅ Admin |

---

### 🛒 Cart (`267 lines · 6 endpoints`)

**Base path:** `/api/v1/cart/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | Get current user's cart | ✅ Customer |
| `POST` | `/items` | Add item to cart | ✅ Customer |
| `PUT` | `/items/{item_id}` | Update cart item quantity | ✅ Customer |
| `DELETE` | `/items/{item_id}` | Remove item from cart | ✅ Customer |
| `DELETE` | `/clear` | Clear entire cart | ✅ Customer |
| `POST` | `/buy-now` | Buy-now (skip cart → checkout) | ✅ Customer |

---

### 📋 Orders (`414 lines · 9 endpoints`)

**Base path:** `/api/v1/orders/`

Complete order lifecycle from checkout to delivery with timeline tracking.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/checkout` | Create order from cart | ✅ Customer |
| `GET` | `/` | List user's orders | ✅ Customer |
| `GET` | `/{order_id}` | Get order details | ✅ Customer |
| `POST` | `/{order_id}/cancel` | Cancel order | ✅ Customer |
| `GET` | `/{order_id}/timeline` | Order status timeline | ✅ Customer |
| `GET` | `/vendor/orders` | Vendor's received orders | ✅ Vendor |
| `PATCH` | `/vendor/{order_id}/status` | Update order fulfillment status | ✅ Vendor |
| `GET` | `/admin/all` | All platform orders | ✅ Admin |
| `PATCH` | `/admin/{order_id}/status` | Admin order status override | ✅ Admin |

**Order Status Flow:**
```
pending → confirmed → processing → shipped → delivered
                    ↘              ↗
                    cancelled / returned
```

---

### 💳 Payments (`102 lines · 3 endpoints`)

**Base path:** `/api/v1/payments/`

Powered by **Stripe** with full webhook verification.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/create` | Create Stripe Payment Intent | ✅ Customer |
| `POST` | `/webhook` | Stripe webhook receiver | Public (signed) |
| `GET` | `/status/{payment_id}` | Get payment status | ✅ Customer |

**Stripe Webhook Events Handled:**
- `payment_intent.succeeded` — Confirms payment & updates order status
- `payment_intent.payment_failed` — Marks payment failed
- `charge.refunded` — Processes refund records

All webhooks are signature-verified using `STRIPE_WEBHOOK_SECRET`.

---

### ⭐ Reviews (`269 lines · 5 endpoints`)

**Base path:** `/api/v1/reviews/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/` | Submit product review | ✅ Customer |
| `GET` | `/product/{product_id}` | Get product reviews | Public |
| `POST` | `/{review_id}/helpful` | Mark review as helpful | ✅ Customer |
| `DELETE` | `/{review_id}` | Delete own review | ✅ Customer |
| `GET` | `/admin/all` | All reviews (moderation) | ✅ Admin |

---

### 🏷 Coupons (`268 lines · 5 endpoints`)

**Base path:** `/api/v1/coupons/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/admin` | Create coupon | ✅ Admin |
| `GET` | `/admin` | List all coupons | ✅ Admin |
| `DELETE` | `/admin/{coupon_id}` | Delete coupon | ✅ Admin |
| `POST` | `/apply` | Apply coupon to cart | ✅ Customer |
| `GET` | `/validate/{code}` | Validate coupon code | ✅ Customer |

---

### 📍 Addresses (`288 lines · 6 endpoints`)

**Base path:** `/api/v1/addresses/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/` | Create address | ✅ User |
| `GET` | `/` | List user's addresses | ✅ User |
| `GET` | `/{address_id}` | Get specific address | ✅ User |
| `PUT` | `/{address_id}` | Update address | ✅ User |
| `DELETE` | `/{address_id}` | Delete address | ✅ User |
| `PATCH` | `/{address_id}/default` | Set as default address | ✅ User |

---

### ❤️ Wishlist (`145 lines · 4 endpoints`)

**Base path:** `/api/v1/wishlist/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/` | Add product to wishlist | ✅ Customer |
| `GET` | `/` | Get wishlist items | ✅ Customer |
| `DELETE` | `/{item_id}` | Remove item from wishlist | ✅ Customer |
| `DELETE` | `/clear` | Clear entire wishlist | ✅ Customer |

---

### 🔔 Notifications (`269 lines · 5 endpoints`)

**Base path:** `/api/v1/notifications/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | List user notifications | ✅ User |
| `PATCH` | `/{notification_id}/read` | Mark notification as read | ✅ User |
| `PATCH` | `/read-all` | Mark all notifications as read | ✅ User |
| `DELETE` | `/{notification_id}` | Delete a notification | ✅ User |
| `DELETE` | `/cleanup-test` | Cleanup old notifications (admin) | ✅ Admin |

**Notification Channels:**
- **In-app:** Stored in `Notification` model, retrieved via API
- **Push:** Firebase Cloud Messaging (FCM) via device token registration
- **Email:** HTML templated emails via SMTP

---

### 👥 Customers (`255 lines · 5 endpoints`)

**Base path:** `/api/v1/customers/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | List all customers | ✅ Admin |
| `GET` | `/{customer_id}` | Customer profile detail | ✅ Admin |
| `PUT` | `/{customer_id}` | Update customer profile | ✅ Admin |
| `POST` | `/` | Create customer profile | ✅ Admin |
| `DELETE` | `/{customer_id}` | Deactivate customer | ✅ Admin |

---

### 🧾 Invoice (`109 lines · 4 endpoints`)

**Base path:** `/api/v1/invoice/`

Auto-generates PDF invoices using ReportLab with custom fonts.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | List user's invoices | ✅ Customer |
| `GET` | `/{order_id}` | Get invoice metadata for order | ✅ Customer |
| `GET` | `/{order_id}/download` | Download PDF invoice | ✅ Customer |

---

### 🔍 Search (`87 lines · 1 endpoint`)

**Base path:** `/api/v1/search/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | Full-text product search with filters | Public |

Query parameters: `q` (search term), `category_id`, `brand_id`, `min_price`, `max_price`, `page`, `per_page`

---

### 📈 Vendor Analytics (`218 lines · 6 endpoints`)

**Base path:** `/api/v1/vendor-analytics/`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/dashboard` | Vendor performance dashboard | ✅ Vendor |
| `GET` | `/revenue` | Revenue breakdown by period | ✅ Vendor |
| `GET` | `/orders` | Order statistics & trends | ✅ Vendor |
| `GET` | `/products` | Product performance metrics | ✅ Vendor |
| `GET` | `/customers` | Customer insights | ✅ Vendor |
| `GET` | `/inventory` | Inventory health summary | ✅ Vendor |

---

### 📊 Analytics — Admin (Scaffolded)

**Base path:** `/api/v1/analytics/`

Platform-level analytics module for admin dashboard. Currently scaffolded and being actively developed.

---

## 🔒 Security System

### 1. JWT Authentication

```python
# Token structure
{
    "sub":   "user_id",
    "type":  "access" | "refresh",
    "iss":   "luxora-auth",
    "aud":   "luxora-users",
    "exp":   <timestamp>,
    "host":  <hostname>
}
```

- All protected endpoints validate `Bearer <token>` headers
- Refresh tokens rotate on use
- All sessions tracked in `UserSession` model
- Logout invalidates tokens server-side

### 2. Attack Detector (`app/core/attack_detector.py`)

Redis-backed brute-force protection:

```
Failed attempt → record in Redis (attack:<prefix>:<ip>)
  → Exceeds threshold → block IP (attack:block:<ip>)
  → Blocked IP gets 429 on all requests
  → Auto-unblock after TTL expires
```

### 3. Rate Limiting

| Target | Limit |
|---|---|
| Login endpoint | 5 requests / window |
| General API | 100 requests / window |

Implemented via both `RateLimiterCore` (per-route) and `RateLimitMiddleware` (global).

### 4. RBAC Permission System (`app/core/permissions.py`)

Role-based access control enforced at the dependency injection level:

```python
# Route access example
@router.get("/admin/users")
def get_users(current_user: User = Depends(require_admin)):
    ...
```

Roles: `customer` → `vendor` → `admin`

### 5. Security Headers Middleware

Automatically injects:
- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy`
- `Referrer-Policy`

### 6. OTP Verification

Two-factor authentication via email OTP:
- OTP generated on login
- Stored in Redis with TTL
- User must verify OTP before receiving JWT tokens
- Resend OTP endpoint with rate limiting

---

## 🏗 Core Infrastructure

### Database Session (`app/infrastructure/database/session.py`)

```python
# Usage pattern in routes
def endpoint(db: Session = Depends(get_db)):
    ...
```

- Uses SQLAlchemy `SessionLocal` with automatic commit/rollback
- Connection pooling configured for production

### Redis Client (`app/infrastructure/redis/client.py`)

Used for:
- Rate limiting counters
- OTP storage with TTL
- Attack detection blocks
- Session caching
- General cache layer

### Email Service (`app/infrastructure/email/service.py`)

- SMTP with STARTTLS (port 587) or SSL support
- Jinja2-powered HTML templates for branded emails
- Async-friendly design

### Firebase FCM (`app/infrastructure/firebase/fcm.py`)

- Lazy-initialized Firebase app singleton
- Reads credentials from `FIREBASE_CREDENTIALS_PATH`
- Sends targeted push notifications per device token

### Invoice Generator (`app/infrastructure/invoice/generator.py`)

- ReportLab-based PDF generation
- Custom font support
- Branded invoice layout
- Auto-saved to `/invoices/` directory

### Order Scheduler (`app/jobs/order_scheduler.py`)

- Background thread running every **60 seconds**
- Auto-updates stale order statuses
- Started during FastAPI app lifespan startup

### Notification Cleanup

- Automatically purges old notifications on a schedule
- Prevents database bloat from accumulated notification records

---

## ⚙️ Configuration & Environment Variables

All configuration is managed via `app/core/config.py` using **Pydantic BaseSettings**, loaded from environment variables or `.env` file.

### Required Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | MySQL connection URL | `mysql+pymysql://root:@localhost:3306/luxora_db` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing secret (min 32 chars) | `your-very-secure-secret-key-here-32chars` |
| `STRIPE_PUBLIC_KEY` | Stripe publishable key | `pk_test_...` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_...` |

### Optional Variables

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Luxora Backend` | Application name |
| `ENVIRONMENT` | `development` | Environment (`development`, `staging`, `production`) |
| `DEBUG` | `False` | Debug mode flag |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime in days |
| `LOGIN_RATE_LIMIT` | `5` | Max login attempts per window |
| `API_RATE_LIMIT` | `100` | Max API requests per window |
| `MAIL_USERNAME` | `None` | SMTP username |
| `MAIL_PASSWORD` | `None` | SMTP password |
| `MAIL_FROM` | `None` | Sender email address |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_SERVER` | `None` | SMTP server hostname |
| `MAIL_STARTTLS` | `True` | Use STARTTLS encryption |
| `MAIL_SSL_TLS` | `False` | Use SSL/TLS encryption |
| `FIREBASE_CREDENTIALS_PATH` | `None` | Path to Firebase service account JSON |
| `ADMIN_ALERT_EMAIL` | `None` | Email address for admin alerts |

### `.env` File Template

```env
# ── APPLICATION ─────────────────────────────────────────
APP_NAME=Luxora Backend
ENVIRONMENT=development
DEBUG=False

# ── DATABASE ─────────────────────────────────────────────
DATABASE_URL=mysql+pymysql://root:@localhost:3306/luxora_db

# ── REDIS ────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── JWT SECURITY ─────────────────────────────────────────
SECRET_KEY=your-super-secret-key-minimum-32-characters-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── EMAIL ─────────────────────────────────────────────────
MAIL_USERNAME=noreply@luxora.com
MAIL_PASSWORD=your_smtp_password
MAIL_FROM=noreply@luxora.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

# ── STRIPE ────────────────────────────────────────────────
STRIPE_PUBLIC_KEY=pk_test_your_stripe_publishable_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret

# ── FIREBASE ─────────────────────────────────────────────
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json

# ── ADMIN ─────────────────────────────────────────────────
ADMIN_ALERT_EMAIL=admin@luxora.com

# ── RATE LIMITING ─────────────────────────────────────────
LOGIN_RATE_LIMIT=5
API_RATE_LIMIT=100
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.11+
- **MySQL** 8.0+
- **Redis** 7+
- **pip** / **virtualenv**

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/luxora-backend.git
cd luxora-backend

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Configure your .env file (see Configuration section above)
nano .env
```

### Database Setup

```bash
# Ensure MySQL is running and your DATABASE_URL is configured

# Run Alembic migrations to create all tables
alembic upgrade head

# (Optional) Create initial admin user
python scripts/createadmin.py
```

### Redis Setup

```bash
# Ensure Redis is running on the configured REDIS_URL
redis-cli ping   # Should return: PONG
```

---

## ▶️ Running the Application

### Development

```bash
# Start with hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Start with Gunicorn + Uvicorn workers
gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

The application will be available at: `http://localhost:8000`

---

## 🗃 Database Migrations

Luxora uses **Alembic** for database schema migrations.

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration (after modifying models)
alembic revision --autogenerate -m "describe your change"

# Roll back one migration
alembic downgrade -1

# View migration history
alembic history

# Check current migration status
alembic current
```

---

## 📚 API Documentation

Luxora serves a **custom-branded Swagger UI** interface:

| Interface | URL | Description |
|---|---|---|
| **Swagger UI** | `http://<local-network-ip>:8000/docs` | Interactive API explorer (local network only) |
| **Root** | `http://<local-network-ip>:8000/` | Health check & info (local network only) |

> ⚠️ **Network Access Restriction:** The API does **not** allow all origins. CORS is configured to permit **local network origins only** (e.g., `192.168.x.x`, `10.x.x.x`). Requests from external or public origins will be rejected. This applies to both the Swagger UI and all API endpoints.

The Swagger UI is powered by `swagger-ui-bundle` with a customized skin matching the Luxora brand.

**To find your local network IP:**
```bash
# Linux / macOS
ip addr show       # or: ifconfig

# Windows
ipconfig
```

**Allowed Origin Examples:**
```
http://192.168.1.105:8000      ✅ Local network — allowed
http://10.0.0.50:8000          ✅ Local network — allowed
http://localhost:8000           ✅ Loopback — allowed
http://yourdomain.com           ❌ External origin — blocked
```

**Authentication in Swagger:**
1. Open `http://<your-local-ip>:8000/docs` from a device on the **same local network**
2. Call `POST /api/v1/auth/login`
3. Copy the `access_token` from the response
4. Click **Authorize** in Swagger UI
5. Enter: `Bearer <your_access_token>`

---

## ⏱ Background Jobs

### Order Auto-Updater (`app/jobs/order_scheduler.py`)

Runs in a **background thread** (every 60 seconds) to:
- Auto-confirm pending orders after payment confirmation
- Transition orders through status stages based on elapsed time
- Send status update notifications to customers

**Lifecycle:**
```
App Start → Threading.Thread(target=auto_update_orders) → starts in daemon mode
```

### Notification Cleanup (`app/infrastructure/cleanup/notification_cleanup.py`)

Purges notifications older than the configured retention window to prevent database bloat.

---

## 🗂 File Storage

Static files are served from the `/uploads/` directory:

```
uploads/
├── brands/     # Brand logos
└── products/   # Product images
```

**Storage Backend:** Local filesystem (development)

> ⚠️ **Production Note:** The codebase includes a comment to replace local storage with **AWS S3** or **Cloudinary** for production deployments. Update `app/core/storage.py` accordingly.

**Image Processing:**
- Pillow (PIL) is used for image validation and resizing
- Thumbnails are auto-generated on upload
- Supported formats: JPEG, PNG, WebP

---

## 📧 Email Service

SMTP-based transactional email with HTML templates:

```
app/infrastructure/email/
├── service.py      # SMTP sender (STARTTLS/SSL)
├── renderer.py     # Jinja2 template renderer
└── templates/      # HTML email templates
    ├── welcome.html
    ├── otp.html
    ├── order_confirmation.html
    └── ...
```

**Supported Email Events:**
- Welcome email on registration
- OTP verification codes
- Order confirmation & status updates
- Password reset links
- Admin alert notifications

---

## 🔔 Push Notifications (Firebase FCM)

Device registration and push notification flow:

```bash
# 1. Register device token (after user login)
POST /api/v1/notifications/register-token
Body: { "fcm_token": "device_fcm_token_here" }

# 2. Notifications are sent automatically by the backend
#    on events like: order updates, promotions, etc.
```

**Firebase Setup:**
1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Download the service account JSON key
3. Set `FIREBASE_CREDENTIALS_PATH` in your `.env` to the JSON file path

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` and `DEBUG=False`
- [ ] Use a strong, random `SECRET_KEY` (minimum 32 chars)
- [ ] Switch Stripe keys to live (`pk_live_`, `sk_live_`)
- [ ] Configure production SMTP credentials
- [ ] Set up Firebase production project
- [ ] Replace local file storage with S3/Cloudinary
- [ ] Configure reverse proxy (nginx) with SSL/TLS
- [ ] Set up database connection pooling
- [ ] Configure log aggregation (ELK, Datadog, etc.)
- [ ] Set up health check monitoring
- [ ] Enable database backups

---

## 🤝 Contributing

This project is maintained by the **Luxora Engineering Team**. Contributions follow internal engineering standards.

```bash
# Development workflow
git checkout -b feature/your-feature-name
# Make changes
git add .
git commit -m "feat: describe your changes"
git push origin feature/your-feature-name
# Open a pull request for review
```

**Code Standards:**
- Follow the **Route → Service → Repository** pattern for all new features
- All new routes must have Pydantic request/response schemas in `schemas.py`
- Business logic belongs in `domains/*/service.py` — never in routes
- Database queries belong in `domains/*/repository.py` — never in services
- All new config values must be added to `app/core/config.py` `Settings` class
- Run linting before committing: `ruff check .`
- Type hints are required for all function signatures

---

<div align="center">

---

**Luxora Backend** · Full Source Code Reference · `Dev` Build

*156 Python Files · 29,442 Lines of Code · 600 Functions · 237 Classes*

---

</div>
