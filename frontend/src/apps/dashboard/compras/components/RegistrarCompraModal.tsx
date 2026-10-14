import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Loader2, Plus, Trash2, X } from 'lucide-react';
import compraService from '../../../../services/compraService';
import proveedorService from '../../../../services/proveedorService';
import normalizarErrorApi from '../../../../services/erroresApi';
import type { Compra, CompraPayload, CompraReposicion, MateriaPrima } from '../../../../types/compra';
import type { Proveedor } from '../../../../types/proveedor';

interface RegistrarCompraModalProps {
  onClose: () => void;
  onSaved: (compra: Compra) => void;
  reposicion?: CompraReposicion;
}

/** Una fila del formulario. Los valores son string porque vienen de <input>. */
interface LineaForm {
  clave: number;
  id_materia_prima: string;
  cantidad: string;
  precio_unitario: string;
}

interface ErroresForm {
  general?: string;
  proveedor?: string;
  lineas: Record<number, string>;
}

const SIN_ERRORES: ErroresForm = { lineas: {} };

const aNumero = (valor: string): number => {
  const n = Number(valor);
  return Number.isFinite(n) ? n : 0;
};

const subtotalDe = (linea: LineaForm): number =>
  aNumero(linea.cantidad) * aNumero(linea.precio_unitario);

const formatoBs = (monto: number): string => `Bs ${monto.toFixed(2)}`;

const validar = (idProveedor: string, lineas: LineaForm[]): ErroresForm => {
  const errores: ErroresForm = { lineas: {} };
  if (!idProveedor) errores.proveedor = 'Seleccione un proveedor.';

  const vistos = new Set<string>();
  for (const linea of lineas) {
    if (!linea.id_materia_prima) {
      errores.lineas[linea.clave] = 'Elija un insumo.';
    } else if (vistos.has(linea.id_materia_prima)) {
      errores.lineas[linea.clave] = 'Este insumo ya está en otra línea.';
    } else if (aNumero(linea.cantidad) <= 0) {
      errores.lineas[linea.clave] = 'La cantidad debe ser mayor a 0.';
    } else if (aNumero(linea.precio_unitario) <= 0) {
      errores.lineas[linea.clave] = 'El precio debe ser mayor a 0.';
    }
    vistos.add(linea.id_materia_prima);
  }
  return errores;
};

const tieneErrores = (e: ErroresForm): boolean =>
  Boolean(e.general || e.proveedor) || Object.keys(e.lineas).length > 0;

const inputClass = (conError: boolean) =>
  `w-full px-3 py-2 bg-slate-50 border rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all ${
    conError ? 'border-red-300' : 'border-slate-200'
  }`;

