import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthProvider';
import ProtectedRoute from './ProtectedRoute';
import LoginPage from '../apps/auth/LoginPage';
import ForgotPasswordPage from '../apps/auth/ForgotPasswordPage';
import ResetPasswordPage from '../apps/auth/ResetPasswordPage';
import DashboardLayout from '../apps/dashboard/DashboardLayout';
import DashboardHome from '../apps/dashboard/DashboardHome';
import UsuariosPage from '../apps/dashboard/usuarios/UsuariosPage';

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

            {/* CU3 - Gestión de usuarios.
                Va DENTRO de /dashboard y no como ruta suelta porque comparte
                el Sidebar, el Topbar y el pie con el resto del panel. Si
                fuera una ruta hermana, el usuario perdería el marco al entrar
                a administrar cuentas.

                El `ProtectedRoute` va AQUÍ y no en la ruta padre porque cada
                ventana puede pedir un permiso distinto: hoy esta exige
                `gestionar_usuarios`, y cuando CU4 se sume va a exigir
                `asignar_permisos`. Si el permiso se comprobara en la ruta
                padre, el día que las dos coexistan, entrar a una cerraría
                la otra. El primer filtro es de navegación (el Sidebar
                esconde el enlace) y este es de seguridad (la URL directa
                no sirve). Son capas distintas y hacen falta las dos. */}
            <Route
              path="usuarios"
              element={
                <ProtectedRoute requiredPermission="gestionar_usuarios">
                  <UsuariosPage />
                </ProtectedRoute>
              }
            />
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
