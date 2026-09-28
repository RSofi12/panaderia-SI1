# Sesión de Desarrollo: CU2 — Recuperar contraseña (backend completo)

- **Fecha:** 2026-09-28
- **Autor / Integrante:** opencode (agente de IA)
- **Paquete / Módulo:** `apps.usuarios_seguridad`
- **Casos de Uso abordados:** CU2 (secundariamente CU1 y CU26, al corregir código compartido)
- **Ciclo:** Ciclo 1

---

## 1. 🎯 Objetivo de la sesión

Implementar el backend del CU2 completo: solicitud del enlace por correo, token de un solo uso con expiración, confirmación con contraseña nueva, anti-enumeración, límites de abuso, revocación de sesiones y auditoría.

Alcance acordado: **solo backend**. El frontend se hará en una sesión aparte.

Restricciones pedidas explícitamente:
- Usar un SMTP de pruebas propio, no datos reales.
- Correos de prueba para los actores, no los reales.
- Token de enlace de tamaño mediano (20 caracteres), no un código de 6 dígitos.
- `Usuario.email` debe ser obligatorio, porque es el canal de recuperación.
- Al final, un resumen de cambios y la documentación actualizada.

## 2. 🛠️ Cambios realizados

### Backend — archivos creados

- `backend/apps/usuarios_seguridad/recuperacion/__init__.py`
- `backend/apps/usuarios_seguridad/recuperacion/apps.py`
- `backend/apps/usuarios_seguridad/recuperacion/models.py` — `TokenRecuperacion` (tabla `token_recuperacion`).
- `backend/apps/usuarios_seguridad/recuperacion/admin.py`
- `backend/apps/usuarios_seguridad/recuperacion/services/__init__.py`
- `backend/apps/usuarios_seguridad/recuperacion/services/token.py` — emisión, hash, búsqueda por estado, evaluación de cuota, reserva con lock.
- `backend/apps/usuarios_seguridad/recuperacion/services/correo.py` — `EmailMultiAlternatives`.
- `backend/apps/usuarios_seguridad/recuperacion/services/confirmacion.py` — cambio de contraseña, revocación de sesiones, auditoría, purga.
- `backend/apps/usuarios_seguridad/recuperacion/templates/emails/recuperacion_contrasena.txt`
- `backend/apps/usuarios_seguridad/recuperacion/templates/emails/recuperacion_contrasena.html`
- `backend/apps/usuarios_seguridad/recuperacion/tests.py` — 61 pruebas.

### Backend — archivos modificados

- `auth_app/serializers.py` — `RecuperacionSolicitudSerializer` y `RecuperacionConfirmacionSerializer`.
- `auth_app/views.py` — dos vistas `APIView` sin autenticación, más `RecuperacionSolicitudThrottle` y `RecuperacionConfirmacionThrottle`.
- `auth_app/urls.py` — `password-reset-request/` y `password-reset-confirm/`.
- `auth_app/exceptions.py` — `TokenRecuperacionInvalidoError` y `ContrasenaDebilError`.
- `users/models.py` — `email` con `NOT NULL` y `UniqueConstraint(Lower('email'))`.
- `users/password_validators.py` — **bug preexistente corregido** (ver sección 3.1).
- `configuracion/models.py` — `minutos_expiracion_token`, `max_intentos_token`, `max_solicitudes_por_hora`, con CHECK de rango.
- `configuracion/admin.py` — los tres campos en el panel.
- `bitacora/models.py` — tres acciones nuevas del enum `AccionBitacora`.
- `config/settings.py` — app, `PASSWORD_RESET_URL`, bloque `EMAIL_*`, dos throttle rates.
- `backend/.env.example` — variables de correo y del enlace.
- `users/management/commands/seed_usuarios.py` — correos `*.mail.com` y salida ASCII para no romper la consola de Windows.

### Migraciones aplicadas (4)

| Migración | Qué hace |
|---|---|
| `users/0004_usuario_email_obligatorio` | `RunPython` que aborta con mensaje claro si hay nulos o duplicados, `AlterField` a `NOT NULL` y constraint `Lower('email')`. Escrita a mano porque el `makemigrations` interactivo no puede resolver un cambio de `null=True` a `null=False`. |
| `bitacora/0005_alter_bitacora_accion` | Agrega las tres acciones de CU2 al enum. |
| `configuracion/0003_...max_intentos_token_and_more` | Los tres campos nuevos. |
| `recuperacion/0001_initial` | Tabla `token_recuperacion`. |
| `recuperacion/0002_fk_token_recuperacion_cascade` | Pone real el `ON DELETE CASCADE` de la FK a `usuario`. Ver sección 3.8. |

