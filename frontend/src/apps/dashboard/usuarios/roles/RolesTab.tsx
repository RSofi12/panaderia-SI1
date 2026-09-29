import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  KeyRound,
  Lock,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from 'lucide-react';
import rolesService from '../../../../services/rolesService';
import { normalizarErrorApi } from '../../../../services/erroresApi';
import type { GrupoModuloPermisos, RolDetalle, RolListado } from '../../../../types/roles';
import TarjetaRol from './TarjetaRol';
import MatrizPermisosModal from './MatrizPermisosModal';
import ModalRol from './ModalRol';

type FiltroTipoRol = 'todos' | 'sistema' | 'personalizados';

export const RolesTab: React.FC = () => {
  const [roles, setRoles] = useState<RolListado[]>([]);
  const [modulos, setModulos] = useState<GrupoModuloPermisos[]>([]);
  const [cargando, setCargando] = useState(true);
  const [cargandoDetalleId, setCargandoDetalleId] = useState<number | null>(null);

  // Filtros de búsqueda y segmentación
  const [busqueda, setBusqueda] = useState('');
  const [filtroTipo, setFiltroTipo] = useState<FiltroTipoRol>('todos');

  // Estados de modales
  const [rolDetalleMatriz, setRolDetalleMatriz] = useState<RolDetalle | null>(null);
  const [modalRol, setModalRol] = useState<{ abierto: boolean; rol: RolListado | null }>({
    abierto: false,
    rol: null,
  });

  const [aviso, setAviso] = useState<{ texto: string; tono: 'ok' | 'error' } | null>(null);
  const [refresco, setRefresco] = useState(0);

  const cargarDatos = useCallback(async () => {
    setCargando(true);
    try {
      const [listaRoles, listaModulos] = await Promise.all([
        rolesService.getRoles(),
        rolesService.getPermisosAgrupados(),
      ]);
      setRoles(listaRoles);
      setModulos(listaModulos);
    } catch (err: unknown) {
      const errorNorm = normalizarErrorApi(err);
      setAviso({
        texto: errorNorm.mensaje || 'No se pudieron cargar los roles del sistema.',
        tono: 'error',
      });
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos, refresco]);

  // Cálculos de métricas globales (KPIs)
  const totalPermisosSistema = useMemo(() => {
    return modulos.reduce((acc, m) => acc + m.permisos.length, 0);
  }, [modulos]);

  const kpis = useMemo(() => {
    const totalRoles = roles.length;
    const rolesProtegidos = roles.filter((r) => r.es_protegido).length;
    const rolesPersonalizados = totalRoles - rolesProtegidos;
    const totalUsuariosAsignados = roles.reduce((acc, r) => acc + r.total_usuarios, 0);

    return {
      totalRoles,
      rolesProtegidos,
      rolesPersonalizados,
      totalUsuariosAsignados,
    };
  }, [roles]);

  // Filtrado reactivo de roles
  const rolesFiltrados = useMemo(() => {
    const termino = busqueda.trim().toLowerCase();

    return roles.filter((rol) => {
      // Filtro por tipo
      if (filtroTipo === 'sistema' && !rol.es_protegido) return false;
      if (filtroTipo === 'personalizados' && rol.es_protegido) return false;

      // Filtro por texto
      if (!termino) return true;
      const nombreMatch = rol.nombre.toLowerCase().includes(termino);
      const descMatch = (rol.descripcion || '').toLowerCase().includes(termino);
      return nombreMatch || descMatch;
    });
  }, [roles, busqueda, filtroTipo]);

  const abrirMatriz = async (rolItem: RolListado) => {
    setCargandoDetalleId(rolItem.id_rol);
    try {
      const detalle = await rolesService.getRol(rolItem.id_rol);
      setRolDetalleMatriz(detalle);
    } catch (err: unknown) {
      const errorNorm = normalizarErrorApi(err);
      setAviso({
        texto: errorNorm.mensaje || `Error al abrir la matriz del rol "${rolItem.nombre}".`,
        tono: 'error',
      });
    } finally {
      setCargandoDetalleId(null);
    }
  };

  const guardarMatriz = async (permisosIds: number[]) => {
    if (!rolDetalleMatriz) return;
    await rolesService.actualizarMatriz(rolDetalleMatriz.id_rol, permisosIds);
    setRefresco((prev) => prev + 1);
  };

  return (
    <div className="space-y-6">
      {/* Barra superior del módulo */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-amber-600" aria-hidden="true" />
            <span>Perfiles de Acceso y Autorizaciones (RBAC)</span>
          </h2>
          <p className="mt-1 text-xs text-slate-500 leading-relaxed max-w-2xl">
            Administra los roles del personal y gobierna la matriz de permisos por módulo.
            Las autorizaciones se asignan a roles y se propagan inmediatamente a todas las cuentas asociadas.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setRefresco((prev) => prev + 1)}
            disabled={cargando}
            className="inline-flex min-h-10 items-center justify-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 cursor-pointer disabled:opacity-50"
            title="Actualizar listado de roles"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${cargando ? 'animate-spin' : ''}`}
              aria-hidden="true"
            />
            <span className="hidden sm:inline">Refrescar</span>
          </button>

          <button
            type="button"
            onClick={() => setModalRol({ abierto: true, rol: null })}
            className="inline-flex min-h-10 items-center justify-center gap-1.5 rounded-xl bg-amber-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-amber-700 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 cursor-pointer"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            <span>Nuevo rol</span>
          </button>
        </div>
      </div>

      {/* Tarjetas KPI de resumen */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Roles configurados</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-700 border border-amber-200/60">
              <ShieldCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 text-xl font-bold tracking-tight text-slate-900">
            {cargando ? '—' : kpis.totalRoles}
          </div>
          <p className="mt-0.5 text-[11px] text-slate-500">Perfiles en el sistema</p>
        </div>

        <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Personal cubierto</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200/60">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 text-xl font-bold tracking-tight text-slate-900">
            {cargando ? '—' : kpis.totalUsuariosAsignados}
          </div>
          <p className="mt-0.5 text-[11px] text-slate-500">Cuentas con rol activo</p>
        </div>

        <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Roles del sistema</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-700 border border-slate-200">
              <Lock className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 text-xl font-bold tracking-tight text-slate-900">
            {cargando ? '—' : kpis.rolesProtegidos}
          </div>
          <p className="mt-0.5 text-[11px] text-slate-500">Perfiles base protegidos</p>
        </div>

        <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Catálogo permisos</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-50 text-orange-700 border border-orange-200/60">
              <KeyRound className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 text-xl font-bold tracking-tight text-slate-900">
            {cargando ? '—' : totalPermisosSistema}
          </div>
          <p className="mt-0.5 text-[11px] text-slate-500">{modulos.length} módulos funcionales</p>
        </div>
      </div>

      {/* Alertas de retroalimentación accesible */}
      {aviso && (
        <div
          role="status"
          className={`flex items-center justify-between rounded-xl border px-4 py-3 text-xs font-medium transition-all ${
            aviso.tono === 'ok'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : 'border-red-200 bg-red-50 text-red-800'
          }`}
        >
          <span>{aviso.texto}</span>
          <button
            type="button"
            onClick={() => setAviso(null)}
            className="text-xs underline hover:no-underline ml-3 cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      )}

      {/* Barra de Filtros y Búsqueda */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-1">
        {/* Buscador de roles */}
        <div className="relative flex-1 max-w-sm">
          <Search
            className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
            aria-hidden="true"
          />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar por rol o descripción..."
            className="w-full pl-9 pr-8 py-2 text-xs rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 shadow-2xs transition-colors"
            aria-label="Buscar roles"
          />
          {busqueda && (
            <button
              type="button"
              onClick={() => setBusqueda('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
              aria-label="Limpiar búsqueda"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Segmented control de tipo de rol */}
        <div
          role="radiogroup"
          aria-label="Filtrar roles por tipo"
          className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/80 text-xs font-medium shrink-0"
        >
          <button
            type="button"
            role="radio"
            aria-checked={filtroTipo === 'todos'}
            onClick={() => setFiltroTipo('todos')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              filtroTipo === 'todos'
                ? 'bg-white text-slate-900 font-semibold shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Todos ({roles.length})
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={filtroTipo === 'sistema'}
            onClick={() => setFiltroTipo('sistema')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              filtroTipo === 'sistema'
                ? 'bg-white text-slate-900 font-semibold shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Sistema ({kpis.rolesProtegidos})
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={filtroTipo === 'personalizados'}
            onClick={() => setFiltroTipo('personalizados')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              filtroTipo === 'personalizados'
                ? 'bg-white text-slate-900 font-semibold shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Personalizados ({kpis.rolesPersonalizados})
          </button>
        </div>
      </div>

      {/* Grid de Tarjetas de Roles */}
      {cargando ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-2xl border border-slate-200 bg-white p-5 space-y-3"
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 bg-slate-200 rounded-xl" />
                  <div className="space-y-1">
                    <div className="h-4 w-28 bg-slate-200 rounded" />
                    <div className="h-3 w-16 bg-slate-100 rounded" />
                  </div>
                </div>
                <div className="h-5 w-16 bg-slate-100 rounded-full" />
              </div>
              <div className="h-3 w-full bg-slate-100 rounded mt-2" />
              <div className="h-3 w-4/5 bg-slate-100 rounded" />
              <div className="grid grid-cols-2 gap-2 pt-2">
                <div className="h-7 bg-slate-100 rounded-lg" />
                <div className="h-7 bg-slate-100 rounded-lg" />
              </div>
              <div className="h-9 bg-slate-200 rounded-xl mt-3" />
            </div>
          ))}
        </div>
      ) : rolesFiltrados.length === 0 ? (
        <div className="text-center py-12 px-4 border border-dashed border-slate-200 rounded-2xl bg-white shadow-2xs">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-600 border border-amber-200/60 mb-3">
            <Sparkles className="h-6 w-6" aria-hidden="true" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 mb-1">
            No se encontraron roles coincidentes
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mb-4">
            {busqueda
              ? `No hay ningún rol que contenga el término "${busqueda}" en el filtro seleccionado.`
              : 'No existen roles registrados en esta categoría.'}
          </p>
          {(busqueda || filtroTipo !== 'todos') && (
            <button
              type="button"
              onClick={() => {
                setBusqueda('');
                setFiltroTipo('todos');
              }}
              className="text-xs font-semibold text-amber-700 hover:text-amber-800 bg-amber-50 hover:bg-amber-100/80 px-3.5 py-1.5 rounded-xl border border-amber-200 transition-colors cursor-pointer"
            >
              Restablecer filtros
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {rolesFiltrados.map((rolItem) => (
            <div key={rolItem.id_rol} className="relative">
              <TarjetaRol
                rol={rolItem}
                totalPermisosCatalogo={totalPermisosSistema}
                onConfigurar={abrirMatriz}
                onEditar={(r) => setModalRol({ abierto: true, rol: r })}
              />
              {cargandoDetalleId === rolItem.id_rol && (
                <div className="absolute inset-0 bg-white/75 backdrop-blur-[1px] rounded-2xl flex items-center justify-center z-10 transition-opacity">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-800 bg-white border border-slate-200 shadow-md px-3.5 py-2 rounded-xl">
                    <div className="h-3.5 w-3.5 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
                    <span>Cargando matriz...</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal de Matriz de Permisos */}
      {rolDetalleMatriz && (
        <MatrizPermisosModal
          key={`matriz-${rolDetalleMatriz.id_rol}`}
          rol={rolDetalleMatriz}
          modulos={modulos}
          onCerrar={() => setRolDetalleMatriz(null)}
          onGuardar={guardarMatriz}
          onExito={(msg) => setAviso({ texto: msg, tono: 'ok' })}
          onError={(msg) => setAviso({ texto: msg, tono: 'error' })}
        />
      )}

      {/* Modal de Alta o Edición de Rol */}
      {modalRol.abierto && (
        <ModalRol
          key={`modal-rol-${modalRol.rol?.id_rol ?? 'nuevo'}`}
          rol={modalRol.rol}
          onCerrar={() => setModalRol({ abierto: false, rol: null })}
          onGuardado={() => setRefresco((prev) => prev + 1)}
          onExito={(msg) => setAviso({ texto: msg, tono: 'ok' })}
          onError={(msg) => setAviso({ texto: msg, tono: 'error' })}
        />
      )}
    </div>
  );
};

export default RolesTab;
