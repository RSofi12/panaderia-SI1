import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  CalendarDays,
  ClipboardList,
  Eye,
  Filter,
  Loader2,
  RefreshCw,
  Search,
  Wheat,
} from 'lucide-react';
import produccionService from '../../../../services/produccionService';
import productoService from '../../../../services/productoService';
import type { Producto } from '../../../../types/producto';
import type {
  JornadaProduccion,
  ProduccionFiltros,
  ProduccionRegistro,
} from '../../../../types/produccion';
import { JORNADAS_LABELS } from '../../../../types/produccion';
import ModalDetalleProduccion from './components/ModalDetalleProduccion';

const formatoFecha = (fecha: string) =>
  new Intl.DateTimeFormat('es-BO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(`${fecha}T00:00:00`));

export const HistorialProduccionPage: React.FC = () => {
  const [historial, setHistorial] = useState<ProduccionRegistro[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detalle, setDetalle] = useState<ProduccionRegistro | null>(null);
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [jornada, setJornada] = useState<JornadaProduccion | ''>('');
  const [idProducto, setIdProducto] = useState('');
  const [filtrosAplicados, setFiltrosAplicados] = useState<ProduccionFiltros>({});

  useEffect(() => {
    let vigente = true;
    productoService.listar({ activo: 'true' }).then((data) => {
      if (vigente) setProductos(data);
    }).catch(() => {
      if (vigente) setProductos([]);
    });
    return () => {
      vigente = false;
    };
  }, []);

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    setError(null);

    produccionService.listarHistorial(filtrosAplicados)
      .then((data) => {
        if (vigente) setHistorial(data);
      })
      .catch(() => {
        if (vigente) setError('No se pudo cargar el historial. Revisa la conexión con el servidor e inténtalo de nuevo.');
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });

    return () => {
      vigente = false;
    };
  }, [filtrosAplicados]);

  const aplicarFiltros = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFiltrosAplicados({
      ...(fechaDesde && { fecha_desde: fechaDesde }),
      ...(fechaHasta && { fecha_hasta: fechaHasta }),
      ...(jornada && { jornada }),
      ...(idProducto && { id_producto: Number(idProducto) }),
    });
  };

  const limpiarFiltros = () => {
    setFechaDesde('');
    setFechaHasta('');
    setJornada('');
    setIdProducto('');
    setFiltrosAplicados({});
  };

  const totalUnidades = historial.reduce((total, item) => total + item.total_unidades, 0);

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="flex flex-col gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold text-amber-800">CU11 · Consulta de producción</p>
          <h1 className="mt-1 flex items-center gap-2 text-2xl font-bold text-slate-900">
            <ClipboardList className="h-6 w-6 text-amber-700" />
            Historial de producción
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">
            Consulta jornadas registradas, revisa sus responsables y abre el detalle de cada lote.
          </p>
        </div>
        <dl className="flex items-center divide-x divide-slate-200 rounded-lg border border-slate-200 bg-white px-4 py-3" aria-live="polite">
          <div className="pr-5">
            <dt className="text-xs font-medium text-slate-500">Jornadas</dt>
            <dd className="mt-0.5 text-xl font-bold tabular-nums text-slate-900">{historial.length}</dd>
          </div>
          <div className="pl-5">
            <dt className="text-xs font-medium text-slate-500">Unidades producidas</dt>
            <dd className="mt-0.5 flex items-center gap-1.5 text-xl font-bold tabular-nums text-slate-900">
              <CalendarDays className="h-4 w-4 text-amber-700" />
              {totalUnidades.toLocaleString('es-BO')}
            </dd>
          </div>
        </dl>
      </header>

      <section className="rounded-lg border border-slate-200 border-l-4 border-l-amber-700 bg-white p-4 shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-100 text-amber-800">
            <Filter className="h-4 w-4" />
          </span>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Filtrar historial</h2>
            <p className="text-xs text-slate-500">Acota la consulta por fecha, jornada o producto.</p>
          </div>
        </div>
        <form onSubmit={aplicarFiltros} className="grid grid-cols-1 items-end gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
            Desde
            <input
              type="date"
              value={fechaDesde}
              max={fechaHasta || undefined}
              onChange={(event) => setFechaDesde(event.target.value)}
              className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-normal focus:border-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-100"
            />
          </label>
          <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
            Hasta
            <input
              type="date"
              value={fechaHasta}
              min={fechaDesde || undefined}
              onChange={(event) => setFechaHasta(event.target.value)}
              className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-normal focus:border-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-100"
            />
          </label>
          <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
            Jornada
            <select
              value={jornada}
              onChange={(event) => setJornada(event.target.value as JornadaProduccion | '')}
              className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-normal focus:border-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-100"
            >
              <option value="">Todas</option>
              <option value="manana">Mañana</option>
              <option value="tarde">Tarde</option>
              <option value="noche">Noche</option>
              <option value="unica">Única</option>
            </select>
          </label>
          <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
            Producto
            <select
              value={idProducto}
              onChange={(event) => setIdProducto(event.target.value)}
              className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-normal focus:border-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-100"
            >
              <option value="">Todos los productos</option>
              {productos.map((producto) => (
                <option key={producto.id_producto} value={producto.id_producto}>
                  {producto.nombre}
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md bg-amber-800 px-4 text-sm font-semibold text-white transition-colors hover:bg-amber-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
          >
            <Search className="h-4 w-4" />
            Aplicar filtros
          </button>
          <button
            type="button"
            onClick={limpiarFiltros}
            className="min-h-10 rounded-md border border-slate-300 px-4 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
          >
            Limpiar
          </button>
        </form>
      </section>

      <section aria-label="Resultados del historial" aria-live="polite">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Jornadas encontradas</h2>
            <p className="mt-0.5 text-xs text-slate-500">Más recientes primero</p>
          </div>
          <button
            type="button"
            onClick={() => setFiltrosAplicados({ ...filtrosAplicados })}
            disabled={cargando}
            className="inline-flex min-h-10 items-center gap-2 rounded-md px-3 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${cargando ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>

        {error ? (
          <div role="alert" className="flex items-start gap-3 border-l-4 border-rose-600 bg-rose-50 px-4 py-3 text-sm text-rose-900">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase text-slate-600">
                <tr>
                  <th className="px-4 py-3">Jornada</th>
                  <th className="px-4 py-3">Responsable</th>
                  <th className="px-4 py-3 text-right">Unidades</th>
                  <th className="px-4 py-3 text-right">Variedades</th>
                  <th className="px-4 py-3 text-right">Costo total</th>
                  <th className="px-4 py-3 text-right">Detalle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {cargando ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-slate-500">
                      <Loader2 className="mx-auto mb-2 h-5 w-5 animate-spin text-amber-700" />
                      Consultando historial…
                    </td>
                  </tr>
                ) : historial.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-14 text-center text-slate-600">
                      <span className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-amber-100 text-amber-800">
                        <Wheat className="h-5 w-5" />
                      </span>
                      <p className="font-semibold text-slate-900">No hay jornadas para mostrar</p>
                      <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
                        {Object.keys(filtrosAplicados).length
                          ? 'Prueba cambiando o limpiando los filtros.'
                          : 'Cuando existan registros de producción en esta base, aparecerán aquí.'}
                      </p>
                    </td>
                  </tr>
                ) : (
                  historial.map((registro) => (
                    <tr key={registro.id_produccion} className="transition-colors hover:bg-amber-50/50">
                      <td className="px-4 py-3">
                        <span className="block font-semibold text-slate-900">{formatoFecha(registro.fecha)}</span>
                        <span className="text-xs text-slate-500">
                          #{registro.id_produccion} · {JORNADAS_LABELS[registro.jornada] || registro.jornada}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-700">{registro.usuario_nombre}</td>
                      <td className="px-4 py-3 text-right font-semibold tabular-nums text-slate-900">
                        {registro.total_unidades.toLocaleString('es-BO')}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">{registro.total_variedades}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                        Bs {Number(registro.costo_total).toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => setDetalle(registro)}
                          aria-label={`Ver detalle de la jornada ${registro.id_produccion}`}
                          className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-700 hover:bg-white"
                        >
                          <Eye className="h-4 w-4" />
                          Ver detalle
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <ModalDetalleProduccion registro={detalle} onCerrar={() => setDetalle(null)} />
    </div>
  );
};

export default HistorialProduccionPage;