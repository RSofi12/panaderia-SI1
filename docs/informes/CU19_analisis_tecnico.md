# CU19 — Consultar historial de precios: análisis previo

> **Actualización 2026-10-22:** el usuario resolvió el alcance y autorizó la implementación: solo precios de venta de productos, Propietario más gestionar_productos, sin modelos ni migraciones nuevos. El texto siguiente se conserva como registro del análisis previo. Resultado actual: [CU19_implementacion_tecnica.md](CU19_implementacion_tecnica.md).

- **Fecha:** 2026-10-22, America/La_Paz.
- **Estado:** preparación y análisis. No se implementó CU19.
- **Repositorio:** https://github.com/RSofi12/panaderia-SI1.git
- **Copia de trabajo:** `C:\Users\vacaa\Downloads\panaderia-SI1-main-actualizado`.
- **Rama:** `feature/cu19-historial-precios`.
- **Base verificada:** `7a5031baaeb4b4ad109eaf22218584ddfcfdf3ff`, último `origin/main` obtenido por fetch en esta etapa.
- **Fecha del commit:** 2026-10-15 03:40:51 -04:00; asunto: permitir dominio de Vercel en CORS.

## 1. Preparación de Git y conservación del entorno

Se comprobaron `git status`, rama, remotos y stash antes de cambiar archivos. Se ejecutó `git fetch origin --prune`.

La copia antigua `C:\Users\vacaa\Downloads\panaderia-SI1-main copia\panaderia-SI1` mantiene la rama CU09, sus cambios de documentación, archivos personales y el stash `Respaldo local antes de actualizar main`. No se cambió de rama allí, ni se aplicó o eliminó el stash. Las dos carpetas encontradas con nombre `panaderia-SI1-main` no contienen `.git`.

La copia preparada anteriormente estaba limpia y en `main`. Se actualizó mediante fast-forward de `3e79def` a `7a5031b`; el único cambio entrante respecto de esa copia fue la configuración CORS versionada del equipo. Se comprobó que la rama CU19 no existiera y se creó directamente desde `origin/main`. HEAD coincide con la base indicada; no se configuró upstream de publicación.

Los archivos `.env`, el entorno virtual, dependencias y scripts locales se conservaron. No se mostraron secretos, ni se inició la aplicación, ni se realizaron conexiones a PostgreSQL, migraciones, seeders o pruebas contra bases de datos. No hubo commits, pushes ni cambios del remoto. Los únicos cambios de archivos de esta etapa son documentación de análisis y continuidad.

## 2. Alcance encontrado y discrepancia que requiere decisión

El repositorio define CU19 como consulta del **precio de venta de productos**:

| Evidencia versionada | Definición encontrada |
|---|---|
| `backend/apps/PACKAGE_CU_MAP.md:69–71` | CU19 en `apps.productos_inventario.productos`, cambios históricos del precio de venta de un producto, actor Propietario |
| `docs/ai/IMPLEMENTATION_PHASES.md:251` | Historial de precios de productos, Ciclo 3, Propietario |
| `docs/ai/DECISIONS_LOG.md:476–480` | `productos/` contiene CU05 y CU19, llamado Historial precio venta |
| `docs/ai/ARCHITECTURE.md:88–93` | CU19 junto al modelo `HistorialPrecioProducto` |
| `docs/ai/CURRENT_STATE.md:62` | CU19 pendiente de implementación |
| `backend/apps/PACKAGE_CU_MAP.md:83–85` | CU07 actualiza otro historial: precios de insumos |

La solicitud actual plantea materias primas, compras y proveedores. Esa necesidad es válida, pero representa un alcance diferente al CU19 documentado. El perfil del proyecto también menciona comparar compras y precios de insumos (`docs/informes/Perfil Proyecto SI-1 grupo 3.md:104–106`), sin asignarlo expresamente a CU19.

No se encontró una ficha detallada versionada de CU19 que imponga filtros, gráfica, indicadores, exportación o periodos concretos. Prioridad baja y riesgo bajo proceden de la solicitud del usuario. Los filtros y contratos descritos abajo son propuestas de diseño.

**Recomendación:** revisar esta diferencia con el equipo antes de implementar. La propuesta principal mantiene el CU19 documentado de productos; la sección 7 explica cómo atender insumos si ese es el objetivo confirmado. No ampliar silenciosamente a ambos ni mezclar sus datos.

