/* ------------------------------------------------------------------ *
 * CU3 - Servicio de gestión de usuarios
 * ------------------------------------------------------------------ *
 *
 * POR QUÉ UN SERVICIO Y NO LLAMAR A `api` DESDE LOS COMPONENTES
 * Por la misma razón que existe `authService.ts`: los componentes
 * describen una pantalla, no conocen rutas. Si `UsuariosPage` escribiera
 * `api.patch('/usuarios/7/toggle-activo/')`, el día que el backend
 * renombre la acción habría que buscarla dentro de un componente de
 * React, que es el peor sitio posible para una cadena de API.
 *
 * Cada función devuelve `response.data` ya desenvuelto. Quien llama no
 * debería tener que acordarse de que axios anida todo bajo `.data`.
 *
 * NADA DE ESTE ARCHIVO LANZA ERRORES NORMALIZADOS. Devuelve la promesa
 * de axios y deja que la pantalla llame a `normalizarErrorApi`. Quien
 * atrapa la excepción decide qué pintar, y el mensaje crudo de axios
 * ("Request failed with status code 400") no dice nada al usuario.
 */

import api from './api';
import type {
  AltaUsuario,
  CambioEstado,
  Desbloquear,
  EditarUsuario,
  FiltrosUsuarios,
  Paginado,
  RestablecerContrasena,
  RolSimple,
  UsuarioFila,
} from '../types/usuarios';

/** Respuesta de los endpoints que solo confirman con un texto. */
export interface MensajeOperacion {
  message: string;
}

/**
 * Quita los parámetros vacíos antes de mandarlos.
 *
 * Sin esto, el buscador mandaría `search=` con la cadena vacía y el
 * backend respondería TODAS las filas en vez de ninguna... que es lo
 * mismo, pero el detalle importante es el otro: mandar `activo: undefined`
 * llega como la cadena `"undefined"` en el query string, y
 * `activo=undefined` no es `true` ni `false`, así que el filtro del
 * backend lo rechaza. Es un bug que solo aparece con el campo vacío.
 */
const limpiar = (filtros: FiltrosUsuarios): Record<string, string> => {
  const limpio: Record<string, string> = {};

  if (filtros.search?.trim()) limpio.search = filtros.search.trim();
  if (filtros.activo !== undefined) limpio.activo = filtros.activo ? 'true' : 'false';
  if (filtros.id_rol !== undefined) limpio.id_rol = String(filtros.id_rol);
  if (filtros.ordering) limpio.ordering = filtros.ordering;
  if (filtros.page !== undefined && filtros.page > 1) limpio.page = String(filtros.page);

  return limpio;
};

export const usuariosService = {
  /**
   * `GET /api/usuarios/` — listado paginado, buscable y filtrable.
   *
   * `search` usa `icontains` en el backend, y en PostgreSQL eso NO
   * ignora acentos: buscar "Maria" no encuentra "María". Es una
   * limitación conocida del filtro, no un bug de esta pantalla, y está
   * documentado en `DECISIONS_LOG.md`.
   */
  async listar(filtros: FiltrosUsuarios = {}): Promise<Paginado<UsuarioFila>> {
    const response = await api.get<Paginado<UsuarioFila>>('/usuarios/', {
      params: limpiar(filtros),
    });
    return response.data;
  },

  /** `GET /api/usuarios/roles/` — para el desplegable. NO viene paginado. */
  async listarRoles(): Promise<RolSimple[]> {
    const response = await api.get<RolSimple[]>('/usuarios/roles/');
    return response.data;
  },

  /** `GET /api/usuarios/<id>/` */
  async obtener(id: number): Promise<UsuarioFila> {
    const response = await api.get<UsuarioFila>(`/usuarios/${id}/`);
    return response.data;
  },

  /** `POST /api/usuarios/` — alta de cuenta. */
  async crear(datos: AltaUsuario): Promise<UsuarioFila> {
    const response = await api.post<UsuarioFila>('/usuarios/', datos);
    return response.data;
  },

  /**
   * `PUT` / `PATCH /api/usuarios/<id>/` — edición.
   *
   * Se usa siempre PATCH aunque se manden todos los campos: el backend
   * lo declara con `partial=True`, y PATCH con el cuerpo completo
   * produce el mismo resultado sin depender de que el servidor siga
   * aceptando PUT. Es además la operación que el CU3 describe, "editar
   * los datos de la cuenta".
   */
  async editar(id: number, datos: EditarUsuario): Promise<UsuarioFila> {
    const response = await api.patch<UsuarioFila>(`/usuarios/${id}/`, datos);
    return response.data;
  },

  /**
   * `PATCH /api/usuarios/<id>/toggle-activo/` — activar / inactivar.
   *
   * Devuelve la fila ya actualizada, no un texto de confirmación, para
   * que la tabla pueda refrescar la fila sin volver a pedir la página
   * entera. Un POST de inactivación que devuelve un booleano obligaría a
   * la UI a adivinar el nuevo estado, y adivinar es cómo una tabla
   * termina mostrando un "Activo" sobre una cuenta inactivada.
   */
  async cambiarEstado(id: number, datos: CambioEstado): Promise<UsuarioFila> {
    const response = await api.patch<UsuarioFila>(`/usuarios/${id}/toggle-activo/`, datos);
    return response.data;
  },

  /**
   * `POST /api/usuarios/<id>/restablecer-contrasena/` — extensión.
   *
   * El backend responde con un texto, no con la fila, porque la cuenta
   * no cambió: solo su clave. La UI tiene que recargar la fila aparte si
   * quiere reflejar algo, y normalmente no quiere, porque la tabla no
   * muestra contraseñas.
   */
  async restablecerContrasena(
    id: number,
    datos: RestablecerContrasena
  ): Promise<MensajeOperacion> {
    const response = await api.post<MensajeOperacion>(
      `/usuarios/${id}/restablecer-contrasena/`,
      datos
    );
    return response.data;
  },

  /**
   * `POST /api/usuarios/<id>/desbloquear/` — extensión.
   *
   * Devuelve un texto, igual que el reset. La fila de la tabla sí
   * cambia: `esta_bloqueado` pasa a `false` y
   * `minutos_bloqueo_restantes` a `0`. Por eso `UsuariosPage` actualiza
   * la fila localmente después de llamar a esta función, en vez de
   * recargar la página entera: el servidor no manda el estado nuevo.
   */
  async desbloquear(id: number, datos: Desbloquear = {}): Promise<MensajeOperacion> {
    const response = await api.post<MensajeOperacion>(`/usuarios/${id}/desbloquear/`, datos);
    return response.data;
  },
};

export default usuariosService;
