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

  return (
    <div className="space-y-6 transition-opacity duration-300 ease-out">
      {/* 1. SECCIÓN DE HEADLINE KPIS */}
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

      {/* 3. SÍNTESIS DE TOMA DE DECISIONES */}
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

      {/* 4. ALERTAS DE MATERIA PRIMA (Drilldown operativo) */}
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