## 3. Datos reales existentes

La verificación corresponde al código y las migraciones versionadas. No se inspeccionaron registros ni el esquema físico de una base durante esta etapa.

| Modelo y tabla | Campos reales relevantes | Relaciones y significado |
|---|---|---|
| `HistorialPrecioProducto`, `historial_precio_producto` | `id_historial`, `id_producto`, `precio`, `fecha_inicio` | `id_producto` FK PROTECT a Producto, inversa `historial_precios`. Precio de venta registrado; Decimal(10,2), fecha/hora con `timezone.now` |
| `HistorialPrecioMateriaPrima`, `historial_precio_materia_prima` | `id_historial`, `id_materia_prima`, `precio`, `fecha_inicio` | FK PROTECT a MateriaPrima, inversa `historial_precios`. Precio de compra registrado; Decimal(10,2), fecha/hora con `timezone.now` |
| `DetalleCompra`, `detalle_compra` | `id_detalle_compra`, `id_compra`, `id_materia_prima`, `cantidad`, `precio_unitario`, `subtotal` | FKs a Compra y MateriaPrima; precio realmente registrado en la línea; cantidad Decimal(10,3), importes Decimal(10,2) |
| `Compra`, `compra` | `id_compra`, `id_proveedor`, `id_usuario`, `fecha_hora`, `total` | Cabecera que identifica proveedor, usuario y fecha de la compra |
| `Proveedor`, `proveedor` | `id_proveedor`, `nombre`, `telefono`, `direccion`, `fecha_registro`, `activo` | Catálogo con baja lógica; nombre actual del proveedor |

Ubicaciones: `backend/apps/productos_inventario/productos/models.py:77`, `backend/apps/productos_inventario/materia_prima/models.py:64`, `backend/apps/compras/compra_materia_prima/models.py:6,44`, `backend/apps/compras/proveedores/models.py:6`.

Ninguno de los dos historiales de precio tiene FK a compra, proveedor o usuario, ni campo `fecha_fin`. Sus nombres se obtienen del catálogo actual: no son instantáneas históricas de nombres o unidades. Tampoco existe una relación de proveedor que corresponda al precio de venta de un producto fabricado por la panadería.

### Escritores que ya generan el historial

- CU05: `productos/views.py:53` crea una entrada al dar de alta un producto; `:95` agrega otra cuando cambia realmente `precio_venta`. Una edición sin cambio de precio no crea otra entrada. El historial corresponde a precio de venta, no a `precio_sugerido` ni a costo de producción.
- `productos/management/commands/seed_productos.py:71` también crea el precio inicial de productos. Ese origen no equivale a una compra ni se ejecutó durante este análisis.
- CU07: `compras/compra_materia_prima/services/registrar_compra.py:98` registra la operación atómicamente. En `:175` guarda DetalleCompra y en `:187` inserta HistorialPrecioMateriaPrima **en cada compra**, aunque el precio sea igual al anterior. Actualiza inventario, movimientos y bitácora.
- `seed_materias_primas.py:56` también introduce precios iniciales sin compra ni proveedor. No se ejecutó en esta etapa.
- CU08 gestiona el catálogo, inventario inicial y estado; no expone edición de históricos.
- `produccion/services.py:63` utiliza el último precio histórico de insumos para calcular costos. No calcula un promedio ponderado. CU19 no debe cambiar esa regla ni el orden global del historial de insumos.

**Relación segura con proveedor:** `DetalleCompra.id_compra → Compra.id_proveedor → Proveedor`. Compra.fecha_hora y el historial.fecha_inicio reciben valores independientes. Una coincidencia de fecha y precio no identifica la compra: no debe usarse para atribuir proveedores. Tampoco es seguro suponer correspondencia por posición o ID entre las tablas.

## 4. Implementación parcial y reutilización

Los modelos históricos, las tablas y sus escritores ya existen. No hay endpoint REST de listado de ninguno de estos historiales, ni pantalla, ruta, servicio HTTP o tipo TypeScript específico de CU19. Django Admin registra los modelos; ese acceso técnico no sustituye la pantalla del Propietario.

Endpoints existentes útiles:

