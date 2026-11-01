/**
 * Tipos e interfaces TypeScript para:
 *  - CU12: Consultar existencias de productos terminados.
 *  - CU18: Registrar baja de productos terminados (mermas/pérdidas).
 * Autor: Roberto (Equipo Panadería Santiago).
 */

export type NivelStock = 'disponible' | 'critico' | 'agotado';

export interface ExistenciaProducto {
  id_inventario: number;
  id_producto: number;
  producto_nombre: string;
  producto_descripcion: string | null;
  categoria_id: number | null;
  categoria_nombre: string;
  precio_venta: string;
  costo_produccion: string;
  porcentaje_ganancia: string;
  stock_actual: number;
  activo: boolean;
  valor_total_stock: string;
  estado_stock: NivelStock;
}

export interface ResumenExistencias {
  total_panes_distintos: number;
  total_unidades_stock: number;
  valor_total_inventario: string;
  productos_agotados: number;
  productos_stock_critico: number;
  productos_disponibles: number;
}

export interface MovimientoProducto {
  id_movimiento: number;
  id_inventario: number;
  producto_nombre: string;
  fecha_hora: string;
  tipo: 'entrada' | 'salida';
  tipo_display: string;
  cantidad: number;
  id_produccion: number | null;
  id_nota_perdida: number | null;
  origen_detalle: string;
}

export interface DetalleKardexProducto {
  producto_id: number;
  producto_nombre: string;
  stock_actual: number;
  movimientos: MovimientoProducto[];
}

export interface FiltrosExistencias {
  q?: string;
  categoria?: string;
  estado_stock?: '' | 'disponible' | 'critico' | 'agotado';
  solo_activos?: boolean;
  ordenar_por?: 'nombre_asc' | 'nombre_desc' | 'stock_asc' | 'stock_desc' | 'precio_asc' | 'precio_desc';
}

/**
 * Entidades para CU18: Registrar baja de productos terminados (Mermas / Pérdidas)
 */
export interface NotaPerdida {
  id_nota_perdida: number;
  id_detalle_produccion: number;
  id_producto: number;
  producto_nombre: string;
  categoria_nombre: string;
  id_usuario: number;
  registrado_por: string;
  produccion_id: number;
  cantidad: number;
  costo_unitario: string;
  costo_total: string;
  fecha_salida: string;
}

export interface RegistrarBajaPayload {
  id_producto: number;
  cantidad: number;
  id_detalle_produccion?: number | null;
  motivo?: string;
  observaciones?: string;
  costo_unitario?: number | string | null;
}

export interface FiltrosMermas {
  id_producto?: number;
  q?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}
