import React, { useRef, useState } from 'react';
import { KeyRound, Loader2 } from 'lucide-react';
import Modal from '../../components/Modal';
import CampoFormulario from './CampoFormulario';
import { claseInput } from './estilosFormulario';
import PasswordRequirements from '../../../auth/components/PasswordRequirements';
import { normalizarErrorApi } from '../../../../services/erroresApi';
import type { UsuarioFila } from '../../../../types/usuarios';

/**
 * Restablecimiento administrativo de contraseña (extensión del CU3).
 *
 * POR QUÉ PIDE LA CONTRASEÑA DOS VECES
 * El backend lo exige (`confirmar_contrasena` es `required`) y la razón
 * está escrita en su serializer: en un formulario de Administrador la
 * clave se teclea con prisa y sin que nadie esté mirando, y un error de
 * dedo en un campo que no se relee deja la cuenta inaccesible hasta el
 * siguiente ciclo de recuperación. Confirmar convierte un error de un
 * segundo en un inconveniente de treinta segundos.
 *
 * ESTO ES UNA EXTENSIÓN, NO EL NÚCLEO DEL CU3
 * `PACKAGE_CU_MAP.md` define CU3 como "registro, edición, activación e
 * inactivación". Este modal implementa `cambiarContrasena()` del
 * diagrama de clases, que es la contraparte del CU2 vista desde el
 * Administrador. Que la frontera esté escrita acá es lo que permite que
 * una revisión vea qué es el caso de uso y qué es administración de
 * cuentas.
 *
 * AVISO QUE HAY QUE DAR SIEMPRE
 * Al confirmar, el backend revoca TODAS las sesiones abiertas de esa
 * cuenta. La persona queda desconectada de golpe y hay que avisarla
 * antes de que pulse el botón, no después.
 */

interface ModalRestablecerContrasenaProps {
  usuario: UsuarioFila;
  onCerrar: () => void;
  onConfirmar: (nueva: string, confirmacion: string) => Promise<string>;
  onError: (mensaje: string) => void;
  onExito: (mensaje: string) => void;
}

export const ModalRestablecerContrasena: React.FC<
  ModalRestablecerContrasenaProps
> = ({ usuario, onCerrar, onConfirmar, onError, onExito }) => {
  const [nueva, setNueva] = useState('');
  const [repeticion, setRepeticion] = useState('');
  const [error, setError] = useState<{ mensaje: string | null; campos: Record<string, string[]> }>({
    mensaje: null,
    campos: {},
  });
  const [enviando, setEnviando] = useState(false);
  const resumenRef = useRef<HTMLDivElement>(null);

  // Sin `useEffect` que reinicie el formulario cuando cambia el usuario.
  // El padre monta este modal con `key={id_usuario}`, así que cambiar de
  // cuenta produce un componente NUEVO con el estado ya en cero. Hacerlo
  // con un efecto son dos renders extra y un parpadeo: primero se pinta el
  // modal con los valores de la cuenta anterior y un tick después se
  // borran. `UsuariosPage` es quien pone esa `key`.

  // La diferencia entre los dos campos se comprueba acá, no esperando al
  // servidor. Es la validación más barata que existe y la única que
  // puede dar feedback sin red. El backend la vuelve a hacer igual, que
  // no está mal: el navegador no es una frontera de seguridad.
  const noCoinciden = repeticion.length > 0 && nueva !== repeticion;

  const textoDe = (campo: string): string | undefined => {
    const errores = error.campos[campo];
    return errores?.length ? errores.join(' ') : undefined;
  };

  const confirmar = async (evento: React.FormEvent) => {
    evento.preventDefault();
    if (enviando) return;

    if (noCoinciden) {
      setError({
        mensaje: 'Las dos contraseñas no coinciden.',
        campos: { confirmar_contrasena: ['Las dos contraseñas no coinciden.'] },
      });
      return;
    }

    setEnviando(true);
    setError({ mensaje: null, campos: {} });

    try {
      const mensaje = await onConfirmar(nueva, repeticion);
      onExito(mensaje);
      onCerrar();
    } catch (fallo) {
      const normalizado = normalizarErrorApi(fallo);
      setError({ mensaje: normalizado.mensaje, campos: normalizado.campos });
      window.setTimeout(() => resumenRef.current?.focus(), 0);
      onError(normalizado.mensaje ?? 'No se pudo restablecer la contraseña.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Modal
      titulo="Restablecer contraseña"
      subtitulo={`@${usuario.nombre_usuario} · ${usuario.nombre_completo}`}
      onCerrar={onCerrar}
      pie={
        <>
          <button
            type="button"
            onClick={onCerrar}
            disabled={enviando}
            className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:opacity-60 cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="submit"
            form="formulario-reset"
            disabled={enviando}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-amber-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
          >
            {enviando ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <KeyRound className="h-4 w-4" aria-hidden="true" />
            )}
            {enviando ? 'Restableciendo...' : 'Restablecer contraseña'}
          </button>
        </>
      }
    >
      <form id="formulario-reset" onSubmit={confirmar} noValidate className="space-y-4">
        {error.mensaje && (
          <div
            ref={resumenRef}
            tabIndex={-1}
            role="alert"
            className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
          >
            <p className="text-xs font-bold text-red-800">No se pudo restablecer</p>
            <p className="mt-1 text-xs text-red-700">{error.mensaje}</p>
          </div>
        )}

        <div className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
          <KeyRound className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" aria-hidden="true" />
          <p className="text-xs leading-relaxed text-slate-700">
            Al restablecer la contraseña se cerrarán{' '}
            <strong className="font-semibold">todas las sesiones abiertas</strong> de{' '}
            {usuario.nombre_completo}. Avísele para que no se entere a la mitad de un turno.
            {usuario.esta_bloqueado && (
              <>
                {' '}
                <strong className="font-semibold">
                  La cuenta está bloqueada por intentos fallidos
                </strong>{' '}
                y este restablecimiento también levanta ese bloqueo.
              </>
            )}
          </p>
        </div>

        <CampoFormulario
          etiqueta="Nueva contraseña"
          requerido
          error={textoDe('nueva_contrasena') ?? textoDe('contrasena')}
        >
          {(props) => (
            <input
              {...props}
              type="password"
              value={nueva}
              onChange={(e) => {
                setNueva(e.target.value);
                setError((previo) => ({ ...previo, mensaje: null }));
              }}
              disabled={enviando}
              autoComplete="new-password"
              autoFocus
              className={claseInput(Boolean(props['aria-invalid']))}
            />
          )}
        </CampoFormulario>

        <PasswordRequirements contrasena={nueva} />

        <CampoFormulario
          etiqueta="Repetir la contraseña"
          requerido
          error={noCoinciden ? 'Las dos contraseñas no coinciden.' : textoDe('confirmar_contrasena')}
        >
          {(props) => (
            <input
              {...props}
              type="password"
              value={repeticion}
              onChange={(e) => {
                setRepeticion(e.target.value);
                setError((previo) => ({ ...previo, mensaje: null }));
              }}
              disabled={enviando}
              autoComplete="new-password"
              className={claseInput(noCoinciden || Boolean(props['aria-invalid']))}
            />
          )}
        </CampoFormulario>
      </form>
    </Modal>
  );
};

export default ModalRestablecerContrasena;