| Endpoint real | Utilidad y límite |
|---|---|
| `GET /api/productos/` y `/api/productos/<id>/` | Catálogo/selector de productos; no devuelve el historial |
| `GET /api/categorias-producto/` | Categorías, si posteriormente se justifica ese filtro |
| `GET /api/materias-primas/` | Catálogo de insumos; muestra `precio_ultima_compra`, no la serie completa |
| `GET /api/compras/` | Cabeceras con proveedor, filtros de proveedor/fecha/búsqueda; no incluye líneas para construir todo el historial de precios |
| `GET /api/compras/<id>/` | Compra con fecha, proveedor y líneas/precios; útil para abrir la procedencia de una fila de compras |

No conviene descargar todas las compras y solicitar cada detalle desde React para construir la tabla: produciría múltiples peticiones, duplicaría reglas de filtrado y trasladaría una consulta de datos al cliente.

Se conservan las capas actuales: selector ORM para lectura, serializer para contrato/validación, permiso local, vista de consulta y rutas. No hacen falta un servicio de escritura, una tabla nueva, triggers ni recalcular inventarios.

## 5. Seguridad propuesta

El actor encontrado es Propietario. Debe decidirse expresamente si Administrador tendrá acceso secundario; `is_superuser` por sí solo no debe sustituir esa decisión.

- `TienePermiso`, en `usuarios_seguridad/users/permissions.py:25`, consulta `Usuario.get_permisos_nombres()`. No concede bypass automático por Administrador o superusuario.
- El permiso **existente** `gestionar_productos` está en Administrador y Propietario según el seed actual.
- `PuedeGestionarProductos` permite GET a cualquier usuario autenticado (`productos/permissions.py:15–16`): reutilizarlo sin otra restricción expondría CU19.
- `gestionar_inventario` y `generar_reportes` también están asignados a Ventas; no son suficientes para limitar la consulta al actor solicitado.
- No existe `consultar_historial_precios` en el catálogo definido por el seed. Ese nombre sería un permiso **nuevo propuesto**.

**Opción mínima sin modificar datos RBAC:** combinar autenticación, `TienePermiso('gestionar_productos')` y una comprobación local de rol Propietario, solo en la nueva vista. Instanciar TienePermiso mediante `get_permissions()`, siguiendo el patrón existente de CU09. Replicar permiso y rol en `ProtectedRoute`, sin cambiar la clase global del catálogo.

**Opción de autorización granular:** introducir posteriormente `consultar_historial_precios` y asignarlo al rol acordado. Requiere aprobación para crear/asignar esos datos y plan de despliegue; no un ID fijo ni ejecutar el seeder general que restablece contraseñas. Un nuevo permiso es un cambio de datos RBAC, no necesariamente un cambio de esquema.

Si se confirma una consulta de compras, `registrar_compras` es otro permiso existente del Propietario que podría combinarse con su rol. Elegirlo acopla consulta y registro; un permiso dedicado separaría ambas capacidades. Ninguna asignación se realizó durante este análisis.

## 6. Propuesta principal: precios de venta de productos

Todos los nombres y rutas de esta sección son **propuestas pendientes de implementación**.

`GET /api/productos/historial-precios/?id_producto=...&fecha_desde=YYYY-MM-DD&fecha_hasta=YYYY-MM-DD&page=...`

- Fuente: HistorialPrecioProducto existente.
- Consulta: `select_related('id_producto')`, con categoría solo si el contrato realmente la usa; ordenar por `-fecha_inicio, -id_historial` para resolver empates sin cambiar Meta del modelo.
- Filtros iniciales opcionales: producto y fechas. Validar ID entero positivo, fechas reales y rango coherente mediante serializer de parámetros. Fechas por día completo en `America/La_Paz`, con límites compatibles con USE_TZ.
- No excluir productos inactivos: su historial sigue siendo relevante. El selector debe permitir encontrarlos y mostrar su estado.
- Contrato propuesto: ID histórico, ID/nombre actual del producto, precio como cadena decimal y fecha ISO con zona horaria. No añadir proveedor porque no está relacionado con este dato.
- Paginación limitada a la nueva vista (`count`, `next`, `previous`, `results`), sin cambiar las respuestas actuales de CU05, CU07 o CU08. ListAPIView permite usar paginación explícita; las APIView existentes no la aplican por declarar un ajuste global.
- Respuestas esperadas: 200 con lista paginada o vacía, 400 para filtros inválidos, 401 sin sesión, 403 sin rol/permiso, 405 para escrituras de un usuario autorizado. GET/HEAD/OPTIONS no registran compras ni modifican precios o stock.
- No fabricar registros si existe producto sin historial. El precio actual del catálogo no debe presentarse como un precio antiguo inexistente.
- No se necesita migración de esquema. Los modelos no declaran un índice compuesto de entidad y fecha; medir volumen y consultas antes de proponer uno, con autorización futura si se requiere.

