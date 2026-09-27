# Visión del Proyecto (PROJECT VISION)

## 📌 Nombre del Proyecto
**Sistema de Información Web para la Gestión de Ventas, Producción, Inventario y Control Administrativo — Panadería "Santiago"**  
Materia: Sistemas de Información 1 (SI-1) — Grupo 3 — Santa Cruz de la Sierra, Bolivia.

---

## 🥐 Problema que Resuelve
La Panadería Santiago opera históricamente bajo un esquema manual basado en cuadernos físicos, notas en papel y cálculos con calculadora. Este procedimiento genera:
1. **Pérdida de tiempo y errores aritméticos:** Dificultad para cuadrar caja diaria (efectivo vs. pagos QR) y calcular utilidades periódicas.
2. **Desconexión operativa:** Las compras no incrementan el stock de materia prima automáticamente; la producción diaria no descuenta insumos consumidos ni da de alta el pan horneado; las ventas de mostrador no descuentan el stock de producto terminado en tiempo real.
3. **Falta de información histórica y alertas:** Imposibilidad de saber a tiempo cuándo reponer harina, azúcar o manteca antes de desabastecimiento, o cuantificar con precisión las mermas.

---

## 🎯 Objetivo Principal
Proveer una solución web moderna, centralizada y multiusuario que integre la cadena de valor completa del negocio:
$$\text{Compras a Proveedores} \longrightarrow \text{Stock Insumos} \longrightarrow \text{Producción Diaria} \longrightarrow \text{Stock Panes} \longrightarrow \text{Ventas (Efectivo/QR) y Pedidos} \longrightarrow \text{Resultados Económicos}$$

El sistema es de uso exclusivo para el personal interno autorizado:
- **Administrador:** Seguridad, usuarios, roles, permisos y bitácora.
- **Propietario (Carlos Santiago Vargas):** Compras, gastos, precios, supervisión global y balances financieros.
- **Personal de Ventas:** Mostrador, pedidos, comprobantes y consulta de stock.
- **Personal de Producción / Maestro Panadero (Miguel Ángel Rojas):** Producción diaria, control de insumos y mermas.

---

## 🏗️ Alcance General y Arquitectura
- **Backend:** API REST modular construida con Python / Django 5+ / Django REST Framework (5 paquetes bien definidos en `backend/apps/`).
- **Frontend:** Aplicación de una sola página (SPA) responsiva con React, TypeScript, Vite y Tailwind CSS en `frontend/`.
- **Base de Datos:** PostgreSQL 14+ con normalización, integridad referencial, llaves foráneas y triggers para bitácora de auditoría.
- **Metodología:** Proceso Unificado de Desarrollo de Software (PUDS) dividido en 4 ciclos incrementales que cubren 26 Casos de Uso.

---

## 🛡️ Principios Inmutables del Proyecto
1. **Clientes y Proveedores como datos, no como usuarios:** Los clientes y proveedores no tienen cuenta, contraseña ni acceso al panel; son entidades registradas por el personal.
2. **Consistencia Transaccional de Inventarios:** Todo movimiento que afecte stock o dinero debe ser atómico (`transaction.atomic`) para garantizar que la producción descuente insumos y aumente panes sin inconsistencias intermedias.
3. **Seguridad RBAC Granular:** Cada usuario accede estrictamente a las opciones correspondientes a su rol asignado.
4. **Desarrollo Limpio y sin Hardcoding:** Toda configuración sensible o dependiente de red se gestiona mediante `.env`.
