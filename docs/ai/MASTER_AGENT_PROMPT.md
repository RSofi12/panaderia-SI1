# MASTER AGENT PROMPT — Panadería Santiago (SI-1)

**⚠️ REGLAS PRIMARIAS PARA CUALQUIER IA O DESARROLLADOR QUE PROGRAME EN ESTE PROYECTO:**

---

1. **CONTEXTO OMNIPRESENTE (LEE `docs/ai/` y `PACKAGE_CU_MAP.md`):**
   El sistema es un **Sistema de Información Web para la Gestión de Ventas, Producción, Inventario y Control Administrativo para la Panadería "Santiago"** (Santa Cruz de la Sierra, Bolivia).
   - Backend: Django 5+ / Django REST Framework (DRF) en `backend/`.
   - Frontend: React + TypeScript + Vite + Tailwind CSS en `frontend/`.
   - Base de datos: PostgreSQL 14+ con integridad referencial y triggers de bitácora.
   - Antes de generar código, absorbe [`docs/ai/ARCHITECTURE.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/ARCHITECTURE.md), [`backend/apps/PACKAGE_CU_MAP.md`](file:///c:/Users/PERSONAL/panaderia-SI1/backend/apps/PACKAGE_CU_MAP.md) y [`docs/informes/Database_Panaderia_Santiago.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Database_Panaderia_Santiago.sql).

2. **CLIENTES Y PROVEEDORES COMO DATOS (NO COMO USUARIOS CON LOGIN):**
   Los clientes que compran en mostrador o realizan pedidos, y los proveedores de materia prima, son entidades de datos. **No tienen cuenta de usuario, no hacen login ni tienen acceso al sistema.**
   Los únicos usuarios con acceso autenticado (JWT + RBAC) son los colaboradores internos:
   - **Administrador** (Seguridad, usuarios, roles, permisos y bitácora).
   - **Propietario** (Carlos Santiago Vargas - Control global, compras, gastos, precios y balances).
   - **Personal de Ventas** (Ventas mostrador, pedidos, comprobantes y stock disponible).
   - **Personal de Producción / Maestro Panadero** (Miguel Ángel Rojas - Registro de producción, consumo de insumos, stock de materias primas y mermas).

3. **ORGANIZACIÓN MODULAR ESTRICTA (5 PAQUETES DJANGO):**
   Todo código de backend pertenece exclusivamente a uno de los 5 paquetes en `backend/apps/`:
   1. `apps.usuarios_seguridad` (CU1, CU2, CU3, CU4, CU26)
   2. `apps.productos_inventario` (CU5, CU8, CU9, CU10, CU11, CU12, CU18, CU19)
   3. `apps.compras` (CU6, CU7, CU20)
   4. `apps.comercializacion` (CU13, CU14, CU15, CU16, CU17)
   5. `apps.reportes` (CU21, CU22, CU23, CU24, CU25)

4. **INTEGRACIÓN DEL FLUJO DE NEGOCIO Y TRAZABILIDAD:**
   El software conecta el ciclo operativo completo:
   $$\text{Compras/Proveedores} \longrightarrow \text{Stock Materia Prima} \longrightarrow \text{Producción} \longrightarrow \text{Stock Panes} \longrightarrow \text{Ventas/Pedidos} \longrightarrow \text{Resultados Económicos}$$
   Toda acción relevante debe respetar transacciones atómicas de base de datos (`transaction.atomic()`) para evitar inconsistencias de inventario o dinero.

5. **NO HARDCODEES Y USA VARIABLES DE ENTORNO:**
   Credenciales, puertos, URLs de API y claves secretas se gestionan mediante `.env` y variables de entorno del sistema. El proyecto cuenta con **entorno dockerizado oficial** (`docker-compose.yml`, `backend/Dockerfile` y `frontend/Dockerfile`) que orquesta los 4 servicios (`db`, `mailpit`, `backend` y `frontend`) con un solo comando (`docker compose up -d`), manteniendo además compatibilidad completa con ejecución local directa (`venv` y `npm`).

6. **MEMORIA VIVA DEL PROYECTO — OBLIGATORIA Y AUTOMÁTICA (`docs/ai/`):**
   El registro de sesión **no es opcional ni queda a criterio del autor**: se escribe en el momento en que ocurre el cambio, no "al final si sobra tiempo". Cada vez que se cree, modifique o elimine un archivo del proyecto —sin importar si es backend, frontend, base de datos, configuración o documentación— se debe:
   - **Crear el archivo de bitácora en [`docs/ai/sessions/`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/sessions/) siguiendo la plantilla de [`docs/ai/sessions/README.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/sessions/README.md).**
     - Nombre obligatorio: `YYYY-MM-DD-[autor]-[resumen-corto].md` (ej. `2026-09-27-equipo-cu1-login-jwt.md`).
     - Si en el mismo día hay varias sesiones del mismo autor, se agrega un sufijo: `2026-09-27-equipo-cu5-productos-2.md`.
     - La plantilla es obligatoria: objetivo, cambios por capa (backend/frontend/BD), decisiones, pendientes y cómo probar.
     - Si el archivo del día ya existe, se **actualiza** (se agregan las entradas nuevas); nunca se sobrescribe el historial.
   - Actualizar [`docs/ai/CURRENT_STATE.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/CURRENT_STATE.md) reflejando el progreso real.
   - Mantener [`docs/ai/HANDOFF_LATEST.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/HANDOFF_LATEST.md) con el resumen de entrega.
   - Registrar decisiones en [`docs/ai/DECISIONS_LOG.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/DECISIONS_LOG.md) si hubo cambios arquitectónicos.
   - Sin bitácora en `docs/ai/sessions/`, una tarea se considera **incompleta**, aunque el código funcione. Esto aplica también a los agentes de IA que trabajan en este repositorio (`.opencode/agents/*.md`).
