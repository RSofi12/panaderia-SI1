# Sesión de Desarrollo: Despliegue Django en Render detenido por permiso duplicado

- **Fecha:** 2026-10-14
- **Autor / Integrante:** equipo
- **Paquete / Módulo:** `apps.productos_inventario` / `materia_prima`
- **Casos de Uso abordados:** CU8 (gestión de materias primas), CU18 (historial de producción, bloqueado porque el backend no publica)
- **Ciclo:** Ciclo 2

---

## 1. Objetivo de la sesión

Saber por qué el servicio Python `panaderia-SI1` en Render sigue en el commit `1070850` y las pantallas de stock e historial responden 404.

## 2. Cambios realizados

- **Backend:**
  - Archivo modificado: `backend/apps/productos_inventario/materia_prima/migrations/0002_gestion_materias_primas_permission.py`
  - Antes de crear el permiso `gestionar_materias_primas`, la migración alinea la secuencia `permiso_id_permiso` en PostgreSQL.
- **Frontend:** sin cambios.
- **Render:** no se volvió a lanzar el deploy. El fallo leído es el de `d531b75` (14 oct 2026, 24,4 s): `IntegrityError: duplicate key value violates unique constraint "permiso_pkey"`.

## 3. Decisiones técnicas tomadas

El seed carga permisos con id fijo. En PostgreSQL un `INSERT` con id explícito no avanza el contador. La migración pedía el siguiente id y recibía uno ya usado. `setval` deja el contador en `MAX(id_permiso)`. En SQLite no se ejecuta, para no romper las pruebas.

## 4. Pendientes o siguientes pasos

- Subir este cambio a `main` y lanzar Manual Deploy del commit nuevo, no de `d531b75`.
- El servicio en vivo sigue siendo `1070850` hasta que un deploy quede en verde.
- La terminal local sigue detenida en Vim por un merge a `prueba`. Hay que salir de Vim antes de commitear.

## 5. Cómo probar lo implementado

1. En Render, el próximo deploy de `panaderia-SI1` no debe terminar en `permiso_pkey`.
2. El encabezado del servicio debe dejar de decir `1070850` y pasar a Live.
3. En el portal, Stock de materia prima e Historial de producción no deben mostrar el aviso rojo de conexión.
