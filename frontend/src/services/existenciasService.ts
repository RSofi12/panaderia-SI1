/**
 * Servicio cliente para CU12: Consultar existencias de productos terminados.
 * Autor: Roberto (Equipo Panadería Santiago).
 */
import api from './api';
import type {
  DetalleKardexProducto,
  ExistenciaProducto,
  FiltrosExistencias,
  ResumenExistencias,
} from '../types/existencias';

// Datos de fallback en caso de trabajar en modo mockup o sin conexión al backend
const MOCK_EXISTENCIAS: ExistenciaProducto[] = [
  {
    id_inventario: 1,
    id_producto: 1,
    producto_nombre: 'Marraqueta tradicional',
    producto_descripcion: 'Pan crujiente tradicional elaborado con harina de trigo y sal.',
    categoria_id: 1,
    categoria_nombre: 'Panes Tradicionales',
    precio_venta: '0.80',
    costo_produccion: '0.45',
    porcentaje_ganancia: '77.78',
    stock_actual: 140,
    activo: true,
    valor_total_stock: '112.00',
    estado_stock: 'disponible',
  },
  {
    id_inventario: 2,
    id_producto: 2,
    producto_nombre: 'Pan Arani',
    producto_descripcion: 'Pan típico de masa densa y corteza firme.',
    categoria_id: 1,
    categoria_nombre: 'Panes Tradicionales',
    precio_venta: '1.00',
    costo_produccion: '0.60',
    porcentaje_ganancia: '66.67',
    stock_actual: 80,
    activo: true,
    valor_total_stock: '80.00',
    estado_stock: 'disponible',
  },
  {
    id_inventario: 3,
    id_producto: 3,
    producto_nombre: 'Pan Chama',
    producto_descripcion: 'Pan plano redondo de miga esponjosa y textura suave.',
    categoria_id: 1,
    categoria_nombre: 'Panes Tradicionales',
    precio_venta: '0.80',
    costo_produccion: '0.48',
    porcentaje_ganancia: '66.67',
    stock_actual: 95,
    activo: true,
    valor_total_stock: '76.00',
    estado_stock: 'disponible',
  },
  {
    id_inventario: 4,
    id_producto: 4,
    producto_nombre: 'Pan Casero',
    producto_descripcion: 'Pan hogareño de corteza dorada y miga tierna.',
    categoria_id: 1,
    categoria_nombre: 'Panes Tradicionales',
    precio_venta: '0.80',
    costo_produccion: '0.46',
    porcentaje_ganancia: '73.91',
    stock_actual: 110,
    activo: true,
    valor_total_stock: '88.00',
    estado_stock: 'disponible',
  },
  {
    id_inventario: 5,
    id_producto: 5,
    producto_nombre: 'Pan Tortilla',
    producto_descripcion: 'Pan plano semicrocante ideal para desayunos.',
    categoria_id: 1,
    categoria_nombre: 'Panes Tradicionales',
    precio_venta: '0.70',
    costo_produccion: '0.40',
    porcentaje_ganancia: '75.00',
    stock_actual: 65,
    activo: true,
    valor_total_stock: '45.50',
    estado_stock: 'disponible',
  },
  {
    id_inventario: 6,
    id_producto: 6,
    producto_nombre: 'Pan Integral',
    producto_descripcion: 'Elaborado con harina integral de alto contenido en fibra.',
    categoria_id: 2,
    categoria_nombre: 'Panes Especiales',
    precio_venta: '1.20',
    costo_produccion: '0.75',
    porcentaje_ganancia: '60.00',
    stock_actual: 30,
    activo: true,
    valor_total_stock: '36.00',
    estado_stock: 'disponible',
  },
  {
    id_inventario: 7,
    id_producto: 7,
    producto_nombre: 'Pan Gusanito',
    producto_descripcion: 'Pan dulce trenzado con cubierta espolvoreada.',
    categoria_id: 3,
    categoria_nombre: 'Panes Dulces',
    precio_venta: '1.00',
    costo_produccion: '0.62',
    porcentaje_ganancia: '61.29',
    stock_actual: 45,
    activo: true,
    valor_total_stock: '45.00',
    estado_stock: 'disponible',
  },
  {
    id_inventario: 8,
    id_producto: 8,
    producto_nombre: 'Pan con Azúcar',
    producto_descripcion: 'Pan suave con capa dulce cristalizada.',
    categoria_id: 3,
    categoria_nombre: 'Panes Dulces',
    precio_venta: '1.00',
    costo_produccion: '0.58',
    porcentaje_ganancia: '72.41',
    stock_actual: 25,
    activo: true,
    valor_total_stock: '25.00',
    estado_stock: 'disponible',
  },
  {
    id_inventario: 9,
    id_producto: 9,
    producto_nombre: 'Pan Dulce Especial',
    producto_descripcion: 'Especialidad festiva con pasas y esencia de vainilla.',
    categoria_id: 3,
    categoria_nombre: 'Panes Dulces',
    precio_venta: '1.50',
    costo_produccion: '0.90',
    porcentaje_ganancia: '66.67',
    stock_actual: 15,
    activo: true,
    valor_total_stock: '22.50',
    estado_stock: 'critico',
  },
  {
    id_inventario: 10,
    id_producto: 10,
    producto_nombre: 'Pan Mollete',
    producto_descripcion: 'Pan tradicional suave y redondeado.',
    categoria_id: 1,
    categoria_nombre: 'Panes Tradicionales',
    precio_venta: '0.90',
    costo_produccion: '0.55',
    porcentaje_ganancia: '63.64',
    stock_actual: 18,
    activo: true,
    valor_total_stock: '16.20',
    estado_stock: 'critico',
  },
  {
    id_inventario: 11,
    id_producto: 11,
    producto_nombre: 'Pan Galleta',
    producto_descripcion: 'Pan tostado crocante de larga conservación.',
    categoria_id: 1,
    categoria_nombre: 'Panes Tradicionales',
    precio_venta: '0.60',
    costo_produccion: '0.35',
    porcentaje_ganancia: '71.43',
    stock_actual: 0,
    activo: true,
    valor_total_stock: '0.00',
    estado_stock: 'agotado',
  },
  {
    id_inventario: 12,
    id_producto: 12,
    producto_nombre: 'Pan de Leche',
    producto_descripcion: 'Masa enriquecida con leche entera y mantequilla.',
    categoria_id: 3,
    categoria_nombre: 'Panes Dulces',
    precio_venta: '1.20',
    costo_produccion: '0.70',
    porcentaje_ganancia: '71.43',
    stock_actual: 50,
    activo: true,
    valor_total_stock: '60.00',
    estado_stock: 'disponible',
  },
];

