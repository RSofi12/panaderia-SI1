import React, { useEffect, useRef, useState } from 'react';
import { CheckCircle2, Loader2, X } from 'lucide-react';
import { normalizarErrorApi } from '../../../../services/erroresApi';
import gastosService from '../../../../services/gastosService';
import { CATEGORIAS_MOVIMIENTO, TIPOS_MOVIMIENTO } from '../../../../types/gasto';
import type {
  CategoriaMovimiento,
  MovimientoEconomico,
  TipoMovimiento,
} from '../../../../types/gasto';

interface Props {
  onCerrar: () => void;
  /** Se llama al confirmar el backend. La página recarga la lista sin cerrar el modal. */
  onRegistrado: (movimiento: MovimientoEconomico) => void;
}

/** Valor para `<input type="datetime-local">`: ahora en hora local del navegador. */
function ahoraLocal(): string {
  const ahora = new Date();
  const local = new Date(ahora.getTime() - ahora.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

/**
 * Valida lo mismo que el serializer, pero antes de viajar al servidor.
 * El backend sigue siendo la autoridad: esto solo evita un viaje obvio.
 */
function validarFormulario(concepto: string, monto: string, fecha: string) {
  const errores: Record<string, string[]> = {};
  const texto = concepto.trim();
  if (!texto) errores.concepto = ['Indica en qué se usó el dinero.'];
  else if (texto.length < 3) errores.concepto = ['El concepto debe tener al menos 3 caracteres.'];

  const limpio = monto.replace(',', '.').trim();
  const numero = Number(limpio);
  if (!limpio) errores.monto = ['Escribe el monto.'];
  else if (!Number.isFinite(numero) || numero <= 0) errores.monto = ['El monto debe ser mayor a cero.'];
  else if (!/^\d{1,8}(\.\d{1,2})?$/.test(limpio)) errores.monto = ['Usa como máximo dos decimales.'];

  if (fecha && new Date(fecha).getTime() > Date.now()) {
    errores.fecha_hora = ['La fecha no puede estar en el futuro.'];
  }

  return { errores, montoLimpio: limpio };
}

function ErroresCampo({ mensajes }: { mensajes?: string[] }) {
  if (!mensajes?.length) return null;
  return (
    <ul className="mt-1 space-y-0.5 text-xs text-rose-600">
      {mensajes.map((mensaje) => (
        <li key={mensaje}>{mensaje}</li>
      ))}
    </ul>
  );
}

const estiloCampo =
  'w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-amber-600 focus:ring-2 focus:ring-amber-600/20';

export const RegistrarGastoModal: React.FC<Props> = ({ onCerrar, onRegistrado }) => {
  const [tipo, setTipo] = useState<TipoMovimiento>('gasto');
  const [categoria, setCategoria] = useState<CategoriaMovimiento>('otros');
  const [concepto, setConcepto] = useState('');
  const [monto, setMonto] = useState('');
  const [fecha, setFecha] = useState(ahoraLocal);
  const [descripcion, setDescripcion] = useState('');
  const [errores, setErrores] = useState<Record<string, string[]>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const [exito, setExito] = useState<MovimientoEconomico | null>(null);

  const conceptoRef = useRef<HTMLInputElement>(null);
  const maxFecha = ahoraLocal();

  useEffect(() => {
    conceptoRef.current?.focus();
  }, []);

  useEffect(() => {
    function alPresionar(evento: KeyboardEvent) {
      if (evento.key === 'Escape' && !guardando && !exito) onCerrar();
    }
    document.addEventListener('keydown', alPresionar);
    const overflowPrevio = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', alPresionar);
      document.body.style.overflow = overflowPrevio;
    };
  }, [guardando, exito, onCerrar]);

  // El panel de confirmación se muestra un instante antes de cerrar: el usuario
  // ve que el registro sí entró, sin un modal que quede abierto de más.
  useEffect(() => {
    if (!exito) return;
    const temporizador = window.setTimeout(onCerrar, 1100);
    return () => window.clearTimeout(temporizador);
  }, [exito, onCerrar]);

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (guardando || exito) return;

    const { errores: locales, montoLimpio } = validarFormulario(concepto, monto, fecha);
    if (Object.keys(locales).length > 0) {
      setErrores(locales);
      setErrorGeneral(null);
      return;
    }

    setGuardando(true);
    setErrores({});
    setErrorGeneral(null);
    try {
      const creado = await gastosService.registrar({
        tipo,
        categoria,
        concepto: concepto.trim(),
        monto: montoLimpio,
        descripcion: descripcion.trim() || undefined,
        fecha_hora: fecha || undefined,
      });
      setExito(creado);
      onRegistrado(creado);
    } catch (error) {
      const normalizado = normalizarErrorApi(error);
      setErrores(normalizado.campos);
      setErrorGeneral(normalizado.mensaje);
    } finally {
      setGuardando(false);
    }
  }

  const indiceTipo = TIPOS_MOVIMIENTO.findIndex((opcion) => opcion.valor === tipo);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onMouseDown={(evento) => {
        if (evento.target === evento.currentTarget && !guardando && !exito) onCerrar();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-registrar-gasto"
        className="mostrador-aparecer w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl border border-amber-100 bg-white shadow-xl"
      >
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
          <div>
            <h2 id="titulo-registrar-gasto" className="text-lg font-bold text-slate-900">
              Registrar gasto o inversión
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Queda guardado a tu nombre en la bitácora del sistema.
            </p>
          </div>
          <button
            type="button"
            onClick={onCerrar}
            disabled={guardando || Boolean(exito)}
            aria-label="Cerrar el formulario"
            className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 disabled:opacity-40"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        {exito ? (
          <div className="mostrador-aparecer flex flex-col items-center gap-3 px-5 py-12 text-center">
            <CheckCircle2 className="h-12 w-12 text-emerald-600" />
            <p className="text-base font-semibold text-slate-900">Registro guardado</p>
            <p className="text-sm text-slate-500">
              {exito.tipo === 'inversion' ? 'Inversión' : 'Gasto'} de{' '}
              <span className="font-semibold tabular-nums text-slate-700">{exito.concepto}</span> por{' '}
              <span className="font-semibold tabular-nums text-slate-700">Bs {exito.monto}</span>.
            </p>
          </div>
        ) : (
          <form onSubmit={enviar} noValidate className="space-y-4 px-5 py-4">
            {errorGeneral && (
              <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {errorGeneral}
              </div>
            )}

            {/* Selector de tipo con indicador deslizante: el cambio se ve, no se adivina. */}
            <fieldset>
              <legend className="mb-1.5 text-xs font-semibold text-slate-600">Tipo de egreso</legend>
              <div className="relative grid grid-cols-2 rounded-xl bg-slate-100 p-1">
                <span
                  aria-hidden="true"
                  className={`absolute inset-y-1 left-1 w-[calc(50%-0.25rem)] rounded-lg bg-white shadow-xs transition-transform duration-300 ease-out ${
                    indiceTipo === 1 ? 'translate-x-[calc(100%+0.25rem)]' : 'translate-x-0'
                  }`}
                />
                {TIPOS_MOVIMIENTO.map((opcion) => (
                  <button
                    key={opcion.valor}
                    type="button"
                    aria-pressed={tipo === opcion.valor}
                    onClick={() => setTipo(opcion.valor)}
                    disabled={guardando}
                    className={`relative z-10 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                      tipo === opcion.valor ? 'text-slate-900' : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    {opcion.etiqueta}
                  </button>
                ))}
              </div>
              <p className="mt-1.5 text-xs text-slate-500">
                {TIPOS_MOVIMIENTO[indiceTipo]?.descripcion}
              </p>
              <ErroresCampo mensajes={errores.tipo} />
            </fieldset>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="gasto-categoria" className="mb-1.5 block text-xs font-semibold text-slate-600">
                  Categoría
                </label>
                <select
                  id="gasto-categoria"
                  value={categoria}
                  onChange={(evento) => setCategoria(evento.target.value as CategoriaMovimiento)}
                  disabled={guardando}
                  className={estiloCampo}
                >
                  {CATEGORIAS_MOVIMIENTO.map((opcion) => (
                    <option key={opcion.valor} value={opcion.valor}>
                      {opcion.etiqueta}
                    </option>
                  ))}
                </select>
                <ErroresCampo mensajes={errores.categoria} />
              </div>

              <div>
                <label htmlFor="gasto-monto" className="mb-1.5 block text-xs font-semibold text-slate-600">
                  Monto
                </label>
                <div className="relative">
                  <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-sm font-medium text-slate-400">
                    Bs
                  </span>
                  <input
                    id="gasto-monto"
                    type="text"
                    inputMode="decimal"
                    autoComplete="off"
                    placeholder="0.00"
                    value={monto}
                    onChange={(evento) => setMonto(evento.target.value)}
                    disabled={guardando}
                    className={`${estiloCampo} pl-9 tabular-nums`}
                  />
                </div>
                <ErroresCampo mensajes={errores.monto} />
              </div>
            </div>

            <div>
              <label htmlFor="gasto-concepto" className="mb-1.5 block text-xs font-semibold text-slate-600">
                Concepto
              </label>
              <input
                id="gasto-concepto"
                ref={conceptoRef}
                type="text"
                maxLength={100}
                autoComplete="off"
                placeholder="Ej. Alquiler del local de noviembre"
                value={concepto}
                onChange={(evento) => setConcepto(evento.target.value)}
                disabled={guardando}
                className={estiloCampo}
              />
              <ErroresCampo mensajes={errores.concepto} />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="gasto-fecha" className="mb-1.5 block text-xs font-semibold text-slate-600">
                  Fecha del pago
                </label>
                <input
                  id="gasto-fecha"
                  type="datetime-local"
                  max={maxFecha}
                  value={fecha}
                  onChange={(evento) => setFecha(evento.target.value)}
                  disabled={guardando}
                  className={`${estiloCampo} tabular-nums`}
                />
                <ErroresCampo mensajes={errores.fecha_hora} />
              </div>

              <div>
                <label htmlFor="gasto-descripcion" className="mb-1.5 block text-xs font-semibold text-slate-600">
                  Detalle <span className="font-normal text-slate-400">(opcional)</span>
                </label>
                <input
                  id="gasto-descripcion"
                  type="text"
                  autoComplete="off"
                  placeholder="Número de factura, observaciones…"
                  value={descripcion}
                  onChange={(evento) => setDescripcion(evento.target.value)}
                  disabled={guardando}
                  className={estiloCampo}
                />
                <ErroresCampo mensajes={errores.descripcion} />
              </div>
            </div>

            <footer className="flex flex-col-reverse gap-2 border-t border-slate-100 pt-4 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={onCerrar}
                disabled={guardando}
                className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={guardando}
                aria-busy={guardando}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 px-5 py-2 text-sm font-semibold text-white shadow-md shadow-amber-600/20 transition-all hover:from-amber-700 hover:to-amber-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {guardando && <Loader2 className="h-4 w-4 animate-spin" />}
                {guardando ? 'Guardando…' : 'Registrar gasto'}
              </button>
            </footer>
          </form>
        )}
      </div>
    </div>
  );
};

export default RegistrarGastoModal;
