import React from 'react';
import { Menu } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import UserAvatar from './UserAvatar';

interface TopbarProps {
  title: string;
  menuAbierto: boolean;
  onAlternarMenu: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ title, menuAbierto, onAlternarMenu }) => {
  const { user } = useAuth();

  if (!user) return null;

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
          <h1 className="truncate text-base font-bold text-slate-900 sm:text-lg">{title}</h1>
        </div>

        <div className="flex items-center gap-3">
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
        </div>
      </div>
    </header>
  );
};

export default Topbar;
