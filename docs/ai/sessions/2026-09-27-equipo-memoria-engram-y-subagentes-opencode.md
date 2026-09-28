# Sesión de Desarrollo: Memoria persistente con Engram y subagentes de opencode

- **Fecha:** 2026-09-27
- **Autor / Integrante:** Equipo (asistente opencode + Engram MCP)
- **Paquete / Módulo:** transversal — `docs/ai/`, `docs/`, `.opencode/agents/`
- **Casos de Uso abordados:** ninguno (documentación y tooling; no toca CUs de código)
- **Ciclo:** Ciclo 1 — Base del Sistema, Seguridad, Catálogos y Auditoría (en curso)

---

## 1. 🎯 Objetivo de la sesión

1. Confirmar la disponibilidad de las herramientas MCP de Engram y registrar el contexto fundacional del proyecto en memoria persistente.
2. Crear el subagente `backend` de opencode (adaptado desde otro repositorio, sin dockerización) y luego `frontend`, `architecture`, `puds` y `code-review`.
3. Convertir el registro de sesiones de `docs/ai/sessions/` en una regla **obligatoria y automática**, ya que hasta ahora no se había generado ninguna bitácora pese a los cambios realizados.

---

## 2. 🛠️ Cambios realizados

- **Base de datos:** sin cambios.
- **Backend:** sin cambios en código. Solo se inspeccionó `backend/requirements.txt` y `backend/config/settings.py` para anclar los agentes al stack real.
- **Frontend:** sin cambios en código. Solo se leyeron `frontend/package.json`, `src/services/api.ts` y `src/routes/AppRoutes.tsx`.
- **Documentación / tooling (lo único modificado):**
  - `.opencode/agents/backend.md` — **nuevo**. Adaptado de `Proyecto-SI1/.opencode/agents/backend.md`, con dockerización eliminada.
  - `.opencode/agents/frontend.md` — **nuevo**. React 19 + TS 6 + Vite 8 + Tailwind 4.
  - `.opencode/agents/architecture.md` — **nuevo**. Límites de paquetes, contratos, seguridad, trazabilidad PUDS.
  - `.opencode/agents/puds.md` — **nuevo** (`bash: deny`). Artefactos PUDS/UML y defensa.
  - `.opencode/agents/code-review.md` — **nuevo** (`edit: deny`). Revisión de código.
  - `.opencode/agents/qa-testing.md` — **nuevo**. Estrategia de validación con el runner de Django, lint y build.
  - `.opencode/agents/security.md` — **nuevo**. Auditoría de JWT, RBAC, bloqueo, CORS, secretos y bitácora.
  - `.opencode/agents/ui-ux.md` — **nuevo**. Usabilidad, accesibilidad, responsive y tokens de diseño.
  - `.opencode/agents/orchestrator.md` — **nuevo** (`mode: primary`). Enruta por tipo de tarea con lista blanca de subagentes.
  - `.opencode/agents/docs-memory.md` — **nuevo** (`bash: deny`). Dueño de la bitácora de sesión y de la continuidad documental.
  - `docs/ai/MASTER_AGENT_PROMPT.md` — regla 6 reemplazada: el registro de sesión pasó de sugerencia ("crear o invitar") a **obligatorio y automático**, con nombre de archivo `YYYY-MM-DD-[autor]-[resumen-corto].md`, sufijo `-2` para segunda sesión del día, y regla de no sobrescribir historial.
  - `agents.md` — sección 5 actualizada: se corrigió la lista de archivos de `docs/ai/` (varios ya existían, estaban aún como "recomendados") y se añadió el bloque **REGLA OBLIGATORIA: BITÁCORA DE SESIÓN AUTOMÁTICA**.
  - `docs/README.md` — árbol de `docs/` corregido y completo; nuevas secciones "Bitácora de Sesiones (obligatoria)" y "Agentes de IA del proyecto".
  - `docs/ai/sessions/2026-09-27-equipo-memoria-engram-y-subagentes-opencode.md` — **este archivo** (primera bitácora del proyecto).

---

## 3. 🧠 Decisiones técnicas tomadas

- **Contexto de dominio:** el sistema se registra en Engram como **MRP (Material Requirements Planning)**, tal como lo definió el usuario, aunque `agents.md` lo describía solo como gestión de ventas/producción/inventario. Queda pendiente decidir si el módulo de producción calcula requerimientos de insumos a partir de recetas y stock.
- **Ishikawa:** se fijó su alcance como **solo documentación** (análisis causa-efecto en material de análisis o defensa), nunca como notación de diseño ni sustituto de un artefacto UML.
- **Los agentes se anclaron al código real, no a la documentación**, porque la doc tiene deriva:
  - `docs/ai/ARCHITECTURE.md` dice "Django 6+", pero `backend/requirements.txt` fija **Django 5.1.1**.
  - `docs/ai/TECH_STACK.md` menciona `python-dotenv`, pero `settings.py` importa **`decouple`** (`python-decouple`).
  - Por eso la primera regla del agente `architecture` es: *el código es la fuente de verdad; reportar la deriva, nunca propagarla*.
