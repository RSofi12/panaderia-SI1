# Sesión de Desarrollo: Adición del atributo tipo_rol en la entidad Rol (CU4)

- **Fecha:** 2026-11-05
- **Autor / Integrante:** Pilar
- **Paquete / Módulo:** `apps.usuarios_seguridad.roles` y `frontend` (`src/apps/dashboard/usuarios/roles`)
- **Casos de Uso abordados:** CU4 (Asignar roles y permisos)
- **Ciclo:** Ciclo 1 (Mantenimiento y extensión de Usuarios y Seguridad)

---

## 1. 🎯 Objetivo de la sesión
Modificar la base de datos y la arquitectura del sistema agregando un nuevo atributo textual (`tipo_rol`) en la entidad `Rol` para clasificar y categorizar cada perfil de usuario (ej: "Administrativo", "Operativo", "Gerencial", "Mostrador"), permitiendo su edición y visualización tanto en el backend Django como en el frontend React.

---

## 2. 🛠️ Cambios realizados

### Base de Datos y Backend (`backend/apps/usuarios_seguridad/roles/`):
- **Modelo (`models.py`):** Agregado campo `tipo_rol = models.CharField(max_length=50, blank=True, default='', verbose_name='Tipo de Rol')`.
- **Migración (`migrations/0003_rol_tipo_rol.py`):** Generada y aplicada exitosamente contra PostgreSQL (`ALTER TABLE rol ADD COLUMN tipo_rol varchar(50) DEFAULT '' NOT NULL`).
- **Documentación DDL (`docs/informes/Database_Panaderia_Santiago.sql`):** Actualizada la tabla `rol` con la nueva columna y comentario explicativo.
- **Serializadores (`serializers.py`):**
  - `RolListSerializer` y `RolDetalleSerializer`: Exponen `tipo_rol`.
  - `RolCrearSerializer` y `RolActualizarSerializer`: Validan `tipo_rol` como campo textual opcional.
- **Servicios (`services/matriz.py`):** `crear_rol()` y `editar_rol()` gestionan la persistencia y auditoría de `tipo_rol`.
- **Vistas (`views.py`):** `RolViewSet` enlaza `tipo_rol` al flujo de alta y edición.
- **Seeder (`seed_usuarios.py`):** Asignados tipos por defecto a los 4 roles base:
  - Administrador: `"Administrativo"`
  - Propietario: `"Gerencial"`
  - Personal de Ventas: `"Mostrador"`
  - Personal de Producción: `"Operativo"`

### Frontend (`frontend/src/`):
- **Tipos TypeScript (`types/roles.ts`):** Agregado `tipo_rol` en `RolListado`, `RolDetalle`, `CrearRol` y `EditarRol`.
- **Formulario Modal (`ModalRol.tsx`):** Agregado campo input interactivo de texto para el "Tipo de rol".
- **Vista de Tarjetas (`TarjetaRol.tsx`):** Renderizado de un chip / badge visual con el `tipo_rol` junto al nombre del perfil.

---

## 3. 🧠 Decisiones técnicas tomadas
- Se utilizó `CharField(max_length=50, blank=True, default='')` para asegurar compatibilidad retroactiva con roles existentes sin requerir bloqueos en PostgreSQL ni valores nulos.
- Se mantuvieron inalteradas las guardas de seguridad contra roles base del sistema, permitiendo ahora editar tanto la descripción como el tipo de rol sin alterar el identificador ni el nombre protegido.

---

## 4. 🧪 Cómo probar lo implementado
1. Iniciar sesión como Administrador (`admin` / `Admin123!`).
2. Ir a **Usuarios y Seguridad $\rightarrow$ Roles y permisos** (`/dashboard/usuarios?tab=roles`).
3. Observar los roles existentes: cada tarjeta muestra su etiqueta de tipo (ej: *Administrativo*, *Gerencial*, *Mostrador*, *Operativo*).
4. Hacer clic en **"Nuevo rol"** o en el botón de edición de un rol: escribir un tipo de rol y guardar.

