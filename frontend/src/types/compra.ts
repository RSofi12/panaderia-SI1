// Los DecimalField de DRF llegan como string ("45.00") para no perder precisión.

// ---------- Salida: lo que devuelve Django ----------

export interface CompraDetalle {
  id_detalle_compra: number;
  id_materia_prima: number;
  nombre_materia_prima: string;
  unidad_medida: string;
  cantidad: string;
  precio_unitario: string;
  subtotal: string;
}

export interface Compra {
  id_compra: number;
  id_proveedor: number;
  proveedor_nombre: string;
  registrado_por: string;
  fecha_hora: string;
  total: string;
  detalles: CompraDetalle[];
  advertencias?: string[];
}

export interface CompraResumen {
  id_compra: number;
  id_proveedor: number;
  proveedor_nombre: string;
  registrado_por: string;
  fecha_hora: string;
  total: string;
  cantidad_lineas: number;
}

export interface CompraFiltros {
  id_proveedor?: number | string;
  fecha_desde?: string;
  fecha_hasta?: string;
  search?: string;
}

// ---------- Entrada: lo que el formulario manda en el POST ----------

export interface CompraDetallePayload {
  id_materia_prima: number;
  cantidad: string;
  precio_unitario: string;
}

export interface CompraPayload {
  id_proveedor: number;
  detalles: CompraDetallePayload[];
}

// ---------- Catálogo para el selector de insumos ----------

export interface MateriaPrima {
  id_materia_prima: number;
  nombre: string;
  unidad_medida: string;
  stock_minimo: string;
  stock_actual: string;
  precio_ultima_compra: string | null;
  fecha_registro: string;
  activo: boolean;
}
