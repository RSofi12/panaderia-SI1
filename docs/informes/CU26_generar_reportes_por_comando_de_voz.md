# Caso de uso — CU26 Generar reportes por comando de voz

> **Nota de trazabilidad:** En la matriz PUDS oficial del repositorio, **CU26** está reservado a *Gestionar bitácora* (`usuarios_seguridad`). Este documento describe el **caso de negocio acordado por el equipo** bajo el nombre **«Generar reportes por comando de voz»**, implementado como **extensión transversal del paquete `apps.reportes`** sobre **CU21–CU25**. Si el informe del grupo usa otra numeración, ajustar solo el identificador; el flujo y la implementación son los aquí descritos.

| Elemento | Descripción |
|----------|-------------|
| **Nombre del CU** | **CU26** — Generar reportes por comando de voz |
| **Actor principal** | **Propietario** (Carlos Santiago Vargas) |
| **Actor iniciador** | Propietario (usuario con permiso RBAC `generar_reportes` en sesión activa). |
| **Objetivo** | Permitir solicitar, en **lenguaje natural** (voz o texto), la consulta o descarga de reportes gerenciales (ventas, producción, inventario, compras o resultados económicos), de modo que el sistema interprete el comando, aplique filtros de período y formato, muestre el resultado en pantalla y, cuando corresponda, genere el archivo (PDF, CSV o Excel), **confirmando al usuario con respuesta hablada** cuando el navegador lo permita. |
| **Precondiciones** | 1) El actor ha iniciado sesión con JWT válido. 2) Su rol incluye el permiso `generar_reportes`. 3) El módulo de reportes del caso de uso solicitado está disponible en pantalla (hoy **solo CU21** de extremo a extremo; CU22–CU25 se interpretan en backend). 4) Los datos de ventas u otros dominios ya existen en PostgreSQL para los períodos consultados (no se inventan datos). |
| **Postcondición** | Si hay datos: el reporte queda consultado en pantalla con el rango y filtros inferidos; si el actor pidió descargar y el período tiene registros, el archivo se genera. Si no hay datos: **no** se entrega archivo vacío; el actor recibe el mensaje *«No hay datos disponibles para el período solicitado»* en pantalla y por voz. El comando interpretado no persiste tablas nuevas (servicio sin estado). |
| **Paquete / capa** | `backend/apps/reportes` (`interprete_voz.py`, `views.py`) + `frontend/.../reportes` (`AsistenteVozReporte.tsx`, `ReportesPage.tsx`). |
| **Servicios externos** | API **Gemini** (opcional, `GEMINI_API_KEY`); si falla o no está configurada, **intérprete local** por reglas. **Voz de salida:** API del navegador **Web Speech `speechSynthesis`** (no es audio de Gemini). **Voz de entrada:** Web Speech Recognition (recomendado Chrome/Edge; en otros navegadores, texto escrito). |

---

## Flujo principal

1. El actor accede a la opción **Reportes** del sistema (CU21 u otra pestaña futura).
2. El actor abre el **Asistente de voz y texto** en la pantalla de reportes.
3. El actor dicta o escribe un comando en español (ej.: *«Descarga en PDF las ventas del año 2025 en efectivo»*).
4. El sistema envía el texto a `POST /api/reportes/voz/interpretar/` (autenticado, permiso `generar_reportes`).
5. El backend traduce el comando a JSON estructurado: `caso_uso` (CU21–CU25), `accion` (`consultar` / `descargar`), `formato` (`pdf` / `csv` / `excel` / `pantalla`), `filtros` (`desde`, `hasta`, `metodo_pago`, `columnas`, etc.) y `respuesta_voz` (frase corta para confirmar o preguntar).
6. El frontend aplica filtros en los selectores de la pantalla y consulta el reporte vía `GET /api/reportes/ventas/` (para CU21).
7. **Si el período tiene ventas (`cantidad` > 0):**
   - 7a. El sistema muestra KPIs y tablas actualizados.
   - 7b. Si faltó indicar formato de descarga, muestra tarjeta para elegir **PDF · CSV · Excel**.
   - 7c. Si el comando ya incluía formato y acción descargar, solicita `GET /api/reportes/ventas/pdf/` o `.../csv/` y guarda el archivo.
   - 7d. El sistema reproduce por voz la confirmación (`speechSynthesis`, idioma `es-ES`).
8. **Si el período no tiene registros (`cantidad` = 0):** el sistema informa *No hay datos disponibles para el período solicitado*, **no** descarga archivos y reproduce ese mensaje por voz.

