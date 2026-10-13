# Sesión de Desarrollo: Diagrama de comunicación CU07

- **Fecha:** 2026-10-13
- **Autor / Integrante:** Equipo Panadería Santiago
- **Paquete / Módulo:** `apps.compras.compra_materia_prima` / documentación
- **Casos de Uso abordados:** CU07
- **Ciclo:** Ciclo 2

---

## 1. 🎯 Objetivo de la sesión
Dejar el diagrama de comunicación UML del CU07 (Registrar compra de materia prima) en formato draw.io, alineado al DDL de `docs/informes/Database_Panaderia_Santiago.sql` y al flujo real de registro.

## 2. 🛠️ Cambios realizados
- **Documentación:**
  - `docs/informes/CU07_diagrama_comunicacion.drawio`: actor Propietario, frontera `ComprasPageView`, control `:CompraController` y entidades Proveedor, MateriaPrima, Compra, DetalleCompra, InventarioMateriaPrima, HistorialPrecioMateriaPrima, MovimientoMateriaPrima y Bitacora.
  - `docs/informes/CU07_diagrama_clases.drawio`: diagrama de clases del CU07 con `<<Interface>>`, `<<Controller>>`, entidades del DDL y la enumeración `TipoMovimiento`.
- **Backend:** sin cambios.
- **Frontend:** sin cambios.

## 3. 🧠 Decisiones técnicas tomadas
- El actor del diagrama es el Propietario, como declara `PACKAGE_CU_MAP.md` para el CU07.
- Los objetos entidad usan los nombres de las tablas del informe SQL que el servicio `registrar_compra` lee o escribe.
- El control agrupa `CompraListCreateView`, `CompraDetailView` y el servicio `registrar_compra`.

## 4. ⚠️ Pendientes o siguientes pasos
- Exportar el diagrama a imagen e insertarlo en el informe del caso de uso.
- Ajustar a mano en draw.io cualquier etiqueta que quede encima de una línea.

## 5. 🧪 Cómo probar lo implementado
- Abrir `docs/informes/CU07_diagrama_comunicacion.drawio` en diagrams.net (Archivo → Abrir).
- Comprobar que el flujo 2 recorre proveedor, materia prima, compra, detalle, inventario, historial, movimiento y bitácora, en ese orden.
- Abrir `docs/informes/CU07_diagrama_clases.drawio` y revisar multiplicidades: compra 1 a 1..* detalles, materia prima 1 a 1 inventario, movimiento usa `TipoMovimiento`.
