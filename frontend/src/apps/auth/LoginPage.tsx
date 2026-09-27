import React, { useState } from 'react';
import { isAxiosError } from 'axios';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Lock, User, Eye, EyeOff, AlertCircle, CheckCircle2, ChefHat, Sparkles } from 'lucide-react';
import circleLogo from '../../assets/circle-logo-panaderia.svg';

export const LoginPage: React.FC = () => {
  const [nombreUsuario, setNombreUsuario] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPasswordPolicy, setShowPasswordPolicy] = useState(false);

  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Destino posterior al login (por defecto /dashboard)
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

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
      const responseData = isAxiosError<{ error?: string; detail?: string }>(err)
        ? err.response?.data
        : undefined;
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
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-amber-50/60 via-slate-50 to-amber-100/40 p-4 sm:p-6 lg:p-8">
      {/* Contenedor Principal de la Tarjeta */}
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl shadow-amber-900/5 border border-amber-100/80 overflow-hidden backdrop-blur-sm">
        
        {/* Cabecera con Logo e Identidad Visual */}
        <div className="pt-8 pb-4 px-8 text-center bg-gradient-to-b from-amber-50/70 to-transparent">
          <div className="relative inline-block mb-3">
            <div className="w-24 h-24 sm:w-28 sm:h-28 mx-auto rounded-full bg-white shadow-md p-1 border-2 border-amber-200/80 flex items-center justify-center transition-transform duration-300 hover:scale-105">
              <img
                src={circleLogo}
                alt="Logo Panadería Santiago"
                className="w-full h-full object-contain rounded-full"
              />
            </div>
            <div className="absolute -bottom-1 -right-1 bg-amber-600 text-white p-1.5 rounded-full shadow-sm">
              <ChefHat className="w-4 h-4" />
            </div>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Panadería Santiago
          </h1>
          <p className="text-xs sm:text-sm text-amber-800 font-medium mt-1">
            Sistema de Información Web • SI-1
          </p>
        </div>

        {/* Formulario de Login */}
        <div className="px-6 sm:px-8 pb-8 pt-2">
          {error && (
            <div className="mb-5 p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm rounded-xl flex items-start gap-2.5 animate-shake">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500 mt-0.5" />
              <span>{error}</span>
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
                <span className="text-[11px] text-amber-700 hover:text-amber-800 font-medium cursor-pointer">
                  ¿Olvidaste tu contraseña?
                </span>
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
              disabled={isSubmitting}
              className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-semibold text-sm rounded-xl shadow-md shadow-amber-600/20 hover:shadow-lg hover:shadow-amber-600/30 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Iniciando sesión...</span>
                </>
              ) : (
                <>
                  <span>Ingresar al Sistema</span>
                  <CheckCircle2 className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Panel Rápido de Cuentas de Prueba (Seed Data) */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                Cuentas de Prueba (Demo)
              </span>
              <span className="text-[11px] text-slate-400 font-mono">Pass: Admin123!</span>
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

        </div>

        {/* Pie de Página de la Tarjeta */}
        <div className="py-3 px-6 bg-slate-50 border-t border-slate-100 text-center text-[11px] text-slate-400">
          Panadería Santiago • Santa Cruz de la Sierra, Bolivia
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
