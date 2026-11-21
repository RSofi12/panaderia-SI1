import React, { useState } from 'react';

export interface DonutSegment {
  etiqueta: string;
  valor: number;
  color: string;
  colorHover?: string;
  formateado?: string;
}

interface DonutChartProps {
  segmentos: DonutSegment[];
  tituloCentro?: string;
  subtituloCentro?: string;
  tamano?: number;
  grosor?: number;
}

export const DonutChart: React.FC<DonutChartProps> = ({
  segmentos,
  tituloCentro,
  subtituloCentro,
  tamano = 200,
  grosor = 26,
}) => {
  const [activo, setActivo] = useState<number | null>(null);

  const total = segmentos.reduce((acc, s) => acc + s.valor, 0);
  const radio = (tamano - grosor) / 2;
  const circunferencia = 2 * Math.PI * radio;

  let acumulado = 0;

  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-around">
      {/* Gráfico circular interactivo en SVG nativo */}
      <div className="relative shrink-0" style={{ width: tamano, height: tamano }}>
        <svg
          width={tamano}
          height={tamano}
          viewBox={`0 0 ${tamano} ${tamano}`}
          className="-rotate-90 transform"
        >
          {total === 0 ? (
            <circle
              cx={tamano / 2}
              cy={tamano / 2}
              r={radio}
              fill="transparent"
              stroke="#f1f5f9"
              strokeWidth={grosor}
            />
          ) : (
            segmentos.map((segmento, idx) => {
              const porcentaje = segmento.valor / total;
              const longitudSegmento = porcentaje * circunferencia;
              const desfase = acumulado * circunferencia;
              acumulado += porcentaje;
              const estaActivo = activo === idx;

              return (
                <circle
                  key={segmento.etiqueta}
                  cx={tamano / 2}
                  cy={tamano / 2}
                  r={radio}
                  fill="transparent"
                  stroke={segmento.color}
                  strokeWidth={estaActivo ? grosor + 4 : grosor}
                  strokeDasharray={`${longitudSegmento} ${circunferencia - longitudSegmento}`}
                  strokeDashoffset={-desfase}
                  strokeLinecap="round"
                  onMouseEnter={() => setActivo(idx)}
                  onMouseLeave={() => setActivo(null)}
                  className="cursor-pointer transition-all duration-300 ease-out"
                />
              );
            })
          )}
        </svg>

        {/* Texto central con métrica */}
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-[11px] font-medium text-slate-400">
            {activo !== null ? segmentos[activo]?.etiqueta : tituloCentro || 'Total'}
          </span>
          <span className="text-base font-extrabold text-slate-900 leading-tight">
            {activo !== null
              ? `${Math.round(((segmentos[activo]?.valor || 0) / (total || 1)) * 100)}%`
              : subtituloCentro || (total > 0 ? `${total.toLocaleString('es-BO')}` : '0')}
          </span>
        </div>
      </div>

      {/* Leyenda interactiva */}
      <div className="space-y-2 text-xs">
        {segmentos.map((s, idx) => {
          const pct = total > 0 ? Math.round((s.valor / total) * 100) : 0;
          const estaActivo = activo === idx;

          return (
            <div
              key={s.etiqueta}
              onMouseEnter={() => setActivo(idx)}
              onMouseLeave={() => setActivo(null)}
              className={`flex items-center justify-between gap-4 rounded-lg px-2.5 py-1.5 transition-colors cursor-pointer ${
                estaActivo ? 'bg-slate-100 font-bold' : 'hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className="h-3 w-3 shrink-0 rounded-full transition-transform"
                  style={{
                    backgroundColor: s.color,
                    transform: estaActivo ? 'scale(1.25)' : 'scale(1)',
                  }}
                />
                <span className="text-slate-700">{s.etiqueta}</span>
              </div>
              <div className="text-right">
                <span className="font-semibold text-slate-900">{s.formateado || s.valor}</span>
                <span className="ml-1.5 text-[10px] text-slate-400 font-medium">({pct}%)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DonutChart;
