import React, { useCallback, useEffect, useId, useRef } from 'react';
import { X } from 'lucide-react';

/**
 * Diálogo modal compartido por las pantallas del panel.
 *
 * POR QUÉ EXISTE
 * El CU3 necesita tres modales (alta/edición, cambio de estado y
 * restablecimiento de contraseña) y el CU4 va a necesitar al menos dos
 * más. Un modal son unas 60 líneas de cosas de accesibilidad que es
 * facilísimo dejar a medias: el `Escape`, la trampa de foco, la
 * restauración del foco, el bloqueo del scroll, el `aria-modal`. Copiar
 * eso tres veces produce tres versiones donde la segunda forgot el
 * `Escape`.
 *
 * `AuthCard.tsx` ya fijó la política del proyecto: una abstracción se
 * saca cuando ya duele, no de forma preventiva. Con tres usos ya duele.
 *
 * POR QUÉ VIVE AQUÍ Y NO EN `src/components/`
 * `src/components/` queda reservada para lo que es compartido por TODO
 * el sistema, y hoy no hay nada: `AuthCard` es de las pantallas públicas
 * y este modal es del panel. Cuando aparezca un componente que sirva a
 * ambos, ahí sí se sube. Subirlo antes sería adivinar.
 *
 * LO QUE NO HACE Y POR QUÉ
 * No gestiona los datos del formulario. Cada modal es dueño de su
 * estado porque los tres tienen necesidades distintas: el de alta tiene
 * checklist de contraseña, el de estado solo un motivo, y el de reset
 * dos campos que deben coincidir. Un modal genérico que además sabe
 * validar contraseñas deja de ser una abstracción y pasa a ser un
 * framework con tres usuarios.
 */

interface ModalProps {
  /** Se muestra en la cabecera. Es también el `aria-labelledby`. */
  titulo: string;
  /** Bajada bajo el título. Opcional. */
  subtitulo?: string;
  /** Si está en `true` el botón de cerrar queda oculto. */
  sinCerrar?: boolean;
  /** Se llama con Escape, con la X y con el clic en el fondo. */
  onCerrar: () => void;
  /** Cuerpo con los campos. */
  children: React.ReactNode;
  /** Pie con los botones. Pega a abajo y no tapa lo que hay encima. */
  pie?: React.ReactNode;
  /** Ancho máximo. `md` para formularios, `sm` para confirmaciones, `xl` para matrices. */
  ancho?: 'sm' | 'md' | 'lg' | 'xl';
}

const ANCHOS = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
} as const;

export const Modal: React.FC<ModalProps> = ({
  titulo,
  subtitulo,
  sinCerrar = false,
  onCerrar,
  children,
  pie,
  ancho = 'md',
}) => {
  const cajaRef = useRef<HTMLDivElement>(null);
  const botonInicialRef = useRef<HTMLElement | null>(null);
  // `useId` y no `Math.random()`: React garantiza que el id sea estable
  // entre renders y único en el documento, y no rompe las reglas de
  // render puro. Un `Math.random()` en el cuerpo del componente es una
  // función impura y además cambia el id en cada StrictMode, lo que
  // desvincula el `aria-labelledby` del `<h2>`.
  const tituloId = useId();

  // Qué tiene el foco justo antes de abrir. Se guarda en un `ref` y no
  // en un `state` porque no hay que re-renderizar nada para recordarlo.
  useEffect(() => {
    botonInicialRef.current = document.activeElement as HTMLElement | null;
    return () => {
      // Al cerrar, el foco vuelve a donde estaba. Sin esto, el foco cae
      // al `<body>` y la persona que usan el teclado tiene que tabular
      // desde el principio de la página para seguir trabajando: perder
      // el lugar al cerrar un formulario es el síntoma clásico de un
      // modal mal hecho.
      botonInicialRef.current?.focus?.();
    };
  }, []);

  // Mueve el foco al primer control del modal al abrir. Sin esto el foco
  // se queda atrás, en la página, y la primera Tabulación se lleva a
  // cualquier parte menos al formulario que se acaba de abrir.
  useEffect(() => {
    const primero = cajaRef.current?.querySelector<HTMLElement>(
      'input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])'
    );
    primero?.focus();
  }, []);

  const manejarTeclado = useCallback(
    (evento: KeyboardEvent) => {
      if (evento.key === 'Escape' && !sinCerrar) {
        evento.preventDefault();
        onCerrar();
        return;
      }

      if (evento.key !== 'Tab') return;

      // Trampa de foco: Tab en el último control vuelve al primero, y
      // Shift+Tab en el primero va al último. Sin esto, el teclado
      // escapa del modal hacia la página de atrás, que sigue siendo
      // visible y en la que el foco ya no se ve. WCAG lo llama
      // "keyboard trap" y lo prohíbe al revés: la trampa es la que
      // impide SALIR del diálogo abierto, no la que impide entrar.
      const focusables = Array.from(
        cajaRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        ) ?? []
      ).filter((elemento) => elemento.offsetParent !== null);

      if (focusables.length === 0) {
        evento.preventDefault();
        return;
      }

      const primero = focusables[0];
      const ultimo = focusables[focusables.length - 1];
      const activo = document.activeElement;

      if (evento.shiftKey && (activo === primero || !cajaRef.current?.contains(activo))) {
        evento.preventDefault();
        ultimo.focus();
      } else if (!evento.shiftKey && activo === ultimo) {
        evento.preventDefault();
        primero.focus();
      }
    },
    [onCerrar, sinCerrar]
  );

  useEffect(() => {
    document.addEventListener('keydown', manejarTeclado);
    return () => document.removeEventListener('keydown', manejarTeclado);
  }, [manejarTeclado]);

  // Bloquea el scroll del fondo. Sin esto, hacer scroll con la rueda
  // sobre un modal corto mueve la página de atrás y el modal queda
  // flotando a media altura, con la cabecera fuera de la pantalla.
  useEffect(() => {
    const previo = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previo;
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center overflow-y-auto bg-slate-900/50 p-4 backdrop-blur-sm sm:items-center"
      onMouseDown={(evento) => {
        // Solo cierra si el gesto empezó en el fondo. Con `onClick` hace
        // falta comprobar que el `target` sea el propio fondo, porque un
        // click que empieza en un input y termina al soltar sobre el
        // fondo cerraría el modal y perdería lo escrito.
        if (evento.target === evento.currentTarget && !sinCerrar) onCerrar();
      }}
    >
      <div
        ref={cajaRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={tituloId}
        className={`w-full ${ANCHOS[ancho]} overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl`}
      >
        <header className="flex items-start gap-4 border-b border-slate-100 px-6 py-4">
          <div className="min-w-0 flex-1">
            <h2
              id={tituloId}
              className="text-base font-bold leading-tight tracking-tight text-slate-900"
            >
              {titulo}
            </h2>
            {subtitulo && <p className="mt-0.5 text-xs text-slate-500">{subtitulo}</p>}
          </div>

          {!sinCerrar && (
            <button
              type="button"
              onClick={onCerrar}
              aria-label="Cerrar"
              className="-mr-2 -mt-1 shrink-0 rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 cursor-pointer"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </header>

        <div className="max-h-[65vh] overflow-y-auto px-6 py-5">{children}</div>

        {pie && (
          <footer className="flex flex-col-reverse gap-2 border-t border-slate-100 bg-slate-50 px-6 py-4 sm:flex-row sm:justify-end">
            {pie}
          </footer>
        )}
      </div>
    </div>
  );
};

export default Modal;