---

## Excepciones

| ID | Nombre | Condición | Comportamiento del sistema |
|----|--------|-----------|----------------------------|
| **A1** | Sin datos en el período | La consulta devuelve `cantidad = 0` (ej. año sin ventas, fecha futura o mal escrita pero válida en API). | Mensaje en pantalla y voz: *No hay datos disponibles para el período solicitado.* No se muestra selector de formato de descarga ni se llama a PDF/CSV (backend responde **400** si se intenta exportar igual). |
| **A2** | Formato no indicado | El actor pide descargar pero no dice PDF, CSV ni Excel. | `requiere_seleccion_formato = true`; tras cargar datos en pantalla, el sistema pregunta por voz/texto y muestra botones PDF · CSV · Excel. |
| **A3** | Datos inválidos de interpretación | El comando no trae `desde`/`hasta` válidos o el texto está vacío. | API **400** en texto vacío; en frontend: error *El comando no trajo un rango de fechas válido* (voz/texto). |
| **A4** | Falta de permiso o sesión vencida | Sin `generar_reportes` o JWT expirado. | **403** / **401**; el asistente no interpreta y se pide volver a iniciar sesión. |
| **A5** | Micrófono no disponible o error de red (reconocimiento) | Navegador sin Web Speech o fallo (ej. Brave con error `network`). | El actor usa el **campo de texto** y chips de sugerencias; la interpretación y la voz de **respuesta** siguen funcionando. |
| **A6** | Módulo de reporte no integrado en pantalla | `caso_uso` CU22–CU25 (`modulo_disponible = false`). | El backend entiende el comando; la pantalla informa que ese reporte aún no está integrado y lee la `respuesta_voz` explicativa (sin descarga automática). |
| **A7** | Falla del motor Gemini | Sin clave, timeout o JSON inválido. | Fallback automático al **intérprete local** (`motor: local`); el flujo continúa con las reglas de palabras clave (hoy, semana, mes, **año YYYY**, PDF/CSV/Excel). |
| **A8** | Cancelación o interrupción | El actor pulsa *Detener* en el micrófono o abandona la pantalla. | Se detiene el reconocimiento; no se llama a interpretar hasta que confirme con *Detener* o envíe texto. |

---

## Reglas de negocio relevantes (defensa técnica)

1. **Interpretación ≠ generación:** Gemini (o el motor local) solo devuelve **texto JSON**; no consulta la base de datos ni genera PDF.
2. **Verificación en datos reales:** La existencia de ventas se valida contra PostgreSQL **después** de interpretar; así se evita decir «descargando…» y generar un PDF del mes equivocado.
3. **Año explícito:** Frases del tipo *«del año 20250»* se mapean a `20250-01-01` … `20250-12-31` (local y corrección sobre respuesta Gemini).
4. **Exportes vacíos prohibidos:** `ReporteVentasPdfView` y `ReporteVentasCsvView` rechazan exportación si `cantidad = 0`.
5. **RBAC:** Mismo permiso que los reportes clásicos (`generar_reportes`); solo Propietario en el diseño académico del negocio.

---

## Trazabilidad con otros casos de uso

| Relación | Caso de uso |
|----------|-------------|
| `<<include>>` | **CU1** Iniciar sesión |
| `<<include>>` | **CU4** Asignar roles y permisos (`generar_reportes`) |
| `<<extend>>` / invoca | **CU21** Generar reporte de ventas (único integrado E2E) |
| Preparado (backend) | **CU22–CU25** (interpretación lista; pantallas pendientes) |
| Auditoría futura | Acciones de descarga podrían registrarse en **bitácora** (CU26 oficial del repositorio). |

---

## Ejemplos de comando → resultado esperado

| Comando (texto) | Resultado esperado |
|-----------------|-------------------|
| *Muéstrame las ventas de hoy* | Consulta CU21 en pantalla; voz de confirmación; KPIs del día. |
| *Descarga en PDF las ventas de este mes* | Si hay ventas: PDF; si no: A1 sin archivo. |
| *Reporte del año 20250 en PDF* | Rango anual 20250; A1 si no hay ventas; **sin PDF**. |
| *Descarga el reporte de existencias en Excel* | CU23 interpretado; A6 en pantalla actual. |

---

*Documento para informe SI-1 — Panadería Santiago. Alineado con implementación en rama `prueba` (commit `aef545f` y posteriores).*