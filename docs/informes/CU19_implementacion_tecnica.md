# CU19 — Entrega técnica de implementación

- **Fecha:** 2026-10-22 (America/La_Paz).
- **Ciclo:** 3.
- **Rama:** `feature/cu19-historial-precios`.
- **Base/HEAD:** `7a5031baaeb4b4ad109eaf22218584ddfcfdf3ff`; cambios de trabajo sin commit.
- **Carpeta:** `C:\Users\vacaa\Downloads\panaderia-SI1-main-actualizado`.
- **Alcance aprobado:** consulta de precios de venta de productos, solo Propietario con gestionar_productos. Sin compras, proveedores, materias primas, modelos o migraciones nuevas.

## Resultado

CU19 reutiliza HistorialPrecioProducto y expone una consulta paginada de solo lectura. La pantalla incorpora producto, precio en bolivianos, fecha de inicio en hora de Bolivia, filtros, limpiar, navegación de páginas, carga, errores, reintento y mensajes distintos para historial vacío o filtros sin coincidencias.

No se cambian los escritores del historial de CU05, CU07, las reglas de CU08/CU09 ni la pestaña `historial` de CU11. Se conserva la configuración local y el historial documental de la etapa anterior.

## Backend y contrato definitivo

**Endpoint:** `GET /api/productos/historial-precios/`.

**Nombre Django:** `productos_inventario:historial_precios`.

Parámetros opcionales:

| Parámetro | Significado |
|---|---|
| `id_producto` | ID entero positivo dentro del rango BigInt |
| `fecha_desde` | Fecha ISO; incluir cambios desde las 00:00 del día en America/La_Paz |
| `fecha_hasta` | Fecha ISO; incluir cambios hasta las 23:59:59.999999 del día en America/La_Paz |
| `page` | Página, según PageNumberPagination existente |

Respuesta paginada: `count`, `next`, `previous`, `results`. Cada fila incluye `id_historial`, `id_producto`, `producto_nombre`, `producto_activo`, `precio` como string decimal de dos posiciones y `fecha_inicio` ISO. El precio no se calcula mediante float.

- Tamaño de página: 10, según la configuración DRF actual.
- Orden: fecha de inicio descendente y, en empate, ID histórico descendente.
- Se incluyen productos inactivos y se muestran nombres actuales del catálogo; no se fabrican instantáneas del pasado ni registros faltantes.
- Fechas e IDs inválidos, parámetros presentes vacíos y rangos invertidos: HTTP 400.
- Lista válida sin registros: HTTP 200 con count=0 y results vacío.
- Anónimo: 401. Rol o permiso insuficientes: 403. Escrituras de un usuario autorizado: 405. Página inválida: comportamiento 404 de DRF.

El selector usa select_related para evitar consultas por producto. La conversión de query_params a diccionario plano conserva valores vacíos explícitos para que se validen y no se interpreten como campos opcionales omitidos de un formulario HTML.

La autorización combina IsAuthenticated, TienePermiso('gestionar_productos') y EsPropietarioCU19. No hay excepción por Administrador o is_superuser. El permiso GET amplio del catálogo CU05 permanece intacto.

## Frontend y acceso

**Ruta:** `/dashboard/productos/historial-precios`.

El enlace «Historial de precios» aparece en Productos únicamente cuando coinciden rol Propietario y permiso gestionar_productos. ProtectedRoute vuelve a verificar ambos requisitos al entrar por URL directa.

- Axios y JWT utilizan el cliente compartido; no se cambian URLs, interceptores o archivos de entorno.
- Catálogo e historial se solicitan de forma independiente. Un fallo del catálogo no oculta los resultados por fechas; permite reintentar el selector.
- El selector incluye productos inactivos y los identifica. La tabla marca también su estado.
- Aplicar o limpiar filtros vuelve a página 1. El historial cancela solicitudes anteriores y descarta respuestas obsoletas.
- La tabla reutiliza formatearBs; la fecha se presenta explícitamente en America/La_Paz.
- Se mantienen etiquetas nativas, encabezados, estados accesibles, navegación por teclado, foco visible y desplazamiento horizontal local de tabla en pantallas estrechas.
- No hay gráficas, bibliotecas nuevas, funciones de edición, exportación ni indicadores fuera del alcance.

