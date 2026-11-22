import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, BarChart3, ShieldCheck, Sparkles } from 'lucide-react';
import ReporteComprasCu24 from './ReporteComprasCu24';

export const ReporteComprasPage: React.FC = () => {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Botón de retorno y migas de pan */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <Link
          to="/dashboard/reportes"
          className="inline-flex items-center gap-2 text-xs font-bold text-amber-800 hover:text-amber-900 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver al panel general de reportes
        </Link>

        <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-0.5 text-[11px] font-semibold text-amber-800">
          <Sparkles className="h-3 w-3 text-amber-600" />
          Ciclo 4 · CU24
        </span>
      </div>

      {/* Banner de Identificación del CU24 */}
      <section className="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50 via-orange-50/50 to-white p-5 shadow-xs">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-700 text-white shadow-md shadow-amber-700/20">
              <BarChart3 className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-900">
                  CU24
                </span>
                <h2 className="text-base font-bold text-slate-900">
                  Reporte de Compras y Gastos de Materia Prima
                </h2>
              </div>
              <p className="mt-0.5 text-xs text-slate-600 max-w-2xl leading-relaxed">
                Supervisión financiera y operativa de compras a proveedores, cálculo dinámico de volúmenes de insumos y generación de cierres estáticos inmutables para el Propietario.
              </p>
            </div>
          </div>

          <div className="inline-flex shrink-0 items-center gap-1.5 rounded-xl border border-amber-300 bg-white px-3 py-1.5 text-xs font-semibold text-amber-900 shadow-xs">
            <ShieldCheck className="h-4 w-4 text-amber-700" />
            <span>Acceso: Propietario</span>
          </div>
        </div>
      </section>

      {/* Contenido interactivo del CU24 */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <ReporteComprasCu24 />
      </div>
    </div>
  );
};

export default ReporteComprasPage;
