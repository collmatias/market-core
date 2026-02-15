# 🗺️ ROADMAP: VetCore System

## 🎯 Visión del Proyecto
Construir una plataforma de gestión veterinaria **Híbrida (Offline-First)** que combine la robustez de una aplicación de escritorio con la inteligencia y conectividad de la nube.
El sistema debe garantizar la operatividad continua (incluso sin internet) y sincronizarse con una API central para servicios avanzados (IA, Backups, Catálogos, Proveedores).

---

## ✅ Estado Actual (Fase 1: Cimientos)
- [x] **Arquitectura Híbrida:** - Entorno Desktop con SQLite (Datos locales).
    - Entorno SaaS con PostgreSQL (Multi-tenant).
- [x] **Gestión de Licencias:**
    - Validación Offline (Hardware ID) para Desktop.
    - Validación Online (Empresa Activa) para SaaS.
- [x] **Gestión de Empresas:**
    - Modelo Multi-empresa (Tenant Awareness).
    - Flujo de Inicialización (Configuración de Veterinaria al primer uso).
- [x] **Módulos Básicos:**
    - Gestión de Clientes y Pacientes.
    - Ventas y Cierre de Caja (con filtros de fecha/turno).
    - Reportes básicos.

---

## 🚧 Corto Plazo (Fase 2: Consolidación y Sync)
### 1. Motor de Sincronización (El Corazón Offline-First)
- [ ] Implementar sistema de **Colas de Sincronización**.
    - *Lógica:* Cuando se crea una venta offline, se guarda en una tabla `PendingSync`. Un proceso en segundo plano intenta subirla a la nube cuando detecta internet.
- [ ] Implementar **Webhooks/Polling** para bajar datos de la nube (ej: nuevos precios, nuevos productos).

### 2. Catálogo Maestro (Vademécum Global)
- [ ] Crear base de datos centralizada de medicamentos y procedimientos en la Nube.
- [ ] Funcionalidad de "Importar Catálogo" en el Desktop para evitar carga manual.
- [ ] Sistema de actualización de precios masivos.

### 3. Empaquetado y Distribución
- [ ] Configurar **PyInstaller** para generar el `.exe`.
- [ ] Crear instalador silencioso (Inno Setup / NSIS).
- [ ] Endpoint de Auto-Update (El software se actualiza solo).

---

## 📅 Mediano Plazo (Fase 3: Inteligencia y Servicios)
### 1. Módulo IA (VetCore Agent) 🧠
- [ ] Integración con LLMs (Gemini/OpenAI) vía Cloud API.
- [ ] **Asistente Clínico:** Analizar historia clínica y sugerir diagnósticos diferenciales.
- [ ] **Análisis de Adjuntos:** Leer PDFs de laboratorios y extraer valores anómalos automáticamente.

### 2. Backups Cloud
- [ ] Servicio de respaldo automático: Encriptar `db.sqlite3` local y subirlo a AWS S3/Google Cloud Storage.
- [ ] Botón de "Restaurar desde la Nube" (Panic Button).

### 3. Portal de Novedades
- [ ] Feed de noticias en el Dashboard (Alertas sanitarias, promos de proveedores, updates del sistema).

---

## 🔮 Largo Plazo (Fase 4: Ecosistema y Comunidad)
### 1. Interconexión (Red VetCore)
- [ ] **Interconsultas:** Derivar un paciente (con su historia clínica digital) a un especialista que también use VetCore.
- [ ] **Ficha Unificada:** (Opcional) Que la historia clínica viaje con la mascota, no con la veterinaria.

### 2. Marketplace de Proveedores
- [ ] Conexión directa con distribuidores de insumos.
- [ ] **Pedido Automático:** "Me quedan 2 vacunas, generar pedido de reposición al proveedor X".
- [ ] Comparador de precios de insumos en tiempo real.

---

## 🛠️ Stack Tecnológico
- **Frontend/Desktop:** Django Templates + Bootstrap + PyWebView (Futuro) / Electron (Evaluación).
- **Backend Local:** Django + SQLite.
- **Cloud API:** FastAPI + PostgreSQL + Redis (para colas).
- **IA:** LangChain + Gemini Pro API.
- **Infra:** Docker (Dev), AWS/DigitalOcean (Prod).