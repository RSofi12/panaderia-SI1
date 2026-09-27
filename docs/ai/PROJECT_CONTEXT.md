# Contexto General del Proyecto

## Sistema de Información Web para la Gestión de Ventas, Producción, Inventario y Control Administrativo
### **Panadería "Santiago"** — Santa Cruz de la Sierra, Bolivia

---

## 1. Introducción y Antecedentes del Negocio

La **Panadería Santiago** es una empresa privada ubicada en el Cuarto Anillo, calle Surubí, en la ciudad de Santa Cruz de la Sierra. Surgió como un emprendimiento familiar y, con el transcurso del tiempo, fue incrementando sus niveles de producción y diversificando su catálogo de productos.

Actualmente, la panadería elabora y comercializa diariamente una amplia variedad de panes tradicionales y especiales, entre los que destacan:
- **Panes salados y tradicionales:** Marraqueta, Chama, Casero, Tortilla, Integral, Arani.
- **Panes dulces y especiales:** Gusanito, Pan con azúcar, Pan dulce, Pan mollete, Pan galleta y Pan de leche.

La producción se realiza todos los días para abastecer la venta fresca en mostrador y atender solicitudes o pedidos especiales. Los cobros a clientes se realizan mediante **efectivo** y transferencias electrónicas mediante **código QR**.

---

## 2. Descripción del Problema y Justificación

### 2.1. Diagnóstico del Estado Actual
El negocio opera actualmente bajo un esquema tradicional de **gestión manual basada en papel**:
1. **Registros en cuadernos y notas físicas:** Las ventas diarias, la producción por jornada, las compras a proveedores y los gastos operativos menores se asientan de manera manuscrita en cuadernos.
2. **Cálculos manuales y uso de calculadora:** Para determinar el dinero recaudado en la jornada, conciliar pagos QR vs. efectivo, o calcular el margen de ganancia semanal/mensual, el propietario realiza sumas manuales susceptibles a errores aritméticos o de transcripción.
3. **Desconexión entre áreas (Ausencia de integración):**
   - Una compra de insumos no incrementa automáticamente el inventario de materia prima.
   - El registro de producción no deduce automáticamente los insumos consumidos (harina, levadura, azúcar, huevos, etc.) ni da de alta automáticamente las existencias de pan horneado.
   - Una venta en mostrador no descuenta el stock de producto terminado en tiempo real.
4. **Dificultad de consulta y toma de decisiones:** Obtener datos históricos (ej. *¿cuál fue la merma del mes pasado?*, *¿qué producto tiene mayor margen de ganancia?*, *¿cuándo reponer harina antes de desabastecimiento?*) exige revisar decenas de hojas físicas.

### 2.2. Justificación de la Solución
El desarrollo e implementación de este sistema web automatizado y centralizado resuelve la problemática al:
- **Centralizar la información:** Disponer de una base de datos relacional (PostgreSQL) robusta, consistente y normalizada.
- **Garantizar la trazabilidad del flujo de negocio:** Conectar el ciclo productivo integral:
  $$\text{Compras/Proveedores} \longrightarrow \text{Stock Materia Prima} \longrightarrow \text{Producción} \longrightarrow \text{Stock Producto Terminado} \longrightarrow \text{Venta/Pedido} \longrightarrow \text{Resultados Económicos}$$
- **Disminución del error humano:** Automatización de cálculos de costos, subtotales, inventarios, alertas de stock mínimo y reportes financieros.
- **Acceso seguro basado en roles:** Control de acceso granular para que cada miembro del personal interactúe únicamente con las opciones necesarias para su puesto.

---

## 3. Objetivos del Proyecto

### 3.1. Objetivo General
Desarrollar un sistema de información web para la gestión de ventas, producción, inventario y control administrativo para la Panadería "Santiago", que optimice y centralice el control operativo y financiero de la empresa.

### 3.2. Objetivos Específicos
1. **Relevar y modelar:** Recopilar y analizar los requisitos funcionales y no funcionales del negocio utilizando la metodología PUDS y diagramas UML.
2. **Seguridad y Accesos:** Implementar el control de acceso, gestión de usuarios, roles, permisos y registro de auditoría en bitácora.
3. **Catálogo e Inventario:** Gestionar los catálogos de productos y proveedores, así como el control en tiempo real de inventarios de materia prima y productos terminados.
4. **Producción (MRP Base):** Registrar la producción diaria con recálculo de costos y descuento/incremento automático en inventarios.
5. **Comercialización y Ventas:** Administrar ventas en mostrador (efectivo y QR) y pedidos programados, generando comprobantes y sincronizando inventarios.
6. **Finanzas y Reportes:** Registrar compras, gastos e inversiones, y generar reportes operativos y consolidados de resultados económicos.

---

## 4. Actores del Sistema y Matriz de Responsabilidades

El sistema define 4 actores principales con accesos diferenciados:

