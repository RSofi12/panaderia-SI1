import React, { useRef, useState } from 'react';
import { Loader2, Save } from 'lucide-react';
import Modal from '../../components/Modal';
import CampoFormulario from './CampoFormulario';
import { claseInput } from './estilosFormulario';
import PasswordRequirements from '../../../auth/components/PasswordRequirements';
import { normalizarErrorApi } from '../../../../services/erroresApi';
import type {
  AltaUsuario,
  EditarUsuario,
  ErrorNormalizado,
  RolSimple,
  UsuarioFila,
} from '../../../../types/usuarios';

/**
 * Alta y edición de una cuenta (CU3).
 *
 * UN MISMO MODAL PARA LAS DOS OPERACIONES, Y POR QUÉ
 * Los campos son los mismos, las validaciones del backend son las
 * mismas, y la forma de la respuesta también. Duplicar el formulario
 * en dos archivos garantiza que el día que se agrega un campo al alta
 * (digamos `telefono`) se olvide en la edición, y el síntoma es un
 * campo que existe en un formulario y no en el otro sin explicación
 * posible para quien use la pantalla.
 *
 * Lo que cambia entre alta y edición se decide explícitamente y en un
 * solo lugar, `esEdicion`, en vez de inferirse de si viene `usuario`.
 *
 * POR QUÉ LA CONTRASEÑA SOLO SE PIDE EN EL ALTA
 * El backend tiene un endpoint aparte, `restablecer-contrasena`, con su
 * propia auditoría y su propio efecto colateral: revoca las sesiones
 * abiertas de esa cuenta. Meter la contraseña en el PATCH de edición
 * permitiría cambiar una clave sin que quedara registro de por qué, y
 * la respuesta de esa operación llega en un modal distinto.
 */

interface ModalUsuarioProps {
  /** `null` = alta. Con objeto = edición. */
  usuario: UsuarioFila | null;
  roles: RolSimple[];
  onCerrar: () => void;
  onGuardado: (fila: UsuarioFila) => void;
  onError: (mensaje: string) => void;
  onExito: (mensaje: string) => void;
  crear: (datos: AltaUsuario) => Promise<UsuarioFila>;
  editar: (id: number, datos: EditarUsuario) => Promise<UsuarioFila>;
}

const CAMPOS_VACIOS = {
  nombre_usuario: '',
  nombre_completo: '',
  email: '',
  password: '',
  activo: true,
  id_rol: '',
};

