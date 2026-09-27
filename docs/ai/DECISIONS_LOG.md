# Registro de Decisiones Técnicas y Arquitectónicas (DECISIONS LOG)

## 📌 Proyecto: Sistema de Información Web — Panadería Santiago (SI-1)

---

## 📅 2026-09-26 — Estructura modular de 5 paquetes backend
- **Decisión:** Organizar el backend en exactamente 5 Django apps (`usuarios_seguridad`, `productos_inventario`, `compras`, `comercializacion`, `reportes`).
- **Motivo:** En versiones previas se consideraba separar catálogo de insumos de la producción. Se decidió unificarlos en `productos_inventario` para mantener un número balanceado de módulos (5 paquetes) y facilitar la trazabilidad entre materia prima, receta/producción y pan horneado.
- **Impacto:** Menor complejidad en migraciones y llaves foráneas cruzadas, cumpliendo con la distribución formal de 26 Casos de Uso en 4 ciclos PUDS.

---

## 📅 2026-09-26 — Alcance y priorización del Ciclo 1 (7 Casos de Uso)
- **Decisión:** El Ciclo 1 implementa CU1 (Iniciar sesión), CU2 (Recuperar contraseña), CU3 (Gestionar usuarios), CU4 (Asignar roles y permisos), CU26 (Gestionar bitácora) en `usuarios_seguridad`, junto con los catálogos base CU5 (Gestionar productos) en `productos_inventario` y CU6 (Gestionar proveedores) en `compras`.
- **Motivo:** Garantizar la autenticación, seguridad RBAC y los datos maestros (productos y proveedores) antes de programar los procesos transaccionales de compras y producción diaria del Ciclo 2.
- **Impacto:** Permite validar la arquitectura base, la conexión con PostgreSQL y el login desde el frontend React desde la primera entrega.

---

## 📅 2026-09-26 — Clientes y Proveedores como entidades de datos (Sin Login)
- **Decisión:** Los clientes que compran en mostrador o hacen pedidos, y los proveedores de materia prima, son entidades de datos administradas por el personal. No cuentan con usuario, contraseña ni acceso al panel del sistema.
- **Motivo:** El alcance del sistema es de gestión interna operativa y administrativa para la panadería. No es un e-commerce abierto al público general.
- **Impacto:** Simplifica la seguridad y evita exponer endpoints públicos de registro (`/auth/register/`). Los roles se limitan a: Administrador, Propietario, Ventas y Producción.

---

## 📅 2026-09-26 — PostgreSQL 14+ y Bitácora de Auditoría
- **Decisión:** Utilizar PostgreSQL como motor relacional con soporte para llaves foráneas en cascada controlada y tabla `bitacora` para auditoría (CU26).
- **Motivo:** Cumplimiento de requerimientos de la materia SI-1 y preservación de la integridad transaccional del negocio.
- **Impacto:** Las operaciones críticas (creación/edición de usuarios, cambios de precios, registros de producción y ventas) quedan registradas con fecha, hora, responsable y acción efectuada.

---

## 📅 2026-09-26 — Postergación de Dockerización tras el Ciclo 1
- **Decisión:** Trabajar el Ciclo 1 en entorno local directo (`python -m venv venv` y `npm install`) y postergar la configuración de Docker/Docker Compose para etapas posteriores.
- **Motivo:** Priorizar la velocidad de desarrollo de los primeros 7 casos de uso y la familiarización del equipo con el código sin fricciones de configuración de contenedores.
- **Impacto:** La documentación de puesta en marcha refleja comandos locales directos y uso de variables de entorno `.env`.
