import React, { useId, useMemo, useState } from 'react';
import {
  AlertTriangle,
  BarChart3,
  CheckSquare,
  Lock,
  Package,
  Receipt,
  Search,
  ShieldCheck,
  ShoppingCart,
  Square,
  X,
} from 'lucide-react';
import { Modal } from '../../components/Modal';
import type { GrupoModuloPermisos, RolDetalle } from '../../../../types/roles';
import { estilosRoles } from './estilosRoles';

interface MatrizPermisosModalProps {
  rol: RolDetalle;
  modulos: GrupoModuloPermisos[];
  onCerrar: () => void;
  onGuardar: (permisosIds: number[]) => Promise<void>;
  onExito: (mensaje: string) => void;
  onError: (mensaje: string) => void;
}

interface ModuloConfig {
  icono: React.ElementType;
  colorBadge: string;
  colorIcono: string;
}

const CONFIG_MODULOS: Record<string, ModuloConfig> = {
  usuarios_seguridad: {
    icono: ShieldCheck,
    colorBadge: 'bg-amber-100/70 text-amber-800 border-amber-200',
    colorIcono: 'text-amber-700',
  },
  productos_inventario: {
    icono: Package,
    colorBadge: 'bg-orange-100/70 text-orange-800 border-orange-200',
    colorIcono: 'text-orange-700',
  },
  compras: {
    icono: ShoppingCart,
    colorBadge: 'bg-sky-100/70 text-sky-800 border-sky-200',
    colorIcono: 'text-sky-700',
  },
  comercializacion: {
    icono: Receipt,
    colorBadge: 'bg-emerald-100/70 text-emerald-800 border-emerald-200',
    colorIcono: 'text-emerald-700',
  },
  reportes: {
    icono: BarChart3,
    colorBadge: 'bg-purple-100/70 text-purple-800 border-purple-200',
    colorIcono: 'text-purple-700',
  },
};

