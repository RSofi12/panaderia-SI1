/** Un registro de auditoría tal como lo devuelve `GET /api/bitacora/` (CU26). */
export interface RegistroBitacora {
  id_bitacora: number;
  /** `null` en intentos de acceso sin sesión (login fallido, bloqueo). */
  id_usuario: number | null;
  nombre_usuario: string | null;
  nombre_completo: string | null;
  /** Nombre digitado en un intento fallido, cuando no hay usuario. */
  nombre_usuario_intento: string | null;
  accion: string;
  accion_etiqueta: string;
  tabla_afectada: string | null;
  descripcion: string | null;
  agente_usuario: string | null;
  fecha_hora: string;
}

export interface OpcionAccion {
  valor: string;
  etiqueta: string;
}

export interface UsuarioConRegistros {
  id_usuario: number;
  nombre_usuario: string;
  nombre_completo: string;
}

/** Valores para los desplegables de filtros (`GET /api/bitacora/opciones/`). */
export interface OpcionesBitacora {
  acciones: OpcionAccion[];
  modulos: string[];
  usuarios: UsuarioConRegistros[];
}

/** Filtros que acepta `GET /api/bitacora/`. Fechas en formato AAAA-MM-DD. */
export interface FiltrosBitacora {
  page?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
  usuario?: string;
  modulo?: string;
  accion?: string;
  q?: string;
}
