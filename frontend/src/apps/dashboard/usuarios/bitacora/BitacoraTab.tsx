import React, { useEffect, useState } from 'react';
import { AlertCircle, ChevronLeft, ChevronRight, Eye, History, Search, X } from 'lucide-react';
import bitacoraService from '../../../../services/bitacoraService';
import { normalizarErrorApi } from '../../../../services/erroresApi';
import type { FiltrosBitacora, OpcionesBitacora, RegistroBitacora } from '../../../../types/bitacora';
import type { Paginado } from '../../../../types/usuarios';
import DetalleBitacoraModal from './DetalleBitacoraModal';
import { autorRegistro, clasesAccion, formatearFechaHora, nombreModulo } from './formato';

/** Igual al `PAGE_SIZE` de DRF en `settings.py`. */
const TAMANO_PAGINA = 10;
const RETRASO_BUSQUEDA = 300;

interface Filtros {
  fecha_desde: string;
  fecha_hasta: string;
  usuario: string;
  modulo: string;
  accion: string;
}

const FILTROS_VACIOS: Filtros = { fecha_desde: '', fecha_hasta: '', usuario: '', modulo: '', accion: '' };

interface Resultado {
  clave: string;
  datos: Paginado<RegistroBitacora> | null;
  error: string | null;
}

const OPCIONES_VACIAS: OpcionesBitacora = { acciones: [], modulos: [], usuarios: [] };

const claseCampo =
  'w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500';

