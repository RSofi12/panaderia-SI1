# Arquitectura del Sistema

## Sistema de Información Web — Panadería "Santiago"
**Backend:** Django 6+ / Django REST Framework (Python 3.12+)  
**Frontend:** React (TypeScript + Vite)  
**Base de Datos:** PostgreSQL 14+  

---

## 1. Visión General de la Arquitectura

El sistema está diseñado bajo una **arquitectura en capas desacoplada** con comunicación mediante API REST. Esta estructura asegura alta cohesión, bajo acoplamiento, mantenibilidad y escalabilidad a lo largo de los 4 ciclos del proyecto.

```
+-------------------------------------------------------------------------------+
|                       CAPA DE PRESENTACIÓN (FRONTEND)                         |
|  React (TypeScript) + Vite + Tailwind CSS / UI Components                     |
|  - Vistas por Rol: Administrador | Propietario | Ventas | Producción          |
|  - Manejo de Estado y Auth Context                                            |
|  - Cliente HTTP (Axios / Fetch API con Interceptores)                         |
+---------------------------------------+---------------------------------------+
                                        | (Peticiones HTTP/JSON - REST)
                                        v
+-------------------------------------------------------------------------------+
|                         CAPA DE APLICACIÓN (BACKEND)                          |
|  Django REST Framework (DRF)                                                  |
|  +-------------------------------------------------------------------------+  |
|  | URLs & Router (Enrutamiento y versionado)                               |  |
|  +-------------------------------------------------------------------------+  |
|  | Middlewares & Seguridad (CORS, Autenticación, Bitácora Interceptor)      |  |
|  +-------------------------------------------------------------------------+  |
|  | Permisos & RBAC (Role-Based Access Control por Actores)                 |  |
|  +-------------------------------------------------------------------------+  |
|  | Vistas / ViewSets (Controladores HTTP, orquestación de entrada/salida) |  |
|  +-------------------------------------------------------------------------+  |
|  | Serializers (Validación de esquema, parseo y formato de datos)         |  |
|  +-------------------------------------------------------------------------+  |
|  | Servicios / Lógica de Negocio (Transacciones atómicas, cálculos, MRP)   |  |
|  +-------------------------------------------------------------------------+  |
|  | Modelos ORM (Abstracción relacional y restricciones de integridad)      |  |
|  +-------------------------------------------------------------------------+  |
+---------------------------------------+---------------------------------------+
                                        | (SQL / Transacciones ACID)
                                        v
+-------------------------------------------------------------------------------+
|                        CAPA DE DATOS (POSTGRESQL 14+)                         |
|  Tablas Normalizadas, Llaves Foráneas (FK), Triggers y Restricciones Físicas  |
+-------------------------------------------------------------------------------+
```

---

## 2. Organización de Paquetes en `backend/apps/`

