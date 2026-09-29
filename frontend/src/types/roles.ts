/* ------------------------------------------------------------------ *
 * CU4 - Tipos de Roles y Matriz de Permisos
 * ------------------------------------------------------------------ *
 *
 * Contratos de datos TypeScript para la gestión de roles y la matriz de
 * asignación de permisos según el backend de Django REST Framework.
 */

/** Permiso individual devuelto por el catálogo del backend. */
export interface Permiso {
  id_permiso: number;
  nombre: string;
  descripcion: string;
  modulo: string;
  modulo_display: string;
}

/** Grupo de permisos clasificados por paquete del backend. */
export interface GrupoModuloPermisos {
  modulo: string;
  modulo_display: string;
  permisos: Permiso[];
}

/** Elemento del listado general de roles. */
export interface RolListado {
  id_rol: number;
  nombre: string;
  descripcion: string | null;
  total_permisos: number;
  total_usuarios: number;
  es_protegido: boolean;
}

/** Detalle completo de un rol con su lista de permisos asignados. */
export interface RolDetalle {
  id_rol: number;
  nombre: string;
  descripcion: string | null;
  es_protegido: boolean;
  total_permisos: number;
  total_usuarios: number;
  permisos: Permiso[];
}

/** Datos requeridos para dar de alta un nuevo rol. */
export interface CrearRol {
  nombre: string;
  descripcion?: string | null;
}

/** Datos para modificar un rol existente. */
export interface EditarRol {
  nombre?: string;
  descripcion?: string | null;
}

/** Payload para el reemplazo completo de la matriz de permisos. */
export interface MatrizPayload {
  permisos: number[];
}
