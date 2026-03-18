# 🗺️ ROADMAP — VetCore Platform

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

## 🚧 FASE 2 — Licenses + Auto-update (NEXT)

### License Hardening
- [ ] Encrypt payload in `/check-license` request/response
- [ ] Anti-tampering: server-side hardware fingerprint validation
- [ ] Grace period logic: allow 3-day offline window before blocking

### Release System
- [ ] `GET /releases/latest` — returns latest active version + download URL
- [ ] `GET /releases/download/{version}` — signed binary download
- [ ] Admin: create/deactivate releases via JWT endpoints
- [ ] Desktop: startup check → notification → auto-download + install

---

## 📅 FASE 3 — Unified Sign-in + Roles

### Registration & Auth
- [ ] Unified sign-in page for SaaS (email + password)
- [ ] Account type selection at registration: Veterinary, Supplier, or Both
- [ ] Email verification + password recovery
- [ ] Tenant creation on registration (with type: VET | SUPPLIER | BOTH)

### SaaS Onboarding
- [ ] Cloud onboarding wizard (similar to Desktop setup_wizard)
- [ ] If type = BOTH: combined menu (vet features + supplier portal tab)

---

## 📅 FASE 4 — Master Catalog + Barcode Lookup

### Cloud Catalog
- [ ] `MasterProduct` model: EAN, description, category, brand, suggested_price, image_url, source
- [ ] Seed from free APIs: Open Food Facts, UPC Database
- [ ] `GET /catalog/search?q=` — search by name or EAN
- [ ] `GET /catalog/lookup/{barcode}` — barcode → product info

### Desktop Integration
- [ ] POS/Inventory scan: if product not found locally → query cloud catalog
- [ ] Auto-create local product from catalog match (user edits price/cost)
- [ ] Periodic sync: Desktop downloads master catalog for offline use

---

## 📅 FASE 5 — Suppliers + Marketplace + Orders

### Supplier Model
- [ ] Supplier = Tenant with type SUPPLIER or BOTH
- [ ] `SupplierProduct`: supplier FK, master_product FK (nullable), SKU, description, price, stock

### Supplier Portal (within SaaS)
- [ ] Dashboard with metrics (orders received, products listed)
- [ ] Product CRUD with barcode scan → master catalog matching
- [ ] Geographic zone: provinces/states where supplier operates

### Order System
- [ ] `Order` + `OrderItem` with state machine:
  `DRAFT → PLACED → QUOTED → ACCEPTED → PAYMENT_AGREED → SHIPPED → DELIVERED → CANCELLED`
- [ ] Flow: Vet browses suppliers in zone → builds order → supplier quotes → vet accepts → payment → ship → deliver → stock updated
- [ ] Notifications (email + in-app) for state changes

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
│                      vetcore.app (Cloud)                         │
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