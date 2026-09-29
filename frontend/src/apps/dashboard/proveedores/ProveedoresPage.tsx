import React, { useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import {
  AlertCircle,
  CheckCircle2,
  Pencil,
  Plus,
  Power,
  Search,
  Truck,
} from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import proveedorService from '../../../services/proveedorService';
import type { Proveedor, ProveedorFiltros } from '../../../types/proveedor';
import ProveedorFormModal from './components/ProveedorFormModal';
import ConfirmarEstadoProveedorDialog from './components/ConfirmarEstadoProveedorDialog';

type EstadoFiltro = '' | 'true' | 'false';

type ModalAbierto =
  | { tipo: 'formulario'; proveedor: Proveedor | null }
  | { tipo: 'estado'; proveedor: Proveedor }
  | null;

interface Resultado {
  clave: string;
  proveedores: Proveedor[];
  error: string | null;
}

const formatoFecha = new Intl.DateTimeFormat('es-BO', { dateStyle: 'medium' });

export const ProveedoresPage: React.FC = () => {
  const { hasPermission } = useAuth();
  const puedeGestionar = hasPermission('gestionar_proveedores');

  const [busqueda, setBusqueda] = useState('');
  const [estado, setEstado] = useState<EstadoFiltro>('');
  const [version, setVersion] = useState(0);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [modal, setModal] = useState<ModalAbierto>(null);
  const [procesandoEstado, setProcesandoEstado] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  const claveConsulta = JSON.stringify([busqueda.trim(), estado, version]);
  const cargando = resultado?.clave !== claveConsulta;

  useEffect(() => {
    let vigente = true;
    const filtros: ProveedorFiltros = {};
    const termino = busqueda.trim();
    if (termino) filtros.q = termino;
    if (estado) filtros.activo = estado;

    const temporizador = window.setTimeout(() => {
      proveedorService
        .listar(filtros)
        .then((proveedores) => {
          if (vigente) setResultado({ clave: claveConsulta, proveedores, error: null });
        })
        .catch((err: unknown) => {
          if (!vigente) return;
          const sinPermiso = isAxiosError(err) && err.response?.status === 403;
          setResultado({
            clave: claveConsulta,
            proveedores: [],
            error: sinPermiso
              ? 'Tu rol no puede consultar el directorio de proveedores.'
              : 'No se pudo cargar el directorio. Verifica que el backend esté en ejecución.',
          });
        });
    }, termino ? 250 : 0);

    return () => {
      vigente = false;
      window.clearTimeout(temporizador);
    };
  }, [busqueda, estado, claveConsulta]);

  const proveedores = resultado?.proveedores ?? [];
  let activos = 0;
  for (const proveedor of proveedores) {
    if (proveedor.activo) activos += 1;
  }

  const mostrarAviso = (mensaje: string) => {
    setAviso(mensaje);
    window.setTimeout(() => setAviso(null), 3500);
  };

  const handleGuardado = (proveedor: Proveedor) => {
    const eraEdicion = modal?.tipo === 'formulario' && modal.proveedor !== null;
    setModal(null);
    setVersion((v) => v + 1);
    mostrarAviso(eraEdicion ? `${proveedor.nombre} actualizado.` : `${proveedor.nombre} registrado.`);
  };

  const handleConfirmarEstado = async () => {
    if (modal?.tipo !== 'estado') return;
    setProcesandoEstado(true);
    try {
      const actualizado = await proveedorService.alternarActivo(modal.proveedor.id_proveedor);
      setModal(null);
      setVersion((v) => v + 1);
      mostrarAviso(`${actualizado.nombre} ${actualizado.activo ? 'activado' : 'inactivado'}.`);
    } catch {
      setModal(null);
      mostrarAviso('No se pudo cambiar el estado del proveedor.');
    } finally {
      setProcesandoEstado(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
            Compras y Proveedores · CU6
          </p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Proveedores</h2>
          <p className="mt-1 text-sm text-slate-500">
            Proveedores de materias primas e insumos, con sus datos de contacto.
          </p>
        </div>
        {puedeGestionar && (
          <button
            type="button"
            onClick={() => setModal({ tipo: 'formulario', proveedor: null })}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-amber-600/20 hover:from-amber-700 hover:to-amber-800 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Nuevo proveedor
          </button>
        )}
      </div>

      {aviso && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          {aviso}
        </div>
      )}

      <section className="rounded-2xl border border-slate-200 bg-white">
        <div className="flex flex-col gap-3 border-b border-slate-100 p-4 md:flex-row">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 w-4 h-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por nombre o teléfono..."
              aria-label="Buscar proveedor por nombre o teléfono"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder-slate-400 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <select
            value={estado}
            onChange={(e) => setEstado(e.target.value as EstadoFiltro)}
            aria-label="Filtrar por estado"
            className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500 md:w-44"
          >
            <option value="">Todos los estados</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
        </div>

        {resultado?.error ? (
          <div className="m-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <AlertCircle className="w-5 h-5 shrink-0" />
            {resultado.error}
          </div>
        ) : (
          <div className={`overflow-x-auto transition-opacity ${cargando ? 'opacity-60' : ''}`}>
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">Proveedor</th>
                  <th className="px-4 py-3">Teléfono</th>
                  <th className="px-4 py-3">Dirección</th>
                  <th className="px-4 py-3">Registro</th>
                  <th className="px-4 py-3">Estado</th>
                  {puedeGestionar && <th className="px-4 py-3 text-right">Acciones</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {proveedores.map((proveedor) => (
                  <tr
                    key={proveedor.id_proveedor}
                    className={proveedor.activo ? '' : 'bg-slate-50/60 text-slate-400'}
                  >
                    <td className="px-4 py-3">
                      <p className={`font-semibold ${proveedor.activo ? 'text-slate-900' : 'text-slate-500'}`}>
                        {proveedor.nombre}
                      </p>
                    </td>
                    <td className="px-4 py-3 tabular-nums text-slate-600">{proveedor.telefono ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-600">
                      <p className="max-w-xs truncate">{proveedor.direccion ?? '—'}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {formatoFecha.format(new Date(proveedor.fecha_registro))}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                          proveedor.activo ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${proveedor.activo ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                        {proveedor.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    {puedeGestionar && (
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-1">
                          <button
                            type="button"
                            onClick={() => setModal({ tipo: 'formulario', proveedor })}
                            title="Editar"
                            aria-label={`Editar ${proveedor.nombre}`}
                            className="rounded-lg p-2 text-slate-500 hover:bg-amber-50 hover:text-amber-700 cursor-pointer"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setModal({ tipo: 'estado', proveedor })}
                            title={proveedor.activo ? 'Inactivar' : 'Activar'}
                            aria-label={`${proveedor.activo ? 'Inactivar' : 'Activar'} ${proveedor.nombre}`}
                            className={`rounded-lg p-2 cursor-pointer ${
                              proveedor.activo
                                ? 'text-slate-500 hover:bg-red-50 hover:text-red-600'
                                : 'text-slate-400 hover:bg-emerald-50 hover:text-emerald-600'
                            }`}
                          >
                            <Power className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}

                {!cargando && proveedores.length === 0 && (
                  <tr>
                    <td colSpan={puedeGestionar ? 6 : 5} className="px-4 py-12 text-center">
                      <Truck className="mx-auto mb-2 w-8 h-8 text-slate-300" />
                      <p className="text-sm font-medium text-slate-500">No hay proveedores con esos filtros.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="border-t border-slate-100 px-4 py-3 text-xs text-slate-500">
          {cargando && !resultado
            ? 'Cargando proveedores...'
            : `Mostrando ${proveedores.length} proveedores · ${activos} activos · ${proveedores.length - activos} inactivos`}
        </div>
      </section>

      {modal?.tipo === 'formulario' && (
        <ProveedorFormModal
          proveedor={modal.proveedor}
          onClose={() => setModal(null)}
          onSaved={handleGuardado}
        />
      )}

      {modal?.tipo === 'estado' && (
        <ConfirmarEstadoProveedorDialog
          proveedor={modal.proveedor}
          procesando={procesandoEstado}
          onCancel={() => setModal(null)}
          onConfirm={handleConfirmarEstado}
        />
      )}
    </div>
  );
};

export default ProveedoresPage;
