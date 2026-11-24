import React, { useEffect, useRef, useState } from 'react';
import { ChevronDown, LogOut, Menu, Shield } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import UserAvatar from './UserAvatar';

interface TopbarProps {
  title: string;
  menuAbierto: boolean;
  onAlternarMenu: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ title, menuAbierto, onAlternarMenu }) => {
  const { user, logout } = useAuth();
  const [dropdownAbierto, setDropdownAbierto] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Cerrar al hacer clic fuera
  useEffect(() => {
    const alClicFuera = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setDropdownAbierto(false);
      }
    };
    const alPresionarEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDropdownAbierto(false);
    };

    if (dropdownAbierto) {
      document.addEventListener('mousedown', alClicFuera);
      document.addEventListener('keydown', alPresionarEscape);
    }
    return () => {
      document.removeEventListener('mousedown', alClicFuera);
      document.removeEventListener('keydown', alPresionarEscape);
    };
  }, [dropdownAbierto]);

  if (!user) return null;

  const cerrarSesion = async () => {
    setDropdownAbierto(false);
    await logout();
  };

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur-sm">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onAlternarMenu}
            aria-expanded={menuAbierto}
            aria-controls="menu-lateral"
            aria-label={menuAbierto ? 'Cerrar menú de navegación' : 'Abrir menú de navegación'}
            className="inline-flex h-11 w-11 items-center justify-center rounded-xl text-[#2b1a10] transition-colors hover:bg-amber-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-200 cursor-pointer"
          >
            <Menu className="h-5 w-5" />
          </button>
          <h1 className="font-sugo truncate text-lg font-normal tracking-wide text-slate-900 sm:text-xl">{title}</h1>
        </div>

        {/* Dropdown de Usuario */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setDropdownAbierto((prev) => !prev)}
            aria-expanded={dropdownAbierto}
            aria-haspopup="true"
            className="flex items-center gap-3 rounded-2xl p-1.5 transition-all duration-200 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300 cursor-pointer"
          >
            <div className="hidden text-right sm:block">
              <p className="text-sm font-semibold text-slate-900 leading-tight">
                {user.nombre_completo}
              </p>
              <p className="text-xs text-slate-500">
                @{user.nombre_usuario} ·{' '}
                <span className="font-semibold text-amber-700">{user.rol}</span>
              </p>
            </div>
            <UserAvatar usuario={user} />
            <ChevronDown
              className={`h-4 w-4 text-slate-400 transition-transform duration-200 ${
                dropdownAbierto ? 'rotate-180' : ''
              }`}
            />
          </button>

          {/* Menú Flotante con transición fluida */}
          <div
            className={`absolute right-0 mt-2 w-72 origin-top-right rounded-2xl border border-slate-200/90 bg-white p-2.5 shadow-xl ring-1 ring-black/5 z-50 transition-all duration-200 ease-out motion-reduce:transition-none ${
              dropdownAbierto
                ? 'opacity-100 scale-100 translate-y-0 pointer-events-auto'
                : 'opacity-0 scale-95 -translate-y-2 pointer-events-none'
            }`}
          >
            {/* Encabezado con datos del usuario */}
            <div className="flex items-center gap-3 border-b border-slate-100 p-2.5 pb-3">
              <UserAvatar usuario={user} size="md" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-bold text-slate-900 leading-tight">
                  {user.nombre_completo}
                </p>
                <p className="truncate text-[11px] text-slate-500">
                  @{user.nombre_usuario}
                </p>
                <span className="mt-1 inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-800 border border-amber-200/60">
                  <Shield className="h-3 w-3" />
                  {user.rol}
                </span>
              </div>
            </div>

            {/* Acciones */}
            <div className="pt-2">
              <button
                type="button"
                onClick={cerrarSesion}
                className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-rose-700 transition-colors hover:bg-rose-50 cursor-pointer"
              >
                <LogOut className="h-4 w-4" />
                Cerrar sesión
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
