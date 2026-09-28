import React from 'react';
import {
  Ban,
  KeyRound,
  Loader2,
  LockOpen,
  Pencil,
  ShieldCheck,
  UserCheck,
} from 'lucide-react';
import UserAvatar from '../../components/UserAvatar';
import type { UsuarioFila } from '../../../../types/usuarios';

/**
 * Tabla de cuentas del Administrador (CU3).
 *
 * POR QUÉ NO HAY COLUMNA DE "BORRAR"
 * El CU3 no tiene borrado. La baja es la inactivación, y por diseño el
 * backend responde 405 a un `DELETE`. Ofrecer un botón que el servidor
 * va a rechazar obliga a la persona a descubrir la regla por un error.
 *
 * POR QUÉ EL ESTADO ES UNA ETIQUETA DE TEXTO Y NO UN INTERRUPTOR
 * Un interruptor implica "esto ya está hecho" al moverlo. Inactivar una
 * cuenta cierra el acceso de alguien y además revoca sus sesiones: es
 * una decisión con consecuencia, no un ajuste. Va como botón, y detrás
 * de un modal que obliga a leer (ver `ModalEstado`).
 *
 * CELDAS QUE NO SE ROMPEN EN MÓVIL
 * La tabla va dentro de un contenedor con scroll horizontal. La regla
 * general "nada desborda en móvil" tiene aquí una excepción legítima:
 * seis columnas de datos no caben en 360 px, y la alternativa —ocultar
 * columnas según el ancho— hace que la persona no vea el estado de la
 * cuenta que está a punto de cambiar. Se prefiere el scroll.
 */

interface UsuariosTablaProps {
  filas: UsuarioFila[];
  cargando: boolean;
  /** Ids con una operación en curso, para deshabilitar solo esa fila. */
  procesandoId: number | null;
  onEditar: (fila: UsuarioFila) => void;
  onCambiarEstado: (fila: UsuarioFila) => void;
  onRestablecer: (fila: UsuarioFila) => void;
  onDesbloquear: (fila: UsuarioFila) => void;
  onNuevo: () => void;
  /** `true` si la fila es la del usuario conectado; no se puede inactivar. */
  esUsuarioActual: (id: number) => boolean;
}

/** Un botón de acción de la fila. 24 px es el mínimo de WCAG 2.2 AA. */
const claseAccion =
  'inline-flex h-9 min-w-9 items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 text-[11px] font-semibold text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-40 cursor-pointer';

