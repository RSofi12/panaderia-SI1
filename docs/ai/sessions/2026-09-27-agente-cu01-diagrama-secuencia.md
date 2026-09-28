# Sesión: 2026-09-27 — Agente IA — CU01 Diagrama de Secuencia (Ciclo 1)

## Objetivo
Crear el diagrama de secuencia UML del **CU01 - Iniciar Sesión** para Enterprise Architect,
siguiendo la arquitectura BCE (Actor-Boundary-Control-Entity) y usando como plantilla el script
`CUsecuenciaEA/CU20_diagrama_secuencia_generar_reportes.js`.

---

## Cambios por capa

### 📁 Nuevo archivo creado
| Archivo | Descripción |
|---|---|
| [`ciclo1Secuencia_CU/CU01_diagrama_secuencia_iniciar_sesion.js`](file:///c:/Users/PERSONAL/panaderia-SI1/ciclo1Secuencia_CU/CU01_diagrama_secuencia_iniciar_sesion.js) | Script JScript para EA que genera el diagrama de secuencia del CU01 |

---

## Participantes BCE del CU01

| Rol BCE | Elemento | Nombre en EA |
|---|---|---|
| **Actor** | Todos los roles del sistema | `Usuario` |
| **Boundary** | Formulario React de login | `:LoginPageComponent` |
| **Control** | Vista DRF / SimpleJWT | `:AuthController` |
| **Entity** | Modelo CustomUser | `:Usuario` |
| **Entity** | Modelo AuditLog | `:BitacoraAcceso` |

---

## Flujos modelados

### Flujo Principal (credenciales válidas)
```
1: ingresarCredenciales(username, password)
1.1: POST /api/auth/token/ {username, password}
1.2: buscarUsuario(username)              → :Usuario
1.3: return(usuario_data)                ← :Usuario
1.4: check_password(password, hash)       [auto-llamada en :AuthController]
1.5: generarTokenJWT(usuario)             [auto-llamada en :AuthController]
1.6: registrarAcceso('LOGIN_OK', ...)     → :BitacoraAcceso
1.7: return(registro_guardado)           ← :BitacoraAcceso
1.8: return 200 OK {access_token, refresh_token, rol, username}
1.9: redirigirAlDashboard(rol)
```

### Flujo Alternativo [alt] — credenciales inválidas / usuario inactivo
```
2.1: registrarAcceso('LOGIN_FAIL', ...)   → :BitacoraAcceso
2.2: return(registro_guardado)           ← :BitacoraAcceso
2.3: return 401 Unauthorized {detail: 'Credenciales inválidas'}
2.4: mostrarError('Credenciales inválidas. Intente nuevamente.')
```

---

## Decisiones tomadas

1. **Actor genérico "Usuario":** El CU01 tiene actor "Todos", por lo que se usa un único participante
   `Usuario` que representa a cualquier rol (Administrador, Propietario, Ventas, Producción).
2. **Endpoint real:** `POST /api/auth/token/` de SimpleJWT, coherente con `docs/ai/TECH_STACK.md`.
3. **Auto-llamadas en Controller:** `check_password()` y `generarTokenJWT()` son operaciones internas
   de Django/SimpleJWT; se modelan como mensajes reflexivos sobre `:AuthController` (flechas recursivas).
4. **BitacoraAcceso en ambos flujos:** Tanto el login exitoso como el fallido quedan registrados,
   cumpliendo el requerimiento de auditoría del CU26 que se inicia en el mismo Ciclo 1.
5. **Fragmento `alt` para flujo alternativo:** Posicionado entre coordenadas `y=-420` y `y=-700` del
   canvas de EA, cubriendo los mensajes del flujo de error sin solapar el flujo principal.
6. **Carpeta nueva:** `ciclo1Secuencia_CU/` creada para alojar todos los diagramas del Ciclo 1,
   siguiendo la misma convención de `CUsecuenciaEA/` que ya existía en el proyecto.

---

## Cómo ejecutar en Enterprise Architect

1. Abrir el proyecto `.eapx` en **Enterprise Architect 15+**.
2. Ir al menú **Tools → Scripting → Script Manager**.
3. Crear un nuevo script de tipo **JScript** y pegar el contenido del archivo.
4. (Opcional) Seleccionar el paquete destino en el Project Browser antes de ejecutar.
5. Hacer clic en **Run** — el diagrama se genera y abre automáticamente.

---

## Pendientes

- [ ] Crear los diagramas de secuencia de CU02, CU03, CU04, CU05, CU06, CU26 del Ciclo 1
      en la misma carpeta `ciclo1Secuencia_CU/`.

---

## Estado
✅ CU01 diagrama de secuencia creado y listo para importar en EA.
