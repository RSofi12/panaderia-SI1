/** CU19: el precio conserva el texto decimal recibido de Django REST Framework. */
export interface HistorialPrecioProducto {
  id_historial: number;
  id_producto: number;
  producto_nombre: string;
  producto_activo: boolean;
  precio: string;
  fecha_inicio: string;
}

export interface HistorialPrecioFiltros {
  id_producto?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface HistorialPrecioPagina {
  count: number;
  next: string | null;
  previous: string | null;
  results: HistorialPrecioProducto[];
}
