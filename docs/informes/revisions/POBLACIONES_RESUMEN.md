# Guía Maestra de Poblaciones de Datos — Panadería Santiago (SI-1)

> **Documento de Referencia Técnica y Operativa**  
> **Ubicación:** `docs/informes/revisions/POBLACIONES_RESUMEN.md`  
> **Proyecto:** Sistema de Información Web para la Gestión de Ventas, Producción, Inventario y Control Administrativo  
> **Empresa:** Panadería "Santiago" (Santa Cruz de la Sierra, Bolivia)  
> **Última Actualización:** 24 de noviembre de 2026  

---

## 1. 📌 Propósito y Filosofía del Conjunto de Datos

Para las defensas académicas y la evaluación del sistema en **Sistemas de Información 1 (SI-1)**, el sistema no utiliza datos estáticos ni registros aislados. Contiene una **simulación cronológica realista y matemáticamente coherente de 4 meses y medio de operación** (desde la apertura a mediados de julio de 2026 hasta el 24 de noviembre de 2026).

### Principios Fundamentales del Modelo de Datos:
1. **Superávit Económico Real:** Los ingresos por mostrador y pedidos superan a los costos de compra de harina/insumos, gastos de alquiler/luz y mermas. El negocio demuestra rentabilidad sostenible.
2. **Trazabilidad Integral (CU10 $\rightarrow$ CU18 $\rightarrow$ CU13 $\rightarrow$ CU25):** 
   - Todo pan vendido o perdido provino de una orden de horneado en `Produccion`.
   - Toda salida descuenta inventario en `MovimientoProductoTerminado` (Kardex).
   - Toda compra descuenta o alimenta existencias de `MateriaPrima`.
3. **Mermas Tipificadas (CU18):** Se registran diariamente tanto los panes fríos que quedaron en mostrador al cierre (18:15 hrs) como los defectos de horneado matutinos (08:30 hrs).
4. **Horario Laboral Realista:** Ventas distribuidas de lunes a sábado de **08:00 a 18:00** (con pico matutino de 08:00 a 11:30, descanso de 12:00 a 13:00, y pico vespertino de 15:30 a 18:00).

---

## 2. 📊 Resumen Ejecutivo Consolidado (Julio a Noviembre 2026)

| Concepto / Métrica | Julio 2026 (Quincena) | Agosto 2026 | Septiembre 2026 | Octubre 2026 | Noviembre 2026 (al 24) | Total Acumulado |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Etapa del Negocio** | *Apertura local* | *Maduración inicial* | *Inversión en Horno* | *Consolidación* | *Pico de Demanda* | **4.5 Meses** |
| **Días Operativos (L-S)** | 15 días | 27 días | 26 días | 27 días | 21 días | **116 días** |
| **Ventas Mostrador / Día** | 18 a 24 | 26 a 32 | 35 a 40 | 35 a 40 | 45 a 55 | **~3.800 comprobantes** |
| **Pedidos Especiales** | 4 pedidos | 8 pedidos | 10 pedidos | 12 pedidos | 14 pedidos | **48 pedidos** |
| **Panes Horneados** | ~8.400 un. | ~22.600 un. | ~29.800 un. | ~32.400 un. | ~28.300 un. | **~121.500 panes** |
| **Panes Mermados (CU18)** | 160 un. | 460 un. | 540 un. | 610 un. | 520 un. | **~2.290 panes (~1.9%)** |
| **Ingresos Totales (Bs)** | **Bs 5.710,00** | **Bs 18.940,00** | **Bs 24.280,00** | **Bs 26.850,00** | **Bs 32.450,00** | **Bs 108.230,00** |
| **Compras Insumos (Bs)** | Bs 3.200,00 | Bs 8.600,00 | Bs 10.400,00 | Bs 11.200,00 | Bs 13.800,00 | **Bs 47.200,00** |
| **Costo Mermas (Bs)** | Bs 78,00 | Bs 230,00 | Bs 265,00 | Bs 305,00 | Bs 260,00 | **Bs 1.138,00** |
| **Gastos Operativos (Bs)** | Bs 1.630,00 | Bs 4.860,00 | Bs 5.055,00 | Bs 5.575,00 | Bs 5.540,00 | **Bs 22.660,00** |
| **Inversión Capital (Bs)** | Bs 0,00 | Bs 0,00 | **Bs 8.000,00** *(Horno)* | Bs 0,00 | **Bs 4.000,00** *(Cámara frío)* | **Bs 12.000,00** |
| **Utilidad Neta Resultante** | **+Bs 802,00** | **+Bs 5.250,00** | **+Bs 560,00** | **+Bs 5.770,00** | **+Bs 8.850,00** | **+Bs 25.232,00 (Ganancia)** |

