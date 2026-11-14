# Bitácora de Sesión: Expansión de Catálogos y Poblado de 1 Mes Operativo Completo

- **Fecha:** 2026-11-14
- **Autor / Agente:** Antigravity (Pair Programming con Desarrollador)
- **Caso de Uso / Módulo:** Orquestación de Carga de Datos, CU5 (Productos), CU6 (Proveedores), CU7 (Compras), CU8 (Materia Prima), CU10/CU11 (Producción Diaria), CU13 (Ventas en Mostrador), CU14 (Pedidos), CU20 (Gastos Operativos), CU21 (Reportes de Venta).

---

## 1. Contexto y Objetivo
El usuario solicitó poblar la base de datos de Panadería Santiago con 1 mes de trabajo continuo y realista (Octubre 2026):
1. **Catálogo ampliado:** Llegar a 36 variedades de pan y masas (incluyendo masas típicas cruceñas como cuñapé, sonso, masaco; repostería como queques de zanahoria y banana, pastel de choclo, panetón con chocolate; salados como salteñas tradicionales, tamales a la olla, empanadas; y panes gourmet como croissant, brioche, baguette, pan de centeno, bagel, ciabatta y focaccia).
2. **Proveedores y Materias Primas:** Ampliar a 9 proveedores especializados (Sofía, Guabirá, Lácteos Chaqueños, San Gabriel, San Juan, etc.) y 20 materias primas (queso criollo, almidón, charque, choclo, etc.).
3. **Flujo de Ventas:** 22 a 28 ventas diarias entre semana (Lunes a Viernes) y 15 a 20 ventas los Sábados, distribuidas en horario comercial de 8 horas (06:30 a 14:30), con variedad de productos y métodos de pago (efectivo y Stripe).
4. **Producción, Compras y Gastos:** 27 jornadas de producción matutina (05:00 - 07:00), mermas periódicas (CU18), 16 compras de reabastecimiento y gastos fijos/variables del mes (alquiler, luz, agua, mantenimiento).

---

## 2. Cambios Implementados

### Backend (Django REST Framework)
1. **Nuevo Seeder de Mes Operativo (`seed_mes_operativo.py`):**
   - Archivo: `backend/apps/comercializacion/ventas/management/commands/seed_mes_operativo.py`
   - Simula 27 días laborables (Lunes a Sábado, descanso dominical) de Octubre 2026.
   - Crea 648 tickets de venta en mostrador (`Venta` y `DetalleVenta`), totalizando Bs 23.458,75 facturados con excelente rentabilidad.
   - Crea 27 lotes de producción diaria (`Produccion` y `DetalleProduccion`) con 632 líneas de panadería elaborada.
   - Registra notas de merma (`NotaPerdidaProducto`) con motivos y costos unitarios realistas.
   - Registra 16 compras de materia prima periódicas (`Compra` y `DetalleCompra`) a los 9 proveedores.
   - Registra 21 pedidos anticipados de clientes frecuentes (`Pedido` y `DetallePedido`).
   - Registra 6 movimientos económicos (`MovimientoEconomico`) de alquiler, energía, agua, mantenimiento y equipamiento.
   - Actualiza existencias iniciales saludables para `InventarioProductoTerminado` e `InventarioMateriaPrima`.

2. **Actualización de Catálogos Existentes:**
   - `seed_proveedores.py`: Ampliado de 3 a 9 proveedores locales con `get_or_create`.
   - `seed_materias_primas.py`: Ampliado de 7 a 20 materias primas con precios e inventario inicial.
   - `seed_productos.py`: Ampliado de 12 a 36 productos bajo 11 categorías (incluyendo masas típicas cruceñas, salados y gourmet).
   - `seed_recetas.py`: Añadidas las formulaciones completas de BOM/MRP para las 36 variedades (108 ingredientes registrados/actualizados).
   - `apps/productos_inventario/productos/models.py`: Agregados los campos `activo` y `estado` al modelo `CategoriaProducto` para reflejar con precisión el esquema físico de PostgreSQL.

3. **Seeder Maestro `seed_all.py`:**
   - Archivo: `backend/apps/usuarios_seguridad/users/management/commands/seed_all.py`
   - Incorporado `seed_mes_operativo` como paso 12 del flujo maestro.
   - Verificación ejecutada exitosamente: 12/12 seeders procesados con 0 errores.

---

## 3. Verificación Local
- Motor: PostgreSQL 16 local (`postgresql-x64-18`).
- Ejecución probada:
  ```bash
  cd backend
  python manage.py seed_all
  ```
- Resultado: 12 seeders ejecutados en orden de dependencia referencial sin violaciones de integridad ni duplicados.
