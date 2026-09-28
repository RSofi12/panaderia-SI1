# Bitácora de Sesión — 2026-09-27 — opencode — CU1 endurece el bloqueo (4 parches del metodo de la clinica)

## Objetivo

Auditar el módulo de seguridad del proyecto de la clínica de ojos
(`C:\Users\PERSONAL\Proyecto-SI1\backend\apps\Usuarios`) como referencia, decidir si su
método de bloqueo es mejor que el nuestro, y aplicar los puntos en que realmente lo es.

**Conclusión de la auditoría: no se cambia la arquitectura.** Se conservan las columnas de
bloqueo en `usuario` y el singleton `configuracion_seguridad`. Se adoptan 5 mejoras
puntuales y se rechazan 3 de su diseño por ser inseguras.

## Cambios por capa

### Backend — modelo de datos

- `bitacora/models.py`: nuevo enum `AccionBitacora(TextChoices)` con 6 acciones, aplicado
  como `choices` en `bitacora.accion`. Los **valores almacenados no cambian**.
- `bitacora/models.py`: nueva columna `agente_usuario` (varchar 255, truncada a 255).
- `Bitacora.registrar()` acepta `agente_usuario`.
- Migración generada y aplicada: `bitacora.0003_bitacora_agente_usuario_alter_bitacora_accion`.

### Backend — servicio de bloqueo

- `politica_bloqueo.py`: `registrar_intento_fallido()` reescrito con
  `transaction.atomic()` + `select_for_update()`. Corrige la condición de carrera en la que
  dos intentos simultáneos leían el mismo contador y **el bloqueo se atrasaba un intento**.
- Nuevo comportamiento: si la cuenta ya está bloqueada y la ventana sigue vigente, un intento
  adicional **no cuenta ni reinicia** la ventana; solo informa cuánto falta.
- `EstadoBloqueo`: el campo `minutos_restantes` pasa a ser propiedad calculada; la fuente de
  verdad es `segundos_restantes` (int), que permite la cuenta regresiva del frontend.
- Nuevo helper `_segundos_que_faltan()` con `math.ceil` (redondeo hacia arriba).
- Se eliminó el uso de `F()` en el conteo.

### Backend — errores HTTP

- `exceptions.py`: `CuentaBloqueadaError` (423 Locked) → `DemasiadosIntentosError`
  (**429 Too Many Requests**). Corrección de una decisión anterior equivocada.
- Devuelve `retry_after_seconds` como **entero real** (arma el payload después de
  `super().__init__()` para que `_get_error_details()` no lo convierta con `force_str()`).
- Expone `Retry-After` en la cabecera vía el atributo `wait` de DRF.

### Backend — serializadores y vistas

- `serializers.py`: nuevo helper `obtener_agente_usuario(request)`.
- `serializers.py` y `views.py`: todas las acciones de bitácora pasan a usar `AccionBitacora`.
- `serializers.py`: el 429 se lanza con `mensaje` y `retry_after_seconds` reales.

### Frontend

- `LoginPage.tsx`: contador regresivo `mm:ss` con `setInterval` limpiado en el `useEffect`;
  el botón "Ingresar" queda deshabilitado mostrando "Espera 09:58" hasta que expire.
- `LoginPage.tsx`: el contador se limpia a 0 cuando la respuesta **no** trae
  `retry_after_seconds`. Sin eso, un error de red posterior dejaba el botón congelado
  durante el resto de la ventana.
- `services/api.ts`: **bug corregido** — con `ROTATE_REFRESH_TOKENS=True` el backend emite un
  refresh nuevo y mete el viejo en lista negra, pero el interceptor solo guardaba el `access`.
  El refresh guardado quedaba revocado y la sesión se cerraba a la mitad del turno. Ahora
  persiste el refresh rotado.

## Decisiones tomadas

1. Mantener columnas en `usuario` en vez de una tabla `bloqueo_intento_login` claveada por
   texto. Su tabla bloquearía también usuarios inexistentes, pero un bot que pruebe 100.000
   nombres inventados llenaría 100.000 filas sin purga.
2. No copiar su código de recuperación de 6 dígitos en texto plano: 1.000.000 de
   combinaciones y ningún límite de intentos. Para CU2 se tomará su UX pero con hash.
3. Mantener el `CHECK (id_configuracion = 1)` en base de datos; su singleton solo se protege
   en Python y un `.update()` lo esquiva.
