# Plan de Fases e Implementación

## Sistema de Información Web — Panadería "Santiago"
**Ciclo Actual de Desarrollo:** 🔵 **Ciclo 1 — Base del Sistema, Seguridad, Catálogos y Auditoría (7 CU)**

---

## 🗺️ Resumen General de Ciclos (PUDS)

- [ ] **🔵 Ciclo 1 — Base del Sistema (7 CU):** CU 1, CU 2, CU 3, CU 4, CU 5, CU 6, CU 26
- [ ] **🟢 Ciclo 2 — Abastecimiento y Producción / MRP (6 CU):** CU 7, CU 8, CU 9, CU 10, CU 11, CU 12
- [ ] **🟡 Ciclo 3 — Comercialización y Ventas (7 CU):** CU 13, CU 14, CU 15, CU 16, CU 17, CU 18, CU 19
- [ ] **🔴 Ciclo 4 — Control Financiero y Reportes (6 CU):** CU 20, CU 21, CU 22, CU 23, CU 24, CU 25

---

# 🔵 FASES DETALLADAS — CICLO 1 (7 Casos de Uso)

---

### Fase 0: Configuración Base y Entorno de Desarrollo
- [ ] **Base de Datos & Conexión:**
  - [ ] Verificar conexión PostgreSQL con credenciales de `.env` en `backend/config/settings.py`.
  - [ ] Cargar/validar el esquema DDL de tablas base desde `Database_Panaderia_Santiago_FINAL.sql` (`rol`, `permiso`, `rol_permiso`, `usuario`, `bitacora`, `categoria_producto`, `producto`, `proveedor`).
- [ ] **Configuración Backend:**
  - [ ] Instalar dependencias esenciales (`djangorestframework`, `django-cors-headers`, `python-decouple`, `psycopg2-binary`, etc.).
  - [ ] Configurar CORS para permitir comunicación con `http://localhost:5173`.
  - [ ] Configurar middleware de autenticación y manejo global de excepciones.
- [ ] **Configuración Frontend:**
  - [ ] Configurar cliente Axios/Fetch con interceptores para tokens y manejo de errores 401/403 (token expirado o sin permisos).
        Ojo: el login **no** devuelve 401 ni 403, devuelve `400`/`429`. El interceptor no debe interpretar un `400` de login como "token expirado" e intentar refrescar, porque provocaría un bucle de reintentos.
  - [ ] Configurar React Router DOM para rutas públicas y rutas protegidas por rol.
  - [ ] Configurar estado global de autenticación (`AuthContext`).

---

### Fase 1: CU 1 — Iniciar sesión
**Actor:** Todos (`Administrador`, `Propietario`, `Personal De Ventas`, `Personal De Producción`)  
**Prioridad:** Alta | **Riesgo:** Medio (Manejo de credenciales, hash de contraseña y tokens de sesión)

- [ ] **Backend (`apps.usuarios_seguridad`):**
  - [ ] Modelo `Usuario` y `Rol` configurados con campo `activo` y `hash_contrasena`.
  - [ ] Serializador de Login (`LoginSerializer`) que valide credenciales y estado activo del usuario.
  - [ ] Servicio de autenticación con verificación segura de hash (`check_password` o bcrypt/argon2).
  - [ ] Endpoint `POST /api/auth/login/` que retorna datos del usuario, rol y token de sesión.
  - [ ] Endpoint `POST /api/auth/logout/` para invalidar sesión.
  - [ ] Registro automático en Bitácora del evento de inicio de sesión exitoso y fallido.
- [ ] **Frontend:**
  - [ ] Pantalla de Login con formulario reactivo (usuario y contraseña).
  - [ ] Validación de campos en cliente (campos obligatorios).
  - [ ] Almacenamiento seguro de credenciales de sesión en `AuthContext` / `localStorage`.
  - [ ] Redirección inteligente al dashboard o módulo según el rol del usuario autenticado.
