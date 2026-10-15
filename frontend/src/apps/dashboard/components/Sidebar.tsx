import React, { useEffect, useId, useRef, useState } from 'react';
import type { ElementType } from 'react';
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

interface Pista {
  texto: string;
  top: number;
}

function useEscritorio() {
  const [esEscritorio, setEsEscritorio] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches,
  );

  useEffect(() => {
    const consulta = window.matchMedia('(min-width: 1024px)');
    const actualizar = () => setEsEscritorio(consulta.matches);
    actualizar();
    consulta.addEventListener('change', actualizar);
    return () => consulta.removeEventListener('change', actualizar);
  }, []);

  return esEscritorio;
}

/**
 * Enlace del menú. El nombre vive en el botón; la pista flotante la pinta
 * el menú, fuera del recorte, para que no la corte el ancho del riel.
 */
function EnlaceMenu({
  to,
  end,
  icon: Icono,
  etiqueta,
  orden,
  expandido,
  onClick,
  onPista,
  onSoltarPista,
}: {
  to: string;
  end?: boolean;
  icon: ElementType;
  etiqueta: string;
  orden: number;
  expandido: boolean;
  onClick: () => void;
  onPista: (evento: React.SyntheticEvent<HTMLElement>, texto: string) => void;
  onSoltarPista: () => void;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onClick}
      aria-label={etiqueta}
      onMouseEnter={(evento) => onPista(evento, etiqueta)}
      onFocus={(evento) => onPista(evento, etiqueta)}
      onMouseLeave={onSoltarPista}
      onBlur={onSoltarPista}
      style={{ animationDelay: `${orden * 45}ms` }}
      className={({ isActive }) =>
        `mostrador-aparecer group flex min-h-11 items-center rounded-xl text-sm font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300/40 ${
          expandido ? 'gap-3 px-3' : 'justify-center px-2'
        } ${
          isActive
            ? 'bg-amber-600 font-bold text-white shadow-xs ring-1 ring-amber-400/40'
            : 'text-amber-100/85 hover:bg-[#2c1d14] hover:text-white'
        }`
      }
    >
      <Icono className="h-5 w-5 shrink-0 transition-transform duration-200 group-hover:translate-x-0.5 motion-reduce:transition-none" />
      <span
        className={`overflow-hidden whitespace-nowrap transition-[max-width,opacity] duration-300 ease-out motion-reduce:transition-none ${
          expandido ? 'max-w-56 opacity-100' : 'max-w-0 opacity-0'
        }`}
      >
        {etiqueta}
      </span>
    </NavLink>
  );
}

