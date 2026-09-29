import type { ElementType } from 'react';
import {
  BarChart3,
  Package,
  ShoppingCart,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';

export interface NavModule {
  /** Nombre visible de la ventana. */
  label: string;
  /** Ruta interna de la ventana. */
  to: string;
  icon: ElementType;
  /** Casos de Uso que implementa la ventana. */
  casosDeUso: string;
  /**
   * Permisos que habilitan la ventana. Semántica "cualquiera de" (OR):
   * basta con uno para que el actor la vea.
   */
  permisos: string[];
  /**
   * `false` mientras la ventana no tenga pantalla implementada. El Sidebar
   * ignora los módulos no implementados para no publicar enlaces muertos.
   * Pasa a `true` el mismo día que se cree la carpeta en `src/apps/dashboard/`.
   */
  implemented: boolean;
}

/**
 * Un único menú para los cuatro actores. Lo que cambia por rol NO es el
 * dashboard, es qué entradas de este arreglo sobreviven al filtro de permisos.
 *
 * Los nombres de `permisos` deben coincidir exactamente con la tabla `permiso`
 * poblada por `python manage.py seed_usuarios`.
 */
export const NAV_MODULES: NavModule[] = [
  {
    label: 'Usuarios y Seguridad',
    to: '/dashboard/usuarios',
    icon: ShieldCheck,
    casosDeUso: 'CU3, CU4, CU26',
    permisos: ['gestionar_usuarios', 'asignar_permisos', 'consultar_bitacora'],
    // `true` desde el 2026-09-28: existe `apps/dashboard/usuarios/UsuariosPage.tsx`
    // con el CU3 y CU4 completos. CU26 (bitácora) agregará su propia pestaña
    // dentro de esta misma ventana, no un módulo aparte del menú.
    implemented: true,
  },
  {
    label: 'Productos e Inventario',
    to: '/dashboard/productos',
    icon: Package,
    casosDeUso: 'CU5, CU8–CU12, CU18, CU19',
    permisos: ['gestionar_productos', 'gestionar_inventario', 'registrar_produccion'],
    implemented: false,
  },
  {
    label: 'Compras y Proveedores',
    to: '/dashboard/compras',
    icon: ShoppingCart,
    casosDeUso: 'CU6, CU7, CU20',
    permisos: ['gestionar_proveedores', 'registrar_compras', 'registrar_gastos'],
    implemented: false,
  },
  {
    label: 'Ventas y Pedidos',
    to: '/dashboard/ventas',
    icon: TrendingUp,
    casosDeUso: 'CU13–CU17',
    permisos: ['registrar_ventas', 'registrar_pedidos'],
    implemented: false,
  },
  {
    label: 'Reportes',
    to: '/dashboard/reportes',
    icon: BarChart3,
    casosDeUso: 'CU21–CU25',
    permisos: ['generar_reportes'],
    implemented: false,
  },
];
