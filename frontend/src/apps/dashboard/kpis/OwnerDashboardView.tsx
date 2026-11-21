import React from 'react';
import {
  TrendingUp,
  Wallet,
  ShoppingCart,
  AlertTriangle,
  ArrowUpRight,
  PieChart as PieIcon,
  BarChart2,
  Scale,
  CreditCard,
  Receipt,
  ClipboardList,
  PackageCheck,
  FileSpreadsheet,
  BarChart3,
  PieChart,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import type { OwnerKpiSummary } from '../../../services/kpiDashboardService';
import KpiCard from './components/KpiCard';
import DonutChart, { type DonutSegment } from './components/DonutChart';
import ColumnBarChart, { type ColumnBarItem } from './components/ColumnBarChart';

interface OwnerDashboardViewProps {
  data: OwnerKpiSummary;
}

export const OwnerDashboardView: React.FC<OwnerDashboardViewProps> = ({ data }) => {
  const formatoMoneda = (val: number) =>
    `Bs ${val.toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const totalEgresos = data.totalComprasInsumos + data.totalGastosOperativos;
  const esGanancia = data.resultadoEconomico >= 0;

  // Segmentos para el Gráfico Circular (Donut) de Composición Económica
  const segmentosDonut: DonutSegment[] = [
    {
      etiqueta: 'Ventas (Ingresos)',
      valor: data.ingresosTotales,
      color: '#059669', // Emerald-600
      formateado: formatoMoneda(data.ingresosTotales),
    },
    {
      etiqueta: 'Compras Materia Prima',
      valor: data.totalComprasInsumos,
      color: '#d97706', // Amber-600
      formateado: formatoMoneda(data.totalComprasInsumos),
    },
    {
      etiqueta: 'Gastos Operativos',
      valor: data.totalGastosOperativos,
      color: '#e11d48', // Rose-600
      formateado: formatoMoneda(data.totalGastosOperativos),
    },
  ];

  // Columnas para el Gráfico de Barras Verticales del Top Productos
  const itemsColumnas: ColumnBarItem[] = data.topProductos.map((p) => ({
    etiqueta: p.nombre,
    valor: p.cantidad,
    valorSecundario: formatoMoneda(p.subtotal),
    color: 'bg-amber-600 hover:bg-amber-700',
  }));

  // Accesos directos a los reportes oficiales del Ciclo 4
  const reportesAtajos = [
    {
      cu: 'CU21',
      titulo: 'Reporte de Ventas',
      desc: 'Detalle por producto y forma de pago',
      icono: TrendingUp,
      color: 'text-emerald-700 bg-emerald-50 hover:border-emerald-300',
    },
    {
      cu: 'CU22',
      titulo: 'Reporte de Producción',
      desc: 'Horneadas físicas vs. ventas',
      icono: BarChart3,
      color: 'text-amber-700 bg-amber-50 hover:border-amber-300',
    },
    {
      cu: 'CU23',
      titulo: 'Reporte de Existencias',
      desc: 'Stock de insumos y pan valorizado',
      icono: PieChart,
      color: 'text-indigo-700 bg-indigo-50 hover:border-indigo-300',
    },
    {
      cu: 'CU24',
      titulo: 'Compras y Gastos',
      desc: 'Compras a proveedores e inversiones',
      icono: Wallet,
      color: 'text-slate-700 bg-slate-100 hover:border-slate-300',
    },
    {
      cu: 'CU25',
      titulo: 'Resultados Económicos',
      desc: 'Balance neto y márgenes consolidados',
      icono: FileSpreadsheet,
      color: 'text-rose-700 bg-rose-50 hover:border-rose-300',
    },
  ];

  return (
    <div className="space-y-6 transition-opacity duration-300 ease-out">
      {/* 1. SECCIÓN DE HEADLINE KPIS (4 Métricas principales) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          titulo="Ingresos por Ventas"
          valor={formatoMoneda(data.ingresosTotales)}
          subtexto={`${data.transaccionesVentas} notas registradas`}
          icono={TrendingUp}
          variante="emerald"
          tendencia={{
            valor: `${data.transaccionesVentas} ventas`,
            esPositiva: true,
          }}
        />

        <KpiCard
          titulo="Total Egresos (Compras + Gastos)"
          valor={formatoMoneda(totalEgresos)}
          subtexto={`Compras: ${formatoMoneda(data.totalComprasInsumos)}`}
          icono={ShoppingCart}
          variante="slate"
        />

        <KpiCard
          titulo="Resultado Económico Neto"
          valor={formatoMoneda(data.resultadoEconomico)}
          subtexto={`Margen estimado: ${data.margenOperativoPct}%`}
          icono={Wallet}
          variante={esGanancia ? 'emerald' : 'rose'}
          tendencia={{
            valor: esGanancia ? 'Balance positivo' : 'Déficit operativo',
            esPositiva: esGanancia,
          }}
        />

        <KpiCard
          titulo="Insumos en Alerta Crítica"
          valor={data.insumosCriticosCount}
          subtexto="Stock menor o igual al mínimo"
          icono={AlertTriangle}
          variante={data.insumosCriticosCount > 0 ? 'rose' : 'emerald'}
          tendencia={{
            valor: data.insumosCriticosCount > 0 ? 'Reponer urgente' : 'Abastecimiento óptimo',
            esPositiva: data.insumosCriticosCount === 0,
          }}
        />
      </div>

      {/* 2. GRÁFICOS INTERACTIVOS (DONUT Y COLUMNAS) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* GRÁFICO CIRCULAR: Distribución de Flujo Financiero */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
                <PieIcon className="h-4 w-4" />
              </span>
              <div>
                <h3 className="text-base font-bold text-slate-900">Composición de Flujo Económico</h3>
                <p className="text-xs text-slate-500">Distribución de ingresos vs. egresos del periodo</p>
              </div>
            </div>
            <Link
              to="/dashboard/reportes"
              className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 hover:text-amber-800 transition-colors"
            >
              CU25
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="pt-2">
            <DonutChart
              segmentos={segmentosDonut}
              tituloCentro="Balance"
              subtituloCentro={formatoMoneda(data.resultadoEconomico)}
            />
          </div>
        </div>

        {/* GRÁFICO DE COLUMNAS: Top Productos más Vendidos */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-50 text-amber-700">
                <BarChart2 className="h-4 w-4" />
              </span>
              <div>
                <h3 className="text-base font-bold text-slate-900">Demanda por Producto (Unidades)</h3>
                <p className="text-xs text-slate-500">Los 5 panes y productos con mayor rotación</p>
              </div>
            </div>
            <Link
              to="/dashboard/comercializacion"
              className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 hover:text-amber-800 transition-colors"
            >
              Ventas
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {itemsColumnas.length === 0 ? (
            <p className="text-xs text-slate-400 py-12 text-center">No hay productos vendidos en el periodo seleccionado.</p>
          ) : (
            <div className="pt-2">
              <ColumnBarChart items={itemsColumnas} prefijoValor="" />
            </div>
          )}
        </div>
      </div>

      {/* 3. NUEVA FILA DE INDICADORES OPERATIVOS TÁCTICOS */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Indicadores Operativos y de Mostrador</h4>
            <p className="text-xs text-slate-500">Métricas tácticas de flujo diario, caja y rotación</p>
          </div>
          <span className="rounded-md bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-800 border border-amber-200/60">
            En tiempo real
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Ticket Promedio */}
          <div className="group rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md hover:border-amber-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Ticket Promedio</span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-amber-800">
                <Receipt className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-2 text-xl font-bold text-slate-900">{formatoMoneda(data.ticketPromedio)}</p>
            <p className="mt-1 text-[11px] text-slate-400">Gasto promedio por transacción</p>
          </div>

          {/* Adopción Pago Digital vs Efectivo */}
          <div className="group rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md hover:border-indigo-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Pagos Digitales (QR/Tarjeta)</span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-100 text-indigo-800">
                <CreditCard className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <p className="text-xl font-bold text-slate-900">{data.digitalPct}%</p>
              <span className="text-xs font-semibold text-slate-500">del total</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Efectivo: {formatoMoneda(data.totalEfectivo)}
            </p>
          </div>

          {/* Pedidos Activos */}
          <div className="group rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md hover:border-emerald-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Pedidos por Entregar</span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-800">
                <ClipboardList className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-2 text-xl font-bold text-slate-900">{data.pedidosPendientes}</p>
            <Link
              to="/dashboard/comercializacion/pedidos/estado"
              className="mt-1 inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 hover:text-emerald-800"
            >
              Consultar estado (CU15) →
            </Link>
          </div>

          {/* Capital en Mostrador */}
          <div className="group rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md hover:border-slate-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Stock Valorizado (Mostrador)</span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-800">
                <PackageCheck className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-2 text-xl font-bold text-slate-900">{formatoMoneda(data.valorInventarioMostrador)}</p>
            <Link
              to="/dashboard/productos"
              className="mt-1 inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 hover:text-amber-800"
            >
              Existencias de pan (CU12) →
            </Link>
          </div>
        </div>
      </div>

      {/* 4. CENTRO DE ACCESO RÁPIDO A REPORTES DEL CICLO 4 */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs">
        <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900">Centro de Reportes Oficiales</h3>
            <p className="text-xs text-slate-500">
              Exportación y auditoría detallada en PDF y CSV para la administración
            </p>
          </div>
          <Link
            to="/dashboard/reportes"
            className="inline-flex items-center gap-1 text-xs font-bold text-amber-700 hover:text-amber-800 transition-colors"
          >
            Abrir módulo de Reportes completo
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {reportesAtajos.map((rep) => {
            const Icono = rep.icono;
            return (
              <Link
                key={rep.cu}
                to="/dashboard/reportes"
                className={`group flex flex-col justify-between rounded-xl border border-slate-200/80 p-3.5 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-sm ${rep.color}`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded-md bg-white/80 px-1.5 py-0.5 text-[10px] font-black text-slate-800 shadow-2xs">
                      {rep.cu}
                    </span>
                    <Icono className="h-4 w-4" />
                  </div>
                  <h4 className="mt-2.5 text-xs font-bold text-slate-900 group-hover:text-amber-900 transition-colors">
                    {rep.titulo}
                  </h4>
                  <p className="mt-1 text-[11px] text-slate-500 leading-snug">
                    {rep.desc}
                  </p>
                </div>

                <span className="mt-3 text-[10px] font-bold text-amber-800 opacity-80 group-hover:opacity-100 transition-opacity">
                  Generar reporte →
                </span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* 5. SÍNTESIS DE TOMA DE DECISIONES */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs">
        <div className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-slate-500" />
          <span className="text-xs font-bold text-slate-800">Síntesis para decisiones de negocio:</span>
        </div>
        <p className="mt-1 text-xs text-slate-600">
          {esGanancia
            ? `El negocio sostiene un superávit de ${formatoMoneda(data.resultadoEconomico)}. El costo total de abastecimiento y gastos operativos representa el ${
                data.ingresosTotales > 0 ? ((totalEgresos / data.ingresosTotales) * 100).toFixed(1) : 0
              }% de los ingresos del periodo.`
            : `Atención: Los egresos superan los ingresos en ${formatoMoneda(Math.abs(data.resultadoEconomico))}. Se aconseja evaluar compras extraordinarias de insumos o costos fijos.`}
        </p>
      </div>

      {/* 6. ALERTAS DE MATERIA PRIMA (Drilldown operativo) */}
      {data.insumosCriticosCount > 0 && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-100 text-rose-700">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-rose-950">Insumos bajo stock mínimo de seguridad</h4>
                <p className="text-xs text-rose-800">
                  {data.insumosCriticosCount} insumos requieren reposición inmediata para no interrumpir horneadas diarias.
                </p>
              </div>
            </div>
            <Link
              to="/dashboard/compras"
              className="hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-rose-700 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:bg-rose-800 transition-colors"
            >
              Registrar Compra (CU07)
            </Link>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.insumosCriticos.map((insumo: { id: number; nombre: string; stock: number; stockMinimo: number; unidad: string }) => (
              <div
                key={insumo.id}
                className="flex items-center justify-between rounded-xl border border-rose-200/80 bg-white p-3 text-xs"
              >
                <div>
                  <span className="font-bold text-slate-900">{insumo.nombre}</span>
                  <p className="text-[11px] text-slate-500">Mínimo: {insumo.stockMinimo} {insumo.unidad}</p>
                </div>
                <div className="text-right">
                  <span className="font-extrabold text-rose-700">
                    {insumo.stock} {insumo.unidad}
                  </span>
                  <span className="block text-[10px] uppercase font-semibold text-rose-600">Crítico</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default OwnerDashboardView;
