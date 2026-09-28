/* ------------------------------------------------------------------ *
 * Normalizador de errores de la API
 * ------------------------------------------------------------------ *
 *
 * POR QUÉ EXISTE
 * El backend responde con tres estructuras de error distintas y todas
 * son legítimas, porque las produce código distinto:
 *
 *   { "error": "No puedes inactivarte a ti mismo." }        <- APIException
 *   { "error": ["Muy común.", "Muy corta."] }               <- ContrasenaDebilError
 *   { "nombre_usuario": ["Ya existe una cuenta..."] }      <- ValidationError
 *
 * Son tres capas de Django con tres convenciones, no un descuido. Pero
 * para la UI son el mismo evento: "el servidor rechazó esto". Si cada
 * componente ramifica por el formato, el mismo `if` se copia en cuatro
 * archivos y el cuarto lo escribe alguien que no se enteró de los otros
 * tres. Este módulo es el único lugar que sabe distinguirlas.
 *
 * Lo que devuelve NO es la respuesta del backend: es una estructura
 * con la forma que los componentes quieren. Los tipos viven en
 * `types/usuarios.ts` para que la UI no dependa de axios.
 */

import axios from 'axios';
import type { AxiosError } from 'axios';
import type { ErrorNormalizado } from '../types/usuarios';

/** Claves que el backend usa para el error de negocio, no de campo. */
const CLAVES_DE_NEGOCIO = ['error', 'detail', 'message', 'non_field_errors'];

/**
 * Convierte un `AxiosError` en algo que se pueda pintar.
 *
 * Nunca lanza y nunca devuelve `undefined`: un error sin cuerpo (red
 * caída, CORS, servidor apagado) es el caso MÁS probable de todos y si
 * esta función lo devolviera vacío, los componentes tendrían que
 * tener un `if (!error)` por todos lados, que es exactamente lo que se
 * está tratando de evitar.
 */
export const normalizarErrorApi = (error: unknown): ErrorNormalizado => {
  // Red caída, timeout, CORS, servidor apagado: no hubo respuesta.
  if (!axios.isAxiosError(error)) {
    return {
      mensaje: 'Ocurrió un error inesperado. Intente de nuevo.',
      campos: {},
    };
  }

  const estado = error.response?.status;
  const cuerpo = error.response?.data as Record<string, unknown> | string | undefined;

  if (!error.response) {
    return {
      mensaje: 'No se pudo conectar con el servidor. Revise su conexión.',
      campos: {},
    };
  }

  // 429 es el throttle (`usuarios: 120/min`) o el bloqueo de CU1. Tiene
  // su propio `Retry-After` y merece su propio mensaje: decir "error"
  // en un 429 hace que el Administrador piense que la cuenta se rompió
  // cuando lo que pasó es que tocó el botón demasiado rápido.
  if (estado === 429) {
    const retryAfter = leerRetryAfter(error);
    return {
      mensaje: retryAfter
        ? `Demasiadas solicitudes. Intente de nuevo en ${retryAfter} segundo${retryAfter === 1 ? '' : 's'}.`
        : 'Demasiadas solicitudes. Espere un momento e intente de nuevo.',
      campos: {},
      retryAfter,
    };
  }

  // 403: el permiso faltó. `ProtectedRoute` ya evita que se llegue acá
  // por la UI normal, pero a una sesión pueden caducarle los permisos
  // mientras la pantalla está abierta, y el mensaje genérico de axios
  // ("Request failed with status code 403") no dice nada.
  if (estado === 403) {
    return {
      mensaje: 'No tiene permiso para realizar esta acción.',
      campos: {},
    };
  }

  // 405: es el `DELETE /api/usuarios/<id>/`. La UI no ofrece borrar, así
  // que esto solo aparece si alguien la llama a mano. Se reconoce igual,
  // porque el mensaje de axios no dice nada.
  if (estado === 405) {
    return {
      mensaje: 'Esta operación no está permitida. Las cuentas se inactivan, no se borran.',
      campos: {},
    };
  }

  // 500 y 404 no tienen cuerpo útil: mostrar el HTML de la página de
  // error de Django en un formulario sería peor que no mostrar nada.
  if (estado === 500) {
    return {
      mensaje: 'Error interno del servidor. Intente de nuevo en unos minutos.',
      campos: {},
    };
  }
  if (estado === 404) {
    return { mensaje: 'No se encontró el recurso solicitado.', campos: {} };
  }

  if (typeof cuerpo === 'string') {
    return { mensaje: cuerpo || 'No se pudo completar la operación.', campos: {} };
  }

  if (!cuerpo || typeof cuerpo !== 'object') {
    return {
      mensaje: `No se pudo completar la operación (HTTP ${estado ?? 'sin código'}).`,
      campos: {},
    };
  }

  return aplanarCuerpo(cuerpo);
};

/** Separa la clave de negocio del resto y normaliza a string[]. */
const aplanarCuerpo = (cuerpo: Record<string, unknown>): ErrorNormalizado => {
  const campos: Record<string, string[]> = {};
  const mensajes: string[] = [];

  for (const [clave, valor] of Object.entries(cuerpo)) {
    const textos = aTextoLista(valor);

    if (CLAVES_DE_NEGOCIO.includes(clave)) {
      // `{error: [...]}` y `{detail: "..."}` van al mensaje general. Un
      // 400 de contraseña débil llega acá y tiene que poder pintarse
      // arriba Y junto al campo, así que se guarda en los dos sitios.
      mensajes.push(...textos);
      if (textos.length > 0) campos.contrasena = textos;
      continue;
    }

    campos[clave] = textos;
  }

  return {
    mensaje: mensajes.length > 0 ? mensajes.join(' ') : primerMensajeDeCampos(campos),
    campos,
  };
};

/** DRF manda `["texto"]`, `"texto"` o a veces `[{...}]`. Todo a string[]. */
const aTextoLista = (valor: unknown): string[] => {
  if (valor === null || valor === undefined) return [];
  if (typeof valor === 'string') return [valor];
  if (typeof valor === 'number' || typeof valor === 'boolean') return [String(valor)];
  if (Array.isArray(valor)) {
    return valor
      .flatMap((item) => (typeof item === 'string' ? [item] : objetoAMensaje(item)))
      .filter(Boolean);
  }
  return objetoAMensaje(valor);
};

/** DRF devuelve a veces `{"detail": "..."}` dentro de una lista. */
const objetoAMensaje = (valor: unknown): string[] => {
  if (valor && typeof valor === 'object') {
    const detalle = (valor as Record<string, unknown>).detail;
    if (typeof detalle === 'string') return [detalle];
  }
  return [];
};

/** Si no hay mensaje de negocio, al menos que se sepa QUÉ campo falló. */
const primerMensajeDeCampos = (campos: Record<string, string[]>): string | null => {
  const [clave, textos] = Object.entries(campos)[0] ?? [];
  if (!clave || !textos?.length) return null;
  return `Revise el campo "${clave}": ${textos.join(' ')}`;
};

/** `Retry-After` puede venir como segundos o como fecha HTTP. */
const leerRetryAfter = (error: AxiosError): number | undefined => {
  const crudo = error.response?.headers?.['retry-after'];
  if (!crudo) return undefined;

  const segundos = Number(crudo);
  if (Number.isFinite(segundos)) return Math.ceil(segundos);

  const fecha = Date.parse(crudo);
  if (Number.isNaN(fecha)) return undefined;
  return Math.max(1, Math.ceil((fecha - Date.now()) / 1000));
};

export default normalizarErrorApi;
