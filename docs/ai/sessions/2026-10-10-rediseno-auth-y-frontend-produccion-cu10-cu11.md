# Sesión de Desarrollo: Rediseño Corporativo de Autenticación (CU1, CU2) e Implementación Frontend de Producción (CU10, CU11)

- **Fecha:** 2026-10-10
- **Autor / Integrante:** Equipo de Desarrollo (Asistente IA Antigravity)
- **Paquete / Módulo:** `frontend` (`src/apps/auth/`, `src/apps/dashboard/productos/produccion/`) / `backend`
- **Casos de Uso abordados:** CU1 (Iniciar sesión), CU2 (Recuperar y restablecer contraseña), CU10 (Registrar producción diaria), CU11 (Consultar historial de producción)
- **Ciclo:** Consolidación Ciclo 1 (Auth UI/UX institucional) y Arranque Ciclo 2 (Producción)

---

## 1. 🎯 Objetivo de la sesión

1. **Resolver conflicto de integración:** Sanear el conflicto de merge en `backend/requirements.txt` originado tras la compatibilización de `psycopg2-binary>=2.9.9`.
2. **Implementar el Frontend del módulo de Producción Diaria (CU10 y CU11):**
   - Construir los contratos de tipos TypeScript, servicios de API con soporte de fallback a datos mock simulados, componentes de balance de insumos en tiempo real, tabla de lotes de producción con filtros y paginación, modal de detalle de lote y modal de registro de producción diaria.
   - Conectar la pestaña "Producción diaria" dentro de `ProductosPage.tsx` respetando permisos RBAC.
3. **Modernizar y Profesionalizar el diseño del flujo de Autenticación (CU1 y CU2):**
   - Adaptar `LoginPage.tsx` al diseño institucional de Figma: layout Split-Screen en escritorio con fotografía de panadería (`photo-bakery.jpg`), integración de la tipografía oficial `Sugo Regular` (`sugo.regular.otf`), logo circular SVG limpio sin ornamentos superfluos (sin gorro de chef ni marco amarillo), y reemplazo de emojis en botones de demo por iconos Lucide acordes (`ShieldCheck`, `Briefcase`, `ShoppingBag`, `ChefHat`).
   - Implementar función de conveniencia frontend "Recordarme" con persistencia local segura.
   - Ajustar el diseño para garantizar que quepa en pantalla sin scrollbars verticales en zoom estándar y sea 100% responsivo (ocultando la imagen lateral en móviles).
   - Adaptar `ForgotPasswordPage.tsx` con el mismo layout Split-Screen y tipografía `Sugo`.
   - Actualizar `ResetPasswordPage.tsx` y `AuthCard.tsx` con el diseño refinado y tipografía `Sugo`, manteniendo su disposición de tarjeta centrada (sin foto) conforme al requerimiento del usuario.

---

## 2. 🛠️ Cambios realizados

### Frontend — Autenticación y Diseño Institucional:
- **`frontend/src/assets/fonts/sugo.regular.otf`:** Instalación de la fuente tipográfica corporativa `Sugo Regular`.
- **`frontend/src/index.css`:** Declaración de regla `@font-face` para la familia tipográfica `Sugo` y utilidad `.font-sugo` para títulos y logomarcas.
- **`frontend/src/apps/auth/LoginPage.tsx`:**
  - Estructura Split-Screen: mitad izquierda con `photo-bakery.jpg` y degradados oscuros sobre fondos fotográficos (`hidden lg:flex`), mitad derecha con formulario centrado y scroll automático solo si se requiere en pantallas muy pequeñas.
  - Reemplazo del logo PNG por `circle-logo-panaderia.svg` con marco blanco limpio y elevación suave.
  - Títulos `"Bienvenido"` y `"Panadería Santiago"` renderizados con clase `.font-sugo`.
  - Reemplazo de emojis en los botones de auto-inserción de credenciales de prueba por iconos vectoriales Lucide representativos de los 4 roles del sistema.
  - Checkbox "Recordarme" para autocompletar el nombre de usuario localmente mediante `localStorage` (sin alterar el esquema JWT del backend).
  - Ajuste de paddings y espaciados para evitar barras de desplazamiento vertical innecesarias en resolución estándar (100% viewport fit).
- **`frontend/src/apps/auth/ForgotPasswordPage.tsx`:**
  - Rediseño con layout Split-Screen idéntico a Login.
  - Título `"Recuperar contraseña"` en fuente `Sugo`, logo circular SVG y campos estilizados.
- **`frontend/src/apps/auth/ResetPasswordPage.tsx`:**
  - Mantenimiento del layout centrado (sin foto lateral de panadería), enfocado en la tarjeta de restablecimiento.
  - Título `"Restablecer contraseña"` con tipografía `Sugo`.
  - Campos de nueva clave y confirmación con botones para alternar visibilidad de contraseña (`Eye`/`EyeOff`).
  - Preservación estricta de la lógica de seguridad: token leído perezosamente y eliminado de la barra del navegador con `window.history.replaceState()`, checklist en tiempo real con `PasswordRequirements` y separación de errores de validación de campo vs excepciones de negocio.
- **`frontend/src/apps/auth/components/AuthCard.tsx`:**
  - Actualización del contenedor común para utilizar el logo SVG circular con borde blanco y título principal en `.font-sugo`.

### Frontend — Módulo de Producción (CU10 y CU11):
- **`frontend/src/types/produccion.ts`:**
  - Interfaces TypeScript: `LoteProduccion`, `DetalleProduccionInsumo`, `DetalleProduccionProducto`, `BalanceInsumo`, `RegistrarProduccionPayload`, `FiltrosProduccion`.