---

## 3. 📂 Mapeo de Archivos de Población (Seeders)

Todos los seeders se ejecutan mediante Django Management Commands ubicados en el backend:

```
backend/apps/
├── comercializacion/ventas/management/commands/
│   ├── seed_mes_operativo.py       <-- Pobla Julio, Agosto, Septiembre y Octubre completos
│   ├── seed_ventas_demo.py          <-- Ventas rápidas demostrativas
│   └── seed_pedidos_demo.py         <-- Pedidos para clientes (eventos, salones, colegios)
├── reportes/management/commands/
│   └── seed_noviembre_demo.py       <-- Pobla Noviembre 2026 (mes actual al día 24)
├── compras/gastos/management/commands/
│   └── seed_gastos_demo.py          <-- Gastos fijos (alquiler, luz, agua, mantenimiento)
├── compras/compras/management/commands/
│   └── seed_compras_demo.py         <-- Facturas de compra de sacos de harina y manteca
├── productos_inventario/produccion/management/commands/
│   └── seed_historial_demo.py       <-- Jornadas de horneado matutinas/tardes
└── usuarios_seguridad/users/management/commands/
    ├── seed_all.py                  <-- SEEDER MAESTRO (Orquesta todo en orden)
    ├── seed_usuarios.py             <-- Roles y credenciales de prueba
    └── seed_productos.py            <-- Catálogo de 10 variedades de panadería
```

---

## 4. 🍞 Detalle por Mes Operativo

### A. Julio 2026 (Apertura del Local Comercial)
* **Período:** Del 15 de julio al 31 de julio de 2026 (15 días laborables).
* **Comportamiento:** La panadería abre sus puertas. Clientela barrial en crecimiento.
* **Ventas:** 18 a 24 ventas diarias de mostrador (promedio 15 a 30 panes por compra).
* **Mermas:** Panadero calibra tiempos de cocción; sobran de 6 a 12 panes por día.
* **Resultado Económico:** Ingresos de Bs 5.710 absorben compras de harina iniciales (Bs 3.200) y gastos básicos, cerrando con balance neto de **+Bs 802,00**.

### B. Agosto 2026 (Maduración Inicial y Clientela Fija)
* **Período:** Del 01 al 31 de agosto de 2026 (27 jornadas laborales).
* **Comportamiento:** Aumento de producción en variedades populares (Marraqueta, Casero, Pan de Leche).
* **Ventas:** 26 a 32 ventas diarias en mostrador + 8 pedidos para reuniones y desayunos.
* **Mermas:** 10 a 18 panes sobrantes diarios al cierre (18:15 hrs) + defecto de horneado cada 2 días (08:30 hrs).
* **Resultado Económico:** Ingresos de Bs 18.940 frente a costos totales de Bs 13.690, dejando un superávit neto de **+Bs 5.250,00**.

### C. Septiembre 2026 (Inversión en Horno Rotativo)
* **Período:** Del 01 al 30 de septiembre de 2026 (26 jornadas laborales).
* **Hito de Negocio:** Adquisición de un nuevo horno industrial por **Bs 8.000,00** registrado en `MovimientoEconomico` (`tipo=INVERSION`).
* **Ventas:** Consolidación con 35 a 40 ventas diarias de mostrador + 10 pedidos programados.
* **Resultado Económico:** A pesar de pagar el horno en efectivo, los ingresos por ventas (Bs 24.280) cubrieron todos los costos de insumos, servicios y la inversión de capital, arrojando una utilidad neta positiva de **+Bs 560,00**.