De acuerdo con el diseño modular y el mapeo oficial de casos de uso ([`PACKAGE_CU_MAP.md`](file:///c:/Users/PERSONAL/panaderia-SI1/backend/apps/PACKAGE_CU_MAP.md)), el backend se divide exactamente en **5 paquetes (Django apps)**:

```
backend/
├── config/                      # Configuración global del proyecto Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py              # Instalación de apps, DB, middlewares, etc.
│   ├── urls.py                  # Enrutador principal que incluye las URLs de cada app
│   └── wsgi.py
├── apps/                        # Directorio raíz de módulos del sistema
│   ├── __init__.py
│   ├── PACKAGE_CU_MAP.md        # Matriz oficial de Casos de Uso por Paquete y Ciclo
│   │
│   ├── usuarios_seguridad/      # Módulo 1: Usuarios, Roles, Permisos y Bitácora
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py            # Rol, Permiso, RolPermiso, Usuario, Bitacora
│   │   ├── serializers.py       # Serializadores y validadores DRF
│   │   ├── permissions.py       # Clases de permisos personalizadas (RBAC)
│   │   ├── services.py          # Lógica de autenticación, hash, registro de bitácora
│   │   ├── urls.py              # Rutas /api/usuarios/, /api/auth/, /api/bitacora/
│   │   └── views.py             # ViewSets y APIViews de seguridad
│   │
│   ├── productos_inventario/    # Módulo 2: Catálogo, Stock Insumos y Stock Panes
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py            # CategoriaProducto, Producto, MateriaPrima,
│   │   │                        # InventarioMateriaPrima, InventarioProductoTerminado,
│   │   │                        # Produccion, DetalleProduccion, Movimientos, etc.
│   │   ├── serializers.py
│   │   ├── services.py          # Lógica de producción (MRP), cálculo de costos y mermas
│   │   ├── urls.py              # /api/productos/, /api/inventario/, /api/produccion/
│   │   └── views.py
│   │
│   ├── compras/                 # Módulo 3: Proveedores, Compras de Insumos y Gastos
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py            # Proveedor, Compra, DetalleCompra, MovimientoEconomico
│   │   ├── serializers.py
│   │   ├── services.py          # Lógica de compras e impacto en inventario y finanzas
│   │   ├── urls.py              # /api/proveedores/, /api/compras/, /api/gastos/
│   │   └── views.py
│   │
│   ├── comercializacion/        # Módulo 4: Clientes, Ventas (Mostrador/QR) y Pedidos
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py            # Cliente, Pedido, DetallePedido, Venta, DetalleVenta
│   │   ├── serializers.py
│   │   ├── services.py          # Registro de ventas, pedidos, comprobantes y stock
│   │   ├── urls.py              # /api/ventas/, /api/pedidos/, /api/clientes/
│   │   └── views.py
│   │
│   └── reportes/                # Módulo 5: Generación y Agregación de Reportes
│       ├── migrations/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── serializers.py
│       ├── services.py          # Consultas SQL optimizadas y consolidación financiera
│       ├── urls.py              # /api/reportes/ventas, /produccion, /resultados, etc.
│       └── views.py
├── manage.py
└── requirements.txt
```

---

## 3. Mapeo entre Tablas Físicas SQL y Paquetes Django

Las tablas definidas en [`Database_Panaderia_Santiago_FINAL.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/Database_Panaderia_Santiago_FINAL.sql) se distribuyen de forma coherente en las 5 aplicaciones:

| Paquete Django | Tablas de la Base de Datos | Casos de Uso que Implementa |
|---|---|---|
| **`apps.usuarios_seguridad`** | `rol`, `permiso`, `rol_permiso`, `usuario`, `bitacora` | **CU 1, CU 2, CU 3, CU 4, CU 26** |
| **`apps.productos_inventario`** | `categoria_producto`, `producto`, `producto_materia_prima`, `historial_precio_producto`, `materia_prima`, `historial_precio_materia_prima`, `inventario_materia_prima`, `movimiento_materia_prima`, `inventario_producto_terminado`, `movimiento_producto_terminado`, `produccion`, `detalle_produccion`, `nota_perdida_producto` | **CU 5, CU 8, CU 9, CU 10, CU 11, CU 12, CU 18, CU 19** |
| **`apps.compras`** | `proveedor`, `compra`, `detalle_compra`, `movimiento_economico` | **CU 6, CU 7, CU 20** |
| **`apps.comercializacion`** | `cliente`, `pedido`, `detalle_pedido`, `venta`, `detalle_venta` | **CU 13, CU 14, CU 15, CU 16, CU 17** |
| **`apps.reportes`** | *(Vistas / Consultas agregadas de todas las tablas anteriores)* | **CU 21, CU 22, CU 23, CU 24, CU 25** |

---

## 4. Patrón de Capas Interno por Paquete

Para mantener el código limpio y fácil de probar, cada paquete sigue un patrón estándar de responsabilidades:

1. **Model Layer (`models.py`):**
   - Refleja fielmente los campos, tipos, restricciones `null/blank`, `unique`, `default` y llaves foráneas definidas en la base de datos física.
   - Define nombres de tabla explícitos con `db_table = 'nombre_tabla'` y métodos estándar `__str__()`.

2. **Service / Business Logic Layer (`services.py`):**
   - **Regla de Oro:** La lógica de negocio compleja (como el descuento de inventario al registrar una producción o venta, o el hash de contraseñas) **NO debe residir en las vistas ni en los serializadores**, sino en funciones o clases de servicio.
   - Utiliza transacciones atómicas (`@transaction.atomic`) para garantizar que las operaciones con múltiples escrituras sean totalmente consistentes.
   - Llama a la utilidad de bitácora para auditar cambios críticos.

3. **Serializer Layer (`serializers.py`):**
   - Valida la integridad del payload entrante (tipos de datos, rangos, campos obligatorios).
   - Transforma los modelos ORM en representaciones JSON estructuradas para el frontend.

4. **Permission & Security Layer (`permissions.py`):**
   - Implementa clases basadas en `BasePermission` de DRF para verificar el rol del usuario autenticado (`Administrador`, `Propietario`, `Personal de Ventas`, `Personal de Producción`).

5. **View / Controller Layer (`views.py`):**
   - Recibe la petición HTTP, invoca los permisos correspondientes, llama al serializador para validación, ejecuta el servicio y retorna la respuesta HTTP con el código de estado adecuado (`200 OK`, `201 Created`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`).

6. **Routing Layer (`urls.py`):**
   - Define los endpoints REST limpios siguiendo las convenciones de nombres RESTful.

---

## 5. Guía Paso a Paso para Implementar un Nuevo Caso de Uso (CU)

Cuando un desarrollador vaya a implementar un nuevo Caso de Uso (por ejemplo, del Ciclo 1 o ciclos posteriores), debe seguir estrictamente este flujo de trabajo:

```
[ Paso 1: Revisar CU y Permisos ] 
       │
       ▼
[ Paso 2: Definir/Ajustar Modelos & Migraciones ]
       │
       ▼
[ Paso 3: Implementar Lógica de Negocio en services.py ]
       │
       ▼
[ Paso 4: Crear Serializadores en serializers.py ]
       │
       ▼
[ Paso 5: Implementar Vistas y Permisos RBAC en views.py ]
       │
       ▼
[ Paso 6: Configurar Rutas en urls.py ]
       │
       ▼
[ Paso 7: Registrar Acción en Bitácora ]
       │
       ▼
[ Paso 8: Integrar con Frontend (React) ]
       │
       ▼
[ Paso 9: Pruebas Unitarias y de Integración ]
```

### Detalle de cada paso:

### Paso 1: Revisar la Ficha del CU y Actores Permitidos
- Consultar [`docs/PROJECT_CONTEXT.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/PROJECT_CONTEXT.md) y [`backend/apps/PACKAGE_CU_MAP.md`](file:///c:/Users/PERSONAL/panaderia-SI1/backend/apps/PACKAGE_CU_MAP.md) para identificar el número de CU, su objetivo, el paquete al que pertenece y los actores autorizados (`Administrador`, `Propietario`, `Personal De Ventas`, `Personal De Producción`).

### Paso 2: Modelos y Migraciones (`models.py`)
- Ubicar la tabla correspondiente en [`Database_Panaderia_Santiago_FINAL.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/Database_Panaderia_Santiago_FINAL.sql).
- Si el modelo aún no existe en el `models.py` de la app respectiva, definirlo respetando tipos y `db_table`.
- Ejecutar migraciones:
  ```bash
  python manage.py makemigrations <nombre_app>
  python manage.py migrate
  ```

### Paso 3: Lógica de Negocio (`services.py`)
- Crear funciones de servicio puras y testeables.
- Si la operación involucra más de una tabla o cálculos de inventario/costos, envolver en `@transaction.atomic`.
- *Ejemplo:*
  ```python
  from django.db import transaction
  from apps.usuarios_seguridad.services import registrar_bitacora

  @transaction.atomic
  def crear_producto_servicio(datos_producto, usuario):
      producto = Producto.objects.create(**datos_producto)
      registrar_bitacora(
          usuario=usuario,
          accion="CREACION",
          tabla="producto",
          descripcion=f"Se creó el producto {producto.nombre} con precio {producto.precio_venta}"
      )
      return producto
  ```

### Paso 4: Serializadores (`serializers.py`)
- Definir un `ModelSerializer` o `Serializer` para validar los campos recibidos.
- Agregar validaciones personalizadas (`validate_<campo>` o `validate`) si existen reglas de negocio (ej. precios no negativos, nombres únicos).

### Paso 5: Vistas y Control de Acceso (`views.py` y `permissions.py`)
- Crear la vista (`APIView` o `ModelViewSet`).
- Asignar la clase de autenticación y la clase de permiso correspondiente al rol del actor.

### Paso 6: Rutas (`urls.py`)
- Registrar la ruta en el `urls.py` de la app y verificar que la app esté incluida en `backend/config/urls.py` con el prefijo `/api/`.

### Paso 7: Auditoría y Bitácora (CU 26)
- Toda operación de modificación, inserción o eliminación de datos de negocio debe emitir un registro hacia la tabla `bitacora` indicando `id_usuario`, `accion`, `tabla_afectada`, `descripcion` y `fecha_hora`.

### Paso 8: Integración Frontend (React)
- Crear/actualizar el servicio de API en `frontend/src/services/` con tipado TypeScript.
- Crear la pantalla o componente en `frontend/src/pages/` o `frontend/src/components/`.
- Gestionar estados de carga (`loading`), errores (`error`) y retroalimentación al usuario (toasts/alertas).
- Restringir la visualización de botones o rutas en la interfaz según el rol del usuario logueado.

### Paso 9: Pruebas y Validación
- Crear pruebas automatizadas en `tests.py` para validar:
  - Respuesta exitosa con datos válidos (`200`/`201`).
  - Rechazo de acceso a usuarios sin el rol permitido (`403`).
  - Manejo de datos inválidos (`400`).
  - Registro efectivo en la bitácora.
