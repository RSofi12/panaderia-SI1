/**
 * Clases de estilo compartidas para el módulo de Roles y Matriz de Permisos (CU4).
 * Modularizado para cumplir con Fast Refresh de Vite (react-refresh/only-export-components).
 */

export const estilosRoles = {
  // Contenedores y tarjetas
  tarjeta:
    'group relative flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-xs transition-all duration-200 hover:border-amber-400 hover:shadow-md hover:-translate-y-0.5',
  tarjetaHeader: 'flex items-start justify-between gap-3 mb-3',
  tarjetaTitulo: 'text-base font-bold tracking-tight text-slate-900 flex items-center gap-2',
  tarjetaDesc: 'text-xs text-slate-600 line-clamp-2 leading-relaxed mb-4 min-h-[2rem]',

  // Badges e insignias
  badgeProtegido:
    'inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold text-amber-900 border border-amber-200/90 shadow-2xs',
  badgePersonalizado:
    'inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-700 border border-slate-200',
  badgeMetrica:
    'inline-flex items-center gap-1.5 rounded-xl bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 border border-slate-200/70',

  // Barra de progreso de permisos
  barraProgresoFondo: 'h-2 w-full overflow-hidden rounded-full bg-slate-100',
  barraProgresoRelleno: 'h-full rounded-full bg-gradient-to-r from-amber-500 to-amber-600 transition-all duration-300',

  // Botones de acción
  botonConfigurar:
    'inline-flex min-h-10 items-center justify-center gap-2 rounded-xl bg-amber-600 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all duration-150 hover:bg-amber-700 active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 cursor-pointer flex-1',
  botonEditar:
    'inline-flex min-h-10 items-center justify-center rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition-all duration-150 hover:bg-slate-50 hover:border-slate-400 active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 cursor-pointer',

  // Matriz de permisos
  seccionModulo: 'rounded-2xl border border-slate-200/90 bg-slate-50/60 p-4 transition-colors',
  seccionModuloHeader: 'flex items-center justify-between pb-3 mb-3 border-b border-slate-200/80',
  seccionModuloTitulo: 'text-sm font-bold text-slate-900 flex items-center gap-2',
  itemPermiso:
    'group/item relative flex items-start gap-3 rounded-xl border border-slate-200/90 bg-white p-3.5 transition-all duration-150 hover:border-amber-300 hover:shadow-2xs has-[:checked]:border-amber-500 has-[:checked]:bg-amber-50/40 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-amber-500',
  checkboxPermiso:
    'h-4 w-4 rounded-md border-slate-300 text-amber-600 focus:ring-amber-500 focus:ring-offset-1 mt-0.5 cursor-pointer disabled:cursor-not-allowed',
} as const;
