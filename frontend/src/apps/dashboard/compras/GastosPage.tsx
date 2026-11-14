import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  Ban,
  Filter,
  Loader2,
  Plus,
  Receipt,
  RefreshCw,
  RotateCcw,
  Search,
  X,
} from 'lucide-react';
import { normalizarErrorApi } from '../../../services/erroresApi';
import gastosService from '../../../services/gastosService';
import { CATEGORIAS_MOVIMIENTO, TIPOS_MOVIMIENTO } from '../../../types/gasto';
import type { CategoriaMovimiento, MovimientoEconomico, TipoMovimiento } from '../../../types/gasto';
import { formatearBs } from '../productos/precios';
import { Paginacion } from '../components/Paginacion';
import { paginar, usePagina } from '../components/paginar';
import { RegistrarGastoModal } from './components/RegistrarGastoModal';
import { AnularGastoModal } from './components/AnularGastoModal';

// "13 nov 2026, 10:30". El navegador toma `es-BO` del ICU; si no lo tiene,
// cae al locale por defecto sin romper la tabla.
const formatoFecha = new Intl.DateTimeFormat('es-BO', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

const formatearFecha = (iso: string) => formatoFecha.format(new Date(iso));

const plural = (cantidad: number, singular: string, plural_: string) =>
  `${cantidad} ${cantidad === 1 ? singular : plural_}`;

type ModalAbierto = { tipo: 'registrar' } | { tipo: 'anular'; movimiento: MovimientoEconomico } | null;

interface Aviso {
  tono: 'exito' | 'error';
  texto: string;
}

// Mismo lenguaje visual que la barra de filtros de ComprasPage.
const estiloFiltro =
  'w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500';
const estiloEtiqueta = 'mb-1 block text-[11px] font-semibold text-slate-600';

export const GastosPage: React.FC = () => {
  const [busqueda, setBusqueda] = useState('');
  const [busquedaDiferida, setBusquedaDiferida] = useState('');
  const [tipo, setTipo] = useState<TipoMovimiento | ''>('');
  const [categoria, setCategoria] = useState<CategoriaMovimiento | ''>('');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [incluirAnulados, setIncluirAnulados] = useState(false);

  const [movimientos, setMovimientos] = useState<MovimientoEconomico[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recarga, setRecarga] = useState(0);

  const [modal, setModal] = useState<ModalAbierto>(null);
  const [aviso, setAviso] = useState<Aviso | null>(null);
  const [anulando, setAnulando] = useState(false);

  // El buscador espera 250 ms: teclear no debe disparar una petición por letra.
  useEffect(() => {
    const temporizador = window.setTimeout(() => setBusquedaDiferida(busqueda), 250);
    return () => window.clearTimeout(temporizador);
  }, [busqueda]);

  useEffect(() => {
    let cancelado = false;
    setCargando(true);
    gastosService
      .listar({
        search: busquedaDiferida,
        tipo,
        categoria,
        fecha_desde: desde,
        fecha_hasta: hasta,
        anulado: incluirAnulados ? 'todos' : undefined,
      })
      .then((lista) => {
        if (cancelado) return;
        setMovimientos(lista);
        setError(null);
      })
      .catch((fallo: unknown) => {
        if (cancelado) return;
        setMovimientos([]);
        setError(normalizarErrorApi(fallo).mensaje ?? 'No se pudieron cargar los gastos.');
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });
    return () => {
      cancelado = true;
    };
  }, [busquedaDiferida, tipo, categoria, desde, hasta, incluirAnulados, recarga]);

  // Un aviso de éxito se retira solo; uno de error se queda hasta que el
  // usuario lo cierre, porque puede necesitar leerlo con calma.
  useEffect(() => {
    if (!aviso || aviso.tono !== 'exito') return;
    const temporizador = window.setTimeout(() => setAviso(null), 5000);
    return () => window.clearTimeout(temporizador);
  }, [aviso]);

  const recargar = useCallback(() => setRecarga((valor) => valor + 1), []);
  // Identidad estable: los modales la usan como dependencia de sus efectos
  // (bloqueo de scroll, Escape) y no deben re-suscribirse en cada render.
  const cerrarModal = useCallback(() => setModal(null), []);

  // Los totales se calculan solo para mostrar. La autoridad del dinero es el
  // backend: acá se suman strings convertidos a número y nunca se persisten.
  const vigentes = useMemo(() => movimientos.filter((movimiento) => !movimiento.anulado), [movimientos]);
  const totalGastos = vigentes
    .filter((movimiento) => movimiento.tipo === 'gasto')
    .reduce((total, movimiento) => total + Number(movimiento.monto), 0);
  const totalInversiones = vigentes
    .filter((movimiento) => movimiento.tipo === 'inversion')
    .reduce((total, movimiento) => total + Number(movimiento.monto), 0);
  const total = totalGastos + totalInversiones;
  const porcentajeGastos = total > 0 ? (totalGastos / total) * 100 : 0;
  const cantidadAnulados = movimientos.length - vigentes.length;

  const hayFiltros =
    busqueda.trim() !== '' ||
    tipo !== '' ||
    categoria !== '' ||
    desde !== '' ||
    hasta !== '' ||
    incluirAnulados;

  // La página vuelve a 1 cuando cambian los filtros, no cuando se refresca el
  // listado: recargar no debe sacar al usuario de la página donde estaba.
  const clavePagina = `${busquedaDiferida}|${tipo}|${categoria}|${desde}|${hasta}|${incluirAnulados}|${movimientos.length}`;
  const [pagina, setPagina] = usePagina(clavePagina);
  const visibles = paginar(movimientos, pagina);

  function limpiarFiltros() {
    setBusqueda('');
    setBusquedaDiferida('');
    setTipo('');
    setCategoria('');
    setDesde('');
    setHasta('');
    setIncluirAnulados(false);
  }

  async function confirmarAnulacion(motivo?: string) {
    if (modal?.tipo !== 'anular') return;
    const { movimiento } = modal;
    setAnulando(true);
    try {
      await gastosService.anular(movimiento.id_movimiento, motivo);
      setAviso({ tono: 'exito', texto: `Movimiento anulado: ${movimiento.concepto}.` });
      setModal(null);
      recargar();
    } catch (fallo) {
      setAviso({
        tono: 'error',
        texto: normalizarErrorApi(fallo).mensaje ?? 'No se pudo anular el movimiento.',
      });
      setModal(null);
    } finally {
      setAnulando(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="mostrador-aparecer flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
            Compras y Proveedores · CU20
          </p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">
            Gastos e inversiones
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Los egresos que no son materia prima. Cada registro queda en la bitácora con su responsable.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setModal({ tipo: 'registrar' })}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-amber-600/20 hover:from-amber-700 hover:to-amber-800 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Registrar gasto
        </button>
      </header>

      {aviso && (
        <div
          role={aviso.tono === 'error' ? 'alert' : 'status'}
          className={`flex items-start justify-between gap-3 rounded-xl border px-4 py-3 text-sm ${
            aviso.tono === 'exito'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : 'border-red-200 bg-red-50 text-red-800'
          }`}
        >
          <span>{aviso.texto}</span>
          {aviso.tono === 'error' && (
            <button
              type="button"
              onClick={() => setAviso(null)}
              aria-label="Cerrar el aviso"
              className="rounded p-0.5 text-red-500 transition-colors hover:bg-red-100 hover:text-red-700"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      )}

      {/* Cinta de caja: el único bloque que grita. Separa gasto de inversión
          porque esa división es la que alimenta los reportes de CU24 y CU25. */}
      <section
        aria-label="Resumen de egresos del período"
        aria-busy={cargando}
        className={`overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs transition-opacity ${
          cargando ? 'opacity-70' : ''
        }`}
      >
        <div className="flex flex-col gap-5 p-4.5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Egresos del período
            </p>
            <p className="mt-1 text-3xl font-bold tabular-nums tracking-tight text-slate-900">
              {formatearBs(total)}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {plural(vigentes.length, 'movimiento vigente', 'movimientos vigentes')}
              {cantidadAnulados > 0 && ` · ${plural(cantidadAnulados, 'anulado', 'anulados')} sin contar`}
            </p>
          </div>

          <div className="w-full sm:max-w-md">
            <div
              role="img"
              aria-label={`Proporción del período: gastos ${formatearBs(totalGastos)}, inversiones ${formatearBs(totalInversiones)}`}
              className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100"
            >
              {total > 0 && (
                <>
                  <div
                    className="bg-rose-400 transition-[width] duration-500"
                    style={{ width: `${porcentajeGastos}%` }}
                  />
                  <div
                    className="bg-indigo-400 transition-[width] duration-500"
                    style={{ width: `${100 - porcentajeGastos}%` }}
                  />
                </>
              )}
            </div>
            <dl className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-xs">
              <div className="flex items-center gap-2">
                <span aria-hidden="true" className="h-2 w-2 rounded-full bg-rose-400" />
                <dt className="text-slate-500">Gastos</dt>
                <dd className="font-semibold tabular-nums text-slate-800">{formatearBs(totalGastos)}</dd>
              </div>
              <div className="flex items-center gap-2">
                <span aria-hidden="true" className="h-2 w-2 rounded-full bg-indigo-400" />
                <dt className="text-slate-500">Inversiones</dt>
                <dd className="font-semibold tabular-nums text-slate-800">
                  {formatearBs(totalInversiones)}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <Filter className="w-3.5 h-3.5 text-amber-600" />
            <span>Filtros de búsqueda</span>
          </div>
          <div className="flex items-center gap-3">
            {hayFiltros && (
              <button
                type="button"
                onClick={limpiarFiltros}
                className="inline-flex items-center gap-1 text-xs text-amber-700 hover:text-amber-900 font-medium cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" />
                Limpiar filtros
              </button>
            )}
            <button
              type="button"
              onClick={recargar}
              disabled={cargando}
              aria-label="Actualizar listado"
              title="Actualizar listado"
              className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${cargando ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          <div className="sm:col-span-3">
            <label htmlFor="gasto-buscar" className={estiloEtiqueta}>
              Buscar
            </label>
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                id="gasto-buscar"
                type="search"
                placeholder="Concepto o detalle…"
                value={busqueda}
                onChange={(evento) => setBusqueda(evento.target.value)}
                className={`${estiloFiltro} pl-9`}
              />
            </div>
          </div>

          <div className="sm:col-span-2">
            <label htmlFor="gasto-filtro-tipo" className={estiloEtiqueta}>
              Tipo
            </label>
            <select
              id="gasto-filtro-tipo"
              value={tipo}
              onChange={(evento) => setTipo(evento.target.value as TipoMovimiento | '')}
              className={estiloFiltro}
            >
              <option value="">Todos</option>
              {TIPOS_MOVIMIENTO.map((opcion) => (
                <option key={opcion.valor} value={opcion.valor}>
                  {opcion.etiqueta}
                </option>
              ))}
            </select>
          </div>

          <div className="sm:col-span-3">
            <label htmlFor="gasto-filtro-categoria" className={estiloEtiqueta}>
              Categoría
            </label>
            <select
              id="gasto-filtro-categoria"
              value={categoria}
              onChange={(evento) => setCategoria(evento.target.value as CategoriaMovimiento | '')}
              className={estiloFiltro}
            >
              <option value="">Todas</option>
              {CATEGORIAS_MOVIMIENTO.map((opcion) => (
                <option key={opcion.valor} value={opcion.valor}>
                  {opcion.etiqueta}
                </option>
              ))}
            </select>
          </div>

          <div className="sm:col-span-2">
            <label htmlFor="gasto-desde" className={estiloEtiqueta}>
              Desde
            </label>
            <input
              id="gasto-desde"
              type="date"
              value={desde}
              max={hasta || undefined}
              onChange={(evento) => setDesde(evento.target.value)}
              className={`${estiloFiltro} tabular-nums`}
            />
          </div>

          <div className="sm:col-span-2">
            <label htmlFor="gasto-hasta" className={estiloEtiqueta}>
              Hasta
            </label>
            <input
              id="gasto-hasta"
              type="date"
              value={hasta}
              min={desde || undefined}
              onChange={(evento) => setHasta(evento.target.value)}
              className={`${estiloFiltro} tabular-nums`}
            />
          </div>
        </div>

        <label className="inline-flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
          <input
            type="checkbox"
            checked={incluirAnulados}
            onChange={(evento) => setIncluirAnulados(evento.target.checked)}
            className="h-4 w-4 rounded border-slate-300 accent-amber-600"
          />
          Incluir movimientos anulados
        </label>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
        {error ? (
          <div role="alert" className="flex flex-col items-center gap-3 px-5 py-14 text-center">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <p className="text-sm font-semibold text-slate-800">{error}</p>
            <button
              type="button"
              onClick={recargar}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
            >
              Reintentar
            </button>
          </div>
        ) : cargando && movimientos.length === 0 ? (
          <div className="flex items-center justify-center gap-2 px-5 py-16 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Cargando movimientos…
          </div>
        ) : movimientos.length === 0 ? (
          <div className="flex flex-col items-center gap-3 px-5 py-14 text-center">
            <Receipt className="h-8 w-8 text-slate-300" />
            <p className="text-sm font-semibold text-slate-800">
              {hayFiltros ? 'Ningún movimiento coincide con los filtros.' : 'Todavía no hay gastos registrados.'}
            </p>
            <p className="max-w-sm text-xs text-slate-500">
              {hayFiltros
                ? 'Prueba con otro rango de fechas o quita algún filtro.'
                : 'Registra el alquiler, los servicios o una compra de equipos y aparecerán aquí.'}
            </p>
            {hayFiltros ? (
              <button
                type="button"
                onClick={limpiarFiltros}
                className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                Limpiar filtros
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setModal({ tipo: 'registrar' })}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-amber-600/20 transition-all hover:from-amber-700 hover:to-amber-800"
              >
                <Plus className="h-4 w-4" />
                Registrar el primero
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[880px] text-sm">
                <caption className="sr-only">Gastos e inversiones registrados</caption>
                <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th scope="col" className="px-4 py-3">Fecha</th>
                    <th scope="col" className="px-4 py-3">Tipo</th>
                    <th scope="col" className="px-4 py-3">Categoría</th>
                    <th scope="col" className="px-4 py-3">Concepto</th>
                    <th scope="col" className="px-4 py-3 text-right">Monto</th>
                    <th scope="col" className="px-4 py-3">Registró</th>
                    <th scope="col" className="px-4 py-3">Estado</th>
                    <th scope="col" className="px-4 py-3">
                      <span className="sr-only">Acciones</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {visibles.items.map((movimiento) => (
                    <tr
                      key={movimiento.id_movimiento}
                      className={
                        movimiento.anulado
                          ? 'bg-slate-50/60 text-slate-400'
                          : 'transition-colors hover:bg-amber-50/30'
                      }
                    >
                      <td className="whitespace-nowrap px-4 py-3 text-xs tabular-nums text-slate-500">
                        {formatearFecha(movimiento.fecha_hora)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${
                            movimiento.anulado
                              ? 'bg-slate-100 text-slate-500 ring-slate-200'
                              : movimiento.tipo === 'inversion'
                                ? 'bg-indigo-50 text-indigo-700 ring-indigo-200'
                                : 'bg-rose-50 text-rose-700 ring-rose-200'
                          }`}
                        >
                          {movimiento.tipo_display}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{movimiento.categoria_display}</td>
                      <td className="max-w-[260px] px-4 py-3">
                        <p
                          className={`truncate font-medium ${
                            movimiento.anulado ? 'text-slate-400 line-through' : 'text-slate-900'
                          }`}
                          title={movimiento.concepto}
                        >
                          {movimiento.concepto}
                        </p>
                        {movimiento.descripcion && (
                          <p className="truncate text-xs text-slate-400" title={movimiento.descripcion}>
                            {movimiento.descripcion}
                          </p>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right font-semibold tabular-nums text-slate-900">
                        {formatearBs(movimiento.monto)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-500">
                        {movimiento.registrado_por}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${
                            movimiento.anulado
                              ? 'bg-slate-100 text-slate-500 ring-slate-200'
                              : 'bg-emerald-50 text-emerald-700 ring-emerald-200'
                          }`}
                        >
                          {movimiento.anulado ? 'Anulado' : 'Vigente'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {!movimiento.anulado && (
                          <button
                            type="button"
                            onClick={() => setModal({ tipo: 'anular', movimiento })}
                            aria-label={`Anular ${movimiento.concepto}`}
                            title="Anular movimiento"
                            className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                          >
                            <Ban className="h-4 w-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3 border-t border-slate-100 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs text-slate-500">
                Mostrando{' '}
                <span className="font-semibold tabular-nums text-slate-700">
                  {visibles.inicio + 1}–{visibles.fin}
                </span>{' '}
                de <span className="font-semibold tabular-nums text-slate-700">{visibles.total}</span>{' '}
                {visibles.total === 1 ? 'movimiento' : 'movimientos'}
              </p>
              <Paginacion
                pagina={visibles.pagina}
                totalPaginas={visibles.totalPaginas}
                onCambiar={setPagina}
                etiqueta="Paginación de gastos"
              />
            </div>
          </>
        )}
      </section>

      {modal?.tipo === 'registrar' && (
        <RegistrarGastoModal
          onCerrar={cerrarModal}
          onRegistrado={(movimiento) => {
            setAviso({
              tono: 'exito',
              texto: `${movimiento.tipo === 'inversion' ? 'Inversión registrada' : 'Gasto registrado'}: ${movimiento.concepto} (${formatearBs(movimiento.monto)}).`,
            });
            recargar();
          }}
        />
      )}

      {modal?.tipo === 'anular' && (
        <AnularGastoModal
          movimiento={modal.movimiento}
          ocupado={anulando}
          onCancelar={cerrarModal}
          onConfirmar={confirmarAnulacion}
        />
      )}
    </div>
  );
};

export default GastosPage;
