import React, { useEffect, useState } from 'react';
import {
  CalendarDays,
  ClipboardList,
  Eye,
  Loader2,
  RefreshCw,
  Search,
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
          <p className="text-xs font-bold uppercase text-amber-800">Consulta · CU11</p>
          <h1 className="mt-1 flex items-center gap-2 text-2xl font-bold text-slate-900">
            <ClipboardList className="h-6 w-6 text-amber-700" />
            Historial de producción
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">
            Consulta jornadas registradas, revisa sus responsables y abre el detalle de cada lote.
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-600" aria-live="polite">
          <CalendarDays className="h-4 w-4 text-amber-700" />
          <span>{historial.length} jornadas · {totalUnidades.toLocaleString('es-BO')} unidades</span>
        </div>
      </header>

      <form
        onSubmit={aplicarFiltros}
        className="grid grid-cols-1 items-end gap-3 border-b border-slate-200 pb-5 sm:grid-cols-2 lg:grid-cols-6"
      >
        <label className="flex flex-col gap-1 text-xs font-semibold text-slate-700">
          Desde
          <input
            type="date"
            value={fechaDesde}
            onChange={(event) => setFechaDesde(event.target.value)}
            className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-normal"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs font-semibold text-slate-700">
          Hasta
          <input
            type="date"
            value={fechaHasta}
            onChange={(event) => setFechaHasta(event.target.value)}
            className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-normal"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs font-semibold text-slate-700">
          Jornada
          <select
            value={jornada}
            onChange={(event) => setJornada(event.target.value as JornadaProduccion | '')}
            className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-normal"
          >
            <option value="">Todas</option>
            <option value="manana">Mañana</option>
            <option value="tarde">Tarde</option>
            <option value="noche">Noche</option>
            <option value="unica">Única</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs font-semibold text-slate-700">
          Producto
          <select
            value={idProducto}
            onChange={(event) => setIdProducto(event.target.value)}
            className="min-h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-normal"
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
          className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md bg-amber-800 px-4 text-sm font-semibold text-white hover:bg-amber-900"
        >
          <Search className="h-4 w-4" />
          Filtrar
        </button>
        <button
          type="button"
          onClick={limpiarFiltros}
          className="min-h-10 rounded-md border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Limpiar
        </button>
      </form>

      <section aria-label="Resultados del historial" aria-live="polite">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-slate-800">Jornadas encontradas</h2>
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
          <div role="alert" className="border-l-4 border-rose-600 bg-rose-50 px-4 py-3 text-sm text-rose-900">
            {error}
          </div>
        ) : (
          <div className="overflow-x-auto border-y border-slate-200">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-600">
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
                    <td colSpan={6} className="px-4 py-12 text-center text-slate-600">
                      <p className="font-semibold">No hay jornadas para mostrar</p>
                      <p className="mt-1 text-sm text-slate-500">
                        {Object.keys(filtrosAplicados).length
                          ? 'Prueba cambiando o limpiando los filtros.'
                          : 'Cuando existan registros de producción en esta base, aparecerán aquí.'}
                      </p>
                    </td>
                  </tr>
                ) : (
                  historial.map((registro) => (
                    <tr key={registro.id_produccion} className="hover:bg-amber-50/40">
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
                          Ver
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