export const MatrizPermisosModal: React.FC<MatrizPermisosModalProps> = ({
  rol,
  modulos,
  onCerrar,
  onGuardar,
  onExito,
  onError,
}) => {
  const modalId = useId();

  // Conjunto inicial de IDs asignados
  const idsIniciales = useMemo(
    () => new Set(rol.permisos.map((p) => p.id_permiso)),
    [rol.permisos]
  );

  const [seleccionados, setSeleccionados] = useState<Set<number>>(
    () => new Set(idsIniciales)
  );
  const [busqueda, setBusqueda] = useState('');
  const [guardando, setGuardando] = useState(false);

  // Rol Administrador tiene guarda obligatoria para 'asignar_permisos'
  const esAdmin = rol.nombre === 'Administrador';

  // Buscar el id_permiso del permiso 'asignar_permisos'
  const permisoAsignarId = useMemo(() => {
    for (const mod of modulos) {
      const p = mod.permisos.find((item) => item.nombre === 'asignar_permisos');
      if (p) return p.id_permiso;
    }
    return null;
  }, [modulos]);

  const esPermisoBloqueado = (permisoId: number): boolean => {
    return esAdmin && permisoId === permisoAsignarId;
  };

  const alternarPermiso = (id: number) => {
    if (esPermisoBloqueado(id)) return;

    setSeleccionados((prev) => {
      const siguiente = new Set(prev);
      if (siguiente.has(id)) {
        siguiente.delete(id);
      } else {
        siguiente.add(id);
      }
      return siguiente;
    });
  };

  // Acciones globales
  const seleccionarTodos = () => {
    const todosLosIds = new Set<number>();
    for (const mod of modulos) {
      for (const p of mod.permisos) {
        todosLosIds.add(p.id_permiso);
      }
    }
    setSeleccionados(todosLosIds);
  };

  const deseleccionarTodos = () => {
    const minSeleccionados = new Set<number>();
    if (esAdmin && permisoAsignarId !== null) {
      minSeleccionados.add(permisoAsignarId);
    }
    setSeleccionados(minSeleccionados);
  };

  // Acciones por módulo
  const marcarModulo = (moduloSlug: string) => {
    const grupo = modulos.find((m) => m.modulo === moduloSlug);
    if (!grupo) return;
    setSeleccionados((prev) => {
      const siguiente = new Set(prev);
      for (const p of grupo.permisos) {
        siguiente.add(p.id_permiso);
      }
      return siguiente;
    });
  };

  const desmarcarModulo = (moduloSlug: string) => {
    const grupo = modulos.find((m) => m.modulo === moduloSlug);
    if (!grupo) return;
    setSeleccionados((prev) => {
      const siguiente = new Set(prev);
      for (const p of grupo.permisos) {
        if (!esPermisoBloqueado(p.id_permiso)) {
          siguiente.delete(p.id_permiso);
        }
      }
      return siguiente;
    });
  };

  // Cálculo de cambios respecto al inicio
  const cambiosPendientes = useMemo(() => {
    let agregados = 0;
    let quitados = 0;

    for (const id of seleccionados) {
      if (!idsIniciales.has(id)) agregados++;
    }
    for (const id of idsIniciales) {
      if (!seleccionados.has(id)) quitados++;
    }

    return { agregados, quitados, total: agregados + quitados };
  }, [seleccionados, idsIniciales]);

  // Filtrado de permisos por texto
  const modulosFiltrados = useMemo(() => {
    const termino = busqueda.trim().toLowerCase();
    if (!termino) return modulos;

    return modulos
      .map((grupo) => {
        const permisosCoincidentes = grupo.permisos.filter(
          (p) =>
            p.nombre.toLowerCase().includes(termino) ||
            p.descripcion.toLowerCase().includes(termino)
        );
        return {
          ...grupo,
          permisos: permisosCoincidentes,
        };
      })
      .filter((grupo) => grupo.permisos.length > 0);
  }, [modulos, busqueda]);

  const totalPermisosGlobal = useMemo(
    () => modulos.reduce((acc, m) => acc + m.permisos.length, 0),
    [modulos]
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGuardando(true);
    try {
      await onGuardar(Array.from(seleccionados));
      onExito(`Matriz de permisos actualizada exitosamente para el rol "${rol.nombre}".`);
      onCerrar();
    } catch (err: unknown) {
      const mensaje =
        err instanceof Error ? err.message : 'No se pudo guardar la matriz de permisos.';
      onError(mensaje);
    } finally {
      setGuardando(false);
    }
  };

  const pieModal = (
    <div className="flex flex-col-reverse sm:flex-row items-center justify-between gap-3 w-full">
      <div className="flex items-center gap-3 text-xs text-slate-600 font-medium">
        <span>
          <strong className="text-slate-900 font-semibold">{seleccionados.size}</strong> de{' '}
          {totalPermisosGlobal} permisos activos
        </span>

        {cambiosPendientes.total > 0 && (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
            {cambiosPendientes.total === 1
              ? '1 cambio sin guardar'
              : `${cambiosPendientes.total} cambios sin guardar`}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 w-full sm:w-auto">
        <button
          type="button"
          onClick={onCerrar}
          disabled={guardando}
          className="flex-1 sm:flex-initial min-h-10 px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 cursor-pointer disabled:opacity-50"
        >
          Cancelar
        </button>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={guardando || cambiosPendientes.total === 0}
          className="flex-1 sm:flex-initial min-h-10 px-5 py-2 text-xs font-semibold text-white bg-amber-600 rounded-xl shadow-xs hover:bg-amber-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {guardando && (
            <div
              className="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"
              aria-hidden="true"
            />
          )}
          <span>{guardando ? 'Guardando...' : 'Guardar matriz'}</span>
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      titulo={`Matriz de permisos — ${rol.nombre}`}
      subtitulo="Configura las autorizaciones por módulo que poseen los usuarios asignados a este perfil."
      ancho="xl"
      onCerrar={onCerrar}
      pie={pieModal}
    >
      <div className="space-y-4">
        {/* Aviso de seguridad para Administrador */}
        {esAdmin && (
          <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50/80 p-3.5 text-xs text-amber-900 leading-relaxed shadow-2xs">
            <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <strong className="font-semibold text-amber-950">Guarda de auto-bloqueo:</strong>{' '}
              El rol Administrador debe conservar obligatoriamente el permiso{' '}
              <code className="bg-amber-100/90 px-1 py-0.5 rounded font-mono text-[11px] text-amber-950 font-bold border border-amber-300/50">
                asignar_permisos
              </code>{' '}
              para garantizar que el sistema siempre cuente con al menos un perfil habilitado para gobernar la seguridad.
            </div>
          </div>
        )}

        {/* Buscador de permisos y acciones globales */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-slate-200/80">
          {/* Buscador interactivo */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" aria-hidden="true" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Filtrar por nombre o descripción..."
              className="w-full pl-8.5 pr-8 py-1.5 text-xs rounded-xl border border-slate-200 bg-slate-50/60 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-colors"
              aria-label="Buscar permiso en la matriz"
            />
            {busqueda && (
              <button
                type="button"
                onClick={() => setBusqueda('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
                aria-label="Limpiar búsqueda"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* Botones de selección rápida global */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={seleccionarTodos}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <CheckSquare className="h-3.5 w-3.5 text-amber-600" aria-hidden="true" />
              <span>Marcar todos</span>
            </button>
            <button
              type="button"
              onClick={deseleccionarTodos}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <Square className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
              <span>Desmarcar todos</span>
            </button>
          </div>
        </div>

        {/* Mensaje de búsqueda sin resultados */}
        {modulosFiltrados.length === 0 && (
          <div className="text-center py-8 px-4 border border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
            <p className="text-xs font-medium text-slate-600 mb-2">
              No se encontraron permisos que coincidan con &ldquo;{busqueda}&rdquo;.
            </p>
            <button
              type="button"
              onClick={() => setBusqueda('')}
              className="text-xs font-semibold text-amber-700 hover:text-amber-800 underline cursor-pointer"
            >
              Restablecer filtro de búsqueda
            </button>
          </div>
        )}

        {/* Secciones por Módulo del Sistema */}
        <div className="space-y-4">
          {modulosFiltrados.map((grupo) => {
            const config = CONFIG_MODULOS[grupo.modulo] || {
              icono: ShieldCheck,
              colorBadge: 'bg-slate-100 text-slate-800 border-slate-200',
              colorIcono: 'text-slate-600',
            };
            const IconoModulo = config.icono;

            const todosEnModulo = grupo.permisos.length;
            const activosEnModulo = grupo.permisos.filter((p) =>
              seleccionados.has(p.id_permiso)
            ).length;
            const todosActivos = todosEnModulo > 0 && activosEnModulo === todosEnModulo;

            return (
              <section
                key={grupo.modulo}
                className={estilosRoles.seccionModulo}
                aria-labelledby={`modulo-${grupo.modulo}-${modalId}`}
              >
                {/* Cabecera del módulo con acciones por lote */}
                <div className={estilosRoles.seccionModuloHeader}>
                  <div className="flex items-center gap-2 min-w-0">
                    <IconoModulo className={`h-4 w-4 ${config.colorIcono} shrink-0`} aria-hidden="true" />
                    <h3
                      id={`modulo-${grupo.modulo}-${modalId}`}
                      className={estilosRoles.seccionModuloTitulo}
                    >
                      <span>{grupo.modulo_display}</span>
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[11px] font-semibold border px-2 py-0.5 rounded-full ${
                        todosActivos
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                          : 'bg-white text-slate-600 border-slate-200'
                      }`}
                    >
                      {activosEnModulo} de {todosEnModulo} activos
                    </span>

                    {/* Botón rápido para este módulo */}
                    <button
                      type="button"
                      onClick={() =>
                        todosActivos ? desmarcarModulo(grupo.modulo) : marcarModulo(grupo.modulo)
                      }
                      className="text-[11px] font-medium text-slate-600 hover:text-amber-800 bg-white border border-slate-200 hover:border-amber-300 px-2 py-0.5 rounded-lg transition-colors cursor-pointer"
                    >
                      {todosActivos ? 'Desmarcar módulo' : 'Marcar módulo'}
                    </button>
                  </div>
                </div>

                {/* Grid de checkboxes de permisos */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {grupo.permisos.map((p) => {
                    const estaSeleccionado = seleccionados.has(p.id_permiso);
                    const estaBloqueado = esPermisoBloqueado(p.id_permiso);
                    const inputId = `permiso-${p.id_permiso}-${modalId}`;

                    return (
                      <label
                        key={p.id_permiso}
                        htmlFor={inputId}
                        className={`${estilosRoles.itemPermiso} ${
                          estaBloqueado
                            ? 'opacity-85 bg-slate-100/60 cursor-not-allowed'
                            : 'cursor-pointer'
                        }`}
                      >
                        <input
                          id={inputId}
                          type="checkbox"
                          checked={estaSeleccionado}
                          disabled={estaBloqueado}
                          onChange={() => alternarPermiso(p.id_permiso)}
                          className={estilosRoles.checkboxPermiso}
                          aria-describedby={`desc-${p.id_permiso}-${modalId}`}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap mb-1">
                            <span className="text-xs font-semibold text-slate-900 leading-snug">
                              {p.nombre.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                            </span>
                            <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1 py-0.5 rounded border border-slate-200/60">
                              {p.nombre}
                            </span>
                            {estaBloqueado && (
                              <span
                                className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-amber-800 bg-amber-100/90 px-1.5 py-0.5 rounded-full border border-amber-200"
                                title="Permiso protegido de seguridad"
                              >
                                <Lock className="h-2.5 w-2.5 text-amber-700" aria-hidden="true" />
                                Requerido
                              </span>
                            )}
                          </div>
                          <p
                            id={`desc-${p.id_permiso}-${modalId}`}
                            className="text-[11px] text-slate-600 leading-relaxed"
                          >
                            {p.descripcion}
                          </p>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </Modal>
  );
};

export default MatrizPermisosModal;
