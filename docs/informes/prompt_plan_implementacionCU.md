# CONTEXTO
Soy integrante del equipo de la Panadería Santiago (proyecto de Sistemas de
Información: sistema web MRP). Estamos en el Ciclo {{CICLO}} y me asignaron
implementar el {{CU_ID}} {{CU_NOMBRE}}.

Stack: Backend Django + Django REST Framework (Python), Frontend React
(TypeScript), PostgreSQL, todo dockerizado (docker compose).
Metodología: PUDS iterativo-incremental, modelado con UML.

# DOCUMENTOS QUE DEBES LEER ANTES DE RESPONDER
1. backend\apps\PACKAGE_CU_MAP.md → descripción, actor, paquete, ciclo,
   prioridad, riesgo y relaciones <<include>>/<<extend>> del CU.
2. panaderia-SI1\docs\ → arquitectura y convenciones del proyecto.
3. panaderia-SI1\docs\informes\Database_Panaderia_Santiago.sql → DDL vigente.
4. El código ya existente en backend\apps\ y frontend\ (para respetar
   nombres, estilo, estructura y lo que ya implementó el Ciclo 1).
Si algún archivo no existe o no lo puedes leer, dímelo; no lo inventes.

# REGLAS DE ARQUITECTURA (obligatorias)
- NO usamos triggers ni procedimientos almacenados (PA) en la BD. Toda la
  lógica de negocio va en Django (Python).
- Capas por app: urls.py → views.py (delgada, hace de "controller") →
  serializers.py (validación) → services.py (escrituras y reglas de
  negocio) → models.py. Las consultas de solo lectura con filtros o
  cálculos van en selectors.py.
- Toda operación que escriba en varias tablas usa transaction.atomic();
  si modifica inventario usa select_for_update() para evitar condiciones
  de carrera.
- Cantidades y dinero con Decimal (nunca float).
- Valores fijos (p. ej. el "tipo" de movimiento) con choices/enum en el
  modelo, un único valor por concepto en todo el proyecto.
- Cada regla de negocio vive en UN solo lugar (no duplicar la actualización
  de inventario en varios archivos).
- Permisos según rol (RBAC del CU04): indica qué rol(es) pueden usar cada
  endpoint y cómo se valida en DRF.
- Las acciones relevantes (crear/modificar/eliminar) se registran en la
  bitácora (CU26) con usuario, fecha y hora.
- El DDL puede cambiar levemente; si propones un cambio, justifícalo.

# TAREA (en esta respuesta SOLO planificación, NO escribas código todavía)
Dame por el chat un plan de implementación del {{CU_ID}}, con estas secciones:

1. Resumen del CU: objetivo, actor, precondiciones, flujo principal,
   flujos alternativos/errores y postcondiciones (qué cambia en la BD).
2. Dependencias: qué CU o tablas deben existir antes (Ciclo 1 y 2) y qué
   puedo simular o crear temporalmente si todavía no están.
3. Base de datos:
   a) Tablas del DDL que usa este CU y cómo se usa cada una (leer/escribir).
   b) Modelos Django NUEVOS que hay que crear (si la tabla aún no tiene
      modelo) y los que ya existen.
   c) Cambios propuestos al DDL (si los hay) y su justificación.
   d) Migraciones necesarias.
4. Backend: árbol de archivos nuevos o modificados con su ruta completa
   (models, serializers, views, services, selectors, urls, permissions,
   tests) y, por cada archivo, su responsabilidad en una línea.
5. API: tabla de endpoints (método, URL, rol permitido, request, response,
   códigos de error).
6. Lógica de negocio: pasos del service en pseudocódigo (bucles,
   cálculos, validaciones, orden de las escrituras y qué pasa si falla).
7. Frontend: árbol de archivos con ruta completa (pages, components,
   services/api, hooks, types .ts, rutas), estados de la pantalla (cargando,
   vacío, error, éxito), validaciones del formulario y flujo del usuario.
8. Pruebas: casos de prueba clave (camino feliz, datos inválidos, falta de
   stock, usuario sin permiso, falla a mitad de la transacción).
9. Riesgos y preguntas abiertas: decisiones de negocio que debo consultar
   al equipo o a la docente antes de programar.
10. Orden de implementación sugerido (paso a paso, con entregables
    verificables por paso) y nombre de rama de Git sugerido.

# FORMATO
- Español, claro y sencillo (soy estudiante de pregrado).
- Usa tablas para archivos, endpoints y pruebas.
- Cita al final de qué archivo (y sección) sacaste cada dato.
- No avances a la implementación hasta que yo apruebe el plan.

# VARIABLES DE ESTE PEDIDO
{{CICLO}} = ...
{{CU_ID}} = ...
{{CU_NOMBRE}} = ...
{{POR_QUE_ES_COMPLEJO}} = ...