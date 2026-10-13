/** Los decimales de la API llegan como texto para conservar su precisión. */
export interface AlertaBajoStock {
  id_materia_prima: number;
  nombre: string;
  unidad_medida: string;
  stock_actual: string;
  stock_minimo: string;
  faltante: string;
}

export const ROLES_ALERTAS_BAJO_STOCK = [
  'Administrador',
  'Propietario',
  'Personal de Producción',
];