- [ ] **Pruebas y Verificación:**
  - [ ] Prueba unitaria de login con credenciales válidas -> `200 OK`.
  - [ ] Prueba de login con credenciales inválidas -> `400 Bad Request`.
  - [ ] Prueba de login con usuario inexistente -> `400 Bad Request` (mismo mensaje que contraseña incorrecta, para no revelar qué usernames existen).
  - [ ] Prueba de login con usuario inactivo (`activo=False`) -> `400 Bad Request`.
  - [ ] Prueba de bloqueo tras agotar los intentos fallidos -> `429 Too Many Requests` con `Retry-After` y `retry_after_seconds`.
  - [ ] Prueba de que la ventana de bloqueo respeta los minutos configurados en `ConfiguracionSeguridad`.
  - [ ] Prueba de que al vencer la ventana el contador se reinicia y el usuario dispone de 3 intentos nuevos.
  - [ ] Verificar que el bloqueo concurrente no duplica contadores (dos intentos simultáneos no se pierden).

> **Nota de diseño (CU1).** El contrato de login es `400` / `400` / `429` y no `401` / `403` / `423`:
> - Credenciales inválidas, usuario inexistente y cuenta inactiva devuelven `400`, no `401`. Un `401` implica que el cliente puede reenviar credenciales sin más, y aquí eso alimentaría un ataque de fuerza bruta. El mensaje es deliberadamente genérico y se registra en bitácora con `nombre_usuario_intento` y `agente_usuario`.
> - El bloqueo es `429`, no `423 Locked`. `429` es el código estándar que significa "demasiadas peticiones, reintenta más tarde" y lo entienden los clientes y proxies automáticamente; además permite acompañar la respuesta con `Retry-After`. `423` no lo interpreta casi nadie.
> - El `429` es siempre acumulativo: la ventana de bloqueo no se extiende en cada intento, así un atacante no puede alargar el bloqueo indefinidamente.

---

### Fase 2: CU 2 — Recuperar contraseña
**Actor:** Todos  
**Prioridad:** Media | **Riesgo:** Medio (Generación de tokens temporales de un solo uso y expiración)

- [ ] **Backend (`apps.usuarios_seguridad`):**
  - [ ] Tabla/Mecanismo para tokens temporales de restablecimiento con fecha de expiración.
  - [ ] Endpoint `POST /api/auth/password-reset-request/` (solicitud por email o nombre de usuario).
  - [ ] Servicio de envío/generación de enlace o código de recuperación (consola/email).
  - [ ] Endpoint `POST /api/auth/password-reset-confirm/` que valida el token y actualiza la contraseña cifrada.
  - [ ] Registro en Bitácora del cambio de contraseña por recuperación.
- [ ] **Frontend:**
  - [ ] Pantalla "Olvidé mi contraseña" para ingresar usuario/email.
  - [ ] Pantalla de ingreso de nueva contraseña con validación de fortaleza y confirmación.
  - [ ] Mensajes de éxito y redirección al login.
- [ ] **Pruebas y Verificación:**
  - [ ] Prueba de solicitud con usuario existente -> token generado.
  - [ ] Prueba de confirmación con token válido -> contraseña actualizada exitosamente.
  - [ ] Prueba con token expirado o reutilizado -> `400 Bad Request`.

---

### Fase 3: CU 3 — Gestionar usuarios
**Actor:** `Administrador`  
**Prioridad:** Alta | **Riesgo:** Bajo (CRUD administrativo con activación/inactivación)

