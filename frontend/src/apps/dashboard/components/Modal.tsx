import React from 'react';
import ModalBase, { type AnchoModal } from './ModalBase';
import ModalLectura, { type ModalLecturaProps } from './ModalLectura';
import ModalFormulario, {
  type ModalFormularioProps,
  useModalFormulario,
} from './ModalFormulario';

export { ModalBase, ModalLectura, ModalFormulario, useModalFormulario };
export type { AnchoModal, ModalLecturaProps, ModalFormularioProps };

/**
 * Diálogo modal compartido por las pantallas del panel.
 * Mantiene compatibilidad total con consumidores históricos usando la nueva base animada y accesible.
 */
export interface ModalProps {
  titulo: React.ReactNode;
  subtitulo?: React.ReactNode;
  sinCerrar?: boolean;
  onCerrar: () => void;
  children: React.ReactNode;
  pie?: React.ReactNode;
  ancho?: AnchoModal;
  className?: string;
}

export const Modal: React.FC<ModalProps> = ({
  titulo,
  subtitulo,
  sinCerrar = false,
  onCerrar,
  children,
  pie,
  ancho = 'md',
  className = '',
}) => {
  return (
    <ModalLectura
      titulo={titulo}
      subtitulo={subtitulo}
      sinCerrar={sinCerrar}
      onCerrar={onCerrar}
      ancho={ancho}
      pie={pie}
      className={className}
    >
      {children}
    </ModalLectura>
  );
};

export default Modal;
