import api from './api';
import type {
  BalanceMaterialesSimulacion,
  ConsumoInsumoCalculado,
  ProduccionFiltros,
  ProduccionRegistro,
  RecetaProducto,
  RegistrarProduccionPayload,
} from '../types/produccion';

/**
 * Bandera para desarrollo frontend desacoplado (Ciclo 2 - CU10).
 *
 * Mientras el equipo de backend integra los modelos de inventario en conjunto
 * (CU07/CU08/CU10), mantenemos esta bandera en `true`. Permite probar toda
 * la interfaz de usuario, validaciones reactivas y simulación MRP en vivo.
 *
 * Una vez que el backend esté desplegado, se cambia a `false` y todo el código
 * consumirá automáticamente las rutas `/api/productos/producciones/`.
 */
const USAR_MOCK = true;

// ============================================================================
// DATOS MOCK OFICIALES (Fuente: Poblacion_4_Dias_Panaderia_Santiago.sql)
// ============================================================================

interface MockMateriaPrima {
  id_materia_prima: number;
  nombre: string;
  unidad_medida: string;
  stock_actual: number;
}

const MOCK_MATERIAS_PRIMAS: MockMateriaPrima[] = [
  { id_materia_prima: 1, nombre: 'Harina', unidad_medida: 'kg', stock_actual: 180.0 },
  { id_materia_prima: 2, nombre: 'Azúcar', unidad_medida: 'kg', stock_actual: 45.0 },
  { id_materia_prima: 3, nombre: 'Levadura', unidad_medida: 'kg', stock_actual: 8.5 },
  { id_materia_prima: 4, nombre: 'Sal', unidad_medida: 'kg', stock_actual: 18.0 },
  { id_materia_prima: 5, nombre: 'Huevos', unidad_medida: 'unidad', stock_actual: 280.0 },
  { id_materia_prima: 6, nombre: 'Leche', unidad_medida: 'litro', stock_actual: 55.0 },
  { id_materia_prima: 7, nombre: 'Mantequilla', unidad_medida: 'kg', stock_actual: 14.0 },
];

