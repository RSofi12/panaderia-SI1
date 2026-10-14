import { CardElement, Elements, useElements, useStripe } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import type { Stripe } from '@stripe/stripe-js';
import {
  AlertCircle,
  ArrowLeft,
  KeyRound,
  Loader2,
  Lock,
  ShieldCheck,
  X,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import type { DetalleVentaEntrada } from '../../../../types/venta';
import { ventaService } from './ventaService';

interface ModalPagoTarjetaProps {
  abierto: boolean;
  totalTexto: string;
  totalCentavos: number;
  detalles: DetalleVentaEntrada[];
  procesando: boolean;
  errorMensaje?: string;
  onCerrar: () => void;
  onVentaConfirmada: (idTransaccionStripe: string) => Promise<void>;
}

interface FormularioCardElementProps {
  totalTexto: string;
  totalCentavos: number;
  detalles: DetalleVentaEntrada[];
  procesandoPadre: boolean;
  onCerrar: () => void;
  onVentaConfirmada: (idTransaccionStripe: string) => Promise<void>;
}

function FormularioCardElement({
  totalTexto,
  totalCentavos,
  detalles,
  procesandoPadre,
  onCerrar,
  onVentaConfirmada,
}: FormularioCardElementProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [titular, setTitular] = useState('Cliente Mostrador');
  const [guardando, setGuardando] = useState(false);
  const [errorLocal, setErrorLocal] = useState('');

  const procesando = procesandoPadre || guardando;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorLocal('');

    if (totalCentavos < 600) {
      setErrorLocal('El monto mínimo para cobro con tarjeta vía Stripe es de Bs 6.00.');
      return;
    }

    if (!stripe || !elements) {
      setErrorLocal('El servicio de Stripe aún no está listo. Recarga la página.');
      return;
    }

    const cardElement = elements.getElement(CardElement);
    if (!cardElement) {
      setErrorLocal('No se pudo inicializar el formulario de tarjeta de Stripe.');
      return;
    }

    setGuardando(true);

    try {
      // 1. Crear el PaymentIntent en el backend para obtener el client_secret
      const intencion = await ventaService.crearIntencion(detalles);

      // 2. Confirmar el pago directamente con el SDK oficial de Stripe
      const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(
        intencion.client_secret,
        {
          payment_method: {
            card: cardElement,
            billing_details: {
              name: titular.trim() || 'Cliente Mostrador',
            },
          },
        },
      );

      if (stripeError) {
        setErrorLocal(stripeError.message || 'Error al procesar el pago con la tarjeta.');
        setGuardando(false);
        return;
      }

      if (paymentIntent?.status !== 'succeeded') {
        setErrorLocal('El pago no fue aprobado. Intenta con otra tarjeta.');
        setGuardando(false);
        return;
      }

      // 3. Registrar la venta en la base de datos con el id oficial de Stripe
      await onVentaConfirmada(paymentIntent.id);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detalles?: string | string[] } } })?.response?.data
          ?.detalles ||
        (err instanceof Error ? err.message : 'Error inesperado al procesar la venta.');
      setErrorLocal(Array.isArray(msg) ? msg.join(' ') : String(msg));
      setGuardando(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-6 space-y-4">
      {/* Campo oficial de Stripe: CardElement */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-slate-700">
            Datos de la tarjeta (Verificación oficial Stripe)
          </label>
          <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Conexión cifrada
          </span>
        </div>

        <div className="rounded-xl border border-slate-300 bg-white p-3.5 shadow-xs transition focus-within:border-amber-500 focus-within:ring-4 focus-within:ring-amber-100">
          <CardElement
            options={{
              hidePostalCode: true,
              style: {
                base: {
                  fontSize: '15px',
                  color: '#0f172a',
                  fontFamily: 'Inter, system-ui, sans-serif',
                  '::placeholder': {
                    color: '#94a3b8',
                  },
                },
                invalid: {
                  color: '#dc2626',
                  iconColor: '#dc2626',
                },
              },
            }}
          />
        </div>
      </div>

      {/* Nombre del titular */}
      <div>
        <label htmlFor="titular-card" className="text-xs font-semibold text-slate-700 block mb-1">
          Nombre en la tarjeta
        </label>
        <input
          id="titular-card"
          type="text"
          value={titular}
          disabled={procesando}
          onChange={(e) => setTitular(e.target.value)}
          placeholder="Nombre del cliente"
          className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-amber-500 focus:ring-4 focus:ring-amber-100 disabled:cursor-not-allowed"
        />
      </div>

      {/* Tarjeta de prueba académica */}
      <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-3 text-[11px] text-slate-600 leading-relaxed flex items-start gap-2.5">
        <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <span className="font-semibold text-slate-800">Tarjeta de prueba Stripe:</span>{' '}
          <code className="font-mono font-bold text-slate-900 bg-white px-1.5 py-0.5 rounded border border-slate-200">
            4242 4242 4242 4242
          </code>
          {' · '}Vto: cualquier fecha futura{' · '}CVC:{' '}
          <span className="font-mono font-bold text-slate-900">123</span>.
        </div>
      </div>

      {/* Aviso de error */}
      {errorLocal ? (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900"
        >
          <AlertCircle className="h-4 w-4 shrink-0 text-amber-700 mt-0.5" aria-hidden="true" />
          <p className="font-medium">{errorLocal}</p>
        </div>
      ) : null}

      {/* Botones de acción */}
      <div className="pt-2 flex items-center gap-3">
        <button
          type="button"
          onClick={onCerrar}
          disabled={procesando}
          className="w-1/3 rounded-xl border border-slate-200 py-3.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition disabled:opacity-50"
        >
          Cancelar
        </button>

        <button
          type="submit"
          disabled={procesando || !stripe || !elements}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-700 py-3.5 text-sm font-bold text-white shadow-md transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-300 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
        >
          {procesando ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Lock className="h-4 w-4" aria-hidden="true" />
          )}
          {procesando ? 'Procesando con Stripe…' : `Pagar ${totalTexto}`}
        </button>
      </div>

      <p className="text-center text-[10px] text-slate-400 flex items-center justify-center gap-1.5 pt-1">
        <Lock className="h-3 w-3 text-emerald-600" aria-hidden="true" />
        Formulario oficial de Stripe verificado por TLS 256-bit
      </p>
    </form>
  );
}

