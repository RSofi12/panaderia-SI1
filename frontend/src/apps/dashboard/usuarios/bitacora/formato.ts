import type { RegistroBitacora } from '../../../../types/bitacora';

const formatoFechaHora = new Intl.DateTimeFormat('es-BO', {
  dateStyle: 'medium',
  timeStyle: 'medium',
});

export const formatearFechaHora = (iso: string): string => formatoFechaHora.format(new Date(iso));

/** Nombre visible de cada `tabla_afectada` que hoy escribe el backend. */
const NOMBRES_MODULO: Record<string, string> = {
  usuario: 'Usuarios',
  rol: 'Roles',
  rol_permiso: 'Roles y permisos',
  token_recuperacion: 'Recuperación de contraseña',
  producto: 'Productos',
  proveedor: 'Proveedores',
};

export const nombreModulo = (tabla: string | null): string => {
  if (!tabla) return 'General';
  return NOMBRES_MODULO[tabla] ?? tabla.charAt(0).toUpperCase() + tabla.slice(1).replace(/_/g, ' ');
};

/** Quién hizo la acción. Un intento fallido no tiene usuario, pero sí el nombre que se digitó. */
export const autorRegistro = (registro: RegistroBitacora): string => {
  if (registro.nombre_completo) return registro.nombre_completo;
  if (registro.nombre_usuario_intento) return `Sin sesión · intentó "${registro.nombre_usuario_intento}"`;
  return 'Sistema';
};

const ACCION_DE_RIESGO = /FALLIDO|BLOQUEADO|DENEGADO|INVALIDADA/;

/** Color del distintivo según el tipo de acción, para leer la tabla de un vistazo. */
export const clasesAccion = (accion: string): string => {
  if (ACCION_DE_RIESGO.test(accion)) return 'bg-red-50 text-red-700 ring-red-200';
  if (accion.startsWith('ALTA_')) return 'bg-emerald-50 text-emerald-700 ring-emerald-200';
  if (accion.startsWith('EDICION_') || accion.startsWith('ACTUALIZACION_') || accion.startsWith('ASIGNAR_')) {
    return 'bg-amber-50 text-amber-800 ring-amber-200';
  }
  if (accion.includes('SESION')) return 'bg-sky-50 text-sky-700 ring-sky-200';
  return 'bg-slate-100 text-slate-700 ring-slate-200';
};