- **`frontend/src/services/produccionService.ts`:**
  - Cliente Axios conectado a los endpoints `/api/produccion/` y `/api/produccion/balance-insumos/`, con arquitectura híbrida de fallback automático a datos simulados (*mock*) para permitir pruebas inmediatas en UI antes del despliegue del backend de producción.
- **`frontend/src/apps/dashboard/productos/produccion/components/BalanceInsumosCard.tsx`:**
  - Tarjeta de cálculo y visualización de balance de materia prima (harina, levadura, manteca, etc.), alertas de stock insuficiente y barras de consumo porcentual proyectado.
- **`frontend/src/apps/dashboard/productos/produccion/components/TablaLoteProduccion.tsx`:**
  - Tabla de historial de lotes (CU11) con indicadores de estado de producción, fecha/hora, responsable y desglose de unidades producidas.
- **`frontend/src/apps/dashboard/productos/produccion/components/ModalDetalleProduccion.tsx`:**
  - Modal de auditoría y detalle para inspeccionar materias primas consumidas vs panes obtenidos en un lote específico.
- **`frontend/src/apps/dashboard/productos/produccion/RegistrarProduccionModal.tsx`:**
  - Modal interactivo de registro de producción diaria (CU10): selección de recetas/productos, cálculo dinámico de insumos requeridos según cantidad a producir y validaciones antes del envío.
- **`frontend/src/apps/dashboard/productos/produccion/ProduccionTab.tsx`:**
  - Vista orquestadora de la pestaña de producción con KPIs de resumen, filtros de búsqueda y botón de acción principal para registrar nuevo lote.
- **`frontend/src/apps/dashboard/productos/ProductosPage.tsx`:**
  - Integración de sistema de pestañas dobles: "Catálogo de productos" (CU5) y "Producción diaria" (CU10/CU11) con sincronización en URL (`?tab=catalogo` / `?tab=produccion`).

### Backend / Git:
- **`backend/requirements.txt`:** Se resolvió el marcador de conflicto git preservando `psycopg2-binary>=2.9.9` para compatibilidad universal con entornos Windows y contenedores Docker.

---

## 3. 🧠 Decisiones técnicas y de diseño

1. **Tipografía institucional `Sugo`:**
   - La fuente corporativa `sugo.regular.otf` se empaquetó como un asset local en `src/assets/fonts/` y se registró mediante `@font-face` en `src/index.css`. Esto garantiza que no dependa de conexiones externas (CDN) y cargue con latencia cero en cualquier entorno o dispositivo.
2. **Asimetría intencional en las pantallas de autenticación:**
   - Para las pantallas iniciales de entrada y solicitud de acceso (`LoginPage` y `ForgotPasswordPage`), se implementó la arquitectura visual *Split-Screen* (50% fotografía editorial, 50% formulario) para causar un alto impacto visual de marca.
   - Para la pantalla final de restablecimiento (`ResetPasswordPage`), se preservó intencionalmente el formato de tarjeta centrada (*Card layout*), minimizando distracciones visuales mientras el usuario interactúa con los requisitos de complejidad de su nueva clave.
3. **Función "Recordarme" en el cliente:**
   - La función "Recordarme" se implementó puramente en el cliente (`localStorage` para el identificador/usuario). No altera el contrato ni los tokens del backend Django REST Framework, evitando introducir complejidades innecesarias en los tiempos de expiración de los JWT en esta fase.
4. **Mock Graceful Fallback en `produccionService`:**
   - Para desbloquear el desarrollo ágil de la interfaz de usuario de producción (CU10/CU11) sin esperar a la finalización de los modelos ORM del backend, el servicio intenta comunicarse con la API de Django y, si no responde o devuelve 404, conmuta automáticamente a mocks realistas tipados.

---

## 4. ⚠️ Siguientes pasos

1. **Implementar modelos y endpoints backend de Producción (Ciclo 2):**
   - Crear modelos `Receta`, `DetalleReceta`, `Produccion` (Lote), `DetalleProduccionInsumos` y `DetalleProduccionProductos` en `apps.productos_inventario`.
   - Desarrollar la lógica transaccional de descuento automático de stock de insumos e incremento de stock de producto terminado bajo `@transaction.atomic`.
2. **Implementar CU7 (Registrar compra de materia prima):**
   - Continuar con el ciclo transaccional de compras en `apps.compras`.

---

## 5. 🧪 Cómo probar lo implementado

```powershell
# 1. Validar compilación estricta de TypeScript y bundle de producción
cd frontend
npm run build
# Debe terminar con: ✓ built in ~6-7s, 0 errores

# 2. Iniciar servidor de desarrollo
npm run dev

# 3. Pruebas visuales en el navegador:
# - Login: http://localhost:5173/login
#   * Verificar tipografía Sugo en "Bienvenido" y "Panadería Santiago".
#   * Comprobar que en desktop se ve la foto y en móvil se oculta limpiamente.
#   * Probar botones de inserción rápida con los nuevos iconos Lucide.
#   * Verificar que la página no genera scrollbar vertical en 100% zoom.
# - Recuperar contraseña: http://localhost:5173/recuperar-password
#   * Verificar Split-screen con foto de panadería y tipografía Sugo.
# - Restablecer contraseña: http://localhost:5173/recuperar-password/nueva?token=prueba
#   * Verificar tarjeta centrada (sin foto), tipografía Sugo en el título,
#     checklist de requisitos en tiempo real y alternancia de ver/ocultar clave.
# - Producción Diaria: http://localhost:5173/dashboard/productos?tab=produccion
#   * Verificar KPIs, balance de insumos, tabla de lotes y modales interactivos.
```