- [x] **Backend (`apps.usuarios_seguridad`):** — *completado y verificado el 2026-09-28*
  - [x] `UsuarioSerializer` con validaciones de campos únicos (`nombre_usuario`) y formato de datos. → Se partió en 6 serializers por lectura/escritura; la unicidad sin distinguir mayúsculas la impone la base con el índice `usuario_username_unico_ci` sobre `Lower(nombre_usuario)`, no solo el `__iexact` del serializer.
  - [x] Servicio de creación/edición de usuarios con hash automático de contraseñas. → `users/services/usuarios.py`, con el hash a cargo de `set_password()` y las tres guardas de auto-destrucción.
  - [x] Endpoints REST protegidos para rol `Administrador`:
    - `GET /api/usuarios/` (Listar usuarios con filtros por estado/rol). → Paginado y buscable; `activo` e `id_rol` a mano, sin `django-filter`.
    - `POST /api/usuarios/` (Crear nuevo usuario).
    - `GET /api/usuarios/<id>/` (Detalle de usuario).
    - `PUT/PATCH /api/usuarios/<id>/` (Modificar datos de usuario).
    - `PATCH /api/usuarios/<id>/toggle-activo/` (Activar / Inactivar usuario).
    - *Extensiones aprobadas:* `POST /api/usuarios/<id>/restablecer-contrasena/`, `POST /api/usuarios/<id>/desbloquear/`, `GET /api/usuarios/roles/`.
  - [x] Registro en Bitácora de toda alta, modificación o cambio de estado de usuarios. → Cuatro acciones nuevas en `AccionBitacora`; el desbloqueo reutiliza `DESBLOQUEO_CUENTA` de CU1.
- [ ] **Frontend:**
  - [ ] Vista de listado de usuarios con tabla interactiva, buscador y filtros por rol y estado.
  - [ ] Modal/Formulario de creación de usuario con selector de rol.
  - [ ] Modal de edición de datos de usuario.
  - [ ] Botón de alternar estado Activo/Inactivo con confirmación modal.
- [x] **Pruebas y Verificación (backend):** — *52 pruebas propias en verde; suite del paquete 144 en verde*
  - [x] Intentar acceder con rol `Personal De Ventas` -> `403 Forbidden`. → Cubierto con dos pruebas: una por `permission_classes` y otra por el flujo completo con token.
  - [x] Acceso con `Administrador` -> `200 OK` y operaciones CRUD funcionando.
  - [x] Verificar que no se puedan duplicar nombres de usuario. → Cubierto en el serializer, en el servicio y contra la base real: el índice rechaza `MGONZALES` frente a `mgonzales`.

> **Pendiente de esta fase:** solo el bloque de Frontend. La suite corrió contra SQLite
> porque `panaderia_admin` no tiene `CREATEDB`; ver `docs/ai/HANDOFF_LATEST.md`.

---

### Fase 4: CU 4 — Asignar roles y permisos
**Actor:** `Administrador`  
**Prioridad:** Alta | **Riesgo:** Medio (Integridad del control de acceso RBAC)

- [ ] **Backend (`apps.usuarios_seguridad`):**
  - [ ] Modelos `Rol`, `Permiso` y `RolPermiso` cargados con los datos semilla iniciales:
    - Roles: `Administrador`, `Propietario`, `Personal De Ventas`, `Personal De Producción`.
  - [ ] `RolSerializer` y `PermisoSerializer`.
  - [ ] Endpoints:
    - `GET /api/roles/` (Listar roles y sus permisos asociados).
    - `GET /api/permisos/` (Listar catálogo de permisos del sistema).
    - `POST /api/roles/<id>/permisos/` (Actualizar la asignación de permisos a un rol).
    - `PATCH /api/usuarios/<id>/rol/` (Asignar rol a un usuario).
  - [ ] Registro en Bitácora de los cambios de permisos o roles.
- [ ] **Frontend:**
  - [ ] Vista de gestión de roles y matriz de permisos por módulo.
  - [ ] Selector de permisos con checkboxes por categoría de módulo.
  - [ ] Modal en gestión de usuarios para cambiar el rol de un usuario rápidamente.
- [ ] **Pruebas y Verificación:**
  - [ ] Comprobar que un usuario con nuevo rol adquiere inmediatamente los permisos correspondientes.
  - [ ] Proteger endpoints contra accesos no autorizados mediante la clase `IsAdminUserRole`.

---

### Fase 5: CU 26 — Gestionar bitácora
**Actor:** `Administrador`  
**Prioridad:** Baja | **Riesgo:** Bajo (Consulta y trazabilidad de eventos del sistema)

