import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, PackageX, RefreshCw, Search, ShoppingCart } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { useAlertasBajoStock } from './useAlertasBajoStock';
import { filtrarAlertas, resumirAlertas } from './resumenAlertas';

export default function AlertasBajoStockPage() {
  const { hasPermission } = useAuth();
  // CU07 tiene su propio permiso; consultar CU09 no habilita compras.
  const puedeComprar = hasPermission('registrar_compras');
  const { alertas, cargando, error, actualizar } = useAlertasBajoStock();
  const [busqueda, setBusqueda] = useState('');
  const resumen = resumirAlertas(alertas);
  const visibles = filtrarAlertas(alertas, busqueda);
  const disponible = !cargando && !error;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <Link to="/dashboard/productos?tab=inventario" className="text-sm font-medium text-amber-800 underline">Volver a stock de materia prima</Link>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900">
            <AlertTriangle aria-hidden="true" className="h-6 w-6 text-amber-700" />Alertas de bajo stock
          </h1>
          <p className="mt-2 text-sm text-slate-600">Insumos activos cuyo stock está en el mínimo o por debajo de él. Los insumos sin inventario se consideran con stock cero.</p>
        </div>
        <button type="button" disabled={cargando} onClick={actualizar}
          className="flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-700 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-800 disabled:opacity-60 cursor-pointer">
          <RefreshCw aria-hidden="true" className="h-4 w-4" />Actualizar
        </button>
      </div>
      <div aria-label="Resumen de todas las alertas" className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="flex items-center gap-2 text-sm font-medium text-slate-600"><AlertTriangle aria-hidden="true" className="h-5 w-5 text-amber-700" />Materias primas en alerta</p>
          <p className="mt-2 text-3xl font-bold tabular-nums text-slate-900">{disponible ? resumen.total : '—'}</p>
          <p className="mt-1 text-xs text-slate-500">En el mínimo o por debajo de él.</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="flex items-center gap-2 text-sm font-medium text-slate-600"><PackageX aria-hidden="true" className="h-5 w-5 text-red-700" />Materias primas agotadas</p>
          <p className="mt-2 text-3xl font-bold tabular-nums text-slate-900">{disponible ? resumen.agotadas : '—'}</p>
          <p className="mt-1 text-xs text-slate-500">Stock cero entre los insumos en alerta.</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-sm font-medium text-slate-600">Mayor faltante por unidad</p>
          {disponible && resumen.maximosPorUnidad.length > 0 ? (
            <ul className="mt-2 space-y-2">
              {resumen.maximosPorUnidad.map((alerta) => (
                <li key={alerta.unidad_medida.trim()}>
                  <p className="text-lg font-bold tabular-nums text-slate-900">{alerta.faltante} {alerta.unidad_medida}</p>
                  <p className="text-xs text-slate-600">{alerta.nombre}</p>
                </li>
              ))}
            </ul>
          ) : <p className="mt-2 text-xl font-bold text-slate-900">{disponible ? 'Sin faltantes' : '—'}</p>}
          <p className="mt-2 text-xs text-slate-500">Se comparan insumos con la misma unidad.</p>
        </div>
      </div>
      <section aria-label="Listado de alertas" aria-busy={cargando} className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
        <label className="mb-4 block text-sm font-medium text-slate-700">
          Buscar materia prima
          <span className="relative mt-2 block">
            <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <input type="search" value={busqueda} onChange={(event) => setBusqueda(event.target.value)} placeholder="Nombre del insumo"
              className="min-h-11 w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500" />
          </span>
        </label>
        <p className="mb-4 text-xs text-slate-500">La búsqueda filtra la tabla. Los indicadores consideran todas las alertas.</p>
        {cargando ? <p role="status" className="text-slate-600">Consultando existencias…</p>
          : error ? <p role="alert" className="text-red-700">{error}</p>
          : alertas.length === 0 ? <p role="status" className="text-emerald-800">No hay materias primas activas en el mínimo o por debajo de él.</p>
          : visibles.length === 0 ? <div role="status" className="text-slate-600">
            <p>No hay alertas que coincidan con tu búsqueda.</p>
            <button type="button" onClick={() => setBusqueda('')} className="mt-2 min-h-11 font-semibold text-amber-800 underline cursor-pointer">Limpiar búsqueda</button>
          </div>
          : <>
            <p role="status" className="mb-4 text-sm font-semibold text-amber-900">Mostrando {visibles.length} de {resumen.total} insumos en alerta.</p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Stock actual, mínimo y cantidad faltante por materia prima</caption>
                <thead className="border-b border-slate-200 text-slate-700"><tr>
                  {['Materia prima', 'Unidad', 'Stock actual', 'Stock mínimo', 'Faltante'].map((label) => <th key={label} scope="col" className="px-3 py-3">{label}</th>)}
                  {puedeComprar && <th scope="col" className="px-3 py-3">Acciones</th>}
                </tr></thead>
                <tbody>{visibles.map((alerta) => <tr key={alerta.id_materia_prima} className="border-b border-slate-100 last:border-0">
                  <th scope="row" className="px-3 py-4 font-medium text-slate-900">{alerta.nombre}</th>
                  <td className="px-3 py-4 text-slate-700">{alerta.unidad_medida}</td>
                  <td className="px-3 py-4 tabular-nums">{alerta.stock_actual}</td>
                  <td className="px-3 py-4 tabular-nums">{alerta.stock_minimo}</td>
                  <td className="px-3 py-4 font-semibold tabular-nums text-amber-900">{alerta.faltante}</td>
                  {puedeComprar && <td className="px-3 py-4">
                    <Link to={`/dashboard/compras?${new URLSearchParams({ tab: 'compras', reposicion_materia_prima: String(alerta.id_materia_prima), reposicion_cantidad: alerta.faltante })}`}
                      aria-label={`Comprar ${alerta.nombre}`}
                      className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 font-semibold text-amber-900 hover:bg-amber-100">
                      <ShoppingCart aria-hidden="true" className="h-4 w-4" />Comprar
                    </Link>
                  </td>}
                </tr>)}</tbody>
              </table>
            </div>
          </>}
      </section>
    </div>
  );
}