Para verlo localmente: iniciar sesión como **Propietario**, abrir Productos y seleccionar Historial de precios. La cuenta Administrador está excluida por la decisión funcional aprobada.

## Pruebas y comprobaciones ejecutadas

Se creó `test_panaderia_cu19_20261022` después de comprobar que no existía. El runner aplicó las migraciones existentes solamente en esa base temporal. Se comprobó su OID antes de operar y se conservó durante las verificaciones de navegador. Después se cerraron los servicios aislados y se eliminó únicamente esa base, verificando identidad y ausencia de conexiones. No se modificaron bases anteriores ni Render.

Los scripts locales de aislamiento, logs, capturas y configuración de pruebas viven en `.local/`, ignorados por Git. No deben incorporarse al commit.

| Verificación | Resultado |
|---|---|
| manage.py check, configuración aislada | Sin problemas |
| makemigrations --check --dry-run | No changes detected; no archivos de migración nuevos |
| migrate --check, base temporal | Código 0; migraciones existentes coherentes |
| Productos: 28 CU19 + 5 CU05 | Aprobadas |
| CU07 compra_materia_prima | 8 aprobadas |
| CU08/CU09 materia_prima | 20 aprobadas |
| Total backend dirigido | **61 pruebas aprobadas**, ejecución final 2.508 s |
| npm run build | Aprobado: TypeScript y Vite |
| ESLint de los seis archivos frontend modificados/nuevos | Aprobado, sin advertencias |
| npm run lint global | Falla por **14 errores y 1 advertencia preexistentes** |
| Chrome con API y PostgreSQL temporales | **61 comprobaciones principales + 5 adicionales aprobadas** |
| Revisión independiente de código | Sin hallazgos críticos/importantes/menores abiertos |

La primera ejecución de backend detectó tres subcasos fallidos por parámetros vacíos ignorados por QueryDict. Se corrigió la vista; no se eliminaron ni debilitaron pruebas. La ejecución posterior aprobó los 61 casos.

### Cobertura de CU19

Propietario autorizado, otros roles aunque tengan permiso, Administrador/superusuario de otro rol, propietario sin permiso, sin rol y anónimo; vacío, filtros independientes/combinados, rango invertido y fechas imposibles, IDs inválidos o fuera de BigInt, fronteras de día y zona activa distinta; orden por fecha/ID, paginación, precisión decimal y productos inactivos. Se compararon los estados completos de productos, precios, compras, inventarios, movimientos y bitácora antes/después de GET, además de verificar ausencia de SQL de escritura y evitar N+1.

### Regresiones

- CU05: alta, catálogo, baja lógica y dos pruebas nuevas de edición con/sin cambio de precio; se mantiene su respuesta anterior sin paginación.
- CU07: compra, detalles, actualización de stock/historial y advertencias/auditoría existentes.
- CU08/CU09: catálogo y permisos, alertas, igualdad al mínimo, insumos sin inventario y ausencia de escrituras al consultar.
- Rutas: historial nuevo, catálogo, recetas, detalle/toggle de productos y pestaña CU11 preservados.

### Comandos reproducibles de esta ejecución

Desde raíz se usó el wrapper **local e ignorado** para fijar la conexión exclusivamente a la base temporal creada por esta sesión:

```powershell
.\.venv\Scripts\python.exe .\.local\cu19_test_environment.py manage check
.\.venv\Scripts\python.exe .\.local\cu19_test_environment.py manage makemigrations --check --dry-run
.\.venv\Scripts\python.exe .\.local\cu19_test_environment.py manage test apps.productos_inventario.productos apps.compras.compra_materia_prima apps.productos_inventario.materia_prima --keepdb --verbosity 2
.\.venv\Scripts\python.exe .\.local\cu19_test_environment.py manage migrate --check
```

La base ya fue eliminada tras completar las pruebas: para repetir se debe preparar otra base temporal comprobada, no apuntar a bases existentes ni ejecutar el wrapper de creación sobre un nombre ocupado. El código de CU19 no depende del wrapper local.

En frontend se ejecutaron npm run build, npm run lint y:

```powershell
npx eslint src/types/historialPrecio.ts src/services/historialPreciosService.ts src/apps/dashboard/productos/historial-precios/HistorialPreciosPage.tsx src/apps/dashboard/productos/historial-precios/useHistorialPrecios.ts src/routes/AppRoutes.tsx src/apps/dashboard/productos/ProductosPage.tsx
```

