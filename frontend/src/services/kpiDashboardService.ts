import {
  consultarReporteVentas,
  fechaHoy,
  semanaActual,
  mesActual,
  rangoDelPeriodo,
  type PeriodoReporte,
  type ProductoVendido,
} from './reporteVentasService';
import { inventarioService } from './inventarioService';
import { compraService } from './compraService';
import { gastosService } from './gastosService';
import { usuariosService } from './usuariosService';
import { bitacoraService } from './bitacoraService';
import type { MateriaPrimaStock } from '../types/inventario';
import type { CompraResumen } from '../types/compra';
import type { MovimientoEconomico } from '../types/gasto';
import type { UsuarioFila } from '../types/usuarios';
import type { RegistroBitacora } from '../types/bitacora';

export interface OwnerKpiSummary {
  periodo: PeriodoReporte;
  ingresosTotales: number;
  transaccionesVentas: number;
  totalComprasInsumos: number;
  totalGastosOperativos: number;
  resultadoEconomico: number;
  margenOperativoPct: number;
  insumosCriticosCount: number;
  insumosCriticos: Array<{ id: number; nombre: string; stock: number; stockMinimo: number; unidad: string }>;
  topProductos: Array<{ nombre: string; cantidad: number; subtotal: number }>;
}

export interface AdminKpiSummary {
  totalUsuarios: number;
  usuariosActivos: number;
  usuariosInactivos: number;
  eventosHoy: number;
  intentosFallidosOSeguridad: number;
  distribucionRoles: Array<{ rol: string; total: number }>;
  ultimosEventosBitacora: Array<{ id: number; usuario: string; accion: string; modulo: string; fecha: string; descripcion: string }>;
}

export const kpiDashboardService = {
  /**
   * Agrega métricas estratégicas para el Propietario (CU05, CU07, CU08, CU09, CU13, CU20, CU21, CU25)
   */
  async obtenerResumenPropietario(periodo: PeriodoReporte = 'mes'): Promise<OwnerKpiSummary> {
    const valorPeriodo = periodo === 'dia' ? fechaHoy() : periodo === 'semana' ? semanaActual() : mesActual();
    const rango = rangoDelPeriodo(periodo, valorPeriodo);

    // 1. Consultar ventas del periodo
    const reporteVentas = await consultarReporteVentas(rango.desde, rango.hasta);
    const ingresos = parseFloat(reporteVentas.total || '0') || 0;

    // 2. Consultar compras, gastos e inventario
    const [compras, gastos, materiasPrimas] = await Promise.all([
      compraService.listar({ fecha_desde: rango.desde, fecha_hasta: rango.hasta }).catch(() => [] as CompraResumen[]),
      gastosService.listar({ fecha_desde: rango.desde, fecha_hasta: rango.hasta }).catch(() => [] as MovimientoEconomico[]),
      inventarioService.listarStock().catch(() => [] as MateriaPrimaStock[]),
    ]);

    const comprasFiltradas = compras || [];
    const totalCompras = comprasFiltradas.reduce((acc: number, c: CompraResumen) => acc + (parseFloat(c.total) || 0), 0);

    const gastosFiltrados = (gastos || []).filter((g: MovimientoEconomico) => !g.anulado);
    const totalGastos = gastosFiltrados.reduce((acc: number, g: MovimientoEconomico) => acc + (parseFloat(g.monto) || 0), 0);

    const resultado = ingresos - (totalCompras + totalGastos);
    const egresosTotales = totalCompras + totalGastos;
    const margen = egresosTotales > 0 ? ((resultado / (ingresos || 1)) * 100) : (ingresos > 0 ? 100 : 0);

    // Insumos críticos (stock <= stock_minimo)
    const insumosCriticos = (materiasPrimas || [])
      .filter((m: MateriaPrimaStock) => Number(m.stock_actual) <= Number(m.stock_minimo) && m.activo)
      .map((m: MateriaPrimaStock) => ({
        id: m.id_materia_prima,
        nombre: m.nombre,
        stock: Number(m.stock_actual),
        stockMinimo: Number(m.stock_minimo),
        unidad: m.unidad_medida,
      }));

    // Top productos vendidos
    const topProductos = (reporteVentas.productos || [])
      .slice(0, 5)
      .map((p: ProductoVendido) => ({
        nombre: p.nombre,
        cantidad: p.cantidad,
        subtotal: parseFloat(p.subtotal) || 0,
      }));

    return {
      periodo,
      ingresosTotales: ingresos,
      transaccionesVentas: reporteVentas.cantidad || 0,
      totalComprasInsumos: totalCompras,
      totalGastosOperativos: totalGastos,
      resultadoEconomico: resultado,
      margenOperativoPct: Number(margen.toFixed(1)),
      insumosCriticosCount: insumosCriticos.length,
      insumosCriticos,
      topProductos,
    };
  },

  /**
   * Agrega métricas operativas de seguridad y auditoría para el Administrador (CU03, CU04, CU26)
   */
  async obtenerResumenAdmin(): Promise<AdminKpiSummary> {
    const [usuariosResp, bitacoraResp] = await Promise.all([
      usuariosService.listar().catch(() => ({ count: 0, results: [] })),
      bitacoraService.listar().catch(() => ({ count: 0, results: [] })),
    ]);

    const usuarios: UsuarioFila[] = usuariosResp.results || [];
    const activos = usuarios.filter((u: UsuarioFila) => u.activo).length;
    const inactivos = usuarios.length - activos;

    // Conteo por roles
    const rolesMap = new Map<string, number>();
    for (const u of usuarios) {
      const nombreRol = u.rol || 'Sin Rol';
      rolesMap.set(nombreRol, (rolesMap.get(nombreRol) || 0) + 1);
    }
    const distribucionRoles = Array.from(rolesMap.entries()).map(([rol, total]) => ({ rol, total }));

    const bitacora: RegistroBitacora[] = bitacoraResp.results || [];
    const hoyStr = fechaHoy();
    const eventosHoy = bitacora.filter((b: RegistroBitacora) => (b.fecha_hora || '').startsWith(hoyStr)).length;

    // Eventos de seguridad (login fallido, bloqueo, clave cambiada)
    const eventosSeguridad = bitacora.filter((b: RegistroBitacora) =>
      b.accion.toLowerCase().includes('fall') ||
      b.accion.toLowerCase().includes('bloque') ||
      b.accion.toLowerCase().includes('password') ||
      b.accion.toLowerCase().includes('contrase')
    ).length;

    const ultimosEventos = bitacora.slice(0, 8).map((b: RegistroBitacora) => ({
      id: b.id_bitacora,
      usuario: b.nombre_completo || b.nombre_usuario || b.nombre_usuario_intento || 'Sistema',
      accion: b.accion_etiqueta || b.accion,
      modulo: b.tabla_afectada || 'General',
      fecha: b.fecha_hora,
      descripcion: b.descripcion || '',
    }));

    return {
      totalUsuarios: usuariosResp.count || usuarios.length,
      usuariosActivos: activos,
      usuariosInactivos: inactivos,
      eventosHoy,
      intentosFallidosOSeguridad: eventosSeguridad,
      distribucionRoles,
      ultimosEventosBitacora: ultimosEventos,
    };
  },
};

export default kpiDashboardService;
