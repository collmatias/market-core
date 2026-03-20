# 🗺️ ROADMAP — MarketCoreSoft Platform

## Vision
Build a hybrid (offline-first) business management platform combining desktop reliability with cloud intelligence. Designed for retail stores, supermarkets, butcher shops, warehouses, and similar businesses. The system must guarantee continuous operation without internet and sync with a central API for advanced services (catalogs, suppliers, analytics, backups).

---

## ✅ FASE 1 — Cloud API Infrastructure (DONE)
> 2026-03-18

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

## ✅ FASE 2 — MarketCoreSoft Rebrand (DONE)
> 2026-03-20

- [x] VetCore → MarketCoreSoft rebranding (all code, templates, docs)
- [x] Removed clinical module (patients, medical records, appointments, schedule)
- [x] Removed Vetter (FoxPro) import service
- [x] Adapted roles: VET → CASHIER, removed license_number
- [x] Adapted tenant types: VET/SUPPLIER → RETAIL/WHOLESALE
- [x] Updated all Docker config, env vars, and documentation

---

## 🚧 FASE 3 — Licenses + Auto-update (NEXT)

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

## 📅 FASE 4 — Suppliers & Purchase Orders

### Supplier Management
- [ ] `Supplier` model: name, tax_id, contact, payment terms, notes
- [ ] Supplier CRUD with search and pagination
- [ ] Associate suppliers to products (preferred supplier per product)

### Purchase Orders
- [ ] `PurchaseOrder` + `PurchaseOrderItem` models
- [ ] State machine: `DRAFT → SENT → RECEIVED → CANCELLED`
- [ ] Create purchase order from low-stock alerts
- [ ] Receive order → auto-update stock movements
- [ ] Purchase order history and reporting

---

## 📅 FASE 5 — Advanced Reports & Analytics

### Sales Reports
- [ ] Sales by period (daily, weekly, monthly, custom range)
- [ ] Sales by product / category / payment method
- [ ] Top sellers ranking
- [ ] Profit margin analysis (cost vs sale price)

### Inventory Reports
- [ ] Stock valuation report (current stock × cost)
- [ ] Low stock alerts dashboard
- [ ] Stock movement history by product
- [ ] Dead stock / slow-moving items

### Export
- [ ] PDF and Excel export for all reports

---

## 📅 FASE 6 — Master Catalog + Barcode Lookup

### Cloud Catalog
- [ ] `MasterProduct` model: EAN, description, category, brand, suggested_price, image_url
- [ ] Seed from free APIs: Open Food Facts, UPC Database
- [ ] `GET /catalog/search?q=` — search by name or EAN
- [ ] `GET /catalog/lookup/{barcode}` — barcode → product info

### Desktop Integration
- [ ] POS/Inventory scan: if product not found locally → query cloud catalog
- [ ] Auto-create local product from catalog match (user edits price/cost)
- [ ] Periodic sync: Desktop downloads master catalog for offline use

---

## 📅 FASE 7 — Invoice & Billing

### Basic Invoicing
- [ ] Generate invoice from sale (with tax calculation)
- [ ] Invoice templates (configurable header/footer)
- [ ] Sequential invoice numbering
- [ ] PDF generation and email sending

### Tax Configuration
- [ ] Tax rates per product category
- [ ] Tax-inclusive / tax-exclusive pricing modes
- [ ] Regional tax rules

---

## 📅 FASE 8 — Multi-branch Support

### Branch Management
- [ ] `Branch` model linked to Company
- [ ] Per-branch inventory tracking
- [ ] Inter-branch stock transfers
- [ ] Branch-level reports and dashboards

### Unified Dashboard
- [ ] Company-wide overview across all branches
- [ ] Consolidated reports

---

## 🔮 FASE 9 — AI Assistant

### Invoice OCR
- [ ] `POST /ai/process-invoice` — image → LLM (Gemini Vision / GPT-4V)
- [ ] Extract: items, quantities, prices, supplier
- [ ] Fuzzy match against local inventory + master catalog
- [ ] UI: "Load stock from invoice" button → camera/upload → preview → confirm

### Smart Restock Suggestions
- [ ] Analyze sales velocity and predict optimal reorder points
- [ ] Suggest purchase orders based on demand patterns

---

## 🔮 FASE 10 — Sync + Backup + Build

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

## 📅 FASE 11 — SaaS Onboarding

### Registration & Auth
- [ ] Unified sign-in page for SaaS (email + password)
- [ ] Account type selection at registration: Retail, Wholesale, or Both
- [ ] Email verification + password recovery
- [ ] Tenant creation on registration

### SaaS Onboarding
- [ ] Cloud onboarding wizard (similar to Desktop setup_wizard)
- [ ] Subscription plans and billing

---

## Known Technical Debt
- Multi-tenant inconsistency: some views don't filter by company
- Sales signal-based stock deduction should be reviewed for atomicity
- Locale .po files need regeneration after rebranding

---

## Architecture Diagram
```
┌──────────────────────────────────────────────────────────────────┐
│                marketcoresoft.com (Cloud)                         │
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
└──────────────────────────────────────────────────────────────────┘
```