- [ ] **Backend (`apps.usuarios_seguridad`):**
  - [ ] Modelo `Bitacora` con campos `id_bitacora`, `id_usuario`, `accion`, `tabla_afectada`, `descripcion`, `fecha_hora`.
  - [ ] Función utilitaria centralizada `registrar_bitacora(usuario, accion, tabla, descripcion)` exportada para todos los módulos.
  - [ ] `BitacoraSerializer` con datos anidados del usuario responsable.
  - [ ] Endpoint `GET /api/bitacora/` con soporte de:
    - Filtro por rango de fechas (`fecha_inicio`, `fecha_fin`).
    - Filtro por usuario responsable (`id_usuario`).
    - Filtro por tipo de acción (`CREACION`, `MODIFICACION`, `ELIMINACION`, `LOGIN`, `CAMBIO_ESTADO`).
    - Filtro por tabla afectada (`usuario`, `producto`, `proveedor`, etc.).
    - Paginación de resultados.
- [ ] **Frontend:**
  - [ ] Vista de Bitácora / Auditoría exclusiva para el rol `Administrador`.
  - [ ] Filtros superiores por fecha, usuario, módulo y tipo de acción.
  - [ ] Tabla con badges de color según la acción (verde = creación, amarillo = edición, rojo = eliminación, azul = sesión).
  - [ ] Modal de detalle para ver la descripción completa del registro de auditoría.
- [ ] **Pruebas y Verificación:**
  - [ ] Realizar una acción en usuarios o productos y verificar que aparezca inmediatamente en el listado de bitácora.
  - [ ] Probar filtros por fecha y por usuario.

---

### Fase 6: CU 5 — Gestionar productos
**Actor:** `Propietario`  
**Prioridad:** Alta | **Riesgo:** Bajo (Catálogo maestro de panes y precios)

- [ ] **Backend (`apps.productos_inventario`):**
  - [ ] Modelos `CategoriaProducto` y `Producto` con campos:
    - `id_producto`, `id_categoria`, `nombre`, `descripcion`, `costo_produccion`, `porcentaje_ganancia`, `precio_sugerido`, `precio_venta`, `activo`.
  - [ ] Cargar catálogo inicial de panes: Marraqueta, Arani, Chama, Casero, Tortilla, Integral, Gusanito, Pan con azúcar, Pan dulce, Pan mollete, Pan galleta, Pan de leche.
  - [ ] `ProductoSerializer` con cálculo de `precio_sugerido` basado en `costo_produccion` y `porcentaje_ganancia`.
  - [ ] Endpoints REST:
    - `GET /api/productos/` (Listar productos con filtros por categoría y estado activo).
    - `POST /api/productos/` (Crear nuevo producto - solo Propietario).
    - `GET /api/productos/<id>/` (Detalle de producto).
    - `PUT/PATCH /api/productos/<id>/` (Actualizar producto y registrar en historial de precios).
    - `PATCH /api/productos/<id>/toggle-activo/` (Inactivar/Activar producto).
    - `GET /api/categorias-producto/` (Listar categorías).
  - [ ] Registro en Bitácora de altas, modificaciones de precios y cambios de estado.
- [ ] **Frontend:**
  - [ ] Vista del Catálogo de Productos con vista en tarjetas o tabla.
  - [ ] Modal/Formulario de alta de producto con cálculo dinámico de precio sugerido.
  - [ ] Modal de edición de producto con alerta sobre cambio de precio de venta.
  - [ ] Filtro por categoría de pan y buscador por nombre.
- [ ] **Pruebas y Verificación:**
  - [ ] Validar que `precio_venta` no pueda ser menor o igual a cero.
  - [ ] Comprobar que el `Propietario` puede crear/editar y `Personal De Ventas` solo puede consultar.

---

### Fase 7: CU 6 — Gestionar proveedores
**Actor:** `Propietario`  
**Prioridad:** Media | **Riesgo:** Bajo (Registro de proveedores de insumos)

- [ ] **Backend (`apps.compras`):**
  - [ ] Modelo `Proveedor` con campos `id_proveedor`, `nombre`, `telefono`, `direccion`, `fecha_registro`, `activo`.
  - [ ] `ProveedorSerializer` con validaciones de campos obligatorios y formato de teléfono.
  - [ ] Endpoints REST:
    - `GET /api/proveedores/` (Listar proveedores activos/inactivos).
    - `POST /api/proveedores/` (Crear proveedor - solo Propietario).
    - `GET /api/proveedores/<id>/` (Detalle de proveedor).
    - `PUT/PATCH /api/proveedores/<id>/` (Modificar datos de contacto/dirección).
    - `PATCH /api/proveedores/<id>/toggle-activo/` (Inactivar/Activar proveedor).
  - [ ] Registro en Bitácora de operaciones con proveedores.