export function ModalPagoTarjeta({
  abierto,
  totalTexto,
  totalCentavos,
  detalles,
  procesando,
  errorMensaje,
  onCerrar,
  onVentaConfirmada,
}: ModalPagoTarjetaProps) {
  // Clave pública inicial desde variables de entorno de Vite o Next.js
  const claveEnv = (
    (import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY as string | undefined) ||
    (import.meta.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY as string | undefined) ||
    localStorage.getItem('panaderia_stripe_pk') ||
    ''
  ).trim();

  const [claveStripe, setClaveStripe] = useState<string>(claveEnv);
  const [claveManual, setClaveManual] = useState('');

  // Si no hay clave en el entorno, consultar al backend si tiene STRIPE_PUBLISHABLE_KEY
  useEffect(() => {
    if (!claveStripe) {
      void ventaService.obtenerConfigStripe().then((res) => {
        if (res.publishable_key) {
          setClaveStripe(res.publishable_key);
        }
      });
    }
  }, [claveStripe]);

  // Manejar tecla Escape
  useEffect(() => {
    function alPresionarTecla(e: KeyboardEvent) {
      if (e.key === 'Escape' && abierto && !procesando) {
        onCerrar();
      }
    }
    window.addEventListener('keydown', alPresionarTecla);
    return () => window.removeEventListener('keydown', alPresionarTecla);
  }, [abierto, procesando, onCerrar]);

  const stripePromise = useMemo<Promise<Stripe | null> | null>(() => {
    if (!claveStripe) return null;
    return loadStripe(claveStripe);
  }, [claveStripe]);

  function guardarClaveManual(e: React.FormEvent) {
    e.preventDefault();
    const limpia = claveManual.trim();
    if (limpia.startsWith('pk_test_') || limpia.startsWith('pk_live_')) {
      localStorage.setItem('panaderia_stripe_pk', limpia);
      setClaveStripe(limpia);
    }
  }

  if (!abierto) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-pago-tarjeta"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-md overflow-hidden rounded-3xl bg-white shadow-2xl ring-1 ring-slate-900/10 transition-all">
        {/* Encabezado */}
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <button
            type="button"
            onClick={onCerrar}
            disabled={procesando}
            aria-label="Volver"
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition disabled:opacity-50"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            <span>Volver</span>
          </button>

          <h3 id="titulo-pago-tarjeta" className="text-base font-bold text-slate-900">
            Pagar con tarjeta
          </h3>

          <button
            type="button"
            onClick={onCerrar}
            disabled={procesando}
            aria-label="Cerrar modal"
            className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition disabled:opacity-50"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {/* Si Stripe tiene clave pública, montamos el componente oficial Elements + CardElement */}
        {stripePromise ? (
          <Elements stripe={stripePromise}>
            <FormularioCardElement
              totalTexto={totalTexto}
              totalCentavos={totalCentavos}
              detalles={detalles}
              procesandoPadre={procesando}
              onCerrar={onCerrar}
              onVentaConfirmada={onVentaConfirmada}
            />
          </Elements>
        ) : (
          /* Si no hay clave pública configurada, orientamos al desarrollador/cajero */
          <div className="p-6 space-y-4">
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900 space-y-2">
              <div className="flex items-center gap-2 font-bold text-amber-950">
                <KeyRound className="h-5 w-5 text-amber-700" />
                <span>Configuración de Stripe requerida</span>
              </div>
              <p className="leading-relaxed">
                Para mostrar la ventana oficial de Stripe con el formulario seguro de tarjeta, se
                necesita la clave pública (<code className="font-mono font-bold">pk_test_...</code>).
              </p>
              <div className="rounded-xl bg-white p-2.5 border border-amber-200 font-mono text-[11px] text-slate-800">
                # frontend/.env
                <br />
                VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
              </div>
              <p className="text-[11px] text-amber-800">
                También puedes definirla en <code className="font-bold">backend/.env</code> como{' '}
                <code className="font-bold">STRIPE_PUBLISHABLE_KEY</code>.
              </p>
            </div>

            {/* Opción rápida: pegar clave para la sesión actual */}
            <form onSubmit={guardarClaveManual} className="space-y-3">
              <label htmlFor="clave-manual" className="block text-xs font-semibold text-slate-700">
                O ingresa tu clave pública para activar en esta sesión:
              </label>
              <div className="flex gap-2">
                <input
                  id="clave-manual"
                  type="text"
                  value={claveManual}
                  onChange={(e) => setClaveManual(e.target.value)}
                  placeholder="pk_test_51..."
                  className="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-100"
                />
                <button
                  type="submit"
                  disabled={!claveManual.trim().startsWith('pk_')}
                  className="rounded-xl bg-amber-700 px-3 py-2 text-xs font-semibold text-white hover:bg-amber-800 disabled:bg-slate-300 transition"
                >
                  Activar
                </button>
              </div>
            </form>

            {errorMensaje ? (
              <p className="text-xs text-red-600 font-medium">{errorMensaje}</p>
            ) : null}

            <div className="pt-2">
              <button
                type="button"
                onClick={onCerrar}
                className="w-full rounded-xl border border-slate-200 py-3 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition"
              >
                Volver al mostrador
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
