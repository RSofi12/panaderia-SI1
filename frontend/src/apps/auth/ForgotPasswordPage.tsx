import React, { useState } from 'react';
import { isAxiosError } from 'axios';
import { Link, Navigate } from 'react-router-dom';
import { AlertCircle, ArrowLeft, Mail, Send, Timer } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { authService } from '../../services/authService';
import AuthCard from './components/AuthCard';
import type { ErrorRecuperacion } from '../../types/auth';

/**
 * Convierte los segundos que devuelve el backend en mm:ss.
 *
 * Copia deliberada del helper de `LoginPage`: son cuatro líneas y un
 * `formatearEspera` compartido por tres pantallas no justifica un archivo nuevo,
 * pero cuando se sume la cuarta conviene moverlo a `utils/formato.ts`.
 */
const formatearEspera = (segundos: number): string => {
  const minutos = Math.floor(segundos / 60);
  const resto = segundos % 60;
  return `${String(minutos).padStart(2, '0')}:${String(resto).padStart(2, '0')}`;
};

/**
 * CU2, paso 1: pedir un enlace de recuperación (`/recuperar-password`).
 *
 * LA REGLA DE ORO DE ESTA PANTALLA
 * Después de enviar, se muestra SIEMPRE el mismo mensaje, se haya enviado el
 * correo o no. El backend responde 200 con un texto fijo en los cuatro casos
 * (cuenta real, cuenta inexistente, cuenta inactiva, cuota agotada) justamente
 * para que no se pueda usar el sistema para averiguar qué correos están
 * registrados.
 *
 * El frontend tiene la misma obligación. Sería tentador escribir "Enviamos el
 * enlace a gonzales.ventas@mail.com" o "No encontramos ese correo": las dos
 * cosas son ciertas solo a veces, y una sola vez alcanza para romper la
 * protección. Si el texto se toma tal cual de la respuesta del backend, la
 * garantía se mantiene sola, porque el backend ya la garantiza.
 */
