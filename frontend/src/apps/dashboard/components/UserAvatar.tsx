import React from 'react';
import type { Usuario } from '../../../types/auth';

type Size = 'sm' | 'md' | 'lg';

const SIZES: Record<Size, { box: string; text: string }> = {
  sm: { box: 'w-8 h-8', text: 'text-[11px]' },
  md: { box: 'w-10 h-10', text: 'text-sm' },
  lg: { box: 'w-20 h-20', text: 'text-2xl' },
};

const ROL_STYLES: Record<string, string> = {
  Administrador: 'bg-amber-100 text-amber-800 ring-amber-200',
  Propietario: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
  'Personal de Ventas': 'bg-sky-100 text-sky-800 ring-sky-200',
  'Personal de Producción': 'bg-orange-100 text-orange-800 ring-orange-200',
};

const FALLBACK_STYLE = 'bg-slate-100 text-slate-700 ring-slate-200';

const getIniciales = (nombre: string): string =>
  nombre
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((parte) => parte.charAt(0).toUpperCase())
    .join('');

interface UserAvatarProps {
  usuario: Pick<Usuario, 'nombre_completo' | 'rol'>;
  size?: Size;
  className?: string;
}

/**
 * El modelo `usuario` no expone un campo de imagen, así que el avatar se
 * construye con las iniciales y se colorea según el rol del actor.
 */
export const UserAvatar: React.FC<UserAvatarProps> = ({ usuario, size = 'md', className = '' }) => {
  const dimensiones = SIZES[size];
  const paleta = ROL_STYLES[usuario.rol] ?? FALLBACK_STYLE;

  return (
    <div
      role="img"
      aria-label={`Avatar de ${usuario.nombre_completo}`}
      className={`${dimensiones.box} ${dimensiones.text} ${paleta} shrink-0 rounded-full ring-2 flex items-center justify-center font-bold select-none ${className}`}
    >
      {getIniciales(usuario.nombre_completo)}
    </div>
  );
};

export default UserAvatar;