### Frontend — implementado en la segunda tanda de esta sesión

**Nada.** No se creó ni se modificó ningún archivo. Quedan identificados para la sesión siguiente:
- `src/apps/auth/ForgotPasswordPage.tsx` (nuevo)
- `src/apps/auth/ResetPasswordPage.tsx` (nuevo)
- `src/apps/auth/AppRoutes.tsx` (registrar las dos rutas)
- `src/apps/auth/services/authService.ts` (las dos llamadas)
- `src/apps/auth/types/auth.ts` (los dos tipos de respuesta)
- `src/apps/auth/LoginPage.tsx:196-198` (el `<span>` de "¿Olvidaste tu contraseña?" necesita `onClick`)

> Los seis archivos de arriba son los que se terminaron de hacer después. Se
> listaban con la ruta equivocada: las rutas reales son `src/types/`,
> `src/services/` y `src/routes/AppRoutes.tsx`, porque ese proyecto tiene un solo
> `types/` y un solo `services/` para toda la SPA, no uno por módulo de negocio.

### Contrato de la API

```
POST /api/auth/password-reset-request/
  { "identificador": "mgonzales" }              // usuario o correo
  -> 200 { "message": "Si los datos corresponden a una cuenta activa, te enviamos
           un enlace para restablecer tu contraseña. Revisá tu correo, incluida
           la carpeta de spam." }

POST /api/auth/password-reset-confirm/
  { "token": "A4W2M8D5FN7B7RKDV3AX",
    "nueva_contrasena": "NuevaClave2026!",
    "confirmar_contrasena": "NuevaClave2026!" }
  -> 200 { "message": "...restablecida...", "nombre_usuario": "mgonzales",
           "intentos_consumidos": 1, "intentos_restantes": 4 }
  -> 400 { "error": "..." }   // token inválido o contraseña débil
```

Ambos endpoints son anónimos: quien llega del correo no tiene sesión.

## 3. 🧠 Decisiones técnicas tomadas

### 3.1 `validar_contrasena()` nunca funcionó (bug preexistente)

La función tenía `from django.contrib.auth.password_validation import validate_password` y dentro llamaba `validate_password(contrasena, usuario=usuario)`. Como el nombre local tapaba al import, eso **no era una llamada a Django sino una reentrada a sí misma** con un keyword inexistente: `TypeError` en la primera invocación. Nadie la llamaba, así que el bug llevaba tiempo latente y el CU2 fue el primer consumidor. Se aliaseó el import como `validar_con_politica_de_django` y se invoca con `user=`.

De paso: esto confirma que la política de contraseñas del CU3 ya es utilizable.

### 3.2 El token es de 20 caracteres, no un código de 6 dígitos

Se mantiene el alfabeto de 32 símbolos `23456789ABCDEFGHJKLMNPQRSTUVWXYZ` (5 bits por carácter, ~100 bits), longitud 20, con `secrets.choice()`. Sin `0`/`1`/`I`/`O`/`L` para que no haya confusión al transcribirlo a mano.

El argumento de por qué no 6 dígitos: con 6 dígitos hay 1.000.000 de combinaciones y, sin un límite de intentos por token, la tabla se puede consultar un millón de veces. Además el token en claro queda solo en el correo; la base guarda únicamente el SHA-256, de modo que un dump de la tabla no permite reutilizar ningún enlace.

### 3.3 La cuota por cuenta NO devuelve 429 (se corrigió durante la sesión)

La primera implementación devolvía `429` con `retry_after_seconds` cuando la cuenta agotaba sus solicitudes por hora, con el razonamiento de que ese 429 lo produce la IP y no la existencia de la cuenta. **El razonamiento era falso:** la rama del 429 por cuota solo se alcanza con un usuario real y activo.

