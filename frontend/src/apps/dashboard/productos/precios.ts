const formatoBs = new Intl.NumberFormat('es-BO', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export const formatearBs = (valor: string | number): string => {
  const numero = Number(valor);
  return `Bs ${formatoBs.format(Number.isFinite(numero) ? numero : 0)}`;
};

/**
 * Misma fórmula que Producto.calcular_precio_sugerido() en el backend.
 * Solo se usa para mostrar el valor mientras se escribe; el backend guarda el definitivo.
 */
export const calcularPrecioSugerido = (costo: string, porcentaje: string): number | null => {
  const c = Number(costo);
  const p = Number(porcentaje);
  if (costo.trim() === '' || porcentaje.trim() === '' || !Number.isFinite(c) || !Number.isFinite(p)) {
    return null;
  }
  return Math.round(c * (1 + p / 100) * 100) / 100;
};