**Interfaz mínima:** tabla de producto, fecha/hora y precio Bs; filtros de producto/desde/hasta, paginación, limpiar y reintentar. Distinguir cargando, historial vacío, filtros sin coincidencias, fallo de carga y acceso denegado.

Una tabla es suficiente para prioridad/riesgo bajos. No hay librería de gráficas instalada ni requisito verificado de gráfica. Como mejora futura, una serie de un solo producto puede facilitar tendencias, pero necesita el rango completo y no solamente una página de datos. No sumar precios de distintos productos ni mostrar un promedio general de entidades/unidades diferentes. Indicadores como último precio o variación solo se justificarían para una entidad seleccionada y con reglas de comparación acordadas.

Debe decidirse si el rango significa solo cambios ocurridos dentro del intervalo o si también se mostrará, claramente distinguido, el precio que ya estaba vigente al inicio. La propuesta mínima lista los cambios del intervalo y no añade registros sintéticos.

## 7. Alternativa si el equipo confirma materias primas y proveedores

Hay dos consultas distintas posibles; no deben presentarse como equivalentes:

1. **Todos los precios históricos de insumos:** endpoint propuesto `GET /api/materias-primas/historial-precios/`, basado en HistorialPrecioMateriaPrima. Incluye precios iniciales sin compra. Mostrar proveedor como no registrado, porque no existe FK que identifique su origen. Filtros de materia prima y fechas.
2. **Precios pagados en compras con proveedor:** endpoint propuesto `GET /api/compras/historial-precios/`, basado en DetalleCompra, con `select_related('id_materia_prima', 'id_compra', 'id_compra__id_proveedor')`. Filtros de materia prima, proveedor y fechas de Compra.fecha_hora; orden descendente de fecha e ID de detalle. Devuelve ID de detalle/compra, materia, unidad actual, fecha, precio unitario y proveedor reales. No incluye precios iniciales sin compra. Reutiliza CU07 sin duplicar filas, sin nueva tabla y sin cambiar su registro.

La segunda es la opción de menor impacto si el objetivo prioritario es comparar compras y proveedores. La consulta se ubicaría en el dominio de compras que posee sus detalles, con acceso desde Productos e Inventario si el equipo mantiene esa navegación. Antes de llamarla CU19 deben acordarse su trazabilidad y la actualización del mapa de casos de uso; no se crea una sexta app.

No se recomienda unir ambos conjuntos emparejando fecha/precio, ni duplicar cada compra como dos eventos en una tabla combinada. Si el equipo exige que cada entrada de HistorialPrecioMateriaPrima tenga proveedor verificable, hará falta diseñar una FK de procedencia futura y el tratamiento de registros antiguos: cambio de esquema y de CU07 sujeto a aprobación específica. No es necesario para la consulta mínima sobre DetalleCompra.

Los precios repetidos siguen siendo compras distintas; no deduplicarlos si se presenta historial de compras. Los catálogos y proveedores inactivos deben poder conservar su presencia histórica. La unidad y el nombre mostrados son actuales; la base no conserva sus valores antiguos.

## 8. Propuesta frontend y archivos afectados

CU19 pertenece a Productos e Inventario. `ReportesPage` corresponde a CU21–CU25 del Ciclo 4; no usarlo como ubicación por defecto. La pestaña actual `historial` de ProductosPage es CU11, historial de producción, y debe conservar su significado.

Ruta **propuesta:** `/dashboard/productos/historial-precios`, con permiso elegido y `requiredRole="Propietario"` mientras no se acuerde otro actor. Acceso mediante enlace autorizado en ProductosPage; mantener todas las rutas y pestañas actuales.

Reutilización verificada:

