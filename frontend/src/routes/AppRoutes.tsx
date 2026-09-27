import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthProvider';
import ProtectedRoute from './ProtectedRoute';
import LoginPage from '../apps/auth/LoginPage';
import DashboardLayout from '../apps/dashboard/DashboardLayout';
import DashboardHome from '../apps/dashboard/DashboardHome';

export const AppRoutes: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Ruta pública: Login (CU1) */}
          <Route path="/login" element={<LoginPage />} />

          {/* Ventana privada: shell del dashboard con rutas anidadas */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardHome />} />
          </Route>

          {/* Redirecciones por defecto */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default AppRoutes;
