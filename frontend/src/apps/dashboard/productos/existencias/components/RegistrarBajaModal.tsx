import React, { useState, useMemo } from 'react';
import { X, AlertTriangle, AlertOctagon, CheckCircle2, Package, Info } from 'lucide-react';
import type { ExistenciaProducto, NotaPerdida } from '../../../../../types/existencias';
import { existenciasService } from '../../../../../services/existenciasService';

interface RegistrarBajaModalProps {
  existencias: ExistenciaProducto[];
  productoInicial?: ExistenciaProducto | null;
  onClose: () => void;
  onBajaRegistrada: (nota: NotaPerdida) => void;
}

const MOTIVOS_MERMA = [
  'Expiración / Vencimiento',
  'Defecto de Horneado / Quemado',
  'Daño / Mala manipulación',
  'Pérdida / Rotura accidental',
  'Devolución en mal estado',
  'Contaminación o plaga',
  'Otro motivo',
];

export const RegistrarBajaModal: React.FC<RegistrarBajaModalProps> = ({
  existencias,
  productoInicial,
  onClose,
  onBajaRegistrada,
}) => {
  const productosConStock = useMemo(() => {
    return existencias.filter((p) => p.stock_actual > 0);
  }, [existencias]);

  const [idProductoSeleccionado, setIdProductoSeleccionado] = useState<number>(() => {
    if (productoInicial && productoInicial.stock_actual > 0) {
      return productoInicial.id_producto;
    }
    return productosConStock[0]?.id_producto || 0;
  });

  const [cantidad, setCantidad] = useState<number>(1);
  const [motivo, setMotivo] = useState<string>(MOTIVOS_MERMA[0]);
  const [observaciones, setObservaciones] = useState<string>('');
  const [procesando, setProcesando] = useState<boolean>(false);
  const [errorServidor, setErrorServidor] = useState<string | null>(null);

  const productoActual = useMemo(() => {
    return existencias.find((p) => p.id_producto === idProductoSeleccionado);
  }, [existencias, idProductoSeleccionado]);

  const stockDisponible = productoActual?.stock_actual || 0;
  const precioUnitario = productoActual ? Number(productoActual.precio_venta) : 0;
  const costoUnitarioEstimado = precioUnitario > 0 ? Number((precioUnitario * 0.65).toFixed(2)) : 0.5;
  const valorPerdidaEstimado = (cantidad * costoUnitarioEstimado).toFixed(2);

  const errorCantidad = useMemo(() => {
    if (cantidad <= 0) return 'La cantidad a dar de baja debe ser mayor a 0.';
    if (cantidad > stockDisponible) {
      return `No puedes dar de baja más unidades de las disponibles en vitrina (${stockDisponible}).`;
    }
    return null;
  }, [cantidad, stockDisponible]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productoActual || errorCantidad || stockDisponible <= 0) return;

    setProcesando(true);
    setErrorServidor(null);

    try {
      const nota = await existenciasService.registrarBaja({
        id_producto: idProductoSeleccionado,
        cantidad,
        motivo,
        observaciones: observaciones.trim() ? `${motivo}: ${observaciones.trim()}` : motivo,
      });

      onBajaRegistrada(nota);
      onClose();
    } catch (err: unknown) {
      let mensaje = 'Error al procesar la baja del producto en el servidor.';
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const responseData = (err as { response?: { data?: { error?: string; detail?: string } } }).response?.data;
        if (responseData?.error) mensaje = responseData.error;
        else if (responseData?.detail) mensaje = responseData.detail;
      }
      setErrorServidor(mensaje);
    } finally {
      setProcesando(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-baja-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div
        className="bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-linear-to-r from-rose-50/70 to-amber-50/50">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-100 text-rose-700 shadow-2xs">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <h2 id="modal-baja-title" className="text-base font-bold text-slate-900">
                Registrar Baja de Producto (Merma)
              </h2>
              <p className="text-xs text-slate-500">
                CU18: Descuenta stock en vitrina y genera movimiento de salida
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={procesando}
            aria-label="Cerrar modal"
            className="text-slate-400 hover:text-slate-700 hover:bg-slate-100 p-1.5 rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
          {errorServidor && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5 animate-in fade-in">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
              <div className="flex-1">
                <p className="font-bold">No se pudo registrar la baja</p>
                <p className="mt-0.5">{errorServidor}</p>
              </div>
            </div>
          )}

          <div>
            <label className="block mb-1.5 text-xs font-bold uppercase tracking-wider text-slate-600">
              Producto Terminado <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <select
                value={idProductoSeleccionado}
                onChange={(e) => {
                  setIdProductoSeleccionado(Number(e.target.value));
                  setCantidad(1);
                }}
                disabled={procesando || productosConStock.length === 0}
                className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 transition-all font-medium"
              >
                {productosConStock.length === 0 ? (
                  <option value={0}>No hay productos con stock disponible</option>
                ) : (
                  productosConStock.map((prod) => (
                    <option key={prod.id_producto} value={prod.id_producto}>
                      {prod.producto_nombre} — Stock: {prod.stock_actual} un. ({prod.categoria_nombre})
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          {productoActual && (
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-amber-100 text-amber-800">
                  <Package className="w-4 h-4" />
                </div>
                <div>
                  <p className="font-bold text-slate-800">{productoActual.producto_nombre}</p>
                  <p className="text-slate-500 text-[11px]">{productoActual.categoria_nombre}</p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-[11px] text-slate-500 block">Stock actual en vitrina</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full font-bold text-xs bg-emerald-100 text-emerald-800">
                  {stockDisponible} un.
                </span>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block mb-1.5 text-xs font-bold uppercase tracking-wider text-slate-600">
                Cantidad a dar de baja <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                min="1"
                max={stockDisponible || 1}
                value={cantidad}
                onChange={(e) => setCantidad(parseInt(e.target.value) || 0)}
                disabled={procesando || stockDisponible <= 0}
                className={`w-full px-3.5 py-2.5 text-sm font-semibold rounded-xl border ${
                  errorCantidad
                    ? 'border-rose-300 bg-rose-50/50 text-rose-900 focus:ring-rose-500/20 focus:border-rose-500'
                    : 'border-slate-300 bg-white text-slate-800 focus:ring-rose-500/20 focus:border-rose-500'
                } focus:outline-none focus:ring-2 transition-all`}
              />
              {errorCantidad && (
                <p className="mt-1 text-xs text-rose-600 font-medium">{errorCantidad}</p>
              )}
            </div>

            <div>
              <label className="block mb-1.5 text-xs font-bold uppercase tracking-wider text-slate-600">
                Causa o Motivo <span className="text-rose-500">*</span>
              </label>
              <select
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                disabled={procesando}
                className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 transition-all font-medium"
              >
                {MOTIVOS_MERMA.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-xs flex items-center justify-between text-amber-900">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Pérdida estimada proyectada:</span>
            </div>
            <div className="text-right font-bold text-amber-950 text-sm">
              Bs. {valorPerdidaEstimado}
            </div>
          </div>

          <div>
            <label className="block mb-1.5 text-xs font-bold uppercase tracking-wider text-slate-600">
              Observaciones adicionales <span className="text-slate-400 font-normal">(Opcional)</span>
            </label>
            <textarea
              rows={2}
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              disabled={procesando}
              placeholder="Ej: 4 unidades quemadas en horneado matutino lote #102..."
              className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 transition-all resize-none"
            />
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={procesando}
              className="px-4 py-2.5 text-sm font-semibold rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
            >
              Cancelar
            </button>

            <button
              type="submit"
              disabled={procesando || Boolean(errorCantidad) || stockDisponible <= 0}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold rounded-xl bg-rose-600 text-white hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg transition-all cursor-pointer"
            >
              {procesando ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Procesando Baja...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Confirmar y Descontar Stock</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};