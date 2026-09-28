import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para inyectar el Access Token en cada petición
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para refrescar el token en caso de 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Evitamos bucle infinito si la petición que falló ya era de login o refresh
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login/') &&
      !originalRequest.url?.includes('/auth/refresh/')
    ) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          localStorage.setItem('access_token', response.data.access);

          // El backend tiene ROTATE_REFRESH_TOKENS=True y BLACKLIST_AFTER_ROTATION=True:
          // cada refresh emite un refresh NUEVO y mete el anterior en la lista negra.
          // Si aquí se descartara el nuevo, el que queda guardado en localStorage
          // estaría revocado y el siguiente refresh fallaría, cerrando la sesión del
          // usuario a la mitad de su turno sin motivo aparente.
          if (response.data.refresh) {
            localStorage.setItem('refresh_token', response.data.refresh);
          }

          originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Si el refresh token también expiró, cerramos sesión
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user_data');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
