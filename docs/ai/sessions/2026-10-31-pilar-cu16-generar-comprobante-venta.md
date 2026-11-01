# Sesión de Desarrollo: CU16 - Generar comprobante de venta

- **Fecha:** 2026-10-31
- **Autor / Integrante:** Pilar
- **Paquete / Módulo:** `apps.comercializacion` (Backend: `apps.comercializacion.ventas`) y `frontend` (`src/apps/dashboard/comercializacion`)
- **Casos de Uso abordados:** CU16 (Generar comprobante de venta), articulado con CU13 (Registrar venta)
- **Ciclo:** Ciclo 3 (Comercialización)
- **Rama:** `pilar-cu16-generar-comprobante-de-venta`

---

## 1. 🎯 Objetivo de la sesión
Implementar de extremo a extremo el **Caso de Uso 16: Generar comprobante de venta** para la Panadería Santiago, permitiendo que tras registrar una venta en mostrador (o al consultarla en el historial de ventas del día), el personal pueda:
1. Visualizar el comprobante detallado con formato de ticket térmico comercial (80mm).
2. Imprimir directamente el ticket en cualquier impresora de tickets o convencional.
3. Descargar el comprobante oficial en formato PDF descargable/imprimible generado en el servidor.
4. Registrar la auditoría de la emisión en la Bitácora del sistema (`EMISION_COMPROBANTE`).

---

## 2. 🛠️ Cambios realizados

### Backend (`backend/apps/comercializacion/ventas/` y `usuarios_seguridad/bitacora/`):
- **Bitácora (`bitacora/models.py`):**
  - Agregada la acción de auditoría `EMISION_COMPROBANTE = 'EMISION_COMPROBANTE', 'Emisión de comprobante de venta'`.
- **Permisos (`ventas/permissions.py`):**
  - Creada la clase de permiso RBAC `PuedeConsultarComprobante` (permite acceso a usuarios con permisos `registrar_ventas`, `generar_reportes`, `gestionar_usuarios`, staff y superusuarios).
- **Selectores (`ventas/selectors.py`):**
  - Creada la función `obtener_comprobante_venta(identificador)` con optimización `prefetch_related('detalles__id_producto')` y `select_related('registrado_por')`. Soporta búsqueda por clave primaria `id_venta` o por `numero_comprobante`.
- **Serializadores (`ventas/serializers.py`):**
  - `ComprobanteDetalleSerializer`: Serializa cada ítem con cantidad, precio unitario, subtotal y nombre del producto.
  - `ComprobanteVentaSerializer`: Expone metadatos de la panadería (razón social, NIT/propietario, dirección en Santa Cruz, teléfonos), nombre del cajero, total de artículos, totales en Bolivianos y referencia Stripe si aplica.
- **Servicio de generación de PDF (`ventas/services/comprobante_pdf.py`):**
  - Generador PDF 1.4 térmico puro en Python (`generar_ticket_pdf_bytes`), que no requiere dependencias binarias externas pesadas (como reportlab o weasyprint), garantizando portabilidad absoluta en cualquier entorno o contenedor Docker. Formato estándar 80mm de ancho.
- **Vistas (`ventas/views.py`):**
  - `VentaComprobanteView`: `GET /api/ventas/<pk>/comprobante/` retorna el payload JSON estructurado. Registra evento en Bitácora.
  - `VentaComprobantePdfView`: `GET /api/ventas/<pk>/comprobante/pdf/` genera y retorna el binario `application/pdf` con encabezados HTTP `Content-Disposition: inline; filename="comprobante_<num>.pdf"`. Registra evento en Bitácora.
- **Rutas (`ventas/urls.py`):**
  - Registrados los endpoints `<int:pk>/comprobante/` y `<int:pk>/comprobante/pdf/`.
- **Pruebas unitarias (`ventas/tests.py`):**
  - Clase `PruebasComprobanteVenta` con 6 pruebas automatizadas:
    1. Autenticación requerida (401 si no hay token).
    2. RBAC requerido (403 si el rol no tiene permisos).
    3. Contrato de datos JSON del comprobante (200 OK con estructura completa).
    4. Manejo de venta inexistente (404 Not Found).
    5. Generación y descarga de PDF (cabecera `%PDF-1.4`, tipo MIME `application/pdf`).
    6. Auditoría automática en Bitácora (`AccionBitacora.EMISION_COMPROBANTE`).

