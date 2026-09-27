import api from './api';
import type { AuthResponse, LoginCredentials, Usuario } from '../types/auth';

export const authService = {
  /**
   * Inicia sesión (CU1) enviando nombre de usuario y contraseña
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login/', credentials);
    return response.data;
  },

  /**
   * Obtiene los datos del usuario actualmente autenticado (/api/auth/me/)
   */
  async getMe(): Promise<Usuario> {
    const response = await api.get<Usuario>('/auth/me/');
    return response.data;
  },

  /**
   * Notifica al backend el cierre de sesión para registrarlo en Bitácora
   */
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout/');
    } catch {
      // Si falla la red, continuamos con la limpieza local
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
    }
  },
};

export default authService;
