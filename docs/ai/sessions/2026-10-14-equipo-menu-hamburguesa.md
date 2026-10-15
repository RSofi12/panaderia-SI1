# Sesión de Desarrollo: Menú hamburguesa del panel

- **Fecha:** 2026-10-14
- **Autor / Integrante:** Equipo
- **Paquete / Módulo:** `frontend`
- **Casos de Uso abordados:** CU1 (marco del panel, compartido por todos los módulos)
- **Ciclo:** Ciclo 1

---

## 1. 🎯 Objetivo de la sesión

Que el menú lateral del panel se abra y se cierre como un cajón en el teléfono, sin cambiar el menú fijo del escritorio.

## 2. 🛠️ Cambios realizados

- **Frontend:**
  - `DashboardLayout.tsx`: el botón alterna el cajón; cerrar es una función estable para no reenfocar el menú en cada render.
  - `Topbar.tsx`: el botón de hamburguesa mide 44 px, anuncia si el menú está abierto (`aria-expanded`) y apunta al cajón (`aria-controls="menu-lateral"`). También se muestra en escritorio.
  - En escritorio el menú empieza abierto. Al ocultarlo, el contenido pierde el margen de 18 rem y usa todo el ancho. No hay velo.
  - `Sidebar.tsx`: por debajo de 1024 px el menú es un diálogo. Se cierra con la X, tocando el velo o con Escape. El foco entra en la X y vuelve al botón al cerrar. Mientras está cerrado, el cajón queda `inert` para que el teclado no entre en enlaces fuera de la pantalla. El ancho es como máximo `18rem`, dejando una franja de la página visible. En escritorio sigue fijo y el botón de hamburguesa no se muestra.

## 3. 🧠 Decisiones técnicas tomadas

- El cajón reutiliza el café `#1c120c` del menú. El velo usa el mismo color al 45 % para que se lea como la misma corteza, no como un gris genérico.
- `inert` y el diálogo solo aplican cuando la ventana es menor que `lg`. En escritorio el menú no es un modal.

## 4. ⚠️ Pendientes o siguientes pasos

- Las tablas anchas de los listados siguen desplazándose de lado en el teléfono.

## 5. 🧪 Cómo probar lo implementado

1. Entrar al panel y estrechar la ventana por debajo de 1024 px.
2. Pulsar el botón de las tres rayas: entra el menú, el foco queda en Cerrar y la página de atrás no se desplaza.
3. Elegir un módulo: el cajón se cierra y cambia la pantalla.
4. Abrirlo de nuevo y cerrarlo con la X, con un toque fuera del menú y con Escape.
5. En 1280 px o más el menú empieza abierto. El mismo botón de las tres rayas lo oculta y el contenido ocupa todo el ancho. No aparece el velo oscuro: en escritorio el menú empuja la página, no la tapa. Escape también lo cierra.

---

## Actualización: riel de iconos en escritorio

En el escritorio el menú ya no desaparece. Se estrecha a una columna de 4.5 rem y el contenido conserva ese margen. Al pasar el cursor o el foco por un icono, el nombre sale a la derecha en una pastilla color miga (`#f6e7c1`) con una animación corta. En el teléfono sigue siendo un cajón que se oculta del todo. Elegir un módulo en escritorio no pliega el menú.

---

## Actualización: marca Softtech y entrada de los paquetes

Se quitó la X del encabezado del menú. El cubo de Softtech se probó en ese lugar y se retiró: el encabezado vuelve a mostrar solo el logo y el nombre de Panadería Santiago. En el teléfono el cajón se cierra con las tres rayas, tocando fuera o con Escape; el foco entra en Inicio.

Los enlaces del menú y las tarjetas de «Tus módulos» usan la misma entrada que el mostrador (`mostrador-aparecer`), escalonada. Al pasar el cursor, el icono del paquete se corre un poco hacia la derecha. El encabezado de Usuarios, Productos, Compras, Proveedores y Reportes entra con esa misma animación.