- **Entorno local solamente:** se eliminó toda mención a Docker, contenedores y despliegue cloud en los agentes, porque la contenedorización está pospuesta tras el Ciclo 1.
- **Comandos de validación reales:** no existe pytest en `requirements.txt` ni runner de tests en `package.json`, así que los agentes validan con `manage.py check` / `makemigrations --check` / `manage.py test`, y `npm run lint` / `npm run build`.
  - **Contrato de errores de autenticación:** `auth_app/exceptions.py` devuelve `{"error": "<texto>"}` plano y `429 Too Many Requests` (con `retry_after_seconds`) para cuenta bloqueada; el frontend lo consume con `setError()`. Los tests deben afirmar esa forma exacta. Ojo: el valor de `retry_after_seconds` debe llegar como **entero**, no como cadena.
- **Contadores en caché:** la política de bloqueo y el throttling de DRF usan `django.core.cache`; los tests deben limpiar la caché en `setUp` o quedan dependientes del orden.
- **Hallazgos de seguridad abiertos (documentados en el agente `security`):** `SECRET_KEY` con default inseguro y `DEBUG=True` por defecto en `settings.py`; `ALLOWED_HOSTS = ['*']` sin `CSRF_TRUSTED_ORIGINS` ni `SECURE_*`; `ROTATE_REFRESH_TOKENS=True` con `BLACKLIST_AFTER_ROTATION=False`; `seed_usuarios` crea 6 usuarios (incluido superusuario) con `Admin123!`; tokens en `localStorage`.
- **Carpeta correcta de agentes:** `.opencode/agents/` (en plural) es la ruta oficial por proyecto de opencode 1.18.32; el nombre del archivo es el nombre del agente y se invoca con `@nombre`. Requiere reiniciar opencode para cargarse.
- **Inconsistencia detectada en frontend:** existen `src/context/` (vacía) y `src/contexts/` (con `AuthContext.tsx`). Se dejó la decisión para el equipo; el agente `frontend` advierte sobre ello.

---

## 4. ⚠️ Pendientes o siguientes pasos

- **Actualizar la documentación con deriva:** corregir "Django 6+" en `docs/ai/ARCHITECTURE.md` y `python-dotenv` en `docs/ai/TECH_STACK.md` (el agente `architecture` lo hará con `@architecture`).
- **Definir el alcance MRP:** confirmar si el cálculo de requerimientos de insumos por receta/BOM entra en el Ciclo 2 (CU8-CU12) y si esa decisión cambia `PROJECT_VISION.md` y `agents.md`.
- **Agentes restantes opcionales:** `diagrams-modeling`, `mrp`. El conjunto actual de 10 (`backend`, `frontend`, `ui-ux`, `architecture`, `puds`, `code-review`, `qa-testing`, `security`, `docs-memory`, `orchestrator`) ya cubre la programación del proyecto.
- **Pendiente para CU2 (recuperar contraseña):** decidir la herramienta de captura de correo en local y conectar el correo de Django (`EMAIL_BACKEND`) a ella. Mailpit es la opción recomendada frente a Mailhog.
- **El `orchestrator` hereda la regla de bitácora:** incluye la obligación de crear/actualizar `docs/ai/sessions/YYYY-MM-DD-[autor]-[resumen-corto].md` y la prohibición de hacer `git commit`/`git add`/`git push` por iniciativa propia, porque el usuario commitea manualmente.
- **Copiar la skill de diagramas:** el otro proyecto tiene `.opencode/skills/uml-c4-puds-diagrams/SKILL.md`; aquí solo existe `.agents/skills/`. El agente `puds` la usa si está disponible.
- **Resolver `src/context/` vs `src/contexts/`** y eliminar la carpeta vacía.
- **Reiniciar opencode** para que los 5 subagentes aparezcan en el menú `@`.
- Migrar a `docs/ai/CURRENT_STATE.md` y `HANDOFF_LATEST.md` los avances de esta sesión.

---

## 5. 🧪 Cómo probar lo implementado

Los agentes de opencode no se "ejecutan", se cargan al arrancar. Verificación:

1. **Confirmar que los archivos existen y el frontmatter es válido** (delimitadores `---` en líneas 1 y 11):
   ```powershell
   Get-ChildItem .opencode\agents\*.md | ForEach-Object { $_.Name; (Get-Content $_.FullName | Select-String '^mode:').Line }
   ```
2. **Reiniciar opencode** en la raíz del proyecto y escribir `@` en el chat: deben aparecer `backend`, `frontend`, `architecture`, `puds` y `code-review`.
3. **Probar un subagente** (ej. revisión sin editar nada):
   ```
   @code-review revisa los cambios de backend/apps/usuarios_seguridad
   ```
   Resultado esperado: hallazgos con `ruta:línea`, sin haber modificado ningún archivo.
4. **Probar la regla de bitácora** con una tarea cualquiera y verificar que se crea `docs/ai/sessions/YYYY-MM-DD-[autor]-[resumen].md`.

Nota: en esta sesión no se ejecutaron `manage.py check` ni `npm run build` porque **no hubo cambios de código** — solo documentación y archivos de agente.
