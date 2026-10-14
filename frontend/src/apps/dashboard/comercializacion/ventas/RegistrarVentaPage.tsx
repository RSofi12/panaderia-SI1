import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import {
  AlertCircle,
  ArrowLeft,
  Banknote,
  CheckCircle2,
  CreditCard,
  Loader2,
  Minus,
  Plus,
  RefreshCw,
  Search,
  ShoppingBasket,
  Trash2,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ElementType, ReactNode } from 'react';
import { Link } from 'react-router-dom';
import existenciasService from '../../../../services/existenciasService';
import type { ExistenciaProducto } from '../../../../types/existencias';
import type { MetodoPago, VentaRegistrada, VentaResumen } from '../../../../types/venta';
import { ChipMetodo } from './ChipMetodo';
import { FormularioStripe } from './FormularioStripe';
import { ventaService } from './ventaService';

const claveStripe = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;
const stripePromise = claveStripe ? loadStripe(claveStripe) : null;

const BILLETES = [10, 20, 50, 100, 200];
const TODAS = 'Todas';
// El número de columnas sigue al ancho del catálogo, no al de la ventana:
// con el menú lateral abierto, la ventana puede ser ancha y el catálogo angosto.
const GRILLA_CATALOGO = 'grid grid-cols-1 gap-3 @min-[26rem]:grid-cols-2 @min-[42rem]:grid-cols-3';

interface LineaCarrito {
  id_producto: number;
  nombre: string;
  precio: string;
  cantidad: number;
  stock: number;
}

interface VentaCerrada {
  venta: VentaRegistrada;
  cambio: number | null;
  recibido: number | null;
}

function centavos(valor: string | number): number {
  return Math.round(Number(valor) * 100);
}

function bolivianos(valor: string | number): string {
  return `Bs ${Number(valor).toFixed(2)}`;
}

function hora(fechaIso: string): string {
  return new Date(fechaIso).toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' });
}

function mensajeDeError(error: unknown): string {
  if (error instanceof Error && !('response' in error) && error.message) {
    return error.message;
  }
  const datos = (error as { response?: { data?: unknown } })?.response?.data;
  if (!datos || typeof datos !== 'object') {
    return 'No se pudo registrar la venta. Revisa la conexión e intenta de nuevo.';
  }
  const partes = Object.values(datos as Record<string, unknown>).flatMap((valor) =>
    Array.isArray(valor) ? valor.map(String) : [String(valor)],
  );
  return partes.join(' ') || 'La venta fue rechazada.';
}

async function pedirMostrador() {
  try {
    const [panes, ventas] = await Promise.all([
      existenciasService.listar({ solo_activos: true, ordenar_por: 'nombre_asc' }),
      ventaService.listarHoy(),
    ]);
    return { panes: panes.filter((pan) => pan.activo), ventas };
  } catch {
    return null;
  }
}