### D. Octubre 2026 (Alta Maduración y Eficiencia)
* **Período:** Del 01 al 31 de octubre de 2026 (27 jornadas laborales).
* **Comportamiento:** Operación estable a capacidad plena del nuevo horno.
* **Ventas:** 35 a 40 ventas diarias + 12 pedidos de alto volumen (hamburgueserías y salones de té).
* **Mermas:** 16 a 24 panes diarios registrados con motivo `Sobrante de mostrador al cierre` (CU18).
* **Resultado Económico:** Excelente margen neto de ganancia con **+Bs 5.770,00**.

### E. Noviembre 2026 (Mes Actual en Curso — Pico Operativo)
* **Período:** Del 01 al 24 de noviembre de 2026 (21 jornadas laborales).
* **Comportamiento:** Récord de recaudación pre-festividades.
* **Ventas:** 45 a 55 ventas diarias de mostrador + 14 pedidos institucionales.
* **Resultado Económico:** Ingresos por Bs 32.450 y utilidad neta récord de **+Bs 8.850,00**.

---

## 5. 🛠️ Tablas y Modelos Afectados en la Base de Datos

1. **`users_usuario` / `users_rol`:** Actores con roles diferenciados (`csantiago` Propietario, `mgonzales` Ventas, `mrojas` Producción Maestro Panadero).
2. **`productos_producto` / `productos_categoria`:** 10 variedades activas (Marraqueta, Pan Dulce, Casero, Pan de Leche, Integral, etc.).
3. **`produccion_produccion` y `produccion_detalle_produccion`:** Lotes diarios de horneado en jornadas Mañana y Tarde.
4. **`nota_perdida_producto` (CU18):**
   - Atributos clave: `cantidad`, `costo_unitario`, `motivo`, `observaciones`, `fecha_salida`.
   - Motivos soportados: `Sobrante de mostrador al cierre`, `Defecto de horneado / deformación`, `Dañado en vitrina`.
5. **`ventas_venta` y `ventas_detalle_venta`:** Comprobantes emitidos en efectivo y QR (Stripe/tarjeta).
6. **`pedidos_pedido` y `pedidos_detalle_pedido`:** Pedidos anticipados con estado `ENTREGADO` y pago completado.
7. **`compras_compra` y `compras_detalle_compra`:** Compras quincenales de sacos de harina, azúcar y levadura.
8. **`gastos_movimientoeconomico` (CU20):** Alquiler mensual (Bs 2.800), Electricidad CRE (Bs 1.280), Agua Saguapac (Bs 345), Mantenimiento de amasadoras y bolsas kraft.
9. **`movimiento_producto_terminado` (CU12):** Kardex histórico automatizado que refleja entradas por horneado y salidas por venta/merma.

---

## 6. 🚀 Cómo Ejecutar y Probar las Poblaciones

### En Entorno Local (Virtualenv o Docker):
```bash
# 1. Aplicar migraciones pendientes
python manage.py migrate

# 2. Ejecutar el seeder maestro (aplica todas las poblaciones en orden seguro)
python manage.py seed_all

# O ejecutar selectivamente con regeneración forzada si ya existen datos:
python manage.py seed_mes_operativo --force
python manage.py seed_noviembre_demo
```

### En Servidor Remoto (Render / Cloud):
El `entrypoint.sh` de Docker está configurado para ejecutar automáticamente:
```bash
python manage.py migrate --noinput
python manage.py seed_all
```
> [!NOTE]
> Gracias al control de dependencias foráneas (`MovimientoProductoTerminado` $\rightarrow$ `NotaPerdidaProducto` $\rightarrow$ `DetalleProduccion`), los seeders pueden ejecutarse múltiples veces o con `--force` sin generar bloqueos `ProtectedError`.
