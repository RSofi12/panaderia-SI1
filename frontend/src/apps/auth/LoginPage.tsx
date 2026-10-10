import React, { useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { useNavigate, useLocation, Navigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  Lock,
  User,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  Timer,
  Sparkles,
  ShieldCheck,
  Briefcase,
  ShoppingCart,
  Wheat,
} from 'lucide-react';
import circleLogo from '../../assets/circle-logo-panaderia.svg';
import photoBakery from '../../assets/photo-bakery.jpg';

type RespuestaErrorLogin = {
  error?: string;
  detail?: string;
  retry_after_seconds?: number;
};

/**
 * Convierte los segundos que devuelve el backend en mm:ss.
 */
const formatearEspera = (segundos: number): string => {
  const minutos = Math.floor(segundos / 60);
  const resto = segundos % 60;
  return `${String(minutos).padStart(2, '0')}:${String(resto).padStart(2, '0')}`;
};

export const LoginPage: React.FC = () => {
  const [nombreUsuario, setNombreUsuario] = useState('');
  const [password, setPassword] = useState('');
  const [recordarme, setRecordarme] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPasswordPolicy, setShowPasswordPolicy] = useState(false);
  const [retryAfter, setRetryAfter] = useState(0);

  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  useEffect(() => {
    if (retryAfter <= 0) return;
    const intervalo = window.setInterval(() => {
      setRetryAfter((actual) => Math.max(0, actual - 1));
    }, 1000);
    return () => window.clearInterval(intervalo);
  }, [retryAfter]);

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

      if (!recordarme) {
        sessionStorage.setItem('session_ephemeral', 'true');
      } else {
        sessionStorage.removeItem('session_ephemeral');
      }

      navigate(from, { replace: true });
    } catch (err) {
      setShowPasswordPolicy(true);
      const responseData = isAxiosError<RespuestaErrorLogin>(err)
        ? err.response?.data
        : undefined;

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

  const setDemoCredentials = (username: string) => {
    setNombreUsuario(username);
    setPassword('Admin123!');
    setError(null);
    setRetryAfter(0);
  };

  const cuentaBloqueada = retryAfter > 0;

  return (
    <div className="min-h-screen lg:h-screen w-full flex flex-col lg:flex-row bg-white overflow-x-hidden">
      {/* ==================================================================== */}
      {/* LADO IZQUIERDO: Fotografía (solo en pantallas grandes / desktop)      */}
      {/* En teléfonos/tablets se oculta para que el login quede 100% limpio    */}
      {/* ==================================================================== */}
      <div className="hidden lg:flex lg:w-1/2 h-full min-h-screen relative bg-slate-900 overflow-hidden flex-shrink-0">
        <img
          src={photoBakery}
          alt="Panadería Santiago"
          className="absolute inset-0 w-full h-full object-cover object-center"
        />
        {/* Overlay degradado sutil */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-black/10" />

        {/* Marca en la esquina inferior izquierda */}
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
      {/* LADO DERECHO: Formulario de inicio de sesión centrado y compacto      */}
      {/* ==================================================================== */}
      <div className="w-full lg:w-1/2 min-h-screen lg:h-screen flex flex-col justify-center items-center px-5 py-6 sm:px-10 lg:px-12 xl:px-16 bg-white overflow-y-auto">
        <div className="w-full max-w-sm sm:max-w-md my-auto">
          {/* Logo circular superior e Identidad */}
          <div className="text-center mb-4 sm:mb-5">
            <div className="w-20 h-20 sm:w-24 sm:h-24 mx-auto rounded-full bg-white shadow-md p-1.5 border-4 border-white flex items-center justify-center mb-2.5 transition-transform duration-300 hover:scale-105">
              <img
                src={circleLogo}
                alt="Logo Panadería Santiago"
                className="w-full h-full object-contain rounded-full"
              />
            </div>

            <h1 className="font-sugo text-2xl sm:text-3xl text-slate-900 tracking-wide">
              Bienvenido
            </h1>
            <p className="mt-0.5 text-xs text-slate-500">
              Inicia sesión para acceder al panel de la panadería
            </p>
          </div>

          {/* Alerta de Error / Bloqueo */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-start gap-2 animate-shake">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-500 mt-0.5" />
              <div className="flex-1">
                <span>{error}</span>
                {cuentaBloqueada && (
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

          {/* Formulario */}
          <form onSubmit={handleSubmit} className="space-y-3.5">
            {/* Campo Usuario */}
            <div>
              <label
                htmlFor="nombre_usuario"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Nombre de Usuario
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <User className="w-4 h-4" />
                </div>
                <input
                  id="nombre_usuario"
                  type="text"
                  autoComplete="username"
                  required
                  value={nombreUsuario}
                  onChange={(e) => setNombreUsuario(e.target.value)}
                  placeholder="ej. csantiago, mrojas"
                  className="w-full pl-9 pr-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200"
                />
              </div>
            </div>

            {/* Campo Contraseña */}
            <div>
              <label
                htmlFor="password"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-10 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {showPasswordPolicy && (
                <p className="mt-1 text-[11px] text-slate-500">
                  Mínimo 8 caracteres, 1 mayúscula, 1 número y 1 símbolo (!@#%).
                </p>
              )}
            </div>

            {/* Fila Recordarme y Enlace Recuperación */}
            <div className="flex items-center justify-between pt-0.5">
              <label className="flex items-center gap-1.5 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={recordarme}
                  onChange={(e) => setRecordarme(e.target.checked)}
                  className="h-3.5 w-3.5 rounded border-slate-300 text-amber-600 focus:ring-amber-500 cursor-pointer accent-amber-600"
                />
                <span className="text-xs text-slate-600 font-medium">Recordarme</span>
              </label>

              <Link
                to="/recuperar-password"
                className="text-xs text-amber-700 hover:text-amber-800 font-medium transition-colors"
              >
                ¿Olvidaste tu contraseña?
              </Link>
            </div>

            {/* Botón Principal Iniciar Sesión */}
            <button
              type="submit"
              disabled={isSubmitting || cuentaBloqueada}
              className="w-full mt-1.5 py-2.5 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-semibold text-xs sm:text-sm rounded-xl shadow-md shadow-amber-600/20 hover:shadow-lg hover:shadow-amber-600/30 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
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
                  <span>Iniciar Sesión</span>
                  <CheckCircle2 className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Panel de Cuentas de Prueba (Demo en DEV) */}
          {import.meta.env.DEV && (
            <div className="mt-4 pt-3.5 border-t border-slate-100">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                  Cuentas Demo
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  Pass: Admin123!
                </span>
              </div>

              <div className="grid grid-cols-2 gap-1.5">
                <button
                  type="button"
                  onClick={() => setDemoCredentials('admin')}
                  className="py-1.5 px-2 bg-amber-50/70 hover:bg-amber-100/80 text-amber-950 border border-amber-200/70 rounded-xl text-xs font-semibold text-left transition-all duration-150 flex items-center justify-between group cursor-pointer"
                >
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-amber-600 group-hover:scale-110 transition-transform shrink-0" />
                    <span>Admin</span>
                  </div>
                  <code className="text-[10px] font-mono text-amber-800/80 bg-amber-100/60 px-1 py-0.5 rounded">admin</code>
                </button>

                <button
                  type="button"
                  onClick={() => setDemoCredentials('csantiago')}
                  className="py-1.5 px-2 bg-slate-50 hover:bg-slate-100/90 text-slate-800 border border-slate-200 rounded-xl text-xs font-semibold text-left transition-all duration-150 flex items-center justify-between group cursor-pointer"
                >
                  <div className="flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-slate-600 group-hover:scale-110 transition-transform shrink-0" />
                    <span>Propietario</span>
                  </div>
                  <code className="text-[10px] font-mono text-slate-600 bg-slate-200/60 px-1 py-0.5 rounded">csantiago</code>
                </button>

                <button
                  type="button"
                  onClick={() => setDemoCredentials('mgonzales')}
                  className="py-1.5 px-2 bg-slate-50 hover:bg-slate-100/90 text-slate-800 border border-slate-200 rounded-xl text-xs font-semibold text-left transition-all duration-150 flex items-center justify-between group cursor-pointer"
                >
                  <div className="flex items-center gap-1.5">
                    <ShoppingCart className="w-3.5 h-3.5 text-slate-600 group-hover:scale-110 transition-transform shrink-0" />
                    <span>Ventas</span>
                  </div>
                  <code className="text-[10px] font-mono text-slate-600 bg-slate-200/60 px-1 py-0.5 rounded">mgonzales</code>
                </button>

                <button
                  type="button"
                  onClick={() => setDemoCredentials('mrojas')}
                  className="py-1.5 px-2 bg-slate-50 hover:bg-slate-100/90 text-slate-800 border border-slate-200 rounded-xl text-xs font-semibold text-left transition-all duration-150 flex items-center justify-between group cursor-pointer"
                >
                  <div className="flex items-center gap-1.5">
                    <Wheat className="w-3.5 h-3.5 text-slate-600 group-hover:scale-110 transition-transform shrink-0" />
                    <span>Producción</span>
                  </div>
                  <code className="text-[10px] font-mono text-slate-600 bg-slate-200/60 px-1 py-0.5 rounded">mrojas</code>
                </button>
              </div>
            </div>
          )}

          {/* Pie institucional */}
          <div className="mt-5 text-center text-[10px] text-slate-400">
            Panadería Santiago • Santa Cruz de la Sierra, Bolivia
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
