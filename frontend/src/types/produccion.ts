/**
 * Tipos y contratos de datos para Producción Diaria (CU10 y CU11).
 *
 * Módulo: Gestión de Productos e Inventario (MRP)
 * Actor: Personal de Producción (permiso: registrar_produccion)
 */

export type JornadaProduccion = 'manana' | 'tarde' | 'noche' | 'unica';

export const JORNADAS_LABELS: Record<JornadaProduccion, string> = {
  manana: 'Mañana',
  tarde: 'Tarde',
  noche: 'Noche',
  unica: 'Jornada Única',
};

/** Ítem de producto con receta para el formulario de producción */
export interface ProductoParaProduccion {
  id_producto: number;
  nombre: string;
  categoria_nombre: string | null;
  costo_produccion: string;
  precio_venta: string;
  activo: boolean;
}

/** Insumo requerido por unidad de producto (BOM / Receta) */
export interface RecetaInsumo {
  id_materia_prima: number;
  nombre_insumo: string;
  unidad_medida: string;
  cantidad_requerida: number; // Ej: 0.060 kg
}

/** Receta completa por producto */
export interface RecetaProducto {
  id_producto: number;
  nombre_producto: string;
  insumos: RecetaInsumo[];
}

/** Renglón del formulario editable */
export interface RenglonLoteProduccion {
  id_producto: number;
  nombre_producto: string;
  categoria_nombre: string | null;
  costo_unitario: number;
  cantidad_producida: number;
}

/** Payload enviado al registrar la producción (CU10) */
export interface RegistrarProduccionPayload {
  fecha: string; // Formato YYYY-MM-DD
  jornada: JornadaProduccion;
  observaciones?: string;
  detalles: Array<{
    id_producto: number;
    cantidad_producida: number;
  }>;
}

/** Insumo evaluado en la explosión de materiales (MRP) */
export interface ConsumoInsumoCalculado {
  id_materia_prima: number;
  nombre_insumo: string;
  unidad_medida: string;
  cantidad_requerida: number;
  stock_disponible: number;
  suficiente: boolean;
  diferencia_faltante: number;
}

/** Resultado del cálculo en vivo del balance de materiales */
export interface BalanceMaterialesSimulacion {
  es_viable: boolean;
  total_panes_unidades: number;
  costo_estimado_total: number;
  insumos: ConsumoInsumoCalculado[];
}

/** Detalle de un producto producido dentro de una jornada */
export interface DetalleProduccionHistorial {
  id_detalle_produccion: number;
  id_producto: number;
  nombre_producto: string;
  cantidad_producida: number;
  costo_unitario: string;
  subtotal_costo: string;
}

/** Movimiento de salida de insumo asociado a una producción */
export interface MovimientoInsumoHistorial {
  id_materia_prima: number;
  nombre_insumo: string;
  cantidad_descontada: number;
  unidad_medida: string;
}

/** Cabecera de jornada de producción registrada (CU10 / CU11) */
export interface ProduccionRegistro {
  id_produccion: number;
  fecha: string;
  jornada: JornadaProduccion;
  usuario_id: number;
  usuario_nombre: string;
  total_unidades: number;
  total_variedades: number;
  costo_total: string;
  fecha_hora_registro: string;
  detalles: DetalleProduccionHistorial[];
  consumos_materia_prima?: MovimientoInsumoHistorial[];
}

export interface ProduccionFiltros {
  fecha_desde?: string;
  fecha_hasta?: string;
  jornada?: JornadaProduccion | '';
}
