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

- **Librería Base:** React 19 + TypeScript
- **Herramienta de Construcción (Bundler):** Vite 8 (`@vitejs/plugin-react`)
- **Estilos y UI:** **Tailwind CSS v4** instalado como plugin oficial `@tailwindcss/vite`.
  - ⚠️ En Tailwind v4 **no se usa `tailwind.config.js` ni PostCSS/Autoprefixer**. La configuración se hace con `@theme` dentro del archivo CSS, y el import es `@import "tailwindcss";`.
  - Versión: `tailwindcss@^4.3.3` + `@tailwindcss/vite@^4.3.3`
- **Iconografía:** `lucide-react` (árbol de iconos SVG, import individual por componente)
- **Enrutamiento:** `react-router-dom@^7` (patrón `BrowserRouter` + `Routes`/`Route`)
- **Cliente HTTP:** `axios@^1.20` con interceptores para inyección automática del token JWT en el header `Authorization: Bearer <token>` y refresco automático ante `401`.
- **Manejo de Estado y Autenticación:** React Context API.
  - `contexts/AuthContext.ts` → define el contexto y el hook `useAuth()`
  - `contexts/AuthProvider.tsx` → componente `AuthProvider` con la lógica de sesión (login, logout, verificación de token, `hasPermission`, `hasRole`)
- **Lint / Calidad:** ESLint 10 (flat config) con `typescript-eslint`, `eslint-plugin-react-hooks` y `eslint-plugin-react-refresh`
- **Variables de entorno:** archivo `frontend/.env` con prefijo `VITE_` (ej. `VITE_API_URL`), tipadas en `src/vite-env.d.ts`

### 2.1. Criterio de Organización del Frontend

El frontend se organiza **por ventanas / flujo visual del usuario** en `frontend/src/apps/`, mientras que el backend se organiza **por paquetes de dominio** en `backend/apps/`. La justificación completa de esta asimetría y el mapeo pantalla ↔ caso de uso ↔ paquete están en [`ARCHITECTURE.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/ARCHITECTURE.md) (sección 3).

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

### Variables de entorno del Frontend (`frontend/.env`)

| Variable | Descripción | Ejemplo local |
|---|---|---|
| `VITE_API_URL` | URL base del backend (API REST) | `http://localhost:8000/api` |

> ⚠️ Solo las variables con prefijo `VITE_` son expuestas al bundle del navegador. **Nunca** coloques secretos (claves, contraseñas, tokens de terceros) en este archivo: todo lo que exista ahí queda visible para el usuario.

---

## 🚀 5. Entorno y Despliegue

- **Fase Actual (Ciclo 1):** Ejecución en entorno local directo:
  - Backend: `python -m venv venv` $\rightarrow$ `python manage.py runserver`
  - Frontend: `npm install` $\rightarrow$ `npm run dev`
- **Fase Futura (Post Ciclo 1):** Dockerización con `Dockerfile` y `docker-compose.yml` para empaquetado y despliegue a servidor en nube.