4. Cambiar 423 → 429 aunque ya estaba implementado y probado: 423 es de la familia WebDAV y
   no corresponde a un límite de tasa.

## Pruebas

- **31/31 en verde** con SQLite (antes 22). `manage.py test apps.usuarios_seguridad`.
- 9 pruebas nuevas: segundos restantes, cabecera `Retry-After`, cuenta regresiva decreciente,
  intento extra no reinicia la ventana, bitácora con IP + user-agent, truncado de user-agent
  gigante, valores del enum sin cambios, y acceda inexistente que falla al escribirse.
- **Smoke test en PostgreSQL real:** 400 → 400 → 429, `retry_after_seconds: 120` recibido
  como `int`, cabecera `Retry-After: 120`, `agente_usuario` persistido, y el contador se
  mantiene en 3 tras dos intentos extra sobre la cuenta ya bloqueada.
- `manage.py check` sin problemas. Migración aplicada.
- Frontend: `npm run lint` y `npm run build` limpios.

## Pendientes

- **CU2 (Recuperar contraseña):** no implementado. Requiere `Usuario.email` no nullable.
- `seed_usuarios.py` sigue dando `generar_reportes` a Personal de Ventas, aunque el usuario
  confirmó que los reportes son exclusivos del Propietario.
- Pendientes de producción: Redis para throttling compartido, purga de `OutstandingToken`,
  `DEBUG=False`, `ALLOWED_HOSTS` restringido.

## Resueltos en esta sesión (cierre de CU1)

- **El desbloqueo manual no es un faltante de CU1.** Se verificó empíricamente el ciclo
  completo: 3 fallos → cuenta bloqueada → se espera la ventana → 3 intentos **nuevos** → 3
  fallos → vuelve a bloquear. El desbloqueo automático ya funciona y es perezoso: al vencer
  `bloqueado_hasta`, el siguiente intento limpia el contador. `desbloquear_usuario()`
  (`politica_bloqueo.py:248`) queda como **utilidad opcional de desbloqueo inmediato**, sin
  llamadores por ahora; CU2 podrá reutilizarla tras validar la recuperación por correo, y
  CU26 el botón administrativo. No es un hueco de CU1.
- **Código 401/403 vs 400 de `IMPLEMENTATION_PHASES.md`:** resuelto/documentado. El markdown
  se actualizó al contrato real `400` (inválidas, inexistente, inactiva) y `429` (bloqueo
  acumulado con `Retry-After`), con la justificación de por qué no se usa `401`, `403` ni
  `423`. Los `403` de RBAC de los demás CUs se dejaron intactos porque son correctos ahí.
- **DDL maestro** `docs/informes/Database_Panaderia_Santiago.sql`: sincronizado con el
  schema real y **validado ejecutándolo** en un esquema temporal con rollback.

## Hallazgo de integridad referencial (bug encontrado y corregido)

La FK `bitacora.id_usuario` decía `ON DELETE NO ACTION` en la base de desarrollo, mientras el
modelo y la migración `0002` declaran `SET NULL`. Causa: `0001` creó la FK con `CASCADE`,
`0002` la cambió a `SET NULL`, pero la constraint real quedó en `NO ACTION`.

- `makemigrations --check` **no lo detecta**: compara el estado de los modelos contra el
  estado de las migraciones, no contra la base real. Como `0002` ya decía `SET_NULL`, Django
  daba el schema por bueno.
- Por el ORM no se nota: Django pone la columna en `NULL` desde Python antes de borrar. Pero
  un `DELETE FROM usuario` por SQL directo (pgAdmin, script de la docente) fallaba con
  *"update o delete en usuario viola la llave foránea bitacora_id_usuario"*, justo cuando lo
  que se quiere es conservar la auditoría de ese usuario.
- Corregido con `bitacora/migrations/0004_sincronizar_fk_bitacora_set_null.py`, que es
  defensiva: solo reconstruye la constraint si la regla actual no es `SET NULL`.
- De paso se detectó que las 16 FK reales son `DEFERRABLE INITIALLY DEFERRED` (lo que emite
  Django) mientras el DDL decía `INITIALLY IMMEDIATE` en las 39 apariciones. Corregido, con
  la razón explicada en la cabecera del DDL.