- `frontend/src/services/api.ts`: Axios, VITE_API_URL, JWT y refresh; sin modificar configuración.
- `frontend/src/routes/ProtectedRoute.tsx`: combina permiso y rol, no necesita un guard global nuevo.
- `frontend/src/services/productoService.ts` y `types/producto.ts`: catálogo/selector de productos; no filtrar solo activos para una consulta histórica.
- `frontend/src/apps/dashboard/productos/precios.ts`: `formatearBs` para presentación; no usar flotantes para cálculos monetarios del dominio.
- Patrones de filtros y tabla de CU11, cancelación/carga de `useAlertasBajoStock` y normalización de `services/erroresApi.ts`. Usarlos como referencia sin modificar componentes de esos casos de uso ni trasladar sus errores de lint al código nuevo.
- No se encontró una tabla/paginación genérica compartida; una tabla local es suficiente. No crear un sistema de componentes genérico sin necesidad.

### Inventario de archivos propuestos para el alcance documentado

| Acción futura | Archivo | Responsabilidad |
|---|---|---|
| Crear | `backend/apps/productos_inventario/productos/selectors.py` | Consulta filtrada y ordenada de historial existente |
| Modificar | `backend/apps/productos_inventario/productos/serializers.py` | Respuesta de lectura y validación de filtros |
| Modificar | `backend/apps/productos_inventario/productos/permissions.py` | Regla local CU19, sin cambiar permisos del catálogo |
| Modificar | `backend/apps/productos_inventario/productos/views.py` | Vista GET con autorización y paginación propia |
| Modificar | `backend/apps/productos_inventario/productos/urls.py` | Ruta estática nueva, conservando recetas y CRUD |
| Modificar | `backend/apps/productos_inventario/productos/tests.py` | Casos de consulta y regresión |
| Crear | `frontend/src/apps/dashboard/productos/historial-precios/HistorialPreciosPage.tsx` | Filtros, tabla, paginación y estados |
| Crear | `frontend/src/apps/dashboard/productos/historial-precios/index.ts` | Exportación de pantalla según arquitectura |
| Crear | `frontend/src/services/historialPreciosService.ts` | GET tipado, filtros y AbortSignal |
| Crear | `frontend/src/types/historialPrecio.ts` | Filas, filtros y respuesta paginada; precio string y fecha ISO |
| Modificar | `frontend/src/routes/AppRoutes.tsx` | Ruta protegida CU19 |
| Modificar | `frontend/src/apps/dashboard/productos/ProductosPage.tsx` | Enlace visible según rol y permiso |
| Condicional | `frontend/src/apps/dashboard/navigation.ts` | Solo si un permiso nuevo debe habilitar entrada al módulo |

No se ha creado ninguno de esos archivos de implementación en esta etapa. Un hook local adicional solo se justificaría si la carga/filtros lo necesitan. Si se elige insumos, los selectores/vistas irán en materia_prima o compra_materia_prima según la fuente acordada, no se reutilizará el nombre HistorialPrecioProducto para otro concepto.

Con un permiso granular nuevo, revisar también `navigation.ts` y la admisión del módulo en `ProductosPage.tsx:79–100`: sus filtros actuales solo conocen permisos existentes. Para proveedores, el endpoint actual requiere gestionar_proveedores o registrar_compras; no otorgar capacidades de escritura solo para llenar un selector de consulta. Un contrato de metadatos autorizado para CU19 es una alternativa si hay actores con permisos reducidos.

## 9. Pruebas necesarias tras autorizar la implementación

### Backend, en base aislada autorizada

1. Propietario con permiso permitido; propietario sin permiso, usuarios sin rol, otros roles con ese mismo permiso y anónimos rechazados. Administrador/superusuario conforme política expresamente acordada.
2. Historial vacío, un registro, varios productos y múltiples precios; ceros y decimales exactos; empates de fecha con orden determinista.
3. Filtros independientes/combinados, IDs inválidos, fechas inexistentes, rango invertido, extremos inclusivos del día en Bolivia y paginación.
4. Productos/materias/proveedores inactivos conservan su historial; registros sin historial no se convierten en entradas inventadas.
5. Escrituras rechazadas; comparar antes/después para demostrar que GET no cambia compras, detalles, precios, historiales, inventarios ni movimientos.
6. Consultas acotadas sin N+1 mediante relaciones precargadas.
7. Regresión CU05: alta genera historial; cambio de precio genera una entrada; edición sin cambio no genera otra; baja lógica conserva datos.
8. Regresión CU07: compra, detalle, stock, historial, advertencia de variación de al menos 50% y bitácora continúan funcionando; regresión CU08/CU09 en catálogos y alertas.
9. Si hay insumos: precios repetidos, varios proveedores, precios iniciales sin compra y prohibición de atribuir proveedor por coincidencias.

