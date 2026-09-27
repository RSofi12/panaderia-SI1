import React from 'react';
import { CheckCircle2, Clock, Construction, KeyRound } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { NAV_MODULES } from './navigation';
import UserAvatar from './components/UserAvatar';

export const DashboardHome: React.FC = () => {
  const { user, hasPermission } = useAuth();

  if (!user) return null;

  const modulosHabilitados = NAV_MODULES.filter((modulo) =>
    modulo.permisos.some((permiso) => hasPermission(permiso))
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <section className="overflow-hidden rounded-2xl border border-amber-100 bg-gradient-to-br from-amber-600 via-amber-700 to-amber-800 shadow-sm">
        <div className="flex flex-col items-center gap-5 p-6 text-center sm:flex-row sm:p-8 sm:text-left">
          <div className="rounded-full bg-white/15 p-1.5 backdrop-blur-sm">
            <UserAvatar usuario={user} size="lg" className="ring-4 ring-white/25" />
          </div>

          <div className="min-w-0 flex-1">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-[11px] font-semibold text-amber-50">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Sesión iniciada (CU1)
            </span>

            <h2 className="mt-2.5 text-2xl font-bold tracking-tight text-white sm:text-3xl">
              ¡Bienvenido/a, {user.nombre_completo}!
            </h2>

            <p className="mt-1 text-sm text-amber-100">
              Ingresaste como{' '}
              <span className="font-semibold text-white">{user.rol}</span> con el usuario{' '}
              <span className="font-mono">@{user.nombre_usuario}</span>. El inicio y el cierre de
              esta sesión quedaron registrados en la bitácora (CU26).
            </p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-3 flex w-10 h-10 items-center justify-center rounded-xl bg-amber-50 text-amber-700">
            <Construction className="w-5 h-5" />
          </div>
          <p className="text-xs font-medium text-slate-500">Módulos disponibles para tu rol</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{modulosHabilitados.length}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-3 flex w-10 h-10 items-center justify-center rounded-xl bg-amber-50 text-amber-700">
            <KeyRound className="w-5 h-5" />
          </div>
          <p className="text-xs font-medium text-slate-500">Permisos asignados</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{user.permisos?.length ?? 0}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-3 flex w-10 h-10 items-center justify-center rounded-xl bg-amber-50 text-amber-700">
            <Clock className="w-5 h-5" />
          </div>
          <p className="text-xs font-medium text-slate-500">Ciclo PUDS en curso</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">Ciclo 1</p>
        </div>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="text-sm font-bold text-slate-900">Tus módulos</h3>
        <p className="mt-1 text-xs text-slate-500">
          Esta es la misma vista que ve el resto de actores. Lo único que cambia según tu rol es
          qué módulos quedan habilitados.
        </p>

        <ul className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {modulosHabilitados.map((modulo) => (
            <li
              key={modulo.to}
              className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50/60 px-4 py-3"
            >
              <modulo.icon className="w-5 h-5 shrink-0 text-slate-400" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-slate-700">{modulo.label}</p>
                <p className="truncate text-[11px] text-slate-400">{modulo.casosDeUso}</p>
              </div>
              <span className="shrink-0 rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                Próximamente
              </span>
            </li>
          ))}

          {modulosHabilitados.length === 0 && (
            <li className="rounded-xl border border-dashed border-slate-200 px-4 py-6 text-center text-xs text-slate-400 sm:col-span-2">
              Tu rol todavía no tiene módulos habilitados.
            </li>
          )}
        </ul>
      </section>
    </div>
  );
};

export default DashboardHome;
