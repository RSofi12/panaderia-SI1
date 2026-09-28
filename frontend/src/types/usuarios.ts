/* ------------------------------------------------------------------ *
 * CU3 - Gestionar usuarios
 * ------------------------------------------------------------------ *
 *
 * POR QUÉ ESTE ARCHIVO Y NO `types/usuarios.ts` DENTRO DE `apps/`
 * Los tipos de la API no son de una pantalla: son el contrato con el
 * backend, y el backend es uno solo. Si el tipo viviera junto a la
 * pantalla, la segunda pantalla del mismo endpoint tendría que
 * importarlo de una carpeta hermana y el acoplamiento quedaría al
 * revés. `types/auth.ts` ya fijó esta convención en CU1 y CU2.
 */

/**
 * Fila de la tabla de usuarios.
 *
 * NO es el mismo tipo que `Usuario` de `types/auth.ts`, aunque las dos
 * se llamen cosas parecidas. `Usuario` es la sesión de QUIÉN ESTÁ
 * CONECTADO y trae `permisos: string[]`, que es lo que lee el JWT para
 * decidir qué botones pintar. `UsuarioFila` es una fila del LISTADO y
 * trae `total_permisos`, `esta_bloqueado` y `minutos_bloqueo_restantes`.
 *
 * Confundirlas rompe en los dos sentidos: mandar `permisos` al backend
 * en un PATCH lo ignoraría, y usar `UsuarioFila` para la sesión dejaría
 * al Sidebar sin lista de permisos y escondería todos los módulos.
 * De ahí que esta se llame `UsuarioFila` y no `Usuario`.
 */
export interface UsuarioFila {
  id_usuario: number;
  nombre_usuario: string;
  nombre_completo: string;
  email: string | null;
  id_rol: number | null;
  /** Nombre del rol ya resuelto, para pintar sin una segunda consulta. */
  rol: string;
  activo: boolean;
  /** Cuántos permisos tiene el rol. `0` en un rol sin permisos asignados. */
  total_permisos: number;
  /**
   * Bloqueada por intentos fallidos (CU1). Es una propiedad calculada en
   * el backend, no una columna: por eso la UI puede mostrarla pero nunca
   * enviarla.
   */
  esta_bloqueado: boolean;
  /** Minutos que faltan para que expire el bloqueo. `0` si no está bloqueada. */
  minutos_bloqueo_restantes: number;
}

/** Rol para el desplegable del formulario. No viene paginado: son cuatro filas. */
export interface RolSimple {
  id_rol: number;
  nombre: string;
  descripcion: string;
  total_permisos: number;
}

/**
 * Envoltura de `PageNumberPagination` de DRF.
 *
 * Los cuatro campos vienen siempre. `next` y `previous` son `null` en la
 * primera y la última página, y son URL completas, no relativas: hay que
 * pedirle la URL tal cual o el `next` de la página 2 rompería.
 */
export interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** Filtros que acepta `GET /api/usuarios/`. Todos opcionales. */
export interface FiltrosUsuarios {
  /** `icontains` sobre nombre de usuario, nombre completo y correo. */
  search?: string;
  /** `true` o `false`. Ausente = ambos. */
  activo?: boolean;
  id_rol?: number;
  /** Campo y sentido: `nombre_usuario` o `-nombre_usuario`. */
  ordering?: string;
  page?: number;
}

/** Cuerpo de `POST /api/usuarios/`. La contraseña se escribe una sola vez. */
export interface AltaUsuario {
  nombre_usuario: string;
  nombre_completo: string;
  email: string;
  password: string;
  id_rol: number;
  activo: boolean;
}

/**
 * Cuerpo de `PUT/PATCH /api/usuarios/<id>/`.
 *
 * Todo opcional: el backend usa `partial=True`, así que lo que no se
 * manda no se toca. La contraseña NO va aquí. Cambiarla tiene su propio
 * endpoint a propósito, porque tiene su propia auditoría y su propia
 * lista de efectos colaterales (revocar sesiones).
 */
export interface EditarUsuario {
  nombre_usuario?: string;
  nombre_completo?: string;
  email?: string;
  id_rol?: number;
  activo?: boolean;
}

/** Cuerpo de `PATCH /api/usuarios/<id>/toggle-activo/`. */
export interface CambioEstado {
  activo: boolean;
  /** Queda en la bitácora. El backend escribe "no indicado" si viene vacío. */
  motivo?: string;
}

/** Cuerpo de `POST /api/usuarios/<id>/restablecer-contrasena/`. */
export interface RestablecerContrasena {
  nueva_contrasena: string;
  confirmar_contrasena: string;
}

/** Cuerpo de `POST /api/usuarios/<id>/desbloquear/`. */
export interface Desbloquear {
  motivo?: string;
}

/**
 * Los tres formatos de error que devuelve el backend del CU3, ya
 * normalizados a la misma forma.
 *
 * El backend responde con tres estructuras distintas y la UI tiene que
 * saber cuál llegó: las guardas de negocio usan `{"error": "texto"}`, la
 * contraseña débil usa `{"error": ["texto"]}` y la validación de campo
 * usa `{"campo": ["texto"]}`. `erroresApi.ts` las aplana a esta forma
 * para que los componentes no tengan que ramificar por el formato.
 */
export interface ErrorNormalizado {
  /** Mensaje para mostrar arriba del formulario. `null` si no hay. */
  mensaje: string | null;
  /** Error por campo, para pegar debajo del input. `{}` si no hay. */
  campos: Record<string, string[]>;
  /** `Retry-After` en segundos, cuando el backend fue un 429. */
  retryAfter?: number;
}