export const Sidebar: React.FC<SidebarProps> = ({ open, onNavigate }) => {
  const { user, logout, hasPermission } = useAuth();
  const esEscritorio = useEscritorio();
  const expandido = open || !esEscritorio;
  const cajonAbierto = open && !esEscritorio;
  const tituloId = useId();
  const marcoRef = useRef<HTMLDivElement>(null);
  const cajonRef = useRef<HTMLElement>(null);
  const [pista, setPista] = useState<Pista | null>(null);

  useEffect(() => {
    if (!cajonAbierto) return;
    const focoAnterior = document.activeElement;
    cajonRef.current?.querySelector<HTMLElement>('a[href]')?.focus();
    const overflowAnterior = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const alPresionar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') {
        onNavigate();
        return;
      }
      if (evento.key !== 'Tab' || !cajonRef.current) return;
      const focables = cajonRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled])',
      );
      if (focables.length === 0) return;
      const primero = focables[0];
      const ultimo = focables[focables.length - 1];
      if (evento.shiftKey && document.activeElement === primero) {
        evento.preventDefault();
        ultimo.focus();
      } else if (!evento.shiftKey && document.activeElement === ultimo) {
        evento.preventDefault();
        primero.focus();
      }
    };
    window.addEventListener('keydown', alPresionar);
    return () => {
      document.body.style.overflow = overflowAnterior;
      window.removeEventListener('keydown', alPresionar);
      if (focoAnterior instanceof HTMLElement) focoAnterior.focus();
    };
  }, [cajonAbierto, onNavigate]);

  useEffect(() => {
    if (!open || !esEscritorio) return;
    const alPresionar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') onNavigate();
    };
    window.addEventListener('keydown', alPresionar);
    return () => window.removeEventListener('keydown', alPresionar);
  }, [open, esEscritorio, onNavigate]);

  if (!user) return null;

  const ventanasVisibles = NAV_MODULES.filter(
    (modulo) => modulo.implemented && modulo.permisos.some((permiso) => hasPermission(permiso))
  );

  const alElegirModulo = () => {
    if (!esEscritorio) onNavigate();
  };

  const mostrarPista = (evento: React.SyntheticEvent<HTMLElement>, texto: string) => {
    if (expandido || !marcoRef.current) return;
    const marco = marcoRef.current.getBoundingClientRect();
    const item = evento.currentTarget.getBoundingClientRect();
    setPista({ texto, top: item.top - marco.top + item.height / 2 });
  };

  const soltarPista = () => setPista(null);

  const cerrarSesion = async () => {
    if (!esEscritorio) onNavigate();
    await logout();
  };

  return (
    <>
      {cajonAbierto && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-[#1c120c]/45 lg:hidden"
          aria-label="Cerrar menú"
          onClick={onNavigate}
        />
      )}

      <div
        ref={marcoRef}
        className={`fixed inset-y-0 left-0 z-40 transition-[transform,width] duration-300 ease-out motion-reduce:transition-none ${
          open
            ? 'w-[min(18rem,calc(100vw-2.5rem))] translate-x-0 lg:w-72'
            : 'w-[min(18rem,calc(100vw-2.5rem))] -translate-x-full lg:w-[4.5rem] lg:translate-x-0'
        }`}
      >
        <aside
          ref={cajonRef}
          id="menu-lateral"
          role={cajonAbierto ? 'dialog' : undefined}
          aria-modal={cajonAbierto ? true : undefined}
          aria-labelledby={tituloId}
          inert={!open && !esEscritorio}
          className="flex h-full w-full flex-col overflow-hidden border-r border-[#2e1d13] bg-[#1c120c] text-white shadow-2xl"
        >
          <div
            className={`flex items-center border-b border-[#2e1d13] py-4 ${
              expandido ? 'gap-3 px-4' : 'justify-center px-2'
            }`}
          >
            <div className="shrink-0 rounded-full bg-white p-0.5 shadow-xs">
              <img
                src={circleLogo}
                alt=""
                className="h-10 w-10 rounded-full object-contain"
              />
            </div>
            <div
              className={`min-w-0 overflow-hidden transition-[max-width,opacity] duration-300 ease-out motion-reduce:transition-none ${
                expandido ? 'max-w-48 flex-1 opacity-100' : 'max-w-0 opacity-0'
              }`}
            >
              <p id={tituloId} className="truncate text-sm font-bold leading-tight text-white">
                Panadería Santiago
              </p>
              <p className="text-[11px] font-medium text-amber-300/90">Panel Administrativo</p>
            </div>
          </div>

          <nav
            className={`flex-1 px-2 py-4 ${expandido ? 'overflow-y-auto' : 'overflow-hidden'}`}
            aria-label="Módulos del sistema"
          >
            <EnlaceMenu
              to="/dashboard"
              end
              icon={LayoutDashboard}
              etiqueta="Inicio"
              orden={0}
              expandido={expandido}
              onClick={alElegirModulo}
              onPista={mostrarPista}
              onSoltarPista={soltarPista}
            />

            {ventanasVisibles.length > 0 && (
              <>
                <p
                  className={`overflow-hidden px-3 text-[10px] font-bold uppercase tracking-wider text-amber-400/80 transition-[max-height,margin,opacity] duration-300 motion-reduce:transition-none ${
                    expandido ? 'mt-6 mb-2 max-h-6 opacity-100' : 'mt-3 mb-0 max-h-0 opacity-0'
                  }`}
                >
                  Módulos
                </p>
                <ul className="space-y-1">
                  {ventanasVisibles.map((modulo, indice) => (
                    <li key={modulo.to}>
                      <EnlaceMenu
                        to={modulo.to}
                        icon={modulo.icon}
                        etiqueta={modulo.label}
                        orden={indice + 1}
                        expandido={expandido}
                        onClick={alElegirModulo}
                        onPista={mostrarPista}
                        onSoltarPista={soltarPista}
                      />
                    </li>
                  ))}
                </ul>
              </>
            )}

            {ventanasVisibles.length === 0 && (
              <div className="mt-6 rounded-xl border border-dashed border-[#3a261a] px-4 py-6 text-center">
                <PackageOpen className="mx-auto mb-2 h-6 w-6 text-amber-400/60" />
                {expandido && (
                  <>
                    <p className="text-xs font-medium text-amber-200">Sin módulos habilitados</p>
                    <p className="mt-1 text-[11px] text-amber-300/60">
                      Las ventanas se habilitan a medida que se implementen los casos de uso.
                    </p>
                  </>
                )}
              </div>
            )}
          </nav>

          <div className="border-t border-[#2e1d13] p-3">
            <div className={`flex items-center ${expandido ? 'gap-3 px-2' : 'flex-col gap-2'}`}>
              <div
                tabIndex={expandido ? -1 : 0}
                className="shrink-0 rounded-full focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300/40"
                aria-label={expandido ? undefined : user.nombre_completo}
                onMouseEnter={(evento) => mostrarPista(evento, user.nombre_completo)}
                onFocus={(evento) => mostrarPista(evento, user.nombre_completo)}
                onMouseLeave={soltarPista}
                onBlur={soltarPista}
              >
                <UserAvatar usuario={user} size="sm" />
              </div>
              <div
                className={`min-w-0 overflow-hidden transition-[max-width,opacity] duration-300 ease-out motion-reduce:transition-none ${
                  expandido ? 'max-w-40 flex-1 opacity-100' : 'max-w-0 opacity-0'
                }`}
              >
                <p className="truncate text-xs font-semibold text-white">{user.nombre_completo}</p>
                <p className="truncate text-[11px] font-medium text-amber-300/90">{user.rol}</p>
              </div>
              <button
                type="button"
                onClick={cerrarSesion}
                aria-label="Cerrar sesión"
                onMouseEnter={(evento) => mostrarPista(evento, 'Cerrar sesión')}
                onFocus={(evento) => mostrarPista(evento, 'Cerrar sesión')}
                onMouseLeave={soltarPista}
                onBlur={soltarPista}
                className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-amber-300/80 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300/40 cursor-pointer"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </aside>

        {pista && !expandido && (
          <div
            key={pista.texto}
            className="pista-menu pointer-events-none absolute left-[calc(100%+0.7rem)] z-50 -translate-y-1/2 whitespace-nowrap rounded-lg bg-[#f6e7c1] px-3 py-1.5 text-sm font-semibold text-[#2b1a10] shadow-lg shadow-black/25"
            style={{ top: pista.top }}
            aria-hidden
          >
            <span
              className="absolute top-1/2 -left-1 h-2 w-2 -translate-y-1/2 rotate-45 bg-[#f6e7c1]"
              aria-hidden
            />
            {pista.texto}
          </div>
        )}
      </div>
    </>
  );
};

export default Sidebar;
