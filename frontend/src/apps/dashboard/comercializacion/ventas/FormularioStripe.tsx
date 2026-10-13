import { CardElement, useElements, useStripe } from '@stripe/react-stripe-js';
import type { StripeCardElementChangeEvent } from '@stripe/stripe-js';
import { CreditCard, Loader2, Lock } from 'lucide-react';
import { useState } from 'react';

interface FormularioStripeProps {
  registrando: boolean;
  deshabilitado: boolean;
  totalTexto: string;
  onConfirmar: (confirmarPago: (clientSecret: string) => Promise<string>) => void;
}

const ESTILO_TARJETA = {
  hidePostalCode: true,
  style: {
    base: {
      fontSize: '16px',
      color: '#1e293b',
      '::placeholder': { color: '#94a3b8' },
    },
    invalid: { color: '#b45309' },
  },
};

export function FormularioStripe({ registrando, deshabilitado, totalTexto, onConfirmar }: FormularioStripeProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [tarjetaLista, setTarjetaLista] = useState(false);
  const [errorTarjeta, setErrorTarjeta] = useState('');

  function alCambiar(evento: StripeCardElementChangeEvent) {
    setTarjetaLista(evento.complete);
    setErrorTarjeta(evento.error?.message ?? '');
  }

  function cobrar() {
    onConfirmar(async (clientSecret: string) => {
      if (!stripe || !elements) {
        throw new Error('Stripe todavía no está listo.');
      }
      const tarjeta = elements.getElement(CardElement);
      if (!tarjeta) {
        throw new Error('No se encontró el formulario de la tarjeta.');
      }
      const resultado = await stripe.confirmCardPayment(clientSecret, {
        payment_method: { card: tarjeta },
      });
      if (resultado.error || !resultado.paymentIntent) {
        throw new Error(resultado.error?.message ?? 'Stripe no confirmó el cobro.');
      }
      return resultado.paymentIntent.id;
    });
  }

  return (
    <div className="space-y-3">
      <div>
        <span className="text-xs font-semibold text-slate-600">Datos de la tarjeta</span>
        <div className="mt-1.5 rounded-xl border border-slate-300 bg-white px-3 py-3.5 focus-within:border-amber-500 focus-within:ring-4 focus-within:ring-amber-100">
          <CardElement onChange={alCambiar} options={ESTILO_TARJETA} />
        </div>
        {errorTarjeta ? (
          <p role="alert" className="mt-1.5 text-xs text-amber-800">
            {errorTarjeta}
          </p>
        ) : (
          <p className="mt-1.5 flex items-center gap-1 text-[11px] text-slate-400">
            <Lock className="h-3 w-3" aria-hidden="true" />
            La tarjeta la procesa Stripe; el sistema solo guarda el id del cobro.
          </p>
        )}
      </div>
      <button
        type="button"
        disabled={deshabilitado || registrando || !stripe || !tarjetaLista}
        onClick={cobrar}
        className="flex w-full items-center justify-center gap-2 rounded-2xl bg-amber-700 px-4 py-4 text-base font-bold text-white shadow-sm transition hover:bg-amber-800 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
      >
        {registrando ? (
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
        ) : (
          <CreditCard className="h-5 w-5" aria-hidden="true" />
        )}
        {registrando ? 'Procesando cobro…' : `Cobrar ${totalTexto} con tarjeta`}
      </button>
    </div>
  );
}