- [ ] **Frontend:**
  - [ ] Vista de Proveedores con directorio de contactos, teléfonos y direcciones.
  - [ ] Modal de registro de nuevo proveedor.
  - [ ] Modal de edición de datos de proveedor.
  - [ ] Buscador de proveedores por nombre o teléfono.
- [ ] **Pruebas y Verificación:**
  - [ ] Verificar que un proveedor inactivo no esté disponible para compras en el Ciclo 2.
  - [ ] Probar validaciones de campos requeridos.

---

### Fase 8: Integración Global y Cierre del Ciclo 1
- [ ] **Pruebas de Integración y Seguridad:**
  - [ ] Simulación de sesión con los 4 roles y verificación de acceso a sus vistas correspondientes.
  - [ ] Comprobar que todas las mutaciones realizadas en Usuarios, Productos y Proveedores quedaron registradas en la Bitácora con su usuario correspondiente.
- [ ] **Revisión de Calidad:**
  - [ ] Respuestas JSON homogéneas (`{ success: true, data: ..., message: ... }`).
  - [ ] Manejo de códigos de estado HTTP correctos.
  - [ ] Frontend sin errores de consola y con diseño responsivo.

---

# 📅 HOJA DE RUTA — CICLOS POSTERIORES

### 🟢 Ciclo 2 — Abastecimiento y Producción / MRP (6 CU)
- [ ] **CU 7:** Registrar compra de materia prima (`apps.compras` - Propietario).
- [ ] **CU 8:** Consultar stock de materia prima (`apps.productos_inventario` - Producción, Propietario).
- [ ] **CU 9:** Consultar alertas de bajo stock (`apps.productos_inventario` - Producción, Propietario).
- [ ] **CU 10:** Registrar producción diaria con consumo automático de insumos (`apps.productos_inventario` - Producción).
- [ ] **CU 11:** Consultar historial de producción (`apps.productos_inventario` - Producción).
- [ ] **CU 12:** Consultar existencias de productos terminados (`apps.productos_inventario` - Propietario, Ventas).

### 🟡 Ciclo 3 — Comercialización y Ventas (7 CU)
- [ ] **CU 13:** Registrar venta en mostrador (efectivo / QR) con descuento de stock (`apps.comercializacion` - Ventas).
- [ ] **CU 14:** Registrar pedido anticipado (`apps.comercializacion` - Ventas).
- [ ] **CU 15:** Consultar estado de pedido (`apps.comercializacion` - Ventas, Producción).
- [ ] **CU 16:** Generar comprobante de venta (`apps.comercializacion` - Ventas).
- [ ] **CU 17:** Consultar disponibilidad de productos en mostrador (`apps.comercializacion` - Ventas).
- [ ] **CU 18:** Registrar baja de productos terminados por pérdida/merma (`apps.productos_inventario` - Producción).
- [ ] **CU 19:** Consultar historial de precios de productos (`apps.productos_inventario` - Propietario).

### 🔴 Ciclo 4 — Control Financiero y Reportes (6 CU)
- [ ] **CU 20:** Registrar gasto / inversión operativa (`apps.compras` - Propietario).
- [ ] **CU 21:** Generar reporte de ventas por periodo/método de pago (`apps.reportes` - Propietario).
- [ ] **CU 22:** Generar reporte de producción vs. ventas (`apps.reportes` - Propietario).
- [ ] **CU 23:** Generar reporte de existencias consolidado (`apps.reportes` - Propietario).
- [ ] **CU 24:** Generar reporte de compras y gastos (`apps.reportes` - Propietario).
- [ ] **CU 25:** Generar reporte de resultados económicos / balance general (`apps.reportes` - Propietario).
