import React, { useState } from 'react';
import { isAxiosError } from 'axios';
import { Link, Navigate } from 'react-router-dom';
import { AlertCircle, ArrowLeft, Mail, Send, Timer } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { authService } from '../../services/authService';
import circleLogo from '../../assets/circle-logo-panaderia.svg';
import photoBakery from '../../assets/photo-bakery.jpg';
import type { ErrorRecuperacion } from '../../types/auth';

/**
 * Convierte los segundos que devuelve el backend en mm:ss.
 */
const formatearEspera = (segundos: number): string => {
  const minutos = Math.floor(segundos / 60);
  const resto = segundos % 60;
  return `${String(minutos).padStart(2, '0')}:${String(resto).padStart(2, '0')}`;
};

/**
 * CU2, paso 1: pedir un enlace de recuperación (`/recuperar-password`).
 *
 * Muestra el diseño Split-Screen corporativo idéntico a LoginPage.
 */
export const ForgotPasswordPage: React.FC = () => {
  const [identificador, setIdentificador] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [retryAfter, setRetryAfter] = useState(0);

  const { isAuthenticated } = useAuth();

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

      const segundos = datos?.retry_after_seconds;
      const hayBloqueo =
        typeof segundos === 'number' && Number.isFinite(segundos) && segundos > 0;
      setRetryAfter(hayBloqueo ? Math.ceil(segundos) : 0);

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

  return (
    <div className="min-h-screen lg:h-screen w-full flex flex-col lg:flex-row bg-white overflow-x-hidden">
      {/* ==================================================================== */}
      {/* LADO IZQUIERDO: Fotografía de panadería (solo desktop)                */}
      {/* ==================================================================== */}
      <div className="hidden lg:flex lg:w-1/2 h-full min-h-screen relative bg-slate-900 overflow-hidden flex-shrink-0">
        <img
          src={photoBakery}
          alt="Panadería Santiago"
          className="absolute inset-0 w-full h-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-black/10" />

        <div className="absolute bottom-8 left-8 xl:bottom-12 xl:left-12 z-10 text-white select-none">
          <h2 className="font-sugo text-3xl sm:text-4xl xl:text-5xl text-white tracking-wide drop-shadow-lg">
            Panadería Santiago
          </h2>
          <p className="mt-1 text-xs sm:text-sm font-medium tracking-wider text-amber-200/90 uppercase drop-shadow">
            Portal de Gestión
          </p>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* LADO DERECHO: Formulario de recuperación centrado                    */}
      {/* ==================================================================== */}
      <div className="w-full lg:w-1/2 min-h-screen lg:h-screen flex flex-col justify-center items-center px-6 py-8 sm:px-10 lg:px-12 xl:px-16 bg-white overflow-y-auto">
        <div className="w-full max-w-sm sm:max-w-md my-auto">
          {/* Logo circular superior */}
          <div className="text-center mb-5">
            <div className="w-20 h-20 sm:w-24 sm:h-24 mx-auto rounded-full bg-white shadow-md p-1.5 border-4 border-white flex items-center justify-center mb-3 transition-transform duration-300 hover:scale-105">
              <img
                src={circleLogo}
                alt="Logo Panadería Santiago"
                className="w-full h-full object-contain rounded-full"
              />
            </div>

            <h1 className="font-sugo text-2xl sm:text-3xl text-slate-900 tracking-wide">
              Recuperar contraseña
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-slate-500">
              Ingresá tu usuario o correo para enviarte un enlace de acceso
            </p>
          </div>

          {/* ================================================================ */}
          {/* ESTADO DE ÉXITO                                                  */}
          {/* ================================================================ */}
          {mensaje ? (
            <div className="space-y-4 animate-in fade-in duration-300">
              <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs sm:text-sm rounded-2xl flex items-start gap-3 shadow-2xs">
                <Mail className="w-5 h-5 flex-shrink-0 text-emerald-600 mt-0.5" />
                <div>
                  <p className="font-semibold text-emerald-950">{mensaje}</p>
                  <p className="mt-1.5 text-emerald-800 text-[11px] leading-relaxed">
                    Si no aparece en unos minutos, revisá tu carpeta de correo no deseado (spam).
                  </p>
                </div>
              </div>

              <Link
                to="/login"
                className="w-full py-2.5 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-semibold text-xs sm:text-sm rounded-xl shadow-md shadow-amber-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
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
                className="w-full text-center text-xs text-amber-800 hover:text-amber-900 font-medium transition-colors cursor-pointer pt-1"
              >
                ¿Necesitás enviar a otro correo? Volver a intentar
              </button>
            </div>
          ) : (
            /* ================================================================ */
            /* FORMULARIO NORMAL                                                */
            /* ================================================================ */
            <div>
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-start gap-2 animate-shake">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-500 mt-0.5" />
                  <div className="flex-1">
                    <span>{error}</span>
                    {limiteAlcanzado && (
                      <div className="mt-1.5 flex items-center gap-1.5 font-mono text-xs font-semibold text-red-800 tabular-nums">
                        <Timer className="w-3.5 h-3.5" />
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
                    className="block text-xs font-semibold text-slate-700 mb-1.5"
                  >
                    Usuario o correo electrónico
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      id="identificador"
                      type="text"
                      autoComplete="username"
                      required
                      value={identificador}
                      onChange={(e) => setIdentificador(e.target.value)}
                      placeholder="ej. mgonzales o ventas@mail.com"
                      className="w-full pl-9 pr-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || limiteAlcanzado}
                  className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-semibold text-xs sm:text-sm rounded-xl shadow-md shadow-amber-600/20 hover:shadow-lg hover:shadow-amber-600/30 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Enviando enlace...</span>
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

              <div className="mt-5 text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center gap-1.5 text-xs text-amber-800 hover:text-amber-900 font-semibold transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Volver al inicio de sesión
                </Link>
              </div>
            </div>
          )}

          {/* Pie institucional */}
          <div className="mt-8 text-center text-[10px] text-slate-400">
            Panadería Santiago • Santa Cruz de la Sierra, Bolivia
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
