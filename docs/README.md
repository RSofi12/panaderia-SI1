# Sistema de Información Web — Panadería Santiago (SI-1)

Documentación técnica y operativa del proyecto desarrollado para la materia **Sistemas de Información 1 (SI-1)** — Grupo 3.

---

## 📁 1. Estructura de Documentación

```
docs/
├── ai/                                # Memoria y contexto para agentes de IA y equipo
│   ├── ARCHITECTURE.md                # Arquitectura lógica, capas y flujo de datos
│   ├── IMPLEMENTATION_PHASES.md       # Casos de uso y fases por ciclo de desarrollo
│   ├── PROJECT_CONTEXT.md             # Antecedentes, justificación y alcance del negocio
│   ├── PROJECT_VISION.md              # Visión del sistema y alcance de los 4 ciclos
│   ├── TECH_STACK.md                  # Dependencias y variables de entorno
│   ├── CURRENT_STATE.md               # Avance real: CUs funcionales vs pendientes
│   ├── DECISIONS_LOG.md               # Registro de decisiones técnicas del equipo
│   ├── HANDOFF_LATEST.md              # Resumen de la última entrega
│   ├── MASTER_AGENT_PROMPT.md         # Reglas primarias obligatorias (regla 6 = bitácora)
│   └── sessions/                      # Bitácora obligatoria de cada sesión de trabajo
│       ├── README.md                  # Guía y plantilla de registro de sesiones
│       └── YYYY-MM-DD-[autor]-[resumen].md
├── informes/                          # Documentos formales y esquemas físicos
│   ├── Database_Panaderia_Santiago.sql# Script DDL de base de datos PostgreSQL
│   ├── database_panaderia_con_funciones.puml # Diagrama de clases PlantUML
│   └── Perfil Proyecto SI-1 grupo 3.md# Perfil y especificación de requerimientos
└── README.md                          # Este archivo (Guía general de documentación)
```

---

## 🏗️ 2. Arquitectura y Paquetes del Sistema

El proyecto sigue una arquitectura modular en capas desacopladas (Frontend SPA en React + Backend API REST en Django + Base de Datos Relacional PostgreSQL).

El backend se organiza en **5 paquetes (Django apps)** ubicados en `backend/apps/`:

| # | Paquete Django | Casos de Uso Asociados | Ciclo PUDS |
|---|---|---|---|
| **1** | `apps.usuarios_seguridad` | CU1, CU2, CU3, CU4, CU26 | **Ciclo 1** |
| **2** | `apps.productos_inventario`| CU5, CU8, CU9, CU10, CU11, CU12, CU18, CU19 | **Ciclos 1, 2 y 3** |
| **3** | `apps.compras` | CU6, CU7, CU20 | **Ciclos 1, 2 y 4** |
| **4** | `apps.comercializacion` | CU13, CU14, CU15, CU16, CU17 | **Ciclo 3** |
| **5** | `apps.reportes` | CU21, CU22, CU23, CU24, CU25 | **Ciclo 4** |

> Para el detalle completo de los 26 casos de uso, consultar [`backend/apps/PACKAGE_CU_MAP.md`](file:///c:/Users/PERSONAL/panaderia-SI1/backend/apps/PACKAGE_CU_MAP.md).

---

## 🚀 3. Guía de Puesta en Marcha en Entorno Local

> ⚠️ **Nota:** El proyecto se ejecuta en entorno local directo (sin Docker durante el Ciclo 1). La contenedorización se evaluará en ciclos posteriores.

### 🐍 Backend (Django & DRF)

1. **Crear y activar entorno virtual:**
   ```bash
   cd backend
   python -m venv venv
   # En Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # En Windows CMD:
   .\venv\Scripts\activate.bat
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno:**
   - Crear archivo `.env` en la carpeta `backend/` a partir de `.env.example` con los datos de conexión a PostgreSQL:
     ```env
     SECRET_KEY=tu_secret_key_aqui
     DEBUG=True
     DB_NAME=panaderia_santiago
     DB_USER=postgres
     DB_PASSWORD=tu_password
     DB_HOST=localhost
     DB_PORT=5432
     ```

4. **Ejecutar migraciones y servidor de desarrollo:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```
   El backend quedará disponible en `http://localhost:8000/api/`.

---

### ⚛️ Frontend (React + Vite + TypeScript)

1. **Instalar paquetes:**
   ```bash
   cd frontend
   npm install
   ```

2. **Iniciar servidor de desarrollo:**
   ```bash
   npm run dev
   ```
   La aplicación web estará disponible en `http://localhost:5173/`.

---

## 📌 4. Convenciones del Proyecto

### Control de Versiones (Git)
- Ramas de trabajo: `main` (producción/entregas), `develop` (integración), `feature/[modulo-caso-de-uso]`, `fix/[descripcion]`.
- Commits descriptivos en español siguiendo la convención de verbos en presente (ej. `feat(usuarios): agregar endpoint de login con JWT`).

### Estándares de Código
- **Backend (Python):** PEP 8, nombres de tablas en `snake_case`, vistas y modelos documentados en español.
- **Frontend (TypeScript/React):** Componentes funcionales, hooks personalizados para consumo de API, tipado estricto con interfaces de TypeScript.
- **Base de Datos:** Definida en PostgreSQL 14+, manteniendo coherencia estricta con el script [`Database_Panaderia_Santiago.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Database_Panaderia_Santiago.sql) y los modelos Django.

### Bitácora de Sesiones (obligatoria)
- **Todo cambio en el repositorio** (backend, frontend, base de datos, configuración o documentación) se registra en `docs/ai/sessions/` siguiendo la plantilla de [`docs/ai/sessions/README.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/sessions/README.md).
- **Nombre del archivo:** `YYYY-MM-DD-[autor]-[resumen-corto].md` (ej. `2026-09-27-equipo-cu1-login-jwt.md`). Segunda sesión del mismo día y autor: sufijo `-2`.
- Se escribe **en el momento del cambio**. Si el archivo del día ya existe, se actualiza agregando entradas: el historial nunca se sobrescribe.
- Sin bitácora, la tarea se considera **incompleta**, aunque el código funcione.
- Aplica por igual a integrantes del equipo y a los agentes de IA del proyecto (`.opencode/agents/*.md`). Detalle en [`docs/ai/MASTER_AGENT_PROMPT.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/MASTER_AGENT_PROMPT.md) (regla 6).

### Agentes de IA del proyecto
- Los agentes especializados viven en `.opencode/agents/`. El principal es `orchestrator` (se selecciona con la tecla `Tab` y enruta cada tarea al especialista adecuado). Los subagentes se invocan con `@nombre`:

| Agente | Para qué |
|---|---|
| `backend` | Modelos, serializers, vistas, migraciones, API, reglas MRP |
| `frontend` | Pantallas, componentes, rutas, formularios, consumo de API |
| `ui-ux` | Diseño, tokens, accesibilidad, responsive, consistencia visual |
| `architecture` | Límites de paquetes, contratos, decisiones estructurales |
| `puds` | Casos de uso, ciclos, diagramas UML/PlantUML, material de defensa |
| `code-review` | Revisión de cambios antes de entregar (no edita) |
| `qa-testing` | Tests, lint, build y estado de migraciones |
| `security` | JWT, RBAC, bloqueo de cuenta, CORS, secretos, bitácora |
| `docs-memory` | Bitácora de sesión, `CURRENT_STATE`, `HANDOFF_LATEST`, `DECISIONS_LOG` |

- Ningún agente hace `git commit` por iniciativa propia: el equipo versiona manualmente.
