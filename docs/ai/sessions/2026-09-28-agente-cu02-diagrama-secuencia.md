# Sesión: 2026-09-28 — Agente IA — CU02 Diagrama de Secuencia (Ciclo 1)

## Objetivo
Crear el diagrama de secuencia UML del **CU02 - Recuperar Contraseña** para Enterprise Architect,
siguiendo la arquitectura BCE (Actor-Boundary-Control-Entity) y el mismo formato JScript de CU01
en la carpeta `ciclo1Secuencia_CU/`.

---

## Cambios por capa

### 📁 Nuevo archivo creado
| Archivo | Descripción |
|---|---|
| [`ciclo1Secuencia_CU/CU02_diagrama_secuencia_recuperar_contrasena.js`](file:///c:/Users/PERSONAL/panaderia-SI1/ciclo1Secuencia_CU/CU02_diagrama_secuencia_recuperar_contrasena.js) | Script JScript para EA que genera el diagrama de secuencia del CU02 |

---

## Participantes BCE del CU02

| Rol BCE | Elemento EA | Descripción |
|---|---|---|
| **Actor** | `Usuario` | Cualquier actor que olvidó su contraseña |
| **Boundary** | `:RecuperarPasswordPageComponent` | Formulario solicitud + formulario confirmación (React/TypeScript) |
| **Control** | `:PasswordResetController` | Lógica de generación, validación e invalidación del token |
| **Entity** | `:Usuario` | Modelo `CustomUser` — búsqueda y actualización del hash |
| **Entity** | `:TokenRecuperacion` | Modelo `PasswordResetToken` — token temporal con TTL de 1 hora |
| **Entity** | `:BitacoraAcceso` | Modelo `AuditLog` — auditoría de cada evento de recuperación |

---

## Flujos modelados

### Flujo 1: Solicitud de recuperación (`POST /api/auth/password-reset/`)
```
1:    solicitarRecuperacion(username)
1.1:  POST /api/auth/password-reset/ {username}
1.2:  buscarUsuario(username)                         → :Usuario
1.3:  return(usuario_data)                           ← :Usuario
1.4:  generarTokenTemporal()   [reflexivo en Controller]
1.5:  crearToken(usuario_id, token_uid, expires_at)   → :TokenRecuperacion
1.6:  return(token_guardado)                         ← :TokenRecuperacion
1.7:  registrarAcceso('PASSWORD_RESET_REQUEST', ...)  → :BitacoraAcceso
1.8:  return(registro_guardado)                      ← :BitacoraAcceso
1.9:  return 200 OK {mensaje, token_uid}
1.10: mostrarMensaje('Ingrese el token recibido...')
```

### Flujo 2: Confirmación con nueva contraseña (`POST /api/auth/password-reset/confirm/`)
```
2:    confirmarReset(token_uid, nueva_password)
2.1:  POST /api/auth/password-reset/confirm/ {token_uid, nueva_password}
2.2:  buscarToken(token_uid)                          → :TokenRecuperacion
2.3:  return(token_data: {usuario_id, expires_at, usado}) ← :TokenRecuperacion
2.4:  validarToken(token_data)  [reflexivo en Controller]
```

### Flujo Alternativo [alt] — token inválido o expirado
```
2.5a: registrarAcceso('RESET_TOKEN_INVALID', ...)    → :BitacoraAcceso
2.6a: return(registro_guardado)                     ← :BitacoraAcceso
2.7a: return 400 Bad Request {detail: 'Token inválido o expirado'}
2.8a: mostrarError('El token es inválido o ha expirado. Solicite uno nuevo.')
```

### Flujo 2 (continuación — token válido):
```
2.5:  hashearPassword(nueva_password)  [reflexivo en Controller]
2.6:  actualizarPassword(usuario_id, nueva_password_hash)  → :Usuario
2.7:  return(password_actualizado)                        ← :Usuario
2.8:  invalidarToken(token_uid)                            → :TokenRecuperacion
2.9:  return(token_invalidado)                            ← :TokenRecuperacion
2.10: registrarAcceso('PASSWORD_RESET_OK', ...)            → :BitacoraAcceso
2.11: return(registro_guardado)                           ← :BitacoraAcceso
2.12: return 200 OK {mensaje: 'Contraseña restablecida correctamente'}
2.13: redirigirALogin(...)
```

---

## Decisiones tomadas

1. **Dos flujos en un solo diagrama:** El CU02 tiene dos pasos naturales (solicitar reset y
   confirmar con token). Se modelan como Flujo 1 y Flujo 2 dentro del mismo diagrama de secuencia
   para mantener la narrativa completa del caso de uso.
2. **TokenRecuperacion como entidad propia:** El token temporal se persiste en BD
   (`PasswordResetToken`) con `usuario_id`, `token_uid` (UUID), `expires_at` y `usado=False`.
   Esto permite invalidarlo tras el primer uso y detectar tokens expirados.
3. **TTL de 1 hora:** Decisión de seguridad estándar para tokens de reset. En entorno local
   el token se devuelve en la respuesta HTTP; en producción se enviaría por email.
4. **Fragmento `alt` para token inválido:** Cubre tres casos: token inexistente, token ya usado,
   token expirado (`expires_at < now()`). Se registra el intento en bitácora en todos los casos.
5. **`make_password()` de Django:** El hasheo de la nueva contraseña es una auto-llamada
   (mensaje reflexivo) sobre `:PasswordResetController`, consistente con cómo Django gestiona
   internamente el hashing (PBKDF2/argon2).
6. **BitacoraAcceso en cada evento:** Se registran tres eventos: `PASSWORD_RESET_REQUEST`,
   `RESET_TOKEN_INVALID` y `PASSWORD_RESET_OK`, cumpliendo la auditoría del CU26.

---

## Cómo ejecutar en Enterprise Architect

1. Abrir el proyecto `.eapx` en **Enterprise Architect 15+**.
2. Ir a **Tools → Scripting → Script Manager**.
3. Crear un nuevo script de tipo **JScript** y pegar el contenido del archivo.
4. (Opcional) Seleccionar el paquete destino en el Project Browser antes de ejecutar.
5. Hacer clic en **Run** — el diagrama se genera y abre automáticamente.

---

## Pendientes

- [ ] CU03 Gestionar usuarios — Ciclo 1
- [ ] CU04 Asignar roles y permisos — Ciclo 1
- [ ] CU05 Gestionar productos — Ciclo 1
- [ ] CU06 Gestionar proveedores — Ciclo 1
- [ ] CU26 Gestionar bitácora — Ciclo 1

---

## Estado
✅ CU01 diagrama de secuencia — completado (sesión anterior)
✅ CU02 diagrama de secuencia — completado en esta sesión
