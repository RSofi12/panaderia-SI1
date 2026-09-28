import api from './api';
import type {
  AuthResponse,
  ConfirmacionRecuperacion,
  LoginCredentials,
  RespuestaConfirmacion,
  RespuestaSolicitud,
  SolicitudRecuperacion,
  Usuario,
} from '../types/auth';

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
   * Notifica al backend el cierre de sesión.
   *
   * Envía el refresh_token a propósito: el backend lo revoca en su lista negra,
   * de modo que el token deja de servir aunque alguien lo hubiera copiado. Sin
   * este parámetro el cierre de sesión solo limpia el navegador y el token
   * seguiría válido hasta cumplir sus 7 días.
   */
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout/', {
        refresh: localStorage.getItem('refresh_token'),
      });
    } catch {
      // Si falla la red, continuamos con la limpieza local
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
    }
  },

  /**
   * CU2 paso 1: pide un enlace de recuperación.
   *
   * `identificador` puede ser el nombre de usuario o el correo. El backend
   * devuelve SIEMPRE 200 con el mismo mensaje, exista o no la cuenta, así que
   * esta función no se puede usar para averiguar si un correo está registrado:
   * del lado del cliente no hay información que leer.
   */
  async solicitarRecuperacion(
    datos: SolicitudRecuperacion
  ): Promise<RespuestaSolicitud> {
    const response = await api.post<RespuestaSolicitud>(
      '/auth/password-reset-request/',
      datos
    );
    return response.data;
  },

  /**
   * CU2 paso 2: confirma el enlace y fija la contraseña nueva.
   *
   * Envía el token que venía en la URL del correo. Ojo con el estado: al
   * devolver 200 el backend ya cambió la contraseña, revocó las sesiones
   * abiertas y quemó el token, así que un reintento con el mismo enlace
   * devuelve 400.
   */
  async confirmarRecuperacion(
    datos: ConfirmacionRecuperacion
  ): Promise<RespuestaConfirmacion> {
    const response = await api.post<RespuestaConfirmacion>(
      '/auth/password-reset-confirm/',
      datos
    );
    return response.data;
  },
};

export default authService;
