# Sesión de Desarrollo: CU21 — diagrama 6.2 de implementación de la arquitectura

- **Fecha:** 2026-11-01
- **Autor / Integrante:** Agente de IA
- **Paquete / Módulo:** `docs` | `apps.reportes`
- **Casos de Uso abordados:** CU21
- **Ciclo:** Ciclo 4

---

## 1. Objetivo de la sesión

Adaptar el diagrama de componentes de implementación (sección 6.2) al reporte de ventas ya construido, con las capas Django/React y las tablas reales del CU21.

## 2. Cambios realizados

- **Documentación:** `docs/4-implementacion/CU21_6.2_implementacion_arquitectura.drawio`.
- **Backend y frontend:** sin cambios de código.

## 3. Decisiones técnicas tomadas

- Se conservó la notación del diagrama de origen: componente UML, carpeta de paquete, tabla, script y flecha punteada de dependencia.
- FastAPI, SQLAlchemy, Alembic y los paquetes de FashionStore se reemplazaron por `config/urls.py`, services de `apps.reportes`, migraciones Django y los paquetes P1, P2, P4 y P5.
- Compras no aparece: el CU21 no lee ni escribe ese paquete.
- Las tablas azules ya existían y el CU21 las lee o, en `bitacora`, solo amplía una acción. Las verdes (`cierre_reporte_ventas` y `linea_cierre_reporte_ventas`) las crea `reportes.0001`.

## 4. Pendientes o siguientes pasos

- Pegar el diagrama en el informe 6.2 y revisar que el tamaño de página quepa en la entrega.

## 5. Cómo probar lo implementado

Abrir `docs/4-implementacion/CU21_6.2_implementacion_arquitectura.drawio` en diagrams.net. La pantalla, el servicio Axios, `config/urls.py`, las cinco capas y la carpeta PostgreSQL deben verse unidas por flechas punteadas.

## Corte 3 — el diagrama es del sistema, no del CU21

La sección 6.2 describe la arquitectura de todo el sistema. El diagrama pasó a `docs/4-implementacion/6.2_implementacion_arquitectura.drawio` y se retiró el archivo centrado en el CU21.

Quedaron las tres capas con los cuatro actores, el dashboard único, los cinco paquetes (CU1 a CU26), el pipeline DRF (URLs, JWT/RBAC, vistas, serializadores, servicios atómicos, ORM y bitácora) y las tablas principales de PostgreSQL.

## Corte 2 — el diagrama queda en tres capas

El texto de la sección 6.2 describe Three-Tier: presentación SPA, API REST con RBAC y transacción, y PostgreSQL. El diagrama se reorganizó en esas tres carpetas. El CU21 sigue siendo el ejemplo concreto: `Authorization: Bearer`, `PuedeGenerarReportes`, `@transaction.atomic` en el cierre, bitácora y las restricciones del cierre. Pérdidas, consumo de materia prima y precios quedan nombrados como responsabilidad de la misma capa de negocio en otros casos de uso.
