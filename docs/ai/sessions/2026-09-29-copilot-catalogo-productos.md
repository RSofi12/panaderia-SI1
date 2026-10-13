# Sesión de Desarrollo: Carga del catálogo de productos

- **Fecha:** 2026-09-29
- **Autor / Integrante:** GitHub Copilot
- **Paquete / Módulo:** `apps.productos_inventario`
- **Casos de Uso abordados:** CU5
- **Ciclo:** Ciclo 1

---

## 1. Objetivo de la sesión
Hacer que las categorías y productos del catálogo estén cargados al preparar el backend para iniciar el proyecto.

## 2. Cambios realizados
- **Backend:** Se ejecutó `seed_productos` en la base de datos configurada; antes de la carga había 0 categorías y 0 productos.
- **Frontend:** Sin cambios; la pantalla ya consume las categorías y productos mediante la API.
- **Documentación:** Se agregó `python manage.py seed_productos` al procedimiento de inicio del `README.md`, después de migraciones y del seed de usuarios.

## 3. Decisiones técnicas tomadas
- Se reutilizó el comando idempotente existente `seed_productos`; no se agregó una carga automática en cada inicio del servidor.
- La semilla debe ejecutarse una vez por base de datos nueva. Las ejecuciones posteriores no duplican categorías ni productos.

## 4. Pendientes o siguientes pasos
- Ninguno para CU5.

## 5. Cómo probar lo implementado
- Desde `backend`, ejecutar `python manage.py seed_productos`.
- Confirmar que aparecen 7 categorías y 12 productos en `/dashboard/productos` con un usuario que tenga permiso `gestionar_productos`.