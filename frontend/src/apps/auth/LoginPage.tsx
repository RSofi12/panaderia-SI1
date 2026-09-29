import React, { useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { useNavigate, useLocation, Navigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Lock, User, Eye, EyeOff, AlertCircle, CheckCircle2, Timer, Sparkles } from 'lucide-react';
import AuthCard from './components/AuthCard';

type RespuestaErrorLogin = {
  error?: string;
  detail?: string;
  retry_after_seconds?: number;
};

/**
 * Convierte los segundos que devuelve el backend en mm:ss.
 *
 * El texto "espera 10 minutos" que llegaba antes era inverificable para el
 * usuario: no tenía forma de saber si ya había pasado el tiempo, así que
 * reintentaba y recibía el mismo error. Con la cuenta regresiva ve exactamente
 * cuándo vuelve a habilitarse el botón.
 */
const formatearEspera = (segundos: number): string => {
  const minutos = Math.floor(segundos / 60);
  const resto = segundos % 60;
  return `${String(minutos).padStart(2, '0')}:${String(resto).padStart(2, '0')}`;
};

export const LoginPage: React.FC = () => {
  const [nombreUsuario, setNombreUsuario] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPasswordPolicy, setShowPasswordPolicy] = useState(false);
  // Segundos que faltan para que expire el bloqueo. 0 = la cuenta no está bloqueada.
  const [retryAfter, setRetryAfter] = useState(0);

  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Destino posterior al login (por defecto /dashboard)
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  // Cuenta regresiva. Se actualiza con un intervalo de un segundo y se detiene
  // solo al llegar a cero, para no dejar timers huérfanos en el componente.
  useEffect(() => {
    if (retryAfter <= 0) return;
    const intervalo = window.setInterval(() => {
      setRetryAfter((actual) => Math.max(0, actual - 1));
    }, 1000);
    return () => window.clearInterval(intervalo);
  }, [retryAfter]);

  // Si ya hay sesión activa no tiene sentido mostrar el formulario
  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!nombreUsuario.trim() || !password.trim()) {
      setShowPasswordPolicy(true);
      setError('Por favor, ingresa tu usuario y contraseña.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login({
        nombre_usuario: nombreUsuario.trim(),
        password: password,
      });
      navigate(from, { replace: true });
    } catch (err) {
      setShowPasswordPolicy(true);
      const responseData = isAxiosError<RespuestaErrorLogin>(err)
        ? err.response?.data
        : undefined;

      // El backend envía `retry_after_seconds` cuando la cuenta quedó bloqueada.
      // Si viene, se arma la cuenta regresiva y el botón queda deshabilitado
      // hasta que expire la ventana. Si NO viene, se limpia cualquier contador
      // anterior: si no, un error de red quedaría con el botón congelado.
      const segundos = responseData?.retry_after_seconds;
      const hayBloqueo =
        typeof segundos === 'number' && Number.isFinite(segundos) && segundos > 0;
      setRetryAfter(hayBloqueo ? Math.ceil(segundos) : 0);

      if (responseData?.error) {
        setError(responseData.error);
      } else if (responseData?.detail) {
        setError(responseData.detail);
      } else {
        setError('No se pudo conectar con el servidor. Verifica que el backend esté en ejecución.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper para auto-completar cuentas de prueba en desarrollo
  const setDemoCredentials = (username: string) => {
    setNombreUsuario(username);
    setPassword('Admin123!');
    setError(null);
    setRetryAfter(0);
  };

  const cuentaBloqueada = retryAfter > 0;

  return (
    <AuthCard titulo="Panadería Santiago" subtitulo="Sistema de Información Web">
      {error && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm rounded-xl flex items-start gap-2.5 animate-shake">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500 mt-0.5" />
          <div className="flex-1">
            <span>{error}</span>
            {cuentaBloqueada && (
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
        {/* Campo Usuario */}
        <div>
          <label
            htmlFor="nombre_usuario"
            className="block text-xs sm:text-sm font-semibold text-slate-700 mb-1.5"
          >
            Nombre de Usuario
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <User className="w-5 h-5" />
            </div>
            <input
              id="nombre_usuario"
              type="text"
              autoComplete="username"
              required
              value={nombreUsuario}
              onChange={(e) => setNombreUsuario(e.target.value)}
              placeholder="ej. csantiago, mrojas"
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200"
            />
          </div>
        </div>

        {/* Campo Contraseña */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label
              htmlFor="password"
              className="block text-xs sm:text-sm font-semibold text-slate-700"
            >
              Contraseña
            </label>
            {/* Antes esto era un <span> sin onClick: un texto que parecía
                    un enlace y no hacía nada. Ahora es un Link de verdad al paso 1
                    del CU2. Se usa Link y no un navigate() con onClick para que
                    Ctrl+clic y "abrir en pestaña nueva" funcionen, y para que no
                    recargue la aplicación. */}
            <Link
              to="/recuperar-password"
              className="text-[11px] text-amber-700 hover:text-amber-800 font-medium transition-colors"
            >
              ¿Olvidaste tu contraseña?
            </Link>
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-5 h-5" />
            </div>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full pl-10 pr-11 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
              aria-label={showPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
            >
              {showPassword ? (
                <EyeOff className="w-5 h-5" />
              ) : (
                <Eye className="w-5 h-5" />
              )}
            </button>
          </div>
          {showPasswordPolicy && (
            <p className="mt-1 text-[11px] text-slate-500">
              Mínimo 8 caracteres, 1 mayúscula, 1 número y 1 símbolo (!@#%).
            </p>
          )}
        </div>

        {/* Botón de Ingreso */}
        <button
          type="submit"
          disabled={isSubmitting || cuentaBloqueada}
          className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-semibold text-sm rounded-xl shadow-md shadow-amber-600/20 hover:shadow-lg hover:shadow-amber-600/30 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Iniciando sesión...</span>
            </>
          ) : cuentaBloqueada ? (
            <>
              <Timer className="w-4 h-4" />
              <span>Espera {formatearEspera(retryAfter)}</span>
            </>
          ) : (
            <>
              <span>Ingresar al Sistema</span>
              <CheckCircle2 className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      {/* Panel Rápido de Cuentas de Prueba (Seed Data).

              Solo en desarrollo. Este panel publica usuarios y una contraseña
              REAL en pantalla; en un build de producción es una puerta abierta
              para cualquiera que llegue a /login. `import.meta.env.DEV` lo
              reemplaza por `false` en el bundle que se sirve, así que Vite elimina
              el código y no queda ni el texto en el bundle resultante. */}
      {import.meta.env.DEV && (
        <div className="mt-6 pt-5 border-t border-slate-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-600" />
              Cuentas de Prueba (Demo)
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              Pass: Admin123!
            </span>
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            <button
              type="button"
              onClick={() => setDemoCredentials('admin')}
              className="py-1.5 px-2 bg-amber-50 hover:bg-amber-100/80 text-amber-900 border border-amber-200/60 rounded-lg text-xs font-medium text-left transition-colors flex items-center justify-between"
            >
              <span>👑 Admin</span>
              <code className="text-[10px] text-amber-700">admin</code>
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials('csantiago')}
              className="py-1.5 px-2 bg-slate-100 hover:bg-slate-200/70 text-slate-800 border border-slate-200 rounded-lg text-xs font-medium text-left transition-colors flex items-center justify-between"
            >
              <span>💼 Propietario</span>
              <code className="text-[10px] text-slate-600">csantiago</code>
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials('mgonzales')}
              className="py-1.5 px-2 bg-slate-100 hover:bg-slate-200/70 text-slate-800 border border-slate-200 rounded-lg text-xs font-medium text-left transition-colors flex items-center justify-between"
            >
              <span>🛒 Ventas</span>
              <code className="text-[10px] text-slate-600">mgonzales</code>
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials('mrojas')}
              className="py-1.5 px-2 bg-slate-100 hover:bg-slate-200/70 text-slate-800 border border-slate-200 rounded-lg text-xs font-medium text-left transition-colors flex items-center justify-between"
            >
              <span>🥖 Producción</span>
              <code className="text-[10px] text-slate-600">mrojas</code>
            </button>
          </div>
        </div>
      )}
    </AuthCard>
  );
};

export default LoginPage;
