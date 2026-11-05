# Bitácora de Sesión: Seeder Maestro y Adaptación de Dataset de 4 Días

- **Fecha:** 2026-11-05
- **Autor / Agente:** Antigravity (Pair Programming con Desarrollador)
- **Caso de Uso / Módulo:** Orquestación de Carga de Datos, CU10/CU11 (Producción y Mermas), CU14 (Pedidos), CU20 (Gastos e Inversiones), Despliegue Railway / Producción.

---

## 1. Contexto y Objetivo
El usuario solicitó poblar más la base de datos de Panadería Santiago a partir del dataset de 4 días (`docs/informes/Poblacion_4_Dias_Panaderia_Santiago.sql`), adaptándolo a la arquitectura actual de Django sin ejecutar SQL crudo directamente, y resolver la ausencia de datos en el entorno desplegado en Railway (donde las tablas de producción diaria y otras aparecían vacías con valores en 0).

Se determinó la creación de un Seeder Maestro (`python manage.py seed_all`) y la implementación de los seeders modulares faltantes para clientes/pedidos y gastos/inversiones, así como la actualización de compras y producción con mermas.

---

## 2. Cambios Implementados

### Backend (Django REST Framework)
1. **Comando Maestro `seed_all`:**
   - Archivo: `backend/apps/usuarios_seguridad/users/management/commands/seed_all.py`
   - Orquesta secuencialmente los 11 seeders del sistema en estricto orden de dependencia referencial:
     1. `seed_usuarios`
     2. `seed_materias_primas`
     3. `seed_productos`
     4. `seed_recetas`
     5. `seed_proveedores`
     6. `seed_compras`
     7. `seed_existencias`
     8. `seed_historial_demo`
     9. `seed_pedidos_demo`
     10. `seed_gastos_demo`
     11. `seed_ventas_demo`
   - Es seguro e idempotente: maneja excepciones y advertencias sin interrumpir el lote completo.

2. **Seeder de Pedidos y Clientes (`seed_pedidos_demo`):**
   - Archivo: `backend/apps/comercializacion/pedidos/management/commands/seed_pedidos_demo.py`
   - Puebla 6 clientes reales cruceños y 10 pedidos anticipados con sus líneas de detalle (`DetallePedido`), estados variados (`entregado`, `en_preparacion`, `listo`, `pendiente`, `cancelado`), métodos de pago y validaciones de restricciones de integridad de Django.

3. **Seeder de Gastos e Inversiones (`seed_gastos_demo`):**
   - Archivo: `backend/apps/compras/gastos/management/commands/seed_gastos_demo.py`
   - Puebla 5 movimientos económicos (`MovimientoEconomico` - CU20): alquiler del local, compra de horno industrial, energía eléctrica, agua potable y mantenimiento de hornos.

4. **Actualización de Producción y Mermas (`seed_historial_demo`):**
   - Archivo: `backend/apps/productos_inventario/produccion/management/commands/seed_historial_demo.py`
   - Añadida la 4ta jornada de producción y la carga de 2 notas de merma (`NotaPerdidaProducto` - CU18): 3 panes dulces dañados en el día 1 y 5 marraquetas en el día 2.
   - Reemplazado `raise CommandError` por advertencia limpia para permitir reejecución segura sin lanzar trazas de error.

5. **Actualización de Compras (`seed_compras`):**
   - Archivo: `backend/apps/compras/compra_materia_prima/management/commands/seed_compras.py`
   - Incluida la reposición del Día 4 (50 kg de harina a Molinos del Oriente S.R.L.).

---

## 3. Decisiones Técnicas y Arquitectónicas
- **No ejecución de SQL crudo:** Se descartó ejecutar el archivo `.sql` directamente en PostgreSQL debido a incompatibilidad con el algoritmo de hash de contraseñas de Django (`PBKDF2` vs hashes demo), desfase de secuencias autoincrementales (`nextval`), y para preservar la ejecución de lógica de negocio (kardex y cálculo de totales).
- **Mantenimiento de seeders individuales:** Ningún seeder preexistente fue eliminado ni alterado en su contrato. Siguen disponibles de forma independiente para testing modular.
- **Ubicación de la consola en Railway:** Se instruyó al usuario sobre la pestaña `Console` en el dashboard de Railway para la ejecución remota de comandos en el contenedor del backend.

---

## 4. Instrucciones de Verificación Local y Despliegue

### Local
Ejecutar el seeder maestro desde la raíz o dentro de `backend/`:
```bash
python manage.py seed_all
```

### En Railway (Producción)
1. Ir al panel de [Railway](https://railway.com) $\rightarrow$ Servicio Backend (`panaderia-SI1`).
2. Abrir la pestaña **Console**.
3. Ejecutar:
   ```bash
   python manage.py seed_all
   ```
4. Refrescar el dashboard web (`panaderia-si-1.vercel.app`) en las pestañas de Producción, Ventas, Pedidos e Inventario.
