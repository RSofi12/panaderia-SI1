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

4. **Consolidación Taxonómica y Deduplicación (CU5):**
   - Comando: `backend/apps/productos_inventario/productos/management/commands/consolidar_categorias.py`
   - Se resolvió la sobre-clasificación taxonómica pasando de 11 micro-categorías a **5 Categorías Maestras Coherentes**:
     1. `Panes Tradicionales y de Mesa` (7 productos)
     2. `Masas Típicas y Regionales` (5 productos)
     3. `Repostería y Panes Dulces` (9 productos)
     4. `Salados y Especialidades` (5 productos)
     5. `Panadería Rústica y Gourmet` (10 productos)
   - Se fusionó el producto duplicado `cuñape` (id 13, sin tilde) en `Cuñapé` (id 18, con tilde), transfiriendo 28 ventas, 17 lotes de producción, recetas e inventario, eliminando el registro huérfano.
   - Se actualizaron `seed_productos.py` y `seed_mes_operativo.py` para sincronizar las nuevas categorías y purgar categorías vacías.

5. **Eliminación de Vulnerabilidad de Duplicados en Alta/Edición de Productos (CU5):**
   - Archivo: `backend/apps/productos_inventario/productos/serializers.py`
   - Se implementó en `ProductoSerializer.validate_nombre` una validación estricta de unicidad insensible a mayúsculas/minúsculas (`iexact`), excluyendo la propia instancia en ediciones. Si el usuario intenta registrar un nombre existente (ej. "marraqueta" o "Marraqueta"), el backend responde con error 400 y el mensaje *"Ya existe un producto registrado con este nombre."*, el cual es capturado y desplegado en rojo en el campo del modal.
   - Se forzó `id_categoria` como campo obligatorio en `extra_kwargs` (`required=True`, `allow_null=False`).
   - Se añadieron pruebas unitarias en `apps/productos_inventario/productos/tests.py` verificando el rechazo de nombres duplicados y categorías ausentes (36/36 tests pasados exitosamente).

### Frontend (Arquitectura de Modales: Plantillas Especializadas y UX Resiliente)
1. **Componente Reutilizable `ConfirmarDescarteDialog`:**
   - Archivo: `frontend/src/apps/dashboard/components/ConfirmarDescarteDialog.tsx`
   - Diálogo modal de confirmación integrado visualmente en React (sin alertas nativas `window.confirm`).
   - Cumple con accesibilidad (`role="alertdialog"`, `aria-modal="true"`, bloqueo de scroll de fondo) y estética cálida (ícono `AlertTriangle` en ámbar, opciones *"Continuar editando"* y *"Descartar y salir"*).

2. **Arquitectura de Plantillas Modales (`ModalBase`, `ModalLectura`, `ModalFormulario`):**
   - Archivo `ModalBase.tsx`: Núcleo accesible con transiciones fluidas de entrada y salida (`duration-200 ease-out`), trampa de foco (`Tab`/`Shift+Tab`), restauración de foco al desmontar, `aria-labelledby` estable con `useId()` y soporte para backdrop estático y dinámico.
   - Archivo `ModalLectura.tsx`: Plantilla para vistas de SOLO LECTURA (consultas, detalles, recibos). Cierra de inmediato y de forma ágil al hacer clic en el fondo, presionar `Escape` o pulsar la `X`.
   - Archivo `ModalFormulario.tsx`: Plantilla para FORMULARIOS y captura de datos. Cuenta con backdrop estático (micro-sacudida al hacer clic fuera para evitar pérdida involuntaria de datos), encapsula internamente `ConfirmarDescarteDialog`, evalúa la prop `tieneCambios` al recibir `Escape`, `X` o el botón "Cancelar" vía `useModalFormulario()` o render-props.
   - Archivo `Modal.tsx`: Re-exporta los nuevos componentes y mantiene retrocompatibilidad total con los consumidores legacy del panel.

3. **Conexión y Refactorización en Modales del Sistema:**
   - **Formularios conectados a `ModalFormulario`:**
     - `frontend/src/apps/dashboard/productos/components/ProductoFormModal.tsx` (CU5: Alta/Edición de productos)
     - `frontend/src/apps/dashboard/compras/components/RegistrarGastoModal.tsx` (CU20: Gastos e inversiones)
   - **Vistas de consulta conectadas a `ModalLectura`:**
     - `frontend/src/apps/dashboard/compras/components/DetalleCompraModal.tsx` (CU7: Detalle de compras)
     - `frontend/src/apps/dashboard/comercializacion/ventas/ComprobanteVentaModal.tsx` (CU16: Ticket térmico e impresión de ventas)
     - `frontend/src/apps/dashboard/compras/components/DetalleGastoModal.tsx` (CU20: Ficha técnica detallada de gastos operativos e inversiones con estado, observaciones y monto)
   - **Resultado:** Reducción neta de código duplicado, comportamiento consistente en todo el sistema y eliminación de la vulnerabilidad de pérdida accidental de datos.
   - **Corrección de ciclo de vida (`forzarCierre`):** Se corrigió un bug en `ModalFormulario` donde al intentar cerrar sin cambios se renderizaba un modal vacío secundario (`<ModalBase>{null}</ModalBase>`). Se reemplazó por la coordinación limpia mediante el prop `cerrando` y la función interceptora booleana `onIntentarCerrar()` en `ModalBase`, asegurando que la ventana cierre directamente con su transición de salida sin remontar contenido vacío.
   - **Estabilidad de Scrollbar y Eliminación de Layout Shift:** Se eliminó el bloqueo forzado de `document.body.style.overflow = 'hidden'` en las plantillas (`ModalBase.tsx` y `AnularGastoModal.tsx`). Ahora la barra de desplazamiento del fondo permanece siempre visible, evitando el parpadeo/desfase horizontal de 15px en Windows al abrir o cerrar modales y permitiendo el desplazamiento de la página de fondo.

---

## 3. Verificación Local
- Motor: PostgreSQL 16 local (`postgresql-x64-18`).
- Backend:
  ```bash
  cd backend
  python manage.py consolidar_categorias
  python manage.py seed_all
  python manage.py test apps.productos_inventario.productos
  ```
  Resultado: 36/36 tests unitarios pasando, 5 categorías maestras consolidadas, seeders ejecutados sin duplicados.
- Frontend:
  ```bash
  cd frontend
  npm run build
  ```
  Resultado: Type-check de TypeScript exitoso (`tsc.cmd -b`: 0 errores) y empaquetado de producción de Vite generado en 14 segundos sin errores.
