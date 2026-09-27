import React from 'react';
import { Menu } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import UserAvatar from './UserAvatar';

interface TopbarProps {
  title: string;
  onOpenSidebar: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ title, onOpenSidebar }) => {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur-sm">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onOpenSidebar}
            aria-label="Abrir menú de navegación"
            className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 cursor-pointer lg:hidden"
          >
            <Menu className="w-5 h-5" />
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