export const ForgotPasswordPage: React.FC = () => {
  const [identificador, setIdentificador] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  // Mensaje de éxito. Se guarda el texto que vino del backend, no uno propio.
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [retryAfter, setRetryAfter] = useState(0);

  const { isAuthenticated } = useAuth();

  // Si ya hay sesión activa no hay contraseña que recuperar, así que esta
  // pantalla no aporta nada: se manda al dashboard, igual que hace `LoginPage`.
  // Ojo que esto NO se replica en `ResetPasswordPage`, y a propósito: ahí la
  // persona llega por el enlace del correo y puede tener sesión abierta en ese
  // mismo navegador (se recupera desde el equipo propio, por ejemplo). El token
  // del enlace ya prueba que es dueña del buzón, así que dejarla terminar la
  // recuperación es lo correcto; además el backend le revoca las sesiones al
  // confirmar, que es justo lo que se busca si alguien más las tenía abiertas.
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!identificador.trim()) {
      setError('Ingresá tu nombre de usuario o tu correo.');
      return;
    }

    setIsSubmitting(true);
    try {
      const respuesta = await authService.solicitarRecuperacion({
        identificador: identificador.trim(),
      });
      setMensaje(respuesta.message);
      setRetryAfter(0);
    } catch (err) {
      const datos = isAxiosError<ErrorRecuperacion>(err)
        ? err.response?.data
        : undefined;

      // El 429 es por IP (5/min), no por cuenta: eso SÍ se puede mostrar con
      // detalle, porque depende de quién pidió y no de qué cuenta escribió.
      const segundos = datos?.retry_after_seconds;
      const hayBloqueo =
        typeof segundos === 'number' && Number.isFinite(segundos) && segundos > 0;
      setRetryAfter(hayBloqueo ? Math.ceil(segundos) : 0);

      // `error` llega como string (token/cuota) o como string[] (reglas del
      // serializador). Se aplana a un solo texto en lugar de dejar un array
      // suelto en el JSX, que React renderizaría concatenado sin separador.
      const bruto = datos?.error;
      if (Array.isArray(bruto)) {
        setError(bruto.join(' '));
      } else if (typeof bruto === 'string') {
        setError(bruto);
      } else if (typeof datos?.detail === 'string') {
        setError(datos.detail);
      } else {
        setError(
          'No se pudo conectar con el servidor. Verificá que el backend esté en ejecución.'
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const limiteAlcanzado = retryAfter > 0;

  /* ---------------------------------------------------------------- *
   * Estado de éxito: el formulario desaparece y queda la confirmación.
   * ---------------------------------------------------------------- */
  if (mensaje) {
    return (
      <AuthCard
        titulo="Revisá tu correo"
        subtitulo="Sistema de Información Web • SI-1"
      >
        <div className="mb-5 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs sm:text-sm rounded-xl flex items-start gap-3">
          <Mail className="w-5 h-5 flex-shrink-0 text-emerald-600 mt-0.5" />
          <div>
            <p>{mensaje}</p>
            <p className="mt-2 text-emerald-700/80 text-[11px] leading-relaxed">
              Si no aparece en unos minutos, revisá la carpeta de correo no
              deseado: a veces el filtro la esconde. Y fijate de que el correo
              que usaste sea el mismo con el que te registraste.
            </p>
          </div>
        </div>

        <Link
          to="/login"
          className="w-full py-3 px-4 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-sm rounded-xl border border-slate-200 transition-colors flex items-center justify-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al inicio de sesión
        </Link>

        <button
          type="button"
          onClick={() => {
            setMensaje(null);
            setIdentificador('');
          }}
          className="mt-3 w-full text-[11px] text-amber-700 hover:text-amber-800 font-medium transition-colors"
        >
          ¿Pediste el enlace por error? Volver a intentarlo
        </button>
      </AuthCard>
    );
  }

  /* ---------------------------------------------------------------- *
   * Estado normal: el formulario.
   * ---------------------------------------------------------------- */
  return (
    <AuthCard
      titulo="Recuperar contraseña"
      subtitulo="Sistema de Información Web • SI-1"
    >
      <p className="mb-5 text-xs sm:text-sm text-slate-600 leading-relaxed">
        Ingresá tu nombre de usuario o tu correo y te enviamos un enlace para
        que elijas una contraseña nueva.
      </p>

      {error && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm rounded-xl flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500 mt-0.5" />
          <div className="flex-1">
            <span>{error}</span>
            {limiteAlcanzado && (
              <div className="mt-2 flex items-center gap-1.5 font-mono text-sm font-semibold text-red-800 tabular-nums">
                <Timer className="w-4 h-4" />
                <span>{formatearEspera(retryAfter)}</span>
                <span className="font-sans font-normal text-red-600">
                  para volver a intentar
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="identificador"
            className="block text-xs sm:text-sm font-semibold text-slate-700 mb-1.5"
          >
            Usuario o correo
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Mail className="w-5 h-5" />
            </div>
            <input
              id="identificador"
              type="text"
              autoComplete="username"
              required
              value={identificador}
              onChange={(e) => setIdentificador(e.target.value)}
              placeholder="ej. mgonzales o gonzales.ventas@mail.com"
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting || limiteAlcanzado}
          className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-semibold text-sm rounded-xl shadow-md shadow-amber-600/20 hover:shadow-lg hover:shadow-amber-600/30 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Enviando...</span>
            </>
          ) : limiteAlcanzado ? (
            <>
              <Timer className="w-4 h-4" />
              <span>Espera {formatearEspera(retryAfter)}</span>
            </>
          ) : (
            <>
              <span>Enviar enlace de recuperación</span>
              <Send className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      <Link
        to="/login"
        className="mt-5 flex items-center justify-center gap-1.5 text-[11px] text-amber-700 hover:text-amber-800 font-medium transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Volver al inicio de sesión
      </Link>
    </AuthCard>
  );
};

export default ForgotPasswordPage;
