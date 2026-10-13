import { Banknote, CreditCard } from 'lucide-react';
import type { MetodoPago } from '../../../../types/venta';

export function ChipMetodo({ metodo }: { metodo: MetodoPago }) {
  const esTarjeta = metodo === 'stripe';
  const Icono = esTarjeta ? CreditCard : Banknote;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
        esTarjeta ? 'bg-indigo-50 text-indigo-700' : 'bg-emerald-50 text-emerald-700'
      }`}
    >
      <Icono className="h-3 w-3" aria-hidden="true" />
      {esTarjeta ? 'Tarjeta' : 'Efectivo'}
    </span>
  );
}
