# Sesión de Desarrollo: CU11 — Consultar historial de producción

- **Fecha:** 2026-10-12
- **Autor / Integrante:** Equipo Panadería Santiago (Pair Programming con Asistente IA)
- **Paquete / Módulo:** `apps.productos_inventario` -> `apps.productos_inventario.produccion`
- **Casos de Uso abordados:** CU11 (Consultar historial de producción)
- **Ciclo:** Ciclo 2

---

## 1. 🎯 Objetivo de la sesión
Implementar la consulta del historial de producción de la Panadería Santiago, con acceso restringido al rol de Personal de Producción y con listado y detalle de lotes ordenados por fecha reciente.

## 2. 🛠️ Cambios realizados

### Backend
- Se creó el selector `get_historial_produccion()` para filtrar por fecha, jornada y producto.
- Se agregó la clase `PuedeConsultarHistorialProduccion` para validar permisos RBAC.
- Se refactorizó `ProduccionListView` para ofrecer `GET /api/produccion/` con filtros.
- Se agregó `ProduccionDetailView` para `GET /api/produccion/<id>/`.
- Se actualizaron `serializers.py` para incluir:
  - responsable,
  - total de unidades,
  - total de variedades,
  - costo total del lote,
  - detalle de cada producto producido.
- Se ajustó `urls.py` para la ruta del historial y el detalle.
- Se agregó una migración correctiva idempotente para crear las tablas físicas de producción cuando la migración inicial figure aplicada pero las tablas no existan en PostgreSQL.
- Se ampliaron pruebas en `tests.py` para cubrir:
  - autenticación requerida,
  - permiso requerido,
  - acceso con rol válido.

### Frontend
- Se dejó la estructura de consumo de la API alineada con el módulo de producción existente.
- Se confirmó que la vista del historial sigue usando el contrato de `ProduccionRegistro` y `ProduccionFiltros` del servicio de producción.
- Se hizo explícita la identificación de los casos de uso en la pantalla: la acción de registro indica CU10 y el panel del historial indica CU11.
- Se implementó CU11 como una pestaña de consulta independiente dentro del módulo Productos e Inventario, según el mapa de paquetes; CU10 conserva su pestaña y flujo originales.
- Se refinó la presentación de CU11 con filtros agrupados, estados vacíos más claros y una tabla mejor jerarquizada, manteniendo la paleta del dashboard.
- Se ajustó el resumen de jornadas/unidades, el estado de error y la acción explícita para abrir el detalle.
- Se agregó un comando local de datos de demostración, protegido para ejecutarse solo cuando no existan producciones y sin crear movimientos de inventario.

## 3. 🧠 Decisiones técnicas tomadas
- El acceso de consulta queda restringido exclusivamente a Personal de Producción, según la decisión del negocio.
- El historial se mantiene como lectura pura; no modifica inventario ni genera movimientos adicionales.
- Los cálculos de totales usan `Decimal` en backend para evitar errores de precisión por `float`.
- La consulta se usa desde un selector específico para separar la capa de lectura de la capa de presentación.

## 4. ⚠️ Pendientes o siguientes pasos
- Validar la ejecución real del backend en un entorno con PostgreSQL disponible y sin bloqueo del driver `psycopg2`.
- Completar la integración real a la API del backend en el frontend si el entorno local lo permite.
- Revisar la zona de permisos del rol en la base de datos de seed para que el permiso `registrar_produccion` quede exactamente alineado con la sintaxis usada por el módulo.
- El backend aún debe exponer el registro POST de CU10 y la simulación de consumo para completar el flujo real desde el modal.
- La migración correctiva de producción debe aplicarse en cada entorno con `python manage.py migrate` antes de consultar CU11.

## 5. 🧪 Cómo probar lo implementado
- Ejecutar el backend en un entorno con PostgreSQL funcionando.
- Iniciar sesión con `mrojas` (`Admin123!`), abrir Productos e Inventario y verificar los rótulos CU10 y CU11 en Producción diaria.
- Verificar que la pestaña `CU11 · Historial` ofrezca filtros de fecha, jornada y producto, tabla de resultados y detalle; comprobar por separado que CU10 conserva su pestaña Producción diaria y modal de registro.
- Para datos de demostración en una base local vacía, ejecutar primero `docker compose exec backend python manage.py seed_historial_demo --dry-run` y luego `docker compose exec backend python manage.py seed_historial_demo`. El comando no modifica inventarios y se detiene si ya hay producciones.
- Ejecutar `npm run build` desde `frontend/`.
- Comprobar:
  - `GET /api/produccion/` devuelve el historial.
  - `GET /api/produccion/<id>/` devuelve el detalle.
  - usuario sin permiso responde `403`.
  - usuario sin login responde `401`.
  - rango inválido de fechas responde `400`.
