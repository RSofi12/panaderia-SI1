import { useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import historialPreciosService from '../../../../services/historialPreciosService';
import productoService from '../../../../services/productoService';
import type { HistorialPrecioFiltros, HistorialPrecioPagina } from '../../../../types/historialPrecio';
import type { Producto } from '../../../../types/producto';

interface ResultadoHistorial {
  clave: string;
  datos: HistorialPrecioPagina | null;
  error: string | null;
}

interface ResultadoCatalogo {
  version: number;
  productos: Producto[];
  error: string | null;
}

function mensajeError(error: unknown): string {
  if (isAxiosError<Record<string, unknown>>(error)) {
    if (error.response?.status === 403) {
      return 'No tienes autorización para consultar el historial de precios.';
    }
    if (error.response?.status === 400) {
      const mensajes = Object.values(error.response.data).flatMap((valor) =>
        typeof valor === 'string'
          ? [valor]
          : Array.isArray(valor)
            ? valor.filter((item): item is string => typeof item === 'string')
            : [],
      );
      if (mensajes.length) return mensajes.join(' ');
    }
  }
  return 'No se pudo cargar el historial de precios. Revisa la conexión con el servidor y vuelve a intentar.';
}

/** Las dos consultas son independientes: un fallo del catálogo no oculta el historial. */
export function useHistorialPrecios(filtros: HistorialPrecioFiltros, pagina: number) {
  const [versionHistorial, setVersionHistorial] = useState(0);
  const [versionCatalogo, setVersionCatalogo] = useState(0);
  const [resultado, setResultado] = useState<ResultadoHistorial | null>(null);
  const [catalogo, setCatalogo] = useState<ResultadoCatalogo | null>(null);
  const { id_producto, fecha_desde, fecha_hasta } = filtros;
  const clave = JSON.stringify([id_producto, fecha_desde, fecha_hasta, pagina, versionHistorial]);

  useEffect(() => {
    const controller = new AbortController();
    historialPreciosService.listar({ id_producto, fecha_desde, fecha_hasta }, pagina, controller.signal)
      .then((datos) => {
        if (!controller.signal.aborted) setResultado({ clave, datos, error: null });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setResultado({ clave, datos: null, error: mensajeError(error) });
        }
      });
    return () => controller.abort();
  }, [id_producto, fecha_desde, fecha_hasta, pagina, clave]);

  useEffect(() => {
    let vigente = true;
    // Sin filtro de estado: CU19 también debe permitir elegir productos inactivos.
    productoService.listar()
      .then((productos) => {
        if (vigente) setCatalogo({ version: versionCatalogo, productos, error: null });
      })
      .catch(() => {
        if (vigente) {
          setCatalogo({
            version: versionCatalogo,
            productos: [],
            error: 'No se pudo cargar el filtro de productos. Puedes seguir consultando el historial por fechas.',
          });
        }
      });
    return () => { vigente = false; };
  }, [versionCatalogo]);

  const historialActual = resultado?.clave === clave ? resultado : null;
  const catalogoActual = catalogo?.version === versionCatalogo ? catalogo : null;

  return {
    datos: historialActual?.datos ?? null,
    error: historialActual?.error ?? null,
    cargando: historialActual === null,
    productos: catalogoActual?.productos ?? [],
    errorCatalogo: catalogoActual?.error ?? null,
    cargandoCatalogo: catalogoActual === null,
    reintentar: () => setVersionHistorial((version) => version + 1),
    reintentarCatalogo: () => setVersionCatalogo((version) => version + 1),
  };
}
