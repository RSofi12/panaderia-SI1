/* ------------------------------------------------------------------ *
 * CU4 - Servicio de Roles y Permisos
 * ------------------------------------------------------------------ *
 *
 * Cliente HTTP que encapsula las llamadas a los endpoints /api/roles/ y
 * /api/permisos/. Desenvuelve response.data y propaga las excepciones de
 * Axios para que la vista las normalice con `normalizarErrorApi`.
 */

import api from './api';
import type {
  CrearRol,
  EditarRol,
  GrupoModuloPermisos,
  MatrizPayload,
  Permiso,
  RolDetalle,
  RolListado,
} from '../types/roles';

export const rolesService = {
  /** Obtiene la lista completa de roles con sus métricas. */
  async getRoles(): Promise<RolListado[]> {
    const respuesta = await api.get<RolListado[]>('/roles/');
    return respuesta.data;
  },

  /** Obtiene el detalle de un rol específico con su lista de permisos. */
  async getRol(id: number): Promise<RolDetalle> {
    const respuesta = await api.get<RolDetalle>(`/roles/${id}/`);
    return respuesta.data;
  },

  /** Da de alta un nuevo rol. */
  async crearRol(datos: CrearRol): Promise<RolDetalle> {
    const respuesta = await api.post<RolDetalle>('/roles/', datos);
    return respuesta.data;
  },

  /** Modifica la descripción (o nombre si no es protegido) de un rol. */
  async editarRol(id: number, datos: EditarRol): Promise<RolDetalle> {
    const respuesta = await api.patch<RolDetalle>(`/roles/${id}/`, datos);
    return respuesta.data;
  },

  /** Reemplaza en bloque la matriz de permisos de un rol. */
  async actualizarMatriz(id: number, permisosIds: number[]): Promise<RolDetalle> {
    const payload: MatrizPayload = { permisos: permisosIds };
    const respuesta = await api.put<RolDetalle>(`/roles/${id}/permisos/`, payload);
    return respuesta.data;
  },

  /** Obtiene el catálogo completo de permisos clasificados por módulo. */
  async getPermisosAgrupados(): Promise<GrupoModuloPermisos[]> {
    const respuesta = await api.get<GrupoModuloPermisos[]>('/permisos/agrupados/');
    return respuesta.data;
  },

  /** Obtiene el catálogo plano de permisos. */
  async getPermisos(): Promise<Permiso[]> {
    const respuesta = await api.get<Permiso[]>('/permisos/');
    return respuesta.data;
  },
};

export default rolesService;
