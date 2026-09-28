/* ------------------------------------------------------------------ *
 * Estilos compartidos de los formularios del CU3
 * ------------------------------------------------------------------ *
 *
 * POR QUÉ NO ESTÁN EN `CampoFormulario.tsx`
 * Estaban, y el linter lo marcaba con `react-refresh/only-export-components`:
 * un archivo que exporta un componente y además funciones sueltas hace que
 * el Fast Refresh de Vite recargue la página entera en vez de intercambiar
 * el componente, y en desarrollo eso se siente como un parpadeo cada vez que
 * se toca el formulario.
 *
 * No es un error de estilo: es una regla de Vite sobre cómo se recargan los
 * módulos. Separar es la solución que la propia herramienta pide.
 */

const BASE =
  'w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:bg-slate-50 disabled:text-slate-400';

const CON_ERROR = 'border-red-300 focus:border-red-500 focus:ring-red-200';
const SIN_ERROR = 'border-slate-300 focus:border-amber-600 focus:ring-amber-200';

/** Clases de un input, con el borde en rojo cuando el campo es inválido. */
export const claseInput = (conError: boolean): string =>
  `${BASE} ${conError ? CON_ERROR : SIN_ERROR}`;

/** El `textarea` del motivo de inactivación. Mismo aspecto que los inputs. */
export const CLASE_TEXTAREA =
  'w-full resize-none rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:border-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-200 disabled:bg-slate-50';
