# Bitácora de Sesión: Actualización del Diagrama de Componentes de Arquitectura General

**Fecha:** 2026-11-22  
**Autor:** Agente Arquitecto / Antigravity  
**Objetivo:** Actualizar y enriquecer el Diagrama de Componentes de la Arquitectura General (`Arquitectura_General_Componentes.drawio`) bajo el estándar UML 2.5, integrando los nuevos artefactos de reportes/dashboards implementados y la disposición radial de tablas hacia el script de migraciones de la base de datos PostgreSQL.

---

## 1. Cambios Realizados en el Diagrama

1. **Nuevo Contenedor `Reportes y Dashboards` (Sección Derecha Media):**
   - Agregada la carpeta de artefactos vinculada desde el orquestador principal (`config/wsgi.py & manage.py`).
   - Mapeo de artefactos reales generados por el paquete de reportes:
     - Formato PDF (`<<artifact>>`): `reporte-ventas.pdf`, `reporte-produccion.pdf`, `reporte-existencias.pdf`, `reporte-economico.pdf`, `reporte-compras.pdf`.
     - Formato CSV/Excel (`<<artifact>>`): `reporte-ventas.csv`, `reporte-produccion.csv`, `reporte-existencias.csv`, `reporte-economico.csv`, `reporte-compras.csv`.

2. **Reorganización Radial de la Base de Datos PostgreSQL 16 (Sección Inferior):**
   - Servidor `PostgreSQL 16` ubicado en la esquina superior izquierda del contenedor de BD.
   - Componente central `<<Script>> python manage.py migrate (Django Migrations)`.
   - Distribución radial periférica de las 31 tablas físicas del sistema (incluyendo las nuevas tablas de congelamiento de cierres de auditoría: `cierre_reporte_ventas`, `linea_cierre_reporte_ventas`, `cierre_reporte_compras`, `linea_cierre_reporte_compras`).
   - Dependencias UML («use») representadas con flechas discontinuas abiertas orientadas desde cada una de las tablas hacia el componente central de migraciones, y desde este hacia el servidor `PostgreSQL 16`.

3. **Trazabilidad con el Código Fuente:**
   - Frontend SPA / Consumo de endpoints y descargas de reportes.
   - Backend Django REST Framework (Capas: Model, Components/Services, Controlador/Views, Routes, Middleware).
   - Paquetes P1 a P5 alineados con los casos de uso CU1 al CU28.

---

## 2. Archivos Afectados

- [`docs/informes/Arquitectura_General_Componentes.drawio`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Arquitectura_General_Componentes.drawio) (Actualizado y validado sintácticamente).
