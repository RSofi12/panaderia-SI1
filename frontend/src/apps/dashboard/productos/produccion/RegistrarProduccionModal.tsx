import React, { useEffect, useState } from 'react';
import {
  Calendar,
  Loader2,
  Save,
  Wheat,
  X,
} from 'lucide-react';
import productoService from '../../../../services/productoService';
import produccionService from '../../../../services/produccionService';
import type {
  BalanceMaterialesSimulacion,
  JornadaProduccion,
  ProduccionRegistro,
  RenglonLoteProduccion,
} from '../../../../types/produccion';
import { JORNADAS_LABELS } from '../../../../types/produccion';
import TablaLoteProduccion from './components/TablaLoteProduccion';
import BalanceInsumosCard from './components/BalanceInsumosCard';

interface RegistrarProduccionModalProps {
  abierto: boolean;
  onCerrar: () => void;
  onGuardado: (registro: ProduccionRegistro) => void;
}

export const RegistrarProduccionModal: React.FC<RegistrarProduccionModalProps> = ({
  abierto,
  onCerrar,
  onGuardado,
}) => {
  const hoyStr = new Date().toISOString().split('T')[0];

  const [fecha, setFecha] = useState(hoyStr);
  const [jornada, setJornada] = useState<JornadaProduccion>('unica');
  const [filas, setFilas] = useState<RenglonLoteProduccion[]>([]);
  const [cargandoProductos, setCargandoProductos] = useState(true);

  const [balance, setBalance] = useState<BalanceMaterialesSimulacion>({
    es_viable: true,
    total_panes_unidades: 0,
    costo_estimado_total: 0,
    insumos: [],
  });
  const [calculandoBalance, setCalculandoBalance] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [errorGuardado, setErrorGuardado] = useState<string | null>(null);

  // 1. Cargar catálogo de productos activos al abrir el modal
  useEffect(() => {
    if (!abierto) return;

    let vigente = true;
    setCargandoProductos(true);
    setErrorGuardado(null);

    productoService
      .listar({ activo: 'true' })
      .then((productos) => {
        if (!vigente) return;
        const renglones: RenglonLoteProduccion[] = productos.map((p) => ({
          id_producto: p.id_producto,
          nombre_producto: p.nombre,
          categoria_nombre: p.categoria_nombre,
          costo_unitario: parseFloat(p.costo_produccion) || 0.5,
          cantidad_producida: 0,
        }));
        setFilas(renglones);
      })
      .catch(() => {
        if (!vigente) return;
        // Si el backend de productos no estuviera disponible, creamos lista con los 12 panes estándar
        const lotePorDefecto: RenglonLoteProduccion[] = [
          { id_producto: 1, nombre_producto: 'Marraqueta', categoria_nombre: 'Tradicionales', costo_unitario: 0.4, cantidad_producida: 0 },
          { id_producto: 2, nombre_producto: 'Casero', categoria_nombre: 'Tradicionales', costo_unitario: 0.45, cantidad_producida: 0 },
          { id_producto: 3, nombre_producto: 'Tortilla', categoria_nombre: 'Tradicionales', costo_unitario: 1.2, cantidad_producida: 0 },
          { id_producto: 4, nombre_producto: 'Arani', categoria_nombre: 'Regionales', costo_unitario: 0.5, cantidad_producida: 0 },
          { id_producto: 5, nombre_producto: 'Chama', categoria_nombre: 'Regionales', costo_unitario: 0.55, cantidad_producida: 0 },
          { id_producto: 6, nombre_producto: 'Integral', categoria_nombre: 'Integrales', costo_unitario: 0.6, cantidad_producida: 0 },
          { id_producto: 7, nombre_producto: 'Pan Dulce', categoria_nombre: 'Dulces', costo_unitario: 0.7, cantidad_producida: 0 },
          { id_producto: 8, nombre_producto: 'Pan con Azúcar', categoria_nombre: 'Dulces', costo_unitario: 0.65, cantidad_producida: 0 },
          { id_producto: 9, nombre_producto: 'Gusanito', categoria_nombre: 'Rellenos', costo_unitario: 1.0, cantidad_producida: 0 },
          { id_producto: 10, nombre_producto: 'Pan Mollete', categoria_nombre: 'Pequeños', costo_unitario: 0.4, cantidad_producida: 0 },
          { id_producto: 11, nombre_producto: 'Pan Galleta', categoria_nombre: 'Pequeños', costo_unitario: 0.35, cantidad_producida: 0 },
          { id_producto: 12, nombre_producto: 'Pan de Leche', categoria_nombre: 'De Leche', costo_unitario: 0.8, cantidad_producida: 0 },
        ];
        setFilas(lotePorDefecto);
      })
      .finally(() => {
        if (vigente) setCargandoProductos(false);
      });

    return () => {
      vigente = false;
    };
  }, [abierto]);

  // 2. Simular consumo en tiempo real con debounce
  useEffect(() => {
    if (!abierto || filas.length === 0) return;

    let vigente = true;
    setCalculandoBalance(true);

    const temporizador = setTimeout(async () => {
      try {
        const detalles = filas
          .filter((f) => f.cantidad_producida > 0)
          .map((f) => ({
            id_producto: f.id_producto,
            cantidad_producida: f.cantidad_producida,
          }));

        const res = await produccionService.simularConsumo(detalles);
        if (vigente) {
          setBalance(res);
          setErrorGuardado(null);
        }
      } catch (err) {
        // En caso de fallo de red al simular
      } finally {
        if (vigente) setCalculandoBalance(false);
      }
    }, 150);

    return () => {
      vigente = false;
      clearTimeout(temporizador);
    };
  }, [filas, abierto]);

  // Manejadores de tabla
  const handleCambiarCantidad = (idProducto: number, cantidad: number) => {
    setFilas((prev) =>
      prev.map((f) =>
        f.id_producto === idProducto ? { ...f, cantidad_producida: cantidad } : f
      )
    );
  };

  const handleCargarHabitual = () => {
    const habitual = produccionService.obtenerLoteHabitual();
    setFilas((prev) =>
      prev.map((f) => ({
        ...f,
        cantidad_producida: habitual[f.id_producto] || 0,
      }))
    );
  };

  const handleLimpiar = () => {
    setFilas((prev) => prev.map((f) => ({ ...f, cantidad_producida: 0 })));
  };

  // Confirmar y registrar la producción
  const handleConfirmar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!balance.es_viable || balance.total_panes_unidades <= 0) return;

    setGuardando(true);
    setErrorGuardado(null);

    try {
      const payload = {
        fecha,
        jornada,
        detalles: filas
          .filter((f) => f.cantidad_producida > 0)
          .map((f) => ({
            id_producto: f.id_producto,
            cantidad_producida: f.cantidad_producida,
          })),
      };

      const registro = await produccionService.registrarProduccion(payload);
      onGuardado(registro);
      onCerrar();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorGuardado(err.message);
      } else {
        setErrorGuardado('Ocurrió un error inesperado al registrar la producción.');
      }
    } finally {
      setGuardando(false);
    }
  };

  if (!abierto) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-registrar-produccion"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-900/60 backdrop-blur-xs"
    >
      <div className="relative flex flex-col w-full max-w-6xl h-[92vh] max-h-[850px] bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
        {/* Encabezado del modal */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-slate-50/90 px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-600 text-white shadow-md shadow-amber-600/30">
              <Wheat className="h-5 w-5" />
            </span>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
                MRP · Transacción Atómica (CU10)
              </p>
              <h2
                id="titulo-registrar-produccion"
                className="text-lg font-bold text-slate-900"
              >
                Registrar Producción Diaria
              </h2>
            </div>
          </div>

          {/* Selector de Fecha y Jornada */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Input Fecha */}
            <div className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 shadow-2xs">
              <Calendar className="h-3.5 w-3.5 text-slate-400" />
              <input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                className="text-xs font-semibold text-slate-800 focus:outline-none"
              />
            </div>

            {/* Selector de Jornada (Pills) */}
            <div className="flex items-center rounded-xl border border-slate-200 bg-slate-100 p-1">
              {(['manana', 'tarde', 'noche', 'unica'] as JornadaProduccion[]).map((j) => (
                <button
                  key={j}
                  type="button"
                  onClick={() => setJornada(j)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors cursor-pointer ${
                    jornada === j
                      ? 'bg-white text-slate-900 shadow-2xs'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  {JORNADAS_LABELS[j]}
                </button>
              ))}
            </div>

            {/* Botón Cerrar */}
            <button
              type="button"
              onClick={onCerrar}
              className="rounded-xl p-2 text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition-colors cursor-pointer"
              aria-label="Cerrar modal"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Mensaje de error general si falló la validación o el backend */}
        {errorGuardado && (
          <div className="bg-rose-50 border-b border-rose-200 px-6 py-2.5 text-xs text-rose-800 font-medium flex items-center justify-between">
            <span>{errorGuardado}</span>
            <button
              type="button"
              onClick={() => setErrorGuardado(null)}
              className="text-rose-600 hover:text-rose-900 font-bold ml-3 cursor-pointer"
            >
              Cerrar aviso
            </button>
          </div>
        )}

        {/* Cuerpo del modal en 2 columnas: Izquierda (Tabla de panes), Derecha (Balance de insumos) */}
        <div className="flex-1 overflow-hidden p-5 bg-slate-50/40">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 h-full">
            {/* Columna Izquierda: Carga de productos (7 cols) */}
            <div className="lg:col-span-7 h-full flex flex-col">
              {cargandoProductos ? (
                <div className="flex flex-col items-center justify-center h-full bg-white rounded-2xl border border-slate-200 p-8 text-slate-400">
                  <Loader2 className="h-8 w-8 animate-spin text-amber-600 mb-2" />
                  <p className="text-xs">Cargando catálogo de panes...</p>
                </div>
              ) : (
                <TablaLoteProduccion
                  filas={filas}
                  onCambiarCantidad={handleCambiarCantidad}
                  onCargarHabitual={handleCargarHabitual}
                  onLimpiar={handleLimpiar}
                />
              )}
            </div>

            {/* Columna Derecha: Balance de insumos (5 cols) */}
            <div className="lg:col-span-5 h-full flex flex-col">
              <BalanceInsumosCard
                balance={balance}
                cargando={calculandoBalance}
              />
            </div>
          </div>
        </div>

        {/* Pie de modal con acciones */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 bg-white px-6 py-4">
          <div className="text-xs text-slate-500">
            <span className="font-semibold text-slate-700">Regla atómica:</span> Descontará insumos del inventario de materia prima y sumará unidades al stock disponible de panes terminados.
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onCerrar}
              disabled={guardando}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer disabled:opacity-50"
            >
              Cancelar
            </button>

            <button
              type="button"
              onClick={handleConfirmar}
              disabled={
                guardando ||
                !balance.es_viable ||
                balance.total_panes_unidades <= 0
              }
              className={`inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-xs font-bold text-white shadow-md transition-all cursor-pointer ${
                balance.es_viable && balance.total_panes_unidades > 0 && !guardando
                  ? 'bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 shadow-amber-600/30'
                  : 'bg-slate-300 shadow-none cursor-not-allowed opacity-60'
              }`}
            >
              {guardando ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Procesando lote y descontando stock...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Confirmar y Descontar Inventario
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegistrarProduccionModal;
