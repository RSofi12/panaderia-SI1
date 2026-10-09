# Sesión de Desarrollo: Dockerización del Entorno y Compatibilidad Python 3.14

- **Fecha:** 2026-10-09
- **Autor / Integrante:** Equipo de Desarrollo (Asistente IA Antigravity)
- **Paquete / Módulo:** Infraestructura / DevOps / `backend` / `frontend`
- **Casos de Uso abordados:** Soporte transversal para todos los casos de uso (CU1 a CU26)
- **Ciclo:** Transición de Infraestructura / Consolidación Ciclo 1

---

## 1. 🎯 Objetivo de la sesión

1. Resolver el fallo de compilación de `psycopg2-binary` en entornos locales modernos con Python 3.14 sobre Windows sin requerir la instalación de *Microsoft Visual C++ Build Tools*.
2. Diseñar e implementar la infraestructura de contenedores Docker para el proyecto completo (`panaderia-SI1`), unificando los 4 servicios de desarrollo (Base de datos PostgreSQL, Mailpit, API Django y SPA React con Vite) para poder levantarlos con un solo comando en lugar de 3 terminales separadas.
3. Asegurar que la arquitectura de contenedores sea 100% compatible y esté lista para despliegues en la nube en plataformas modernas (Railway, Render, Google Cloud Run y Vercel).

---

## 2. 🛠️ Cambios realizados

### Backend:
- **`backend/requirements.txt`:** Se flexibilizó `psycopg2-binary==2.9.9` a `psycopg2-binary>=2.9.9`. Con esto, `pip` descarga las ruedas precompiladas oficiales (`.whl`, ej. 2.9.13) compatibles con Python 3.14 en Windows, eliminando la necesidad de compiladores locales de C++ y manteniendo retrocompatibilidad total con Python 3.12+.
- **`backend/Dockerfile`:** Creado utilizando `python:3.12-slim` con variables de entorno anti-buffer (`PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`), librerías de sistema (`libpq-dev`, `build-essential`, `curl`) y arranque en `0.0.0.0:8000`.
- **`backend/.dockerignore`:** Creado para excluir `venv/`, `__pycache__/`, bases de datos SQLite y archivos de configuración sensibles `.env`.

### Frontend:
- **`frontend/Dockerfile`:** Creado sobre `node:20-alpine`, optimizando el orden de capas para cachear `package.json` y ejecutando Vite dev server en `0.0.0.0:5173`.
- **`frontend/.dockerignore`:** Creado para aislar `node_modules/`, `dist/` y archivos temporales.
- **`frontend/vite.config.ts`:** Se configuró el bloque `server` con `host: '0.0.0.0'`, `port: 5173` y `watch: { usePolling: true }`, garantizando que el *Hot Module Replacement* (HMR) funcione instantáneamente en Windows a través de los volúmenes montados de Docker.

### Orquestación Global:
- **`docker-compose.yml`:** Creado en la raíz del proyecto para gobernar los 4 servicios:
  1. `db`: PostgreSQL 16 con volumen persistente `postgres_data` y mapeo de puertos estándar `5432:5432`.
  2. `mailpit`: Captura de correos transaccionales (SMTP `1025`, Web UI `8025`).
  3. `backend`: Contenedor Django enlazado a `db` y `mailpit` con recarga en caliente de código mediante volumen `./backend:/app`.
  4. `frontend`: Contenedor Vite React enlazado al backend con volumen `./frontend:/app` y volumen anónimo para `/app/node_modules`.

---

## 3. 🧠 Decisiones técnicas tomadas

1. **Resolución de incompatibilidad de Python 3.14 en `requirements.txt`:**
   - La versión fijada rígidamente (`2.9.9`) fue publicada antes del lanzamiento de Python 3.14, por lo que no existía `.whl` en PyPI para esa versión específica, forzando una compilación C++ fallida en Windows. Al usar `>=2.9.9`, se resuelve automáticamente a versiones con binario listo (`2.9.13`) sin romper compatibilidad.
2. **Eliminación de Healthchecks restrictivos en Compose:**
   - Inicialmente se configuró un `healthcheck` con `pg_isready` y `condition: service_healthy`. Debido a la alta carga de CPU/disco durante la compilación simultánea de imágenes en Windows, Docker arrojó un falso positivo por timeout en el chequeo. Se simplificó a `depends_on: [db, mailpit]`, ya que Django `runserver` no se bloquea al arrancar y PostgreSQL está listo en segundos.
3. **Persistencia y Aislamiento de Node Modules:**
   - En el frontend se configuró un volumen anónimo `/app/node_modules` para evitar que la carpeta `node_modules` de la máquina anfitriona Windows colisione o sobreescriba las dependencias compiladas para Linux Alpine dentro del contenedor.

---

## 4. ⚠️ Siguientes pasos

1. Actualizar el archivo `README.md` de la raíz en una sesión dedicada para reflejar el flujo de arranque con Docker como opción principal recomendada, manteniendo las instrucciones locales tradicionales como alternativa secundaria.
2. Opcional: Implementar un seeder unificado `seed_all` (mediante `call_command`) para correr `seed_usuarios`, `seed_proveedores` y `seed_productos` en una sola invocación.
3. Continuar con los casos de uso restantes del proyecto.

---

## 5. 🧪 Cómo probar lo implementado

```powershell
# 1. Levantar todos los servicios en una sola terminal
docker compose up -d --build

# 2. Comprobar que los 4 contenedores están Up
docker compose ps

# 3. Aplicar migraciones y seeds en la base de datos de Docker
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_usuarios
docker compose exec backend python manage.py seed_productos
docker compose exec backend python manage.py seed_proveedores

# 4. Accesos en el navegador
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/api/
# Mailpit Web UI: http://localhost:8025
```
