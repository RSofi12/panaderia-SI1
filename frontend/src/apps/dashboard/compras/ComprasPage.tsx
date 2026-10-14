import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { isAxiosError } from 'axios';
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  DollarSign,
  Eye,
  Filter,
  Plus,
  RotateCcw,
  Search,
  ShoppingCart,
} from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import compraService from '../../../services/compraService';
import proveedorService from '../../../services/proveedorService';
import type { Compra, CompraFiltros, CompraReposicion, CompraResumen } from '../../../types/compra';
import type { Proveedor } from '../../../types/proveedor';
import RegistrarCompraModal from './components/RegistrarCompraModal';
import DetalleCompraModal from './components/DetalleCompraModal';
import { leerReposicion } from './reposicion';

type ModalAbierto =
  | { tipo: 'registrar'; reposicion?: CompraReposicion }
  | { tipo: 'detalle'; idCompra: number }
  | null;

interface Resultado {
  version: number;
  compras: CompraResumen[];
  error: string | null;
}

const formatoFechaHora = new Intl.DateTimeFormat('es-BO', { dateStyle: 'medium', timeStyle: 'short' });

export const ComprasPage: React.FC = () => {
  const { hasPermission } = useAuth();
  const puedeRegistrar = hasPermission('registrar_compras');
  const [params, setParams] = useSearchParams();
  const reposicion = puedeRegistrar ? leerReposicion(params) : undefined;

  const [version, setVersion] = useState(0);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [modal, setModal] = useState<ModalAbierto>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  // Derivar la apertura desde la URL evita duplicar estado mediante un efecto.
  const modalActivo: ModalAbierto = modal ?? (reposicion ? { tipo: 'registrar', reposicion } : null);

  // Filtros
  const [filtros, setFiltros] = useState<CompraFiltros>({
    search: '',
    id_proveedor: '',
    fecha_desde: '',
    fecha_hasta: '',
  });
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);

  const cargando = resultado?.version !== version;

  useEffect(() => {
    proveedorService
      .listar({ activo: 'true' })
      .then(setProveedores)
      .catch(() => {});
  }, []);

  useEffect(() => {
    let vigente = true;
    const timer = setTimeout(() => {
      const params: CompraFiltros = {};
      if (filtros.search?.trim()) params.search = filtros.search.trim();
      if (filtros.id_proveedor) params.id_proveedor = filtros.id_proveedor;
      if (filtros.fecha_desde) params.fecha_desde = filtros.fecha_desde;
      if (filtros.fecha_hasta) params.fecha_hasta = filtros.fecha_hasta;

      compraService
        .listar(params)
        .then((compras) => {
          if (vigente) setResultado({ version, compras, error: null });
        })
        .catch((err: unknown) => {
          if (!vigente) return;
          const sinPermiso = isAxiosError(err) && err.response?.status === 403;
          setResultado({
            version,
            compras: [],
            error: sinPermiso
              ? 'Tu rol no puede consultar las compras.'
              : 'No se pudieron cargar las compras. Verifica que el backend esté en ejecución.',
          });
        });
    }, 250);

    return () => {
      vigente = false;
      clearTimeout(timer);
    };
  }, [version, filtros]);

  const compras = resultado?.compras ?? [];

  // KPIs
  let totalGeneral = 0;
  const conteoProveedores: Record<string, number> = {};
  for (const compra of compras) {
    const monto = Number(compra.total || 0);
    totalGeneral += monto;
    conteoProveedores[compra.proveedor_nombre] =
      (conteoProveedores[compra.proveedor_nombre] || 0) + monto;
  }

  let proveedorTop = '—';
  let maxMonto = 0;
  for (const [nombre, monto] of Object.entries(conteoProveedores)) {
    if (monto > maxMonto) {
      maxMonto = monto;
      proveedorTop = nombre;
    }
  }

  const hayFiltrosActivos = Boolean(
    filtros.search?.trim() || filtros.id_proveedor || filtros.fecha_desde || filtros.fecha_hasta
  );

  const limpiarFiltros = () => {
    setFiltros({
      search: '',
      id_proveedor: '',
      fecha_desde: '',
      fecha_hasta: '',
    });
  };

  const mostrarAviso = (mensaje: string) => {
    setAviso(mensaje);
    window.setTimeout(() => setAviso(null), 4000);
  };

  const cerrarModal = () => {
    setModal(null);
    if (params.has('reposicion_materia_prima') || params.has('reposicion_cantidad')) {
      const siguientes = new URLSearchParams(params);
      siguientes.delete('reposicion_materia_prima');
      siguientes.delete('reposicion_cantidad');
      setParams(siguientes, { replace: true });
    }
  };

  const handleRegistrada = (compra: Compra) => {
    cerrarModal();
    setVersion((v) => v + 1);
    mostrarAviso(
      `Compra registrada: #${compra.id_compra} a ${compra.proveedor_nombre} por Bs ${compra.total}.`
    );
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
            Compras y Proveedores · CU7
          </p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">
            Compras de materia prima
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Cada compra suma stock al inventario y actualiza el último precio del insumo.
          </p>
        </div>
        {puedeRegistrar && (
          <button
            type="button"
            onClick={() => setModal({ tipo: 'registrar' })}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-amber-600/20 hover:from-amber-700 hover:to-amber-800 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Registrar compra
          </button>
        )}
      </div>

      {/* Tarjetas KPI de Resumen */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4.5 shadow-xs flex items-center gap-4">
          <div className="rounded-xl bg-amber-50 p-3 text-amber-700">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Total Invertido</p>
            <p className="text-xl font-bold text-slate-900">
              Bs {totalGeneral.toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">En las compras visualizadas</p>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4.5 shadow-xs flex items-center gap-4">
          <div className="rounded-xl bg-blue-50 p-3 text-blue-700">
            <ShoppingCart className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">N.º de Operaciones</p>
            <p className="text-xl font-bold text-slate-900">{compras.length}</p>
            <p className="text-[11px] text-slate-400 mt-0.5">Registros completados</p>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4.5 shadow-xs flex items-center gap-4">
          <div className="rounded-xl bg-emerald-50 p-3 text-emerald-700">
            <Building2 className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-500">Proveedor Principal</p>
            <p className="text-base font-bold text-slate-900 truncate" title={proveedorTop}>
              {proveedorTop}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {maxMonto > 0 ? `Bs ${maxMonto.toFixed(2)} acumulados` : 'Sin movimientos'}
            </p>
          </div>
        </div>
      </div>

      {/* Barra de Filtros */}
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <Filter className="w-3.5 h-3.5 text-amber-600" />
            <span>Filtros de búsqueda</span>
          </div>
          {hayFiltrosActivos && (
            <button
              type="button"
              onClick={limpiarFiltros}
              className="inline-flex items-center gap-1 text-xs text-amber-700 hover:text-amber-900 font-medium cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              Limpiar filtros
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          {/* Buscador general */}
          <div className="sm:col-span-4 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Buscar por proveedor o N.º..."
              value={filtros.search ?? ''}
              onChange={(e) => setFiltros((prev) => ({ ...prev, search: e.target.value }))}
              className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
            />
          </div>

          {/* Selector de Proveedor */}
          <div className="sm:col-span-3">
            <select
              value={filtros.id_proveedor ?? ''}
              onChange={(e) => setFiltros((prev) => ({ ...prev, id_proveedor: e.target.value }))}
              aria-label="Filtrar por proveedor"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
            >
              <option value="">Todos los proveedores</option>
              {proveedores.map((p) => (
                <option key={p.id_proveedor} value={p.id_proveedor}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>

          {/* Fecha Desde */}
          <div className="sm:col-span-2.5 sm:col-span-2">
            <div className="relative">
              <input
                type="date"
                title="Fecha desde"
                aria-label="Fecha desde"
                value={filtros.fecha_desde ?? ''}
                onChange={(e) => setFiltros((prev) => ({ ...prev, fecha_desde: e.target.value }))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
              />
            </div>
          </div>

          {/* Fecha Hasta */}
          <div className="sm:col-span-2.5 sm:col-span-2">
            <div className="relative">
              <input
                type="date"
                title="Fecha hasta"
                aria-label="Fecha hasta"
                value={filtros.fecha_hasta ?? ''}
                onChange={(e) => setFiltros((prev) => ({ ...prev, fecha_hasta: e.target.value }))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
              />
            </div>
          </div>

          {/* Refrescar */}
          <div className="sm:col-span-1 flex justify-end">
            <button
              type="button"
              onClick={() => setVersion((v) => v + 1)}
              title="Refrescar lista"
              className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-600 hover:text-amber-700 hover:bg-amber-50 flex items-center justify-center transition-all cursor-pointer"
            >
              <RotateCcw className={`w-4 h-4 ${cargando ? 'animate-spin text-amber-600' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {aviso && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          {aviso}
        </div>
      )}

      {/* Tabla de Compras */}
      <section className="rounded-2xl border border-slate-200 bg-white shadow-xs">
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
                  <th className="px-4 py-3">N.º</th>
                  <th className="px-4 py-3">Fecha</th>
                  <th className="px-4 py-3">Proveedor</th>
                  <th className="px-4 py-3">Registrado por</th>
                  <th className="px-4 py-3 text-right">Líneas</th>
                  <th className="px-4 py-3 text-right">Total</th>
                  <th className="px-4 py-3 text-right">Detalle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {compras.map((compra) => (
                  <tr key={compra.id_compra} className="hover:bg-amber-50/30 transition-colors">
                    <td className="px-4 py-3 font-semibold text-slate-900">#{compra.id_compra}</td>
                    <td className="px-4 py-3 text-slate-500">
                      {formatoFechaHora.format(new Date(compra.fecha_hora))}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-800">{compra.proveedor_nombre}</td>
                    <td className="px-4 py-3 text-slate-600">{compra.registrado_por}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-600">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                        {compra.cantidad_lineas} {compra.cantidad_lineas === 1 ? 'ítem' : 'ítems'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums font-semibold text-slate-900">
                      Bs {Number(compra.total).toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => setModal({ tipo: 'detalle', idCompra: compra.id_compra })}
                        title="Ver detalle"
                        aria-label={`Ver detalle de la compra ${compra.id_compra}`}
                        className="rounded-lg p-2 text-slate-500 hover:bg-amber-50 hover:text-amber-700 cursor-pointer transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}

                {!cargando && compras.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center">
                      <ShoppingCart className="mx-auto mb-2 w-8 h-8 text-slate-300" />
                      <p className="text-sm font-medium text-slate-500">
                        {hayFiltrosActivos
                          ? 'No se encontraron compras con los filtros seleccionados.'
                          : 'Todavía no hay compras registradas.'}
                      </p>
                      {hayFiltrosActivos && (
                        <button
                          type="button"
                          onClick={limpiarFiltros}
                          className="mt-2 text-xs font-semibold text-amber-700 hover:underline cursor-pointer"
                        >
                          Restablecer filtros
                        </button>
                      )}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="border-t border-slate-100 px-4 py-3 text-xs font-medium text-slate-500 flex items-center justify-between">
          <span>
            {cargando && !resultado
              ? 'Cargando compras...'
              : `Mostrando ${compras.length} compras registrad${compras.length === 1 ? 'a' : 'as'}`}
          </span>
          <span className="font-semibold text-slate-800">
            Total periodo: Bs {totalGeneral.toFixed(2)}
          </span>
        </div>
      </section>

      {puedeRegistrar && modalActivo?.tipo === 'registrar' && (
        <RegistrarCompraModal
          key={modalActivo.reposicion
            ? `${modalActivo.reposicion.id_materia_prima}:${modalActivo.reposicion.cantidad}`
            : 'manual'}
          reposicion={modalActivo.reposicion}
          onClose={cerrarModal}
          onSaved={handleRegistrada}
        />
      )}

      {modalActivo?.tipo === 'detalle' && (
        <DetalleCompraModal idCompra={modalActivo.idCompra} onClose={cerrarModal} />
      )}
    </div>
  );
};

export default ComprasPage;
