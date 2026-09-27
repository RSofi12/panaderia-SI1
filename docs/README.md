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
│   └── sessions/                      # Bitácora de trabajo colaborativo por sesión
│       └── README.md                  # Guía y plantilla de registro de sesiones
├── informes/                          # Documentos formales y esquemas físicos
│   ├── Database_Panaderia_Santiago.sql# Script DDL de base de datos PostgreSQL
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