### Frontend (`frontend/src/`):
- **Tipos (`src/types/comprobante.ts`):**
  - Definidas interfaces TypeScript `ComprobanteEmpresa`, `ComprobanteDetalleItem` y `ComprobanteVenta`.
- **Servicios (`src/apps/dashboard/comercializacion/ventas/ventaService.ts`):**
  - Agregados `obtenerComprobante(idVenta: number)` y `descargarPdfComprobante(idVenta: number, numeroComprobante: number)` usando Axios con `responseType: 'blob'`.
- **Componente Visual Ticket (`ComprobanteTicketView.tsx`):**
  - Ticket térmico estilizado con Tailwind CSS, tipografía monospace, detalles de venta, tabla de productos, totales y pie de ticket con información institucional de Panadería Santiago.
- **Modal de Comprobante (`ComprobanteVentaModal.tsx`):**
  - Diálogo modal accesible con estados de carga, manejo de errores, botón de impresión emergente en ventana limpia para tickets de 80mm (`window.print()`) y botón para descargar el PDF oficial.
- **Integración en Registrar Venta (`RegistrarVentaPage.tsx`):**
  - Integrado botón *"Ver / Imprimir Comprobante (CU16)"* en el diálogo de éxito post-venta (`DialogoVentaRegistrada`).
  - Integrada columna *"Comprobante"* en la tabla de *"Ventas de hoy"* para re-imprimir cualquier comprobante del turno.
- **Integración en Panel de Comercialización (`ComercializacionPage.tsx`):**
  - Agregado botón de acción *"Ticket"* en la lista de *"Últimas ventas de hoy"*.

---

## 3. 🧠 Decisiones técnicas tomadas
1. **Generación de PDF sin dependencias pesadas:**
   Para asegurar máxima resiliencia tanto en el entorno restringido de desarrollo como en producción Docker, se diseñó un generador conforme al estándar Adobe PDF 1.4 en Python puro. Produce un archivo PDF ligero (menor a 4 KB) de 80mm de ancho con codificación de texto limpia y streams zlib.
2. **Impresión térmica web amigable:**
   En el frontend, además del PDF, se implementó impresión web directa mediante una ventana emergente que aísla el ticket con `@page { size: 80mm auto; margin: 4mm; }`. Esto evita que se impriman barras laterales, menús o encabezados del navegador.
3. **Auditoría granular:**
   Cada visualización o descarga de comprobante deja registro en `bitacora` con el usuario que lo solicitó, su IP y el ID de la venta consultada.
4. **Respeto a las reglas Git del usuario:**
   Todo el desarrollo se mantuvo estrictamente en la rama de trabajo local `pilar-cu16-generar-comprobante-de-venta`. No se realizó ningún merge con `main` ni push remoto sin previa verificación.

---

## 4. ⚠️ Pendientes o siguientes pasos
- Verificar con el usuario la visualización local en su navegador antes de realizar commit y push a la rama remota.
- Próximo CU del Ciclo 3 según planificación: CU14 (Registrar pedido) o CU17 (Consultar disponibilidad de productos).

---

## 5. 🧪 Cómo probar lo implementado

### Pruebas de Backend:
Ejecutar la suite de pruebas unitarias:
```bash
python scratch/run_cu16_tests.py
```
*(6 de 6 pruebas pasan exitosamente en ~0.06s)*

### Pruebas de Frontend:
Compilación de producción y chequeo de tipos:
```bash
npm --prefix frontend run build
```
*(Compila con éxito en ~1.3s con 0 errores de TypeScript)*

### Pruebas en el Navegador:
1. Iniciar el backend (`python manage.py runserver`) y frontend (`npm run dev`).
2. Iniciar sesión como vendedor (`carlos.vargas` o `miguel.ventas`).
3. Ir a **Comercialización $\rightarrow$ Registrar Venta**.
4. Agregar productos al mostrador y registrar una venta en efectivo o con tarjeta Stripe de prueba.
5. Al confirmarse la venta, en el diálogo aparecerá el botón **"Ver / Imprimir Comprobante (CU16)"**.
6. Clic en el botón: se abre el modal del comprobante.
   - Probar **"Imprimir Ticket"**: se abre la ventana de impresión térmica.
   - Probar **"Descargar PDF"**: se descarga el archivo `comprobante_<numero>.pdf`.
7. En la tabla inferior de "Ventas de hoy", presionar el botón **"Ticket"** de cualquier venta para comprobar la reimpresión.

