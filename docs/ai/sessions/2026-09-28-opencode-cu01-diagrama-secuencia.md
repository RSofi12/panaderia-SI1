# Sesión de Desarrollo: CU1 — Diagrama de Secuencia UML para Enterprise Architect (Ciclo 1)

- **Fecha:** 2026-09-28
- **Autor / Integrante:** opencode (agente de IA)
- **Paquete / Módulo:** `apps.usuarios_seguridad` (backend) + `frontend` (capa de presentación)
- **Casos de Uso abordados:** CU1 (secundariamente CU26, por la auditoría de la bitácora)
- **Ciclo:** Ciclo 1
- **Método / Notación:** PUDS iterativo-incremental + UML 2.5, patrón BCE (Boundary-Control-Entity)
- **Fuente de verdad:** `backend/apps/PACKAGE_CU_MAP.md` → `CU01 Iniciar sesión` → `apps.usuarios_seguridad` (Ciclo 1), actor(es): **Todos**

---

## 1. 🎯 Objetivo de la sesión

Generar el **diagrama de secuencia del CU1 (Iniciar sesión)** en formato de script JScript para
Enterprise Architect 15, usando como plantilla el script del proyecto anterior
`CUsecuenciaEA/CU20_diagrama_secuencia_generar_reportes.js`.

El diagrama debía cumplir tres condiciones:

1. Reflejar **el código real**, no una especificación idealizada (regla de `.opencode/agents/puds.md`:
   *"un diagrama debe coincidir con el código y con el DDL"*).
2. Usar parámetros UML correctos: arquitectura BCE, líneas de vida, mensajes de retorno con
   `Stereotype "return"`, y fragmentos combinados `alt` / `opt` con sus condiciones de guarda.
3. Ser defendible ante la docente, recogiendo las decisiones de diseño que el equipo ya
   documentó en `docs/ai/DECISIONS_LOG.md`.

---

## 2. 🛠️ Cambios realizados

### Artefacto creado

| Archivo | Descripción |
|---|---|
| `CUsecuenciaEA/ciclo1Secuencia_CU/CU01_diagrama_secuencia_iniciar_sesion.js` | Script JScript (EA) que genera el diagrama de secuencia del CU1 |

No se modificó **ninguna línea de código de producción** (ni backend, ni frontend, ni base de datos).
La sesión es puramente documental/de modelado.

### Participantes del diagrama (15 líneas de vida)

Cada participante es una clase o módulo real, verificado contra el código:

| # | Nombre en el diagrama | Estereotipo | Ubicación real |
|---|---|---|---|
| 1 | `Administrador / Propietario / Personal de Ventas / Produccion` | `Actor` | CU01 tiene actor "Todos" |
| 2 | `:LoginPage` | `Boundary` | `frontend/src/apps/auth/LoginPage.tsx` |
| 3 | `:AuthProvider` | `Control` | `frontend/src/contexts/AuthProvider.tsx` |
| 4 | `:authService` | `Service` | `frontend/src/services/authService.ts` + `services/api.ts` |
| 5 | `:CustomLoginView` | `Control` | `backend/.../usuarios_seguridad/auth_app/views.py` |
| 6 | `:LoginThrottle` | `Component` | `AnonRateThrottle`, scope `login` = 10/min por IP (`config/settings.py`) |
| 7 | `:CustomTokenObtainPairSerializer` | `Control` | `backend/.../auth_app/serializers.py` |
| 8 | `:RefreshToken` | `Component` | `rest_framework_simplejwt.tokens.RefreshToken` |
| 9 | `:politica_bloqueo` | `Service` | `backend/.../auth_app/services/politica_bloqueo.py` |
| 10 | `:EstadoBloqueo` | `Entity` | `@dataclass(frozen=True)` del mismo módulo (DTO, no tabla) |
| 11 | `:Usuario` | `Entity` | tabla `usuario` (`users/models.py`) |
| 12 | `:ConfiguracionSeguridad` | `Entity` | tabla `configuracion_seguridad` (singleton, 3 intentos / 10 min) |
| 13 | `:Bitacora` | `Entity` | tabla `bitacora` (`bitacora/models.py`) |
| 14 | `:Rol` | `Entity` | tabla `rol` |
| 15 | `:Permiso` | `Entity` | tabla `permiso` |

### Flujos modelados — 65 mensajes, 8 fragmentos combinados, 3 notas

| Fragmento | Tipo | Condición de guarda | Resultado |
|---|---|---|---|
| F1 | `alt` | dentro del límite de peticiones (`LoginThrottle` 10/min por IP) | `200` / `429 {"detail": ...}` |
| F2 | `opt` | `nombre_usuario` o `password` vacío | `400` |
| F3 | `alt` | `Usuario.objects.filter(...)` no devuelve filas | `400` / continúa el flujo principal |
| F4 | `opt` | ventana de bloqueo vencida | reinicio del contador (resolución perezosa) |
| F5 | `alt` | `estado.bloqueado == true` | `429` + `Retry-After` |
| F6 | `alt` | `usuario.activo == false` | `400` cuenta inactiva |
| F7 | `alt` | credenciales correctas | `200` + JWT + redirección a `/dashboard` |
| F8 | `alt` | `intentos_fallidos >= max_intentos_fallidos` | `429` + `Retry-After` |

Además se documentan en la cabecera del script las 4 acciones del
enum `AccionBitacora` que dispara el CU1: `INICIO_SESION`, `LOGIN_FALLIDO`,
`ACCESO_BLOQUEADO` y `ACCESO_DENEGADO`.

---

