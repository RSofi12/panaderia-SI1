# Panadería Santiago — Sistema de Información Web

Sistema de información web para la gestión de ventas, producción, inventario y control administrativo de la Panadería Santiago. Proyecto académico para la materia SI-1 (PUDS + UML).

---

## 🚀 Tecnologías

- **Backend:** Python 3.12+ · Django 5.x + Django REST Framework + SimpleJWT
- **Frontend:** React 19 + TypeScript + Vite + Tailwind CSS v4 + Lucide Icons
- **Base de datos:** PostgreSQL 16+ (Docker) / 14+ (Local)
- **Servidor de correo de desarrollo:** Mailpit (servidor SMTP local y visor web)
- **Contenedores y Orquestación:** Docker + Docker Compose (entorno integrado)
- **Metodología:** PUDS (Proceso Unificado de Desarrollo de Software) iterativo-incremental

---

## 📁 Estructura del repositorio

```
panaderia-SI1/
├── docker-compose.yml   # Orquestador global (DB + Mailpit + Backend + Frontend)
├── backend/             # API Django + Django REST Framework
│   ├── Dockerfile       # Imagen Docker de desarrollo (Python 3.12-slim)
│   ├── apps/            # 5 paquetes por dominio:
│   │                    #   - usuarios_seguridad (CU1-CU4, CU26)
│   │                    #   - productos_inventario (CU5, CU8-CU12, CU18, CU19)
│   │                    #   - compras (CU6, CU7, CU20)
│   │                    #   - comercializacion (CU13-CU17)
│   │                    #   - reportes (CU21-CU25)
│   ├── config/          # Configuración global Django (settings, urls)
│   └── requirements.txt
├── frontend/            # SPA React + TypeScript (Vite)
│   ├── Dockerfile       # Imagen Docker de desarrollo (Node 20-alpine)
│   └── src/
│       ├── apps/        # Pantallas por ventana del flujo visual (auth/, dashboard/*)
│       ├── contexts/    # Contexto de autenticación y sesión (AuthContext)
│       ├── routes/      # Enrutador y guardias RBAC (AppRoutes, ProtectedRoute)
│       ├── services/    # Clientes API Axios (authService, usuariosService, etc.)
│       └── types/       # Contratos e interfaces TypeScript
├── docs/                # Perfil del proyecto, DDL de base de datos, memoria de IA
└── README.md
```

> **Nota de arquitectura:** El backend se organiza por **paquetes de dominio** y sub-apps (base de datos y reglas de negocio), mientras que el frontend se organiza por **ventanas/pantallas** bajo `src/apps/` (flujo visual del usuario y permisos RBAC). El detalle completo se documenta en [`docs/ai/DECISIONS_LOG.md`](docs/ai/DECISIONS_LOG.md).

---

## 📋 Requisitos previos

- **Opción recomendada (Docker):**
  - **Docker Desktop** (con motor WSL2 en Windows) y Git.
- **Opción alternativa (Local directo sin Docker):**
  - **Python 3.12+** y `pip`
  - **Node.js 18+ LTS** y `npm`
  - **PostgreSQL 14+** (con base de datos creada, e.g. `panaderia_db`)
  - **Mailpit** (binario para captura de correos SMTP)
  - Git

---

## 🛠️ Cómo levantar el proyecto

### 🐳 Opción 1: Con Docker Compose (Recomendada — 1 sola terminal)

Esta opción levanta automáticamente la base de datos PostgreSQL, el servidor Mailpit, el backend Django y el frontend React en una red interna coordinada.

#### 1. Iniciar todos los servicios
Con Docker Desktop abierto, ejecuta en la raíz del proyecto (`panaderia-SI1`):

```powershell
docker compose up -d
```
*(O usa `docker compose up --build` si deseas ver los logs de los contenedores en tiempo real).*

#### 2. Migrar y cargar datos de prueba (solo la primera vez)
```powershell
# Aplicar migraciones a PostgreSQL
docker compose exec backend python manage.py migrate

# Poblar datos iniciales
docker compose exec backend python manage.py seed_usuarios      # CU1-CU4: roles, permisos y usuarios de prueba
docker compose exec backend python manage.py seed_productos     # CU5: categorías y catálogo base de productos
docker compose exec backend python manage.py seed_proveedores   # CU6: catálogo maestro de proveedores
```

#### 3. URLs de acceso
- **Aplicación Web (Frontend):** [http://localhost:5173](http://localhost:5173)
- **API REST (Backend):** [http://localhost:8000/api/](http://localhost:8000/api/)
- **Bandeja de correos (Mailpit):** [http://localhost:8025](http://localhost:8025)

#### 4. Detener el sistema
```powershell
docker compose down
```
*(Tus datos de base de datos se conservan intactos en el volumen persistente `postgres_data`).*

---

### 💻 Opción 2: Entorno Local Directo (Alternativa — 3 terminales)

Si prefieres ejecutar el sistema directamente en tu sistema operativo sin Docker, abre **3 terminales**:

#### Terminal 1: Servidor de Correo (Mailpit)
```powershell
C:\Users\PERSONAL\tools\mailpit\mailpit.exe --smtp 0.0.0.0:1025 --listen 0.0.0.0:8025
```
- **Web:** [http://localhost:8025](http://localhost:8025) | **SMTP:** `localhost:1025`

#### Terminal 2: Backend (Django REST Framework)
```powershell
cd backend

# Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno y migrar
copy .env.example .env
python manage.py migrate
python manage.py seed_usuarios
python manage.py seed_productos
python manage.py seed_proveedores

# Iniciar servidor API
python manage.py runserver
```
- **API Backend:** [http://localhost:8000](http://localhost:8000)

#### Terminal 3: Frontend (React + Vite)
```powershell
cd frontend
npm install
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
- [x] **CU4: Asignar roles y permisos** — 🟢 Completo end-to-end (Matriz interactiva por módulos, guardas anti-autobloqueo, pestañas sincronizadas con URL, auditoría con diff).
- [x] **CU26: Gestionar bitácora** — 🟢 Completo end-to-end (Pestaña dedicada en /dashboard/usuarios, filtros por fecha, usuario, módulo y acción, vista de detalle).
- [x] **CU5: Gestionar productos (catálogo base)** — 🟢 Completo end-to-end (Categorías, productos, historial de precios, seed de datos base).
- [x] **CU6: Gestionar proveedores (catálogo base)** — 🟢 Completo end-to-end (Maestro de proveedores, bajas lógicas, seed de datos base).
