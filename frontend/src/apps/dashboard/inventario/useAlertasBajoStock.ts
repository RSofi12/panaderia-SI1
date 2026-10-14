import { useCallback, useEffect, useState } from 'react';
import { materiaPrimaService } from '../../../services/materiaPrimaService';
import type { AlertaBajoStock } from '../../../types/materiaPrima';

interface Resultado {
  clave: string;
  alertas: AlertaBajoStock[];
  error: string | null;
}

/** La página y el contador CU08 consultan la misma fuente sin recalcular stock. */
export function useAlertasBajoStock(habilitado = true, versionExterna = 0) {
  const [version, setVersion] = useState(0);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const clave = JSON.stringify([habilitado, versionExterna, version]);
  const cargando = habilitado && resultado?.clave !== clave;

  useEffect(() => {
    if (!habilitado) return;
    const controller = new AbortController();
    materiaPrimaService.listarAlertas(controller.signal)
      .then((alertas) => {
        if (!controller.signal.aborted) setResultado({ clave, alertas, error: null });
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setResultado({ clave, alertas: [], error: 'No se pudieron consultar las alertas. Comprueba tu conexión y vuelve a intentar.' });
        }
      });
    return () => controller.abort();
  }, [habilitado, clave]);

  const actualizar = useCallback(() => setVersion((v) => v + 1), []);
  const actual = habilitado && resultado?.clave === clave;
  return {
    alertas: actual ? resultado.alertas : [],
    error: actual ? resultado.error : null,
    cargando,
    actualizar,
  };
}
