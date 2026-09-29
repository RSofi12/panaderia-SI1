export interface CategoriaProducto {
  id_categoria: number;
  nombre: string;
  descripcion: string | null;
}

/** Los montos llegan como texto desde DRF (DecimalField) para no perder precisión. */
export interface Producto {
  id_producto: number;
  id_categoria: number | null;
  categoria_nombre: string | null;
  nombre: string;
  descripcion: string | null;
  costo_produccion: string;
  porcentaje_ganancia: string;
  precio_sugerido: string;
  precio_venta: string;
  fecha_registro: string;
  activo: boolean;
}

export interface ProductoPayload {
  id_categoria: number | null;
  nombre: string;
  descripcion: string;
  costo_produccion: string;
  porcentaje_ganancia: string;
  precio_venta: string;
}

export interface ProductoFiltros {
  nombre?: string;
  id_categoria?: string;
  activo?: 'true' | 'false';
}
