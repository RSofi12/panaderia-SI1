export interface Permiso {
  id_permiso: number;
  nombre: string;
  descripcion?: string;
}

export interface Rol {
  id_rol: number;
  nombre: string;
  descripcion?: string;
  permisos?: Permiso[];
}

export interface Usuario {
  id_usuario: number;
  nombre_usuario: string;
  nombre_completo: string;
  email: string | null;
  activo: boolean;
  id_rol: number | null;
  rol: string;
  permisos: string[];
}

export interface LoginCredentials {
  nombre_usuario: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: Usuario;
}

export interface AuthContextType {
  user: Usuario | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permissionName: string) => boolean;
  hasRole: (roleName: string) => boolean;
}

/* ------------------------------------------------------------------ *
 * CU2 - Recuperar contraseña
 * ------------------------------------------------------------------ */

/**
 * Lo que el formulario de "olvidé mi contraseña" envía.
 *
 * `identificador` (y no `email`) a propósito: el backend acepta tanto el nombre
 * de usuario como el correo (`localizar_usuario()` busca por `nombre_usuario` y
 * luego por `email__iexact`). Ponerle `email` obligaría al usuario a recordar
 * cuál de los dos escribió al Minusculas y en qué momento.
 */
export interface SolicitudRecuperacion {
  identificador: string;
}

/**
 * Cuerpo del paso 2. El token viaja en la URL del enlace del correo, no en el
 * cuerpo de la petición: por eso el frontend lo lee de `searchParams` y lo
 * escribe acá.
 */
export interface ConfirmacionRecuperacion {
  token: string;
  nueva_contrasena: string;
  confirmar_contrasena: string;
}

/**
 * Respuesta del paso 1. Siempre 200 y SIEMPRE este mismo texto, exista o no la
 * cuenta: es la anti-enumeración del CU2. Por eso el frontend no debe intentar
 * "mejorar" el mensaje ni deducir nada a partir de él.
 */
export interface RespuestaSolicitud {
  message: string;
}

/**
 * Respuesta del paso 2. `nombre_usuario` viene para poder prellenar el login:
 * quien recupera la contraseña ya sabe cómo se llama y no debería tener que
 * acordarse.
 */
export interface RespuestaConfirmacion {
  message: string;
  nombre_usuario: string;
}

/**
 * Forma de los errores que devuelve el backend en los endpoints del CU2.
 *
 * Son tres formas distintas y el frontend tiene que saber cuál llegó:
 *
 *  - `{ error: string }`       -> `ContrasenaDebilError` y `TokenRecuperacionInvalidoError`.
 *                                Error de negocio, se muestra tal cual.
 *  - `{ error: string[] }`     -> contraseña débil: DRF devuelve una lista de
 *                                mensajes, uno por regla incumplida.
 *  - `{ [campo: string]: string[] }` -> error de campo del serializador
 *                                (`confirmar_contrasena: ["Las contraseñas no coinciden."]`,
 *                                `identificador: ["Este campo no puede estar vacío."]`).
 *                                Se muestra pegado al input, no arriba.
 *
 * Más `retry_after_seconds` en el 429, que es el mismo contrato que ya usa el
 * login del CU1, así que la cuenta regresiva se puede reusar tal cual.
 */
export interface ErrorRecuperacion {
  error?: string | string[];
  retry_after_seconds?: number;
  detail?: string;
  [campo: string]: unknown;
}