## 3. 🧠 Decisiones técnicas tomadas

1. **El Serializer es `<<control>>`, no `<<boundary>>`.** El `CustomTokenObtainPairSerializer` es quien
   orquesta todo el CU1 (busca el usuario, consulta la política, audita, genera el token), no la vista.
   Esto respeta la decisión 4 de `DECISIONS_LOG.md` ("la lógica de negocio del login no vive en la
   vista"); por eso se modela como Control y la vista queda como Control de entrada.

2. **Orden de las líneas de vida por flujo de interacción, no por capa.** Se ordenaron de izquierda a
   derecha siguiendo las colaboraciones más frecuentes (`Serializer ↔ RefreshToken ↔ politica_bloqueo`
   contiguos) en lugar del orden jerárquico BCE, para evitar flechas largas que dificulten la lectura
   en la defensa.

3. **Las ramas de error cierran con 2 mensajes** (retorno HTTP desde `:CustomLoginView` e
   interpretación en `:LoginPage`) y **omiten el salto por `:AuthProvider`** porque `login()` no captura
   la excepción: solo tiene `finally { setIsLoading(false) }`, luego no aporta un mensaje observable.
   Se documentó esta decisión en la cabecera del script.

4. **Se añadieron 3 notas al pie** con las decisiones defendibles ante la docente:
   contrato `400/429` (y por qué **no** `401/423`), anti-enumeración de usuarios + ventana de bloqueo
   que nunca se extiende, y por qué `last_login` se escribe en `registrar_intento_exitoso()` en lugar
   de `update_last_login()` de SimpleJWT.

5. **Se modelaron los 6 flujos alternos que el equipo ya había definido** en
   `docs/ai/IMPLEMENTATION_PHASES.md` (Fase 1), no solo el flujo principal y el error genérico.

6. **Verificación automática del layout.** Se escribió un validador temporal (Node.js) que comprueba:
   (a) la sintaxis JScript parsea correctamente, (b) cada caja de fragmento contiene **exactamente**
   los mensajes que le corresponden según la posición cronológica, (c) no hay solapes horizontales
   entre las 15 líneas de vida. Esto detectó y corrigió **6 errores de coordenada** en la primera versión.

---

## 4. ⚠️ Corrección importante sobre un artefacto previo

Existe un script anterior en la raíz del repositorio,
`ciclo1Secuencia_CU/CU01_diagrama_secuencia_iniciar_sesion.js`, generado en la sesión
`2026-09-27-agente-cu01-diagrama-secuencia.md`. **Está desactualizado y no coincide con el código real.**
Sus principales errores:

| Afirmación del script antiguo | Realidad en el código |
|---|---|
| `POST /api/auth/token/` | `POST /api/auth/login/` (`auth_app/urls.py`) |
| `:AuthController` | No existe: es `CustomLoginView` + `CustomTokenObtainPairSerializer` |
| `:BitacoraAcceso (AuditLog)` | El modelo real es `Bitacora` (tabla `bitacora`) |
| `CustomUser` | El modelo real es `Usuario` (`db_table = "usuario"`) |
| Respuesta `{access_token, refresh_token, rol, username}` | Respuesta real `{refresh, access, user{...}}` |
| Error `401 Unauthorized {detail: 'Credenciales inválidas'}` | El CU devuelve **`400 {"error": ...}`**; el `401` está descartado por diseño |
| Sin bloqueo de intentos | Falta toda la política de bloqueo (`politica_bloqueo`, `429` + `Retry-After`, 3 intentos / 10 min, `select_for_update`) |

> ⚠️ **Pendiente de decisión del equipo:** ese archivo obsoleto de la raíz **no se borró** en esta
> sesión. Se dejó intacto para no hacer cambios destructivos sin aprobación. Se recomienda eliminarlo o
> moverlo, y usar únicamente la versión de `CUsecuenciaEA/ciclo1Secuencia_CU/`.

---

## 5. ⚠️ Pendientes o siguientes pasos

- [ ] **Decidir qué hacer** con el script obsoleto de la raíz (`ciclo1Secuencia_CU/`).
- [ ] Ejecutar el script en Enterprise Architect y verificar visualmente que los fragmentos se
      renderizan donde corresponde (las coordenadas se validaron por cálculo, no dentro de EA).
- [ ] Generar los diagramas del **resto del Ciclo 1**: CU2, CU3, CU4, CU5, CU6 y CU26, en la misma
      carpeta y con el mismo estilo de este script.

---

## 6. 🧪 Cómo probar lo implementado

1. En Enterprise Architect 15, abrir el proyecto `.eapx` del equipo.
2. En el **Project Browser**, seleccionar el paquete destino (por ejemplo `ciclo1Secuencia_CU`).
   Si no hay paquete seleccionado, el script usa/crea el paquete `ciclo1Secuencia_CU` en la raíz.
3. Ir a **Specialize → Tools → Scripting**, cargar el archivo
   `CUsecuenciaEA/ciclo1Secuencia_CU/CU01_diagrama_secuencia_iniciar_sesion.js` y ejecutar
   (**Run Script**).
4. El script borra el diagrama homónimo previo (si existe) y recrea el diagrama
   `CU01 - Iniciar Sesion`, que se abre automáticamente en el editor de secuencia.
5. Comprobaciones visuales esperadas:
   - 15 líneas de vida en recuadros rectangulares (sin iconos circulares de *Robustness*).
   - 65 mensajes numerados; las flechas de retorno son discontinuas.
   - 8 marcos de fragmentos con sus condiciones de guarda, y 3 notas al pie.
