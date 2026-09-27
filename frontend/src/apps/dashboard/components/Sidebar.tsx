import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, LogOut, PackageOpen } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import circleLogo from '../../../assets/circle-logo-panaderia.svg';
import { NAV_MODULES } from '../navigation';
import UserAvatar from './UserAvatar';

interface SidebarProps {
  open: boolean;
  onNavigate: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ open, onNavigate }) => {
  const { user, logout, hasPermission } = useAuth();

  if (!user) return null;

  // Ventanas que este actor puede ver (filtro RBAC) y que ya tienen pantalla.
  const ventanasVisibles = NAV_MODULES.filter(
    (modulo) => modulo.implemented && modulo.permisos.some((permiso) => hasPermission(permiso))
  );

  const cerrarSesion = async () => {
    onNavigate();
    await logout();
  };

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/50 lg:hidden"
          onClick={onNavigate}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-slate-200 bg-white transition-transform duration-200 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-4">
          <img
            src={circleLogo}
            alt="Logo Panadería Santiago"
            className="w-10 h-10 rounded-full border border-amber-200 object-contain"
          />
          <div className="min-w-0">
            <p className="truncate text-sm font-bold text-slate-900 leading-tight">
              Panadería Santiago
            </p>
            <p className="text-[11px] font-medium text-amber-700">Panel Administrativo</p>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Módulos del sistema">
          <NavLink
            to="/dashboard"
            end
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-amber-50 text-amber-800'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            <LayoutDashboard className="w-5 h-5 shrink-0" />
            Inicio
          </NavLink>

          {ventanasVisibles.length > 0 && (
            <>
              <p className="mt-6 mb-2 px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Módulos
              </p>
              <ul className="space-y-1">
                {ventanasVisibles.map((modulo) => (
                  <li key={modulo.to}>
                    <NavLink
                      to={modulo.to}
                      onClick={onNavigate}
                      className={({ isActive }) =>
                        `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                          isActive
                            ? 'bg-amber-50 text-amber-800'
                            : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                        }`
                      }
                    >
                      <modulo.icon className="w-5 h-5 shrink-0" />
                      <span className="truncate">{modulo.label}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </>
          )}

          {ventanasVisibles.length === 0 && (
            <div className="mt-6 rounded-xl border border-dashed border-slate-200 px-4 py-6 text-center">
              <PackageOpen className="w-6 h-6 mx-auto mb-2 text-slate-300" />
              <p className="text-xs font-medium text-slate-500">Sin módulos habilitados</p>
              <p className="mt-1 text-[11px] text-slate-400">
                Las ventanas se habilitan a medida que se implementen los casos de uso.
              </p>
            </div>
          )}
        </nav>

        <div className="border-t border-slate-100 p-3">
          <div className="flex items-center gap-3 rounded-xl px-2 py-2">
            <UserAvatar usuario={user} size="sm" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-slate-900">
                {user.nombre_completo}
              </p>
              <p className="truncate text-[11px] font-medium text-amber-700">{user.rol}</p>
            </div>
            <button
              type="button"
              onClick={cerrarSesion}
              title="Cerrar sesión"
              aria-label="Cerrar sesión"
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600 cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
