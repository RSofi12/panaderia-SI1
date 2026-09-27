import React from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredRole?: string;
}

const SessionLoader: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-slate-50">
    <div className="text-center p-8">
      <div className="w-12 h-12 border-4 border-amber-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
      <p className="text-slate-700 font-medium">Verificando sesión...</p>
    </div>
  </div>
);

const AccessDenied: React.FC<{ rol: string; permiso: string }> = ({ rol, permiso }) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-red-100 p-8 text-center">
        <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Acceso no autorizado</h2>
        <p className="text-slate-600 text-sm leading-relaxed mb-6">
          Tu rol <span className="font-semibold text-slate-900">{rol}</span> no cuenta con el
          permiso{' '}
          <code className="text-red-600 bg-red-50 px-1.5 py-0.5 rounded">{permiso}</code>, por lo
          que esta ventana no está disponible para ti.
        </p>
        <button
          type="button"
          onClick={() => navigate('/dashboard', { replace: true })}
          className="w-full py-2.5 px-4 bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold rounded-xl transition-colors cursor-pointer"
        >
          Volver al panel
        </button>
      </div>
    </div>
  );
};

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPermission,
  requiredRole,
}) => {
  const { user, isAuthenticated, isLoading, hasPermission, hasRole } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <SessionLoader />;
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return <Navigate to="/dashboard" replace />;
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <AccessDenied rol={user.rol} permiso={requiredPermission} />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
