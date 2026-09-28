import React, { useState } from 'react';
import { Loader2, UserCheck, UserX } from 'lucide-react';
import Modal from '../../components/Modal';
import { CLASE_TEXTAREA } from './estilosFormulario';
import { normalizarErrorApi } from '../../../../services/erroresApi';
import type { UsuarioFila } from '../../../../types/usuarios';

/**
 * Activar / inactivar una cuenta (CU3).
 *
 * POR QUÉ ES UN MODAL Y NO UN BOTÓN DIRECTO
 * Inactivar es la única operación de esta pantalla que **cierra el
 * acceso** de alguien. El backend lo acepta con un `PATCH` de una línea,
 * y por eso mismo es peligroso por clic accidental: un solo clic mal
 * apuntando deja a un vendedor sin poder trabajar hasta que alguien se
 * dé cuenta. El modal obliga a leer.
 *
 * Y de paso da un lugar para escribir el motivo, que va a la bitácora
 * (CU26). El backend lo acepta vacío y escribe "no indicado", pero una
 * razón es justo lo que hace útil la auditoría seis meses después.
 *
 * `desbloquear` NO vive acá aunque también sea un POST corto: no es un
 * cambio de estado de la cuenta, es levantar un bloqueo por intentos
 * fallidos, y el botón solo tiene sentido en una cuenta que
 * `esta_bloqueado` sea `true`. Mezclarlos haría aparecer un botón
 * "desbloquear" en cuentas que no están bloqueadas.
 */

interface ModalEstadoProps {
  usuario: UsuarioFila;
  onCerrar: () => void;
  onConfirmar: (motivo: string) => Promise<UsuarioFila>;
  onError: (mensaje: string) => void;
  onExito: (mensaje: string) => void;
}

export const ModalEstado: React.FC<ModalEstadoProps> = ({
  usuario,
  onCerrar,
  onConfirmar,
  onError,
  onExito,
}) => {
  const vaActivar = !usuario.activo;
  const [motivo, setMotivo] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  // Sin `useEffect` que vacíe el motivo al cambiar de cuenta: el padre
  // monta este modal con `key={id_usuario}`, así que cada cuenta recibe
  // una instancia nueva con el formulario en blanco. Con un efecto, el
  // modal se pinta primero con el motivo de la cuenta anterior y un tick
  // después se limpia. `UsuariosPage` es quien pone esa `key`.

  const confirmar = async () => {
    if (guardando) return;
    setGuardando(true);
    setError(null);

    try {
      const fila = await onConfirmar(motivo.trim());
      onExito(
        vaActivar
          ? `La cuenta "${fila.nombre_usuario}" quedó activa.`
          : `La cuenta "${fila.nombre_usuario}" quedó inactiva.`
      );
      onCerrar();
    } catch (fallo) {
      const normalizado = normalizarErrorApi(fallo);
      setError(normalizado.mensaje ?? 'No se pudo cambiar el estado de la cuenta.');
      onError(normalizado.mensaje ?? 'No se pudo cambiar el estado de la cuenta.');
    } finally {
      setGuardando(false);
    }
  };

  const Icono = vaActivar ? UserCheck : UserX;

  return (
    <Modal
      ancho="sm"
      titulo={vaActivar ? 'Activar cuenta' : 'Inactivar cuenta'}
      subtitulo={`@${usuario.nombre_usuario} · ${usuario.nombre_completo}`}
      onCerrar={onCerrar}
      pie={
        <>
          <button
            type="button"
            onClick={onCerrar}
            disabled={guardando}
            className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:opacity-60 cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={confirmar}
            disabled={guardando}
            className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer ${
              vaActivar
                ? 'bg-emerald-600 hover:bg-emerald-700 focus-visible:ring-emerald-600'
                : 'bg-red-600 hover:bg-red-700 focus-visible:ring-red-600'
            }`}
          >
            {guardando ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Icono className="h-4 w-4" aria-hidden="true" />
            )}
            {guardando ? 'Procesando...' : vaActivar ? 'Activar cuenta' : 'Inactivar cuenta'}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        {error && (
          <div
            role="alert"
            className="rounded-xl border border-red-200 bg-red-50 px-4 py-3"
          >
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}

        <div
          className={`flex gap-3 rounded-xl border px-4 py-3 ${
            vaActivar
              ? 'border-emerald-200 bg-emerald-50'
              : 'border-red-200 bg-red-50'
          }`}
        >
          <Icono
            className={`mt-0.5 h-4 w-4 shrink-0 ${
              vaActivar ? 'text-emerald-600' : 'text-red-600'
            }`}
            aria-hidden="true"
          />
          <p className="text-xs leading-relaxed text-slate-700">
            {vaActivar ? (
              <>
                <strong className="font-semibold">{usuario.nombre_completo}</strong> podrá volver
                a iniciar sesión con su contraseña actual.
              </>
            ) : (
              <>
                <strong className="font-semibold">{usuario.nombre_completo}</strong> no podrá
                iniciar sesión. Su historial de ventas y producción se conserva intacto: la
                cuenta se marca, no se borra. También se cerrarán las sesiones que tenga
                abiertas ahora mismo.
              </>
            )}
          </p>
        </div>

        <div>
          <label
            htmlFor="motivo-cambio-estado"
            className="mb-1.5 block text-xs font-semibold text-slate-700"
          >
            Motivo
          </label>
          <textarea
            id="motivo-cambio-estado"
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            disabled={guardando}
            rows={2}
            placeholder={
              vaActivar
                ? 'Reincorporación del personal'
                : 'Renuncia del empleado, cuenta en desuso'
            }
            aria-describedby="ayuda-motivo"
            className={CLASE_TEXTAREA}
          />
          <p id="ayuda-motivo" className="mt-1.5 text-[11px] text-slate-500">
            Opcional. Se guarda en la bitácora para que quede por qué se cambió el estado.
          </p>
        </div>
      </div>
    </Modal>
  );
};

export default ModalEstado;
