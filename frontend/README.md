# Frontend — Panadería Santiago

Cliente web del Sistema de Información. SPA con **React 19 + TypeScript + Vite 8 + Tailwind CSS v4**, consumiendo la API REST del backend Django por HTTP/JSON.

> Este proyecto es una **Startup** de Vite + React + TS. Consulta los scripts disponibles en `package.json`.

---

## 🚀 Puesta en marcha

```bash
cd frontend
npm install
npm run dev
```

La aplicación queda disponible en `http://localhost:5173`.

| Script | Descripción |
|---|---|
| `npm run dev` | Servidor de desarrollo con HMR |
| `npm run build` | Typecheck (`tsc -b`) + build de producción en `dist/` |
| `npm run lint` | ESLint (flat config) |
| `npm run preview` | Sirve el build de producción localmente |

### Variables de entorno

Crear `frontend/.env` a partir del ejemplo:

```bash
VITE_API_URL=http://localhost:8000/api
```

> ⚠️ Solo las variables con prefijo `VITE_` llegan al navegador. **Nunca** coloques secretos ahí: todo lo que exista en ese archivo queda visible para el usuario final.

---

## 🗂️ Organización del código

El frontend se organiza **por ventanas / flujo visual del usuario**, en `src/apps/`. La justificación de por qué el frontend se organiza por pantallas y el backend por paquetes de dominio está en [`../docs/ai/ARCHITECTURE.md`](../docs/ai/ARCHITECTURE.md) (sección 3).

```
src/
├── apps/                  # ⭐ PANTALLAS — una carpeta por ventana
│   ├── auth/
│   │   └── LoginPage.tsx  #   CU1  Iniciar sesión
│   └── dashboard/
│       ├── DashboardLayout.tsx  # Shell único (Sidebar + Topbar + Outlet)
│       ├── DashboardHome.tsx    # Identidad del actor y sus módulos
│       ├── navigation.ts        # Menú único, filtrado por permisos (RBAC)
│       └── components/          # Sidebar, Topbar, UserAvatar
├── components/            # UI compartida (Button, Input, Modal, DataTable…)
├── contexts/              # Estado global
│   ├── AuthContext.ts     #   Contexto + hook useAuth()
│   └── AuthProvider.tsx   #   Componente AuthProvider (lógica de sesión)
├── routes/                # AppRoutes.tsx (tabla de rutas) + ProtectedRoute.tsx
├── services/              # api.ts (Axios + interceptores) + authService.ts
├── types/                 # Contratos TypeScript (Usuario, Rol, Permiso…)
├── assets/                # Logos e imágenes
├── App.tsx                # Shell raíz
├── main.tsx               # Punto de entrada (createRoot)
└── index.css              # Tailwind v4 + estilos base
```

### Un solo dashboard para los cuatro actores

No existe un dashboard por rol. Existe **un** `DashboardLayout` y lo que cambia por actor es **qué entradas del menú sobreviven al filtro de permisos**.

`navigation.ts` declara los módulos con los permisos que los habilitan (semántica OR: basta con uno):

| Módulo | Permisos que lo habilitan | CU |
|---|---|---|
| Usuarios y Seguridad | `gestionar_usuarios`, `consultar_bitacora` | CU3, CU4, CU26 |
| Productos e Inventario | `gestionar_productos`, `gestionar_inventario`, `registrar_produccion` | CU5, CU8–CU12, CU18, CU19 |
| Compras y Proveedores | `gestionar_proveedores`, `registrar_compras`, `registrar_gastos` | CU6, CU7, CU20 |
| Ventas y Pedidos | `registrar_ventas`, `registrar_pedidos` | CU13–CU17 |
| Reportes | `generar_reportes` | CU21–CU25 |

Cada entrada tiene `implemented: false` mientras su carpeta no exista, para no publicar enlaces a ventanas que darían 404. Al implementar un CU:

1. Crear `src/apps/dashboard/<modulo>/` con la pantalla.
2. Poner `implemented: true` en su entrada de `navigation.ts`.
3. Registrar la ruta anidada en `AppRoutes.tsx`.

Con el seed actual: Administrador ve 5/5 módulos, Propietario 4/5, Ventas 2/5, Producción 1/5.

### Mapeo de carpetas a Casos de Uso

| Carpeta | CU implementados |
|---|---|
| `apps/auth/` | CU1 (Login), CU2 (Recuperar contraseña) |
| `apps/dashboard/usuarios/` | CU3, CU4, CU26 |
| `apps/dashboard/productos/` | CU5, CU8–CU12, CU18, CU19 |
| `apps/dashboard/compras/` | CU6, CU7, CU20 |
| `apps/dashboard/ventas/` | CU13–CU17 |
| `apps/dashboard/reportes/` | CU21–CU25 |

Las carpetas se crean **cuando se implemente su CU**, nunca como placeholders vacías.

---

## 📏 Reglas de la casa

1. **Ninguna pantalla llama a `axios` directamente.** Toda la comunicación pasa por `src/services/`, y los contratos de datos se tipan en `src/types/`.
2. **El backend es la autoridad.** No recalcular precios, stock, permisos ni cálculos de producción en el cliente: se renderiza lo que la API devuelve.
3. **Toda pantalla no pública va detrás de `ProtectedRoute`**, registrada en `AppRoutes.tsx`. Ocultar un botón es UX, **no** seguridad.
4. **Tokens en `localStorage`** bajo `access_token`, `refresh_token`, `user_data`. El interceptor 401 de `api.ts` los rota con la guarda `_retry`. No crear un mecanismo paralelo.
5. **TypeScript estricto:** nada de `any`, `@ts-ignore` ni tipos ad-hoc duplicados.
6. **Naming:** identificadores, carpetas y código en inglés; etiquetas visibles al usuario y términos de dominio en español.
7. **Toda pantalla maneja cuatro estados:** carga, vacío, error y éxito con datos.
8. **Tailwind v4** se configura vía plugin de Vite. No hay `tailwind.config.js`, ni PostCSS, ni Autoprefixer. Los tokens custom van en un bloque `@theme` dentro de `src/index.css`.
9. **Dependencias congeladas:** solo `react-router-dom`, `axios`, `lucide-react` y `tailwindcss`. No añadir librerías sin consultar.
10. **Validar siempre con `npm run lint` y `npm run build`** antes de dar por terminado un cambio.

---

## 🔐 Autenticación (CU1)

| Pieza | Responsabilidad |
|---|---|
| `services/api.ts` | Instancia Axios, inyección del `Bearer <token>`, refresco automático ante `401` |
| `services/authService.ts` | `login()`, `getMe()`, `logout()` contra `/api/auth/*` |
| `contexts/AuthProvider.tsx` | Estado de sesión, persistencia, `hasPermission()`, `hasRole()` |
| `routes/ProtectedRoute.tsx` | Guardia: exige sesión, permiso o rol |

Cuentas de demostración (seed data): `admin`, `csantiago`, `mgonzales`, `mrojas` — contraseña `Admin123!`.

---

## 🧰 Extender ESLint

Para endurecer el análisis con reglas que requieren información de tipos, consulta la [documentación de ESLint](https://eslint.org/docs/latest/use/configure/configuration-files) y ajusta `eslint.config.js`.