Pruebas existentes revisadas, no ejecutadas: `productos/tests.py:66` (alta con historial), `compras/compra_materia_prima/tests.py:90,171` (histórico/variación), `materia_prima/tests.py:49` (último precio). No hay cobertura específica de consulta CU19.

### Frontend

Build y lint de los archivos afectados; navegador con API aislada para acceso directo, menú/enlace, sesión cargando/expirada, filtros, paginación, formato de fecha/precio, error/reintento, vacío y cancelación de respuestas obsoletas. Comprobar que las rutas anteriores de CU07/CU08/CU09/CU11 sigan abiertas para sus roles.

`frontend/package.json` no tiene runner de pruebas ni configuración Vitest/Jest/Playwright. Añadir pruebas unitarias automatizadas requerirá acordar esa dependencia; no presentar herramientas inexistentes como comprobaciones ya realizadas. No se ejecutaron build, lint ni pruebas funcionales en esta etapa de análisis.

## 10. Riesgos y límites de dependencia

| Dependencia/riesgo | Tratamiento propuesto |
|---|---|
| Confundir precios de venta y compra | Resolver alcance y nombrar explícitamente cada fuente |
| Reutilizar permiso GET demasiado amplio | Doble control de rol y permiso solo en CU19 |
| Atribuir proveedor inexistente al historial | Usar relaciones de DetalleCompra o mostrar ausencia de procedencia |
| Alterar costos de producción al tocar el historial MP | Conservar escrituras/orden y cálculo de último precio de CU07/CU10 |
| Perder historial de catálogos inactivos | No aplicar por defecto filtros de activo usados en formularios de compra |
| Cambiar paginación o rutas existentes | Contrato y vista nuevos; no ajustes globales |
| Recrear tablas históricas por la modularización | Reutilizar modelos existentes y sus migraciones SeparateDatabaseAndState; no editar migraciones aplicadas |
| Historia incompleta o nombres/unidades cambiados | Mostrar lo realmente registrado y aclarar nombres actuales; no reconstruir pasado sin datos |
| Filtrar fechas y confundir precio vigente | Acordar semántica del intervalo y zona horaria |
| Reutilizar seed general para un permiso nuevo | Evitar IDs fijos/restablecimientos; aprobación y aprovisionamiento específico futuro |

Para el CU19 documentado, CU05 es el escritor del que se depende directamente. CU07/CU08/CU09 no necesitan cambios funcionales; se verifican como regresiones. Para la variante de compras, CU07 es la fuente y CU08 suministra catálogo; CU09 sigue independiente. Ningún caso requiere modificar compras o inventario durante la consulta.

## 11. Decisiones que requiere el equipo

1. **Alcance:** precios de venta de productos, precios pagados por materias primas o ambos como consultas separadas. Si cambia el alcance oficial, actualizar mapa/plan/decisiones de trazabilidad antes de implementar.
2. **Actores:** Propietario exclusivamente o también Administrador. No asumir una excepción automática para superusuario.
3. **Permiso:** reutilizar gestionar_productos (o registrar_compras para compras) con rol explícito, o crear un permiso de consulta independiente.
4. **Fechas:** cambios del intervalo o también precio vigente al comienzo; mantener fecha/hora y zona local coherentes.
5. **Si se eligen insumos:** historial completo, incluidos precios iniciales sin proveedor, frente a historial de compras trazables por proveedor. ¿Se exige enlace de procedencia para cada entrada? Esto último puede cambiar el esquema y CU07.

Recomendaciones de menor alcance: incluir inactivos, tabla paginada sin gráfica ni exportación en la primera entrega, nombres/unidades actuales claramente identificados y ninguna escritura al consultar. Gráfica, indicadores adicionales y nuevos permisos quedan como decisiones explícitas, no requisitos inventados.

La rama y este informe están preparados para revisión. La implementación completa sigue pendiente de autorización del usuario.
