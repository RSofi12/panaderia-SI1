import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthProvider';
import ProtectedRoute from './ProtectedRoute';
import LoginPage from '../apps/auth/LoginPage';
import ForgotPasswordPage from '../apps/auth/ForgotPasswordPage';
import ResetPasswordPage from '../apps/auth/ResetPasswordPage';
import DashboardLayout from '../apps/dashboard/DashboardLayout';
import DashboardHome from '../apps/dashboard/DashboardHome';
import ProductosPage from '../apps/dashboard/productos/ProductosPage';

export const AppRoutes: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Ruta pública: Login (CU1) */}
          <Route path="/login" element={<LoginPage />} />

          {/* Rutas públicas del CU2 (recuperar contraseña).
              No van dentro de /dashboard ni detrás de ProtectedRoute a
              propósito: quien llega acá por el enlace del correo puede no tener
              sesión, y el token de la URL es justamente la prueba de que es
              dueña del buzón.

              '/recuperar-password/nueva' tiene que declararse ANTES que la
              wildcard '*' del final, porque esa wildcard manda a /dashboard:
              sin esta ruta explícita el enlace del correo caería en el
              redirect y la recuperación nunca llegaría a existir. */}
          <Route path="/recuperar-password" element={<ForgotPasswordPage />} />
          <Route
            path="/recuperar-password/nueva"
            element={<ResetPasswordPage />}
          />

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
            <Route path="productos" element={<ProductosPage />} />
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
