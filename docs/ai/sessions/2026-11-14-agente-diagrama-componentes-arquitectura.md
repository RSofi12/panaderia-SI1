# Bitácora de Sesión: Diagrama de Componentes de Arquitectura (UML 2.5)

**Fecha:** 2026-11-14  
**Autor:** Agente Arquitecto / Antigravity  
**Objetivo:** Diseñar y generar el Diagrama de Componentes de la Arquitectura General del Sistema Panadería Santiago en formato Draw.io (`.drawio`), basándose en el estándar UML 2.5, la estructura real del código fuente (Django REST Framework y PostgreSQL) y el modelo de referencia visual establecido.

---

## 1. Contexto y Requerimientos

- El equipo contaba con un borrador inicial en `diagramasUML-panaderia/4-implementacion/6.2_implementacion_arquitectura.drawio`.
- Se solicitó alinear la arquitectura de componentes al formato, diseño y paleta de colores de la referencia institucional (`Arquitectura_General_Componentes.drawio`), mapeando con precisión los artefactos reales de Panadería Santiago.
- Destino del archivo: [`docs/informes/Arquitectura_General_Componentes.drawio`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Arquitectura_General_Componentes.drawio).

---

## 2. Estructura y Distribución de Componentes

1. **Capas Base de la API REST (Columna Izquierda - Azul `#b1ddf0`):**
   - `Model`: `backend/apps/*/models.py` (Django ORM).
   - `Components`: `backend/apps/*/services/` (Lógica de negocio y servicios transaccionales `@transaction.atomic`).
   - `Controlador`: `backend/apps/*/views.py` (APIViews y ViewSets REST).
   - `Routes`: `backend/config/urls.py` & `apps/*/urls.py` (Enrutamiento modular bajo `/api/`).
   - `Middleware`: `backend/config/settings.py` (CORS, JWT Bearer Token, Middleware de Bitácora).

2. **Artefactos Centrales de la API REST (Columna Central - Salmón `#fad9d5`):**
   - `auth_views.py`: Login REST · `POST /api/usuarios/login/` con emisión de tokens JWT.
   - `config/wsgi.py & manage.py`: Orquestador principal de Django 5 y Django REST Framework.
   - `config/settings.py (DATABASES)`: Configuración del conector `psycopg2` para PostgreSQL (Render / Docker con SSL).

3. **Paquetes Arquitectónicos del Sistema (Columna Derecha - Carpetas `#fff2cc`):**
   - `P1. Usuarios y Seguridad` (CU1–CU4, CU26).
   - `P2. Productos e Inventario` (CU5, CU8–CU12, CU18, CU19).
   - `P3. Compras y Proveedores` (CU6, CU7, CU20).
   - `P4. Comercialización` (CU13–CU17).
   - `P5. Reportes y Analítica` (CU21–CU25).

4. **Contenedor Base de Datos (Sección Inferior - Carpeta `#fff2cc`):**
   - Componente Servidor: `PostgreSQL 16` (`#f8cecc`, Servidor Cloud Render con ACID).
   - Componente Script: `<<Script>> python manage.py migrate` (`#e1d5e7`, Django Migrations).
   - Componentes Tablas (`<<Table>>`, `#dae8fc`): Las 29 tablas físicas del sistema (`usuario`, `rol`, `permiso`, `rol_permiso`, `bitacora`, `configuracion_seguridad`, `token_recuperacion`, `categoria_producto`, `producto`, `producto_materia_prima`, `historial_precio_producto`, `materia_prima`, `historial_precio_materia_prima`, `inventario_materia_prima`, `movimiento_materia_prima`, `produccion`, `detalle_produccion`, `inventario_producto_terminado`, `movimiento_producto_terminado`, `nota_perdida_producto`, `proveedor`, `compra`, `detalle_compra`, `movimiento_economico`, `cliente`, `pedido`, `detalle_pedido`, `venta`, `detalle_venta`).

5. **Relaciones UML 2.5:**
   - Dependencias de uso representadas con líneas discontinuas y punta abierta (`dashed=1;endArrow=open;endFill=0;`).

---

## 3. Verificación

- Se validó la sintaxis XML mediante parser de PowerShell confirmando estructura limpia, sin nodos duplicados y lista para abrir directamente en diagrams.net (Draw.io).
