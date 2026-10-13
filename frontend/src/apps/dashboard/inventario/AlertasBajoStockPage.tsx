import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { materiaPrimaService } from '../../../services/materiaPrimaService';
import type { AlertaBajoStock } from '../../../types/materiaPrima';

interface Resultado {
  version: number;
  alertas: AlertaBajoStock[];
  error: string | null;
}

export default function AlertasBajoStockPage() {
  const [version, setVersion] = useState(0);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const cargando = resultado?.version !== version;

  useEffect(() => {
    const controller = new AbortController();
    materiaPrimaService.listarAlertas(controller.signal)
      .then((alertas) => {
        if (!controller.signal.aborted) setResultado({ version, alertas, error: null });
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setResultado({ version, alertas: [], error: 'No se pudieron consultar las alertas. Comprueba tu conexión y vuelve a intentar.' });
        }
      });
    return () => controller.abort();
  }, [version]);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <Link to="/dashboard/productos" className="text-sm font-medium text-amber-800 underline">Volver a productos e inventario</Link>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900">
            <AlertTriangle aria-hidden="true" className="h-6 w-6 text-amber-700" />Alertas de bajo stock
          </h1>
          <p className="mt-2 text-sm text-slate-600">Insumos activos cuyo stock está por debajo del mínimo. Los insumos sin inventario se consideran con stock cero.</p>
        </div>
        <button type="button" disabled={cargando} onClick={() => setVersion((v) => v + 1)}
          className="flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-700 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-800 disabled:opacity-60">
          <RefreshCw aria-hidden="true" className="h-4 w-4" />Actualizar
        </button>
      </div>
      <section aria-label="Listado de alertas" aria-busy={cargando} className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
        {cargando ? <p role="status" className="text-slate-600">Consultando existencias…</p>
          : resultado?.error ? <p role="alert" className="text-red-700">{resultado.error}</p>
          : resultado?.alertas.length === 0 ? <p role="status" className="text-emerald-800">No hay materias primas activas con bajo stock.</p>
          : <>
            <p role="status" className="mb-4 text-sm font-semibold text-amber-900">{resultado?.alertas.length} insumos requieren reposición.</p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Stock actual, mínimo y cantidad faltante por materia prima</caption>
                <thead className="border-b border-slate-200 text-slate-700"><tr>
                  {['Materia prima', 'Unidad', 'Stock actual', 'Stock mínimo', 'Faltante'].map((label) => <th key={label} scope="col" className="px-3 py-3">{label}</th>)}
                </tr></thead>
                <tbody>{resultado?.alertas.map((alerta) => <tr key={alerta.id_materia_prima} className="border-b border-slate-100 last:border-0">
                  <th scope="row" className="px-3 py-4 font-medium text-slate-900">{alerta.nombre}</th>
                  <td className="px-3 py-4 text-slate-700">{alerta.unidad_medida}</td>
                  <td className="px-3 py-4 tabular-nums">{alerta.stock_actual}</td>
                  <td className="px-3 py-4 tabular-nums">{alerta.stock_minimo}</td>
                  <td className="px-3 py-4 font-semibold tabular-nums text-amber-900">{alerta.faltante}</td>
                </tr>)}</tbody>
              </table>
            </div>
          </>}
      </section>
    </div>
  );
}
