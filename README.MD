# 🐶 VetCore - Sistema de Gestión Veterinaria

**VetCore** es un sistema integral diseñado para clínicas veterinarias, enfocado en la simplicidad, robustez y capacidad de funcionamiento offline/online.

Desarrollado con una arquitectura híbrida que permite el desarrollo ágil en contenedores y el despliegue nativo en Windows para clientes finales.

## 🚀 Características Principales

- **Gestión de Clientes y Pacientes:** Historias clínicas, datos de contacto y relaciones.
- **Control de Inventario:**
  - Stock en tiempo real.
  - Alertas de reposición.
  - Diferenciación entre Insumos/Productos y Servicios.
- **Arquitectura Híbrida:**
  - **Modo Servidor:** Permite que otras PCs en la red local se conecten vía navegador.
  - **Modo Standalone:** Base de datos SQLite local para instalaciones sencillas.
- **Interfaz Moderna:** Basada en Bootstrap 5, responsiva y rápida.

## 🛠️ Stack Tecnológico

- **Backend:** Python 3 + Django 5.
- **Base de Datos (Dev):** PostgreSQL 16.
- **Base de Datos (Prod):** SQLite 3 (Autogestionada).
- **Infraestructura:** Docker & Docker Compose.
- **Frontend:** Django Templates + Bootstrap 5 + HTMX (Próximamente).

## 💻 Instalación y Desarrollo

### Prerrequisitos
- Docker y Docker Compose instalados.

### Pasos
1. Clonar el repositorio:
  ```bash
  git clone https://github.com/tu-usuario/vetcore.git
  ```

2. Iniciar los contenedores:
  ```bash
  docker compose up --build
  ```
## 🖥️ Acceso al sistema

- Web: [http://localhost:8000](http://localhost:8000)
- Admin: [http://localhost:8000/admin](http://localhost:8000/admin)

## 🗺️ Roadmap

- [x] Gestión de Clientes/Pacientes
- [x] Inventario y Stock
- [ ] Módulo de Ventas (Punto de Venta)
- [ ] Historias Clínicas Detalladas
- [ ] Compilación a .exe (PyInstaller)
- [ ] Sistema de Licenciamiento por Hardware ID

## 📄 Licencia

Propiedad Privada. Todos los derechos reservados.