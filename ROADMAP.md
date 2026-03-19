# 🗺️ ROADMAP — VetCoreSoft Platform

## Vision
Build a hybrid (offline-first) veterinary management platform combining desktop reliability with cloud intelligence. The system must guarantee continuous operation without internet and sync with a central API for advanced services (AI, catalogs, suppliers, backups).

---

## ✅ FASE 1 — Cloud API Infrastructure (DONE)
> Commit: `3c452c1` — 2026-03-18

- [x] Refactor cloud_api from monolith → modular architecture (routers/, models/, core/)
- [x] SQLAlchemy 2 + Alembic migrations
- [x] JWT admin authentication (login → token → protected endpoints)
- [x] Rate limiting (slowapi), CORS, request logging
- [x] Health check with DB connectivity status
- [x] License CRUD: check, create/renew, revoke, list
- [x] Release and Tenant models (ready for next phases)
- [x] Backward-compatible `/check-license` endpoint for Desktop clients
- [x] Swagger docs at `/docs`

---

## ✅ FASE 2 — Licenses + Owner Portal (DONE)
> 2026-03-18

### License & Identity
- [x] Company identity hardening (email, hardware_id, is_setup_complete immutable after setup)
- [x] Setup wizard auto-registers TRIAL license on cloud_api (fire-and-forget)
- [x] HW mismatch detection: non-blocking warning banner via middleware
- [x] UserProfile.is_owner flag for portal access control
- [x] `owner_required` and `localhost_required` decorators

### Owner Admin Portal (`/platform/`)
- [x] Dashboard with license details, company info
- [x] License CRUD via cloud API (create, view, update, revoke)
- [x] Hardware transfer flow (revoke old → create new license)
- [x] Force password reset on any employee

### Cloud API Enhancements
- [x] License model expanded: plan, notes, company_*, nullable expiration for perpetual
- [x] PendingAction model + auth router (password reset request/confirm)
- [x] Expanded license router: GET single, PATCH, transfer, filtered list
- [x] `/license/check` returns pending_actions[] in response

### Login Experience
- [x] "Forgot password?" modal directing to admin/owner contact
- [x] All Django + Alembic migrations applied

### Deferred to later
- [ ] Encrypt payload in `/check-license` request/response
- [ ] Auto-update system (releases/latest, signed binary download)
- [ ] Grace period logic (3-day offline window)

---

## ✅ FASE 2.5 — Pilot Infrastructure + SaaS Frontend (DONE)
> 2026-03-18

### SaaS Web
- [x] Landing page (`/`) with hero, features, highlights, CTA
- [x] Download page (`/download/`) with step-by-step instructions
- [x] Shared public navbar partial (Home / Download / Sign In — contextual)
- [x] Login page with navbar (SaaS mode)
- [x] Smart home view: SaaS unauthenticated → landing; authenticated → dashboard

### Desktop Packaging
- [x] PyInstaller launcher (`desktop/launcher.py`) with UAC, hosts file, desktop shortcut
- [x] `vetcoresoft.spec`, `build_exe.bat`, `create_icon.py`
- [x] `VETCORE_DATA_DIR` env var for portable data storage
- [x] `vetcoresoft.ini` configurable cloud API URL

### Infrastructure
- [x] nginx reverse proxy (api.vetcoresoft.app → cloud_api, vetcoresoft.app → api_saas)
- [x] Removed api_desktop from docker-compose (SaaS-only)
- [x] ~90+ Spanish translations compiled

---

## ✅ FASE 3 — SaaS Registration + Multi-tenant (DONE)
> 2026-03-19

### Registration & Auth
- [x] Public registration page (`/register/`) with 2-step wizard (account + clinic)
- [x] Cloud API: `POST /tenant/register` — creates Tenant with type, returns tenant_id
- [x] Tenant ↔ Company link (`cloud_tenant_id` stored in Company model)
- [x] Account type selection at registration: Veterinary or Supplier (separate environments)
- [x] `account_type` field on Company model + cloud Tenant.type
- [x] Email verification (EmailVerificationToken model, verification link sent on registration)
- [x] `verify-email/<token>/` endpoint — validates token, marks user email as verified
- [x] `resend-verification/` endpoint for logged-in users
- [x] Password recovery via email (Django PasswordReset views, 4 custom templates)
- [x] Login page: SaaS mode links to `/password-reset/` instead of modal
- [x] SMTP configuration via environment variables (console backend for dev)
- [x] `email_verified` field on UserProfile
- [x] Middleware exemptions for `/verify-email/`, `/password-reset/`
- [x] 23+ new Spanish translations + 11 fuzzy corrections

### SaaS Onboarding
- [x] Registration auto-creates Company + User + UserProfile (ADMIN/owner)
- [x] Auto-login after registration → redirects to dashboard
- [x] VET and SUPPLIER are fully separate environments (same email can register both profiles)

---

## ✅ FASE 4 — Master Catalog + Barcode Lookup (DONE)
> 2026-03-19