export const existenciasService = {
  /**
   * GET /api/productos-terminados/existencias/
   * Lista todas las existencias de panes con filtros dinámicos.
   */
  async listar(filtros: FiltrosExistencias = {}): Promise<ExistenciaProducto[]> {
    try {
      const response = await api.get<ExistenciaProducto[]>(
        '/productos-terminados/existencias/',
        { params: filtros }
      );
      if (Array.isArray(response.data) && response.data.length > 0) {
        return response.data;
      }
    } catch {
      // Fallback a mock en caso de offline
    }

    // Filtrado local para el mock de contingencia
    let resultado = [...MOCK_EXISTENCIAS];

    if (filtros.q) {
      const qNorm = filtros.q.toLowerCase().trim();
      resultado = resultado.filter(
        (p) =>
          p.producto_nombre.toLowerCase().includes(qNorm) ||
          (p.producto_descripcion && p.producto_descripcion.toLowerCase().includes(qNorm))
      );
    }

    if (filtros.categoria) {
      const catId = Number(filtros.categoria);
      resultado = resultado.filter((p) => p.categoria_id === catId);
    }

    if (filtros.estado_stock) {
      resultado = resultado.filter((p) => p.estado_stock === filtros.estado_stock);
    }

    if (filtros.ordenar_por) {
      switch (filtros.ordenar_por) {
        case 'nombre_desc':
          resultado.sort((a, b) => b.producto_nombre.localeCompare(a.producto_nombre));
          break;
        case 'stock_asc':
          resultado.sort((a, b) => a.stock_actual - b.stock_actual);
          break;
        case 'stock_desc':
          resultado.sort((a, b) => b.stock_actual - a.stock_actual);
          break;
        case 'precio_asc':
          resultado.sort((a, b) => Number(a.precio_venta) - Number(b.precio_venta));
          break;
        case 'precio_desc':
          resultado.sort((a, b) => Number(b.precio_venta) - Number(a.precio_venta));
          break;
        default:
          resultado.sort((a, b) => a.producto_nombre.localeCompare(b.producto_nombre));
      }
    }

    return resultado;
  },

  /**
   * GET /api/productos-terminados/existencias/resumen/
   * Retorna métricas globales para tarjetas KPI.
   */
  async obtenerResumen(): Promise<ResumenExistencias> {
    try {
      const response = await api.get<ResumenExistencias>(
        '/productos-terminados/existencias/resumen/'
      );
      if (response.data && response.data.total_panes_distintos !== undefined) {
        return response.data;
      }
    } catch {
      // Fallback
    }

    const panes = MOCK_EXISTENCIAS;
    const totalUnidades = panes.reduce((acc, p) => acc + p.stock_actual, 0);
    const totalValor = panes.reduce((acc, p) => acc + Number(p.valor_total_stock), 0);

    return {
      total_panes_distintos: panes.length,
      total_unidades_stock: totalUnidades,
      valor_total_inventario: totalValor.toFixed(2),
      productos_agotados: panes.filter((p) => p.estado_stock === 'agotado').length,
      productos_stock_critico: panes.filter((p) => p.estado_stock === 'critico').length,
      productos_disponibles: panes.filter((p) => p.estado_stock === 'disponible').length,
    };
  },

  /**
   * GET /api/productos-terminados/existencias/<id>/movimientos/
   * Retorna los movimientos de kardex para un pan seleccionado.
   */
  async obtenerKardex(idProducto: number): Promise<DetalleKardexProducto> {
    try {
      const response = await api.get<DetalleKardexProducto>(
        `/productos-terminados/existencias/${idProducto}/movimientos/`
      );
      if (response.data) {
        return response.data;
      }
    } catch {
      // Fallback
    }

    const producto = MOCK_EXISTENCIAS.find((p) => p.id_producto === idProducto) ?? MOCK_EXISTENCIAS[0];
    return {
      producto_id: producto.id_producto,
      producto_nombre: producto.producto_nombre,
      stock_actual: producto.stock_actual,
      movimientos: [
        {
          id_movimiento: 1,
          id_inventario: producto.id_inventario,
          producto_nombre: producto.producto_nombre,
          fecha_hora: new Date(Date.now() - 3600000 * 4).toISOString(),
          tipo: 'entrada',
          tipo_display: 'Entrada',
          cantidad: producto.stock_actual + 30,
          id_produccion: 101,
          id_nota_perdida: null,
          origen_detalle: 'Producción / Horneado #101',
        },
        {
          id_movimiento: 2,
          id_inventario: producto.id_inventario,
          producto_nombre: producto.producto_nombre,
          fecha_hora: new Date(Date.now() - 3600000 * 2).toISOString(),
          tipo: 'salida',
          tipo_display: 'Salida',
          cantidad: 30,
          id_produccion: null,
          id_nota_perdida: null,
          origen_detalle: 'Venta en mostrador',
        },
      ],
    };
  },
};

export default existenciasService;