El contraejemplo concreto: con `max_solicitudes_por_hora=3`, un atacante que pruebe una lista de correos hace cuatro pasadas. En la cuarta, las direcciones reales devuelven 429 y las inventadas devuelven 200 — o sea, la lista de cuentas válidas que buscaba. Se cambió a devolver el mismo 200 genérico y simplemente no enviar el correo.

Lo que **no** se pierde: la cuota se sigue contando, así que el buzón deja de recibir enlaces; y el atacante se topa igual con el 429 **por IP**, que sí es seguro porque depende de la IP del solicitante y no de la existencia de la cuenta.

### 3.4 El lock tiene que abarcar el cambio de contraseña

`reclamar_token()` ya tenía su propio `@transaction.atomic` con `SELECT ... FOR UPDATE`, pero eso no cerraba la carrera: al retornar **hacía commit y soltaba el lock**, y recién después se escribía la contraseña. Dos peticiones simultáneas con el mismo enlace podían ambas reservar el token y ambas aplicar su cambio; la segunda pisaba la clave de la primera.

La solución es un `transaction.atomic()` en `RecuperacionConfirmacionSerializer.save()` que envuelve la reserva y la aplicación. Anidado así, el `atomic` interno se degrada a savepoint y el lock se mantiene hasta que la contraseña quedó escrita.

**Ojo con el alcance de esta corrección:** está razonada correctamente, pero **no está verificada por una prueba automatizada**. La suite corre sobre SQLite en memoria, donde cada hilo tiene su propia conexión, así que una prueba de concurrencia real daría un falso positivo. Se dejó anotado en `PruebasConfirmacionExitosa` y en la deuda técnica de `CURRENT_STATE.md`.

### 3.5 Recuperar levanta el bloqueo de cuenta y revoca sesiones

Un usuario que se bloquea por olvidar la contraseña justo después de varios intentos quedaría en un círculo sin salida: no entra y no puede recuperar. Además, si alguien se metió con la contraseña vieja, conservar su sesión significaría que el atacante sigue adentro aunque la víctima ya haya cambiado la clave. Por eso al restablecer se ponen a cero `intentos_fallidos`, `bloqueado_hasta` y `ultimo_intento_fallido`, y se mandan todos los refresh tokens vivos a la lista negra (las tablas ya existían por `BLACKLIST_AFTER_ROTATION` de CU1).

### 3.6 Una contraseña débil NO consume intento del token

El contador de intentos frena a alguien que robó un enlace y prueba claves sin parar. Una contraseña corta no es un intento de adivinar, es un error de tecleo. Cobrarle el enlace al usuario por escribir mal le quitaría la mitad de las recuperaciones.

### 3.7 Correcciones de contrato de error y robustez

- `ContrasenaDebilError` pasaba un `detail` de texto plano, que DRF convertía en `{"detail": ...}`. El módulo de excepciones ya decía que todo error de autenticación devuelve `{"error": "..."}`, así que se envuelve en `{'error': mensaje}` para no romper el `setError()` del frontend.
- `auditar_token_rechazado()` dereferenciaba `fila.id_token` fuera del condicional que sí protegía `fila.usuario` e `fila.intentos`. Con un token inexistente —un caso esperado— la petición terminaba en 500 y el rechazo ni siquiera llegaba a bitácora.

### 3.8 La FK a `usuario` NO tenía cascada en la base (y Django no lo veía)

Al contrastar el DDL con el esquema real apareció que `token_recuperacion.usuario_id` estaba en `NO ACTION`, aunque el modelo y el archivo `0001_initial` declaraban `CASCADE`. Dos motivos por los que nadie lo notó:

1. `makemigrations` compara el modelo contra el **archivo** de migraciones, no contra el esquema real. Si el archivo se corrige después de aplicado, Django sigue viéndolos de acuerdo y responde "No changes detected".
2. Escribiendo la `AlterField` a mano, Django la emite como **no-op**: para su editor de esquemas, `on_delete` es una preocupación de Python, no un parámetro de base de datos. Se confirmó con `sqlmigrate`, que devolvió `-- (no-op)`.

Mientras dure esa diferencia, la cascada solo ocurría al borrar desde el ORM de Django, que borra los tokens relacionados en Python antes de emitir el `DELETE`. Un `DELETE` por SQL crudo fallaba con violación de llave foránea, y un token huérfano podía reiniciar el reloj de un enlace viejo.

