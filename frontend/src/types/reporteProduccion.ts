export interface MermaProduccion {
  id_nota_perdida: number;
  fecha: string;
  producto: string;
  cantidad: number;
  costo_unitario: string;
  costo_total: string;
  motivo: string;
  observaciones: string;
  responsable: string;
}

export interface ProductoProducido {
  nombre: string;
  cantidad: number;
  vendidas: number;
  mermadas?: number;
  diferencia: number;
  costo: string;
}

export interface LoteProduccion {
  id_produccion: number;
  fecha: string;
  jornada: string;
  jornada_codigo: string;
  responsable: string;
  unidades: number;
  variedades: number;
  costo: string;
}

export interface ReporteProduccion {
  desde: string;
  hasta: string;
  cantidad: number;
  unidades: number;
  unidades_vendidas: number;
  unidades_mermadas?: number;
  costo_mermas?: string;
  diferencia: number;
  costo: string;
  manana: number;
  tarde: number;
  noche: number;
  lotes: LoteProduccion[];
  productos: ProductoProducido[];
  mermas?: MermaProduccion[];
}
