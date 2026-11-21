import React from 'react';

interface KpiCardProps {
  titulo: string;
  valor: string | number;
  subtexto?: string;
  icono: React.ElementType;
  tendencia?: {
    valor: string;
    esPositiva?: boolean;
    esNeutra?: boolean;
  };
  variante?: 'amber' | 'emerald' | 'rose' | 'slate' | 'indigo';
  onClick?: () => void;
}

const VARIANTE_COLORES = {
  amber: {
    fondoIcono: 'bg-amber-100 text-amber-800',
    bordeHover: 'hover:border-amber-300',
  },
  emerald: {
    fondoIcono: 'bg-emerald-100 text-emerald-800',
    bordeHover: 'hover:border-emerald-300',
  },
  rose: {
    fondoIcono: 'bg-rose-100 text-rose-800',
    bordeHover: 'hover:border-rose-300',
  },
  slate: {
    fondoIcono: 'bg-slate-100 text-slate-800',
    bordeHover: 'hover:border-slate-300',
  },
  indigo: {
    fondoIcono: 'bg-indigo-100 text-indigo-800',
    bordeHover: 'hover:border-indigo-300',
  },
};

export const KpiCard: React.FC<KpiCardProps> = ({
  titulo,
  valor,
  subtexto,
  icono: Icono,
  tendencia,
  variante = 'amber',
  onClick,
}) => {
  const estilos = VARIANTE_COLORES[variante];

  return (
    <div
      onClick={onClick}
      className={`group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-md ${
        estilos.bordeHover
      } ${onClick ? 'cursor-pointer' : ''}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-medium text-slate-500 tracking-normal">{titulo}</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-2xl font-bold tracking-tight text-slate-900 transition-colors group-hover:text-amber-900">
              {valor}
            </h3>
          </div>
        </div>

        <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-transform duration-300 ease-out group-hover:scale-105 ${estilos.fondoIcono}`}>
          <Icono className="h-5 w-5" />
        </div>
      </div>

      {(subtexto || tendencia) && (
        <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2.5 text-[11px]">
          {tendencia && (
            <span
              className={`inline-flex items-center font-semibold ${
                tendencia.esNeutra
                  ? 'text-slate-600'
                  : tendencia.esPositiva
                  ? 'text-emerald-700'
                  : 'text-rose-700'
              }`}
            >
              {tendencia.valor}
            </span>
          )}
          {subtexto && <span className="text-slate-400">{subtexto}</span>}
        </div>
      )}
    </div>
  );
};

export default KpiCard;
