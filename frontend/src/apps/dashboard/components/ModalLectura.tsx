import React from 'react';
import ModalBase, { type AnchoModal } from './ModalBase';

export interface ModalLecturaProps {
  /** Título principal de la consulta, detalle o comprobante. */
  titulo: React.ReactNode;
  /** Subtítulo descriptivo, identificador o metadatos de fecha/usuario. */
  subtitulo?: React.ReactNode;
  /** Ícono temático para la cabecera (ej. FileText, Receipt, Package). */
  iconoCabecera?: React.ReactNode;
  /** Callback para cerrar la vista. */
  onCerrar: () => void;
  /** Contenido de solo lectura (tablas de detalle, resúmenes, auditoría). */
  children: React.ReactNode;
  /** Pie opcional con botones de acción (ej. 'Imprimir', 'Descargar PDF', 'Cerrar'). */
  pie?: React.ReactNode;
  /** Tamaño del diálogo. Por defecto 'lg' para facilitar lectura de tablas/detalles. */
  ancho?: AnchoModal;
  /** Ocultar botón 'X'. */
  sinCerrar?: boolean;
  /** Clases CSS adicionales para la ventana. */
  className?: string;
  /** Clases CSS adicionales para el cuerpo de contenido. */
  cuerpoClassName?: string;
}

/**
 * ModalLectura
 * Plantilla especializada para diálogos de SOLO LECTURA (consultas, detalles, recibos, bitácora).
 *
 * Características UX:
 * - Cierra de forma ágil y no destructiva al hacer clic en el backdrop oscuro.
 * - Cierra al presionar la tecla Escape o el botón 'X'.
 * - Animaciones fluidas de apertura y cierre (fade + scale).
 * - Cero sobrecarga de formularios: no evalúa descarte porque no hay edición.
 */
export const ModalLectura: React.FC<ModalLecturaProps> = ({
  titulo,
  subtitulo,
  iconoCabecera,
  onCerrar,
  children,
  pie,
  ancho = 'lg',
  sinCerrar = false,
  className = '',
  cuerpoClassName = '',
}) => {
  return (
    <ModalBase
      titulo={titulo}
      subtitulo={subtitulo}
      iconoCabecera={iconoCabecera}
      onCerrar={onCerrar}
      ancho={ancho}
      sinCerrar={sinCerrar}
      backdropEstatico={false}
      className={className}
      cuerpoClassName={cuerpoClassName}
      pie={pie}
    >
      {children}
    </ModalBase>
  );
};

export default ModalLectura;
