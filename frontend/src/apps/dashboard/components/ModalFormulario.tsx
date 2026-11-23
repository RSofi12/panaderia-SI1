import React, { createContext, useContext, useState } from 'react';
import ConfirmarDescarteDialog from './ConfirmarDescarteDialog';
import ModalBase, { type AnchoModal } from './ModalBase';

interface ContextoModalFormulario {
  /** Invoca el intento de cierre evaluando si hay cambios pendientes. */
  solicitarCierre: () => void;
  guardando: boolean;
  tieneCambios: boolean;
}

const ModalFormularioContext = createContext<ContextoModalFormulario | null>(null);

/** Hook para que los botones de acción (ej. Cancelar) invoquen el cierre protegido. */
export const useModalFormulario = (): ContextoModalFormulario => {
  const contexto = useContext(ModalFormularioContext);
  if (!contexto) {
    throw new Error('useModalFormulario debe usarse dentro de un <ModalFormulario>');
  }
  return contexto;
};

export interface ModalFormularioProps {
  /** Título principal de la operación (ej. 'Nuevo producto', 'Registrar compra'). */
  titulo: React.ReactNode;
  /** Subtítulo descriptivo o módulo. Opcional. */
  subtitulo?: React.ReactNode;
  /** Ícono temático para la cabecera. Opcional. */
  iconoCabecera?: React.ReactNode;
  /** Callback definitivo cuando el modal se cierra. */
  onCerrar: () => void;
  /** Indica si el formulario tiene datos ingresados o modificados sin guardar. */
  tieneCambios?: boolean;
  /** Indica si la petición de guardado está en curso (bloquea cierres accidentales). */
  guardando?: boolean;
  /** Título personalizado para la alerta de confirmación de descarte. */
  tituloDescarte?: string;
  /** Mensaje explicativo para la alerta de confirmación de descarte. */
  mensajeDescarte?: string;
  /** Ancho de la ventana. Por defecto 'md'. */
  ancho?: AnchoModal;
  /** Ocultar botón 'X'. */
  sinCerrar?: boolean;
  /** Clases CSS adicionales para la ventana. */
  className?: string;
  /** Clases CSS adicionales para el área del formulario. */
  cuerpoClassName?: string;
  /** Contenido o render-prop que recibe helpers. */
  children:
    | React.ReactNode
    | ((helpers: { solicitarCierre: () => void; guardando: boolean }) => React.ReactNode);
  /** Pie opcional con botones de acción (Cancelar / Guardar). Puede ser nodo o render-prop. */
  pie?:
    | React.ReactNode
    | ((helpers: { solicitarCierre: () => void; guardando: boolean }) => React.ReactNode);
}

/**
 * ModalFormulario
 * Plantilla especializada para diálogos de CAPTURA, ALTA Y EDICIÓN DE DATOS.
 *
 * Características UX y Resiliencia:
 * - Backdrop Estático: Clics fuera del modal emiten micro-sacudida, no cierran la ventana.
 * - Prevención de Pérdida de Datos: Intercepta la 'X', 'Cancelar' y la tecla 'Escape'.
 * - Si `tieneCambios === true`, levanta automáticamente el `ConfirmarDescarteDialog`.
 * - Si `tieneCambios === false`, cierra limpiamente con animación.
 * - Elimina la necesidad de duplicar lógica de descarte en cada formulario.
 */
export const ModalFormulario: React.FC<ModalFormularioProps> = ({
  titulo,
  subtitulo,
  iconoCabecera,
  onCerrar,
  tieneCambios = false,
  guardando = false,
  tituloDescarte = '¿Descartar cambios sin guardar?',
  mensajeDescarte = 'Has comenzado a ingresar información en este formulario. Si sales ahora, los datos escritos no se guardarán.',
  ancho = 'md',
  sinCerrar = false,
  className = '',
  cuerpoClassName = '',
  children,
  pie,
}) => {
  const [mostrarDescarte, setMostrarDescarte] = useState(false);
  const [cerrando, setCerrando] = useState(false);

  // Maneja invocaciones directas de cierre (ej. botón Cancelar dentro del formulario)
  const solicitarCierre = () => {
    if (guardando) return;

    if (tieneCambios) {
      setMostrarDescarte(true);
    } else {
      setCerrando(true);
    }
  };

  // Intercepta solicitudes originadas en ModalBase (X o tecla Escape)
  const intentarCerrar = (): boolean => {
    if (guardando) return false;

    if (tieneCambios) {
      setMostrarDescarte(true);
      return false; // Detiene el cierre inmediato para solicitar confirmación
    }

    return true; // Sin cambios: permite a ModalBase animar y cerrar
  };

  const confirmarDescarte = () => {
    setMostrarDescarte(false);
    setCerrando(true);
  };

  const cancelarDescarte = () => {
    setMostrarDescarte(false);
  };

  const valorContexto: ContextoModalFormulario = {
    solicitarCierre,
    guardando,
    tieneCambios,
  };

  const renderChildren = typeof children === 'function' ? children({ solicitarCierre, guardando }) : children;
  const renderPie = typeof pie === 'function' ? pie({ solicitarCierre, guardando }) : pie;

  return (
    <ModalFormularioContext.Provider value={valorContexto}>
      <ModalBase
        titulo={titulo}
        subtitulo={subtitulo}
        iconoCabecera={iconoCabecera}
        onCerrar={onCerrar}
        onIntentarCerrar={intentarCerrar}
        cerrando={cerrando}
        ancho={ancho}
        sinCerrar={sinCerrar}
        backdropEstatico={true}
        className={className}
        cuerpoClassName={cuerpoClassName}
        pie={renderPie}
      >
        {renderChildren}
      </ModalBase>

      <ConfirmarDescarteDialog
        abierto={mostrarDescarte}
        onContinuar={cancelarDescarte}
        onDescartar={confirmarDescarte}
        titulo={tituloDescarte}
        mensaje={mensajeDescarte}
      />
    </ModalFormularioContext.Provider>
  );
};

export default ModalFormulario;
