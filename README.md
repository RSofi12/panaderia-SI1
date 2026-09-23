# Panadería Santiago — Sistema de Información Web

Sistema de información web para la gestión de ventas, producción, inventario y control administrativo de la Panadería Santiago. Proyecto académico.

## Tecnologías

- **Backend:** Django (Python) + Django REST Framework
- **Frontend:** React + TypeScript (Vite)
- **Base de datos:** PostgreSQL 14+
- **Metodología:** PUDS (Proceso Unificado de Desarrollo de Software) + UML
- **Control de calidad de datos:** el sistema funciona bajo lógica de tipo MRP (Material Requirements Planning) para el descuento automático de materia prima según la producción

## Estructura del repositorio

```
panaderia-SI1/
├── backend/          # API Django + Django REST Framework
│   ├── apps/         # Paquetes por caso de uso (usuarios_seguridad, ventas, etc.)
│   ├── config/        # Configuración del proyecto Django (settings, urls)
│   └── requirements.txt
├── frontend/         # Aplicación React + TypeScript (Vite)
└── README.md
```

## Requisitos previos

- Python 3.12+ (recomendado; ver nota sobre 3.14 en el backend)
- Node.js 18+ LTS
- PostgreSQL 14+ y pgAdmin 4 (opcional, para administración visual)
- Git

## Cómo levantar el proyecto

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd panaderia-SI1
```

### 2. Backend (Django)

```bash
cd backend

# Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Mac/Linux

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
# Copia .env.example a .env y completa tus credenciales de PostgreSQL
copy .env.example .env           # Windows
# cp .env.example .env           # Mac/Linux
```

Antes de continuar, crea en PostgreSQL (por psql o pgAdmin) una base de datos vacía y un usuario dedicado, y completa esos datos en tu `.env`:

```
DB_NAME=panaderia_db
DB_USER=panaderia_admin
DB_PASSWORD=tu_contrasena
DB_HOST=localhost
DB_PORT=5432
```

Luego aplica las migraciones y levanta el servidor:

```bash
python manage.py migrate
python manage.py runserver
```

El backend queda disponible en `http://localhost:8000`.

### 3. Frontend (React + TypeScript)

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

El frontend queda disponible en `http://localhost:5173`.

## Estado actual

- [x] Diseño de base de datos (DDL, triggers, procedimientos almacenados) completado y defendido
- [x] Casos de uso definidos y organizados por paquetes/módulos
- [x] Estructura inicial del backend (Django + PostgreSQL) y frontend (React + TS) creada
- [ ] Implementación de módulos por ciclo de desarrollo (en progreso)
- [ ] Contenerización con Docker (planeado, pendiente)
- [ ] Reportes dinámicos (planeado)

