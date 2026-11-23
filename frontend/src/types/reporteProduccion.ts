export interface ProductoProducido {
  nombre: string;
  cantidad: number;
  vendidas: number;
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
  diferencia: number;
  costo: string;
  manana: number;
  tarde: number;
  noche: number;
  lotes: LoteProduccion[];
  productos: ProductoProducido[];
}
