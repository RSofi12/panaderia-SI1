import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Filter,
  History,
  Loader2,
  RefreshCw,
  Search,
} from 'lucide-react';
import type { HistorialPrecioFiltros } from '../../../../types/historialPrecio';
import { formatearBs } from '../precios';
import { useHistorialPrecios } from './useHistorialPrecios';

const formatoFecha = new Intl.DateTimeFormat('es-BO', {
  timeZone: 'America/La_Paz',
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

const claseCampo = 'min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm font-normal text-slate-900 focus:border-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-200 disabled:bg-slate-100 disabled:text-slate-500';
const claseBotonSecundario = 'inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer';

export default function HistorialPreciosPage() {
  const [idProducto, setIdProducto] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [errorFechas, setErrorFechas] = useState<string | null>(null);
  const [consulta, setConsulta] = useState<{ filtros: HistorialPrecioFiltros; pagina: number }>({
    filtros: {},
    pagina: 1,
  });
  const {
    datos, error, cargando, productos, errorCatalogo, cargandoCatalogo, reintentar, reintentarCatalogo,
  } = useHistorialPrecios(consulta.filtros, consulta.pagina);
  const tieneFiltros = Object.keys(consulta.filtros).length > 0;

  function aplicarFiltros(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (fechaDesde && fechaHasta && fechaDesde > fechaHasta) {
      setErrorFechas('La fecha desde no puede ser posterior a la fecha hasta.');
      return;
    }
    setErrorFechas(null);
    setConsulta({
      filtros: {
        ...(idProducto && { id_producto: Number(idProducto) }),
        ...(fechaDesde && { fecha_desde: fechaDesde }),
        ...(fechaHasta && { fecha_hasta: fechaHasta }),
      },
      pagina: 1,
    });
  }

  function limpiarFiltros() {
    setIdProducto('');
    setFechaDesde('');
    setFechaHasta('');
    setErrorFechas(null);
    setConsulta({ filtros: {}, pagina: 1 });
  }

  function cambiarPagina(pagina: number) {
    setConsulta((actual) => ({ ...actual, pagina }));
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <Link to="/dashboard/productos" className="inline-flex min-h-11 items-center gap-2 rounded-lg text-sm font-semibold text-amber-800 hover:text-amber-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2">
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          Volver a Productos
        </Link>
        <p className="mt-3 text-xs font-semibold uppercase tracking-wider text-amber-800">Productos e Inventario · CU19</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Historial de precios</h1>
        <p className="mt-1 text-sm text-slate-600">Consulta los precios de venta registrados de tus productos, incluidos los que están inactivos.</p>
      </div>

      <section aria-labelledby="titulo-filtros-precios" className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
        <div className="mb-4 flex items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800">
            <Filter aria-hidden="true" className="h-5 w-5" />
          </span>
          <div>
            <h2 id="titulo-filtros-precios" className="text-sm font-semibold text-slate-900">Filtrar historial</h2>
            <p className="mt-0.5 text-xs text-slate-600">Cambios registrados dentro del intervalo, incluyendo ambas fechas.</p>
          </div>
        </div>
        <form onSubmit={aplicarFiltros} className="grid grid-cols-1 items-end gap-4 sm:grid-cols-2 lg:grid-cols-6">
          <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700 lg:col-span-2">
            Producto
            <select
              value={idProducto}
              onChange={(event) => setIdProducto(event.target.value)}
              disabled={cargandoCatalogo || Boolean(errorCatalogo)}
              aria-describedby={errorCatalogo ? 'error-catalogo-precios' : undefined}
              className={claseCampo}
            >
              <option value="">{cargandoCatalogo ? 'Cargando productos…' : 'Todos los productos'}</option>
              {productos.map((producto) => (
                <option key={producto.id_producto} value={producto.id_producto}>
                  {producto.nombre}{producto.activo ? '' : ' (inactivo)'}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
            Fecha desde
            <input type="date" value={fechaDesde} max={fechaHasta || undefined} onChange={(event) => { setFechaDesde(event.target.value); setErrorFechas(null); }} aria-describedby={errorFechas ? 'error-fechas-precios' : undefined} aria-invalid={Boolean(errorFechas)} className={claseCampo} />
          </label>
          <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
            Fecha hasta
            <input type="date" value={fechaHasta} min={fechaDesde || undefined} onChange={(event) => { setFechaHasta(event.target.value); setErrorFechas(null); }} aria-describedby={errorFechas ? 'error-fechas-precios' : undefined} aria-invalid={Boolean(errorFechas)} className={claseCampo} />
          </label>
          <button type="submit" className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-800 px-4 text-sm font-semibold text-white transition-colors hover:bg-amber-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 cursor-pointer">
            <Search aria-hidden="true" className="h-4 w-4" />
            Aplicar filtros
          </button>
          <button type="button" onClick={limpiarFiltros} className={claseBotonSecundario}>Limpiar</button>
        </form>
        {errorFechas && <p id="error-fechas-precios" role="alert" className="mt-3 text-sm text-red-800">{errorFechas}</p>}
        {errorCatalogo && (
          <div id="error-catalogo-precios" role="alert" className="mt-4 flex flex-col items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950 sm:flex-row sm:items-center sm:justify-between">
            <p>{errorCatalogo}</p>
            <button type="button" onClick={reintentarCatalogo} className={`${claseBotonSecundario} shrink-0`}>Reintentar productos</button>
          </div>
        )}
      </section>

      <section aria-labelledby="titulo-resultados-precios" aria-busy={cargando} className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 id="titulo-resultados-precios" className="text-base font-semibold text-slate-900">Precios registrados</h2>
            <p className="mt-0.5 text-xs text-slate-600">Más recientes primero · Hora de Bolivia</p>
          </div>
          <button type="button" onClick={reintentar} disabled={cargando} className={claseBotonSecundario}>
            <RefreshCw aria-hidden="true" className="h-4 w-4" />
            Actualizar
          </button>
        </div>

        {error ? (
          <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-900">
            <div className="flex items-start gap-3">
              <AlertCircle aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0" />
              <p>{error}</p>
            </div>
            <button type="button" onClick={reintentar} className={`${claseBotonSecundario} mt-4`}>Volver a intentar</button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-sm">
                <caption className="sr-only">Historial de precios de venta de productos, con fecha de inicio en hora de Bolivia.</caption>
                <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-600">
                  <tr>
                    <th scope="col" className="px-4 py-3 sm:px-5">Producto</th>
                    <th scope="col" className="px-4 py-3 text-right sm:px-5">Precio de venta</th>
                    <th scope="col" className="px-4 py-3 sm:px-5">Fecha de inicio</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {cargando ? (
                    <tr><td colSpan={3} className="px-4 py-14 text-center text-slate-600">
                      <div role="status">
                        <Loader2 aria-hidden="true" className="mx-auto mb-3 h-6 w-6 animate-spin text-amber-800 motion-reduce:animate-none" />
                        Consultando historial de precios…
                      </div>
                    </td></tr>
                  ) : datos?.results.length ? datos.results.map((registro) => (
                    <tr key={registro.id_historial} className="transition-colors hover:bg-amber-50/50">
                      <td className="px-4 py-4 sm:px-5">
                        <p className="font-semibold text-slate-900">{registro.producto_nombre}</p>
                        {!registro.producto_activo && <span className="mt-1 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">Inactivo</span>}
                      </td>
                      <td className="whitespace-nowrap px-4 py-4 text-right font-semibold tabular-nums text-amber-900 sm:px-5">{formatearBs(registro.precio)}</td>
                      <td className="px-4 py-4 text-slate-700 sm:px-5"><time dateTime={registro.fecha_inicio}>{formatoFecha.format(new Date(registro.fecha_inicio))}</time></td>
                    </tr>
                  )) : (
                    <tr><td colSpan={3} className="px-4 py-14 text-center">
                      <History aria-hidden="true" className="mx-auto mb-3 h-8 w-8 text-amber-700" />
                      <p className="font-semibold text-slate-900">{tieneFiltros ? 'No hay registros con esos filtros' : 'Aún no hay precios registrados'}</p>
                      <p className="mt-1 text-sm text-slate-600">{tieneFiltros ? 'Prueba con otro producto o limpia los filtros.' : 'Los precios registrados de los productos aparecerán aquí.'}</p>
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="flex flex-col gap-3 border-t border-slate-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">
              <p role="status" className="text-sm text-slate-600">{cargando ? 'Cargando resultados…' : `${datos?.count ?? 0} registros · Página ${consulta.pagina}`}</p>
              <nav aria-label="Paginación del historial de precios" className="flex flex-wrap gap-2">
                <button type="button" onClick={() => cambiarPagina(consulta.pagina - 1)} disabled={cargando || !datos?.previous} className={claseBotonSecundario}>
                  <ChevronLeft aria-hidden="true" className="h-4 w-4" />Anterior
                </button>
                <button type="button" onClick={() => cambiarPagina(consulta.pagina + 1)} disabled={cargando || !datos?.next} className={claseBotonSecundario}>
                  Siguiente<ChevronRight aria-hidden="true" className="h-4 w-4" />
                </button>
              </nav>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