La corrección es la migración `0002_fk_token_recuperacion_cascade`, escrita con `RunPython` y SQL explícito porque el caso es precisamente uno que Django no sabe expresar. Dos detalles que costaron un rato:

- El `DROP` no fija el nombre de la constraint, porque Django la genera con un hash que depende del entorno: se busca en `pg_constraint` la FK que realmente apunta a `usuario`. El nombre nuevo sí es fijo.
- Es `RunPython` y no `RunSQL` **a propósito**: el SQL es de PostgreSQL y la suite corre sobre SQLite, donde un `RunSQL` a secas revienta con `near "DO": syntax error`. La función mira el vendor y no hace nada en otros motores.

Queda una trampa aceptada: si alguien corre la suite sobre otro motor creyendo que todo está verificado, la cascada a nivel de base no existe. El proyecto es PostgreSQL-only.

Verificado sobre PostgreSQL: tras un `DELETE FROM usuario` por SQL crudo, quedan **0 tokens huérfanos** (`confdeltype = 'c'`).

## 4. ⚠️ Pendientes o siguientes pasos

1. **Frontend del CU2** (lo más importante para que el flujo sea usable): los 6 archivos listados en la sección 2.
2. **Levantar Mailpit o configurar un SMTP de pruebas.** Ahora mismo `EMAIL_BACKEND=smtp` apunta a `localhost:1025` y no hay nada escuchando, así que el envío real fallaría.
3. ~~**Verificar el lock de 3.4 sobre PostgreSQL**~~ → **Hecho.** Dos conexiones reales, una gana y la otra se rechaza, ambas auditadas. La verificación destapó un bug extra: el `raise` de conflicto estaba dentro del `transaction.atomic()`, así que el rollback borraba el registro de bitácora del rechazo (decisión 13 del `DECISIONS_LOG.md`). Cubierto por `PruebasConcurrenciaReal` (solo PostgreSQL) y `PruebasAuditoriaAnteConflicto` (cualquier motor).
4. Decidir si la falta de feedback en el caso de cuota agotada (3.3) molesta en la práctica. La salida sería un aviso dentro del propio correo, nunca un 429.
5. Lo pendiente de la sesión anterior: quitar `generar_reportes` al Personal de Ventas en `seed_usuarios.py`, y extraer el panel de credenciales demo del `LoginPage` a un componente reutilizable condicionado a `import.meta.env.DEV`.

## 5. 🧪 Cómo probar lo implementado

### Suite automatizada

El usuario de PostgreSQL no tiene `CREATEDB`, así que `manage.py test` no puede crear la base de pruebas. Se usa un módulo de settings alterno sobre SQLite:

```powershell
cd backend
$env:PYTHONPATH = "C:\Users\PERSONAL\AppData\Local\Temp\opencode"
.\venv\Scripts\python.exe manage.py test --settings=settings_test_sqlite
```

Resultado actual: **92 pruebas, todas en verde** (31 de CU1 + 61 de CU2; 1 se salta porque exige PostgreSQL). El ajuste de `settings_test_sqlite.py` vive fuera del repositorio a propósito, para no ensuciar el proyecto con un módulo que solo sirve para correr tests en esta máquina.

Solución definitiva para el equipo: `ALTER ROLE <usuario> CREATEDB;` en PostgreSQL.

### Comprobaciones de integridad

```powershell
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run   # -> No changes detected
.\venv\Scripts\python.exe manage.py check                                # -> no issues
```

### Prueba manual contra la base real

El flujo se verificó extremo a extremo contra PostgreSQL con el backend de consola (para poder leer el correo sin depender de Mailpit), y después se restauró la contraseña original y se borraron los tokens de prueba. Quedó confirmado que:

- una cuenta inexistente no recibe correo y devuelve el mismo cuerpo que una real;
- el correo sale multipart y el enlace trae un token de 20 caracteres;
- en la base solo queda el hash;
- confirmar con un token inventado da 400 controlado;
- confirmar con el token bueno cambia la contraseña y responde `intentos_consumidos: 1`;
- reutilizar el mismo enlace da 400.

### Datos de prueba

Los seis usuarios del seed usan correos del dominio reservado `mail.com` (RFC 2606) para que ningún correo salga a internet:

