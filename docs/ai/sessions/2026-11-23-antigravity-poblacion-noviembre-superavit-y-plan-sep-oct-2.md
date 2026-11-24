# Bitácora de Sesión: Población Realista Noviembre 2026 y Plan de Ajuste Septiembre-Octubre

- **Fecha:** 2026-11-23
- **Autor / Agente:** Antigravity (Senior Architect / Developer)
- **Caso de Uso / Módulo:** CU13/CU21 (Ventas e Histórico Comercial), CU14 (Pedidos Institucionales), CU25 (Resultados Económicos y Flujo de Caja en KPIs).

---

## 1. Contexto y Diagnóstico
En la revisión del dashboard de KPIs (`/dashboard/kpis`), el Propietario observaba un balance fuertemente negativo (-Bs 2.970,40) con egresos de Bs 3.180,00 e ingresos de apenas Bs 209,60 (11 ventas).

**Causa raíz identificada:**
1. Al filtrarse el mes actual (Noviembre 2026), se contabilizaban las compras de materia prima registradas en noviembre (Bs 3.180,00), pero `seed_ventas_demo.py` únicamente contenía 11 ventas dispersas para todo el mes con tickets mínimos.
2. Una panadería con producción diaria de 870 panes genera ~Bs 600 a 650 diarios en ventas. Tener solo 11 ventas en el mes simulaba un negocio paralizado.
3. El usuario solicitó poblar noviembre con 45 a 55 ventas por día hábil (Lunes a Sábado, horario de atención de 10 horas: 08:00 a 18:30 con pausa de almuerzo) y revisar el estado de Septiembre y Octubre.

---

## 2. Cambios Implementados

### Backend (Django)
1. **Actualización de `seed_ventas_demo.py`:**
   - Archivo: `backend/apps/comercializacion/ventas/management/commands/seed_ventas_demo.py`
   - Incorporada generación diaria realista para Noviembre 2026 (del 1 al 23 de noviembre):
     - **Horario:** Turno mañana (08:00 a 12:00, cajera `mgonzales`) y turno tarde (15:00 a 18:30, cajera `jrivera`).
     - **Curva de demanda:** Picos marcados de desayuno (08:00–10:30, ~24 ventas) y de merienda/café (15:00–17:30, ~17 ventas).
     - **Volumen:** 48 a 54 ventas por día hábil (19 días) + 16 ventas los domingos (desayuno dominical). Total: **~990 transacciones**.
     - **Facturación estimada:** ~**Bs 12.000 a Bs 13.000**.
     - **Medios de pago:** 75% efectivo y 25% Stripe (`pi_demo_cu21_...`).
     - Idempotencia y soporte para `--force` si se requiere regeneración limpia.

2. **Actualización de `seed_pedidos_demo.py`:**
   - Archivo: `backend/apps/comercializacion/pedidos/management/commands/seed_pedidos_demo.py`
   - Incorporados 12 pedidos institucionales para noviembre 2026 (Hotel Cortez, Colegio San Ignacio, Restaurante El Aljibe, clientes particulares) distribuidos entre entregados, en preparación, listos y pendientes, aportando **~Bs 1.850 adicionales** en facturación.

---

## 3. Estado de Septiembre y Octubre y Plan de Ajuste
- **Octubre 2026:** Ya cuenta con un comando especializado (`seed_mes_operativo.py`) que simula 27 jornadas hábiles de octubre (compras, producción madrugadora, ventas en mostrador, mermas y pedidos).
- **Septiembre 2026:** Solo tiene la base de los 4 días académicos (6 al 9 de septiembre).
- **Plan para Septiembre:** Extender la lógica de mes operativo a septiembre para tener los tres meses (Sep, Oct, Nov) completos y coherentes.

---

## 4. Instrucciones de Verificación y Ejecución en Railway
1. Subir cambios a GitHub:
   ```bash
   git add .
   git commit -m "feat(seeders): poblar ventas diarias y pedidos de noviembre con margen positivo"
   git push origin <rama>
   ```
2. En Railway -> Backend -> **Console**:
   ```bash
   python manage.py seed_ventas_demo --force
   python manage.py seed_pedidos_demo
   ```
3. Recargar el dashboard de KPIs en Vercel para observar el resultado económico neto con superávit saludable (+Bs 8.000 a +Bs 9.500).