export const BitacoraTab: React.FC = () => {
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_VACIOS);
  const [texto, setTexto] = useState('');
  const [textoAplicado, setTextoAplicado] = useState('');
  const [pagina, setPagina] = useState(1);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [opciones, setOpciones] = useState<OpcionesBitacora>(OPCIONES_VACIAS);
  const [seleccionado, setSeleccionado] = useState<RegistroBitacora | null>(null);

  const claveConsulta = JSON.stringify([filtros, textoAplicado, pagina]);
  const cargando = resultado?.clave !== claveConsulta;

  useEffect(() => {
    let vigente = true;
    bitacoraService
      .opciones()
      .then((datos) => {
        if (vigente) setOpciones(datos);
      })
      .catch(() => {
        // Sin opciones los filtros quedan vacíos; el listado muestra su propio error.
      });
    return () => {
      vigente = false;
    };
  }, []);

  useEffect(() => {
    const temporizador = window.setTimeout(() => {
      setTextoAplicado(texto.trim());
      setPagina(1);
    }, RETRASO_BUSQUEDA);
    return () => window.clearTimeout(temporizador);
  }, [texto]);

  useEffect(() => {
    let vigente = true;
    const parametros: FiltrosBitacora = { page: pagina };
    for (const [campo, valor] of Object.entries(filtros) as [keyof Filtros, string][]) {
      if (valor) parametros[campo] = valor;
    }
    if (textoAplicado) parametros.q = textoAplicado;

    bitacoraService
      .listar(parametros)
      .then((datos) => {
        if (vigente) setResultado({ clave: claveConsulta, datos, error: null });
      })
      .catch((fallo: unknown) => {
        if (!vigente) return;
        setResultado({
          clave: claveConsulta,
          datos: null,
          error: normalizarErrorApi(fallo).mensaje ?? 'No se pudo cargar la bitácora.',
        });
      });

    return () => {
      vigente = false;
    };
  }, [filtros, textoAplicado, pagina, claveConsulta]);

  const cambiarFiltro = (campo: keyof Filtros, valor: string) => {
    setFiltros((actuales) => ({ ...actuales, [campo]: valor }));
    setPagina(1);
  };

  const hayFiltros = textoAplicado !== '' || Object.values(filtros).some(Boolean);

  const limpiarFiltros = () => {
    setFiltros(FILTROS_VACIOS);
    setTexto('');
    setTextoAplicado('');
    setPagina(1);
  };

  const registros = resultado?.datos?.results ?? [];
  const total = resultado?.datos?.count ?? 0;
  const totalPaginas = Math.max(1, Math.ceil(total / TAMANO_PAGINA));
  const desde = total === 0 ? 0 : (pagina - 1) * TAMANO_PAGINA + 1;
  const hasta = Math.min(pagina * TAMANO_PAGINA, total);

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <div className="relative sm:col-span-2 lg:col-span-6">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Buscar en la descripción o por nombre de usuario..."
              aria-label="Buscar en la bitácora"
              className={`${claseCampo} pl-10`}
            />
          </div>
          <label className="text-xs font-semibold text-slate-600">
            Desde
            <input
              type="date"
              value={filtros.fecha_desde}
              max={filtros.fecha_hasta || undefined}
              onChange={(e) => cambiarFiltro('fecha_desde', e.target.value)}
              className={`${claseCampo} mt-1 font-normal`}
            />
          </label>
          <label className="text-xs font-semibold text-slate-600">
            Hasta
            <input
              type="date"
              value={filtros.fecha_hasta}
              min={filtros.fecha_desde || undefined}
              onChange={(e) => cambiarFiltro('fecha_hasta', e.target.value)}
              className={`${claseCampo} mt-1 font-normal`}
            />
          </label>
          <label className="text-xs font-semibold text-slate-600">
            Usuario
            <select
              value={filtros.usuario}
              onChange={(e) => cambiarFiltro('usuario', e.target.value)}
              className={`${claseCampo} mt-1 font-normal`}
            >
              <option value="">Todos</option>
              {opciones.usuarios.map((u) => (
                <option key={u.id_usuario} value={u.id_usuario}>
                  {u.nombre_completo} (@{u.nombre_usuario})
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs font-semibold text-slate-600">
            Módulo
            <select
              value={filtros.modulo}
              onChange={(e) => cambiarFiltro('modulo', e.target.value)}
              className={`${claseCampo} mt-1 font-normal`}
            >
              <option value="">Todos</option>
              {opciones.modulos.map((m) => (
                <option key={m} value={m}>
                  {nombreModulo(m)}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs font-semibold text-slate-600 sm:col-span-2">
            Tipo de acción
            <select
              value={filtros.accion}
              onChange={(e) => cambiarFiltro('accion', e.target.value)}
              className={`${claseCampo} mt-1 font-normal`}
            >
              <option value="">Todas</option>
              {opciones.acciones.map((a) => (
                <option key={a.valor} value={a.valor}>
                  {a.etiqueta}
                </option>
              ))}
            </select>
          </label>
        </div>
        {hayFiltros && (
          <button
            type="button"
            onClick={limpiarFiltros}
            className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-amber-700 hover:text-amber-800 cursor-pointer"
          >
            <X className="h-3.5 w-3.5" />
            Limpiar filtros
          </button>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white">
        {resultado?.error ? (
          <div className="m-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <AlertCircle className="h-5 w-5 shrink-0" />
            {resultado.error}
          </div>
        ) : (
          <div className={`overflow-x-auto transition-opacity ${cargando ? 'opacity-60' : ''}`}>
            <table className="w-full min-w-[860px] text-left text-sm">
              <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">Fecha y hora</th>
                  <th className="px-4 py-3">Usuario</th>
                  <th className="px-4 py-3">Acción</th>
                  <th className="px-4 py-3">Módulo</th>
                  <th className="px-4 py-3">Descripción</th>
                  <th className="px-4 py-3 text-right">Detalle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {registros.map((registro) => (
                  <tr key={registro.id_bitacora} className="hover:bg-amber-50/40">
                    <td className="whitespace-nowrap px-4 py-3 tabular-nums text-slate-600">
                      {formatearFechaHora(registro.fecha_hora)}
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900">{autorRegistro(registro)}</p>
                      {registro.nombre_usuario && (
                        <p className="text-xs text-slate-400">@{registro.nombre_usuario}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${clasesAccion(registro.accion)}`}
                      >
                        {registro.accion_etiqueta}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{nombreModulo(registro.tabla_afectada)}</td>
                    <td className="px-4 py-3 text-slate-600">
                      <p className="max-w-xs truncate">{registro.descripcion || '—'}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => setSeleccionado(registro)}
                        aria-label={`Ver detalle del registro ${registro.id_bitacora}`}
                        title="Ver detalle"
                        className="rounded-lg p-2 text-slate-500 hover:bg-amber-50 hover:text-amber-700 cursor-pointer"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}

                {!cargando && registros.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center">
                      <History className="mx-auto mb-2 h-8 w-8 text-slate-300" />
                      <p className="text-sm font-medium text-slate-500">No hay registros con esos filtros.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex flex-col gap-2 border-t border-slate-100 px-4 py-3 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <span>
            {cargando && !resultado
              ? 'Cargando bitácora...'
              : `Mostrando ${desde}–${hasta} de ${total} registros`}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPagina((p) => Math.max(1, p - 1))}
              disabled={pagina <= 1 || cargando}
              aria-label="Página anterior"
              className="rounded-lg border border-slate-200 p-1.5 text-slate-600 hover:bg-slate-50 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="tabular-nums">
              Página {pagina} de {totalPaginas}
            </span>
            <button
              type="button"
              onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
              disabled={pagina >= totalPaginas || cargando}
              aria-label="Página siguiente"
              className="rounded-lg border border-slate-200 p-1.5 text-slate-600 hover:bg-slate-50 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>

      {seleccionado && <DetalleBitacoraModal registro={seleccionado} onCerrar={() => setSeleccionado(null)} />}
    </div>
  );
};

export default BitacoraTab;
