import React, { useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { Link, useSearchParams } from 'react-router-dom';
import { AlertCircle, CheckCircle2, Eye, EyeOff, KeyRound, Lock, ShieldAlert } from 'lucide-react';
import { authService } from '../../services/authService';
import AuthCard from './components/AuthCard';
import PasswordRequirements from './components/PasswordRequirements';
import { cumplePoliticaVisible } from './politicaContrasena';
import type { ErrorRecuperacion } from '../../types/auth';

/**
 * CU2, paso 2: escribir la contraseña nueva (`/recuperar-password/nueva`).
 *
 * Se llega acá por el enlace del correo, con el token en el query string:
 * `/recuperar-password/nueva?token=XXXX`
 *
 * CUATRO COSAS QUE ESTA PANTALLA HACE Y QUE NO SON OBVIAS
 *
 * 1. LEE EL TOKEN UNA SOLA VEZ Y LO SACA DE LA URL.
 *    El token es una credencial. Si queda en la barra de direcciones se
 *    guarda en el historial del navegador y puede filtrarse por `Referer` a
 *    cualquier recurso externo que se cargue después. Por eso, apenas se lee,
 *    se reescribe la URL con `replaceState` para que el token desaparezca de la
 *    barra sin recargar la página ni perder el estado del componente.
 *
 * 2. SI NO HAY TOKEN, NO MANDA NADA.
 *    Se muestra un estado de error con el enlace para pedir uno nuevo. Un POST
 *    con token vacío solo gastaría uno de los 5 intentos por minuto del
 *    throttle sin ningún sentido.
 *
 * 3. LOS ERRORES DE CAMPO SE PEGAN AL INPUT, LOS DE NEGOCIO ARRIBA.
 *    El backend devuelve tres formas distintas: `{campo: [msg]}` del
 *    serializador (van al campo), `{error: string}` de las excepciones propias
 *    (van arriba) y `{error: string[]}` de contraseña débil (van arriba, porque
 *    el checklist del formulario ya los muestra uno por uno).
 *
 * 4. TRAS CONFIRMAR, EL TOKEN QUEMÓ.
 *    El backend marca el token como usado, así que recargar la página NO vuelve
 *    a intentar nada: cae en el estado "falta el token" porque la URL ya no lo
 *    tiene. Por eso el estado de éxito se pinta en memoria y no depende de
 *    repreguntarle nada al servidor.
 */
export const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  // 1) El token se lee con un inicializador perezoso, no con un efecto.
  //
  // Leer el query string ES leer estado inicial: el token no va a cambiar
  // mientras la página esté montada, y una pantalla de restablecimiento se
  // monta una vez y se descarta. Con `useEffect` se recarga el componente
  // entero en el primer render con `token = null`, recién en el segundo
  // render ya tiene el token. Ese primer render es el que pinta el estado
  // "falta el token" durante un instante, y en una pantalla con un
  // `return` temprano se traduce en un parpadeo visible.
  const [token, setToken] = useState<string | null>(() =>
    searchParams.get('token'),
  );

  // Limpia el query string del historial visible. El segundo argumento
  // vacío y el tercero con `replace` evitan que esta entrada se pueda volver
  // atrás con el botón del navegador.
  //
  // Esto sí es un efecto, porque no es estado: es historia del navegador. Y
  // va aparte del token justamente por eso, para que el token no dependa de
  // un efecto.
  useEffect(() => {
    window.history.replaceState(null, '', window.location.pathname);
  }, []);

  const [nueva, setNueva] = useState('');
  const [confirmacion, setConfirmacion] = useState('');
  const [verNueva, setVerNueva] = useState(false);
  const [verConfirmacion, setVerConfirmacion] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [exito, setExito] = useState<{ mensaje: string; nombreUsuario: string } | null>(
    null
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setErroresCampos({});

    if (nueva !== confirmacion) {
      setErroresCampos({ confirmar_contrasena: 'Las contraseñas no coinciden.' });
      return;
    }

    if (!cumplePoliticaVisible(nueva)) {
      // No se envía. El checklist de abajo ya dice cuál falta, así que alcanza
      // con el foco en el mensaje y se deja que la persona lea.
      setError('La contraseña todavía no cumple la política de abajo.');
      return;
    }

    if (!token) return;

    setIsSubmitting(true);
    try {
      const respuesta = await authService.confirmarRecuperacion({
        token,
        nueva_contrasena: nueva,
        confirmar_contrasena: confirmacion,
      });
      setExito({
        mensaje: respuesta.message,
        nombreUsuario: respuesta.nombre_usuario,
      });
      // Ya no sirve para nada: se suelta de memoria para que no quede en un
      // closure alcanzable desde la consola del navegador.
      setToken(null);
      setNueva('');
      setConfirmacion('');
    } catch (err) {
      const datos = isAxiosError<ErrorRecuperacion>(err)
        ? err.response?.data
        : undefined;

      // 3) Separa error de campo de error general.
      const porCampo: Record<string, string> = {};
      if (datos) {
        for (const clave of ['nueva_contrasena', 'confirmar_contrasena', 'token']) {
          const valor = datos[clave];
          if (Array.isArray(valor)) porCampo[clave] = valor.join(' ');
          else if (typeof valor === 'string') porCampo[clave] = valor;
        }
      }
      setErroresCampos(porCampo);

      const bruto = datos?.error;
      if (Array.isArray(bruto)) {
        setError(bruto.join(' '));
      } else if (typeof bruto === 'string') {
        setError(bruto);
      } else if (typeof datos?.detail === 'string') {
        setError(datos.detail);
      } else if (Object.keys(porCampo).length > 0) {
        // Los errores de campo ya se muestran junto a su input: no se repite
        // arriba un mensaje genérico que no aporta nada.
        setError(null);
      } else {
        setError(
          'No se pudo conectar con el servidor. Verificá que el backend esté en ejecución.'
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  /* ---------------------------------------------------------------- *
   * Éxito: pantalla de confirmación con acceso directo al login.
   * ---------------------------------------------------------------- */
  if (exito) {
    return (
      <AuthCard
        titulo="Contraseña restablecida"
        subtitulo="Tu cuenta ya está lista y protegida"
      >
        <div className="mb-5 p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs sm:text-sm rounded-2xl flex items-start gap-3 shadow-2xs">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600 mt-0.5" />
          <div>
            <p className="font-semibold text-emerald-950">{exito.mensaje}</p>
            <p className="mt-1.5 text-emerald-800 text-[11px] leading-relaxed">
              Por seguridad, las sesiones que estaban abiertas en otros
              dispositivos se cerraron automáticamente con este cambio.
            </p>
          </div>
        </div>

        <div className="mb-5 p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl text-center">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
            Usuario verificado
          </p>
          <p className="text-sm font-semibold text-slate-800 mt-0.5">
            {exito.nombreUsuario}
          </p>
        </div>

        <Link
          to="/login"
          className="w-full py-2.5 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-semibold text-xs sm:text-sm rounded-xl shadow-md shadow-amber-600/20 hover:shadow-lg hover:shadow-amber-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <span>Iniciar sesión ahora</span>
          <CheckCircle2 className="w-4 h-4" />
        </Link>
      </AuthCard>
    );
  }

  /* ---------------------------------------------------------------- *
   * Sin token: el enlace llegó incompleto o se recargó la página.
   * ---------------------------------------------------------------- */
  if (!token) {
    return (
      <AuthCard
        titulo="Enlace incompleto"
        subtitulo="No se encontró un código de recuperación válido"
      >
        <div className="mb-5 p-4 bg-amber-50 border border-amber-200 text-amber-900 text-xs sm:text-sm rounded-2xl flex items-start gap-3 shadow-2xs">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 text-amber-600 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-950">Este enlace no trae un código de recuperación válido.</p>
            <p className="mt-1.5 text-amber-800 text-[11px] leading-relaxed">
              Suele pasar si se recargó la página después de usar el enlace: el
              código se borra de la barra de direcciones por seguridad. Pedí uno nuevo y abrilo directo desde el correo.
            </p>
          </div>
        </div>

        <Link
          to="/recuperar-password"
          className="w-full py-2.5 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-semibold text-xs sm:text-sm rounded-xl shadow-md shadow-amber-600/20 hover:shadow-lg hover:shadow-amber-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <KeyRound className="w-4 h-4" />
          <span>Pedir un enlace nuevo</span>
        </Link>

        <Link
          to="/login"
          className="mt-3.5 block text-center text-xs text-amber-800 hover:text-amber-900 font-medium transition-colors"
        >
          Volver al inicio de sesión
        </Link>
      </AuthCard>
    );
  }

  /* ---------------------------------------------------------------- *
   * Formulario.
   * ---------------------------------------------------------------- */
  return (
    <AuthCard
      titulo="Restablecer contraseña"
      subtitulo="Elegí tu nueva clave de acceso para continuar"
    >
      <p className="mb-4 text-xs sm:text-sm text-slate-600 leading-relaxed">
        Estás a un paso de volver a ingresar. La nueva contraseña debe cumplir con la política de seguridad corporativa.
      </p>

      {error && (
        <div className="mb-4 p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm rounded-xl flex items-start gap-2.5 animate-in fade-in">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500 mt-0.5" />
          <span className="leading-tight">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* Contraseña nueva */}
        <div>
          <label
            htmlFor="nueva_contrasena"
            className="block text-xs sm:text-sm font-semibold text-slate-700 mb-1.5"
          >
            Nueva contraseña
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-5 h-5" />
            </div>
            <input
              id="nueva_contrasena"
              type={verNueva ? 'text' : 'password'}
              // `new-password` y no `current-password`: le avisa al gestor de
              // contraseñas del navegador que ESTA es una clave nueva y le
              // ofrece generar una, que es justo lo que conviene acá.
              autoComplete="new-password"
              required
              value={nueva}
              onChange={(e) => setNueva(e.target.value)}
              placeholder="••••••••"
              className="w-full pl-10 pr-11 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200"
            />
            <button
              type="button"
              onClick={() => setVerNueva(!verNueva)}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
              aria-label={verNueva ? 'Ocultar contraseña' : 'Ver contraseña'}
            >
              {verNueva ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
          {erroresCampos.nueva_contrasena && (
            <p className="mt-1 text-[11px] text-red-600 font-medium">
              {erroresCampos.nueva_contrasena}
            </p>
          )}
          <PasswordRequirements contrasena={nueva} />
        </div>

        {/* Confirmación */}
        <div>
          <label
            htmlFor="confirmar_contrasena"
            className="block text-xs sm:text-sm font-semibold text-slate-700 mb-1.5"
          >
            Confirmar nueva contraseña
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-5 h-5" />
            </div>
            <input
              id="confirmar_contrasena"
              type={verConfirmacion ? 'text' : 'password'}
              autoComplete="new-password"
              required
              value={confirmacion}
              onChange={(e) => setConfirmacion(e.target.value)}
              placeholder="••••••••"
              className="w-full pl-10 pr-11 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200"
            />
            <button
              type="button"
              onClick={() => setVerConfirmacion(!verConfirmacion)}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
              aria-label={
                verConfirmacion ? 'Ocultar confirmación' : 'Ver confirmación'
              }
            >
              {verConfirmacion ? (
                <EyeOff className="w-5 h-5" />
              ) : (
                <Eye className="w-5 h-5" />
              )}
            </button>
          </div>
          {erroresCampos.confirmar_contrasena && (
            <p className="mt-1 text-[11px] text-red-600 font-medium">
              {erroresCampos.confirmar_contrasena}
            </p>
          )}
          {/* Se avisa en caliente, sin esperar al backend. */}
          {confirmacion.length > 0 && confirmacion !== nueva && (
            <p className="mt-1 text-[11px] text-amber-600 font-medium">
              Las contraseñas todavía no coinciden.
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-semibold text-xs sm:text-sm rounded-xl shadow-md shadow-amber-600/20 hover:shadow-lg hover:shadow-amber-600/30 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Guardando...</span>
            </>
          ) : (
            <>
              <span>Guardar nueva contraseña</span>
              <CheckCircle2 className="w-4 h-4" />
            </>
          )}
        </button>

        <div className="text-center pt-2">
          <Link
            to="/login"
            className="text-xs text-amber-800 hover:text-amber-900 font-medium transition-colors"
          >
            ← Cancelar y volver al inicio de sesión
          </Link>
        </div>
      </form>
    </AuthCard>
  );
};

export default ResetPasswordPage;
