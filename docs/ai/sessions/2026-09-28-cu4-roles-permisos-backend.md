# Sesión 2026-09-28: Implementación Backend CU04 — Asignar roles y permisos

**Objetivo:** Implementar la capa completa del backend para el Caso de Uso 04 (Asignar roles y permisos), siguiendo la arquitectura modular de paquetes de Django, conectando la auditoría en Bitácora (CU26), alineando el DDL y blindando la seguridad con guardas anti-autobloqueo y pruebas automatizadas.

## 1. Cambios Realizados

### A. Modelos y Base de Datos
- **`permisos.models.Permiso`**:
  - Incorporación del enum `ModuloPermiso(models.TextChoices)` con los 5 paquetes del sistema (`usuarios_seguridad`, `productos_inventario`, `compras`, `comercializacion`, `reportes`).
  - Campo `modulo` agregado al modelo `Permiso`.
  - Restricción `UniqueConstraint(Lower('nombre'), name='permiso_nombre_unico_ci')` para evitar duplicados por mayúsculas.
  - Migración aplicada: `permisos/migrations/0002_permiso_modulo_alter_permiso_nombre_and_more.py`.
- **`roles.models.Rol` y `RolPermiso`**:
  - Incorporación de métodos de dominio UML `asignar_permiso()` y `quitar_permiso()` en la clase `Rol`.
  - Restricción `UniqueConstraint(Lower('nombre'), name='rol_nombre_unico_ci')` en `Rol`.
  - Reemplazo de `unique_together` por `UniqueConstraint(fields=['rol', 'permiso'], name='rol_permiso_unico')` en `RolPermiso`.
  - Migración aplicada: `roles/migrations/0002_alter_rolpermiso_unique_together_and_more.py`.
- **`bitacora.models.AccionBitacora`**:
  - Adición de las 5 acciones de auditoría para CU4: `ALTA_ROL`, `EDICION_ROL`, `ASIGNAR_PERMISO_ROL`, `REVOCAR_PERMISO_ROL`, `ACTUALIZACION_MATRIZ_PERMISOS`.
- **DDL (`docs/informes/Database_Panaderia_Santiago.sql`)**:
  - Documentada la columna `modulo` en `permiso` (`-- MODIFICADA (CU4)`).
  - Resuelta la deriva de `rol_permiso`: alineada con la clave subrogada `id` y `UNIQUE("id_rol", "id_permiso")`.
  - Documentado `ON DELETE SET NULL` en la llave foránea de `usuario.id_rol`.

### B. Capa de Servicios y Seguridad
- **`roles/constants.py`**:
  - `ROLES_PROTEGIDOS` (`Administrador`, `Propietario`, `Personal de Ventas`, `Personal de Producción`).
  - `PERMISO_CU4 = 'asignar_permisos'`.
- **`roles/exceptions.py`**:
  - `OperacionInvalidaError` (HTTP 400 Bad Request).
- **`roles/services/matriz.py`**:
  - Operaciones atómicas `@transaction.atomic`.
  - `crear_rol()`: valida unicidad insensible a mayúsculas y registra en Bitácora (`ALTA_ROL`).
  - `editar_rol()`: bloquea modificación de nombre en roles protegidos y registra en Bitácora (`EDICION_ROL`).
  - `asignar_permiso_a_rol()`: asocia un permiso y audita en Bitácora (`ASIGNAR_PERMISO_ROL`).
  - `quitar_permiso_de_rol()`: quita un permiso con validación de anti-autobloqueo y audita (`REVOCAR_PERMISO_ROL`).
  - `reemplazar_permisos_rol()`: reemplaza la matriz completa calculando el diff exacto de agregados/removidos, valida guardas anti-autobloqueo y audita (`ACTUALIZACION_MATRIZ_PERMISOS`).
  - **Guardas de seguridad implementadas:**
    1. HTTP 405 Method Not Allowed en operaciones `DELETE` de roles y permisos.
    2. Inmutabilidad de los nombres de los 4 roles protegidos.
    3. El rol `Administrador` nunca puede perder el permiso `asignar_permisos`.
    4. El actor autenticado no puede remover `asignar_permisos` de su propio rol activo.

### C. Serializadores, ViewSets y URLs
- **`permisos/serializers.py` y `permisos/views.py`**:
  - `PermisoSerializer` con `modulo_display`.
  - `PermisoViewSet` (solo lectura, sin paginación, protegido con `TienePermiso('asignar_permisos')`).
  - Endpoint especial `/api/permisos/agrupados/` para entregar el catálogo organizado por los 5 módulos.
- **`roles/serializers.py` y `roles/views.py`**:
  - `RolListSerializer` con métricas `total_permisos`, `total_usuarios` y bandera `es_protegido`.
  - `RolDetalleSerializer` con lista de objetos `permisos`.
  - `RolViewSet` con acciones:
    - `GET /api/roles/`
    - `POST /api/roles/`
    - `GET /api/roles/<id>/`
    - `PATCH /api/roles/<id>/`
    - `PUT /api/roles/<id>/permisos/`
    - `POST /api/roles/<id>/permisos/asignar/`
    - `POST /api/roles/<id>/permisos/quitar/`
  - Métodos `DELETE` excluidos (`http_method_names`).
- **`config/urls.py`**:
  - Montadas las rutas bajo `/api/roles/` y `/api/permisos/`.
- **`roles/admin.py`**:
  - Removido `RolPermisoInline` para canalizar las mutaciones de permisos exclusivamente a través de la API auditada.

### D. Poblamiento de Datos (Seed)
- **`seed_usuarios.py`**:
  - Permisos 1 a 11 actualizados con su correspondiente `modulo`.
  - Incorporado el permiso 12: `asignar_permisos` (`usuarios_seguridad`).
  - Rol `Administrador` actualizado con los 12 permisos.
  - Ejecutado exitosamente en base de datos.

## 2. Validación y Pruebas Ejecutadas
- `python manage.py check`: 0 errores.
- `python manage.py test apps.usuarios_seguridad.permisos apps.usuarios_seguridad.roles`:
  - **18 tests ejecutados en 8.3s, 100% exitosos.**
  - Cubre: autenticación (401/403/200), listado, detalle, métricas, alta, unicidad case-insensitive, edición de descripción, rechazo de renombre de rol protegido, prohibición de DELETE (405), asignación y revocación puntual, actualización de matriz masiva, registro en Bitácora con diff, y test dinámico de revocación inmediata.
- `python manage.py test apps.usuarios_seguridad.users`:
  - **52 tests de regresión ejecutados en 10.1s, 100% exitosos.**