export const UsuariosTabla: React.FC<UsuariosTablaProps> = ({
  filas,
  cargando,
  procesandoId,
  onEditar,
  onCambiarEstado,
  onRestablecer,
  onDesbloquear,
  onNuevo,
  esUsuarioActual,
}) => {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <header className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-900">Cuentas del sistema</h2>
          <p className="mt-0.5 text-[11px] text-slate-500">
            {cargando
              ? 'Consultando...'
              : `${filas.length} cuenta${filas.length === 1 ? '' : 's'} en esta página`}
          </p>
        </div>

        <button
          type="button"
          onClick={onNuevo}
          disabled={cargando}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-amber-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
        >
          <UserCheck className="h-4 w-4" aria-hidden="true" />
          Nueva cuenta
        </button>
      </header>

      {cargando ? (
        <EsqueletoTabla />
      ) : filas.length === 0 ? (
        <div className="px-6 py-14 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100">
            <ShieldCheck className="h-6 w-6 text-slate-300" aria-hidden="true" />
          </div>
          <p className="text-sm font-semibold text-slate-700">No hay cuentas que mostrar</p>
          <p className="mx-auto mt-1 max-w-xs text-xs text-slate-500">
            Ninguna cuenta coincide con el buscador o los filtros aplicados.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[56rem] border-collapse text-left">
            <caption className="sr-only">
              Listado de cuentas de usuario con su rol, estado y acciones disponibles
            </caption>

            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70">
                <Th>Usuario</Th>
                <Th>Rol</Th>
                <Th>Estado</Th>
                <Th>Acceso</Th>
                <Th className="text-right">Acciones</Th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {filas.map((fila) => {
                const ocupada = procesandoId === fila.id_usuario;
                const yoSoyEsta = esUsuarioActual(fila.id_usuario);

                return (
                  <tr
                    key={fila.id_usuario}
                    className={`transition-colors hover:bg-slate-50/70 ${
                      !fila.activo ? 'bg-slate-50/40' : ''
                    }`}
                  >
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-3">
                        {/* `UserAvatar` solo pide `nombre_completo` y `rol`, y
                            ambos existen en `UsuarioFila`, así que la fila
                            entera se sirve tal cual sin ensuciarla. */}
                        <UserAvatar usuario={fila} size="sm" />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-900">
                            {fila.nombre_completo || '—'}
                          </p>
                          <p className="truncate font-mono text-[11px] text-slate-500">
                            @{fila.nombre_usuario}
                            {fila.email && (
                              <span className="ml-1 font-sans text-slate-400">
                                · {fila.email}
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                    </td>

                    <td className="px-5 py-3">
                      <span
                        className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-700"
                        title={
                          fila.total_permisos === 1
                            ? '1 permiso asignado'
                            : `${fila.total_permisos} permisos asignados`
                        }
                      >
                        {fila.rol || 'Sin rol'}
                        <span className="font-normal text-slate-400">
                          {fila.total_permisos}
                        </span>
                      </span>
                    </td>

                    <td className="px-5 py-3">
                      <Etiqueta
                        tono={fila.activo ? 'verde' : 'gris'}
                        texto={fila.activo ? 'Activo' : 'Inactivo'}
                      />
                    </td>

                    <td className="px-5 py-3">
                      {fila.esta_bloqueado ? (
                        <span
                          className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-red-200 bg-red-50 px-2.5 py-1 text-[11px] font-semibold text-red-700"
                          title={`Bloqueada por intentos fallidos. Faltan ${fila.minutos_bloqueo_restantes} minuto(s).`}
                        >
                          <LockOpen className="h-3 w-3" aria-hidden="true" />
                          Bloqueada
                          {fila.minutos_bloqueo_restantes > 0 && (
                            <span className="font-normal">
                              {fila.minutos_bloqueo_restantes} min
                            </span>
                          )}
                        </span>
                      ) : (
                        <Etiqueta tono="neutro" texto="Normal" />
                      )}
                    </td>

                    <td className="px-5 py-3">
                      <div className="flex items-center justify-end gap-2">
                        {ocupada && (
                          <Loader2
                            className="h-4 w-4 animate-spin text-slate-400"
                            aria-label="Procesando"
                          />
                        )}

                        <button
                          type="button"
                          onClick={() => onEditar(fila)}
                          disabled={ocupada}
                          className={claseAccion}
                          title={`Editar ${fila.nombre_usuario}`}
                        >
                          <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
                          Editar
                        </button>

                        {fila.esta_bloqueado && (
                          <button
                            type="button"
                            onClick={() => onDesbloquear(fila)}
                            disabled={ocupada}
                            className={claseAccion}
                            title={`Desbloquear ${fila.nombre_usuario}`}
                          >
                            <LockOpen className="h-3.5 w-3.5" aria-hidden="true" />
                            Desbloquear
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={() => onRestablecer(fila)}
                          disabled={ocupada}
                          className={claseAccion}
                          title={`Restablecer contraseña de ${fila.nombre_usuario}`}
                        >
                          <KeyRound className="h-3.5 w-3.5" aria-hidden="true" />
                          Clave
                        </button>

                        <button
                          type="button"
                          onClick={() => onCambiarEstado(fila)}
                          disabled={ocupada || yoSoyEsta}
                          className={claseAccion}
                          title={
                            yoSoyEsta
                              ? 'No puede inactivar su propia cuenta'
                              : fila.activo
                                ? `Inactivar ${fila.nombre_usuario}`
                                : `Activar ${fila.nombre_usuario}`
                          }
                        >
                          {fila.activo ? (
                            <Ban className="h-3.5 w-3.5" aria-hidden="true" />
                          ) : (
                            <UserCheck className="h-3.5 w-3.5" aria-hidden="true" />
                          )}
                          {fila.activo ? 'Inactivar' : 'Activar'}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const Th: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <th
    scope="col"
    className={`px-5 py-2.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 ${className}`}
  >
    {children}
  </th>
);

/**
 * Etiqueta de estado.
 *
 * El texto va SIEMPRE junto al color. Un punto verde solo no dice
 * "activo" a quien no distingue el verde del rojo, y en un panel donde el
 * rojo significa "cerrado el acceso" ese es el dato más importante de
 * la fila.
 */
const Etiqueta: React.FC<{ tono: 'verde' | 'gris' | 'neutro'; texto: string }> = ({
  tono,
  texto,
}) => {
  const clases = {
    verde: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    gris: 'border-slate-200 bg-slate-100 text-slate-500',
    neutro: 'border-slate-200 bg-white text-slate-400',
  }[tono];

  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-lg border px-2.5 py-1 text-[11px] font-semibold ${clases}`}
    >
      {texto}
    </span>
  );
};

/**
 * Esqueleto de carga.
 *
 * Pinta la forma de la tabla en vez de un spinner en el centro. El
 * contenido no salta de sitio cuando llegan los datos, que es lo que
 * hace un spinner: la página se recoloca y la persona pierde de vista
 * la fila que estaba leyendo.
 */
const EsqueletoTabla: React.FC = () => (
  <div className="divide-y divide-slate-100" aria-busy="true" aria-live="polite">
    <span className="sr-only">Cargando listado de usuarios...</span>
    {Array.from({ length: 5 }, (_, indice) => (
      <div key={indice} className="flex items-center gap-4 px-5 py-4">
        <div className="h-9 w-9 shrink-0 animate-pulse rounded-full bg-slate-100" />
        <div className="flex-1 space-y-2">
          <div className="h-3 w-1/3 animate-pulse rounded bg-slate-100" />
          <div className="h-2.5 w-1/4 animate-pulse rounded bg-slate-100" />
        </div>
        <div className="h-6 w-20 animate-pulse rounded-lg bg-slate-100" />
        <div className="h-6 w-16 animate-pulse rounded-lg bg-slate-100" />
      </div>
    ))}
  </div>
);

export default UsuariosTabla;
