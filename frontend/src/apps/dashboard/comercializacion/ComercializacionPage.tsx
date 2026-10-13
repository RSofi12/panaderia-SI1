import React, { useEffect, useState } from 'react';
import { ArrowRight, Banknote, CreditCard, Receipt, ShoppingBag, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import type { VentaResumen } from '../../../types/venta';
import { ChipMetodo } from './ventas/ChipMetodo';
import { ventaService } from './ventas/ventaService';

function bolivianos(valor: number): string {
  return `Bs ${valor.toFixed(2)}`;
}

function hora(fechaIso: string): string {
  return new Date(fechaIso).toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' });
}

interface ResumenDia {
  cantidad: number;
  total: number;
  efectivo: number;
  stripe: number;
}

function resumir(ventas: VentaResumen[]): ResumenDia {
  let efectivo = 0;
  let stripe = 0;
  for (const venta of ventas) {
    const centavos = Math.round(Number(venta.total) * 100);
    if (venta.metodo_pago === 'stripe') stripe += centavos;
    else efectivo += centavos;
  }
  return {
    cantidad: ventas.length,
    total: (efectivo + stripe) / 100,
    efectivo: efectivo / 100,
    stripe: stripe / 100,
  };
}

type EstadoCarga = 'cargando' | 'listo' | 'error';

export const ComercializacionPage: React.FC = () => {
  const { hasPermission } = useAuth();
  const puedeVender = hasPermission('registrar_ventas');
  const [ventas, setVentas] = useState<VentaResumen[]>([]);
  const [estado, setEstado] = useState<EstadoCarga>('cargando');

  useEffect(() => {
    if (!puedeVender) return;
    let vigente = true;
    ventaService
      .listarHoy()
      .then((datos) => {
        if (!vigente) return;
        setVentas(datos);
        setEstado('listo');
      })
      .catch(() => {
        if (vigente) setEstado('error');
      });
    return () => {
      vigente = false;
    };
  }, [puedeVender]);

  const resumen = resumir(ventas);
  const ultimas = ventas.slice(0, 5);
  const fechaHoy = new Date().toLocaleDateString('es-BO', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="flex flex-col gap-1">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
          Comercialización · Ciclo 3
        </p>
        <h2 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-slate-900">
          <TrendingUp className="h-7 w-7 text-amber-700" aria-hidden="true" />
          Ventas en mostrador
        </h2>
        <p className="text-sm text-slate-500 first-letter:uppercase">{fechaHoy}</p>
      </header>

      <section
        aria-labelledby="titulo-mostrador"
        className="mostrador-aparecer relative overflow-hidden rounded-3xl bg-[#2b1a10] p-6 text-amber-50 shadow-lg shadow-amber-950/20 sm:p-8"
      >
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-16 -top-20 h-64 w-64 rounded-full bg-amber-500/25 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-24 left-1/3 h-56 w-56 rounded-full bg-orange-600/20 blur-3xl"
        />
        <div className="relative flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="max-w-xl">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-400/15 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-amber-300">
              <ShoppingBag className="h-3.5 w-3.5" aria-hidden="true" />
              CU13 · Registrar venta
            </span>
            <h3 id="titulo-mostrador" className="font-sugo mt-3 text-4xl leading-tight text-amber-100 sm:text-5xl">
              Mostrador
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-amber-100/75">
              Elige los panes, revisa el total y cobra en efectivo o con tarjeta (Stripe). El stock del
              mostrador se descuenta al confirmar.
            </p>
          </div>
          {puedeVender ? (
            <Link
              to="/dashboard/comercializacion/ventas"
              className="group inline-flex shrink-0 items-center justify-center gap-3 rounded-2xl bg-amber-400 px-6 py-4 text-base font-bold text-[#2b1a10] shadow-md transition hover:bg-amber-300 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300/50"
            >
              Abrir mostrador
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </Link>
          ) : (
            <p className="max-w-xs rounded-2xl bg-white/5 p-4 text-sm text-amber-100/80">
              Tu rol no tiene el permiso para registrar ventas. Pídeselo al administrador.
            </p>
          )}
        </div>
      </section>

      {puedeVender ? (
        <>
          <section aria-label="Resumen de hoy" className="grid gap-4 sm:grid-cols-3">
            <TarjetaCifra
              etiqueta="Vendido hoy"
              valor={estado === 'listo' ? bolivianos(resumen.total) : '—'}
              detalle={estado === 'listo' ? `${resumen.cantidad} ${resumen.cantidad === 1 ? 'venta' : 'ventas'}` : ''}
              icono={Receipt}
              destacada
            />
            <TarjetaCifra
              etiqueta="En efectivo"
              valor={estado === 'listo' ? bolivianos(resumen.efectivo) : '—'}
              detalle="Dinero en caja"
              icono={Banknote}
            />
            <TarjetaCifra
              etiqueta="Con tarjeta"
              valor={estado === 'listo' ? bolivianos(resumen.stripe) : '—'}
              detalle="Cobrado por Stripe"
              icono={CreditCard}
            />
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-bold text-slate-900">Últimas ventas de hoy</h3>
              {ventas.length > ultimas.length ? (
                <Link
                  to="/dashboard/comercializacion/ventas"
                  className="text-xs font-semibold text-amber-800 hover:underline"
                >
                  Ver las {ventas.length}
                </Link>
              ) : null}
            </div>

            {estado === 'cargando' ? (
              <p className="mt-4 text-sm text-slate-500">Cargando ventas…</p>
            ) : null}
            {estado === 'error' ? (
              <p className="mt-4 text-sm text-amber-900">No se pudieron cargar las ventas de hoy.</p>
            ) : null}
            {estado === 'listo' && ventas.length === 0 ? (
              <p className="mt-4 text-sm text-slate-500">
                Todavía no hay ventas hoy. La primera aparecerá aquí apenas la cobres.
              </p>
            ) : null}

            {ultimas.length > 0 ? (
              <ul className="mt-3 divide-y divide-slate-100">
                {ultimas.map((venta) => (
                  <li key={venta.id_venta} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs text-slate-400">#{venta.numero_comprobante}</span>
                      <span className="tabular-nums text-slate-500">{hora(venta.fecha_hora)}</span>
                      <ChipMetodo metodo={venta.metodo_pago} />
                    </div>
                    <span className="font-semibold tabular-nums text-slate-900">
                      {bolivianos(Number(venta.total))}
                    </span>
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        </>
      ) : null}
    </div>
  );
};

interface TarjetaCifraProps {
  etiqueta: string;
  valor: string;
  detalle: string;
  icono: React.ElementType;
  destacada?: boolean;
}

function TarjetaCifra({ etiqueta, valor, detalle, icono: Icono, destacada = false }: TarjetaCifraProps) {
  return (
    <div
      className={`rounded-2xl border p-5 ${
        destacada ? 'border-amber-200 bg-amber-50' : 'border-slate-200 bg-white'
      }`}
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{etiqueta}</p>
        <Icono className="h-4 w-4 text-amber-700" aria-hidden="true" />
      </div>
      <p className="mt-2 text-2xl font-bold tabular-nums text-slate-900">{valor}</p>
      <p className="mt-0.5 text-xs text-slate-500">{detalle}</p>
    </div>
  );
}
export default ComercializacionPage;
