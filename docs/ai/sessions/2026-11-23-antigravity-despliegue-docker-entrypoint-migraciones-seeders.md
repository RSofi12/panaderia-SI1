# Bitácora de Sesión: 2026-11-23 — Solución de Despliegue Render/Docker y Sincronización de Base de Datos

- **Fecha:** 2026-11-23
- **Autor:** Antigravity (Senior Architect / DevOps)
- **Caso de Uso / Módulo:** Infraestructura, Despliegue en la Nube (Render + Vercel), Inicialización y Poblado de Datos

---

## 🎯 1. Objetivo de la Sesión
Solucionar el fallo en el inicio de sesión del despliegue en Vercel (`https://panaderia-santiago.vercel.app/login`) contra el backend en Render (`https://panaderia-backend-jgkz.onrender.com`), donde la interfaz reportaba: *"No se pudo conectar con el servidor. Verifica que el backend esté en ejecución."* Asegurar la ejecución automática de migraciones y seeders idempotentes sin requerir shell interactivo de pago en Render.

---

## 🔍 2. Diagnóstico y Causa Raíz

1. **Estado real del Backend en Render:**
   - La instancia estaba viva y la conexión PostgreSQL operativa (`/api/health/` devolvió 40 tablas).
   - Los encabezados CORS hacia `https://panaderia-santiago.vercel.app` funcionaban adecuadamente.
   - Peticiones con usuarios inexistentes respondían con el esperado `HTTP 400 Bad Request` (`Credenciales inválidas`).

2. **Causa del Error 500 al autenticar:**
   - Al intentar autenticar con `admin`, Render respondía `HTTP 500 Internal Server Error` en formato HTML.
   - En el frontend (`LoginPage.tsx`), al no recibir un JSON con `.error` o `.detail`, el código caía en el fallback genérico asumiendo que no había conexión con el servidor.
   - La excepción 500 en Render ocurría porque el contenedor Docker arrancaba únicamente con `python manage.py runserver`, **sin ejecutar `migrate`**. Por tanto, las migraciones añadidas recientemente (como `0003_rol_tipo_rol.py`, agregando la columna `tipo_rol` a la tabla `rol`) no existían en PostgreSQL de Render, disparando un `ProgrammingError: column rol.tipo_rol does not exist`.

3. **Diferenciación conceptual: `migrate` vs `seed_all`:**
   - `python manage.py migrate` aplica **exclusivamente cambios de esquema DDL** (tablas, columnas, índices, llaves foráneas). No inserta datos de negocio ni corre seeders.
   - `python manage.py seed_all` es el comando que ejecuta secuencialmente los 12 seeders de datos maestros, operativos y de simulación de 1 mes completo (idempotentes).

---

## 🛠️ 3. Cambios Implementados

### A. Backend & Docker (`backend/entrypoint.sh` y `backend/Dockerfile`)
- Se creó el script ejecutable [entrypoint.sh](file:///c:/Users/PERSONAL/panaderia-SI1/backend/entrypoint.sh) que orquesta de forma automatizada e idempotente el ciclo de arranque en contenedores de producción:
  1. `python manage.py migrate --no-input` (aplica migraciones pendientes).
  2. `python manage.py collectstatic --no-input` (recolecta estáticos para Django Admin).
  3. `python manage.py seed_all` (ejecuta seeders idempotentes sin duplicar registros).
  4. Ejecución del servidor WSGI de producción: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120`.
- Se adaptó [backend/Dockerfile](file:///c:/Users/PERSONAL/panaderia-SI1/backend/Dockerfile) para otorgar permisos de ejecución a `entrypoint.sh` y utilizarlo como `ENTRYPOINT`.

### B. Endpoint de Mantenimiento y Salvaguarda (`backend/config/urls.py`)
- Se mejoró `health_check` en [backend/config/urls.py](file:///c:/Users/PERSONAL/panaderia-SI1/backend/config/urls.py) para permitir disparar migraciones y seeders vía query parameter protegido (`?migrate=panaderia2026&seed=true`) como mecanismo de emergencia sin necesidad de SSH.

### C. Frontend (`LoginPage.tsx` y `KpiDashboardPage.tsx`)
- En [LoginPage.tsx](file:///c:/Users/PERSONAL/panaderia-SI1/frontend/src/apps/auth/LoginPage.tsx), se diferenció explícitamente el código de respuesta `HTTP 500` ("Error interno del servidor") del error de falta de conexión a la red.
- En [KpiDashboardPage.tsx](file:///c:/Users/PERSONAL/panaderia-SI1/frontend/src/apps/dashboard/kpis/KpiDashboardPage.tsx), se removió la variable `user` sin uso que bloqueaba la compilación TypeScript en producción.
- Verificación exitosa de compilación: `tsc -b && vite build` finalizado en 1m 20s sin advertencias de tipado.

---

## 🧪 4. Verificación y Despliegue
- El build del frontend pasa al 100% en local.
- Para aplicar en Render, se debe commitear y enviar el cambio a la rama `prueba` del repositorio remoto `bakery2` (`RSofi12/panaderia_santiago`).
