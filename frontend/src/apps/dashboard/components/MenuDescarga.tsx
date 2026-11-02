import React, { useEffect, useId, useRef, useState } from 'react';
import { Download, Loader2 } from 'lucide-react';

interface MenuDescargaProps {
  descripcion: string;
  deshabilitado?: boolean;
  /** Si devuelve un texto, no se pide el archivo y se muestra ese aviso. */
  validar?: () => string | null;
  onDescargar: (formato: 'csv' | 'pdf') => Promise<void>;
}

/**
 * Menú «Descargar» con PDF y CSV. El texto de arriba dice qué filtro
 * va a usar el archivo, el mismo que está aplicado en la pantalla.
 */
export const MenuDescarga: React.FC<MenuDescargaProps> = ({
  descripcion,
  deshabilitado = false,
  validar,
  onDescargar,
}) => {
  const [abierto, setAbierto] = useState(false);
  const [descargando, setDescargando] = useState<'csv' | 'pdf' | ''>('');
  const [error, setError] = useState<{ texto: string; filtro: string } | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const contenedor = useRef<HTMLDivElement>(null);
  const disparador = useRef<HTMLButtonElement>(null);
  const primeraOpcion = useRef<HTMLButtonElement>(null);
  const tituloId = useId();
  const filtroId = useId();
  const errorId = useId();
  const ocupado = deshabilitado || descargando !== '';
  const errorVisible = error?.filtro === descripcion ? error.texto : null;

  useEffect(() => {
    if (!abierto) return undefined;
    primeraOpcion.current?.focus();

    function cerrarSiSale(evento: MouseEvent) {
      if (!contenedor.current?.contains(evento.target as Node)) {
        setAbierto(false);
      }
    }

    document.addEventListener('mousedown', cerrarSiSale);
    return () => document.removeEventListener('mousedown', cerrarSiSale);
  }, [abierto]);

  useEffect(() => {
    if (!aviso) return undefined;
    const timer = window.setTimeout(() => setAviso(null), 4000);
    return () => window.clearTimeout(timer);
  }, [aviso]);

  function cerrarMenu() {
    setAbierto(false);
    disparador.current?.focus();
  }

  function alTeclado(evento: React.KeyboardEvent<HTMLDivElement>) {
    if (evento.key === 'Escape') {
      evento.preventDefault();
      cerrarMenu();
      return;
    }

    const opciones = Array.from(
      contenedor.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]') ?? [],
    );
    const actual = opciones.indexOf(document.activeElement as HTMLButtonElement);
    if (actual < 0) return;

    if (evento.key === 'ArrowDown') {
      evento.preventDefault();
      opciones[(actual + 1) % opciones.length]?.focus();
    }
    if (evento.key === 'ArrowUp') {
      evento.preventDefault();
      opciones[(actual - 1 + opciones.length) % opciones.length]?.focus();
    }
  }

  async function descargar(formato: 'csv' | 'pdf') {
    const fallo = validar?.() ?? null;
    if (fallo) {
      setAbierto(false);
      setAviso(null);
      setError({ texto: fallo, filtro: descripcion });
      return;
    }

    setAbierto(false);
    setError(null);
    setAviso(null);
    setDescargando(formato);
    try {
      await onDescargar(formato);
      setAviso(
        formato === 'pdf'
          ? `Se descargó el PDF: ${descripcion}.`
          : `Se descargó el CSV: ${descripcion}.`,
      );
    } catch {
      setError({
        texto: 'No se pudo descargar el archivo. Revisa los filtros e inténtalo de nuevo.',
        filtro: descripcion,
      });
    } finally {
      setDescargando('');
      disparador.current?.focus();
    }
  }

  return (
    <div ref={contenedor} className="relative" onKeyDown={alTeclado}>
      <button
        ref={disparador}
        type="button"
        aria-expanded={abierto}
        aria-haspopup="menu"
        aria-controls={abierto ? tituloId : undefined}
        aria-describedby={errorVisible ? errorId : filtroId}
        aria-busy={descargando !== ''}
        disabled={ocupado}
        onClick={() => {
          setError(null);
          setAbierto((valor) => !valor);
        }}
        className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
      >
        {descargando ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <Download className="h-4 w-4" aria-hidden="true" />
        )}
        Descargar
      </button>
      <p id={filtroId} className="sr-only">
        El archivo usa el filtro actual: {descripcion}.
      </p>

      {abierto ? (
        <div
          id={tituloId}
          role="menu"
          aria-label="Formato de descarga"
          className="absolute right-0 z-20 mt-2 w-72 max-w-[calc(100vw-2rem)] rounded-2xl border border-slate-200 bg-white p-2 shadow-lg"
        >
          <p className="px-3 py-2 text-sm leading-6 text-slate-700">
            Este archivo usa: <span className="font-semibold text-slate-900">{descripcion}</span>
          </p>
          <button
            ref={primeraOpcion}
            type="button"
            role="menuitem"
            onClick={() => void descargar('pdf')}
            className="flex min-h-11 w-full items-center rounded-xl px-3 text-left text-sm font-semibold text-slate-800 hover:bg-amber-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 cursor-pointer"
          >
            Formato PDF
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => void descargar('csv')}
            className="flex min-h-11 w-full items-center rounded-xl px-3 text-left text-sm font-semibold text-slate-800 hover:bg-amber-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 cursor-pointer"
          >
            Formato CSV
          </button>
        </div>
      ) : null}

      {errorVisible ? (
        <p id={errorId} role="alert" className="mt-2 max-w-xs text-sm text-red-700">
          {errorVisible}
        </p>
      ) : null}
      {aviso ? (
        <p role="status" className="mt-2 max-w-xs text-sm text-emerald-800">
          {aviso}
        </p>
      ) : null}
    </div>
  );
};

export default MenuDescarga;