const MOCK_RECETAS: RecetaProducto[] = [
  {
    id_producto: 1,
    nombre_producto: 'Marraqueta',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.06 },
      { id_materia_prima: 3, nombre_insumo: 'Levadura', unidad_medida: 'kg', cantidad_requerida: 0.002 },
      { id_materia_prima: 4, nombre_insumo: 'Sal', unidad_medida: 'kg', cantidad_requerida: 0.001 },
    ],
  },
  {
    id_producto: 2,
    nombre_producto: 'Casero',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.07 },
      { id_materia_prima: 3, nombre_insumo: 'Levadura', unidad_medida: 'kg', cantidad_requerida: 0.002 },
      { id_materia_prima: 4, nombre_insumo: 'Sal', unidad_medida: 'kg', cantidad_requerida: 0.001 },
    ],
  },
  {
    id_producto: 3,
    nombre_producto: 'Tortilla',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.15 },
      { id_materia_prima: 3, nombre_insumo: 'Levadura', unidad_medida: 'kg', cantidad_requerida: 0.003 },
      { id_materia_prima: 4, nombre_insumo: 'Sal', unidad_medida: 'kg', cantidad_requerida: 0.002 },
      { id_materia_prima: 6, nombre_insumo: 'Leche', unidad_medida: 'litro', cantidad_requerida: 0.02 },
    ],
  },
  {
    id_producto: 4,
    nombre_producto: 'Arani',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.08 },
      { id_materia_prima: 3, nombre_insumo: 'Levadura', unidad_medida: 'kg', cantidad_requerida: 0.002 },
      { id_materia_prima: 2, nombre_insumo: 'Azúcar', unidad_medida: 'kg', cantidad_requerida: 0.01 },
    ],
  },
  {
    id_producto: 5,
    nombre_producto: 'Chama',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.08 },
      { id_materia_prima: 3, nombre_insumo: 'Levadura', unidad_medida: 'kg', cantidad_requerida: 0.002 },
      { id_materia_prima: 2, nombre_insumo: 'Azúcar', unidad_medida: 'kg', cantidad_requerida: 0.015 },
    ],
  },
  {
    id_producto: 6,
    nombre_producto: 'Integral',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.07 },
      { id_materia_prima: 3, nombre_insumo: 'Levadura', unidad_medida: 'kg', cantidad_requerida: 0.002 },
      { id_materia_prima: 4, nombre_insumo: 'Sal', unidad_medida: 'kg', cantidad_requerida: 0.001 },
    ],
  },
  {
    id_producto: 7,
    nombre_producto: 'Pan Dulce',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.06 },
      { id_materia_prima: 2, nombre_insumo: 'Azúcar', unidad_medida: 'kg', cantidad_requerida: 0.02 },
      { id_materia_prima: 5, nombre_insumo: 'Huevos', unidad_medida: 'unidad', cantidad_requerida: 0.05 },
      { id_materia_prima: 7, nombre_insumo: 'Mantequilla', unidad_medida: 'kg', cantidad_requerida: 0.01 },
    ],
  },
  {
    id_producto: 8,
    nombre_producto: 'Pan con Azúcar',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.06 },
      { id_materia_prima: 2, nombre_insumo: 'Azúcar', unidad_medida: 'kg', cantidad_requerida: 0.025 },
    ],
  },
  {
    id_producto: 9,
    nombre_producto: 'Gusanito',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.09 },
      { id_materia_prima: 2, nombre_insumo: 'Azúcar', unidad_medida: 'kg', cantidad_requerida: 0.02 },
      { id_materia_prima: 7, nombre_insumo: 'Mantequilla', unidad_medida: 'kg', cantidad_requerida: 0.015 },
    ],
  },
  {
    id_producto: 10,
    nombre_producto: 'Pan Mollete',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.05 },
      { id_materia_prima: 2, nombre_insumo: 'Azúcar', unidad_medida: 'kg', cantidad_requerida: 0.01 },
      { id_materia_prima: 6, nombre_insumo: 'Leche', unidad_medida: 'litro', cantidad_requerida: 0.01 },
    ],
  },
  {
    id_producto: 11,
    nombre_producto: 'Pan Galleta',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.04 },
      { id_materia_prima: 2, nombre_insumo: 'Azúcar', unidad_medida: 'kg', cantidad_requerida: 0.01 },
    ],
  },
  {
    id_producto: 12,
    nombre_producto: 'Pan de Leche',
    insumos: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', unidad_medida: 'kg', cantidad_requerida: 0.06 },
      { id_materia_prima: 6, nombre_insumo: 'Leche', unidad_medida: 'litro', cantidad_requerida: 0.03 },
      { id_materia_prima: 2, nombre_insumo: 'Azúcar', unidad_medida: 'kg', cantidad_requerida: 0.015 },
      { id_materia_prima: 7, nombre_insumo: 'Mantequilla', unidad_medida: 'kg', cantidad_requerida: 0.01 },
    ],
  },
];

const MOCK_COSTOS_PRODUCTO: Record<number, number> = {
  1: 0.4,
  2: 0.45,
  3: 1.2,
  4: 0.5,
  5: 0.55,
  6: 0.6,
  7: 0.7,
  8: 0.65,
  9: 1.0,
  10: 0.4,
  11: 0.35,
  12: 0.8,
};

