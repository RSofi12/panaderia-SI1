# Stack Tecnológico Oficial (TECH STACK)

## 📌 Sistema de Información Web — Panadería Santiago (SI-1)

---

## 🐍 1. Backend

- **Lenguaje:** Python 3.12+
- **Framework Web:** Django 5.x / 6.x
- **API Toolkit:** Django REST Framework (DRF)
- **Autenticación & Seguridad:**
  - JSON Web Tokens (JWT) mediante `djangorestframework-simplejwt`
  - Control de acceso basado en roles (RBAC) personalizado
  - CORS configurado mediante `django-cors-headers`
- **Gestor de Base de Datos / Driver:** PostgreSQL 14+ con driver `psycopg2-binary`
- **Configuración & Entorno:** `python-dotenv` para carga dinámica de variables desde `backend/.env`
- **Estructura Modular (5 Django Apps en `backend/apps/`):**
  1. `apps.usuarios_seguridad`
  2. `apps.productos_inventario`
  3. `apps.compras`
  4. `apps.comercializacion`
  5. `apps.reportes`

---

## ⚛️ 2. Frontend Web

- **Librería Base:** React (TypeScript)
- **Herramienta de Construcción (Bundler):** Vite
- **Estilos y UI:** Tailwind CSS + PostCSS + Autoprefixer
- **Iconografía:** Lucide React / Tabler Icons
- **Enrutamiento:** React Router DOM
- **Cliente HTTP:** Axios / Fetch API con interceptores para inyección automática de tokens JWT en el header `Authorization: Bearer <token>`.
- **Manejo de Estado y Autenticación:** React Context API (`AuthContext`) para sesión de usuario, permisos y almacenamiento seguro de tokens.

---

## 🗄️ 3. Base de Datos (PostgreSQL)

- **Motor:** PostgreSQL 14+
- **Modelo de Datos:** Normalizado (3FN), con llaves foráneas e integridad referencial estricta.
- **Esquema de Referencia:** [`docs/informes/Database_Panaderia_Santiago.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Database_Panaderia_Santiago.sql).
- **Triggers y Procedimientos:** Triggers para registro automático de eventos en la tabla `bitacora` ante operaciones críticas.

---

## ⚙️ 4. Variables de Entorno (`backend/.env`)

| Variable | Descripción | Ejemplo local |
|---|---|---|
| `SECRET_KEY` | Clave secreta criptográfica de Django | `django-insecure-panaderia-santiago-key` |
| `DEBUG` | Modo depuración | `True` |
| `DB_NAME` | Nombre de la base de datos PostgreSQL | `panaderia_santiago` |
| `DB_USER` | Usuario de PostgreSQL | `postgres` |
| `DB_PASSWORD`| Contraseña de PostgreSQL | `postgres123` |
| `DB_HOST` | Host del servidor PostgreSQL | `localhost` |
| `DB_PORT` | Puerto de PostgreSQL | `5432` |
| `CORS_ALLOWED_ORIGINS` | Orígenes frontend permitidos | `http://localhost:5173,http://localhost:3000` |

---

## 🚀 5. Entorno y Despliegue

- **Fase Actual (Ciclo 1):** Ejecución en entorno local directo:
  - Backend: `python -m venv venv` $\rightarrow$ `python manage.py runserver`
  - Frontend: `npm install` $\rightarrow$ `npm run dev`
- **Fase Futura (Post Ciclo 1):** Dockerización con `Dockerfile` y `docker-compose.yml` para empaquetado y despliegue a servidor en nube.
