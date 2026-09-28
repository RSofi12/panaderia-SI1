import React from 'react';

/**
 * Campo de formulario con etiqueta, error y texto de ayuda.
 *
 * POR QUÉ EXISTE
 * Los tres modales del CU3 tienen los mismos cuatro adornos en cada
 * input: etiqueta visible, error debajo, `aria-describedby` apuntando al
 * error y foco visible. Repetir eso en cada input de cada modal son
 * cuatro veces tres bloques de JSX idénticos, y el bloque que se olvide
 * de un `aria-describedby` es justo el que hace que el lector de pantalla
 * no anuncie el error.
 *
 * El error va SIEMPRE debajo del campo, nunca solo arriba. El resumen
 * general del formulario lo pone cada modal; este es el detalle por
 * campo. WCAG pide los dos: el resumen para quien navega con teclado
 * buscando el error, y el inline para quien está parado en el campo.
 *
 * `htmlFor` y el `id` se generan con `useId` de React 19 para que el
 * enlace sea válido sin que nadie tenga que acordarse de escribir un id
 * distinto cada vez.
 *
 * Las clases de los inputs viven en `estilosFormulario.ts` y no acá: este
 * archivo exporta solo el componente, que es lo que el Fast Refresh de
 * Vite espera para poder intercambiarlo sin recargar la página.
 */

interface CampoFormularioProps {
  etiqueta: string;
  /** Se pinta debajo del campo cuando hay error. */
  error?: string;
  /** Ayuda permanente, gris. Se oculta si hay error: no son dos textos
   *  que convivan sin dejar el campo cargado de frases. */
  ayuda?: string;
  /** Se marca como obligatorio en la etiqueta. No deshabilita el campo. */
  requerido?: boolean;
  children: (props: {
    id: string;
    'aria-invalid': boolean;
    'aria-describedby': string | undefined;
  }) => React.ReactNode;
}

export const CampoFormulario: React.FC<CampoFormularioProps> = ({
  etiqueta,
  error,
  ayuda,
  requerido = false,
  children,
}) => {
  const id = React.useId();
  const idError = `${id}-error`;
  const idAyuda = `${id}-ayuda`;

  // `aria-describedby` puede apuntar a varios elementos separados por
  // espacio, así que se arma con lo que exista y no con un string fijo.
  const descritos = [error ? idError : null, !error && ayuda ? idAyuda : null]
    .filter(Boolean)
    .join(' ');

  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-xs font-semibold text-slate-700">
        {etiqueta}
        {requerido && (
          <span className="ml-0.5 text-red-600" aria-hidden="true">
            *
          </span>
        )}
      </label>

      {children({
        id,
        'aria-invalid': Boolean(error),
        'aria-describedby': descritos || undefined,
      })}

      {error ? (
        <p id={idError} className="mt-1.5 text-[11px] font-medium text-red-600">
          {error}
        </p>
      ) : (
        ayuda && (
          <p id={idAyuda} className="mt-1.5 text-[11px] text-slate-500">
            {ayuda}
          </p>
        )
      )}
    </div>
  );
};

export default CampoFormulario;