let mockHistorialProducciones: ProduccionRegistro[] = [
  {
    id_produccion: 3,
    fecha: '2026-09-08',
    jornada: 'unica',
    usuario_id: 6,
    usuario_nombre: 'Pedro Torrez Salvatierra',
    total_unidades: 870,
    total_variedades: 12,
    costo_total: '479.50',
    fecha_hora_registro: '2026-09-08T20:00:00Z',
    detalles: [
      { id_detalle_produccion: 25, id_producto: 1, nombre_producto: 'Marraqueta', cantidad_producida: 200, costo_unitario: '0.40', subtotal_costo: '80.00' },
      { id_detalle_produccion: 26, id_producto: 2, nombre_producto: 'Casero', cantidad_producida: 100, costo_unitario: '0.45', subtotal_costo: '45.00' },
      { id_detalle_produccion: 27, id_producto: 3, nombre_producto: 'Tortilla', cantidad_producida: 30, costo_unitario: '1.20', subtotal_costo: '36.00' },
      { id_detalle_produccion: 28, id_producto: 4, nombre_producto: 'Arani', cantidad_producida: 80, costo_unitario: '0.50', subtotal_costo: '40.00' },
      { id_detalle_produccion: 29, id_producto: 5, nombre_producto: 'Chama', cantidad_producida: 60, costo_unitario: '0.55', subtotal_costo: '33.00' },
      { id_detalle_produccion: 30, id_producto: 6, nombre_producto: 'Integral', cantidad_producida: 50, costo_unitario: '0.60', subtotal_costo: '30.00' },
      { id_detalle_produccion: 31, id_producto: 7, nombre_producto: 'Pan Dulce', cantidad_producida: 60, costo_unitario: '0.70', subtotal_costo: '42.00' },
      { id_detalle_produccion: 32, id_producto: 8, nombre_producto: 'Pan con Azúcar', cantidad_producida: 50, costo_unitario: '0.65', subtotal_costo: '32.50' },
      { id_detalle_produccion: 33, id_producto: 9, nombre_producto: 'Gusanito', cantidad_producida: 40, costo_unitario: '1.00', subtotal_costo: '40.00' },
      { id_detalle_produccion: 34, id_producto: 10, nombre_producto: 'Pan Mollete', cantidad_producida: 70, costo_unitario: '0.40', subtotal_costo: '28.00' },
      { id_detalle_produccion: 35, id_producto: 11, nombre_producto: 'Pan Galleta', cantidad_producida: 90, costo_unitario: '0.35', subtotal_costo: '31.50' },
      { id_detalle_produccion: 36, id_producto: 12, nombre_producto: 'Pan de Leche', cantidad_producida: 40, costo_unitario: '0.80', subtotal_costo: '32.00' },
    ],
    consumos_materia_prima: [
      { id_materia_prima: 1, nombre_insumo: 'Harina', cantidad_descontada: 57.9, unidad_medida: 'kg' },
      { id_materia_prima: 2, nombre_insumo: 'Azúcar', cantidad_descontada: 7.15, unidad_medida: 'kg' },
      { id_materia_prima: 3, nombre_insumo: 'Levadura', cantidad_descontada: 1.07, unidad_medida: 'kg' },
      { id_materia_prima: 4, nombre_insumo: 'Sal', cantidad_descontada: 0.41, unidad_medida: 'kg' },
      { id_materia_prima: 5, nombre_insumo: 'Huevos', cantidad_descontada: 3.0, unidad_medida: 'unidad' },
      { id_materia_prima: 6, nombre_insumo: 'Leche', cantidad_descontada: 2.5, unidad_medida: 'litro' },
      { id_materia_prima: 7, nombre_insumo: 'Mantequilla', cantidad_descontada: 1.6, unidad_medida: 'kg' },
    ],
  },
  {
    id_produccion: 2,
    fecha: '2026-09-07',
    jornada: 'unica',
    usuario_id: 5,
    usuario_nombre: 'Miguel Ángel Rojas',
    total_unidades: 870,
    total_variedades: 12,
    costo_total: '479.50',
    fecha_hora_registro: '2026-09-07T20:00:00Z',
    detalles: [],
  },
  {
    id_produccion: 1,
    fecha: '2026-09-06',
    jornada: 'unica',
    usuario_id: 5,
    usuario_nombre: 'Miguel Ángel Rojas',
    total_unidades: 870,
    total_variedades: 12,
    costo_total: '479.50',
    fecha_hora_registro: '2026-09-06T20:00:00Z',
    detalles: [],
  },
];

