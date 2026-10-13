import React from 'react';
import {
  BarChart3,
  TrendingUp,
  PieChart,
  Wallet,
  FileSpreadsheet,
  Sparkles,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react';

interface CasoUsoReporte {
  cu: string;
  titulo: string;
  descripcion: string;
  icono: React.ElementType;
}

const REPORTES_CASOS: CasoUsoReporte[] = [
  {
    cu: 'CU21',
    titulo: 'Generar reporte de ventas',
    descripcion:
      'Reporte de las ventas realizadas en un periodo (diario, semanal o mensual), detallado por producto o por método de pago.',
    icono: TrendingUp,
  },
  {
    cu: 'CU22',
    titulo: 'Generar reporte de producción',
    descripcion:
      'Reporte de las cantidades producidas en un periodo, permitiendo comparar producción física vs ventas registradas.',
    icono: BarChart3,
  },
  {
    cu: 'CU23',
    titulo: 'Generar reporte de existencias',
    descripcion:
      'Reporte del estado y valorización de existencias de materias primas y productos terminados en mostrador.',
    icono: PieChart,
  },
  {
    cu: 'CU24',
    titulo: 'Generar reporte de compras y gastos',
    descripcion:
      'Reporte de las compras a proveedores y de los gastos operativos e inversiones realizados en un periodo.',
    icono: Wallet,
  },
  {
    cu: 'CU25',
    titulo: 'Generar reporte de resultados económicos',
    descripcion:
      'Reporte analítico que relaciona ingresos por ventas con egresos (compras, mermas y gastos), mostrando el margen neto.',
    icono: FileSpreadsheet,
  },
];

export const ReportesPage: React.FC = () => {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Encabezado General */}
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
          Reportes y Estadísticas · Ciclo 4 (CU21–CU25)
        </p>
        <div className="mt-1 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              <BarChart3 className="h-7 w-7 text-amber-700" />
              Reportes Gerenciales
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Métricas consolidadas del negocio, balance financiero y comparativas de rendimiento.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
            <Sparkles className="h-3.5 w-3.5 text-amber-600" />
            Módulo en Progreso · Ciclo 4
          </span>
        </div>
      </div>

      {/* Banner Informativo */}
      <section className="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50 via-orange-50/50 to-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-700 text-white shadow-md shadow-amber-700/20">
              <BarChart3 className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Módulo de Inteligencia de Negocio y Reportes
              </h3>
              <p className="mt-1 text-sm text-slate-600 leading-relaxed max-w-2xl">
                Diseñado exclusivamente para el <strong className="text-slate-800">Propietario</strong> (y Administrador),
                este módulo consolidará la información generada en Compras, Producción, Inventario y Ventas para
                ofrecer reportes dinámicos, exportación a PDF/Excel y análisis de rentabilidad.
              </p>
            </div>
          </div>
          <div className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-amber-300 bg-white px-4 py-2 text-xs font-semibold text-amber-900 shadow-sm">
            <ShieldCheck className="h-4 w-4 text-amber-700" />
            <span>Acceso: Propietario</span>
          </div>
        </div>
      </section>

      {/* Casos de Uso Planificados */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            Reportes Planificados (5 Casos de Uso)
          </h3>
          <span className="text-xs text-slate-500 font-medium">Ciclo 4 PUDS</span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {REPORTES_CASOS.map((item) => {
            const Icono = item.icono;
            return (
              <div
                key={item.cu}
                className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-xs transition-shadow hover:shadow-md hover:border-amber-200"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="inline-flex items-center rounded-md bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-900">
                      {item.cu}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500">
                      <AlertCircle className="h-3 w-3 text-amber-600" />
                      Planificado
                    </span>
                  </div>

                  <div className="flex items-center gap-2.5 mb-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-800">
                      <Icono className="h-4 w-4" />
                    </div>
                    <h4 className="text-sm font-bold text-slate-900">{item.titulo}</h4>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed mb-4">{item.descripcion}</p>
                </div>

                <div className="border-t border-slate-100 pt-3">
                  <p className="text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-600">Actor:</span> Propietario
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};

export default ReportesPage;