### Navegador: alcance real y simulaciones

Chrome utilizó frontend localhost:5174 y API 127.0.0.1:8001 con datos controlados en PostgreSQL temporal: cuatro actores, tres productos y 27 entradas históricas. Se verificaron permisos/ruta/enlace, formato Bs y Bolivia, orden, filtros, paginación, limpieza, producto inactivo y producto real sin historial. El intervalo 10–11 de octubre devolvió cuatro filas, incluidos los dos extremos locales del día. Se abrieron las pantallas anteriores CU05/CU07/CU08/CU09/CU11 con API 200, sin registrar operaciones de negocio.

Administrador, Ventas y Producción obtuvieron 403 reales de la API, enlace oculto y ruta bloqueada. Anónimo volvió al login. La guarda UI de Propietario sin permiso se comprobó con una simulación explícita del payload de autenticación; el rechazo real del backend sin permiso está cubierto por Django. Vacío general y error 503 se simularon en la API del navegador; reintentar recuperó datos reales. Estas simulaciones no se presentan como cambios de datos ni pruebas de servidor.

Se inspeccionó la interfaz a 1440/390/320 px, sin desbordamiento global ni excepciones JavaScript. No hay runner unitario frontend configurado y no se añadió uno. Los scripts CDP y evidencias no forman una nueva suite versionada del proyecto.

Evidencias locales: `.local/cu19-backend-tests-final.log`, `.local/cu19-global-lint.log`, `.local/cu19-browser-report.json`, `.local/cu19-browser-extra-report.json` y capturas `cu19-*.png`.

## Limitaciones y pendientes

1. Lint global preexistente: HistorialProduccionPage, ProduccionTab, RegistrarProduccionModal, RolesTab y produccionService. Los archivos afectados por CU19 pasan ESLint. No se corrigen otros casos de uso.
2. Build avisa de bundle de aproximadamente 691 kB; compila correctamente y no se añaden bibliotecas.
3. No se ejecutó la suite completa de los módulos ajenos a esta entrega; se ejecutaron los 61 casos dirigidos requeridos y las comprobaciones de navegación descritas.
4. La revisión automática rechazó eliminar recursivamente los perfiles efímeros de Chrome (`blocked by policy`). Chrome fue cerrado; los perfiles permanecen en `.local/chrome-cu19-isolated-*`, ignorados por Git. No se intentó otro mecanismo de borrado.
5. La información muestra el nombre actual del producto; el modelo no conserva nombres históricos. No cambia este alcance aprobado.

## Estado de Git y lista exacta para el commit

No se cambió de rama, no se fusionó main y no se hicieron commits, push ni staging. Se conservaron los cuatro documentos anteriores y se añadieron sus notas de continuación. Configuración local, modelos, migraciones y manifests de dependencias intactos.

Los siguientes **19 archivos** constituyen la entrega propuesta. Revisarlos antes de incorporarlos; no usar git add . para incluir archivos ajenos.

```text
backend/apps/productos_inventario/productos/permissions.py
backend/apps/productos_inventario/productos/selectors.py
backend/apps/productos_inventario/productos/serializers.py
backend/apps/productos_inventario/productos/tests.py
backend/apps/productos_inventario/productos/urls.py
backend/apps/productos_inventario/productos/views.py
frontend/src/apps/dashboard/productos/ProductosPage.tsx
frontend/src/apps/dashboard/productos/historial-precios/HistorialPreciosPage.tsx
frontend/src/apps/dashboard/productos/historial-precios/useHistorialPrecios.ts
frontend/src/routes/AppRoutes.tsx
frontend/src/services/historialPreciosService.ts
frontend/src/types/historialPrecio.ts
docs/ai/CURRENT_STATE.md
docs/ai/DECISIONS_LOG.md
docs/ai/HANDOFF_LATEST.md
docs/ai/sessions/2026-10-22-codex-cu19-analisis.md
docs/ai/sessions/2026-10-22-codex-cu19-implementacion.md
docs/informes/CU19_analisis_tecnico.md
docs/informes/CU19_implementacion_tecnica.md
```

No incluir `.local`, `.env`, `.venv`, node_modules, dist ni evidencias/credenciales temporales. La documentación académica del Ciclo 3 queda para una etapa independiente.
