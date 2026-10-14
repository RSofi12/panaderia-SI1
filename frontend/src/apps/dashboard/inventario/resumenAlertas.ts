import type { AlertaBajoStock } from '../../../types/materiaPrima';

export function resumirAlertas(alertas: AlertaBajoStock[]) {
  const maximos = new Map<string, AlertaBajoStock>();
  let agotadas = 0;
  for (const alerta of alertas) {
    if (Number(alerta.stock_actual) === 0) agotadas += 1;
    const unidad = alerta.unidad_medida.trim();
    const anterior = maximos.get(unidad);
    // Solo comparar cantidades que comparten exactamente la misma unidad.
    if (!anterior || Number(alerta.faltante) > Number(anterior.faltante)) {
      maximos.set(unidad, alerta);
    }
  }
  return {
    total: alertas.length,
    agotadas,
    maximosPorUnidad: [...maximos.values()].sort((a, b) => a.unidad_medida.localeCompare(b.unidad_medida, 'es')),
  };
}

const normalizarNombre = (nombre: string) =>
  nombre.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase('es');

export function filtrarAlertas(alertas: AlertaBajoStock[], busqueda: string) {
  const termino = normalizarNombre(busqueda.trim());
  return alertas.filter((alerta) => normalizarNombre(alerta.nombre).includes(termino));
}