### Cloud Catalog
- [x] `MasterProduct` model: EAN, description, category, brand, suggested_price, image_url, source
- [x] Seed from free APIs: Open Food Facts (`seed_catalog.py --categories`)
- [x] `GET /catalog/search?q=` — search by name, brand, or EAN
- [x] `GET /catalog/lookup/{barcode}` — barcode → product info
- [x] `POST /catalog/products` — admin create/upsert

### Desktop/SaaS Integration
- [x] `GET /catalog/lookup/?barcode=` — Django proxy to cloud catalog
- [x] `POST /catalog/import/` — auto-create local product from catalog match
- [x] POS scan: if product not found locally → async cloud catalog query
- [x] Scanner feedback: "Searching catalog..." → import prompt with price input
- [x] Manual barcode input also falls back to cloud catalog
- [x] Alembic migration for master_products table

---

## ✅ FASE 5 — Suppliers + Marketplace + Orders (DONE)
> 2026-03-19

### Supplier Model
- [x] Supplier = Tenant with type SUPPLIER
- [x] `SupplierProduct`: tenant FK, master_product FK (nullable), SKU, EAN, description, price, stock
- [x] Tenant JWT authentication (`POST /tenant/token`)
- [x] `cloud_tenant_token` stored on Django Company model

### Supplier Portal (within SaaS)
- [x] Dashboard with product listing (`/marketplace/supplier/`)
- [x] Product CRUD: add, edit, deactivate
- [x] Cloud API: `GET/POST/PATCH/DELETE /supplier/products`

### Marketplace (for Vets)
- [x] Browse suppliers: `GET /supplier/search?q=&region=`
- [x] Search page with region filtering (`/marketplace/`)
- [x] View supplier product catalogs

### Order System
- [x] `Order` + `OrderItem` models with state machine:
  `DRAFT → PLACED → QUOTED → ACCEPTED → SHIPPED → DELIVERED → CANCELLED`
- [x] Cloud API: full order lifecycle endpoints
  - `POST /orders/` (create), `GET /orders/my` (list)
  - `/place`, `/quote`, `/accept`, `/ship`, `/deliver`, `/cancel`
- [x] Django views: order list, detail, state transitions
- [x] Buyer can: create, place, accept quote, confirm delivery, cancel
- [x] Supplier can: view received orders, quote, ship, cancel
- [x] Navigation: Marketplace dropdown in base.html (browse, orders, my products)
- [x] 4 marketplace templates: search, supplier dashboard, product form, order list, order detail
- [x] Alembic migration for supplier_products + orders + order_items

---

## 🔮 FASE 6 — AI Agent

### 6A: Invoice OCR (vets & suppliers)
- [ ] `POST /ai/process-invoice` — image → LLM (Gemini Vision / GPT-4V)
- [ ] Extract: items, quantities, prices, supplier
- [ ] Fuzzy match against local inventory + master catalog
- [ ] UI: "Load stock from invoice" button → camera/upload → preview → confirm

### 6B: Clinical Assistant (vets only)
- [ ] `POST /ai/chat` — free chat with clinical context
- [ ] `POST /ai/differential` — symptoms → differential diagnoses
- [ ] `POST /ai/treatment` — suggest treatment + dosage by weight/age/breed
- [ ] `POST /ai/analyze-lab` — lab PDF → anomalous values
- [ ] Context sent: full medical history, breed, age, weight, species
- [ ] Multi-provider abstraction (Gemini / OpenAI / Claude — configurable)
- [ ] Rate limiting by plan (Free: 10/month, Pro: unlimited)

---

## 🔮 FASE 7 — Sync + Backup + Build

### Offline-First Sync
- [ ] `PendingSync` queue on Desktop
- [ ] `POST /sync/push` + `GET /sync/pull`
- [ ] Conflict resolution strategy

### Cloud Backup
- [ ] `POST /backup/upload` — encrypted SQLite upload
- [ ] `GET /backup/download` — restore from cloud
- [ ] Automatic scheduled backups

### Windows Distribution
- [ ] PyInstaller → `.exe` packaging
- [ ] Inno Setup installer
- [ ] Auto-updater that checks `/releases/latest`

---

## Known Technical Debt
- Multi-tenant inconsistency: some views don't filter by company
- Sales don't automatically deduct stock (SaleItem doesn't create StockMovement)

---

## Architecture Diagram
```
┌──────────────────────────────────────────────────────────────────┐
│                      vetcoresoft.app (Cloud)                         │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  FastAPI Cloud API (PostgreSQL)                          │    │
│  │  /license  /releases  /catalog  /ai  /sync  /backup     │    │
│  └─────────────────┬────────────────┬───────────────────────┘    │
│                    │                │                             │
│       ┌────────────┴──┐    ┌───────┴────────┐                    │
│       │  Desktop .exe │    │  SaaS (Web)    │                    │
│       │  SQLite local │    │  PostgreSQL    │                    │
│       │  Offline-first│    │  Multi-tenant  │                    │
│       │  Port 8000    │    │  Port 8001     │                    │
│       └───────────────┘    └────────────────┘                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Supplier Portal (within SaaS)                           │    │
│  │  Product catalog — Order management — Invoice OCR        │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```