- **El DDL se validó ejecutándolo**, no solo revisándolo: se crea un esquema temporal
  `ddl_check`, se corre el documento con `search_path` a ese esquema y se revierte al final.
  Resultado: 30 tablas, las 5 de CU1 presentes, 13 columnas en `usuario`, los 4 CHECK
  rechazando valores inválidos (`CheckViolation` real, no `InFailedSqlTransaction`) y el
  `ON DELETE SET NULL` funcionando. El DDL se reproduce como una BD válida de verdad.
  Truco útil: el rol de PostgreSQL no tiene `CREATEDB`, así que no se puede validar con
  `CREATE DATABASE`; un esquema con rollback cumple la misma función sin ese permiso.

## Verificación del cierre (con una salvedad importante)

El árbol tiene trabajo de **CU2 en curso en otra sesión** (`recuperacion/`, campos de
configuración de token, `email` obligatorio). Para poder certificar CU1 sin interferir ni
depender de ese trabajo, se verificó sobre una **copia aislada** del backend:
- `manage.py test apps.usuarios_seguridad.auth_app` → **33/33 OK**
- `makemigrations --check` → sin cambios pendientes atribuibles a CU1

Lo que falla en la suite completa son 19 pruebas, **todas de `recuperacion`** (token, enlace,
correo, rate limit). Ninguna de CU1. Cuando la otra sesión termine CU2, conviene reejecutar la
suite completa.

Nota: durante esta verificación, `users/password_validators.py` quedó con un `#` faltante en
un comentario (línea 6), lo que impedía **arrancar Django** (`IndentationError`). Se corrigió
porque bloqueaba todo el proyecto por un error tipográfico, no de diseño.

## Cómo probar

```powershell
# Backend (el rol de PostgreSQL no tiene CREATEDB, por eso el settings alterno)
cd C:\Users\PERSONAL\panaderia-SI1\backend
$env:PYTHONPATH = "C:\Users\PERSONAL\AppData\Local\Temp\opencode"
.\venv\Scripts\python.exe manage.py test apps.usuarios_seguridad --settings=settings_test_sqlite
.\venv\Scripts\python.exe manage.py migrate
```

```powershell
# Frontend
cd C:\Users\PERSONAL\panaderia-SI1\frontend
npm run lint
npm run build
```

Para ver la cuenta regresiva en el navegador: hacer tres intentos fallidos con un usuario de
prueba y observar el `429` con la cabecera `Retry-After` en DevTools → Network.

## Nota sobre el bloqueo de pruebas

`manage.py test` falla con "se ha denegado el permiso para crear la base de datos" porque el
usuario de PostgreSQL no tiene `CREATEDB`. Solución definitiva: `ALTER ROLE <usuario> CREATEDB;`.
Mientras tanto se usa `settings_test_sqlite` **con `PYTHONPATH` apuntando al directorio
temporal**, porque el archivo no vive en el repositorio y sin esa variable de entorno Django
no logra importarlo (`ModuleNotFoundError: No module named 'settings_test_sqlite'`).

## Archivos relevantes

- `backend/apps/usuarios_seguridad/auth_app/services/politica_bloqueo.py` — concurrencia y segundos.
- `backend/apps/usuarios_seguridad/auth_app/exceptions.py` — 429, `Retry-After`, entero intacto.
- `backend/apps/usuarios_seguridad/auth_app/serializers.py` — orquestación, enum, user-agent.
- `backend/apps/usuarios_seguridad/auth_app/views.py` — enum en el logout.
- `backend/apps/usuarios_seguridad/bitacora/models.py` — `AccionBitacora` y `agente_usuario`.
- `backend/apps/usuarios_seguridad/bitacora/migrations/0003_*.py` — `agente_usuario` + enum.
- `backend/apps/usuarios_seguridad/bitacora/migrations/0004_*.py` — sincroniza la FK a SET NULL.
- `backend/apps/usuarios_seguridad/auth_app/tests.py` — 33 pruebas.
- `frontend/src/apps/auth/LoginPage.tsx` — contador regresivo.
- `frontend/src/services/api.ts` — persistencia del refresh rotado.
- `docs/informes/Database_Panaderia_Santiago.sql` — DDL validado y sincronizado.
- `docs/ai/IMPLEMENTATION_PHASES.md` — contrato de CU1 corregido a 400/400/429.
- `docs/ai/DECISIONS_LOG.md` — entrada 5 con el análisis completo.