| Usuario | Correo |
|---|---|
| `admin` | admin.global@mail.com |
| `csantiago` | santiago.prop@mail.com |
| `mgonzales` | gonzales.ventas@mail.com |
| `jrivera` | rivera.ventas@mail.com |
| `mrojas` | rojas.produccion@mail.com |
| `ptorrez` | torrez.produccion@mail.com |

---

# Segunda tanda (mismo día, mismo autor): frontend del CU2, purga y Mailpit

## 6. 🎯 Objetivo de la segunda tanda

Tres cosas, en este orden de prioridad:

1. Terminar el frontend del CU2, que era el bloqueo real para poder probarlo.
2. Reemplazar la idea de Celery por un comando de gestión. El usuario fue
   explícito: **no instalar Celery**.
3. Dejar Mailpit descargado y listo para levantar, para probar el envío real.

Restricción del usuario: **no ejecutar build, lint ni pruebas** por ahora; la
validación va a ser manual al levantar el proyecto.

## 7. 🛠️ Cambios de la segunda tanda

### Frontend — archivos creados

| Archivo | Qué hace |
|---|---|
| `src/apps/auth/components/AuthCard.tsx` | Envoltura visual compartida por login, recuperar y restablecer. |
| `src/apps/auth/components/PasswordRequirements.tsx` | Checklist vivo de la política; exporta `evaluarReglas` y `cumplePoliticaVisible`. |
| `src/apps/auth/ForgotPasswordPage.tsx` | Paso 1: pide el enlace y muestra el mensaje genérico. |
| `src/apps/auth/ResetPasswordPage.tsx` | Paso 2: lee el token de la URL, muestra la política y confirma. |

### Frontend — archivos modificados

- `src/types/auth.ts` — `SolicitudRecuperacion`, `ConfirmacionRecuperacion`,
  `RespuestaSolicitud`, `RespuestaConfirmacion` y `ErrorRecuperacion`.
- `src/services/authService.ts` — `solicitarRecuperacion()` y
  `confirmarRecuperacion()`.
- `src/routes/AppRoutes.tsx` — las dos rutas públicas.
- `src/apps/auth/LoginPage.tsx` — usa `AuthCard`, el `<span>` que parecía enlace
  pasó a ser `<Link>`, y el panel de cuentas demo quedó condicionado a
  `import.meta.env.DEV`.

### Backend — archivos creados

- `apps/usuarios_seguridad/recuperacion/management/__init__.py`
- `apps/usuarios_seguridad/recuperacion/management/commands/__init__.py`
- `apps/usuarios_seguridad/recuperacion/management/commands/purgar_tokens_vencidos.py`

### Fuera del repositorio

- `C:\Users\PERSONAL\tools\mailpit\mailpit.exe` — Mailpit v1.31.3 portable.

## 8. 🧠 Decisiones de la segunda tanda

### 8.1 Sin Celery: un comando de gestión

Celery se descartó por indicación del usuario. La purga de tokens vencidos no
necesita una cola: es un `UPDATE` que corre una vez por hora y del que nadie
espera respuesta. Un comando de gestión cubre el caso sin agregar Redis, un
worker, ni un archivo de tareas que mantener.

```
python manage.py purgar_tokens_vencidos            # borra
python manage.py purgar_tokens_vencidos --dry-run  # solo cuenta
python manage.py purgar_tokens_vencidos -v 2       # detalle por token
```

Para que corra sola en Windows, Programador de tareas con la acción
`venv\Scripts\python.exe manage.py purgar_tokens_vencidos` y disparador diario.

**Lo que el comando NO hace** (y conviene tenerlo presente si se lo defendemos):
la expiración ya la aplica `buscar_por_token()` en cada confirmación, así que
borrar filas viejas es higiene, no seguridad. Un token vencido no sirve aunque su
fila siga ahí.

### 8.2 El token se borra de la barra de direcciones

`ResetPasswordPage` lee el token del query string una sola vez y enseguida
reescribe la URL con `replaceState`. El token es una credencial: si queda en la
barra se guarda en el historial del navegador y puede filtrarse por `Referer`.

El efecto tiene `searchParams` fuera de las dependencias **a propósito**: la
limpieza de la URL cambia `searchParams`, y si fuera una dependencia el efecto
se volvería a disparar en bucle. Va con el `eslint-disable` de
`exhaustive-deps` y un comentario que explica por qué.

