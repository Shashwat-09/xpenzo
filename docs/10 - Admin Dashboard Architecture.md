# XPENZ — ADMIN DASHBOARD ARCHITECTURE

> **Status:** CANONICAL — Defines the complete Admin Dashboard web application  
> **Date:** 2026-03-08  
> **Version:** 1.0  
> **Audience:** Engineers, project managers, security auditors  

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Admin Roles & Permissions](#2-admin-roles--permissions)
3. [Tech Stack](#3-tech-stack)
4. [Admin Authentication & Session Management](#4-admin-authentication--session-management)
5. [System Architecture Overview](#5-system-architecture-overview)
6. [Screen Inventory (12 Modules, 42 Screens)](#6-screen-inventory-12-modules-42-screens)
   - [Module A: Dashboard Home](#module-a-dashboard-home)
   - [Module B: User Management](#module-b-user-management)
   - [Module C: Family Management](#module-c-family-management)
   - [Module D: Transaction Monitoring](#module-d-transaction-monitoring)
   - [Module E: ML Model Management](#module-e-ml-model-management)
   - [Module F: Subscription & Revenue](#module-f-subscription--revenue)
   - [Module G: Push Notifications & Campaigns](#module-g-push-notifications--campaigns)
   - [Module H: Feature Flags & Remote Config](#module-h-feature-flags--remote-config)
   - [Module I: Analytics & Insights](#module-i-analytics--insights)
   - [Module J: Support & Tickets](#module-j-support--tickets)
   - [Module K: Security & Audit](#module-k-security--audit)
   - [Module L: System Health & Infrastructure](#module-l-system-health--infrastructure)
7. [Admin Firestore Schema](#7-admin-firestore-schema)
8. [Admin API Endpoints (Cloud Functions)](#8-admin-api-endpoints-cloud-functions)
9. [Admin Security Rules](#9-admin-security-rules)
10. [Navigation & Layout Architecture](#10-navigation--layout-architecture)
11. [Design System Tokens](#11-design-system-tokens)
12. [Implementation Plan](#12-implementation-plan)
13. [Deployment & DevOps](#13-deployment--devops)
14. [Appendix: Wire-flow Diagrams](#14-appendix-wire-flow-diagrams)

---

## 1. EXECUTIVE SUMMARY

### 1.1 What Is the Admin Dashboard?

The **Xpenz Admin Dashboard** is a web-based internal tool for the Xpenz team to monitor, manage, and operate the entire Xpenz ecosystem. It provides real-time visibility into users, families, transactions, ML model performance, subscriptions, support tickets, and system health — all from a single, unified interface.

### 1.2 Why It's Needed

| Problem | Admin Dashboard Solution |
|---------|--------------------------|
| No way to view user data without raw Firestore queries | Searchable user/family management with role-based access |
| ML model deployment requires manual Firebase Storage uploads | One-click model upload, staged rollout (1%→10%→50%→100%), A/B testing |
| Subscription disputes need Play Console access | In-dashboard purchase verification and refund triggers |
| No centralized support system | Built-in ticket system with user context auto-loaded |
| Feature flags require Firebase Console | Visual flag editor with rollout %, targeting rules, history |
| No visibility into system performance | Real-time dashboards for Cloud Functions, Firestore, latency |
| Security events require log parsing | Audit trail browser with filtering, alerting, and export |

### 1.3 Who Uses It

| Role | Description | Count (Initial) |
|------|-------------|-----------------|
| Super Admin | Full access; system-level operations, admin management | 1-2 |
| Operations Manager | User/family management, content moderation, support | 2-3 |
| ML Engineer | Model deployment, A/B testing, accuracy monitoring, training data | 1-2 |
| Finance Manager | Subscription analytics, revenue dashboards, refunds, promo codes | 1 |
| Support Agent | Read-only access + ticket handling, escalation | 2-4 |

### 1.4 Scope

- **In Scope:** All 12 modules listed below, covering the full operational surface of the Xpenz backend
- **Out of Scope:** Direct database writes to user data (all mutations go through Cloud Functions), mobile app build/deploy (handled by CI/CD), marketing site (separate repo)
- **Hosting:** `admin.xpenz.app` on Firebase Hosting

> **Groups & Splits (post-MVP, Phase 10) — admin handling:** when the Splitwise-style
> feature ships, Support Agents get **read-only** visibility into `/groups/**` (for dispute
> resolution: balances, who-owes-whom, settlement status) under the existing audit-logged,
> Cloud-Function-mediated access model. Admins **never** edit balances or settlements
> directly. Group/split/friend data is **excluded from ML aggregation/analytics** (privacy
> boundary — see Backend Schema §3.8). Add a "Groups & Splits" panel to the user-context
> view (Module J) at that time. Spec: PRD F8.

---

## 2. ADMIN ROLES & PERMISSIONS

### 2.1 Role Definitions

#### Super Admin
- Full unrestricted access to every module  
- Can create/delete other admin accounts  
- Can access raw audit logs and security alerts  
- Can deploy ML models to production  
- Can modify system-level feature flags  
- Can override rate limits and account locks  

#### Operations Manager
- Full access to: Users, Families, Transactions, Support, Notifications  
- Read-only access to: Analytics, System Health  
- No access to: ML Models (deploy/edit), Security (admin management), Feature Flags (create/edit)  

#### ML Engineer
- Full access to: ML Model Management, Analytics (ML tab)  
- Read-only access to: Transactions (for data quality), Users (for user-level accuracy), System Health  
- No access to: Support, Subscriptions, Security (admin management), Notifications (create/send)  

#### Finance Manager
- Full access to: Subscriptions & Revenue, Analytics (Revenue tab), Promo Codes  
- Read-only access to: Users (subscription status), Families (plan info), Dashboard Home  
- No access to: ML Models, Security, Feature Flags, System Health  

#### Support Agent
- Read-only access to: Users, Families, Transactions, Analytics  
- Full access to: Support Tickets (create, respond, escalate, close)  
- No access to: ML Models, Security, Feature Flags, Subscriptions (refund), System Health  

### 2.2 Permissions Matrix

| Module | Super Admin | Ops Manager | ML Engineer | Finance | Support |
|--------|:-----------:|:-----------:|:-----------:|:-------:|:-------:|
| A — Dashboard Home | ✅ Full | ✅ Full | 👁 Read | 👁 Read | 👁 Read |
| B — User Management | ✅ Full | ✅ Full | 👁 Read | 👁 Read | 👁 Read |
| C — Family Management | ✅ Full | ✅ Full | 👁 Read | 👁 Read | 👁 Read |
| D — Transaction Monitoring | ✅ Full | ✅ Full | 👁 Read | ❌ None | 👁 Read |
| E — ML Model Management | ✅ Full | ❌ None | ✅ Full | ❌ None | ❌ None |
| F — Subscription & Revenue | ✅ Full | 👁 Read | ❌ None | ✅ Full | ❌ None |
| G — Push Notifications | ✅ Full | ✅ Full | ❌ None | ❌ None | ❌ None |
| H — Feature Flags | ✅ Full | 👁 Read | 👁 Read | ❌ None | ❌ None |
| I — Analytics | ✅ Full | 👁 Read | ✅ ML Tab | ✅ Rev Tab | 👁 Read |
| J — Support & Tickets | ✅ Full | ✅ Full | ❌ None | ❌ None | ✅ Full |
| K — Security & Audit | ✅ Full | ❌ None | ❌ None | ❌ None | ❌ None |
| L — System Health | ✅ Full | 👁 Read | 👁 Read | ❌ None | ❌ None |

### 2.3 Permission Enforcement

Permissions are enforced at **three layers**:

1. **Client-side (Next.js middleware):** Route guards check role before rendering. Unauthorized routes redirect to Dashboard Home.
2. **Server-side (Next.js API routes / Server Actions):** Verify admin token + role claims before processing any mutation.
3. **Firestore rules:** Admin collections require `custom_claims.admin_role` with appropriate level.

---

## 3. TECH STACK

### 3.1 Core Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Framework | Next.js | 14.x (App Router) | SSR, routing, API routes, middleware |
| Language | TypeScript | 5.3+ | Type safety across full stack |
| Styling | Tailwind CSS | 3.4+ | Utility-first CSS, consistent design tokens |
| Components | shadcn/ui | Latest | Accessible, composable Radix-based components |
| Charts | Recharts | 2.x | Responsive, composable chart library |
| Tables | TanStack Table | 8.x | Headless, sortable, filterable data tables |
| State | Zustand | 4.x | Lightweight global state for admin session |
| Forms | React Hook Form | 7.x + Zod | Form state + schema validation |
| Date | date-fns | 3.x | Date formatting (IST timezone aware) |
| Icons | Material Symbols Outlined | Via CDN | Matches mobile app icon set |
| Fonts | Manrope | 400-800 via Google Fonts | Matches mobile app typography |

### 3.2 Firebase Integration

| Service | SDK | Purpose |
|---------|-----|---------|
| Firebase Admin SDK | `firebase-admin` 12.x | Server-side Firestore reads/writes, Auth admin operations |
| Firebase Client SDK | `firebase` 10.x | Client-side real-time listeners (onSnapshot) |
| Firebase Hosting | CLI | Hosting Next.js app at `admin.xpenz.app` |
| Firebase Auth | Admin | Google Workspace SSO, custom claims for roles |

### 3.3 Development & Build

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 20 LTS | Runtime |
| pnpm | 8.x | Package manager |
| ESLint | 8.x + @typescript-eslint | Linting |
| Prettier | 3.x | Code formatting |
| Vitest | 1.x | Unit/integration tests |
| Playwright | 1.x | E2E tests |
| Turbopack | Built-in | Dev server bundler |

### 3.4 Dependency Summary

| Category | Count | Key Dependencies |
|----------|-------|-----------------|
| Core | 4 | next, react, react-dom, typescript |
| Firebase | 2 | firebase, firebase-admin |
| UI | 5 | tailwindcss, @radix-ui/*, class-variance-authority, clsx, tailwind-merge |
| Data | 3 | recharts, @tanstack/react-table, date-fns |
| Forms | 2 | react-hook-form, zod |
| State | 1 | zustand |
| Dev | 5 | eslint, prettier, vitest, playwright, @types/* |
| **Total** | **~22** | Plus shadcn/ui component files (not npm packages) |

---

## 4. ADMIN AUTHENTICATION & SESSION MANAGEMENT

### 4.1 Authentication Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                   ADMIN LOGIN FLOW                                │
│                                                                   │
│  1. Admin navigates to admin.xpenz.app                           │
│  2. Next.js middleware detects no session → redirect to /login    │
│  3. Admin clicks "Sign in with Google"                           │
│  4. Google OAuth consent (restricted to @xpenz.app domain)       │
│  5. Firebase Auth processes Google credential                     │
│  6. Cloud Function verifyAdminLogin() fires:                     │
│     a. Check email domain == @xpenz.app                          │
│     b. Check admin_users collection for role                     │
│     c. Set custom claims: { admin: true, admin_role: "..." }    │
│     d. Return admin session token                                │
│  7. Next.js stores session token in httpOnly cookie              │
│  8. Redirect to /dashboard                                       │
│                                                                   │
│  Session expires: 8 hours (configurable via Remote Config)       │
│  Refresh: Silent refresh 15 min before expiry                    │
│  Forced logout: On role change, on account deactivation          │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Security Constraints

| Constraint | Implementation |
|-----------|----------------|
| Domain restriction | Only `@xpenz.app` Google Workspace emails allowed |
| Session duration | 8-hour httpOnly, secure, SameSite=Strict cookie |
| Session invalidation | On role change, custom claim update triggers forced re-auth |
| IP allowlisting | Optional: configurable per admin via Remote Config |
| MFA | Required for Super Admin role (Google Workspace enforced) |
| Audit trail | Every login/logout recorded to `audit_log` collection |
| Rate limiting | 5 failed attempts → 30-minute lockout per IP |
| CSRF | Next.js built-in CSRF token on all mutations |
| CORS | Restricted to `admin.xpenz.app` origin only |

### 4.3 Session Token Structure

```typescript
interface AdminSession {
  uid: string;                   // Firebase Auth UID
  email: string;                 // @xpenz.app email
  displayName: string;
  photoURL: string;              // Google profile photo
  role: AdminRole;               // 'super_admin' | 'ops_manager' | 'ml_engineer' | 'finance' | 'support'
  permissions: string[];         // Resolved permission list
  sessionCreated: number;        // Unix timestamp
  sessionExpires: number;        // Unix timestamp (created + 8h)
  lastActivity: number;          // Updated on each request
  ipAddress: string;             // For audit
}

type AdminRole = 'super_admin' | 'ops_manager' | 'ml_engineer' | 'finance' | 'support';
```

### 4.4 Next.js Middleware (Route Protection)

```typescript
// middleware.ts — runs on every request
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const PUBLIC_ROUTES = ['/login', '/api/auth/callback'];
const ROLE_ROUTES: Record<string, AdminRole[]> = {
  '/ml-models':   ['super_admin', 'ml_engineer'],
  '/security':    ['super_admin'],
  '/feature-flags': ['super_admin'],
  '/subscriptions': ['super_admin', 'finance'],
  // ... full mapping
};

export function middleware(request: NextRequest) {
  const session = request.cookies.get('admin_session');
  const path = request.nextUrl.pathname;

  // Allow public routes
  if (PUBLIC_ROUTES.some(r => path.startsWith(r))) {
    return NextResponse.next();
  }

  // No session → login
  if (!session) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Decode and check role (simplified — actual impl verifies JWT)
  const decoded = verifySessionToken(session.value);
  if (!decoded) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Check role-based route access
  for (const [route, roles] of Object.entries(ROLE_ROUTES)) {
    if (path.startsWith(route) && !roles.includes(decoded.role)) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }

  return NextResponse.next();
}
```

---

## 5. SYSTEM ARCHITECTURE OVERVIEW

### 5.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ADMIN DASHBOARD ARCHITECTURE                      │
│                                                                          │
│  ┌─────────────────────────────────────────────────────┐               │
│  │              BROWSER (admin.xpenz.app)               │               │
│  │  Next.js 14 App Router + Tailwind + shadcn/ui       │               │
│  │  ┌──────── ┬──────── ┬──────── ┬──────────────┐   │               │
│  │  │ Pages   │ Layouts │ Server  │ Client        │   │               │
│  │  │ (SSR)   │ (Shared)│ Actions │ Components    │   │               │
│  │  └──────── ┴──────── ┴──────── ┴──────────────┘   │               │
│  └───────────────────┬─────────────────────────────────┘               │
│                      │ HTTPS                                            │
│  ┌───────────────────▼─────────────────────────────────┐               │
│  │           NEXT.JS API ROUTES / SERVER ACTIONS         │               │
│  │  • Auth verification (session cookie)                │               │
│  │  • Role-based access control                         │               │
│  │  • Request validation (Zod)                          │               │
│  │  • Firebase Admin SDK calls                          │               │
│  └───────────────────┬─────────────────────────────────┘               │
│                      │                                                   │
│  ┌───────────────────▼─────────────────────────────────┐               │
│  │              FIREBASE BACKEND (asia-south1)           │               │
│  │                                                       │               │
│  │  ┌─────────┐  ┌─────────┐  ┌──────────┐            │               │
│  │  │Firestore│  │  Auth   │  │ Cloud    │            │               │
│  │  │(DB)     │  │(Users)  │  │Functions │            │               │
│  │  └─────────┘  └─────────┘  └──────────┘            │               │
│  │  ┌─────────┐  ┌─────────┐  ┌──────────┐            │               │
│  │  │Storage  │  │  FCM    │  │Analytics │            │               │
│  │  │(Models) │  │(Push)   │  │(Events)  │            │               │
│  │  └─────────┘  └─────────┘  └──────────┘            │               │
│  │  ┌─────────┐  ┌─────────┐  ┌──────────┐            │               │
│  │  │Remote   │  │Crash-   │  │Cloud     │            │               │
│  │  │Config   │  │lytics   │  │Scheduler │            │               │
│  │  └─────────┘  └─────────┘  └──────────┘            │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                          │
│  ┌─────────────────────────────────────────────────────┐               │
│  │          EXTERNAL SERVICES                           │               │
│  │  • Google Play Developer API (subscriptions)         │               │
│  │  • Google Workspace (admin SSO)                      │               │
│  │  • SendGrid (admin email alerts)                     │               │
│  └─────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Data Flow Patterns

**Pattern 1 — Read (Admin views data)**
```
Browser → Server Action → Firebase Admin SDK → Firestore → Response → RSC render
```

**Pattern 2 — Write (Admin performs action)**
```
Browser → Server Action → Validate (Zod) → Firebase Admin SDK → Firestore write
                                          → Audit log write
                                          → Response
```

**Pattern 3 — Real-time (Live dashboards)**
```
Browser → Firebase Client SDK → onSnapshot(collection) → React state update
```

**Pattern 4 — Batch (Bulk operations)**
```
Browser → Server Action → Firebase Admin SDK → Batched writes (max 500)
                                              → Progress stream to client
```

### 5.3 Next.js App Router Structure

```
app/
├── (auth)/
│   ├── login/page.tsx
│   └── layout.tsx                 ← Centered layout, no sidebar
├── (dashboard)/
│   ├── layout.tsx                 ← Sidebar + topbar + main content
│   ├── page.tsx                   ← Module A: Dashboard Home
│   ├── users/
│   │   ├── page.tsx               ← B1: User List
│   │   └── [userId]/page.tsx      ← B2: User Detail
│   ├── families/
│   │   ├── page.tsx               ← C1: Family List
│   │   ├── [familyId]/page.tsx    ← C2: Family Detail
│   │   └── disputes/page.tsx      ← C3: Family Disputes
│   ├── transactions/
│   │   ├── page.tsx               ← D1: Transaction Feed
│   │   ├── flagged/page.tsx       ← D2: Flagged Transactions
│   │   └── overrides/page.tsx     ← D3: Category Overrides
│   ├── ml-models/
│   │   ├── page.tsx               ← E1: ML Dashboard
│   │   ├── deploy/page.tsx        ← E2: Upload & Deploy
│   │   ├── ab-tests/page.tsx      ← E3: A/B Tests
│   │   ├── rules/page.tsx         ← E4: Rule Editor
│   │   ├── accuracy/page.tsx      ← E5: Accuracy Monitor
│   │   └── training-data/page.tsx ← E6: Training Data
│   ├── subscriptions/
│   │   ├── page.tsx               ← F1: Revenue Dashboard
│   │   ├── list/page.tsx          ← F2: Subscription List
│   │   ├── verify/page.tsx        ← F3: Purchase Verification
│   │   └── promos/page.tsx        ← F4: Promo Codes
│   ├── notifications/
│   │   ├── page.tsx               ← G1: Notification Creator
│   │   ├── history/page.tsx       ← G2: Send History
│   │   └── announcements/page.tsx ← G3: Announcements
│   ├── feature-flags/
│   │   ├── page.tsx               ← H1: Flags Dashboard
│   │   ├── [flagId]/page.tsx      ← H2: Flag Editor
│   │   └── history/page.tsx       ← H3: Flag History
│   ├── analytics/
│   │   ├── page.tsx               ← I1: User Analytics
│   │   ├── performance/page.tsx   ← I2: Performance
│   │   ├── ml/page.tsx            ← I3: ML Analytics
│   │   └── revenue/page.tsx       ← I4: Revenue Analytics
│   ├── support/
│   │   ├── page.tsx               ← J1: Ticket Queue
│   │   ├── [ticketId]/page.tsx    ← J2: Ticket Detail
│   │   └── knowledge/page.tsx     ← J3: Knowledge Base
│   ├── security/
│   │   ├── page.tsx               ← K1: Audit Log
│   │   ├── alerts/page.tsx        ← K2: Security Alerts
│   │   ├── admins/page.tsx        ← K3: Admin Management
│   │   └── data-access/page.tsx   ← K4: Data Access Log
│   └── system/
│       ├── page.tsx               ← L1: Firebase Stats
│       ├── errors/page.tsx        ← L2: Error Dashboard
│       └── infra/page.tsx         ← L3: Infrastructure
├── api/
│   ├── auth/
│   │   ├── login/route.ts
│   │   ├── logout/route.ts
│   │   └── callback/route.ts
│   ├── admin/
│   │   ├── users/route.ts
│   │   ├── families/route.ts
│   │   ├── transactions/route.ts
│   │   ├── ml-models/route.ts
│   │   ├── subscriptions/route.ts
│   │   ├── notifications/route.ts
│   │   ├── feature-flags/route.ts
│   │   ├── analytics/route.ts
│   │   ├── support/route.ts
│   │   └── security/route.ts
│   └── webhooks/
│       └── play-billing/route.ts
├── globals.css
├── layout.tsx                      ← Root layout (fonts, providers)
└── middleware.ts                   ← Auth + role route guards
```

---

## 6. SCREEN INVENTORY (12 MODULES, 42 SCREENS)

> Every screen includes: Name, Description, Key Data Displayed, Available Actions, Role Access  
> Layout: All screens share the dashboard `layout.tsx` (sidebar + topbar) except `/login`

---

### MODULE A: DASHBOARD HOME

> **Route:** `/`  
> **Purpose:** Single-screen overview of the entire Xpenz system  
> **Access:** All roles (data scoped by role)

#### Screen A1 — Dashboard Home

**Description:** The landing page after login. A KPI-driven overview with real-time metrics, trend sparklines, and quick-action cards.

**Key Data:**

| KPI Card | Metric | Sparkline |
|----------|--------|-----------|
| Total Users | Count + 7d growth % | 30-day trend |
| Daily Active Users (DAU) | Today count | 7-day trend |
| Active Families | Count + avg members | 30-day trend |
| Transactions Today | Count + total ₹ value | 24-hour hourly |
| ML Accuracy (L1/L2/L3) | Current % | 30-day trend |
| Revenue (MRR) | ₹ amount + growth % | 90-day trend |
| Open Support Tickets | Count + avg resolution time | 7-day trend |
| System Health | Green/Yellow/Red | 24-hour uptime |

**Charts:**
- **Transactions Volume:** Bar chart (last 30 days)
- **Revenue Trend:** Line chart (last 90 days)  
- **User Growth:** Area chart (last 90 days)
- **Top Categories Today:** Horizontal bar (top 10 L1 categories)

**Quick Actions:**
- "View Flagged Transactions" → D2
- "Deploy ML Model" → E2 (ML Engineer, Super Admin only)
- "Send Notification" → G1 (Ops Manager, Super Admin only)
- "Open Tickets" → J1

**Real-time:** Transaction count and system health update via Firestore `onSnapshot`

---

### MODULE B: USER MANAGEMENT

> **Route:** `/users`  
> **Purpose:** View, search, and manage all Xpenz users  
> **Access:** Full (Super Admin, Ops Manager) · Read-only (ML Engineer, Finance, Support)

#### Screen B1 — User List

**Description:** Paginated, searchable, sortable table of all registered users.

**Key Data (Table Columns):**

| Column | Source | Sortable | Filterable |
|--------|--------|:--------:|:----------:|
| UID | `users/{userId}` | ✗ | ✓ (search) |
| Display Name | `users/{userId}.displayName` | ✓ | ✓ (search) |
| Phone | `users/{userId}.phoneNumber` | ✗ | ✓ (search) |
| Status | Derived (active/inactive/suspended) | ✓ | ✓ (dropdown) |
| Premium | `subscriptions/{id}.status` | ✓ | ✓ (dropdown) |
| Family | `families/{familyId}.info.name` | ✓ | ✓ (search) |
| Transactions | Count from analytics | ✓ | ✓ (range) |
| ML Accuracy | Per-user correction rate | ✓ | ✓ (range) |
| Joined | `users/{userId}.createdAt` | ✓ | ✓ (date range) |
| Last Active | `users/{userId}.lastLoginAt` | ✓ | ✓ (date range) |

**Actions (Role Permitting):**
- Search: Full-text search across name, phone, UID
- Filter: Multi-filter sidebar (status, premium, family, date range)
- Sort: Click column headers
- Export: CSV download of filtered results
- Click row → Navigate to B2

**Pagination:** 50 rows per page, server-side cursor pagination via Firestore

#### Screen B2 — User Detail

**Description:** Comprehensive single-user view with all associated data.

**Layout:** Tabbed interface

**Tab 1 — Profile:**
| Field | Editable | Source |
|-------|:--------:|--------|
| Display Name | ✗ | `users/{userId}.displayName` |
| Phone Number | ✗ | Firebase Auth |
| Email | ✗ | `users/{userId}.email` |
| Profile Photo | ✗ | `users/{userId}.photoUrl` |
| Created At | ✗ | `users/{userId}.createdAt` |
| Last Login | ✗ | `users/{userId}.lastLoginAt` |
| App Version | ✗ | `users/{userId}/devices/{latest}.appVersion` |
| Device Info | ✗ | `users/{userId}/devices/{latest}` |
| Premium Status | ✗ | `subscriptions/{id}` |
| Family | link | `families/{familyId}` |

**Tab 2 — Transactions (last 100):**
- Mini table: Date, Merchant/Description, Amount, Category (L1→L2→L3), ML Confidence, Corrected?
- Link to D1 filtered to this user

**Tab 3 — ML Performance:**
- Correction rate (pie chart: correct / corrected / unreviewed)
- Top corrected categories (table)
- Habit model entries (count of learned patterns)

**Tab 4 — Activity Log:**
- Login history (timestamp, device, IP)
- App events (permission granted, premium purchased, family joined)

**Tab 5 — Subscriptions:**
- Current plan, start/end dates, auto-renew status
- Payment history (table from Google Play API)

**Actions (Super Admin + Ops Manager):**
- Suspend User (sets status to `suspended`, blocks login)
- Unsuspend User
- Force Logout (invalidate all sessions)
- Delete Account (triggers Cloud Function: full data purge per DPDP compliance)
- Reset ML Model (clears user-local habit cache + corrections)
- Send Notification (quick push via FCM)

#### Screen B3 — User Actions Log

**Description:** Dedicated audit view for all admin actions taken on users.

**Key Data:**
- Admin who performed action, timestamp, action type (suspend/delete/reset/notification)
- Before/after state where applicable
- Filterable by admin, action type, date

---

### MODULE C: FAMILY MANAGEMENT

> **Route:** `/families`  
> **Purpose:** Monitor and manage family groups  
> **Access:** Full (Super Admin, Ops Manager) · Read-only (ML Engineer, Finance, Support)

#### Screen C1 — Family List

**Description:** Paginated table of all family groups.

**Key Data (Table Columns):**

| Column | Source | Sortable |
|--------|--------|:--------:|
| Family ID | `families/{familyId}` | ✗ |
| Family Name | `families/{familyId}/info.name` | ✓ |
| Admin | Member with role=ADMIN | ✓ |
| Members | Count of `/members` subcollection | ✓ |
| Plan | Free / Premium | ✓ |
| Total Spending (30d) | Aggregated from transactions | ✓ |
| Active Budgets | Count of `/budgets` | ✓ |
| Created | `families/{familyId}/info.createdAt` | ✓ |
| Last Activity | Latest transaction timestamp | ✓ |

**Actions:**
- Search by family name, admin name, family ID
- Filter: member count range, plan, activity date
- Click row → C2

#### Screen C2 — Family Detail

**Description:** Full family view with members, spending, budgets.

**Layout:** Tabbed interface

**Tab 1 — Overview:**
- Family name, creation date, invite code (masked), plan status
- Member list (name, role, joined date, individual spending 30d)
- Settings: `require_approval`, `max_members`, budget alert thresholds

**Tab 2 — Spending:**
- Family spending chart (daily/weekly/monthly toggle)
- Per-member breakdown (stacked bar chart)
- Top categories (horizontal bar)
- Budget vs actual (progress bars for each budget)

**Tab 3 — Budgets:**
- Table of all budgets: type (FAMILY/CATEGORY/MEMBER), amount, period, current %, status
- Alert history (which alerts were triggered and when)

**Tab 4 — Transactions:**
- Family transaction feed (all members, with `visibility` status)
- Note: PRIVATE transactions show as "[Private Transaction]" with ₹ amount only — no details

**Actions (Super Admin + Ops Manager):**
- Force Remove Member (kicks a member from family)
- Deactivate Family (freezes the family — all data preserved, access blocked)
- Reactivate Family
- Reset Invite Code (generates new code, invalidates old)
- Transfer Admin Role (change family admin to another member)

#### Screen C3 — Family Disputes

**Description:** Queue of flagged family issues (member complaints, unauthorized joins, spending disputes).

**Key Data:**
- Dispute source: automated (suspicious join pattern, budget override) or manual (support ticket)
- Family involved, members involved, dispute type
- Status: Open / Investigating / Resolved
- Resolution notes, resolved by (admin), resolved at

**Actions:**
- Assign to self, add notes, resolve, escalate to Super Admin

---

### MODULE D: TRANSACTION MONITORING

> **Route:** `/transactions`  
> **Purpose:** Monitor transaction feed, flag anomalies, override ML categories  
> **Access:** Full (Super Admin, Ops Manager) · Read-only (ML Engineer, Support)

#### Screen D1 — Transaction Feed

**Description:** Real-time feed of all transactions across all users, with filtering and search.

**Key Data (Table Columns):**

| Column | Source | Sortable |
|--------|--------|:--------:|
| Timestamp | `transactions/{txnId}.timestamp` | ✓ |
| User | `transactions/{txnId}.userId` → user lookup | ✓ |
| Family | `transactions/{txnId}.familyId` → family lookup | ✓ |
| Raw SMS | `transactions/{txnId}.rawSms` (truncated) | ✗ |
| Amount | `transactions/{txnId}.amount` | ✓ |
| Category | L1 / L2 / L3 | ✓ |
| Confidence | ML confidence % | ✓ |
| Source | CHT / Rule / Habit / ATP | ✓ |
| Visibility | FAMILY / PRIVATE | ✓ |
| Corrected | Yes/No + corrected category | ✓ |

**Filters:**
- Date range, amount range, confidence range (< 60% = low confidence flag)
- Category (L1 dropdown → L2 → L3 cascade)
- Source (CHT/Rule/Habit/ATP), visibility, corrected status
- User/family search

**Actions:**
- Click row → expand to show full SMS, category hierarchy, ML explanation
- Export filtered results as CSV
- Bulk flag selected transactions

**Real-time:** New transactions appear at top via `onSnapshot` (throttled to 5s intervals)

#### Screen D2 — Flagged Transactions

**Description:** Transactions flagged by automated rules or admin review.

**Auto-flag Rules:**
- Confidence < 40%
- Amount > ₹50,000 (high-value)
- Category changed by user within 1 minute
- Duplicate detection (same amount + merchant within 2 minutes)
- Currency mismatch (non-INR detected)

**Key Data:**
- Same columns as D1 + Flag Reason, Flag Date, Reviewed By, Review Status

**Actions:**
- Review: Mark as correct, override category, or dismiss flag
- Bulk review: Select multiple + batch action

#### Screen D3 — Category Overrides

**Description:** Admin-initiated category corrections that feed back to ML training.

**Key Data:**
- Original category (L1/L2/L3), overridden to, admin who overrode, timestamp
- Linked transaction details
- Impact: number of similar transactions that would be affected

**Actions:**
- Create override rule: "All transactions matching [pattern] should be [category]"
- View override history
- Disable/enable override rules

---

### MODULE E: ML MODEL MANAGEMENT

> **Route:** `/ml-models`  
> **Purpose:** Deploy models, run A/B tests, monitor accuracy, manage rules  
> **Access:** Full (Super Admin, ML Engineer)

#### Screen E1 — ML Dashboard

**Description:** Overview of the ML system health and performance.

**Key Data:**

| Metric | Source | Visualization |
|--------|--------|---------------|
| Current Model Version | `system/config/ml_models/{version}` | Badge |
| Current Accuracy (L1/L2/L3) | Aggregated from corrections | Gauge charts |
| Rollout % | `ml_deployments/{id}.rolloutPercent` | Progress bar |
| Active A/B Tests | Count from `ab_tests` | Badge |
| Rule Engine Rules | Count from rule engine config | Badge |
| Daily Corrections | Count from `ml_corrections` | Line chart (14d) |
| Cold-Start vs Mature Accuracy | Segmented by user age | Comparison chart |
| Ensemble Source Distribution | CHT % / Rule % / Habit % / ATP % | Pie chart |

**Quick Actions:**
- "Deploy New Model" → E2
- "Create A/B Test" → E3
- "Edit Rules" → E4

#### Screen E2 — Model Upload & Deploy

**Description:** Upload new TFLite model and stage deployment.

**Upload Flow:**
1. Upload `.tflite` file + SentencePiece `.model` file + metadata JSON
2. System validates: file size (< 3.5MB for CHT), input/output shapes, tokenizer vocab size
3. Admin sets deployment name, version number, changelog
4. Upload to Firebase Storage (`/ml_models/v{version}/`)
5. Set initial rollout % (default: 1%)
6. Monitor via E5

**Deployment Stages:**
```
Upload → Validation → Canary (1%) → Staged (10%) → Wider (50%) → Full (100%)
                        ↓                ↓              ↓
                   Monitor 24h      Monitor 48h     Monitor 72h
                   Auto-rollback    Auto-rollback   Auto-rollback
                   if accuracy      if accuracy     if accuracy
                   drops > 3%       drops > 2%      drops > 1%
```

**Actions:**
- Upload model package
- View validation results
- Advance rollout stage
- Rollback to previous version (instant)
- Set auto-rollback thresholds

**Key Data:**
- Upload history (table: version, date, size, accuracy at deployment, current rollout %)
- Validation results: pass/fail per check, warnings

#### Screen E3 — A/B Tests

**Description:** Create and monitor A/B tests comparing model versions.

**Test Configuration:**
| Field | Description |
|-------|-------------|
| Test Name | Descriptive name |
| Control Group | Model version A (e.g., current production) |
| Treatment Group | Model version B (e.g., new candidate) |
| Split % | e.g., 50/50 or 90/10 |
| Target Metric | L1 accuracy / L2 accuracy / L3 accuracy / correction rate |
| Duration | 7/14/30 days |
| User Segment | All / New users only / Premium only |
| Confidence Threshold | Statistical significance level (default: 95%) |

**Monitoring:**
- Control vs Treatment comparison table (accuracy, confidence, corrections, ensemble distribution)
- Daily trend chart per group
- Statistical significance indicator (progress towards p < 0.05)

**Actions:**
- Create, start, pause, stop test
- Declare winner → auto-promote to production
- Export raw test data

#### Screen E4 — Rule Editor

**Description:** Visual editor for the Rule Engine's pattern-matching rules.

**Rule Structure:**
```typescript
interface Rule {
  id: string;
  pattern: string;              // Regex or Trie keyword
  patternType: 'regex' | 'keyword' | 'amount_range';
  category: {
    l1: string;
    l2: string;
    l3: string;
  };
  confidence: number;           // 0.0 - 1.0
  priority: number;             // Higher = checked first
  enabled: boolean;
  createdBy: string;            // Admin UID
  createdAt: Timestamp;
  updatedAt: Timestamp;
  matchCount: number;           // Auto-incremented
  lastMatched: Timestamp | null;
}
```

**Key Data:**
- Rules table: pattern, category, confidence, priority, match count, enabled, last matched
- Sortable by priority, match count, category
- Search by pattern text

**Actions:**
- Create new rule (form: pattern, category picker, confidence slider, priority)
- Edit existing rule (inline edit)
- Enable/disable toggle
- Delete rule (soft delete → archive)
- Test rule: Input sample SMS → show match result
- Import/export rules as JSON
- Bulk operations: enable/disable selected

#### Screen E5 — Accuracy Monitor

**Description:** Deep-dive into ML classification accuracy across all dimensions.

**Visualizations:**
- **Overall Accuracy (L1/L2/L3):** Large gauge charts with trend arrows
- **Per-Category Accuracy:** Heatmap grid (L1 rows × accuracy columns)
- **Confusion Matrix:** Interactive L1-level confusion matrix (click cell → drill to L2/L3)
- **Accuracy by User Maturity:** Line chart (0-7d, 7-30d, 30-90d, 90d+ segments)
- **Accuracy by Source:** Bar chart (CHT vs Rule vs Habit vs ATP)
- **Correction Funnel:** Sankey diagram (original category → corrected category)

**Filters:**
- Date range, user segment (new/mature/premium), category, source

**Actions:**
- Export accuracy report (PDF/CSV)
- Set accuracy alert thresholds (email notification when accuracy drops below X%)

#### Screen E6 — Training Data

**Description:** View and manage ML training data from user corrections.

**Key Data:**
- Recent corrections: SMS snippet (anonymized), original category, corrected category, timestamp
- Correction volume: daily/weekly charts
- Top correction patterns: "X was classified as A but users say B" (frequency ranked)
- Data quality metrics: duplicate %, conflicting corrections %, pattern diversity

**Actions:**
- Export training dataset (anonymized, tokenized)
- Flag correction as incorrect (admin override of user correction)
- Create training batch: select time range → bundle for model retraining
- View anonymization preview (ensure no PII leaks)

---

### MODULE F: SUBSCRIPTION & REVENUE

> **Route:** `/subscriptions`  
> **Purpose:** Monitor revenue, manage subscriptions, verify purchases, manage promos  
> **Access:** Full (Super Admin, Finance) · Read-only (Ops Manager)

#### Screen F1 — Revenue Dashboard

**Description:** Financial overview of the Xpenz subscription business.

**Key Metrics:**

| Metric | Visualization |
|--------|---------------|
| MRR (Monthly Recurring Revenue) | Large number + trend |
| ARR (Annual Run Rate) | Large number |
| Active Subscribers | Count + % of total users |
| Churn Rate (Monthly) | % + trend chart |
| ARPU (Avg Revenue Per User) | ₹ amount |
| LTV (Lifetime Value) | ₹ estimated |
| Trial Conversion Rate | % + funnel chart |
| Revenue by Plan | Pie chart (monthly/annual split) |

**Charts:**
- Revenue trend (last 12 months, line chart)
- Subscriber growth (last 12 months, area chart)
- Churn cohort analysis (grid heatmap)
- Plan distribution (pie chart)

#### Screen F2 — Subscription List

**Description:** Paginated table of all subscription records.

**Key Data (Table Columns):**

| Column | Sortable |
|--------|:--------:|
| User | ✓ |
| Plan (Monthly/Annual) | ✓ |
| Status (Active/Cancelled/Expired/Paused) | ✓ |
| Start Date | ✓ |
| Expiry Date | ✓ |
| Auto-Renew | ✓ |
| Amount (₹) | ✓ |
| Payment Method | ✗ |
| Google Play Order ID | ✗ |

**Actions:**
- Search by user name, UID, order ID
- Filter: status, plan, date range, auto-renew
- Click row → subscription detail with full payment history
- Initiate refund (Super Admin, Finance only) → triggers Cloud Function

#### Screen F3 — Purchase Verification

**Description:** Manual purchase verification tool for dispute resolution.

**Flow:**
1. Enter Google Play Order ID or user UID
2. System calls `verifyPurchase` Cloud Function
3. Displays: purchase token validity, product details, purchase timestamp, current status
4. Compare with Firestore `subscriptions/{id}` record
5. Highlight discrepancies

**Actions:**
- Verify purchase
- Force-sync subscription status (re-query Play API)
- Grant premium manually (time-limited, with reason)
- Revoke premium (with reason)

#### Screen F4 — Promo Codes

**Description:** Create and manage promotional discount codes.

**Code Properties:**
```typescript
interface PromoCode {
  id: string;
  code: string;                 // e.g., "LAUNCH50"
  discountType: 'percent' | 'fixed' | 'trial_extension';
  discountValue: number;        // 50 (%) or 99 (₹) or 30 (days)
  maxUses: number;
  currentUses: number;
  validFrom: Timestamp;
  validUntil: Timestamp;
  targetPlan: 'monthly' | 'annual' | 'both';
  targetSegment: 'all' | 'new_users' | 'churned' | 'specific_users';
  specificUserIds?: string[];
  createdBy: string;
  enabled: boolean;
}
```

**Key Data:**
- Active promos table: code, discount, uses/max, validity period, enabled
- Usage analytics: redemption trend, revenue impact

**Actions:**
- Create new promo code
- Edit existing (disable, change dates, change uses limit)
- Deactivate promo
- View redemption list (who used it, when)
- Export promo analytics

---

### MODULE G: PUSH NOTIFICATIONS & CAMPAIGNS

> **Route:** `/notifications`  
> **Purpose:** Create, schedule, and track push notifications  
> **Access:** Full (Super Admin, Ops Manager)

#### Screen G1 — Notification Creator

**Description:** Compose and send push notifications via FCM.

**Notification Config:**

| Field | Type | Options |
|-------|------|---------|
| Title | Text (max 50 chars) | — |
| Body | Text (max 200 chars) | — |
| Image URL | Optional URL | For rich notifications |
| Deep Link | Optional | Navigate to specific app screen |
| Target | Select | All users / Premium / Free / Family admins / Specific users / User segment |
| Schedule | Select | Send now / Schedule (date + time) / Recurring |
| Priority | Select | Normal / High |
| TTL | Number | Hours before notification expires (default: 24) |

**Preview:**
- Mobile notification preview (Android style mockup)
- Character count indicators
- Deep link validation

**Actions:**
- Send immediately
- Schedule for later
- Save as draft
- Send test to self (admin's test device)

#### Screen G2 — Notification History

**Description:** Log of all sent notifications with delivery metrics.

**Key Data:**

| Column | Description |
|--------|-------------|
| Title | Notification title |
| Sent At | Timestamp |
| Sent By | Admin name |
| Target | Audience description |
| Total Sent | FCM messages dispatched |
| Delivered | Successfully delivered count |
| Opened | App opened from notification |
| Delivery Rate | Delivered / Sent % |
| Open Rate | Opened / Delivered % |
| Status | Sent / Scheduled / Failed / Cancelled |

**Actions:**
- Click row → full notification detail with per-device delivery status
- Cancel scheduled notification
- Resend (clone as new notification)
- Export metrics

#### Screen G3 — Announcements

**Description:** In-app announcement banners (shown in mobile app's home screen).

**Announcement Config:**
| Field | Description |
|-------|-------------|
| Title | Banner title |
| Message | Short description |
| CTA Text | Button text (e.g., "Learn More") |
| CTA Action | Deep link or URL |
| Target | All / Premium / Free / Specific segment |
| Start Date | When to start showing |
| End Date | When to stop showing |
| Priority | Display order if multiple active |
| Dismissible | Can user dismiss? |

**Actions:**
- Create, edit, prioritize, deactivate, archive

---

### MODULE H: FEATURE FLAGS & REMOTE CONFIG

> **Route:** `/feature-flags`  
> **Purpose:** Visual editor for Firebase Remote Config parameters used as feature flags  
> **Access:** Full (Super Admin) · Read-only (Ops Manager, ML Engineer)

#### Screen H1 — Flags Dashboard

**Description:** Overview of all feature flags with current state.

**Key Data (Table Columns):**

| Column | Description |
|--------|-------------|
| Flag Name | e.g., `enable_habit_model`, `max_free_categories` |
| Type | Boolean / String / Number / JSON |
| Default Value | Value for users not in any condition |
| Active Conditions | Number of targeting rules |
| Last Modified | Timestamp |
| Modified By | Admin name |
| Status | Active / Deprecated / Draft |

**Visual Indicators:**
- 🟢 Active flags (currently affecting users)
- 🟡 Draft flags (not yet published)
- 🔴 Deprecated flags (marked for removal)

**Actions:**
- Create new flag
- Click row → H2 (Flag Editor)
- Quick toggle: enable/disable (with confirmation)
- Search and filter by name, type, status

#### Screen H2 — Flag Editor

**Description:** Detailed editor for a single feature flag.

**Sections:**

1. **Basic Info:** Name, description, type, default value
2. **Conditions (Targeting Rules):**
   - Condition name, priority (1 = highest)
   - If: [App version] [is/is not/>=/<=/contains] [value]
   - AND: [User property] [is/is not] [value]
   - AND: [% of users] [in random percentile] [0-100]
   - Then: [override value]
   - Multiple conditions supported (evaluated top-down, first match wins)
3. **Publish Preview:** Shows before/after diff
4. **Publish History:** Log of all changes with rollback option

**Actions:**
- Save as draft
- Publish (pushes to Firebase Remote Config)
- Rollback to specific version
- Delete flag (Super Admin only)

#### Screen H3 — Flag History

**Description:** Audit log of all feature flag changes.

**Key Data:**
- Flag name, old value → new value, changed by, timestamp, publish status
- Filter by flag, admin, date range
- Rollback button per entry

---

### MODULE I: ANALYTICS & INSIGHTS

> **Route:** `/analytics`  
> **Purpose:** Data analytics dashboards for different teams  
> **Access:** Full ML tab (ML Engineer) · Full Revenue tab (Finance) · Read-only all tabs (Everyone else)

#### Screen I1 — User Analytics

**Description:** User behavior and engagement metrics.

**Key Metrics:**
- DAU / WAU / MAU with trend charts
- User retention (D1, D7, D30 cohort curves)
- Session duration distribution
- Feature adoption (% using budgets, family, premium features)
- Onboarding completion rate (per step)
- Country / city / device distribution (from Analytics)

#### Screen I2 — Performance Analytics

**Description:** App and backend performance metrics.

**Key Metrics:**
- Cloud Function invocation counts + latency (p50, p95, p99) per function
- Firestore read/write/delete operations per day
- Firebase Storage bandwidth
- FCM delivery rates
- App crash rate (from Crashlytics)
- ANR rate
- Cold start time (from Analytics)
- ML inference latency histogram

#### Screen I3 — ML Analytics

**Description:** ML-specific analytics for the engineering team.

**Key Metrics:**
- Accuracy trends (L1/L2/L3) over time
- Correction rate by category (which categories are users correcting most?)
- Ensemble source usage (% classified by CHT vs Rule vs Habit vs ATP)
- Cold-start accuracy vs mature accuracy
- Model version comparison (if A/B test running)
- Category distribution (which categories are most common in transactions?)
- Training data growth (corrections/day)
- Model download stats (how many users are on each model version?)

#### Screen I4 — Revenue Analytics

**Description:** Revenue-focused analytics for the finance team.

**Key Metrics:**
- MRR / ARR with trends
- Subscriber count by plan
- Conversion funnel: Install → Free user → Trial → Premium
- Churn analysis: reasons, timing, cohort
- ARPU, LTV by cohort
- Promo code impact on revenue
- Refund rate
- Revenue by region (if granular data available)
- Projected revenue (linear + cohort-based)

---

### MODULE J: SUPPORT & TICKETS

> **Route:** `/support`  
> **Purpose:** Handle user support requests  
> **Access:** Full (Super Admin, Ops Manager, Support) · No access (ML Engineer, Finance)

#### Screen J1 — Ticket Queue

**Description:** Prioritized queue of all support tickets.

**Key Data (Table Columns):**

| Column | Description |
|--------|-------------|
| Ticket ID | Auto-generated |
| Subject | User's reported issue |
| User | Linked user (click → B2) |
| Category | Bug / Feature Request / Billing / Account / ML / Other |
| Priority | Critical / High / Medium / Low |
| Status | Open / In Progress / Waiting / Resolved / Closed |
| Assigned To | Admin name |
| Created At | Timestamp |
| Last Update | Timestamp |
| SLA | Time remaining (colored: green > yellow > red) |

**SLA Targets:**
| Priority | First Response | Resolution |
|----------|:-------------:|:----------:|
| Critical | 1 hour | 4 hours |
| High | 4 hours | 24 hours |
| Medium | 12 hours | 72 hours |
| Low | 24 hours | 1 week |

**Actions:**
- Assign to self / another agent
- Change priority
- Filter: status, priority, category, assigned to, date range
- Sort by any column
- Bulk actions: assign, change status

#### Screen J2 — Ticket Detail

**Description:** Full ticket view with conversation thread and user context.

**Layout:** Split pane — left (conversation), right (user context)

**Left Pane — Conversation:**
- User's original message
- Admin responses (threaded)
- Status changes (timeline)
- Internal notes (visible only to admins, highlighted in yellow)

**Right Pane — User Context (auto-loaded):**
- User profile summary (from B2)
- Device info, app version
- Recent transactions (last 10)
- Subscription status
- Family membership
- ML accuracy for this user
- Previous tickets from this user

**Actions:**
- Reply to user (sends push notification + in-app message)
- Add internal note
- Change status
- Change priority
- Escalate to Super Admin
- Link related ticket
- Mark as duplicate
- Close with resolution summary

#### Screen J3 — Knowledge Base

**Description:** Internal knowledge base for support agents.

**Content:**
- FAQ articles (searchable, categorized)
- Troubleshooting guides (step-by-step)
- Known issues list (linked to GitHub issues if applicable)
- Canned responses (pre-written replies agents can insert into tickets)
- Policy documents (refund policy, data deletion policy, etc.)

**Actions (Ops Manager, Super Admin):**
- Create/edit articles
- Categorize
- Mark as outdated
- Usage analytics (which articles are used most?)

---

### MODULE K: SECURITY & AUDIT

> **Route:** `/security`  
> **Purpose:** Audit trail, security alerts, admin management  
> **Access:** Full (Super Admin only)

#### Screen K1 — Audit Log

**Description:** Complete audit trail of all admin actions.

**Key Data (Table Columns):**

| Column | Description |
|--------|-------------|
| Timestamp | ISO 8601 with timezone |
| Admin | Name + email |
| Action | e.g., `user.suspend`, `ml_model.deploy`, `feature_flag.publish` |
| Target | What was acted upon (user UID, model version, flag name) |
| Details | JSON diff of changes |
| IP Address | Admin's IP |
| Session ID | Session identifier |

**Filters:**
- Admin, action type, target, date range
- Full-text search in details

**Actions:**
- Export audit log (CSV/JSON)
- Click row → expand full detail JSON
- Flag suspicious action

**Retention:** 2 years (configurable)

#### Screen K2 — Security Alerts

**Description:** Automated security alerts and anomaly detection.

**Alert Types:**

| Alert | Trigger | Severity |
|-------|---------|----------|
| Brute Force Login | > 5 failed admin logins from same IP in 15 min | 🔴 Critical |
| Unusual Admin Activity | Admin actions outside working hours or from new IP | 🟡 Warning |
| Mass Data Access | > 100 user profiles viewed in 1 hour | 🟡 Warning |
| Bulk Operation | > 50 user suspensions in 1 hour | 🔴 Critical |
| Model Rollback | Auto-rollback triggered due to accuracy drop | 🟡 Warning |
| Firestore Quota | > 80% of daily read/write quota used | 🟡 Warning |
| Function Error Spike | Error rate > 5% for any Cloud Function | 🔴 Critical |
| Unauthorized Access Attempt | Admin tries to access route above their role | 🟡 Warning |

**Actions:**
- Acknowledge alert
- Investigate (view related audit log entries)
- Create incident
- Configure alert thresholds
- Subscribe to email/SMS notifications per alert type

#### Screen K3 — Admin Management

**Description:** Manage admin dashboard users and their roles.

**Key Data:**
- Admin list: name, email, role, last login, MFA status, active sessions
- Invitation management: pending invites

**Actions:**
- Invite new admin (enter email, select role)
- Change admin role
- Deactivate admin (disable access, terminate sessions)
- Reactivate admin
- Force logout admin
- View admin's audit trail (link to K1 filtered)
- Require MFA reset

#### Screen K4 — Data Access Log

**Description:** Log of all user data accessed by admins (DPDP compliance).

**Purpose:** Track which admin viewed which user's data and when. Required for data protection compliance.

**Key Data:**
- Timestamp, admin, user whose data was accessed, data type (profile/transactions/subscription/ML data), access reason

**Actions:**
- Export for compliance audit
- Filter by admin, user, data type, date range
- Generate compliance report

---

### MODULE L: SYSTEM HEALTH & INFRASTRUCTURE

> **Route:** `/system`  
> **Purpose:** Monitor Firebase and Cloud infrastructure health  
> **Access:** Full (Super Admin) · Read-only (Ops Manager, ML Engineer)

#### Screen L1 — Firebase Stats

**Description:** Real-time Firebase usage metrics (proxied from Firebase Console APIs / Cloud Monitoring).

**Key Data:**

| Metric | Source |
|--------|--------|
| Firestore reads/day | Cloud Monitoring |
| Firestore writes/day | Cloud Monitoring |
| Firestore deletes/day | Cloud Monitoring |
| Storage used (GB) | Cloud Monitoring |
| Storage bandwidth/day | Cloud Monitoring |
| Auth active users | Firebase Auth |
| FCM messages sent/day | FCM stats |
| Cloud Functions invocations/day | Cloud Monitoring |
| Cloud Functions avg latency | Cloud Monitoring |
| Cloud Functions error count | Cloud Monitoring |
| Billing estimate (today/month) | Cloud Billing API |

**Charts:**
- 24-hour timeline for each metric
- 30-day trend charts
- Cost breakdown by service (pie chart)
- Quota usage (% of limits) with color coding (green/yellow/red)

#### Screen L2 — Error Dashboard

**Description:** Aggregated error monitoring from Crashlytics and Cloud Functions.

**Sections:**

1. **App Crashes (Crashlytics):**
   - Top crash groups (by occurrence count)
   - Crash-free user % (trend)
   - Crash distribution by: device, OS version, app version
   - Click crash group → stack trace detail

2. **Cloud Function Errors:**
   - Error rate per function (bar chart)
   - Recent errors: function name, error message, timestamp, invocation ID
   - Error trend (24h, 7d, 30d)

3. **Firestore Errors:**
   - Permission denied rate
   - Quota exceeded events
   - Timeout events

**Actions:**
- Export error report
- Create support ticket from crash group
- Set error alerting thresholds

#### Screen L3 — Infrastructure

**Description:** Overview of the deployment, scheduled jobs, and system configuration.

**Sections:**

1. **Cloud Functions Deployment:**
   - Function list: name, runtime (Node.js 20), region (asia-south1), memory, timeout
   - Last deployed, deployment status
   - Environment variables (names only, values masked)

2. **Scheduled Jobs:**
   - Job list: `dailyBudgetCheck`, `weeklyReports`, `cleanupExpiredInvitations`, `syncMLCorrections`
   - Schedule (cron), last run, last status, next run

3. **Firebase Hosting:**
   - Current deployment version, deployed at, deployed by
   - Domain config (`admin.xpenz.app`)
   - SSL status

4. **Remote Config:**
   - Current template version
   - Last modified, modified by
   - Quick link to H1

**Actions:**
- Redeploy Cloud Functions (trigger from CI/CD)
- Force-run scheduled job (Super Admin only)
- View deployment history

---

## 7. ADMIN FIRESTORE SCHEMA

> These collections exist alongside the app's existing collections.  
> All admin collections are prefixed convention: they exist at root level with clear names.

### 7.1 Collection: `admin_users`

```typescript
// Path: /admin_users/{adminUid}
interface AdminUser {
  uid: string;                    // Firebase Auth UID (Google Workspace)
  email: string;                  // @xpenz.app
  displayName: string;
  photoURL: string;
  role: AdminRole;                // 'super_admin' | 'ops_manager' | 'ml_engineer' | 'finance' | 'support'
  status: 'active' | 'deactivated';
  mfaEnabled: boolean;
  permissions: string[];          // Resolved permission list (computed from role)
  
  // Session tracking
  activeSessions: number;
  lastLoginAt: Timestamp;
  lastLoginIp: string;
  lastActivity: Timestamp;
  
  // Metadata
  invitedBy: string;              // UID of admin who invited
  createdAt: Timestamp;
  updatedAt: Timestamp;
  deactivatedAt: Timestamp | null;
  deactivatedBy: string | null;
}

type AdminRole = 'super_admin' | 'ops_manager' | 'ml_engineer' | 'finance' | 'support';
```

### 7.2 Collection: `audit_log`

```typescript
// Path: /audit_log/{logId}
// Write-only from admin actions. Immutable (no updates/deletes).
interface AuditLogEntry {
  id: string;                     // Auto-generated
  adminUid: string;               // Who performed the action
  adminEmail: string;             // Denormalized for quick display
  adminRole: AdminRole;           // Role at time of action
  
  action: string;                 // Dot-notation: 'user.suspend', 'ml_model.deploy', etc.
  category: AuditCategory;       // 'user' | 'family' | 'transaction' | 'ml' | 'subscription' | 'notification' | 'feature_flag' | 'support' | 'security' | 'system'
  
  targetType: string;             // 'user' | 'family' | 'model' | 'flag' | 'ticket' | 'admin' | etc.
  targetId: string;               // UID or ID of the target entity
  targetLabel: string;            // Human-readable label (e.g., user's name)
  
  details: Record<string, any>;   // JSON diff or action-specific payload
  
  // Context
  ipAddress: string;
  userAgent: string;
  sessionId: string;
  
  // Timestamp
  timestamp: Timestamp;           // Server timestamp
  
  // Retention
  expiresAt: Timestamp;           // timestamp + 2 years (TTL policy)
}

type AuditCategory = 
  | 'user' | 'family' | 'transaction' | 'ml' 
  | 'subscription' | 'notification' | 'feature_flag' 
  | 'support' | 'security' | 'system';
```

### 7.3 Collection: `support_tickets`

```typescript
// Path: /support_tickets/{ticketId}
interface SupportTicket {
  id: string;                     // Auto-generated (format: "TKT-{timestamp}-{random}")
  
  // User info (denormalized)
  userId: string;
  userName: string;
  userPhone: string;
  userPremium: boolean;
  
  // Ticket content
  subject: string;
  description: string;
  category: 'bug' | 'feature_request' | 'billing' | 'account' | 'ml_accuracy' | 'family' | 'other';
  priority: 'critical' | 'high' | 'medium' | 'low';
  
  // Assignment
  status: 'open' | 'in_progress' | 'waiting_user' | 'resolved' | 'closed';
  assignedTo: string | null;      // Admin UID
  assignedToName: string | null;  // Denormalized
  escalatedTo: string | null;     // Admin UID if escalated
  
  // SLA tracking
  slaFirstResponse: Timestamp;    // Deadline for first response
  slaResolution: Timestamp;       // Deadline for resolution
  firstRespondedAt: Timestamp | null;
  resolvedAt: Timestamp | null;
  slaBreach: boolean;             // True if any SLA missed
  
  // Related entities
  relatedTicketIds: string[];
  isDuplicate: boolean;
  duplicateOf: string | null;
  
  // Resolution
  resolution: string | null;      // Summary of resolution
  
  // Metadata
  source: 'in_app' | 'email' | 'admin_created';
  tags: string[];
  createdAt: Timestamp;
  updatedAt: Timestamp;
  closedAt: Timestamp | null;
  closedBy: string | null;
}

// Sub-collection: /support_tickets/{ticketId}/messages/{messageId}
interface TicketMessage {
  id: string;
  authorType: 'user' | 'admin';
  authorId: string;
  authorName: string;
  content: string;
  isInternalNote: boolean;        // Only visible to admins
  attachments: string[];          // Firebase Storage URLs
  createdAt: Timestamp;
}
```

### 7.4 Collection: `campaigns`

```typescript
// Path: /campaigns/{campaignId}
interface Campaign {
  id: string;
  
  // Notification content
  title: string;
  body: string;
  imageUrl: string | null;
  deepLink: string | null;
  
  // Targeting
  target: CampaignTarget;
  estimatedReach: number;         // Pre-computed audience size
  
  // Scheduling
  schedule: 'immediate' | 'scheduled' | 'recurring';
  scheduledAt: Timestamp | null;
  recurringCron: string | null;   // Cron expression for recurring
  
  // FCM config
  priority: 'normal' | 'high';
  ttlHours: number;               // Default: 24
  
  // Status
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'cancelled' | 'failed';
  
  // Metrics
  totalSent: number;
  totalDelivered: number;
  totalOpened: number;
  deliveryRate: number;           // Computed: delivered / sent
  openRate: number;               // Computed: opened / delivered
  
  // Metadata
  createdBy: string;              // Admin UID
  createdByName: string;
  sentAt: Timestamp | null;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

interface CampaignTarget {
  type: 'all' | 'premium' | 'free' | 'family_admins' | 'segment' | 'specific';
  segmentRules?: SegmentRule[];   // For 'segment' type
  specificUserIds?: string[];     // For 'specific' type
}

interface SegmentRule {
  field: string;                  // e.g., 'lastLoginAt', 'premiumStatus', 'familyRole'
  operator: 'eq' | 'neq' | 'gt' | 'lt' | 'gte' | 'lte' | 'in';
  value: any;
}
```

### 7.5 Collection: `feature_flags`

```typescript
// Path: /feature_flags/{flagId}
// Mirrors Firebase Remote Config but with admin metadata
interface FeatureFlag {
  id: string;
  key: string;                    // Remote Config parameter name
  description: string;
  type: 'boolean' | 'string' | 'number' | 'json';
  
  // Values
  defaultValue: any;              // Value when no condition matches
  conditions: FlagCondition[];    // Evaluated top-down, first match wins
  
  // Status
  status: 'active' | 'draft' | 'deprecated';
  published: boolean;             // True if synced to Remote Config
  lastPublishedAt: Timestamp | null;
  lastPublishedBy: string | null;
  
  // Metadata
  createdBy: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
  updatedBy: string;
  
  // Versioning
  version: number;                // Incremented on each publish
}

interface FlagCondition {
  name: string;                   // Human-readable condition name
  priority: number;               // Lower = higher priority
  rules: FlagRule[];              // AND logic within a condition
  value: any;                     // Override value when condition matches
}

interface FlagRule {
  field: 'app_version' | 'platform' | 'user_property' | 'percent';
  operator: 'eq' | 'neq' | 'gte' | 'lte' | 'contains' | 'in_percentile';
  value: any;
}

// Sub-collection: /feature_flags/{flagId}/history/{historyId}
interface FlagHistoryEntry {
  id: string;
  version: number;
  previousValue: any;             // Full flag state before change
  newValue: any;                  // Full flag state after change
  changedBy: string;
  changedByName: string;
  changeType: 'create' | 'update' | 'publish' | 'rollback' | 'deprecate';
  timestamp: Timestamp;
}
```

### 7.6 Collection: `promo_codes`

```typescript
// Path: /promo_codes/{promoId}
interface PromoCode {
  id: string;
  code: string;                   // Unique, uppercase, e.g., "LAUNCH50"
  
  // Discount
  discountType: 'percent' | 'fixed_amount' | 'trial_extension';
  discountValue: number;          // 50 (%) or 99 (₹) or 30 (days)
  
  // Limits
  maxUses: number;
  currentUses: number;            // Incremented via FieldValue.increment()
  maxUsesPerUser: number;         // Default: 1
  
  // Validity
  validFrom: Timestamp;
  validUntil: Timestamp;
  enabled: boolean;
  
  // Targeting
  targetPlan: 'monthly' | 'annual' | 'both';
  targetSegment: 'all' | 'new_users' | 'churned_users' | 'specific_users';
  specificUserIds: string[];      // Only if targetSegment == 'specific_users'
  
  // Analytics
  totalRedemptions: number;
  totalRevenueImpact: number;     // ₹ estimate of lost revenue from discounts
  
  // Metadata
  createdBy: string;
  createdByName: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

// Sub-collection: /promo_codes/{promoId}/redemptions/{redemptionId}
interface PromoRedemption {
  userId: string;
  userName: string;
  redeemedAt: Timestamp;
  subscriptionId: string;
  discountApplied: number;        // Actual ₹ discount
}
```

### 7.7 Collection: `ml_deployments`

```typescript
// Path: /ml_deployments/{deploymentId}
interface MLDeployment {
  id: string;
  modelVersion: string;           // e.g., "3.1.0"
  
  // Files
  chtModelUrl: string;            // Firebase Storage URL for .tflite
  chtModelSize: number;           // Bytes
  tokenizerUrl: string;           // Firebase Storage URL for .model
  tokenizerSize: number;
  ruleEngineUrl: string;          // Firebase Storage URL for rules JSON
  ruleEngineSize: number;
  atpTableUrl: string;            // Firebase Storage URL for ATP lookup
  atpTableSize: number;
  metadataUrl: string;            // Firebase Storage URL for metadata JSON
  
  // Validation
  validationStatus: 'pending' | 'passed' | 'failed';
  validationResults: {
    inputShapeValid: boolean;
    outputShapeValid: boolean;
    sizeWithinLimit: boolean;
    tokenVocabValid: boolean;
    benchmarkAccuracy: number;    // Accuracy on validation set
    benchmarkLatency: number;     // ms on reference device
  };
  
  // Rollout
  rolloutPercent: number;         // 0-100
  rolloutStage: 'canary' | 'staged' | 'wider' | 'full' | 'rolled_back';
  autoRollbackEnabled: boolean;
  rollbackThreshold: number;      // Accuracy drop % that triggers rollback
  
  // Status
  status: 'uploading' | 'validating' | 'ready' | 'deploying' | 'active' | 'rolled_back' | 'archived';
  
  // Monitoring
  currentAccuracy: {
    l1: number;
    l2: number;
    l3: number;
  };
  usersOnThisVersion: number;
  
  // Changelog
  changelog: string;
  
  // Metadata
  deployedBy: string;
  deployedByName: string;
  deployedAt: Timestamp | null;
  createdAt: Timestamp;
  updatedAt: Timestamp;
  rolledBackAt: Timestamp | null;
  rolledBackBy: string | null;
  rolledBackReason: string | null;
}
```

### 7.8 Collection: `ab_tests`

```typescript
// Path: /ab_tests/{testId}
interface ABTest {
  id: string;
  name: string;
  description: string;
  
  // Groups
  controlModelVersion: string;    // Existing production model
  treatmentModelVersion: string;  // New candidate model
  splitPercent: number;           // % of users in treatment (rest in control)
  
  // Targeting
  userSegment: 'all' | 'new_users' | 'premium' | 'mature_users';
  
  // Metrics
  targetMetric: 'l1_accuracy' | 'l2_accuracy' | 'l3_accuracy' | 'correction_rate';
  confidenceThreshold: number;    // e.g., 0.95 for 95% confidence
  
  // Duration
  plannedDuration: number;        // Days
  startedAt: Timestamp | null;
  endsAt: Timestamp | null;
  
  // Status
  status: 'draft' | 'running' | 'paused' | 'completed' | 'cancelled';
  
  // Results
  results: {
    controlSampleSize: number;
    treatmentSampleSize: number;
    controlMetricValue: number;
    treatmentMetricValue: number;
    statisticalSignificance: number;  // p-value
    isSignificant: boolean;
    winner: 'control' | 'treatment' | 'inconclusive' | null;
  } | null;
  
  // Metadata
  createdBy: string;
  createdByName: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
  completedAt: Timestamp | null;
  declaredBy: string | null;       // Admin who declared winner
}
```

### 7.9 Schema Summary

| Collection | Documents (est.) | Subcollections | Write Frequency | TTL |
|------------|:----------------:|:--------------:|:---------------:|:---:|
| `admin_users` | 5-15 | — | Low (role changes) | None |
| `audit_log` | 10K+/month | — | High (every admin action) | 2 years |
| `support_tickets` | 100+/month | `messages` | Medium | None |
| `campaigns` | 10-50/month | — | Low | None |
| `feature_flags` | 20-50 total | `history` | Low | None |
| `promo_codes` | 10-30 total | `redemptions` | Low | None |
| `ml_deployments` | 2-5/month | — | Low | None |
| `ab_tests` | 1-3/month | — | Medium (results update) | None |

---

## 8. ADMIN API ENDPOINTS (CLOUD FUNCTIONS)

> All admin endpoints require valid admin session token.  
> All mutations automatically write to `audit_log`.  
> All endpoints are located in region `asia-south1`.  
> Prefix: All admin callable functions use `admin` prefix.

### 8.1 Authentication

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminVerifyLogin` | HTTP | Google credential token | Session token + admin profile | Any admin |
| `adminRefreshSession` | HTTP | Existing session token | New session token | Any admin |
| `adminLogout` | HTTP | Session token | — | Any admin |

### 8.2 User Management

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminListUsers` | Callable | `{ page, pageSize, filters, sort }` | Paginated user list | All except Finance |
| `adminGetUser` | Callable | `{ userId }` | Full user profile + stats | All except Finance |
| `adminSuspendUser` | Callable | `{ userId, reason }` | Updated user + audit entry | Super Admin, Ops |
| `adminUnsuspendUser` | Callable | `{ userId }` | Updated user + audit entry | Super Admin, Ops |
| `adminForceLogout` | Callable | `{ userId }` | Revoked tokens count | Super Admin, Ops |
| `adminDeleteUser` | Callable | `{ userId, confirmation }` | Deletion receipt | Super Admin |
| `adminResetUserML` | Callable | `{ userId }` | Reset confirmation | Super Admin, Ops |
| `adminSendUserNotification` | Callable | `{ userId, title, body, deepLink? }` | FCM message ID | Super Admin, Ops |

### 8.3 Family Management

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminListFamilies` | Callable | `{ page, pageSize, filters, sort }` | Paginated family list | All except Finance |
| `adminGetFamily` | Callable | `{ familyId }` | Full family detail | All except Finance |
| `adminRemoveFamilyMember` | Callable | `{ familyId, memberId, reason }` | Updated family | Super Admin, Ops |
| `adminDeactivateFamily` | Callable | `{ familyId, reason }` | Updated family | Super Admin, Ops |
| `adminReactivateFamily` | Callable | `{ familyId }` | Updated family | Super Admin, Ops |
| `adminResetInviteCode` | Callable | `{ familyId }` | New invite code | Super Admin, Ops |
| `adminTransferAdminRole` | Callable | `{ familyId, fromUid, toUid }` | Updated family | Super Admin |

### 8.4 Transaction Monitoring

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminListTransactions` | Callable | `{ page, pageSize, filters, sort }` | Paginated transactions | Super Admin, Ops, ML, Support |
| `adminGetTransaction` | Callable | `{ familyId, transactionId }` | Full transaction detail | Super Admin, Ops, ML, Support |
| `adminFlagTransaction` | Callable | `{ familyId, txnId, reason }` | Flagged txn | Super Admin, Ops |
| `adminOverrideCategory` | Callable | `{ familyId, txnId, newCategory, reason }` | Updated txn + audit | Super Admin, Ops |
| `adminListFlaggedTransactions` | Callable | `{ page, pageSize, filters }` | Flagged txn list | Super Admin, Ops |
| `adminReviewFlaggedTransaction` | Callable | `{ flagId, action, notes }` | Updated flag | Super Admin, Ops |

### 8.5 ML Model Management

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminUploadModel` | HTTP (multipart) | Model files + metadata | Deployment record | Super Admin, ML |
| `adminValidateModel` | Callable | `{ deploymentId }` | Validation results | Super Admin, ML |
| `adminSetRollout` | Callable | `{ deploymentId, percent, stage }` | Updated deployment | Super Admin, ML |
| `adminRollbackModel` | Callable | `{ deploymentId, reason }` | Rollback confirmation | Super Admin, ML |
| `adminGetMLAccuracy` | Callable | `{ filters }` | Accuracy metrics | Super Admin, ML |
| `adminCreateABTest` | Callable | `{ testConfig }` | AB test record | Super Admin, ML |
| `adminStopABTest` | Callable | `{ testId, declareWinner? }` | Test results | Super Admin, ML |
| `adminListRules` | Callable | `{ page, sort }` | Rule list | Super Admin, ML |
| `adminCreateRule` | Callable | `{ rule }` | Created rule | Super Admin, ML |
| `adminUpdateRule` | Callable | `{ ruleId, updates }` | Updated rule | Super Admin, ML |
| `adminDeleteRule` | Callable | `{ ruleId }` | Deletion confirmation | Super Admin, ML |
| `adminExportTrainingData` | Callable | `{ dateRange, anonymize }` | Download URL | Super Admin, ML |

### 8.6 Subscription & Revenue

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminGetRevenueMetrics` | Callable | `{ period }` | Revenue dashboard data | Super Admin, Finance |
| `adminListSubscriptions` | Callable | `{ page, pageSize, filters }` | Paginated sub list | Super Admin, Finance |
| `adminVerifyPurchase` | Callable | `{ orderId or userId }` | Verification result | Super Admin, Finance |
| `adminGrantPremium` | Callable | `{ userId, duration, reason }` | Updated subscription | Super Admin, Finance |
| `adminRevokePremium` | Callable | `{ userId, reason }` | Updated subscription | Super Admin |
| `adminInitiateRefund` | Callable | `{ subscriptionId, reason }` | Refund status | Super Admin, Finance |
| `adminCreatePromoCode` | Callable | `{ promoConfig }` | Created promo | Super Admin, Finance |
| `adminUpdatePromoCode` | Callable | `{ promoId, updates }` | Updated promo | Super Admin, Finance |
| `adminDeactivatePromoCode` | Callable | `{ promoId }` | Deactivated promo | Super Admin, Finance |

### 8.7 Push Notifications & Campaigns

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminCreateCampaign` | Callable | `{ campaignConfig }` | Created campaign | Super Admin, Ops |
| `adminSendCampaign` | Callable | `{ campaignId }` | Send status + metrics | Super Admin, Ops |
| `adminCancelCampaign` | Callable | `{ campaignId }` | Cancelled campaign | Super Admin, Ops |
| `adminListCampaigns` | Callable | `{ page, filters }` | Campaign list | Super Admin, Ops |
| `adminGetCampaignMetrics` | Callable | `{ campaignId }` | Delivery/open metrics | Super Admin, Ops |
| `adminCreateAnnouncement` | Callable | `{ announcementConfig }` | Created announcement | Super Admin, Ops |
| `adminUpdateAnnouncement` | Callable | `{ announcementId, updates }` | Updated announcement | Super Admin, Ops |

### 8.8 Feature Flags

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminListFeatureFlags` | Callable | `{ filters }` | Flag list | Super Admin, Ops (read), ML (read) |
| `adminGetFeatureFlag` | Callable | `{ flagId }` | Flag detail + history | Super Admin |
| `adminCreateFeatureFlag` | Callable | `{ flagConfig }` | Created flag | Super Admin |
| `adminUpdateFeatureFlag` | Callable | `{ flagId, updates }` | Updated flag (draft) | Super Admin |
| `adminPublishFeatureFlag` | Callable | `{ flagId }` | Published to Remote Config | Super Admin |
| `adminRollbackFeatureFlag` | Callable | `{ flagId, version }` | Rolled-back flag | Super Admin |
| `adminDeleteFeatureFlag` | Callable | `{ flagId }` | Deleted flag | Super Admin |

### 8.9 Support & Tickets

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminListTickets` | Callable | `{ page, filters, sort }` | Ticket list | Super Admin, Ops, Support |
| `adminGetTicket` | Callable | `{ ticketId }` | Ticket + messages | Super Admin, Ops, Support |
| `adminCreateTicket` | Callable | `{ ticketData }` | Created ticket | Super Admin, Ops, Support |
| `adminReplyToTicket` | Callable | `{ ticketId, message, isInternal }` | Updated ticket | Super Admin, Ops, Support |
| `adminUpdateTicket` | Callable | `{ ticketId, updates }` | Updated ticket | Super Admin, Ops, Support |
| `adminAssignTicket` | Callable | `{ ticketId, adminUid }` | Assigned ticket | Super Admin, Ops |
| `adminEscalateTicket` | Callable | `{ ticketId, toAdminUid, reason }` | Escalated ticket | All support roles |
| `adminCloseTicket` | Callable | `{ ticketId, resolution }` | Closed ticket | Super Admin, Ops, Support |

### 8.10 Security & Admin Management

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminGetAuditLog` | Callable | `{ page, filters }` | Audit entries | Super Admin |
| `adminGetSecurityAlerts` | Callable | `{ filters }` | Alert list | Super Admin |
| `adminAcknowledgeAlert` | Callable | `{ alertId }` | Updated alert | Super Admin |
| `adminListAdmins` | Callable | `{ }` | Admin list | Super Admin |
| `adminInviteAdmin` | Callable | `{ email, role }` | Invitation sent | Super Admin |
| `adminUpdateAdminRole` | Callable | `{ adminUid, newRole }` | Updated admin | Super Admin |
| `adminDeactivateAdmin` | Callable | `{ adminUid, reason }` | Deactivated admin | Super Admin |
| `adminReactivateAdmin` | Callable | `{ adminUid }` | Reactivated admin | Super Admin |
| `adminForceLogoutAdmin` | Callable | `{ adminUid }` | Sessions terminated | Super Admin |
| `adminGetDataAccessLog` | Callable | `{ filters }` | Data access entries | Super Admin |
| `adminExportAuditLog` | Callable | `{ dateRange, format }` | Download URL | Super Admin |

### 8.11 System & Analytics

| Function | Type | Parameters | Returns | Role |
|----------|------|-----------|---------|------|
| `adminGetDashboardKPIs` | Callable | `{ }` | All KPI metrics for Dashboard Home | All |
| `adminGetUserAnalytics` | Callable | `{ period, segment }` | User metrics | All |
| `adminGetPerformanceMetrics` | Callable | `{ period }` | Cloud Function / Firestore metrics | Super Admin, Ops, ML |
| `adminGetMLAnalytics` | Callable | `{ period, filters }` | ML accuracy + distribution | Super Admin, ML |
| `adminGetRevenueAnalytics` | Callable | `{ period }` | Revenue + churn metrics | Super Admin, Finance |
| `adminGetFirebaseStats` | Callable | `{ }` | Firestore / Storage / Auth usage | Super Admin, Ops, ML |
| `adminGetErrorDashboard` | Callable | `{ period }` | Crashlytics + function errors | Super Admin, Ops, ML |
| `adminGetInfraStatus` | Callable | `{ }` | Functions, jobs, hosting status | Super Admin |
| `adminForceRunJob` | Callable | `{ jobName }` | Job execution status | Super Admin |

### 8.12 Endpoint Summary

| Category | Endpoints | Mutations | Reads |
|----------|:---------:|:---------:|:-----:|
| Auth | 3 | 2 | 1 |
| Users | 8 | 6 | 2 |
| Families | 7 | 5 | 2 |
| Transactions | 6 | 3 | 3 |
| ML Models | 12 | 9 | 3 |
| Subscriptions | 9 | 6 | 3 |
| Notifications | 7 | 5 | 2 |
| Feature Flags | 7 | 5 | 2 |
| Support | 8 | 6 | 2 |
| Security | 11 | 5 | 6 |
| System | 9 | 1 | 8 |
| **Total** | **87** | **53** | **34** |

---

## 9. ADMIN SECURITY RULES

### 9.1 Firestore Security Rules for Admin Collections

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // ============================================
    // HELPER FUNCTIONS
    // ============================================
    
    // Check if request is from an authenticated admin
    function isAdmin() {
      return request.auth != null 
        && request.auth.token.admin == true;
    }
    
    // Check if admin has a specific role
    function hasRole(role) {
      return isAdmin() 
        && request.auth.token.admin_role == role;
    }
    
    // Check if admin is Super Admin
    function isSuperAdmin() {
      return hasRole('super_admin');
    }
    
    // Check if admin has any of the given roles
    function hasAnyRole(roles) {
      return isAdmin() 
        && request.auth.token.admin_role in roles;
    }
    
    // ============================================
    // ADMIN COLLECTIONS
    // ============================================
    
    // admin_users — only Super Admin can read/write
    match /admin_users/{adminId} {
      allow read: if isSuperAdmin();
      allow create: if isSuperAdmin();
      allow update: if isSuperAdmin();
      allow delete: if false; // Never delete, only deactivate
    }
    
    // audit_log — Super Admin read, all admins write (via Cloud Functions)
    match /audit_log/{logId} {
      allow read: if isSuperAdmin();
      allow create: if isAdmin(); // Cloud Functions write on behalf of admin
      allow update: if false;     // Immutable
      allow delete: if false;     // Immutable
    }
    
    // support_tickets — Super Admin + Ops + Support
    match /support_tickets/{ticketId} {
      allow read: if hasAnyRole(['super_admin', 'ops_manager', 'support']);
      allow create: if hasAnyRole(['super_admin', 'ops_manager', 'support']);
      allow update: if hasAnyRole(['super_admin', 'ops_manager', 'support']);
      allow delete: if false;
      
      match /messages/{messageId} {
        allow read: if hasAnyRole(['super_admin', 'ops_manager', 'support']);
        allow create: if hasAnyRole(['super_admin', 'ops_manager', 'support']);
        allow update: if false;   // Messages are immutable
        allow delete: if false;
      }
    }
    
    // campaigns — Super Admin + Ops Manager
    match /campaigns/{campaignId} {
      allow read: if hasAnyRole(['super_admin', 'ops_manager']);
      allow create: if hasAnyRole(['super_admin', 'ops_manager']);
      allow update: if hasAnyRole(['super_admin', 'ops_manager']);
      allow delete: if false;
    }
    
    // feature_flags — Super Admin full, Ops + ML read-only
    match /feature_flags/{flagId} {
      allow read: if hasAnyRole(['super_admin', 'ops_manager', 'ml_engineer']);
      allow create: if isSuperAdmin();
      allow update: if isSuperAdmin();
      allow delete: if isSuperAdmin();
      
      match /history/{historyId} {
        allow read: if hasAnyRole(['super_admin', 'ops_manager', 'ml_engineer']);
        allow create: if isSuperAdmin();
        allow update: if false;
        allow delete: if false;
      }
    }
    
    // promo_codes — Super Admin + Finance
    match /promo_codes/{promoId} {
      allow read: if hasAnyRole(['super_admin', 'finance']);
      allow create: if hasAnyRole(['super_admin', 'finance']);
      allow update: if hasAnyRole(['super_admin', 'finance']);
      allow delete: if false;
      
      match /redemptions/{redemptionId} {
        allow read: if hasAnyRole(['super_admin', 'finance']);
        allow create: if false; // Only via Cloud Functions
        allow update: if false;
        allow delete: if false;
      }
    }
    
    // ml_deployments — Super Admin + ML Engineer
    match /ml_deployments/{deploymentId} {
      allow read: if hasAnyRole(['super_admin', 'ml_engineer']);
      allow create: if hasAnyRole(['super_admin', 'ml_engineer']);
      allow update: if hasAnyRole(['super_admin', 'ml_engineer']);
      allow delete: if false;
    }
    
    // ab_tests — Super Admin + ML Engineer
    match /ab_tests/{testId} {
      allow read: if hasAnyRole(['super_admin', 'ml_engineer']);
      allow create: if hasAnyRole(['super_admin', 'ml_engineer']);
      allow update: if hasAnyRole(['super_admin', 'ml_engineer']);
      allow delete: if false;
    }
    
    // ============================================
    // ADMIN READ ACCESS TO APP COLLECTIONS
    // ============================================
    
    // Admins can read app collections (not write — writes go through Cloud Functions)
    
    match /users/{userId} {
      // Existing app rules first...
      // Admin overlay:
      allow read: if hasAnyRole(['super_admin', 'ops_manager', 'ml_engineer', 'support']);
    }
    
    match /families/{familyId}/{document=**} {
      // Existing app rules first...
      // Admin overlay:
      allow read: if hasAnyRole(['super_admin', 'ops_manager', 'ml_engineer', 'support']);
    }
    
    match /subscriptions/{subId} {
      // Existing app rules first...
      // Admin overlay:
      allow read: if hasAnyRole(['super_admin', 'ops_manager', 'finance']);
    }
    
    match /ml_corrections/{correctionId} {
      // Existing app rules first...
      // Admin overlay:
      allow read: if hasAnyRole(['super_admin', 'ml_engineer']);
    }
  }
}
```

### 9.2 Service Account Pattern

Admin Cloud Functions execute with a **dedicated admin service account** that has:
- `roles/datastore.user` on Firestore (read/write all collections)
- `roles/firebase.admin` on Firebase project
- `roles/storage.admin` on Cloud Storage (for model uploads)
- `roles/cloudscheduler.admin` for job management

The service account is **NOT** the same as the default Cloud Functions runtime service account. This separation ensures:
- Admin operations are auditable separately
- Revoking admin service account doesn't affect app functions
- Principle of least privilege: admin SA has broader access, app SA has minimal access

### 9.3 Data Protection

| Concern | Mitigation |
|---------|-----------|
| Admin sees encrypted fields | Admin SDK reads ciphertext only: decryption keys are per-user, not available to admin |
| PII in training data export | `adminExportTrainingData` strips all PII: no phone, no UID, no names. Only tokenized SMS + category labels |
| Audit log tampering | `audit_log` is immutable (no update/delete rules), with 2-year TTL |
| Admin account compromise | MFA required for Super Admin, session duration 8h, IP logging, anomaly alerts |
| Cross-admin data access | Data Access Log tracks every user-data read per admin (DPDP compliance) |

---

## 10. NAVIGATION & LAYOUT ARCHITECTURE

### 10.1 Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  TOPBAR                                                  │
│  [Xpenz Logo]    [Search Bar]    [Notifications] [Avatar]│
├──────────┬───────────────────────────────────────────────┤
│          │                                               │
│ SIDEBAR  │           MAIN CONTENT AREA                  │
│          │                                               │
│ ⬡ Home   │   Breadcrumbs: Dashboard > Users > Detail    │
│ 👤 Users │   ┌─────────────────────────────────────┐    │
│ 👨‍👩‍👧‍👦 Family│   │                                     │    │
│ 💳 Txns  │   │         PAGE CONTENT                │    │
│ 🤖 ML    │   │                                     │    │
│ 💰 Subs  │   │   (varies by module/screen)         │    │
│ 🔔 Notif │   │                                     │    │
│ 🚩 Flags │   │                                     │    │
│ 📊 Stats │   │                                     │    │
│ 🎫 Help  │   │                                     │    │
│ 🔒 Sec   │   └─────────────────────────────────────┘    │
│ ⚙️ Sys   │                                               │
│          │                                               │
│ [v1.0]   │                                               │
├──────────┴───────────────────────────────────────────────┤
│  FOOTER: © 2026 Xpenz Team · admin.xpenz.app            │
└─────────────────────────────────────────────────────────┘
```

### 10.2 Sidebar Behavior

| State | Behavior |
|-------|----------|
| Desktop (> 1280px) | Fixed sidebar, 256px width, always visible |
| Tablet (768-1280px) | Collapsible sidebar, icon-only (64px) with tooltip labels |
| Mobile (< 768px) | Hidden sidebar, hamburger menu → sheet overlay |

### 10.3 Topbar Components

| Element | Position | Behavior |
|---------|----------|----------|
| Logo | Left | Links to Dashboard Home |
| Global Search | Center | Cmd+K shortcut, searches users/families/tickets/transactions |
| Notification Bell | Right | Badge count of unread alerts (from K2) |
| Avatar Dropdown | Right | Profile, preferences (dark mode toggle), logout |

### 10.4 Breadcrumbs

Auto-generated from route segments:
- `/` → Dashboard
- `/users` → Dashboard > Users
- `/users/abc123` → Dashboard > Users > John Doe
- `/ml-models/accuracy` → Dashboard > ML Models > Accuracy Monitor

### 10.5 Command Palette

`Cmd+K` (or `Ctrl+K`) opens a command palette (shadcn/ui `CommandDialog`):
- Type to search users, families, tickets, transactions
- Quick actions: "Create ticket", "Send notification", "Deploy model"
- Navigation: "Go to ML Dashboard", "Go to Security"

---

## 11. DESIGN SYSTEM TOKENS

> These tokens match the Xpenz mobile app's design language for brand consistency.

### 11.1 Tailwind Theme Extension

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        serif: ['Lora', 'Georgia', 'serif'],
      },
      colors: {
        // Brand
        primary: {
          50:  '#eef2ff',
          100: '#dde5ff',
          200: '#c3ccff',
          300: '#9aa8ff',
          400: '#6c7bfa',
          500: '#4f54f0',
          600: '#3d39e5',
          700: '#1b3fc0',  // ← Primary brand color (from mobile app)
          800: '#1a339b',
          900: '#1b2f7a',
          950: '#121c49',
        },
        
        // Backgrounds
        surface: {
          light: '#f6f6f8',    // Mobile app light BG
          dark:  '#111521',    // Mobile app dark BG
        },
        
        // Status colors
        success: {
          50:  '#ecfdf5',
          500: '#10b981',      // Green (from mobile app)
          600: '#059669',
          700: '#047857',
        },
        warning: {
          50:  '#fffbeb',
          500: '#f59e0b',      // Amber (from mobile app)
          600: '#d97706',
          700: '#b45309',
        },
        danger: {
          50:  '#fef2f2',
          500: '#ef4444',      // Red
          600: '#dc2626',
          700: '#b91c1c',
        },
        
        // Neutral
        slate: {
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
      },
      
      borderRadius: {
        'xl':  '0.75rem',     // 12px
        '2xl': '1rem',        // 16px (mobile app card radius)
        '3xl': '1.5rem',      // 24px
      },
      
      boxShadow: {
        'card': '0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04)',
        'sidebar': '2px 0 8px rgba(0, 0, 0, 0.04)',
      },
      
      fontSize: {
        'display': ['2.25rem', { lineHeight: '2.5rem', fontWeight: '800' }],
        'heading': ['1.5rem', { lineHeight: '2rem', fontWeight: '700' }],
        'subheading': ['1.125rem', { lineHeight: '1.75rem', fontWeight: '600' }],
        'body': ['0.875rem', { lineHeight: '1.375rem', fontWeight: '400' }],
        'caption': ['0.75rem', { lineHeight: '1rem', fontWeight: '500' }],
      },
      
      spacing: {
        'sidebar': '256px',
        'sidebar-collapsed': '64px',
        'topbar': '64px',
      },
      
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in': 'slideIn 0.2s ease-out',
      },
      
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(-10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),      // For shadcn/ui animations
    require('@tailwindcss/typography'),   // For rich text (knowledge base)
  ],
};

export default config;
```

### 11.2 CSS Variables (Light + Dark)

```css
/* globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Light mode */
    --background: 240 6% 97%;           /* #f6f6f8 */
    --foreground: 222 47% 11%;          /* slate-900 */
    --card: 0 0% 100%;                  /* white */
    --card-foreground: 222 47% 11%;
    --primary: 226 74% 43%;             /* #1b3fc0 */
    --primary-foreground: 0 0% 100%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222 47% 11%;
    --muted: 210 40% 96%;
    --muted-foreground: 215 16% 47%;
    --accent: 210 40% 96%;
    --accent-foreground: 222 47% 11%;
    --destructive: 0 84% 60%;          /* #ef4444 */
    --destructive-foreground: 0 0% 100%;
    --border: 214 32% 91%;             /* slate-200 */
    --input: 214 32% 91%;
    --ring: 226 74% 43%;               /* #1b3fc0 */
    --radius: 1rem;                    /* 16px — matches mobile app */
    
    /* Status */
    --success: 160 84% 39%;            /* #10b981 */
    --warning: 38 92% 50%;             /* #f59e0b */
    --danger: 0 84% 60%;              /* #ef4444 */
    
    /* Sidebar */
    --sidebar-bg: 0 0% 100%;
    --sidebar-border: 214 32% 91%;
    --sidebar-active: 226 74% 43%;
    --sidebar-active-text: 0 0% 100%;
  }

  .dark {
    /* Dark mode */
    --background: 228 35% 10%;          /* #111521 */
    --foreground: 210 40% 98%;          /* slate-50 */
    --card: 224 30% 14%;               /* slightly lighter than bg */
    --card-foreground: 210 40% 98%;
    --primary: 226 74% 50%;            /* Slightly lighter for dark mode */
    --primary-foreground: 0 0% 100%;
    --secondary: 224 30% 18%;
    --secondary-foreground: 210 40% 98%;
    --muted: 224 30% 18%;
    --muted-foreground: 215 20% 65%;
    --accent: 224 30% 22%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 63% 55%;
    --destructive-foreground: 0 0% 100%;
    --border: 224 30% 22%;
    --input: 224 30% 22%;
    --ring: 226 74% 55%;
    --radius: 1rem;
    
    /* Status (slightly adjusted for dark) */
    --success: 160 84% 45%;
    --warning: 38 92% 55%;
    --danger: 0 63% 55%;
    
    /* Sidebar */
    --sidebar-bg: 228 35% 8%;
    --sidebar-border: 224 30% 18%;
    --sidebar-active: 226 74% 50%;
    --sidebar-active-text: 0 0% 100%;
  }
}
```

### 11.3 Component Patterns

| Component | Styling |
|-----------|---------|
| **Cards** | `bg-card rounded-2xl shadow-card border border-border p-6` |
| **Tables** | `rounded-xl border border-border overflow-hidden` with striped rows via `even:bg-muted/50` |
| **Buttons (Primary)** | `bg-primary text-primary-foreground rounded-xl px-4 py-2.5 font-semibold hover:bg-primary/90 transition-colors` |
| **Buttons (Secondary)** | `bg-secondary text-secondary-foreground rounded-xl px-4 py-2.5 font-medium border border-border hover:bg-accent transition-colors` |
| **Buttons (Danger)** | `bg-danger text-white rounded-xl px-4 py-2.5 font-semibold hover:bg-danger/90 transition-colors` |
| **Inputs** | `rounded-xl border border-input bg-background px-3 py-2 text-body focus:ring-2 focus:ring-ring focus:border-transparent` |
| **Badges (Status)** | `rounded-full px-2.5 py-0.5 text-xs font-semibold` + status color variant |
| **Sidebar Items** | `rounded-xl px-3 py-2.5 text-sm font-medium transition-colors` + active: `bg-sidebar-active text-sidebar-active-text` |
| **Stat Cards (KPI)** | `bg-card rounded-2xl shadow-card border border-border p-5` with large number (font-display), small trend arrow + percentage |
| **Charts** | Recharts with `colors.primary[700]`, `colors.success[500]`, `colors.warning[500]` palette |

### 11.4 Icons

```html
<!-- Material Symbols Outlined (matches mobile app) -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
```

Usage in components (via a thin wrapper):
```tsx
// components/ui/icon.tsx
interface IconProps {
  name: string;
  size?: number;
  className?: string;
}

export function Icon({ name, size = 24, className = '' }: IconProps) {
  return (
    <span 
      className={`material-symbols-outlined ${className}`}
      style={{ fontSize: size }}
    >
      {name}
    </span>
  );
}

// Usage:
<Icon name="dashboard" />
<Icon name="person" size={20} className="text-muted-foreground" />
```

### 11.5 Typography Scale

| Name | Size | Weight | Usage |
|------|------|--------|-------|
| Display | 36px / 2.25rem | 800 | Page titles, large stats |
| Heading | 24px / 1.5rem | 700 | Section headings, card titles |
| Subheading | 18px / 1.125rem | 600 | Sub-section titles, table headers |
| Body | 14px / 0.875rem | 400 | Body text, table cells, form labels |
| Caption | 12px / 0.75rem | 500 | Timestamps, help text, badges |

### 11.6 Responsive Breakpoints

| Name | Width | Target |
|------|-------|--------|
| `sm` | 640px | Small tablets |
| `md` | 768px | Tablets |
| `lg` | 1024px | Small desktop |
| `xl` | 1280px | Desktop (primary) |
| `2xl` | 1536px | Large monitors |

Primary design target: 1280px-1440px (typical admin user setup)

---

## 12. IMPLEMENTATION PLAN

> The admin dashboard is added to the existing 20-week roadmap as an extension.  
> It fits into Sprints 7-10 (weeks 15-20) alongside advanced mobile app features.

### 12.1 Sprint 7 (Weeks 15-16): Admin Foundation + Core Modules

**Week 15 — Setup & Auth:**
| Day | Task |
|-----|------|
| D1 | Initialize Next.js 14 project, configure TypeScript, Tailwind, shadcn/ui |
| D1 | Set up monorepo or separate repo, CI/CD with Firebase Hosting |
| D2 | Implement Google Workspace SSO flow (Firebase Auth + custom claims) |
| D2 | Create `admin_users` collection, seed Super Admin account |
| D3 | Build middleware.ts: route guards, role checking, session management |
| D3 | Build sidebar + topbar + dashboard layout |
| D4 | Implement dark mode toggle (class-based, localStorage persistence) |
| D4 | Build command palette (Cmd+K) with basic navigation |
| D5 | Review, fix linting, deploy to staging |

**Week 16 — Dashboard Home + Users + Families:**
| Day | Task |
|-----|------|
| D1 | Module A: Dashboard Home — KPI cards, sparklines, charts |
| D1 | Implement `adminGetDashboardKPIs` Cloud Function |
| D2 | Module B1: User List — TanStack Table, pagination, filters |
| D2 | Implement `adminListUsers` Cloud Function |
| D3 | Module B2: User Detail — Tabbed view (5 tabs), all actions |
| D3 | Implement user mutation Cloud Functions (suspend, force-logout, etc.) |
| D4 | Module C1: Family List + C2: Family Detail |
| D4 | Implement `adminListFamilies`, `adminGetFamily` Cloud Functions |
| D5 | Module C3: Family Disputes + integration testing |

**Deliverables — Sprint 7:**
- ✅ Admin login with Google Workspace SSO
- ✅ Role-based routing and middleware
- ✅ Dashboard Home with real-time KPIs
- ✅ User Management (list + detail + actions)
- ✅ Family Management (list + detail + disputes)
- ✅ Dark mode support
- ✅ Command palette
- ✅ 13 Cloud Functions deployed

### 12.2 Sprint 8 (Weeks 17-18): Transactions + ML + Subscriptions

**Week 17 — Transactions + ML:**
| Day | Task |
|-----|------|
| D1 | Module D1: Transaction Feed with real-time onSnapshot |
| D1 | Module D2: Flagged Transactions (auto-flag rules) |
| D2 | Module D3: Category Overrides |
| D2 | Implement `adminListTransactions`, `adminFlagTransaction`, `adminOverrideCategory` |
| D3 | Module E1: ML Dashboard — gauge charts, ensemble distribution pie |
| D3 | Module E2: Model Upload & Deploy — file upload, validation, staged rollout |
| D4 | Module E3: A/B Tests — create, monitor, declare winner |
| D4 | Module E4: Rule Editor — CRUD, test, import/export |
| D5 | Module E5: Accuracy Monitor — heatmaps, confusion matrix |

**Week 18 — ML (cont.) + Subscriptions:**
| Day | Task |
|-----|------|
| D1 | Module E6: Training Data — export, anonymization preview |
| D1 | Implement all ML Cloud Functions (8 functions) |
| D2 | Module F1: Revenue Dashboard — MRR, churn, ARPU charts |
| D2 | Module F2: Subscription List |
| D3 | Module F3: Purchase Verification (Google Play API integration) |
| D3 | Module F4: Promo Codes (CRUD, redemption analytics) |
| D4 | Implement subscription Cloud Functions (6 functions) |
| D4 | Set up `ml_deployments`, `ab_tests`, `promo_codes` collections |
| D5 | Integration testing, staging deploy |

**Deliverables — Sprint 8:**
- ✅ Transaction Monitoring (feed + flagged + overrides)
- ✅ ML Model Management (6 screens)
- ✅ Subscription & Revenue (4 screens)
- ✅ Auto-flagging rules for transactions
- ✅ Model deployment pipeline with staged rollout
- ✅ A/B testing framework
- ✅ 20+ additional Cloud Functions

### 12.3 Sprint 9 (Weeks 19-20): Notifications + Flags + Analytics + Support

**Week 19 — Notifications + Feature Flags + Analytics:**
| Day | Task |
|-----|------|
| D1 | Module G1: Notification Creator — form, preview, FCM send |
| D1 | Module G2: Notification History with delivery metrics |
| D2 | Module G3: Announcements (in-app banners) |
| D2 | Implement `campaigns` collection + Cloud Functions |
| D3 | Module H1: Feature Flags Dashboard |
| D3 | Module H2: Flag Editor — conditions, targeting, preview |
| D4 | Module H3: Flag History + rollback |
| D4 | Sync feature_flags collection ↔ Firebase Remote Config |
| D5 | Module I1-I4: Analytics tabs (user, performance, ML, revenue) |

**Week 20 — Support + Security + System:**
| Day | Task |
|-----|------|
| D1 | Module J1: Ticket Queue — SLA indicators, assignment |
| D1 | Module J2: Ticket Detail — split pane, conversation thread |
| D2 | Module J3: Knowledge Base — CRUD, search, canned responses |
| D2 | Implement `support_tickets` collection + Cloud Functions |
| D3 | Module K1: Audit Log — immutable log viewer, export |
| D3 | Module K2: Security Alerts — automated alerting |
| D4 | Module K3: Admin Management — invite, role change, deactivate |
| D4 | Module K4: Data Access Log (DPDP compliance) |
| D5 | Module L1-L3: System Health (Firebase stats, errors, infra) |

**Deliverables — Sprint 9:**
- ✅ Push Notifications & Campaigns (3 screens)
- ✅ Feature Flags (3 screens) synced with Remote Config
- ✅ Analytics dashboards (4 screens)
- ✅ Support system (3 screens with SLA)
- ✅ Security & Audit (4 screens)
- ✅ System Health (3 screens)
- ✅ All 42 screens complete

### 12.4 Sprint 10 (Weeks 21-22): Polish, Testing & Launch

| Day | Task |
|-----|------|
| W21 D1-2 | E2E tests with Playwright (all critical flows) |
| W21 D3-4 | Performance optimization: lazy loading, RSC optimization, Firestore pagination tuning |
| W21 D5 | Accessibility audit (WCAG 2.1 AA for admin tools) |
| W22 D1-2 | Security audit: penetration testing, OWASP top 10 checks |
| W22 D3 | Documentation: admin user guide, runbook for common operations |
| W22 D4 | Production deployment, DNS config for admin.xpenz.app |
| W22 D5 | Team onboarding: train all admin roles on dashboard usage |

**Deliverables — Sprint 10:**
- ✅ Full E2E test suite
- ✅ Performance-optimized admin dashboard
- ✅ Security-audited and hardened
- ✅ Admin user guide + operational runbooks
- ✅ Production deployment at `admin.xpenz.app`
- ✅ Team trained and operational

### 12.5 Revised Timeline Summary

| Sprint | Weeks | Mobile App | Admin Dashboard |
|--------|-------|-----------|-----------------|
| 0-1 | 1-4 | Setup + Auth + Core DB | — |
| 2-3 | 5-8 | ML Training + SMS/Notification Detection | — |
| 4-5 | 9-12 | Onboarding + Family + Budget (**MVP Complete**) | — |
| 6 | 13-14 | Premium + Export + Polish | — |
| **7** | **15-16** | Advanced mobile features | **Admin: Foundation + Users + Families** |
| **8** | **17-18** | Mobile polish + edge cases | **Admin: Transactions + ML + Subs** |
| **9** | **19-20** | Mobile hardening | **Admin: Notifications + Flags + Analytics + Support + Security + System** |
| **10** | **21-22** | Final mobile testing | **Admin: Polish + Testing + Launch** |

---

## 13. DEPLOYMENT & DEVOPS

### 13.1 Repository Structure

```
xpenz-admin/                      ← Separate repo (or monorepo subfolder)
├── app/                          ← Next.js App Router
├── components/                   ← Shared UI components
│   ├── ui/                      ← shadcn/ui components
│   ├── layout/                  ← Sidebar, Topbar, Layout
│   ├── charts/                  ← Recharts wrappers
│   ├── tables/                  ← TanStack Table wrappers
│   └── forms/                   ← Form components
├── lib/                         ← Utilities
│   ├── firebase/                ← Firebase Admin + Client SDK setup
│   ├── auth/                    ← Session management, middleware helpers
│   ├── api/                     ← Cloud Function call wrappers
│   └── utils/                   ← Date formatters, validators, etc.
├── types/                       ← TypeScript interfaces (from Section 7)
├── public/                      ← Static assets
├── tests/
│   ├── unit/                    ← Vitest unit tests
│   └── e2e/                     ← Playwright E2E tests
├── .env.local                   ← Local env vars
├── .env.production              ← Production env vars
├── firebase.json                ← Firebase Hosting config
├── next.config.ts               ← Next.js config
├── tailwind.config.ts           ← Tailwind config (Section 11.1)
├── tsconfig.json
├── package.json
└── pnpm-lock.yaml
```

### 13.2 Environment Variables

```env
# Firebase
NEXT_PUBLIC_FIREBASE_API_KEY=       # Client-side Firebase key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=   # e.g., xpenz-app.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=    # e.g., xpenz-app
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=

# Firebase Admin (server-side only)
FIREBASE_ADMIN_SERVICE_ACCOUNT=     # JSON string or path to service account file

# Admin Config
ADMIN_ALLOWED_DOMAIN=xpenz.app     # Google Workspace domain restriction
ADMIN_SESSION_DURATION=28800000    # 8 hours in milliseconds
ADMIN_MAX_FAILED_LOGINS=5
ADMIN_LOCKOUT_DURATION=1800000     # 30 minutes in milliseconds

# External APIs
GOOGLE_PLAY_DEVELOPER_API_KEY=     # For purchase verification
SENDGRID_API_KEY=                  # For admin alert emails

# Feature
NEXT_PUBLIC_APP_URL=https://admin.xpenz.app
```

### 13.3 CI/CD Pipeline

```yaml
# .github/workflows/admin-deploy.yml
name: Deploy Admin Dashboard
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm type-check
      - run: pnpm test

  deploy-staging:
    if: github.event_name == 'pull_request'
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: ${{ secrets.GITHUB_TOKEN }}
          firebaseServiceAccount: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
          projectId: xpenz-app
          channelId: 'admin-pr-${{ github.event.number }}'

  deploy-production:
    if: github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: ${{ secrets.GITHUB_TOKEN }}
          firebaseServiceAccount: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
          projectId: xpenz-app
          channelId: live
          target: admin
```

### 13.4 Firebase Hosting Configuration

```json
{
  "hosting": [
    {
      "target": "admin",
      "public": "out",
      "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
      "rewrites": [
        {
          "source": "**",
          "destination": "/index.html"
        }
      ],
      "headers": [
        {
          "source": "**",
          "headers": [
            { "key": "X-Frame-Options", "value": "DENY" },
            { "key": "X-Content-Type-Options", "value": "nosniff" },
            { "key": "X-XSS-Protection", "value": "1; mode=block" },
            { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
            { "key": "Content-Security-Policy", "value": "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https: blob:; connect-src 'self' https://*.googleapis.com https://*.firebaseio.com wss://*.firebaseio.com https://*.firebase.com" }
          ]
        }
      ]
    }
  ]
}
```

---

## 14. APPENDIX: WIRE-FLOW DIAGRAMS

### 14.1 Admin Login Flow

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│  /login   │───→│ Google OAuth  │───→│ Firebase Auth │───→│ Cloud Func  │
│           │    │ (@xpenz.app) │    │   (verify)   │    │ (set claims)│
└──────────┘    └──────────────┘    └──────────────┘    └──────┬──────┘
                                                              │
    ┌──────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────┐    ┌──────────────┐    ┌───────────────┐
│ Set Session  │───→│ Write Audit  │───→│  Redirect to  │
│   Cookie     │    │    Log       │    │  /dashboard   │
└─────────────┘    └──────────────┘    └───────────────┘
```

### 14.2 ML Model Deployment Flow

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Upload  │───→│ Validate │───→│  Canary  │───→│  Staged  │
│  .tflite │    │  (auto)  │    │   (1%)   │    │  (10%)   │
└─────────┘    └──────────┘    └──────────┘    └──────────┘
                    │                │                │
                    │ fail           │ accuracy       │ accuracy
                    ▼                │ drops > 3%     │ drops > 2%
                ┌────────┐          ▼                ▼
                │ Reject │    ┌──────────┐    ┌──────────┐
                └────────┘    │ Rollback │    │ Rollback │
                              └──────────┘    └──────────┘

     ┌──────────┐    ┌──────────┐
───→│  Wider   │───→│   Full   │
     │  (50%)   │    │  (100%)  │
     └──────────┘    └──────────┘
          │                │
          │ accuracy       │ ✅ Production
          │ drops > 1%     │
          ▼                │
     ┌──────────┐         │
     │ Rollback │         │
     └──────────┘         │
                          ▼
                    ┌──────────┐
                    │ Archive  │
                    │ previous │
                    └──────────┘
```

### 14.3 Support Ticket Lifecycle

```
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Open   │───→│ In Progress  │───→│ Waiting User │───→│  Resolved    │
│         │    │ (assigned)    │    │ (responded)  │    │  (solution)  │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘
    │                │                     │                    │
    │ escalate       │ escalate            │ user replies       │ user confirms
    ▼                ▼                     ▼                    ▼
┌─────────┐    Re-enters            Re-enters             ┌──────────┐
│Escalated│    In Progress          In Progress            │  Closed  │
│(to SA)  │                                                │  (done)  │
└─────────┘                                                └──────────┘
```

### 14.4 Feature Flag Publish Flow

```
┌─────────┐    ┌──────────┐    ┌──────────────┐    ┌───────────────┐
│ Create  │───→│   Edit   │───→│   Preview    │───→│   Publish     │
│ (draft) │    │ (values) │    │ (diff view)  │    │ (to Remote    │
└─────────┘    └──────────┘    └──────────────┘    │  Config)      │
                                                    └───────┬───────┘
                                                            │
     ┌──────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────┐    ┌──────────────┐
│  History    │───→│  Rollback    │───→ (back to Publish with old values)
│  (version)  │    │  (revert)    │
└─────────────┘    └──────────────┘
```

---

## END OF DOCUMENT

> **Total Screens:** 42 across 12 modules  
> **Total Cloud Functions (Admin):** 87 endpoints  
> **Total New Firestore Collections:** 8  
> **Implementation Timeline:** Sprints 7-10 (Weeks 15-22)  
> **Hosting:** `admin.xpenz.app` via Firebase Hosting  
> **Design System:** Matches Xpenz mobile app (Manrope, #1b3fc0, Material Symbols, rounded-2xl cards)
