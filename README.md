# Panadería Santiago — Sistema de Información Web

Sistema de información web para la gestión de ventas, producción, inventario y control administrativo de la Panadería Santiago. Proyecto académico para la materia SI-1 (PUDS + UML).

---

## 🚀 Tecnologías

- **Backend:** Python 3.12+ · Django 5.x + Django REST Framework + SimpleJWT
- **Frontend:** React 19 + TypeScript + Vite + Tailwind CSS v4 + Lucide Icons
- **Base de datos:** PostgreSQL 14+
- **Servidor de correo de desarrollo:** Mailpit (servidor SMTP local y visor web)
- **Metodología:** PUDS (Proceso Unificado de Desarrollo de Software) iterativo-incremental

---

## 📁 Estructura del repositorio

```
panaderia-SI1/
├── backend/          # API Django + Django REST Framework
│   ├── apps/         # 5 paquetes por dominio:
│   │                 #   - usuarios_seguridad (CU1-CU4, CU26)
│   │                 #   - productos_inventario (CU5, CU8-CU12, CU18, CU19)
│   │                 #   - compras (CU6, CU7, CU20)
│   │                 #   - comercializacion (CU13-CU17)
│   │                 #   - reportes (CU21-CU25)
│   │   config/       # Configuración global Django (settings, urls)
│   └── requirements.txt
├── frontend/         # SPA React + TypeScript (Vite)
│   └── src/
│       ├── apps/     # Pantallas por ventana del flujo visual (auth/, dashboard/*)
│       ├── contexts/ # Contexto de autenticación y sesión (AuthContext)
│       ├── routes/   # Enrutador y guardias RBAC (AppRoutes, ProtectedRoute)
│       ├── services/ # Clientes API Axios (authService, usuariosService, etc.)
│       └── types/    # Contratos e interfaces TypeScript
├── docs/             # Perfil del proyecto, DDL de base de datos, memoria de IA
└── README.md
```

> **Nota de arquitectura:** El backend se organiza por **paquetes de dominio** y sub-apps (base de datos y reglas de negocio), mientras que el frontend se organiza por **ventanas/pantallas** bajo `src/apps/` (flujo visual del usuario y permisos RBAC). El detalle completo se documenta en [`docs/ai/DECISIONS_LOG.md`](docs/ai/DECISIONS_LOG.md).

---

## 📋 Requisitos previos

- **Python 3.12+**
- **Node.js 18+ LTS** y `npm`
- **PostgreSQL 14+** (con una base de datos creada, e.g. `panaderia_db`)
- **Git**
- **Mailpit** (para pruebas de correos transaccionales y recuperación de contraseña)

---

## 🛠️ Cómo levantar el proyecto localmente

Para ejecutar el sistema completo en entorno local, se recomienda abrir **3 terminales**:

### 1. Servidor de Correo de Pruebas (Mailpit)

Mailpit captura los correos emitidos por el sistema (como los enlaces de recuperación de contraseña del CU2) sin enviarlos a servidores externos reales.

En una terminal dedicada:

```powershell
# Si ya tienes el ejecutable en tu equipo (ej. en tools\mailpit):
C:\Users\PERSONAL\tools\mailpit\mailpit.exe --smtp 0.0.0.0:1025 --listen 0.0.0.0:8025

# O si utilizas Docker:
# docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit
```

- **Bandeja de entrada Web:** [http://localhost:8025](http://localhost:8025)
- **Servidor SMTP:** `localhost:1025`

---

### 2. Backend (Django REST Framework)

En una segunda terminal:

```powershell
cd backend

# 1. Crear y activar entorno virtual (Windows)
python -m venv venv
.\venv\Scripts\Activate.ps1
# En Linux/Mac: source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
# Copia .env.example a .env y ajusta tus credenciales de PostgreSQL
copy .env.example .env

# 4. Aplicar migraciones a PostgreSQL
python manage.py migrate

# 5. Poblar datos iniciales (roles, permisos y usuarios de prueba)
python manage.py seed_usuarios

# 6. Iniciar el servidor API
python manage.py runserver
```

- **API Backend:** [http://localhost:8000](http://localhost:8000)

> [!TIP]
> **Configuración en `backend/.env` para Mailpit:**
> ```env
> EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
> EMAIL_HOST=localhost
> EMAIL_PORT=1025
> ```
> *Si dejas `EMAIL_BACKEND` sin configurar, Django imprimirá los correos directamente en la consola de `runserver`.*

---

### 3. Frontend (React + Vite)

En una tercera terminal:

```powershell
cd frontend

# 1. Instalar dependencias
npm install

# 2. Iniciar servidor de desarrollo
npm run dev
```

- **Aplicación Web:** [http://localhost:5173](http://localhost:5173)

---

## 👥 Cuentas de Prueba Preconfiguradas (`seed_usuarios`)

Todas las cuentas del seed comparten la contraseña: `Admin123!`

| Usuario | Rol | Permisos clave | Acceso en el sistema |
|---|---|---|---|
| `admin` | **Administrador** | Todos (`gestionar_usuarios`, etc.) | Panel completo y administración de cuentas (CU3) |
| `rpanaderia` | **Propietario** | `consultar_bitacora`, reportes | Panel gerencial de supervisión |
| `mgonzales` | **Personal de Ventas** | `registrar_ventas`, `registrar_pedidos` | Acceso denegado a CU3 (403 verificado) |
| `jperez` | **Personal de Producción** | `registrar_produccion`, etc. | Acceso denegado a CU3 (403 verificado) |

---

## 🧪 Comandos de Validación y Calidad

```powershell
# === Backend ===
cd backend
python manage.py check                              # Validación de sistema Django
python manage.py test apps.usuarios_seguridad       # Pruebas automatizadas (144 tests)

# === Frontend ===
cd frontend
npm run lint                                        # Linter ESLint (0 errores)
npm run build                                       # Chequeo TypeScript y bundle de producción Vite
```

---

## 📌 Estado de los Casos de Uso (Ciclo 1)

- [x] **CU1: Iniciar sesión** — 🟢 Completo end-to-end (JWT, refresco automático, bloqueo de fuerza bruta 429 con cuenta regresiva, auditoría en bitácora).
- [x] **CU2: Recuperar contraseña** — 🟢 Completo end-to-end (Tokens SHA-256 de un solo uso, anti-enumeración, expiración de 15 min, envío SMTP con Mailpit, UI reactiva).
- [x] **CU3: Gestionar usuarios** — 🟢 Completo end-to-end (Listado paginado con debounce 300 ms, alta/edición, activación/inactivación con motivo en bitácora, reseteo administrativo de contraseña, desbloqueo de cuentas, modales accesibles WCAG 2.2 AA).
- [ ] **CU4: Asignar roles y permisos** — 🟡 Modelos listos (`Rol`, `Permiso`, `RolPermiso`), endpoints y vistas frontend pendientes.
- [x] **CU26: Gestionar bitácora (versión simple)** — 🟢 Auditoría activa en backend para eventos de seguridad y cambios de usuario; pantalla pendiente.
- [ ] **CU5: Gestionar productos (catálogo base)** — ⚪ Planificado para Ciclo 1.
- [ ] **CU6: Gestionar proveedores (catálogo base)** — ⚪ Planificado para Ciclo 1.