// ============================================================================
// SERVICIO DE PRODUCCIÓN (CU10 & CU11)
// ============================================================================

export const produccionService = {
  /**
   * Obtiene la lista de recetas (BOM) para cálculo local inmediato.
   */
  async obtenerRecetas(): Promise<RecetaProducto[]> {
    if (USAR_MOCK) {
      return [...MOCK_RECETAS];
    }
    const response = await api.get<RecetaProducto[]>('/productos/recetas/');
    return response.data;
  },

  /**
   * Simulación y explosión de materiales en tiempo real (MRP).
   * Calcula el consumo de cada insumo y verifica si el stock actual alcanza.
   */
  async simularConsumo(
    detalles: Array<{ id_producto: number; cantidad_producida: number }>
  ): Promise<BalanceMaterialesSimulacion> {
    if (USAR_MOCK) {
      // Simula cálculo reactivo en base a las recetas locales
      const consumoPorInsumo: Record<number, number> = {};
      let totalUnidades = 0;
      let costoEstimado = 0;

      for (const item of detalles) {
        if (!item.cantidad_producida || item.cantidad_producida <= 0) continue;
        totalUnidades += item.cantidad_producida;
        costoEstimado += item.cantidad_producida * (MOCK_COSTOS_PRODUCTO[item.id_producto] || 0.5);

        const receta = MOCK_RECETAS.find((r) => r.id_producto === item.id_producto);
        if (receta) {
          for (const insumo of receta.insumos) {
            const consumo = item.cantidad_producida * insumo.cantidad_requerida;
            consumoPorInsumo[insumo.id_materia_prima] =
              (consumoPorInsumo[insumo.id_materia_prima] || 0) + consumo;
          }
        }
      }

      let esViable = true;
      const insumosCalculados: ConsumoInsumoCalculado[] = MOCK_MATERIAS_PRIMAS.map((mp) => {
        const requerido = Number((consumoPorInsumo[mp.id_materia_prima] || 0).toFixed(3));
        const disponible = mp.stock_actual;
        const suficiente = disponible >= requerido;
        if (!suficiente && requerido > 0) {
          esViable = false;
        }
        const diferencia = suficiente ? 0 : Number((requerido - disponible).toFixed(3));

        return {
          id_materia_prima: mp.id_materia_prima,
          nombre_insumo: mp.nombre,
          unidad_medida: mp.unidad_medida,
          cantidad_requerida: requerido,
          stock_disponible: disponible,
          suficiente,
          diferencia_faltante: diferencia,
        };
      }).filter((item) => item.cantidad_requerida > 0);

      return {
        es_viable: esViable,
        total_panes_unidades: totalUnidades,
        costo_estimado_total: Number(costoEstimado.toFixed(2)),
        insumos: insumosCalculados,
      };
    }

    const response = await api.post<BalanceMaterialesSimulacion>(
      '/productos/producciones/simular/',
      { detalles }
    );
    return response.data;
  },

  /**
   * Registra una jornada de producción (CU10).
   * Realiza la transacción atómica: descuenta insumos y suma producto terminado.
   */
  async registrarProduccion(
    payload: RegistrarProduccionPayload
  ): Promise<ProduccionRegistro> {
    if (USAR_MOCK) {
      // Simula retraso de red de 600ms
      await new Promise((resolve) => setTimeout(resolve, 600));

      const balance = await this.simularConsumo(payload.detalles);
      if (!balance.es_viable) {
        const faltantes = balance.insumos
          .filter((i) => !i.suficiente)
          .map((i) => `${i.nombre_insumo} (faltan ${i.diferencia_faltante} ${i.unidad_medida})`)
          .join(', ');
        throw new Error(
          `No hay suficiente materia prima para registrar esta producción: ${faltantes}.`
        );
      }

      // Aplica el descuento al stock simulado
      for (const insumo of balance.insumos) {
        const mp = MOCK_MATERIAS_PRIMAS.find(
          (m) => m.id_materia_prima === insumo.id_materia_prima
        );
        if (mp) {
          mp.stock_actual = Number(
            (mp.stock_actual - insumo.cantidad_requerida).toFixed(3)
          );
        }
      }

      // Construye el nuevo registro
      const nuevoId = mockHistorialProducciones.length + 1;
      const nuevoRegistro: ProduccionRegistro = {
        id_produccion: nuevoId,
        fecha: payload.fecha,
        jornada: payload.jornada,
        usuario_id: 1,
        usuario_nombre: 'Personal de Producción en Turno',
        total_unidades: balance.total_panes_unidades,
        total_variedades: payload.detalles.filter((d) => d.cantidad_producida > 0).length,
        costo_total: balance.costo_estimado_total.toFixed(2),
        fecha_hora_registro: new Date().toISOString(),
        detalles: payload.detalles
          .filter((d) => d.cantidad_producida > 0)
          .map((d, idx) => {
            const receta = MOCK_RECETAS.find((r) => r.id_producto === d.id_producto);
            const costo = MOCK_COSTOS_PRODUCTO[d.id_producto] || 0.5;
            return {
              id_detalle_produccion: nuevoId * 100 + idx,
              id_producto: d.id_producto,
              nombre_producto: receta?.nombre_producto || `Producto #${d.id_producto}`,
              cantidad_producida: d.cantidad_producida,
              costo_unitario: costo.toFixed(2),
              subtotal_costo: (costo * d.cantidad_producida).toFixed(2),
            };
          }),
        consumos_materia_prima: balance.insumos.map((i) => ({
          id_materia_prima: i.id_materia_prima,
          nombre_insumo: i.nombre_insumo,
          cantidad_descontada: i.cantidad_requerida,
          unidad_medida: i.unidad_medida,
        })),
      };

      mockHistorialProducciones = [nuevoRegistro, ...mockHistorialProducciones];
      return nuevoRegistro;
    }

    const response = await api.post<ProduccionRegistro>(
      '/productos/producciones/',
      payload
    );
    return response.data;
  },

  /**
   * Consulta el historial de producciones registradas (CU11).
   */
  async listarHistorial(filtros: ProduccionFiltros = {}): Promise<ProduccionRegistro[]> {
    if (USAR_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      let lista = [...mockHistorialProducciones];
      if (filtros.jornada) {
        lista = lista.filter((p) => p.jornada === filtros.jornada);
      }
      if (filtros.fecha_desde) {
        lista = lista.filter((p) => p.fecha >= filtros.fecha_desde!);
      }
      if (filtros.fecha_hasta) {
        lista = lista.filter((p) => p.fecha <= filtros.fecha_hasta!);
      }
      return lista;
    }

    const response = await api.get<ProduccionRegistro[]>('/productos/producciones/', {
      params: filtros,
    });
    return response.data;
  },

  /**
   * Cantidades habituales estándar para botón rápido "Cargar Lote Habitual".
   */
  obtenerLoteHabitual(): Record<number, number> {
    return {
      1: 200, // Marraqueta
      2: 100, // Casero
      3: 30,  // Tortilla
      4: 80,  // Arani
      5: 60,  // Chama
      6: 50,  // Integral
      7: 60,  // Pan Dulce
      8: 50,  // Pan con Azúcar
      9: 40,  // Gusanito
      10: 70, // Pan Mollete
      11: 90, // Pan Galleta
      12: 40, // Pan de Leche
    };
  },
};

export default produccionService;