export const ModalUsuario: React.FC<ModalUsuarioProps> = ({
  usuario,
  roles,
  onCerrar,
  onGuardado,
  onError,
  onExito,
  crear,
  editar,
}) => {
  const esEdicion = usuario !== null;

  // El formulario se arma UNA vez, al montar, con un inicializador perezoso
  // en vez de un `useEffect`. El padre pasa `key={id_usuario ?? 'nuevo'}`,
  // así que cambiar de cuenta monta un componente nuevo con los valores
  // de esa cuenta. Con un efecto se vería el modal del usuario anterior
  // durante un tick antes de corregir los campos.
  const [form, setForm] = useState(() => {
    if (!usuario) return CAMPOS_VACIOS;
    return {
      nombre_usuario: usuario.nombre_usuario,
      nombre_completo: usuario.nombre_completo,
      email: usuario.email ?? '',
      password: '',
      activo: usuario.activo,
      id_rol: usuario.id_rol === null ? '' : String(usuario.id_rol),
    };
  });

  const [error, setError] = useState<ErrorNormalizado>({ mensaje: null, campos: {} });
  const [guardando, setGuardando] = useState(false);
  // El `alto` del formulario es un div, no un input: se le puede dar
  // foco para que el lector de pantalla salte al error apenas se
  // anuncia. Por eso el ref.
  const resumenRef = useRef<HTMLDivElement>(null);

  const cambiar = (campo: string, valor: string | boolean) => {
    setForm((previo) => ({ ...previo, [campo]: valor }));
    // Escribir borra el error de ese campo. Dejarlo rojo mientras se
    // corrige hace que la pantalla parezca no responder.
    setError((previo) => {
      if (!previo.campos[campo]) return previo;
      const campos = { ...previo.campos };
      delete campos[campo];
      return { ...previo, campos, mensaje: null };
    });
  };

  const errorDe = (campo: string): string | undefined => previoATexto(error.campos[campo]);

  const enviar = async (evento: React.FormEvent) => {
    evento.preventDefault();
    if (guardando) return;

    setGuardando(true);
    setError({ mensaje: null, campos: {} });

    try {
      const idRol = form.id_rol === '' ? null : Number(form.id_rol);

      const fila = esEdicion
        ? await editar(usuario.id_usuario, {
            nombre_usuario: form.nombre_usuario.trim(),
            nombre_completo: form.nombre_completo.trim(),
            email: form.email.trim(),
            id_rol: idRol as number,
            activo: form.activo,
          })
        : await crear({
            nombre_usuario: form.nombre_usuario.trim(),
            nombre_completo: form.nombre_completo.trim(),
            email: form.email.trim(),
            password: form.password,
            id_rol: idRol as number,
            activo: form.activo,
          });

      onGuardado(fila);
      onExito(
        esEdicion
          ? `Los datos de "${fila.nombre_usuario}" quedaron actualizados.`
          : `La cuenta "${fila.nombre_usuario}" fue creada.`
      );
      onCerrar();
    } catch (fallo) {
      const normalizado = normalizarErrorApi(fallo);
      setError(normalizado);
      // Enfocar el resumen del error es lo que hace que alguien que
      // navega con teclado o con lector de pantalla se entere de que
      // algo falló sin tener que recorrer el formulario buscándolo.
      // Con `setTimeout` porque en este render el div todavía no existe.
      window.setTimeout(() => resumenRef.current?.focus(), 0);
      onError(normalizado.mensaje ?? 'No se pudo guardar la cuenta.');
    } finally {
      setGuardando(false);
    }
  };

  const botonEnviar = (
    <button
      type="submit"
      form="formulario-usuario"
      disabled={guardando}
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-amber-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
    >
      {guardando ? (
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      ) : (
        <Save className="h-4 w-4" aria-hidden="true" />
      )}
      {guardando ? 'Guardando...' : esEdicion ? 'Guardar cambios' : 'Crear cuenta'}
    </button>
  );

  return (
    <Modal
      titulo={esEdicion ? `Editar ${usuario.nombre_usuario}` : 'Nueva cuenta de usuario'}
      subtitulo={
        esEdicion
          ? 'Los cambios quedan registrados en la bitácora (CU26).'
          : 'La contraseña se fija ahora y no se vuelve a mostrar.'
      }
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
          {botonEnviar}
        </>
      }
    >
      <form id="formulario-usuario" onSubmit={enviar} noValidate className="space-y-4">
        {error.mensaje && (
          <div
            ref={resumenRef}
            tabIndex={-1}
            role="alert"
            className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
          >
            <p className="text-xs font-bold text-red-800">No se pudo guardar</p>
            <p className="mt-1 text-xs text-red-700">{error.mensaje}</p>
          </div>
        )}

        <CampoFormulario
          etiqueta="Nombre de usuario"
          requerido
          error={errorDe('nombre_usuario')}
          ayuda="Con este nombre inicia sesión la persona. No se distinguen mayúsculas de minúsculas."
        >
          {(props) => (
            <input
              {...props}
              type="text"
              value={form.nombre_usuario}
              onChange={(e) => cambiar('nombre_usuario', e.target.value)}
              disabled={guardando}
              autoComplete="off"
              placeholder="mgonzales"
              className={claseInput(Boolean(props['aria-invalid']))}
            />
          )}
        </CampoFormulario>

        <CampoFormulario
          etiqueta="Nombre completo"
          requerido
          error={errorDe('nombre_completo')}
        >
          {(props) => (
            <input
              {...props}
              type="text"
              value={form.nombre_completo}
              onChange={(e) => cambiar('nombre_completo', e.target.value)}
              disabled={guardando}
              autoComplete="off"
              placeholder="María Gonzales Rivera"
              className={claseInput(Boolean(props['aria-invalid']))}
            />
          )}
        </CampoFormulario>

        <CampoFormulario
          etiqueta="Correo electrónico"
          error={errorDe('email')}
          ayuda="Opcional. Sirve para que la persona recupere su contraseña."
        >
          {(props) => (
            <input
              {...props}
              type="email"
              value={form.email}
              onChange={(e) => cambiar('email', e.target.value)}
              disabled={guardando}
              autoComplete="off"
              placeholder="maria@panaderiasantiago.com"
              className={claseInput(Boolean(props['aria-invalid']))}
            />
          )}
        </CampoFormulario>

        <CampoFormulario
          etiqueta="Rol"
          requerido
          error={errorDe('id_rol')}
          ayuda="Determina a qué módulos del panel puede entrar la persona."
        >
          {(props) => (
            <select
              {...props}
              value={form.id_rol}
              onChange={(e) => cambiar('id_rol', e.target.value)}
              disabled={guardando}
              className={claseInput(Boolean(props['aria-invalid']))}
            >
              <option value="">Seleccione un rol...</option>
              {roles.map((rol) => (
                <option key={rol.id_rol} value={rol.id_rol}>
                  {rol.nombre} ({rol.total_permisos} permisos)
                </option>
              ))}
            </select>
          )}
        </CampoFormulario>

        {!esEdicion && (
          <CampoFormulario
            etiqueta="Contraseña"
            requerido
            error={errorDe('password') ?? errorDe('contrasena')}
            ayuda="Mínimo 8 caracteres, 1 mayúscula, 1 número y 1 símbolo."
          >
            {(props) => (
              <input
                {...props}
                type="password"
                value={form.password}
                onChange={(e) => cambiar('password', e.target.value)}
                disabled={guardando}
                autoComplete="new-password"
                className={claseInput(Boolean(props['aria-invalid']))}
              />
            )}
          </CampoFormulario>
        )}

        {!esEdicion && <PasswordRequirements contrasena={form.password} />}

        <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
          <input
            type="checkbox"
            checked={form.activo}
            onChange={(e) => cambiar('activo', e.target.checked)}
            disabled={guardando}
            className="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-amber-600 focus:ring-amber-500 cursor-pointer"
          />
          <span>
            <span className="block text-xs font-semibold text-slate-800">
              Cuenta activa
            </span>
            <span className="mt-0.5 block text-[11px] text-slate-500">
              Una cuenta inactiva conserva todo su historial de ventas y no puede iniciar sesión.
            </span>
          </span>
        </label>
      </form>
    </Modal>
  );
};

/** El backend manda `string[]`; se junta para que quepa en una línea. */
const previoATexto = (errores?: string[]): string | undefined => {
  if (!errores?.length) return undefined;
  return errores.join(' ');
};

export default ModalUsuario;
