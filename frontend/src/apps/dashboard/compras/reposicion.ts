import type { CompraReposicion } from '../../../types/compra';

const ENTERO_POSITIVO = /^\d+$/;
const CANTIDAD_DECIMAL = /^\d+(?:\.\d{1,3})?$/;

/** La URL solo propone datos; el catálogo y el registro siguen siendo responsabilidad de CU7. */
export const leerReposicion = (params: URLSearchParams): CompraReposicion | undefined => {
  const id = params.get('reposicion_materia_prima');
  const cantidad = params.get('reposicion_cantidad');
  if (!id || cantidad === null || !ENTERO_POSITIVO.test(id) || !CANTIDAD_DECIMAL.test(cantidad)) {
    return undefined;
  }

  const idMateriaPrima = Number(id);
  if (!Number.isSafeInteger(idMateriaPrima) || idMateriaPrima <= 0 || !Number.isFinite(Number(cantidad))) {
    return undefined;
  }

  // Se conserva el decimal como string, incluido 0 cuando el stock coincide con el mínimo.
  return { id_materia_prima: idMateriaPrima, cantidad };
};