Consecuencia asumida: recargar la página **no** reintenta el envío, cae en el
estado "enlace incompleto". Es el comportamiento correcto; el texto de ese
estado explica que el código se borra a propósito y hay que pedir uno nuevo.

### 8.3 `ForgotPasswordPage` redirige si hay sesión; `ResetPasswordPage` no

En el paso 1, si ya hay sesión abierta no hay contraseña que olvidar, así que se
manda al dashboard, igual que hace `LoginPage`.

En el paso 2 **no** se hace, y es deliberado: la persona llega por el enlace del
correo y puede tener sesión abierta en ese mismo navegador. El token ya prueba
que es dueña del buzón, y además el backend le revoca las sesiones al confirmar,
que es justo lo que se quiere si alguien más las tenía abiertas.

### 8.4 Los errores van a dos lugares distintos

El backend devuelve tres formas de error y la pantalla tiene que distinguirlas:
`{campo: [msg]}` del serializador se pega al input, `{error: "..."}` de las
excepciones propias va arriba, y `{error: [...]}` de contraseña débil va arriba
porque el checklist ya muestra cada regla.

### 8.5 El checklist de contraseñas es un espejo, no la fuente de verdad

`PasswordRequirements` reimplementa las cuatro reglas de
`ComplexPasswordValidator` porque son dos lenguajes distintos. `AUTH_PASSWORD_VALIDATORS`
tiene **cuatro** validadores, no uno: también `CommonPasswordValidator` y
`UserAttributeSimilarityValidator`, que dependen de datos que el navegador no
tiene. Por eso el componente dice explícitamente que el servidor revisa además
esas dos, en vez de declarar "contraseña válida" con un `✓` que después el
servidor desmiente.

Se verificó que el conjunto de símbolos del regex del frontend es el mismo del
backend: `!@#$%^&*(),.?":{}|<>=_+\-/[]`.

### 8.6 El panel de cuentas demo se oculta en producción

`import.meta.env.DEV` se reemplaza por `false` al compilar, así que Vite elimina
el código y del bundle servido no queda ni el texto. El panel publicaba usuarios
y la contraseña real en pantalla; en producción era una puerta abierta para
cualquiera que llegara a `/login`.

## 9. ⚠️ Pendientes al cerrar esta tanda

1. **Nada verificado en el frontend.** Por indicación del usuario no se corrieron
   `npm run build`, `npm run lint` ni `tsc`. Los archivos nuevos se revisaron
   leyéndolos contra el backend, no ejecutándolos.
2. `purgar_tokens_vencidos` **no se ejecutó ni una vez**, ni siquiera en `--dry-run`.
3. Mailpit está descargado pero **no corriendo**; el envío SMTP real sigue sin
   verificarse.
4. Sigue pendiente quitar `generar_reportes` al Personal de Ventas en
   `seed_usuarios.py`.
5. Sigue pendiente decidir si la falta de feedback en el caso de cuota agotada
   (sección 3.3) molesta en la práctica.

## 10. 🧪 Cómo probar a mano el flujo completo

```powershell
# 1. Mailpit (dejar esta terminal abierta)
C:\Users\PERSONAL\tools\mailpit\mailpit.exe --smtp 0.0.0.0:1025 --listen 0.0.0.0:8025

# 2. backend\.env: agregar el bloque de correo (ver sección 11)

# 3. Levantar backend y frontend, entrar a http://localhost:5173/login
#    y hacer clic en "¿Olvidaste tu contraseña?"
# 4. En http://localhost:8025 aparece el correo con el enlace.
#    Ojo: el enlace apunta a localhost:5173, no a la bandeja de Mailpit.
# 5. Cambiar la contraseña, volver a /login con la nueva y confirmar.
# 6. Reusar el mismo enlace: tiene que dar 400 controlado.
```

## 11. 📄 Configuración de `backend/.env` para Mailpit

El `.env` actual solo tiene claves de base de datos. Hay que agregarle:

```ini
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=False
EMAIL_TIMEOUT=10
PASSWORD_RESET_URL=http://localhost:5173/recuperar-password/nueva
```

`EMAIL_USE_TLS=False` porque Mailpit habla SMTP en claro en el 1025, igual que
un servidor local de pruebas. En un SMTP real de internet esto va en `True`.
