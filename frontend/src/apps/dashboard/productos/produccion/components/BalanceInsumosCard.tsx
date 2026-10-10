import React from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Coins,
  Layers,
  Scale,
  Wheat,
} from 'lucide-react';
import type { BalanceMaterialesSimulacion } from '../../../../../types/produccion';

interface BalanceInsumosCardProps {
  balance: BalanceMaterialesSimulacion;
  cargando?: boolean;
}

export const BalanceInsumosCard: React.FC<BalanceInsumosCardProps> = ({
  balance,
  cargando = false,
}) => {
  const tieneProductos = balance.total_panes_unidades > 0;

  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      {/* Encabezado */}
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-100 text-amber-800">
              <Wheat className="h-4 w-4" />
            </span>
            <h3 className="text-base font-bold text-slate-900">Balance de Insumos</h3>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Explosión de receta (MRP): consumo proyectado vs stock actual
          </p>
        </div>

        {tieneProductos && (
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${
              balance.es_viable
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-rose-50 text-rose-700 border border-rose-200 animate-pulse'
            }`}
          >
            {balance.es_viable ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                Stock suficiente
              </>
            ) : (
              <>
                <AlertTriangle className="h-3.5 w-3.5 text-rose-600" />
                Stock insuficiente
              </>
            )}
          </span>
        )}
      </div>

      {/* Métricas rápidas del lote */}
      <div className="grid grid-cols-2 gap-3 py-3.5 border-b border-slate-100">
        <div className="flex items-center gap-2.5 rounded-xl bg-slate-50 p-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-slate-700 shadow-2xs">
            <Layers className="h-4 w-4" />
          </span>
          <div>
            <p className="text-[11px] font-medium text-slate-500">Total unidades</p>
            <p className="text-base font-bold text-slate-900">
              {balance.total_panes_unidades.toLocaleString('es-BO')} <span className="text-xs font-normal text-slate-500">panes</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-xl bg-amber-50/60 p-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-amber-700 shadow-2xs">
            <Coins className="h-4 w-4" />
          </span>
          <div>
            <p className="text-[11px] font-medium text-amber-900/70">Costo estimado</p>
            <p className="text-base font-bold text-amber-950">
              Bs {balance.costo_estimado_total.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Alerta crítica si falta stock */}
      {!balance.es_viable && tieneProductos && (
        <div className="mt-3.5 rounded-xl border border-rose-200 bg-rose-50/90 p-3 text-xs text-rose-900">
          <div className="flex items-center gap-2 font-semibold text-rose-950">
            <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
            No se puede completar el registro
          </div>
          <p className="mt-1 text-rose-800 leading-relaxed">
            Hay insumos requeridos que superan las existencias actuales en almacén.
            Ajusta las cantidades producidas o registra una compra previa (CU07).
          </p>
        </div>
      )}

      {/* Lista de insumos requeridos */}
      <div className="flex-1 overflow-y-auto mt-3.5 space-y-2.5 pr-1 max-h-[340px]">
        {!tieneProductos ? (
          <div className="flex flex-col items-center justify-center py-12 text-center text-slate-400">
            <Scale className="h-10 w-10 stroke-[1.5] text-slate-300 mb-2" />
            <p className="text-xs font-medium text-slate-600">Sin unidades ingresadas</p>
            <p className="text-[11px] text-slate-400 max-w-[220px] mt-0.5">
              Escribe cantidades en la lista de panes para calcular el consumo de insumos.
            </p>
          </div>
        ) : balance.insumos.length === 0 ? (
          <p className="text-center py-6 text-xs text-slate-400">
            Los productos seleccionados no tienen receta configurada.
          </p>
        ) : (
          balance.insumos.map((insumo) => {
            const porcentajeUso = Math.min(
              100,
              Math.round((insumo.cantidad_requerida / (insumo.stock_disponible || 1)) * 100)
            );

            return (
              <div
                key={insumo.id_materia_prima}
                className={`rounded-xl border p-3 transition-colors ${
                  insumo.suficiente
                    ? 'border-slate-100 bg-slate-50/70 hover:bg-slate-50'
                    : 'border-rose-300 bg-rose-50/80'
                }`}
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        insumo.suficiente ? 'bg-emerald-500' : 'bg-rose-500 ring-2 ring-rose-200'
                      }`}
                    />
                    {insumo.nombre_insumo}
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-slate-900">
                      {insumo.cantidad_requerida.toFixed(3)} {insumo.unidad_medida}
                    </span>
                    <span className="text-slate-400 text-[11px]">
                      {' '}/ disp: {insumo.stock_disponible.toFixed(2)} {insumo.unidad_medida}
                    </span>
                  </div>
                </div>

                {/* Barra de consumo */}
                <div className="mt-2 h-1.5 w-full rounded-full bg-slate-200 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      insumo.suficiente ? 'bg-amber-600' : 'bg-rose-600'
                    }`}
                    style={{ width: `${Math.min(100, porcentajeUso)}%` }}
                  />
                </div>

                {!insumo.suficiente && (
                  <div className="mt-1.5 flex items-center justify-between text-[11px] font-semibold text-rose-700">
                    <span>Falta para este lote:</span>
                    <span>
                      -{insumo.diferencia_faltante.toFixed(3)} {insumo.unidad_medida}
                    </span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {cargando && (
        <p className="mt-2 text-center text-[11px] text-slate-400">
          Recalculando balance de insumos...
        </p>
      )}
    </div>
  );
};

export default BalanceInsumosCard;
