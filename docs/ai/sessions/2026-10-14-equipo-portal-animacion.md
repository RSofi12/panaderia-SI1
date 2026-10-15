# Sesión de Desarrollo: Animación del portal de gestión

- **Fecha:** 2026-10-14
- **Autor / Integrante:** Equipo
- **Paquete / Módulo:** `frontend`
- **Casos de Uso abordados:** CU1 (iniciar sesión)
- **Ciclo:** Ciclo 1

---

## 1. 🎯 Objetivo de la sesión

Que la pantalla de entrada se mueva una sola vez al cargar, con el mismo lenguaje del mostrador, sin animar cada campo por separado.

## 2. 🛠️ Cambios realizados

- **Frontend:**
  - `LoginPage.tsx`: la foto de los panes se acerca y se asienta (`portal-foto`). El nombre «Panadería Santiago» y el formulario entran con `mostrador-aparecer`. El icono de Iniciar Sesión se corre al pasar el cursor. Si el acceso falla, el aviso se mueve una vez (`portal-aviso`).
  - `index.css`: esas dos animaciones respetan `prefers-reduced-motion`.

## 3. 🧠 Decisiones técnicas tomadas

- El movimiento vive en la foto, que es lo propio de la panadería. El formulario llega como un solo bloque para no retrasar el foco de los campos.
- No se anima cada cuenta demo: el hover que ya tenían alcanza.

## 4. ⚠️ Pendientes o siguientes pasos

- Ninguno de esta pantalla.

## 5. 🧪 Cómo probar lo implementado

1. Abrir `/login` en una ventana de 1280 px o más.
2. La foto se asienta, el nombre aparece abajo y el formulario entra desde abajo.
3. Pasar el cursor por Iniciar Sesión: el icono se corre a la derecha.
4. En el teléfono la foto no se muestra; solo entra el formulario.
