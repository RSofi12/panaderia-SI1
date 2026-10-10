import React, { useMemo, useState } from 'react';
import {
  Minus,
  Plus,
  RotateCcw,
  Search,
  Sparkles,
} from 'lucide-react';
import type { RenglonLoteProduccion } from '../../../../../types/produccion';

interface TablaLoteProduccionProps {
  filas: RenglonLoteProduccion[];
  onCambiarCantidad: (idProducto: number, cantidad: number) => void;
  onCargarHabitual: () => void;
  onLimpiar: () => void;
}

export const TablaLoteProduccion: React.FC<TablaLoteProduccionProps> = ({
  filas,
  onCambiarCantidad,
  onCargarHabitual,
  onLimpiar,
}) => {
  const [busqueda, setBusqueda] = useState('');

  const filasFiltradas = useMemo(() => {
    const q = busqueda.toLowerCase().trim();
    if (!q) return filas;
    return filas.filter(
      (f) =>
        f.nombre_producto.toLowerCase().includes(q) ||
        (f.categoria_nombre && f.categoria_nombre.toLowerCase().includes(q))
    );
  }, [filas, busqueda]);

  const totalUnidades = useMemo(
    () => filas.reduce((acc, f) => acc + (f.cantidad_producida || 0), 0),
    [filas]
  );

  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      {/* Barra de herramientas superior */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-slate-50/60 p-3.5">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar pan o categoría..."
            className="w-full rounded-xl border border-slate-200 bg-white py-1.5 pl-9 pr-3 text-xs text-slate-900 placeholder-slate-400 focus:border-amber-600 focus:outline-none focus:ring-1 focus:ring-amber-600"
          />
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCargarHabitual}
            className="inline-flex items-center gap-1.5 rounded-xl border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-900 transition-colors hover:bg-amber-100 cursor-pointer shadow-2xs"
            title="Pre-llena con las cantidades promedio de producción de la panadería"
          >
            <Sparkles className="h-3.5 w-3.5 text-amber-700" />
            Cargar Lote Habitual
          </button>

          {totalUnidades > 0 && (
            <button
              type="button"
              onClick={onLimpiar}
              className="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 cursor-pointer"
              title="Poner todas las cantidades en cero"
            >
              <RotateCcw className="h-3 w-3 text-slate-400" />
              Limpiar
            </button>
          )}
        </div>
      </div>

      {/* Tabla de panes */}
      <div className="flex-1 overflow-y-auto max-h-[420px]">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="sticky top-0 bg-slate-100/90 backdrop-blur-xs text-[11px] font-semibold text-slate-600 uppercase tracking-wider border-b border-slate-200 z-10">
            <tr>
              <th className="py-2.5 px-4">Pan / Variedad</th>
              <th className="py-2.5 px-3 text-right">Costo unit.</th>
              <th className="py-2.5 px-4 text-center">Cantidad a hornear</th>
              <th className="py-2.5 px-4 text-right">Subtotal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-800">
            {filasFiltradas.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-8 text-center text-slate-400">
                  No se encontraron productos coincidentes.
                </td>
              </tr>
            ) : (
              filasFiltradas.map((fila) => {
                const cantidad = fila.cantidad_producida || 0;
                const tieneCantidad = cantidad > 0;
                const subtotal = (cantidad * fila.costo_unitario).toFixed(2);

                return (
                  <tr
                    key={fila.id_producto}
                    className={`transition-colors ${
                      tieneCantidad
                        ? 'bg-amber-50/40 hover:bg-amber-50/70 font-medium'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <td className="py-2.5 px-4">
                      <div className="flex flex-col">
                        <span className="font-semibold text-slate-900">
                          {fila.nombre_producto}
                        </span>
                        {fila.categoria_nombre && (
                          <span className="text-[10px] text-slate-400 font-normal">
                            {fila.categoria_nombre}
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-2.5 px-3 text-right text-slate-500">
                      Bs {fila.costo_unitario.toFixed(2)}
                    </td>

                    <td className="py-2 px-4">
                      <div className="flex items-center justify-center gap-1.5">
                        {/* Botón restar rápido */}
                        <button
                          type="button"
                          onClick={() =>
                            onCambiarCantidad(
                              fila.id_producto,
                              Math.max(0, cantidad - (cantidad > 10 ? 10 : 1))
                            )
                          }
                          disabled={cantidad <= 0}
                          className="h-7 w-7 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center cursor-pointer transition-colors"
                          aria-label={`Restar ${fila.nombre_producto}`}
                        >
                          <Minus className="h-3 w-3" />
                        </button>

                        {/* Input de cantidad */}
                        <input
                          type="number"
                          min="0"
                          step="1"
                          value={cantidad === 0 ? '' : cantidad}
                          onChange={(e) => {
                            const val = parseInt(e.target.value, 10);
                            onCambiarCantidad(
                              fila.id_producto,
                              isNaN(val) || val < 0 ? 0 : val
                            );
                          }}
                          placeholder="0"
                          className={`w-20 text-center rounded-lg border py-1 px-2 font-bold text-xs focus:outline-none focus:ring-2 ${
                            tieneCantidad
                              ? 'border-amber-500 bg-white text-amber-950 focus:ring-amber-500'
                              : 'border-slate-200 bg-slate-50 text-slate-600 focus:ring-slate-300'
                          }`}
                        />

                        {/* Botón sumar rápido */}
                        <button
                          type="button"
                          onClick={() =>
                            onCambiarCantidad(fila.id_producto, cantidad + 10)
                          }
                          className="h-7 w-7 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 flex items-center justify-center cursor-pointer transition-colors"
                          title="Sumar +10 unidades"
                          aria-label={`Sumar 10 a ${fila.nombre_producto}`}
                        >
                          <Plus className="h-3 w-3" />
                        </button>
                      </div>
                    </td>

                    <td className="py-2.5 px-4 text-right font-mono">
                      {tieneCantidad ? (
                        <span className="font-semibold text-slate-900">
                          Bs {subtotal}
                        </span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pie de tabla con resumen */}
      <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-4 py-2.5 text-xs text-slate-600">
        <span>
          Mostrando <strong>{filasFiltradas.length}</strong> variedades de pan
        </span>
        <span className="font-medium">
          Total ingresado:{' '}
          <strong className="text-slate-900">{totalUnidades} unidades</strong>
        </span>
      </div>
    </div>
  );
};

export default TablaLoteProduccion;