export default function RegistrarVentaPage() {
  const [catalogo, setCatalogo] = useState<ExistenciaProducto[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState('');
  const [ventasHoy, setVentasHoy] = useState<VentaResumen[]>([]);
  const [busqueda, setBusqueda] = useState('');
  const [categoria, setCategoria] = useState(TODAS);
  const [carrito, setCarrito] = useState<LineaCarrito[]>([]);
  const [metodo, setMetodo] = useState<MetodoPago>('efectivo');
  const [recibido, setRecibido] = useState('');
  const [registrando, setRegistrando] = useState(false);
  const [errorCobro, setErrorCobro] = useState('');
  const [cerrada, setCerrada] = useState<VentaCerrada | null>(null);
  const cerrarDialogo = useCallback(() => setCerrada(null), []);

  const aplicarCarga = useCallback((resultado: Awaited<ReturnType<typeof pedirMostrador>>) => {
    if (resultado) {
      setCatalogo(resultado.panes);
      setVentasHoy(resultado.ventas);
      setErrorCarga('');
    } else {
      setErrorCarga('No se pudo cargar el mostrador.');
    }
    setCargando(false);
  }, []);

  async function cargar(silencioso = false) {
    if (!silencioso) setCargando(true);
    aplicarCarga(await pedirMostrador());
  }

  useEffect(() => {
    let vigente = true;
    void pedirMostrador().then((resultado) => {
      if (vigente) aplicarCarga(resultado);
    });
    return () => {
      vigente = false;
    };
  }, [aplicarCarga]);

  const categorias = useMemo(() => {
    const nombres = new Set(catalogo.map((pan) => pan.categoria_nombre).filter(Boolean));
    return [TODAS, ...[...nombres].sort((a, b) => a.localeCompare(b, 'es'))];
  }, [catalogo]);

  const visibles = useMemo(() => {
    const texto = busqueda.trim().toLowerCase();
    return catalogo.filter(
      (pan) =>
        (categoria === TODAS || pan.categoria_nombre === categoria) &&
        (!texto || pan.producto_nombre.toLowerCase().includes(texto)),
    );
  }, [catalogo, busqueda, categoria]);

  const cantidadPorProducto = useMemo(
    () => new Map(carrito.map((linea) => [linea.id_producto, linea.cantidad])),
    [carrito],
  );

  const totalCentavos = carrito.reduce((suma, linea) => suma + centavos(linea.precio) * linea.cantidad, 0);
  const totalTexto = bolivianos(totalCentavos / 100);
  const unidades = carrito.reduce((suma, linea) => suma + linea.cantidad, 0);
  const recibidoCentavos = recibido === '' ? null : centavos(recibido);
  const faltante = recibidoCentavos !== null && recibidoCentavos < totalCentavos;
  const cambioCentavos = recibidoCentavos !== null && !faltante ? recibidoCentavos - totalCentavos : null;
  const totalHoy = ventasHoy.reduce((suma, venta) => suma + centavos(venta.total), 0);

  const detalles = carrito.map((linea) => ({ id_producto: linea.id_producto, cantidad: linea.cantidad }));

  function limpiarAvisos() {
    setErrorCobro('');
  }

  function agregar(pan: ExistenciaProducto) {
    if (pan.stock_actual <= 0) return;
    limpiarAvisos();
    setCarrito((actual) => {
      const ya = actual.find((linea) => linea.id_producto === pan.id_producto);
      if (!ya) {
        return [
          ...actual,
          {
            id_producto: pan.id_producto,
            nombre: pan.producto_nombre,
            precio: pan.precio_venta,
            cantidad: 1,
            stock: pan.stock_actual,
          },
        ];
      }
      if (ya.cantidad >= ya.stock) return actual;
      return actual.map((linea) =>
        linea.id_producto === pan.id_producto ? { ...linea, cantidad: linea.cantidad + 1 } : linea,
      );
    });
  }

  function cambiarCantidad(idProducto: number, cantidad: number) {
    limpiarAvisos();
    setCarrito((actual) =>
      actual.flatMap((linea) => {
        if (linea.id_producto !== idProducto) return [linea];
        if (!Number.isFinite(cantidad) || cantidad <= 0) return [];
        return [{ ...linea, cantidad: Math.min(Math.floor(cantidad), linea.stock) }];
      }),
    );
  }

  function vaciar() {
    setCarrito([]);
    setRecibido('');
    limpiarAvisos();
  }

  async function cerrarVenta(venta: VentaRegistrada) {
    const pagoEnEfectivo = venta.metodo_pago === 'efectivo' && recibidoCentavos !== null;
    setCerrada({
      venta,
      recibido: pagoEnEfectivo ? recibidoCentavos / 100 : null,
      cambio: pagoEnEfectivo ? (recibidoCentavos - centavos(venta.total)) / 100 : null,
    });
    setCarrito([]);
    setRecibido('');
    await cargar(true);
  }

  async function cobrarEfectivo() {
    if (carrito.length === 0 || registrando || faltante) return;
    setRegistrando(true);
    limpiarAvisos();
    try {
      const venta = await ventaService.registrar({ metodo_pago: 'efectivo', detalles });
      await cerrarVenta(venta);
    } catch (error) {
      setErrorCobro(mensajeDeError(error));
    } finally {
      setRegistrando(false);
    }
  }

  async function cobrarStripe(confirmarPago: (clientSecret: string) => Promise<string>) {
    if (carrito.length === 0 || registrando) return;
    setRegistrando(true);
    limpiarAvisos();
    try {
      const intencion = await ventaService.crearIntencion(detalles);
      const idStripe = await confirmarPago(intencion.client_secret);
      const venta = await ventaService.registrar({
        metodo_pago: 'stripe',
        id_transaccion_stripe: idStripe,
        detalles,
      });
      await cerrarVenta(venta);
    } catch (error) {
      setErrorCobro(mensajeDeError(error));
    } finally {
      setRegistrando(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Link
            to="/dashboard/comercializacion"
            className="inline-flex items-center gap-1 text-xs font-semibold text-amber-800 hover:underline"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
            Comercialización
          </Link>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Registrar venta</h1>
          <p className="mt-0.5 text-sm text-slate-500">
            Toca un pan para sumarlo al ticket. El precio sale del catálogo.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm shadow-xs">
          <span className="text-slate-500">Hoy</span>
          <span className="font-bold tabular-nums text-slate-900">{bolivianos(totalHoy / 100)}</span>
          <span className="h-4 w-px bg-slate-200" aria-hidden="true" />
          <span className="tabular-nums text-slate-500">
            {ventasHoy.length} {ventasHoy.length === 1 ? 'venta' : 'ventas'}
          </span>
        </div>
      </header>

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_24rem]">
        <section aria-label="Catálogo de panes" className="@container min-w-0 space-y-4">
          <div className="flex flex-col gap-3">
            <label className="relative block">
              <span className="sr-only">Buscar pan</span>
              <Search
                className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                aria-hidden="true"
              />
              <input
                type="search"
                value={busqueda}
                onChange={(evento) => setBusqueda(evento.target.value)}
                placeholder="Buscar pan por nombre…"
                className="w-full rounded-2xl border border-slate-200 bg-white py-3 pl-10 pr-4 text-sm shadow-xs outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100"
              />
            </label>
            {categorias.length > 2 ? (
              <div role="group" aria-label="Filtrar por categoría" className="flex flex-wrap gap-2">
                {categorias.map((nombre) => {
                  const activa = nombre === categoria;
                  return (
                    <button
                      key={nombre}
                      type="button"
                      aria-pressed={activa}
                      onClick={() => setCategoria(nombre)}
                      className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
                        activa
                          ? 'bg-[#2b1a10] text-amber-100'
                          : 'border border-slate-200 bg-white text-slate-600 hover:border-amber-300 hover:text-amber-900'
                      }`}
                    >
                      {nombre}
                    </button>
                  );
                })}
              </div>
            ) : null}
          </div>

          {cargando ? <EsqueletoCatalogo /> : null}

          {errorCarga ? (
            <div className="flex flex-col items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-8 text-center">
              <AlertCircle className="h-6 w-6 text-amber-700" aria-hidden="true" />
              <p className="text-sm text-amber-900">{errorCarga}</p>
              <button
                type="button"
                onClick={() => void cargar()}
                className="inline-flex items-center gap-2 rounded-xl bg-amber-700 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-800"
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                Reintentar
              </button>
            </div>
          ) : null}

          {!cargando && !errorCarga && catalogo.length === 0 ? (
            <p className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
              No hay panes activos en el mostrador. Registra producción o existencias primero.
            </p>
          ) : null}

          {!cargando && !errorCarga && catalogo.length > 0 && visibles.length === 0 ? (
            <p className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
              Ningún pan coincide con «{busqueda}».
            </p>
          ) : null}

          {!cargando && !errorCarga ? (
            <ul className={GRILLA_CATALOGO}>
              {visibles.map((pan, indice) => (
                <li
                  key={pan.id_producto}
                  className="mostrador-aparecer"
                  style={{ animationDelay: `${Math.min(indice, 12) * 25}ms` }}
                >
                  <TarjetaPan
                    pan={pan}
                    enCarrito={cantidadPorProducto.get(pan.id_producto) ?? 0}
                    onAgregar={() => agregar(pan)}
                  />
                </li>
              ))}
            </ul>
          ) : null}
        </section>

        <aside aria-label="Ticket de venta" className="min-w-0 xl:sticky xl:top-4">
          <div className="ticket-dentado rounded-t-3xl border border-b-0 border-amber-200/70 bg-[#fffaf1] p-5 shadow-md shadow-amber-900/5">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-base font-bold text-slate-900">
                <ShoppingBasket className="h-5 w-5 text-amber-700" aria-hidden="true" />
                Ticket
                {unidades > 0 ? (
                  <span className="rounded-full bg-amber-700 px-2 py-0.5 text-[11px] font-bold tabular-nums text-white">
                    {unidades}
                  </span>
                ) : null}
              </h2>
              {carrito.length > 0 ? (
                <button
                  type="button"
                  onClick={vaciar}
                  disabled={registrando}
                  className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-slate-500 hover:bg-amber-100/60 hover:text-amber-900 disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                  Vaciar
                </button>
              ) : null}
            </div>

            {carrito.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-10 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-amber-700">
                  <ShoppingBasket className="h-6 w-6" aria-hidden="true" />
                </div>
                <p className="text-sm font-semibold text-slate-700">El ticket está vacío</p>
                <p className="max-w-[15rem] text-xs text-slate-500">
                  Toca los panes del catálogo para sumarlos. Cada toque agrega una unidad.
                </p>
              </div>
            ) : (
              <ul className="mt-4 space-y-3">
                {carrito.map((linea) => (
                  <LineaTicket
                    key={linea.id_producto}
                    linea={linea}
                    deshabilitado={registrando}
                    onCambiar={(cantidad) => cambiarCantidad(linea.id_producto, cantidad)}
                  />
                ))}
              </ul>
            )}

            <div className="mt-5 border-t-2 border-dashed border-amber-200 pt-4">
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-semibold uppercase tracking-wider text-slate-500">Total</span>
                <span className="text-3xl font-black tabular-nums text-slate-900" aria-live="polite">
                  {totalTexto}
                </span>
              </div>
            </div>

            <fieldset className="mt-5" disabled={registrando}>
              <legend className="text-xs font-semibold text-slate-600">¿Cómo paga el cliente?</legend>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <OpcionMetodo
                  activo={metodo === 'efectivo'}
                  icono={Banknote}
                  titulo="Efectivo"
                  onSeleccionar={() => {
                    setMetodo('efectivo');
                    limpiarAvisos();
                  }}
                />
                <OpcionMetodo
                  activo={metodo === 'stripe'}
                  icono={CreditCard}
                  titulo="Tarjeta"
                  subtitulo="Stripe"
                  onSeleccionar={() => {
                    setMetodo('stripe');
                    limpiarAvisos();
                  }}
                />
              </div>
            </fieldset>

            <div className="mt-4">
              {metodo === 'efectivo' ? (
                <div className="space-y-3">
                  <div>
                    <label htmlFor="monto-recibido" className="text-xs font-semibold text-slate-600">
                      Recibido del cliente <span className="font-normal text-slate-400">(opcional)</span>
                    </label>
                    <div className="mt-1.5 flex items-center rounded-xl border border-slate-300 bg-white focus-within:border-amber-500 focus-within:ring-4 focus-within:ring-amber-100">
                      <span className="pl-3 text-sm font-semibold text-slate-400">Bs</span>
                      <input
                        id="monto-recibido"
                        type="number"
                        inputMode="decimal"
                        min={0}
                        step="0.10"
                        value={recibido}
                        disabled={registrando || carrito.length === 0}
                        onChange={(evento) => setRecibido(evento.target.value)}
                        placeholder={(totalCentavos / 100).toFixed(2)}
                        className="w-full rounded-xl bg-transparent px-2 py-3 text-lg font-semibold tabular-nums outline-none disabled:cursor-not-allowed"
                      />
                    </div>
                  </div>
                  {carrito.length > 0 && !registrando ? (
                    <div className="flex flex-wrap gap-1.5">
                      <BotonMonto onClick={() => setRecibido((totalCentavos / 100).toFixed(2))}>Exacto</BotonMonto>
                      {BILLETES.filter((billete) => billete * 100 >= totalCentavos).map((billete) => (
                        <BotonMonto key={billete} onClick={() => setRecibido(String(billete))}>
                          Bs {billete}
                        </BotonMonto>
                      ))}
                    </div>
                  ) : null}
                  {cambioCentavos !== null ? (
                    <div className="flex items-center justify-between rounded-xl bg-emerald-50 px-4 py-3">
                      <span className="text-sm font-semibold text-emerald-800">Cambio a devolver</span>
                      <span className="text-xl font-black tabular-nums text-emerald-800">
                        {bolivianos(cambioCentavos / 100)}
                      </span>
                    </div>
                  ) : null}
                  {faltante ? (
                    <p role="alert" className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900">
                      Faltan {bolivianos((totalCentavos - (recibidoCentavos ?? 0)) / 100)} para cubrir el total.
                    </p>
                  ) : null}
                  <button
                    type="button"
                    disabled={carrito.length === 0 || registrando || faltante}
                    onClick={() => void cobrarEfectivo()}
                    className="flex w-full flex-wrap items-center justify-center gap-2 rounded-2xl bg-amber-700 px-4 py-4 text-center text-base font-bold leading-tight text-white shadow-sm transition hover:bg-amber-800 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
                  >
                    {registrando ? (
                      <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
                    ) : (
                      <Banknote className="h-5 w-5" aria-hidden="true" />
                    )}
                    {registrando ? 'Registrando…' : `Cobrar ${totalTexto} en efectivo`}
                  </button>
                </div>
              ) : stripePromise ? (
                <Elements stripe={stripePromise}>
                  <FormularioStripe
                    registrando={registrando}
                    deshabilitado={carrito.length === 0}
                    totalTexto={totalTexto}
                    onConfirmar={(confirmar) => void cobrarStripe(confirmar)}
                  />
                </Elements>
              ) : (
                <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
                  <p className="font-semibold text-slate-800">El cobro con tarjeta no está configurado.</p>
                  <p className="mt-1 text-xs">
                    Falta la clave pública de Stripe (<code>VITE_STRIPE_PUBLISHABLE_KEY</code>). Mientras tanto
                    puedes cobrar en efectivo.
                  </p>
                </div>
              )}
            </div>

            {errorCobro ? (
              <div
                role="alert"
                className="mt-4 flex gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                <p>{errorCobro}</p>
              </div>
            ) : null}
          </div>
        </aside>
      </div>

      <VentasDelDia ventas={ventasHoy} />

      {cerrada ? <DialogoVentaRegistrada cerrada={cerrada} onCerrar={cerrarDialogo} /> : null}
    </div>
  );
}

const ESTILO_STOCK: Record<ExistenciaProducto['estado_stock'], string> = {
  disponible: 'bg-emerald-50 text-emerald-700',
  critico: 'bg-amber-100 text-amber-800',
  agotado: 'bg-slate-100 text-slate-500',
};

interface TarjetaPanProps {
  pan: ExistenciaProducto;
  enCarrito: number;
  onAgregar: () => void;
}

function TarjetaPan({ pan, enCarrito, onAgregar }: TarjetaPanProps) {
  const quedan = pan.stock_actual - enCarrito;
  const agotado = pan.stock_actual <= 0;
  const sinMas = quedan <= 0;
  const etiquetaStock = agotado ? 'Agotado' : sinMas ? 'Todo en el ticket' : `Quedan ${quedan}`;

  return (
    <button
      type="button"
      disabled={sinMas}
      onClick={onAgregar}
      aria-label={`Agregar ${pan.producto_nombre}, ${bolivianos(pan.precio_venta)}. ${etiquetaStock}.`}
      className={`group relative flex h-full w-full flex-col rounded-2xl border bg-white p-4 text-left transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-200 enabled:hover:-translate-y-0.5 enabled:hover:shadow-md enabled:active:translate-y-0 disabled:cursor-not-allowed ${
        enCarrito > 0 ? 'border-amber-400 ring-2 ring-amber-200' : 'border-slate-200 enabled:hover:border-amber-300'
      } ${agotado ? 'opacity-55' : ''}`}
    >
      {enCarrito > 0 ? (
        <span className="mostrador-sello absolute right-2 top-2 flex h-7 min-w-7 items-center justify-center rounded-full bg-amber-700 px-2 text-xs font-bold tabular-nums text-white shadow">
          {enCarrito}
        </span>
      ) : null}
      <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {pan.categoria_nombre || 'Pan'}
      </span>
      <span className="mt-0.5 text-base font-bold leading-snug text-slate-900">{pan.producto_nombre}</span>
      <span className="mt-3 flex flex-wrap items-end justify-between gap-x-2 gap-y-1">
        <span className="text-xl font-black tabular-nums text-amber-800">{bolivianos(pan.precio_venta)}</span>
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold tabular-nums ${
            agotado || sinMas ? ESTILO_STOCK.agotado : ESTILO_STOCK[pan.estado_stock]
          }`}
        >
          {etiquetaStock}
        </span>
      </span>
      {!sinMas ? (
        <span
          aria-hidden="true"
          className="absolute bottom-4 right-4 hidden h-7 w-7 items-center justify-center rounded-full bg-amber-700 text-white opacity-0 shadow transition group-hover:opacity-100 sm:flex"
        >
          <Plus className="h-4 w-4" />
        </span>
      ) : null}
    </button>
  );
}

interface LineaTicketProps {
  linea: LineaCarrito;
  deshabilitado: boolean;
  onCambiar: (cantidad: number) => void;
}

function LineaTicket({ linea, deshabilitado, onCambiar }: LineaTicketProps) {
  const subtotal = (centavos(linea.precio) * linea.cantidad) / 100;
  return (
    <li className="mostrador-aparecer flex items-center gap-3">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-800">{linea.nombre}</p>
        <p className="text-xs tabular-nums text-slate-500">{bolivianos(linea.precio)} c/u</p>
      </div>
      <div className="flex items-center rounded-xl border border-amber-200 bg-white">
        <button
          type="button"
          disabled={deshabilitado}
          onClick={() => onCambiar(linea.cantidad - 1)}
          aria-label={linea.cantidad === 1 ? `Quitar ${linea.nombre}` : `Restar una unidad de ${linea.nombre}`}
          className="flex h-8 w-8 items-center justify-center rounded-l-xl text-slate-600 hover:bg-amber-50 disabled:opacity-40"
        >
          {linea.cantidad === 1 ? <X className="h-3.5 w-3.5" /> : <Minus className="h-3.5 w-3.5" />}
        </button>
        <input
          aria-label={`Cantidad de ${linea.nombre}`}
          type="number"
          inputMode="numeric"
          min={1}
          max={linea.stock}
          value={linea.cantidad}
          disabled={deshabilitado}
          onChange={(evento) => onCambiar(Number(evento.target.value))}
          className="h-8 w-10 border-x border-amber-100 bg-transparent text-center text-sm font-bold tabular-nums outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
        />
        <button
          type="button"
          disabled={deshabilitado || linea.cantidad >= linea.stock}
          onClick={() => onCambiar(linea.cantidad + 1)}
          aria-label={`Sumar una unidad de ${linea.nombre}`}
          className="flex h-8 w-8 items-center justify-center rounded-r-xl text-slate-600 hover:bg-amber-50 disabled:opacity-40"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
      </div>
      <span className="shrink-0 text-right text-sm font-bold tabular-nums text-slate-900">{bolivianos(subtotal)}</span>
    </li>
  );
}

interface OpcionMetodoProps {
  activo: boolean;
  icono: ElementType;
  titulo: string;
  subtitulo?: string;
  onSeleccionar: () => void;
}

function OpcionMetodo({ activo, icono: Icono, titulo, subtitulo, onSeleccionar }: OpcionMetodoProps) {
  return (
    <label
      className={`flex cursor-pointer items-center gap-2.5 rounded-xl border-2 px-3 py-2.5 transition has-[:focus-visible]:ring-4 has-[:focus-visible]:ring-amber-200 ${
        activo ? 'border-amber-600 bg-amber-50 text-amber-900' : 'border-slate-200 bg-white text-slate-600 hover:border-amber-300'
      }`}
    >
      <input type="radio" name="metodo-pago" checked={activo} onChange={onSeleccionar} className="sr-only" />
      <Icono className={`h-5 w-5 ${activo ? 'text-amber-700' : 'text-slate-400'}`} aria-hidden="true" />
      <span className="leading-tight">
        <span className="block text-sm font-bold">{titulo}</span>
        {subtitulo ? <span className="block text-[11px] text-slate-500">{subtitulo}</span> : null}
      </span>
    </label>
  );
}

function BotonMonto({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold tabular-nums text-slate-700 hover:border-amber-400 hover:bg-amber-50 hover:text-amber-900"
    >
      {children}
    </button>
  );
}

function EsqueletoCatalogo() {
  return (
    <ul className={GRILLA_CATALOGO} aria-label="Cargando panes">
      {Array.from({ length: 6 }, (_, indice) => (
        <li key={indice} className="h-[7.5rem] animate-pulse rounded-2xl border border-slate-200 bg-white p-4">
          <div className="h-2.5 w-14 rounded bg-slate-100" />
          <div className="mt-2 h-4 w-32 rounded bg-slate-200" />
          <div className="mt-6 h-5 w-20 rounded bg-amber-100" />
        </li>
      ))}
    </ul>
  );
}

function VentasDelDia({ ventas }: { ventas: VentaResumen[] }) {
  return (
    <section aria-labelledby="titulo-ventas-dia" className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      <h2 id="titulo-ventas-dia" className="text-sm font-bold text-slate-900">
        Ventas de hoy
      </h2>
      {ventas.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">Todavía no hay ventas registradas hoy.</p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[36rem] text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-slate-400">
                <th className="py-2 pr-4 font-semibold">Comprobante</th>
                <th className="py-2 pr-4 font-semibold">Hora</th>
                <th className="py-2 pr-4 font-semibold">Pago</th>
                <th className="py-2 pr-4 font-semibold">Cajero</th>
                <th className="py-2 text-right font-semibold">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {ventas.map((venta) => (
                <tr key={venta.id_venta}>
                  <td className="py-2.5 pr-4 font-mono text-xs text-slate-500">#{venta.numero_comprobante}</td>
                  <td className="py-2.5 pr-4 tabular-nums text-slate-600">{hora(venta.fecha_hora)}</td>
                  <td className="py-2.5 pr-4">
                    <ChipMetodo metodo={venta.metodo_pago} />
                  </td>
                  <td className="py-2.5 pr-4 text-slate-600">{venta.registrado_por}</td>
                  <td className="py-2.5 text-right font-semibold tabular-nums text-slate-900">
                    {bolivianos(venta.total)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

interface DialogoVentaRegistradaProps {
  cerrada: VentaCerrada;
  onCerrar: () => void;
}

function DialogoVentaRegistrada({ cerrada, onCerrar }: DialogoVentaRegistradaProps) {
  const { venta, recibido, cambio } = cerrada;
  const botonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    botonRef.current?.focus();
    const alPresionar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') onCerrar();
    };
    window.addEventListener('keydown', alPresionar);
    return () => window.removeEventListener('keydown', alPresionar);
  }, [onCerrar]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#2b1a10]/50 p-4 backdrop-blur-sm"
      onClick={onCerrar}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-venta-registrada"
        onClick={(evento) => evento.stopPropagation()}
        className="mostrador-sello ticket-dentado w-full max-w-sm rounded-t-3xl bg-[#fffaf1] p-6 shadow-2xl"
      >
        <div className="flex flex-col items-center text-center">
          <CheckCircle2 className="h-12 w-12 text-emerald-600" aria-hidden="true" />
          <h2 id="titulo-venta-registrada" className="mt-2 text-lg font-bold text-slate-900">
            Venta registrada
          </h2>
          <p className="font-mono text-sm text-slate-500">Comprobante #{venta.numero_comprobante}</p>
        </div>

        <ul className="mt-5 max-h-52 space-y-1.5 overflow-y-auto border-y-2 border-dashed border-amber-200 py-4 text-sm">
          {venta.detalles.map((linea) => (
            <li key={linea.id_detalle_venta} className="flex justify-between gap-3">
              <span className="min-w-0 text-slate-700">
                <span className="tabular-nums">{linea.cantidad}</span> × {linea.nombre_producto}
              </span>
              <span className="tabular-nums text-slate-900">{bolivianos(linea.subtotal)}</span>
            </li>
          ))}
        </ul>

        <dl className="mt-4 space-y-1.5 text-sm">
          <div className="flex items-baseline justify-between">
            <dt className="font-semibold text-slate-600">Total</dt>
            <dd className="text-2xl font-black tabular-nums text-slate-900">{bolivianos(venta.total)}</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-slate-500">Pago</dt>
            <dd>
              <ChipMetodo metodo={venta.metodo_pago} />
            </dd>
          </div>
          {recibido !== null ? (
            <div className="flex justify-between">
              <dt className="text-slate-500">Recibido</dt>
              <dd className="tabular-nums text-slate-700">{bolivianos(recibido)}</dd>
            </div>
          ) : null}
          {cambio !== null ? (
            <div className="flex justify-between rounded-lg bg-emerald-50 px-3 py-2">
              <dt className="font-semibold text-emerald-800">Cambio</dt>
              <dd className="text-lg font-black tabular-nums text-emerald-800">{bolivianos(cambio)}</dd>
            </div>
          ) : null}
          {venta.id_transaccion_stripe ? (
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Id Stripe</dt>
              <dd className="truncate font-mono text-xs text-slate-500">{venta.id_transaccion_stripe}</dd>
            </div>
          ) : null}
        </dl>

        <button
          ref={botonRef}
          type="button"
          onClick={onCerrar}
          className="mt-6 w-full rounded-2xl bg-amber-700 px-4 py-3.5 text-base font-bold text-white hover:bg-amber-800 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300"
        >
          Nueva venta
        </button>
      </div>
    </div>
  );
}