export const RegistrarCompraModal: React.FC<RegistrarCompraModalProps> = ({ onClose, onSaved, reposicion }) => {
  const idMateriaReposicion = reposicion?.id_materia_prima;
  const contador = useRef(1);
  const nuevaLinea = (): LineaForm => ({
    clave: contador.current++,
    id_materia_prima: '',
    cantidad: '',
    precio_unitario: '',
  });

  const [proveedores, setProveedores] = useState<Proveedor[]>([]);
  const [materias, setMaterias] = useState<MateriaPrima[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  const [idProveedor, setIdProveedor] = useState('');
  const [lineas, setLineas] = useState<LineaForm[]>(() => [
    {
      clave: 0,
      id_materia_prima: reposicion ? String(reposicion.id_materia_prima) : '',
      cantidad: reposicion?.cantidad ?? '',
      precio_unitario: '',
    },
  ]);
  const [errores, setErrores] = useState<ErroresForm>(SIN_ERRORES);
  const [guardando, setGuardando] = useState(false);
  const [registrada, setRegistrada] = useState<Compra | null>(null);
  const bloqueado = guardando || registrada !== null;

  // Se deja ver la confirmación un momento antes de cerrar el modal.
  useEffect(() => {
    if (!registrada) return;
    const tieneAdvertencias = Boolean(registrada.advertencias && registrada.advertencias.length > 0);
    const tiempo = tieneAdvertencias ? 4500 : 1500;
    const temporizador = window.setTimeout(() => onSaved(registrada), tiempo);
    return () => window.clearTimeout(temporizador);
  }, [registrada, onSaved]);

  useEffect(() => {
    let cancelado = false;
    Promise.all([
      proveedorService.listar({ activo: 'true' }),
      compraService.listarMateriasPrimas({ activo: 'true' }),
    ])
      .then(([listaProveedores, listaMaterias]) => {
        if (cancelado) return;
        setProveedores(listaProveedores);
        const materiasActivas = listaMaterias.filter((materia) => materia.activo);
        setMaterias(materiasActivas);
        const materiaReposicion = materiasActivas.find((materia) => materia.id_materia_prima === idMateriaReposicion);
        if (materiaReposicion) {
          setLineas((actual) => actual.map((linea) => (
            linea.clave === 0 && linea.id_materia_prima === String(idMateriaReposicion)
              ? { ...linea, precio_unitario: linea.precio_unitario || materiaReposicion.precio_ultima_compra || '' }
              : linea
          )));
        }
      })
      .catch((err) => {
        if (!cancelado) setErrorCarga(normalizarErrorApi(err).mensaje ?? 'No se pudieron cargar los datos.');
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });
    return () => {
      cancelado = true;
    };
  }, [idMateriaReposicion]);

  const materiaPorId = new Map(materias.map((m) => [String(m.id_materia_prima), m]));
  const hayInsumosNoDisponibles = lineas.some((linea) => (
    Boolean(linea.id_materia_prima) && !materiaPorId.has(linea.id_materia_prima)
  ));
  const total = lineas.reduce((suma, linea) => suma + subtotalDe(linea), 0);

  const actualizarLinea = (clave: number, cambios: Partial<LineaForm>) => {
    setLineas((actual) => actual.map((l) => (l.clave === clave ? { ...l, ...cambios } : l)));
    setErrores((actual) => {
      const resto = { ...actual.lineas };
      delete resto[clave];
      return { ...actual, general: undefined, lineas: resto };
    });
  };

  const elegirInsumo = (linea: LineaForm, idMateria: string) => {
    const ultimoPrecio = materiaPorId.get(idMateria)?.precio_ultima_compra;
    actualizarLinea(linea.clave, {
      id_materia_prima: idMateria,
      precio_unitario: linea.precio_unitario || ultimoPrecio || '',
    });
  };

  const agregarLinea = () => setLineas((actual) => [...actual, nuevaLinea()]);

  const quitarLinea = (clave: number) =>
    setLineas((actual) => (actual.length > 1 ? actual.filter((l) => l.clave !== clave) : actual));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (bloqueado || cargando || errorCarga) return;
    const erroresLocales = validar(idProveedor, lineas);
    for (const linea of lineas) {
      if (linea.id_materia_prima && !materiaPorId.has(linea.id_materia_prima)) {
        erroresLocales.lineas[linea.clave] = 'El insumo ya no está disponible. Seleccione un insumo activo.';
      }
    }
    if (tieneErrores(erroresLocales)) {
      setErrores(erroresLocales);
      return;
    }

    const payload: CompraPayload = {
      id_proveedor: Number(idProveedor),
      detalles: lineas.map((l) => ({
        id_materia_prima: Number(l.id_materia_prima),
        cantidad: l.cantidad.trim(),
        precio_unitario: l.precio_unitario.trim(),
      })),
    };

    setGuardando(true);
    try {
      setRegistrada(await compraService.registrar(payload));
    } catch (err) {
      setErrores({
        lineas: {},
        general: normalizarErrorApi(err).mensaje ?? 'No se pudo registrar la compra.',
      });
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-compra"
        className="w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-xl border border-amber-100"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 id="titulo-compra" className="text-base font-bold text-slate-900">
              Registrar compra de materia prima
            </h2>
            <p className="text-xs text-slate-500">Suma stock y actualiza el último precio (CU7)</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={bloqueado}
            aria-label="Cerrar"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {cargando ? (
          <p className="px-6 py-10 text-center text-sm text-slate-500">Cargando proveedores e insumos...</p>
        ) : errorCarga ? (
          <div className="m-6 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{errorCarga}</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5 px-6 py-5" noValidate>
            {reposicion && (
              <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900">
                Reposición desde una alerta de stock. Revisa la cantidad, el proveedor y el precio antes de registrar la compra.
              </p>
            )}
            {hayInsumosNoDisponibles && (
              <div role="alert" className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
                <AlertTriangle aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" />
                <span>El insumo seleccionado ya no está disponible en el catálogo activo. Elige un insumo activo o cancela la compra.</span>
              </div>
            )}
            {registrada && (
              <div
                role="status"
                className={`flex flex-col gap-2 rounded-xl border p-4 shadow-xs ${
                  registrada.advertencias && registrada.advertencias.length > 0
                    ? 'border-amber-200 bg-amber-50 text-amber-900'
                    : 'border-emerald-200 bg-emerald-50 text-emerald-800'
                }`}
              >
                <div className="flex items-start gap-3">
                  {registrada.advertencias && registrada.advertencias.length > 0 ? (
                    <AlertTriangle className="w-5 h-5 mt-0.5 text-amber-600 shrink-0" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 mt-0.5 text-emerald-600 shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm font-bold">¡Compra registrada exitosamente!</p>
                    <p className="text-xs mt-0.5">
                      Compra #{registrada.id_compra} a {registrada.proveedor_nombre} por Bs {registrada.total}. El
                      stock ya fue actualizado.
                    </p>
                    {registrada.advertencias && registrada.advertencias.length > 0 && (
                      <div className="mt-2.5 rounded-lg border border-amber-200 bg-white/90 p-2.5 text-xs text-amber-900">
                        <p className="font-semibold text-amber-800">
                          Advertencia de variación inusual registrada en bitácora:
                        </p>
                        <ul className="mt-1 list-disc list-inside space-y-1 text-[11px] text-amber-800">
                          {registrada.advertencias.map((adv, idx) => (
                            <li key={idx}>{adv}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => onSaved(registrada)}
                    className="text-xs font-semibold underline text-amber-900 hover:text-amber-700 cursor-pointer self-start"
                  >
                    Aceptar
                  </button>
                </div>
              </div>
            )}

            {errores.general && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{errores.general}</span>
              </div>
            )}

            <fieldset disabled={bloqueado} className="space-y-5 transition-opacity disabled:opacity-60">
            <div>
              <label htmlFor="proveedor" className="block text-xs font-semibold text-slate-700 mb-1.5">
                Proveedor
              </label>
              <select
                id="proveedor"
                value={idProveedor}
                onChange={(e) => {
                  setIdProveedor(e.target.value);
                  setErrores((actual) => ({ ...actual, proveedor: undefined, general: undefined }));
                }}
                className={inputClass(Boolean(errores.proveedor))}
              >
                <option value="">Seleccione un proveedor activo</option>
                {proveedores.map((p) => (
                  <option key={p.id_proveedor} value={p.id_proveedor}>
                    {p.nombre}
                  </option>
                ))}
              </select>
              {errores.proveedor && <p className="mt-1 text-[11px] text-red-600">{errores.proveedor}</p>}
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Insumos comprados</span>
                <button
                  type="button"
                  onClick={agregarLinea}
                  className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-amber-700 hover:bg-amber-50 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" /> Agregar línea
                </button>
              </div>

              {lineas.map((linea, indice) => {
                const materia = materiaPorId.get(linea.id_materia_prima);
                const error = errores.lineas[linea.clave];
                const cantidadNum = aNumero(linea.cantidad);
                const precioNum = aNumero(linea.precio_unitario);
                const ultimoPrecioNum = materia?.precio_ultima_compra
                  ? Number(materia.precio_ultima_compra)
                  : null;

                // Variación porcentual en tiempo real
                let variacionPorcentual: number | null = null;
                if (ultimoPrecioNum && ultimoPrecioNum > 0 && precioNum > 0) {
                  const diff = precioNum - ultimoPrecioNum;
                  variacionPorcentual = (diff / ultimoPrecioNum) * 100;
                }

                return (
                  <div key={linea.clave} className="rounded-xl border border-slate-100 p-3 bg-white">
                    <div className="grid grid-cols-12 gap-2 items-end">
                      <div className="col-span-12 sm:col-span-5">
                        <label htmlFor={`insumo-${linea.clave}`} className="block text-[11px] text-slate-500 mb-1">
                          Insumo {indice + 1}
                        </label>
                        <select
                          id={`insumo-${linea.clave}`}
                          value={linea.id_materia_prima}
                          onChange={(e) => elegirInsumo(linea, e.target.value)}
                          className={inputClass(Boolean(error))}
                        >
                          <option value="">Elija un insumo</option>
                          {linea.id_materia_prima && !materia && (
                            <option value={linea.id_materia_prima} disabled>Insumo no disponible</option>
                          )}
                          {materias.map((m) => (
                            <option key={m.id_materia_prima} value={m.id_materia_prima}>
                              {m.nombre} ({m.unidad_medida})
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="col-span-4 sm:col-span-2">
                        <label htmlFor={`cantidad-${linea.clave}`} className="block text-[11px] text-slate-500 mb-1">
                          Cantidad {materia ? `(${materia.unidad_medida})` : ''}
                        </label>
                        <input
                          id={`cantidad-${linea.clave}`}
                          type="number"
                          min="0"
                          step="0.001"
                          inputMode="decimal"
                          value={linea.cantidad}
                          onChange={(e) => actualizarLinea(linea.clave, { cantidad: e.target.value })}
                          aria-describedby={reposicion && linea.clave === 0 && cantidadNum <= 0
                            ? 'ayuda-cantidad-reposicion'
                            : undefined}
                          className={inputClass(Boolean(error))}
                        />
                        {reposicion && linea.clave === 0 && cantidadNum <= 0 && (
                          <p id="ayuda-cantidad-reposicion" className="mt-1 text-[11px] text-amber-800">Indica una cantidad mayor a 0 para comprar.</p>
                        )}
                      </div>
                      <div className="col-span-4 sm:col-span-2">
                        <label htmlFor={`precio-${linea.clave}`} className="block text-[11px] text-slate-500 mb-1">
                          Precio unit. (Bs)
                        </label>
                        <input
                          id={`precio-${linea.clave}`}
                          type="number"
                          min="0"
                          step="0.01"
                          inputMode="decimal"
                          value={linea.precio_unitario}
                          onChange={(e) => actualizarLinea(linea.clave, { precio_unitario: e.target.value })}
                          className={inputClass(Boolean(error))}
                        />
                      </div>
                      <div className="col-span-3 sm:col-span-2 text-right">
                        <span className="block text-[11px] text-slate-500 mb-1">Subtotal</span>
                        <span className="block py-2 text-sm font-semibold text-slate-800">
                          {formatoBs(subtotalDe(linea))}
                        </span>
                      </div>
                      <div className="col-span-1 flex justify-end">
                        <button
                          type="button"
                          onClick={() => quitarLinea(linea.clave)}
                          disabled={lineas.length === 1}
                          aria-label={`Quitar insumo ${indice + 1}`}
                          className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Badges de Información de Stock y Alertas */}
                    {materia && (
                      <div className="mt-2.5 flex flex-wrap items-center gap-2 text-xs">
                        <span className="inline-flex items-center gap-1 rounded-lg bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">
                          Stock actual: <strong className="font-semibold">{materia.stock_actual} {materia.unidad_medida}</strong>
                        </span>

                        {cantidadNum > 0 && (
                          <span className="inline-flex items-center gap-1 rounded-lg bg-emerald-50 border border-emerald-200 px-2.5 py-1 text-[11px] font-medium text-emerald-800">
                            Nuevo stock proyectado: <strong className="font-semibold">{(Number(materia.stock_actual || 0) + cantidadNum).toFixed(3)} {materia.unidad_medida}</strong>
                          </span>
                        )}

                        {materia.precio_ultima_compra && (
                          <span className="inline-flex items-center gap-1 rounded-lg bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600">
                            Último precio: Bs {materia.precio_ultima_compra}
                          </span>
                        )}

                        {variacionPorcentual !== null && Math.abs(variacionPorcentual) >= 50 && (
                          <span className="inline-flex items-center gap-1 rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1 text-[11px] font-medium text-amber-800">
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                            Aviso: Variación de precio {variacionPorcentual > 0 ? '+' : ''}{variacionPorcentual.toFixed(1)}% vs anterior
                          </span>
                        )}
                      </div>
                    )}
                    {error && <p className="mt-1 text-[11px] text-red-600">{error}</p>}
                  </div>
                );
              })}
            </div>
            </fieldset>

            <div className="flex items-center justify-between rounded-xl bg-amber-50 px-4 py-3">
              <span className="text-sm font-semibold text-amber-900">Total estimado</span>
              <span className="text-lg font-bold text-amber-900">{formatoBs(total)}</span>
            </div>

            <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
              <button
                type="button"
                onClick={onClose}
                disabled={bloqueado}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={bloqueado || hayInsumosNoDisponibles}
                aria-live="polite"
                className={`inline-flex min-w-[11rem] items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-md transition-all duration-300 cursor-pointer disabled:cursor-not-allowed ${
                  registrada
                    ? 'bg-emerald-600 shadow-emerald-600/30 scale-105'
                    : 'bg-gradient-to-r from-amber-600 to-amber-700 shadow-amber-600/20 hover:-translate-y-0.5 hover:shadow-lg hover:from-amber-700 hover:to-amber-800 active:translate-y-0 active:scale-95 disabled:opacity-80'
                }`}
              >
                {registrada ? (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    ¡Compra registrada!
                  </>
                ) : guardando ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Registrando...
                  </>
                ) : (
                  'Registrar compra'
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default RegistrarCompraModal;
