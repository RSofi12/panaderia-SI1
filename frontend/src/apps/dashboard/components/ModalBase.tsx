import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { X } from 'lucide-react';

export type AnchoModal = 'sm' | 'md' | 'lg' | 'xl' | 'full';

export const ANCHOS_MODAL: Record<AnchoModal, string> = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-5xl',
};

export interface ModalBaseProps {
  /** Título principal visible en la cabecera del modal y vinculado a aria-labelledby. */
  titulo: React.ReactNode;
  /** Subtítulo descriptivo o código del caso de uso. Opcional. */
  subtitulo?: React.ReactNode;
  /** Ícono decorativo o distintivo del módulo para la cabecera. Opcional. */
  iconoCabecera?: React.ReactNode;
  /** Función invocada cuando el modal termina su ciclo de cierre. */
  onCerrar: () => void;
  /** Contenido interno del modal. */
  children: React.ReactNode;
  /** Pie del modal, típicamente barra de acciones con botones. Opcional. */
  pie?: React.ReactNode;
  /** Ancho máximo de la ventana modal. Por defecto 'md'. */
  ancho?: AnchoModal;
  /** Si es true, el botón 'X' de la esquina queda oculto. */
  sinCerrar?: boolean;
  /** Si es true, hacer clic en el backdrop oscuro no cierra el modal; activa sacudida. */
  backdropEstatico?: boolean;
  /** Función para interceptar el intento de cierre. Si retorna false, cancela el cierre. */
  onIntentarCerrar?: () => boolean | void;
  /** Si es true, activa la animación de salida y el posterior onCerrar. */
  cerrando?: boolean;
  /** Si es true, oculta el scrollbar del body (por defecto false para evitar desfase de layout). */
  bloquearScroll?: boolean;
  /** Si está en true, se aplica la clase de sacudida visual al contenedor. */
  sacudirExterno?: boolean;
  /** Clases CSS adicionales para el contenedor principal de la tarjeta. */
  className?: string;
  /** Clases CSS adicionales para el área de contenido scrollable. */
  cuerpoClassName?: string;
}

/**
 * ModalBase
 * Componente base arquitectónico para todos los diálogos modales de Panadería Santiago.
 * Gestiona:
 * - Ciclo de vida y transiciones fluidas de entrada y salida (fade & scale).
 * - Accesibilidad completa WCAG 2.2: aria-modal, role="dialog", useId para aria-labelledby.
 * - Bloqueo de scroll del fondo mientras está abierto.
 * - Trampa de foco (Tab / Shift+Tab) y restauración de foco al control previo.
 * - Soporte para backdrop estático (micro-feedback al hacer clic fuera).
 */
