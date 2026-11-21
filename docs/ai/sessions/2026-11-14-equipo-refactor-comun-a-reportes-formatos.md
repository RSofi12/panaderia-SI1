# Bitácora de Sesión: Reubicación de apps.comun a apps.reportes.formatos

- **Fecha:** 2026-11-14
- **Autor:** Equipo de Desarrollo / Antigravity AI
- **Casos de Uso relacionados:** CU07 (Compras PDF/CSV), CU11 (Producción PDF/CSV), CU21 a CU25 (Reportes y Estadísticas).
- **Enfoque de arquitectura:** Estricto cumplimiento de los 5 paquetes modulares de `PACKAGE_CU_MAP.md`.

---

## 1. Objetivo de la Sesión
Eliminar la carpeta huérfana y desacoplada `backend/apps/comun`, reubicando de forma limpia y segura los módulos de exportación de reportes (PDF con ReportLab, CSV y assets de marca) dentro del paquete oficial `backend/apps/reportes/formatos/`, actualizando todas las referencias dependientes en los módulos de compras y producción.

---

## 2. Cambios Implementados

### Backend
1. **Reubicación de Archivos:**
   - De: `backend/apps/comun/`
   - A: `backend/apps/reportes/formatos/`
     - `pdf_reporte.py` (Generación de hojas de cálculo, tablas y encabezados con el logotipo oficial).
     - `csv_reporte.py` (Exportación en formato delimitado por comas con codificación UTF-8 BOM).
     - `assets/circle-logo-panaderia.png` (Isotipo institucional usado en los membretes).
   - Se eliminó completamente la carpeta raíz `backend/apps/comun/`.

2. **Actualización de Importaciones:**
   - **`backend/apps/reportes/services/exportar_reporte.py`:**
     - Cambiado a `from apps.reportes.formatos.csv_reporte import dinero_local`
     - Cambiado a `from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible`
   - **`backend/apps/compras/compra_materia_prima/exportar_compra.py`:**
     - Cambiado a `from apps.reportes.formatos.csv_reporte import archivo_csv, dinero_local`
     - Cambiado a `from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible`
   - **`backend/apps/productos_inventario/produccion/exportar_produccion.py`:**
     - Cambiado a `from apps.reportes.formatos.csv_reporte import archivo_csv, dinero_local`
     - Cambiado a `from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible`

---

## 3. Verificación Automatizada
Se ejecutó la suite de tests de exportación y reportes de los 3 paquetes afectados:
```powershell
python backend/manage.py test apps.reportes apps.compras.compra_materia_prima apps.productos_inventario.produccion --noinput
```
**Resultado:**
```text
Ran 43 tests in 17.943s
OK
```
Todas las 43 pruebas unitarias y de integración pasaron con **100% de éxito**.
