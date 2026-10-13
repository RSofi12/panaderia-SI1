import React, { useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { AlertCircle, CheckCircle2, Package, Pencil, Plus, Power, RefreshCw, Search } from 'lucide-react';
import { useAuth } from '../../../../contexts/AuthContext';
import Modal from '../../components/Modal';
import inventarioService from '../../../../services/inventarioService';
import ConfirmarEstadoMateriaDialog from './components/ConfirmarEstadoMateriaDialog';
import type {
  EstadoStock,
  MateriaPrimaFiltros,
  MateriaPrimaPayload,
  MateriaPrimaStock,
} from '../../../../types/inventario';

type EstadoFiltro = '' | 'bajo_minimo' | 'true' | 'false' | 'all';

interface Resultado {
  clave: string;
  materias: MateriaPrimaStock[];
  error: string | null;
}

const formatoNumero = new Intl.NumberFormat('es-BO', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 3,
});

const ESTADOS: Record<EstadoStock, { etiqueta: string; badge: string; punto: string }> = {
  normal: {
    etiqueta: 'Normal',
    badge: 'bg-emerald-50 text-emerald-700',
    punto: 'bg-emerald-500',
  },
  bajo_minimo: {
    etiqueta: 'Bajo mínimo',
    badge: 'bg-amber-50 text-amber-700',
    punto: 'bg-amber-500',
  },
  agotado: {
    etiqueta: 'Agotado',
    badge: 'bg-red-50 text-red-700',
    punto: 'bg-red-500',
  },
};