export const ModalBase: React.FC<ModalBaseProps> = ({
  titulo,
  subtitulo,
  iconoCabecera,
  onCerrar,
  children,
  pie,
  ancho = 'md',
  sinCerrar = false,
  backdropEstatico = false,
  onIntentarCerrar,
  cerrando = false,
  bloquearScroll = false,
  sacudirExterno = false,
  className = '',
  cuerpoClassName = '',
}) => {
  const [animandoEntrada, setAnimandoEntrada] = useState(false);
  const [animandoSalida, setAnimandoSalida] = useState(false);
  const [sacudidaInterna, setSacudidaInterna] = useState(false);

  const cajaRef = useRef<HTMLDivElement>(null);
  const elementoPrevioRef = useRef<HTMLElement | null>(null);
  const tituloId = useId();

  // Guardar foco previo y restaurar al desmontar
  useEffect(() => {
    elementoPrevioRef.current = document.activeElement as HTMLElement | null;
    return () => {
      elementoPrevioRef.current?.focus?.();
    };
  }, []);

  // Animación de entrada fluida en el siguiente cuadro de renderizado
  useEffect(() => {
    const frame = requestAnimationFrame(() => setAnimandoEntrada(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  // Bloqueo opcional de scroll en el body (por defecto desactivado para mantener la barra y evitar salto de pantalla)
  useEffect(() => {
    if (!bloquearScroll) return;
    const overflowPrevio = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = overflowPrevio;
    };
  }, [bloquearScroll]);

  // Función para cerrar con transición fluida de salida
  const cerrarConTransicion = useCallback(() => {
    setAnimandoSalida(true);
    window.setTimeout(() => {
      onCerrar();
    }, 180);
  }, [onCerrar]);

  // Si se solicita cerrar desde una propiedad externa (ej. tras confirmar descarte)
  useEffect(() => {
    if (cerrando && !animandoSalida) {
      cerrarConTransicion();
    }
  }, [cerrando, animandoSalida, cerrarConTransicion]);

  // Manejador centralizado para solicitudes de cierre
  const solicitarCierre = useCallback(() => {
    if (onIntentarCerrar) {
      const permiso = onIntentarCerrar();
      if (permiso === false) return;
    }
    cerrarConTransicion();
  }, [onIntentarCerrar, cerrarConTransicion]);

  // Clic en el backdrop oscuro
  const alHacerClicFondo = (evento: React.MouseEvent) => {
    if (evento.target !== evento.currentTarget) return;

    if (backdropEstatico) {
      setSacudidaInterna(true);
      window.setTimeout(() => setSacudidaInterna(false), 240);
    } else if (!sinCerrar) {
      solicitarCierre();
    }
  };

  // Manejo de teclado: Escape y trampa de foco
  const manejarTeclado = useCallback(
    (evento: KeyboardEvent) => {
      if (evento.key === 'Escape' && !sinCerrar) {
        evento.preventDefault();
        solicitarCierre();
        return;
      }

      if (evento.key !== 'Tab') return;

      const elementos = Array.from(
        cajaRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        ) ?? []
      ).filter((el) => el.offsetParent !== null);

      if (elementos.length === 0) {
        evento.preventDefault();
        return;
      }

      const primero = elementos[0];
      const ultimo = elementos[elementos.length - 1];
      const activo = document.activeElement;

      if (evento.shiftKey && (activo === primero || !cajaRef.current?.contains(activo))) {
        evento.preventDefault();
        ultimo.focus();
      } else if (!evento.shiftKey && activo === ultimo) {
        evento.preventDefault();
        primero.focus();
      }
    },
    [sinCerrar, solicitarCierre]
  );

  useEffect(() => {
    document.addEventListener('keydown', manejarTeclado);
    return () => document.removeEventListener('keydown', manejarTeclado);
  }, [manejarTeclado]);

  // Poner foco inicial dentro del modal
  useEffect(() => {
    const timer = setTimeout(() => {
      const primero = cajaRef.current?.querySelector<HTMLElement>(
        'input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])'
      );
      primero?.focus();
    }, 50);
    return () => clearTimeout(timer);
  }, []);

  const sacudir = sacudidaInterna || sacudirExterno;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-200 ${
        animandoEntrada && !animandoSalida
          ? 'bg-slate-900/50 backdrop-blur-xs opacity-100'
          : 'bg-slate-900/0 opacity-0'
      }`}
      onMouseDown={alHacerClicFondo}
    >
      <div
        ref={cajaRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={tituloId}
        className={`w-full ${ANCHOS_MODAL[ancho]} max-h-[90vh] flex flex-col rounded-2xl border border-amber-100 bg-white shadow-2xl transition-all duration-200 ease-out ${
          animandoEntrada && !animandoSalida
            ? 'scale-100 opacity-100 translate-y-0'
            : 'scale-95 opacity-0 translate-y-2'
        } ${sacudir ? 'scale-[1.015] ring-2 ring-amber-400/50' : ''} ${className}`}
      >
        {/* Cabecera */}
        <header className="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-4 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            {iconoCabecera && <div className="shrink-0">{iconoCabecera}</div>}
            <div className="min-w-0">
              <h2
                id={tituloId}
                className="text-base font-bold text-slate-900 truncate"
              >
                {titulo}
              </h2>
              {subtitulo && <p className="text-xs text-slate-500 mt-0.5">{subtitulo}</p>}
            </div>
          </div>

          {!sinCerrar && (
            <button
              type="button"
              onClick={solicitarCierre}
              aria-label="Cerrar ventana"
              className="-mr-1 -mt-1 rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </header>

        {/* Cuerpo */}
        <div className={`overflow-y-auto px-6 py-5 flex-1 ${cuerpoClassName}`}>
          {children}
        </div>

        {/* Pie */}
        {pie && (
          <footer className="border-t border-slate-100 bg-slate-50/60 px-6 py-3.5 rounded-b-2xl shrink-0">
            {pie}
          </footer>
        )}
      </div>
    </div>
  );
};

export default ModalBase;
