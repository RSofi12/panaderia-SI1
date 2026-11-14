import React, { useState } from 'react';

export interface ColumnBarItem {
  etiqueta: string;
  valor: number;
  valorSecundario?: string;
  color?: string;
}

interface ColumnBarChartProps {
  items: ColumnBarItem[];
  altura?: number;
  prefijoValor?: string;
}

export const ColumnBarChart: React.FC<ColumnBarChartProps> = ({
  items,
  altura = 180,
  prefijoValor = '',
}) => {
  const [seleccionado, setSeleccionado] = useState<number | null>(null);

  const valorMaximo = Math.max(...items.map((i) => i.valor), 1);

  return (
    <div className="space-y-3">
      {/* Contenedor de columnas */}
      <div
        className="flex items-end justify-between gap-2 border-b border-slate-200 px-2 pt-6"
        style={{ height: altura }}
      >
        {items.map((item, idx) => {
          const porcentajeAltura = Math.min(100, Math.max(12, (item.valor / valorMaximo) * 100));
          const esActivo = seleccionado === idx;

          return (
            <div
              key={item.etiqueta}
              onMouseEnter={() => setSeleccionado(idx)}
              onMouseLeave={() => setSeleccionado(null)}
              className="group relative flex flex-1 flex-col items-center cursor-pointer"
            >
              {/* Tooltip flotante al pasar el mouse */}
              <div
                className={`pointer-events-none absolute -top-9 z-10 rounded-md bg-slate-900 px-2 py-1 text-[10px] font-bold text-white shadow-md transition-all duration-200 ${
                  esActivo ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
                }`}
              >
                {prefijoValor}{item.valor.toLocaleString('es-BO')}
                {item.valorSecundario ? ` (${item.valorSecundario})` : ''}
              </div>

              {/* Columna vertical */}
              <div className="relative w-full max-w-10 flex flex-col justify-end h-full">
                <div
                  className={`w-full rounded-t-xl transition-all duration-300 ease-out ${
                    item.color || 'bg-amber-600 hover:bg-amber-700'
                  } ${esActivo ? 'brightness-110 shadow-sm -translate-y-1' : ''}`}
                  style={{ height: `${porcentajeAltura}%` }}
                />
              </div>

              {/* Valor numérico encima o en la base */}
              <span className="mt-1.5 text-[11px] font-bold text-slate-700 group-hover:text-amber-800">
                {item.valor}
              </span>
            </div>
          );
        })}
      </div>

      {/* Etiquetas horizontales inferiores */}
      <div className="flex justify-between gap-2 px-2 text-center">
        {items.map((item, idx) => (
          <div
            key={item.etiqueta}
            className={`flex-1 truncate text-[11px] transition-colors ${
              seleccionado === idx ? 'font-bold text-slate-900' : 'text-slate-500'
            }`}
            title={item.etiqueta}
          >
            {item.etiqueta}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ColumnBarChart;