export const InventarioTab: React.FC = () => {
  const { hasPermission } = useAuth();
  const puedeGestionar = hasPermission('gestionar_materias_primas');
  const [busqueda, setBusqueda] = useState('');
  const [filtro, setFiltro] = useState<EstadoFiltro>('');
  const [version, setVersion] = useState(0);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [materiaEditando, setMateriaEditando] = useState<MateriaPrimaStock | null>(null);
  const [materiaCambiarEstado, setMateriaCambiarEstado] = useState<MateriaPrimaStock | null>(null);
  const [procesandoEstado, setProcesandoEstado] = useState(false);
  const [formularioAbierto, setFormularioAbierto] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  const claveConsulta = JSON.stringify([busqueda.trim(), filtro, version]);
  const cargando = resultado?.clave !== claveConsulta;

  useEffect(() => {
    let vigente = true;
    const filtros: MateriaPrimaFiltros = {};
    const termino = busqueda.trim();
    if (termino) filtros.nombre = termino;
    if (filtro === 'bajo_minimo') filtros.bajo_minimo = true;
    if (filtro === 'true') filtros.activo = true;
    if (filtro === 'false') filtros.activo = false;
    if (filtro === 'all') filtros.activo = 'all';

    const temporizador = window.setTimeout(() => {
      inventarioService
        .listarStock(filtros)
        .then((materias) => {
          if (vigente) setResultado({ clave: claveConsulta, materias, error: null });
        })
        .catch((err: unknown) => {
          if (!vigente) return;
          const sinPermiso = isAxiosError(err) && err.response?.status === 403;
          setResultado({
            clave: claveConsulta,
            materias: [],
            error: sinPermiso
              ? 'Tu rol no puede consultar el stock de materia prima.'
              : 'No se pudo cargar el stock. Verifica que el backend esté en ejecución.',
          });
        });
    }, termino ? 250 : 0);

    return () => {
      vigente = false;
      window.clearTimeout(temporizador);
    };
  }, [busqueda, filtro, claveConsulta]);

  const materias = resultado?.materias ?? [];
  let bajoMinimo = 0;
  let agotadas = 0;
  let inactivas = 0;
  for (const materia of materias) {
    if (materia.estado === 'bajo_minimo') bajoMinimo += 1;
    if (materia.estado === 'agotado') agotadas += 1;
    if (!materia.activo) inactivas += 1;
  }

  const cerrarFormulario = () => {
    if (guardando) return;
    setFormularioAbierto(false);
    setMateriaEditando(null);
    setErrorAccion(null);
    setErroresCampos({});
  };

  const guardarMateria = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const payload: MateriaPrimaPayload = {
      nombre: String(datos.get('nombre') ?? '').trim(),
      unidad_medida: String(datos.get('unidad_medida') ?? '').trim(),
      stock_minimo: String(datos.get('stock_minimo') ?? ''),
    };
    setGuardando(true);
    setErrorAccion(null);
    setErroresCampos({});
    try {
      if (materiaEditando) {
        await inventarioService.actualizar(materiaEditando.id_materia_prima, payload);
      } else {
        await inventarioService.crear(payload);
      }
      setFormularioAbierto(false);
      setMateriaEditando(null);
      setMensaje(materiaEditando ? 'Materia prima actualizada.' : 'Materia prima agregada con stock inicial en cero.');
      setVersion((actual) => actual + 1);
    } catch (err: unknown) {
      if (
        isAxiosError(err) &&
        err.response?.status === 400 &&
        typeof err.response.data === 'object' &&
        err.response.data !== null
      ) {
        const data = err.response.data as Record<string, unknown>;
        const errores: Record<string, string> = {};
        for (const [campo, val] of Object.entries(data)) {
          if (Array.isArray(val)) {
            errores[campo] = val.join(' ');
          } else if (typeof val === 'string') {
            errores[campo] = val;
          }
        }
        setErroresCampos(errores);
        if (errores.non_field_errors || errores.detail) {
          setErrorAccion(errores.non_field_errors || errores.detail);
        }
      } else {
        setErrorAccion('No se pudo guardar. Verifica tu permiso y que el backend esté disponible.');
      }
    } finally {
      setGuardando(false);
    }
  };

  const alternarEstado = (materia: MateriaPrimaStock) => {
    setErrorAccion(null);
    setMateriaCambiarEstado(materia);
  };

  const confirmarCambioEstado = async () => {
    if (!materiaCambiarEstado) return;
    setProcesandoEstado(true);
    try {
      await inventarioService.alternarActivo(materiaCambiarEstado.id_materia_prima);
      setMensaje(
        `${materiaCambiarEstado.nombre} ${materiaCambiarEstado.activo ? 'inactivada' : 'activada'}.`
      );
      setMateriaCambiarEstado(null);
      setVersion((actual) => actual + 1);
    } catch {
      setErrorAccion('No se pudo cambiar el estado. Verifica tu permiso y que el backend esté disponible.');
      setMateriaCambiarEstado(null);
    } finally {
      setProcesandoEstado(false);
    }
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white">
      <div className="flex flex-col gap-3 border-b border-slate-100 p-4 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 w-4 h-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar materia prima por nombre..."
            aria-label="Buscar materia prima por nombre"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder-slate-400 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>
        <select
          value={filtro}
          onChange={(e) => setFiltro(e.target.value as EstadoFiltro)}
          aria-label="Filtrar por nivel de stock"
          className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500 md:w-56"
        >
          <option value="">Activas · todos los niveles</option>
          <option value="bajo_minimo">Solo bajo el mínimo</option>
          <option value="true">Solo activas</option>
          <option value="false">Solo inactivas</option>
          <option value="all">Activas e inactivas</option>
        </select>
        <button
          type="button"
          onClick={() => setVersion((v) => v + 1)}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
        >
          <RefreshCw className={`w-4 h-4 ${cargando ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
        {puedeGestionar && (
          <button
            type="button"
            onClick={() => {
              setMateriaEditando(null);
              setErrorAccion(null);
              setFormularioAbierto(true);
            }}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-amber-800 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          >
            <Plus className="h-4 w-4" />
            Nueva materia prima
          </button>
        )}
      </div>

      {mensaje && (
        <div className="m-4 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {mensaje}
          <button type="button" onClick={() => setMensaje(null)} className="ml-auto rounded px-2 py-1 font-semibold hover:bg-emerald-100" aria-label="Cerrar aviso">×</button>
        </div>
      )}
      {errorAccion && (
        <div className="m-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
          <AlertCircle className="h-5 w-5 shrink-0" />
          {errorAccion}
        </div>
      )}

      {resultado?.error ? (
        <div className="m-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {resultado.error}
        </div>
      ) : (
        <div className={`overflow-x-auto transition-opacity ${cargando ? 'opacity-60' : ''}`}>
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Materia prima</th>
                <th className="px-4 py-3">Unidad</th>
                <th className="px-4 py-3 text-right">Stock actual</th>
                <th className="px-4 py-3 text-right">Stock mínimo</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Disponibilidad</th>
                {puedeGestionar && <th className="px-4 py-3 text-right">Acciones</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {materias.map((materia) => {
                const estado = ESTADOS[materia.estado];
                return (
                  <tr key={materia.id_materia_prima}>
                    <td className="px-4 py-3">
                      <p className="font-semibold text-slate-900">{materia.nombre}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{materia.unidad_medida}</td>
                    <td className="px-4 py-3 text-right tabular-nums font-semibold text-slate-900">
                      {formatoNumero.format(Number(materia.stock_actual))}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-600">
                      {formatoNumero.format(Number(materia.stock_minimo))}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${estado.badge}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${estado.punto}`} />
                        {estado.etiqueta}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${materia.activo ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                        {materia.activo ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    {puedeGestionar && (
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => {
                              setMateriaEditando(materia);
                              setErrorAccion(null);
                              setFormularioAbierto(true);
                            }}
                            className="inline-flex min-h-10 items-center gap-1.5 rounded-lg border border-slate-200 px-3 text-xs font-semibold text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-amber-500"
                            aria-label={`Editar ${materia.nombre}`}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => alternarEstado(materia)}
                            className={`inline-flex min-h-10 items-center gap-1.5 rounded-lg border px-3 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-amber-500 ${materia.activo ? 'border-red-200 text-red-700 hover:bg-red-50' : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'}`}
                            aria-label={`${materia.activo ? 'Inactivar' : 'Activar'} ${materia.nombre}`}
                          >
                            <Power className="h-3.5 w-3.5" />
                            {materia.activo ? 'Inactivar' : 'Activar'}
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                );
              })}

              {!cargando && materias.length === 0 && (
                <tr>
                  <td colSpan={puedeGestionar ? 7 : 6} className="px-4 py-12 text-center">
                    <Package className="mx-auto mb-2 w-8 h-8 text-slate-300" />
                    <p className="text-sm font-medium text-slate-500">
                      No hay materias primas con esos filtros.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <div className="border-t border-slate-100 px-4 py-3 text-xs text-slate-500">
        {cargando && !resultado
          ? 'Cargando stock...'
          : `Mostrando ${materias.length} materias primas · ${bajoMinimo} bajo el mínimo · ${agotadas} agotadas · ${inactivas} inactivas`}
      </div>

      {formularioAbierto && (
        <Modal
          titulo={materiaEditando ? 'Editar materia prima' : 'Nueva materia prima'}
          subtitulo="El stock inicial se establece en cero y se incrementa al registrar compras."
          onCerrar={cerrarFormulario}
          sinCerrar={guardando}
        >
          <form className="mt-5 space-y-4" onSubmit={(event) => void guardarMateria(event)}>
            <label className="block text-sm font-medium text-slate-700">
              Nombre
              <input
                name="nombre"
                required
                maxLength={100}
                defaultValue={materiaEditando?.nombre ?? ''}
                autoFocus
                className={`mt-1.5 w-full rounded-xl border px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 ${
                  erroresCampos.nombre
                    ? 'border-red-400 focus:border-red-600 focus:ring-red-500'
                    : 'border-slate-300 focus:border-amber-600 focus:ring-amber-500'
                }`}
              />
              {erroresCampos.nombre && (
                <p className="mt-1 text-xs text-red-600">{erroresCampos.nombre}</p>
              )}
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Unidad de medida
              <input
                name="unidad_medida"
                required
                maxLength={20}
                placeholder="Ej.: kg, litro, unidad"
                defaultValue={materiaEditando?.unidad_medida ?? ''}
                className={`mt-1.5 w-full rounded-xl border px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 ${
                  erroresCampos.unidad_medida
                    ? 'border-red-400 focus:border-red-600 focus:ring-red-500'
                    : 'border-slate-300 focus:border-amber-600 focus:ring-amber-500'
                }`}
              />
              {erroresCampos.unidad_medida && (
                <p className="mt-1 text-xs text-red-600">{erroresCampos.unidad_medida}</p>
              )}
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Stock mínimo
              <input
                name="stock_minimo"
                type="number"
                required
                min="0"
                step="0.001"
                defaultValue={materiaEditando?.stock_minimo ?? '0'}
                className={`mt-1.5 w-full rounded-xl border px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 ${
                  erroresCampos.stock_minimo
                    ? 'border-red-400 focus:border-red-600 focus:ring-red-500'
                    : 'border-slate-300 focus:border-amber-600 focus:ring-amber-500'
                }`}
              />
              {erroresCampos.stock_minimo && (
                <p className="mt-1 text-xs text-red-600">{erroresCampos.stock_minimo}</p>
              )}
            </label>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                disabled={guardando}
                onClick={cerrarFormulario}
                className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60 cursor-pointer"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={guardando}
                className="min-h-11 rounded-xl bg-amber-700 px-4 text-sm font-semibold text-white hover:bg-amber-800 disabled:cursor-wait disabled:opacity-60 cursor-pointer"
              >
                {guardando ? 'Guardando…' : materiaEditando ? 'Guardar cambios' : 'Crear materia prima'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {materiaCambiarEstado && (
        <ConfirmarEstadoMateriaDialog
          materia={materiaCambiarEstado}
          procesando={procesandoEstado}
          onCancel={() => setMateriaCambiarEstado(null)}
          onConfirm={() => void confirmarCambioEstado()}
        />
      )}
    </section>
  );
};

export default InventarioTab;