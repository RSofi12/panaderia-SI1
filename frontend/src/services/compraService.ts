import api from './api';
import type {
  Compra,
  CompraFiltros,
  CompraPayload,
  CompraResumen,
  MateriaPrima,
} from '../types/compra';

export interface MateriaPrimaFiltros {
  nombre?: string;
  activo?: 'true' | 'false';
}

function parametrosCompra(filtros: CompraFiltros = {}): CompraFiltros {
  const params: CompraFiltros = {};
  if (filtros.search?.trim()) params.search = filtros.search.trim();
  if (filtros.id_proveedor) params.id_proveedor = filtros.id_proveedor;
  if (filtros.fecha_desde) params.fecha_desde = filtros.fecha_desde;
  if (filtros.fecha_hasta) params.fecha_hasta = filtros.fecha_hasta;
  return params;
}

function guardarBlob(contenido: Blob, nombre: string) {
  const url = URL.createObjectURL(contenido);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}

function nombreDescarga(filtros: CompraFiltros, extension: 'csv' | 'pdf') {
  const periodo = filtros.fecha_desde || filtros.fecha_hasta
    ? `${filtros.fecha_desde || 'sin-inicio'}_${filtros.fecha_hasta || 'sin-fin'}`
    : 'todas-las-fechas';
  const proveedor = filtros.id_proveedor
    ? `proveedor-${filtros.id_proveedor}`
    : 'todos-los-proveedores';
  return `compras_${periodo}_${proveedor}.${extension}`;
}

export const compraService = {
  /** GET /api/compras/ — listado de compras registradas (CU7) */
  async listar(filtros?: CompraFiltros): Promise<CompraResumen[]> {
    const response = await api.get<CompraResumen[]>('/compras/', { params: parametrosCompra(filtros) });
    return response.data;
  },

  /** GET /api/compras/csv/ o /pdf/ — el mismo listado, en archivo. */
  async descargar(formato: 'csv' | 'pdf', filtros: CompraFiltros = {}): Promise<void> {
    const enviados = parametrosCompra(filtros);
    const response = await api.get<Blob>(`/compras/${formato}/`, {
      params: enviados,
      responseType: 'blob',
    });
    guardarBlob(response.data, nombreDescarga(enviados, formato));
  },

  /** GET /api/compras/<id>/ — cabecera con sus líneas */
  async obtener(id: number): Promise<Compra> {
    const response = await api.get<Compra>(`/compras/${id}/`);
    return response.data;
  },

  /** POST /api/compras/ — registra la compra, suma stock y deja bitácora */
  async registrar(payload: CompraPayload): Promise<Compra> {
    const response = await api.post<Compra>('/compras/', payload);
    return response.data;
  },

  /** GET /api/materias-primas/ — catálogo de insumos para el formulario */
  async listarMateriasPrimas(filtros: MateriaPrimaFiltros = {}): Promise<MateriaPrima[]> {
    const response = await api.get<MateriaPrima[]>('/materias-primas/', { params: filtros });
    return response.data;
  },
};

export default compraService;