```
+--------------------------------------------------------------------------------+
|                             ACTORES DEL SISTEMA                                |
+--------------------------------------------------------------------------------+
|  [ Administrador ]        [ Propietario ]       [ Ventas ]       [ Producción ]|
|  - Usuarios y Roles       - Gestión Global      - Mostrador      - Jornada prod.|
|  - Seguridad y Permisos   - Compras y Gastos    - Pedidos        - Consumo mat. |
|  - Auditoría / Bitácora   - Reportes Financ.    - Comprobantes   - Alertas stock|
+--------------------------------------------------------------------------------+
```

### Descripción de Actores

1. **Administrador:**
   - **Responsabilidad:** Configuración técnica del sistema, administración de cuentas de usuario, asignación de roles y permisos, y auditoría general mediante la bitácora.
   - **Módulos principales:** Usuarios y Seguridad, Bitácora.

2. **Propietario (Carlos Santiago Vargas):**
   - **Responsabilidad:** Máxima autoridad del negocio. Supervisa todas las operaciones, gestiona proveedores, registra compras, gastos e inversiones, define precios y analiza los reportes consolidados y de resultados económicos.
   - **Módulos principales:** Todos los módulos con privilegios de consulta y administración estratégica.

3. **Personal de Ventas / Atención al Cliente:**
   - **Responsabilidad:** Atención en mostrador, registro ágil de ventas en efectivo y QR, toma y seguimiento de pedidos de clientes, consulta rápida de disponibilidad de pan y emisión de comprobantes.
   - **Módulos principales:** Comercialización (Ventas, Pedidos, Comprobantes, Disponibilidad).

4. **Personal de Producción / Panaderos (Miguel Ángel Rojas):**
   - **Responsabilidad:** Registro de la producción diaria elaborada en cada jornada, consulta de stock de materia prima y alertas de bajo stock, consulta de pedidos pendientes a producir y registro de bajas por pérdida/merma.
   - **Módulos principales:** Producción, Inventario de Materia Prima, Inventario de Productos Terminados, Bajas/Mermas.

---

## 5. Alcance Funcional por Módulos

El alcance se distribuye en 8 módulos funcionales del perfil, mapeados directamente a la arquitectura de paquetes del sistema:

| # | Módulo Funcional | Descripción del Alcance | Paquete Backend Asociado |
|---|---|---|---|
| **1** | **Usuarios y Seguridad** | Autenticación, recuperación de contraseñas, CRUD de usuarios, asignación de roles y permisos RBAC. | `apps.usuarios_seguridad` |
| **2** | **Bitácora y Auditoría** | Registro automático de acciones críticas (INSERT/UPDATE/DELETE), fecha, hora, responsable y detalle. | `apps.usuarios_seguridad` |
| **3** | **Productos y Catálogos** | Registro de productos, categorías, costos sugeridos, porcentaje de ganancia y precios de venta. | `apps.productos_inventario` |
| **4** | **Inventario de Materia Prima** | Control de existencias de insumos (harina, azúcar, manteca, etc.), alertas de stock mínimo y movimientos. | `apps.productos_inventario` |
| **5** | **Inventario de Productos Terminados** | Existencias de panes elaborados, entradas por producción, salidas por venta o merma. | `apps.productos_inventario` |
| **6** | **Compras, Proveedores y Gastos** | Registro de proveedores, compras de insumos, historial de costos y gastos/inversiones del negocio. | `apps.compras` |
| **7** | **Producción y Comercialización** | Producción diaria con consumo de insumos, ventas de mostrador (efectivo/QR), pedidos y comprobantes. | `apps.comercializacion` + `apps.productos_inventario` |
| **8** | **Reportes Gerenciales** | Reportes de ventas, producción, existencias, compras/gastos y balance de resultados económicos. | `apps.reportes` |

---

## 6. Metodología de Desarrollo: PUDS y UML

El proyecto se rige bajo el **Proceso Unificado de Desarrollo de Software (PUDS)**:
- **Iterativo e Incremental:** El software se construye en 4 ciclos de desarrollo bien delimitados.
- **Dirigido por Casos de Uso:** Cada ciclo aborda un conjunto concreto de los 26 Casos de Uso (CU 1 al CU 26).
- **Centrado en la Arquitectura:** Separación estricta de capas (Frontend React, Backend Django REST Framework, Base de Datos PostgreSQL con triggers/procedimientos almacenados).
- **Enfocado en los Riesgos:** Priorización de los módulos críticos y con mayor cascada de datos (seguridad y catálogos en Ciclo 1, compras y producción en Ciclo 2, ventas en Ciclo 3, y balance financiero en Ciclo 4).

### Fases del PUDS en el Proyecto:
1. **Inicio:** Levantamiento de requerimientos, entrevistas con propietario y maestro panadero, definición del perfil, alcance y casos de uso.
2. **Elaboración:** Modelado arquitectónico, diseño de base de datos relacional (DDL PostgreSQL, llaves foráneas, triggers) y definición de contratos de API REST.
3. **Construcción:** Desarrollo modular por ciclos (Ciclo 1: 7 CUs, Ciclo 2: 6 CUs, Ciclo 3: 7 CUs, Ciclo 4: 6 CUs), pruebas unitarias e integración.
4. **Transición:** Despliegue, pruebas de aceptación con usuarios finales y entrega del sistema.
