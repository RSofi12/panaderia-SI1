import { ArrowLeft, Banknote, Check, CreditCard, Loader2, Minus, Plus, ShoppingBasket, Trash2, X } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { ElementType } from 'react';
import { Link } from 'react-router-dom';
import productoService from '../../../../services/productoService';
import type { Producto } from '../../../../types/producto';
import { ModalPagoTarjeta } from '../ventas/ModalPagoTarjeta';
import { pedidoService, type PedidoRegistrado } from './pedidoService';

interface Linea {
  id_producto: number;
  nombre: string;
  precio: string;
  cantidad: number;
}

const HORAS = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'];

const NOMBRE_ESTADO: Record<string, string> = {
  pendiente: 'Pendiente',
  en_preparacion: 'En preparación',
  listo: 'Listo',
  cancelado: 'Cancelado',
  entregado: 'Entregado',
};

const ACCIONES: Record<string, { estado: string; etiqueta: string }[]> = {
  pendiente: [
    { estado: 'en_preparacion', etiqueta: 'Preparar' },
    { estado: 'cancelado', etiqueta: 'Cancelar' },
  ],
  en_preparacion: [
    { estado: 'listo', etiqueta: 'Marcar listo' },
    { estado: 'cancelado', etiqueta: 'Cancelar' },
  ],
  listo: [
    { estado: 'entregado', etiqueta: 'Entregar' },
    { estado: 'cancelado', etiqueta: 'Cancelar' },
  ],
};

function bolivianos(valor: string | number): string {
  return `Bs ${Number(valor).toFixed(2)}`;
}

function hoyLocal(): string {
  const ahora = new Date();
  const mes = String(ahora.getMonth() + 1).padStart(2, '0');
  const dia = String(ahora.getDate()).padStart(2, '0');
  return `${ahora.getFullYear()}-${mes}-${dia}`;
}

function horasDisponibles(fecha: string): string[] {
  if (!fecha) return HORAS;
  if (fecha > hoyLocal()) return HORAS;
  if (fecha < hoyLocal()) return [];
  const ahora = new Date();
  return HORAS.filter((hora) => {
    const [hh, mm] = hora.split(':').map(Number);
    const cita = new Date(ahora.getFullYear(), ahora.getMonth(), ahora.getDate(), hh, mm, 0, 0);
    return cita.getTime() > ahora.getTime();
  });
}

function isoEntrega(fecha: string, hora: string): string {
  const [anio, mes, dia] = fecha.split('-').map(Number);
  const [hh, mm] = hora.split(':').map(Number);
  return new Date(anio, mes - 1, dia, hh, mm, 0, 0).toISOString();
}

const PASOS_PEDIDO = [
  { estado: 'pendiente', titulo: 'Pendiente', accion: 'Pendiente' },
  { estado: 'en_preparacion', titulo: 'Preparar', accion: 'Preparar' },
  { estado: 'listo', titulo: 'Listo', accion: 'Marcar listo' },
  { estado: 'entregado', titulo: 'Entregar', accion: 'Entregar' },
] as const;

function LineaTiempoPedido({
  estado,
  enviando,
  onAvanzar,
}: {
  estado: string;
  enviando: boolean;
  onAvanzar: (estado: string) => void;
}) {
  const cancelado = estado === 'cancelado';
  const indiceActual = PASOS_PEDIDO.findIndex((paso) => paso.estado === estado);

  return (
    <ol aria-label="Pasos del pedido" className="-mx-4 grid w-[calc(100%+2rem)] grid-cols-4 sm:mx-auto sm:w-full sm:max-w-md">
      {PASOS_PEDIDO.map((paso, indice) => {
        const hecho = !cancelado && indiceActual > indice;
        const actual = !cancelado && indiceActual === indice;
        const siguiente = !cancelado && indice === indiceActual + 1;
        const pista = siguiente
          ? paso.accion === paso.titulo
            ? 'Toca aquí'
            : paso.accion
          : actual
            ? 'Estás aquí'
            : hecho
              ? 'Hecho'
              : 'Después';
        const claseCirculo = cancelado
          ? 'border-slate-200 bg-slate-100 text-slate-500'
          : hecho
            ? 'border-amber-600 bg-amber-600 text-white'
            : actual
              ? 'border-amber-500 bg-white text-amber-900 ring-4 ring-amber-100'
              : siguiente
                ? 'border-amber-500 bg-amber-400 text-[#2b1a10] group-hover:bg-amber-300'
                : 'border-slate-200 bg-white text-slate-500';
        const marca = (
          <span className={`relative z-10 flex h-11 w-11 items-center justify-center rounded-full border-2 text-sm font-bold ${claseCirculo}`}>
            {hecho ? <Check className="h-5 w-5" aria-hidden="true" /> : indice + 1}
          </span>
        );
        const textos = (
          <>
            <span className={`mt-2 block w-full whitespace-nowrap text-xs font-bold leading-4 tracking-tight ${actual || siguiente ? 'text-slate-900' : 'text-slate-500'}`}>
              {paso.titulo}
            </span>
            {cancelado ? (
              <span className="mt-0.5 block min-h-8 w-full" />
            ) : (
              <span className={`mt-0.5 block min-h-8 w-full text-xs leading-4 ${siguiente || actual ? 'font-semibold text-amber-800' : 'text-slate-500'}`}>
                {pista}
              </span>
            )}
          </>
        );
        const conector = indice === 0 ? null : (
          <span
            aria-hidden="true"
            className={`absolute top-[22px] right-1/2 h-0.5 w-full -translate-y-1/2 ${
              !cancelado && indice <= indiceActual ? 'bg-amber-500' : 'bg-slate-200'
            }`}
          />
        );

        if (siguiente) {
          return (
            <li key={paso.estado} className="relative min-w-0">
              {conector}
              <button
                type="button"
                disabled={enviando}
                onClick={() => onAvanzar(paso.estado)}
                aria-label={`${paso.accion}. Paso ${indice + 1} de ${PASOS_PEDIDO.length}`}
                className="group flex w-full cursor-pointer scroll-mt-24 flex-col items-center rounded-2xl px-0.5 py-1 text-center hover:bg-amber-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300/70 disabled:opacity-50"
              >
                {marca}
                {textos}
              </button>
            </li>
          );
        }

        return (
          <li
            key={paso.estado}
            className="relative flex min-w-0 flex-col items-center px-0.5 py-1 text-center"
            aria-current={actual ? 'step' : undefined}
          >
            {conector}
            {marca}
            {textos}
          </li>
        );
      })}
    </ol>
  );
}

function mensajeDeError(error: unknown): string {
  const datos = (error as { response?: { data?: unknown } })?.response?.data;
  if (!datos || typeof datos !== 'object') {
    return 'No se pudo completar la operación.';
  }
  const partes = Object.values(datos as Record<string, unknown>).flatMap((valor) =>
    Array.isArray(valor) ? valor.map(String) : [String(valor)],
  );
  return partes.join(' ') || 'El pedido fue rechazado.';
}

export default function RegistrarPedidoPage() {
  const [panes, setPanes] = useState<Producto[]>([]);
  const [nombre, setNombre] = useState('');
  const [telefono, setTelefono] = useState('');
  const [direccion, setDireccion] = useState('');
  const [fecha, setFecha] = useState('');
  const [hora, setHora] = useState('');
  const [metodo, setMetodo] = useState<'efectivo' | 'stripe'>('efectivo');
  const [lineas, setLineas] = useState<Linea[]>([]);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [pedido, setPedido] = useState<PedidoRegistrado | null>(null);
  const [abiertos, setAbiertos] = useState<PedidoRegistrado[]>([]);
  const [modalTarjetaAbierto, setModalTarjetaAbierto] = useState(false);
  const [cobrandoNuevo, setCobrandoNuevo] = useState(false);
  const [confirmarCancelacion, setConfirmarCancelacion] = useState(false);
  const [pedidoGuardado, setPedidoGuardado] = useState<PedidoRegistrado | null>(null);
  const [pedidoEntregado, setPedidoEntregado] = useState<PedidoRegistrado | null>(null);
  const detalleRef = useRef<HTMLElement>(null);

  const horas = useMemo(() => horasDisponibles(fecha), [fecha]);

  async function cargarAbiertos() {
    const pedidos = await pedidoService.listarAbiertos();
    setAbiertos(pedidos);
  }

  useEffect(() => {
    let vivo = true;
    Promise.all([productoService.listar({ activo: 'true' }), pedidoService.listarAbiertos()])
      .then(([catalogo, pedidos]) => {
        if (!vivo) return;
        setPanes(catalogo);
        setAbiertos(pedidos);
      })
      .catch(() => {
        if (vivo) setError('No se pudo cargar la pantalla de pedidos.');
      });
    return () => {
      vivo = false;
    };
  }, []);

  useEffect(() => {
    if (hora && !horas.includes(hora)) setHora('');
  }, [hora, horas]);

  const totalCentavos = lineas.reduce(
    (suma, linea) => suma + Math.round(Number(linea.precio) * 100) * linea.cantidad,
    0,
  );
  const unidades = lineas.reduce((suma, linea) => suma + linea.cantidad, 0);

  function agregar(pan: Producto) {
    setLineas((actuales) => {
      const yaEsta = actuales.find((linea) => linea.id_producto === pan.id_producto);
      if (yaEsta) {
        return actuales.map((linea) =>
          linea.id_producto === pan.id_producto ? { ...linea, cantidad: linea.cantidad + 1 } : linea,
        );
      }
      return [
        ...actuales,
        {
          id_producto: pan.id_producto,
          nombre: pan.nombre,
          precio: pan.precio_venta,
          cantidad: 1,
        },
      ];
    });
  }

  function cambiarCantidad(idProducto: number, cantidad: number) {
    setLineas((actuales) =>
      actuales.flatMap((linea) => {
        if (linea.id_producto !== idProducto) return [linea];
        if (!Number.isFinite(cantidad) || cantidad <= 0) return [];
        return [{ ...linea, cantidad: Math.floor(cantidad) }];
      }),
    );
  }

  function datosPedido(idTransaccionStripe?: string) {
    return {
      cliente: {
        nombre: nombre.trim(),
        telefono: telefono.trim(),
        direccion: direccion.trim(),
      },
      fecha_entrega: isoEntrega(fecha, hora),
      metodo_pago: metodo,
      id_transaccion_stripe: idTransaccionStripe,
      detalles: lineas.map((linea) => ({
        id_producto: linea.id_producto,
        cantidad: linea.cantidad,
      })),
    };
  }

  function listoParaGuardar(): boolean {
    if (!nombre.trim() || lineas.length === 0 || !fecha || !hora || !horas.includes(hora)) {
      setError('Elige un día de hoy en adelante y una hora entre las 08:00 y las 17:00.');
      return false;
    }
    return true;
  }

  async function guardar() {
    setError('');
    if (!fecha || !hora || !horas.includes(hora)) {
      setError('Elige un día de hoy en adelante y una hora entre las 08:00 y las 17:00.');
      return;
    }
    setEnviando(true);
    try {
      const creado = await pedidoService.registrar(datosPedido());
      setPedido(creado);
      setPedidoGuardado(creado);
      setLineas([]);
      await cargarAbiertos();
    } catch (causa) {
      setError(mensajeDeError(causa));
    } finally {
      setEnviando(false);
    }
  }

  async function mover(estado: string, idTransaccionStripe?: string) {
    if (!pedido) return;
    setError('');
    setEnviando(true);
    try {
      const actualizado = await pedidoService.cambiarEstado(pedido.id_pedido, estado, idTransaccionStripe);
      setPedido(actualizado);
      if (estado === 'entregado') setPedidoEntregado(actualizado);
      setConfirmarCancelacion(false);
      setModalTarjetaAbierto(false);
      await cargarAbiertos();
    } catch (causa) {
      setError(mensajeDeError(causa));
    } finally {
      setEnviando(false);
    }
  }

  function abrirPasarela() {
    if (!listoParaGuardar()) return;
    setError('');
    setCobrandoNuevo(true);
  }

  async function guardarConTarjeta(idTransaccionStripe: string) {
    setError('');
    setEnviando(true);
    try {
      const creado = await pedidoService.registrar(datosPedido(idTransaccionStripe));
      setPedido(creado);
      setPedidoGuardado(creado);
      setCobrandoNuevo(false);
      setLineas([]);
      await cargarAbiertos();
    } catch (causa) {
      setError(mensajeDeError(causa));
      throw causa;
    } finally {
      setEnviando(false);
    }
  }

  async function entregarConTarjeta(idTransaccionStripe: string) {
    if (!pedido) return;
    setError('');
    setEnviando(true);
    try {
      const actualizado = await pedidoService.cambiarEstado(
        pedido.id_pedido,
        'entregado',
        idTransaccionStripe,
      );
      setPedido(actualizado);
      setPedidoEntregado(actualizado);
      setModalTarjetaAbierto(false);
      await cargarAbiertos();
    } catch (causa) {
      setError(mensajeDeError(causa));
      throw causa;
    } finally {
      setEnviando(false);
    }
  }

  const acciones = pedido ? (ACCIONES[pedido.estado] ?? []) : [];
  const puedeCancelar = acciones.some((accion) => accion.estado === 'cancelado');
  const cantidadPorProducto = new Map(lineas.map((linea) => [linea.id_producto, linea.cantidad]));

  function abrirPedido(item: PedidoRegistrado) {
    setPedido(item);
    setConfirmarCancelacion(false);
    const reducirMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    requestAnimationFrame(() => {
      detalleRef.current?.scrollIntoView({
        behavior: reducirMovimiento ? 'auto' : 'smooth',
        block: 'nearest',
      });
    });
  }

  function avanzar(estadoDestino: string) {
    if (!pedido) return;
    if (
      estadoDestino === 'entregado' &&
      pedido.metodo_pago === 'stripe' &&
      !pedido.id_transaccion_stripe
    ) {
      setError('');
      setModalTarjetaAbierto(true);
      return;
    }
    void mover(estadoDestino);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="flex flex-col gap-1">
        <Link to="/dashboard/comercializacion" className="inline-flex w-fit items-center gap-2 text-sm text-slate-500">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Comercialización
        </Link>
        <span className="mt-2 inline-flex w-fit items-center rounded-full bg-amber-100 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-amber-800">
          CU14 · Registrar pedido
        </span>
        <h2 className="mt-2 text-2xl font-bold text-slate-900">Registrar pedido</h2>
      </header>

      <section className="rounded-3xl bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700">Pedidos abiertos</h3>
        {abiertos.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">No hay pedidos pendientes, en preparación ni listos.</p>
        ) : (
          <ul className="mt-2 divide-y divide-slate-100 text-sm">
            {abiertos.map((item) => (
              <li key={item.id_pedido}>
                <button
                  type="button"
                  onClick={() => abrirPedido(item)}
                  aria-current={pedido?.id_pedido === item.id_pedido ? 'true' : undefined}
                  className={`flex min-h-11 w-full items-center justify-between rounded-xl px-2 text-left ${
                    pedido?.id_pedido === item.id_pedido ? 'bg-amber-50' : ''
                  }`}
                >
                  <span>
                    #{item.id_pedido} · {item.cliente}
                  </span>
                  <span>{NOMBRE_ESTADO[item.estado] ?? item.estado}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {pedido ? (
        <section ref={detalleRef} className="space-y-4 rounded-3xl bg-white p-6 shadow-sm">
          <h3 className="text-xl font-bold text-slate-900">Pedido {pedido.id_pedido}</h3>
          <p className="text-sm text-slate-600">
            {pedido.cliente} · {NOMBRE_ESTADO[pedido.estado] ?? pedido.estado} · {bolivianos(pedido.total)}
          </p>
          <LineaTiempoPedido estado={pedido.estado} enviando={enviando} onAvanzar={avanzar} />
          <p className="text-sm text-slate-500">
            {pedido.estado === 'entregado'
              ? `Se registró la venta${pedido.numero_comprobante ? ` ${pedido.numero_comprobante}` : ''} y se descontó el stock.`
              : pedido.estado === 'listo'
                ? pedido.metodo_pago === 'stripe' && !pedido.id_transaccion_stripe
                  ? 'El paso Entregar abre la ventana de Stripe para que el cliente ingrese su tarjeta. Eso crea la venta y baja el stock.'
                  : pedido.metodo_pago === 'stripe'
                    ? 'La tarjeta ya se cobró al guardar. El paso Entregar crea la venta y baja el stock.'
                    : 'El paso Entregar cobra en efectivo, crea la venta y baja el stock.'
                : pedido.estado === 'cancelado'
                  ? 'El pedido quedó cancelado. No hay venta ni movimiento de stock.'
                  : 'Solo se puede avanzar al paso siguiente. Eso no cobra ni descuenta stock.'}
          </p>
          {puedeCancelar ? (
            <button
              type="button"
              disabled={enviando}
              onClick={() => setConfirmarCancelacion(true)}
              className="min-h-11 rounded-xl border border-red-200 px-4 text-sm font-semibold text-red-700 disabled:opacity-50"
            >
              Cancelar pedido
            </button>
          ) : null}
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
        </section>
      ) : null}

      {pedidoGuardado ? (
        <DialogoPedidoGuardado
          pedido={pedidoGuardado}
          onCerrar={() => setPedidoGuardado(null)}
        />
      ) : null}

      {pedidoEntregado ? (
        <DialogoPedidoEntregado
          pedido={pedidoEntregado}
          onCerrar={() => setPedidoEntregado(null)}
        />
      ) : null}

      {confirmarCancelacion ? (
        <DialogoCancelar
          enviando={enviando}
          onVolver={() => setConfirmarCancelacion(false)}
          onConfirmar={() => {
            void mover('cancelado');
          }}
        />
      ) : null}

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <section className="@container">
          <p className="mb-3 text-sm text-slate-500">
            Toca un pan para sumarlo. El precio queda congelado. El stock se revisa al entregar, no ahora.
          </p>
          <ul className="grid grid-cols-1 gap-3 @min-[26rem]:grid-cols-2 @min-[42rem]:grid-cols-3">
            {panes.map((pan) => (
              <li key={pan.id_producto}>
                <TarjetaPan
                  pan={pan}
                  enPedido={cantidadPorProducto.get(pan.id_producto) ?? 0}
                  onAgregar={() => agregar(pan)}
                />
              </li>
            ))}
          </ul>
        </section>

        <aside aria-label="Pedido" className="min-w-0 xl:sticky xl:top-4">
          <form
            className="space-y-4 rounded-t-3xl border border-b-0 border-amber-200/70 bg-[#fffaf1] p-5 shadow-md"
            onSubmit={(evento) => {
              evento.preventDefault();
              void guardar();
            }}
          >
            <div className="flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-base font-bold text-slate-900">
                <ShoppingBasket className="h-5 w-5 text-amber-700" aria-hidden="true" />
                Pedido
                {unidades > 0 ? (
                  <span className="rounded-full bg-amber-700 px-2 py-0.5 text-[11px] font-bold text-white">{unidades}</span>
                ) : null}
              </h3>
              {lineas.length > 0 ? (
                <button
                  type="button"
                  onClick={() => setLineas([])}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500"
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                  Vaciar
                </button>
              ) : null}
            </div>

            <label className="block text-sm font-semibold text-slate-700">
              Cliente
              <input
                required
                value={nombre}
                onChange={(evento) => setNombre(evento.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              Teléfono
              <input
                value={telefono}
                onChange={(evento) => setTelefono(evento.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              Dirección
              <input
                value={direccion}
                onChange={(evento) => setDireccion(evento.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2"
              />
            </label>
            <div className="grid grid-cols-2 gap-2">
              <label className="text-sm font-semibold text-slate-700">
                Día de entrega
                <input
                  required
                  type="date"
                  min={hoyLocal()}
                  value={fecha}
                  onChange={(evento) => setFecha(evento.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                Hora
                <select
                  required
                  value={hora}
                  onChange={(evento) => setHora(evento.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2"
                >
                  <option value="">Elegir</option>
                  {horas.map((opcion) => (
                    <option key={opcion} value={opcion}>
                      {opcion}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <p className="text-xs text-slate-500">
              Solo días de hoy en adelante, de 08:00 a 17:00. Las horas que ya pasaron no aparecen.
            </p>

            {lineas.length === 0 ? (
              <p className="py-6 text-center text-sm text-slate-500">Toca los panes para armar el pedido.</p>
            ) : (
              <ul className="space-y-3">
                {lineas.map((linea) => (
                  <LineaPedido
                    key={linea.id_producto}
                    linea={linea}
                    onCambiar={(cantidad) => cambiarCantidad(linea.id_producto, cantidad)}
                  />
                ))}
              </ul>
            )}

            <div className="flex items-baseline justify-between border-t-2 border-dashed border-amber-200 pt-4">
              <span className="text-sm font-semibold uppercase tracking-wider text-slate-500">Total</span>
              <span className="text-3xl font-black tabular-nums text-slate-900">
                {bolivianos((totalCentavos / 100).toFixed(2))}
              </span>
            </div>

            <fieldset>
              <legend className="text-xs font-semibold text-slate-600">¿Cómo paga el cliente?</legend>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <OpcionMetodo
                  activo={metodo === 'efectivo'}
                  icono={Banknote}
                  titulo="Efectivo"
                  onSeleccionar={() => setMetodo('efectivo')}
                />
                <OpcionMetodo
                  activo={metodo === 'stripe'}
                  icono={CreditCard}
                  titulo="Tarjeta"
                  subtitulo="Stripe"
                  onSeleccionar={() => setMetodo('stripe')}
                />
              </div>
            </fieldset>
            {metodo === 'stripe' ? (
              <div className="rounded-2xl border border-amber-200/80 bg-white p-4">
                <p className="text-sm font-bold text-slate-800">Tarjeta de débito o crédito</p>
                <p className="mt-1 text-xs leading-relaxed text-slate-500">
                  Al presionar el botón se abre la pasarela de Stripe para que el cliente ingrese su tarjeta.
                </p>
              </div>
            ) : null}

            {error ? <p className="text-sm text-red-700">{error}</p> : null}
            {metodo === 'stripe' ? (
              <button
                type="button"
                disabled={enviando || lineas.length === 0 || !nombre.trim() || !fecha || !hora}
                onClick={abrirPasarela}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-amber-700 px-4 py-4 text-base font-bold text-white disabled:bg-slate-300 disabled:text-slate-500"
              >
                <CreditCard className="h-5 w-5" aria-hidden="true" />
                {`Pagar ${bolivianos((totalCentavos / 100).toFixed(2))} con tarjeta`}
              </button>
            ) : (
              <button
                type="submit"
                disabled={enviando || lineas.length === 0 || !nombre.trim() || !fecha || !hora}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-amber-700 px-4 py-4 text-base font-bold text-white disabled:bg-slate-300 disabled:text-slate-500"
              >
                {enviando ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> : null}
                Guardar pedido
              </button>
            )}
          </form>
        </aside>
      </div>

      <ModalPagoTarjeta
        abierto={cobrandoNuevo || modalTarjetaAbierto}
        totalTexto={
          cobrandoNuevo || !pedido
            ? bolivianos((totalCentavos / 100).toFixed(2))
            : bolivianos(pedido.total)
        }
        totalCentavos={
          cobrandoNuevo || !pedido
            ? totalCentavos
            : Math.round(Number(pedido.total) * 100)
        }
        procesando={enviando}
        errorMensaje={error}
        titularInicial={cobrandoNuevo || !pedido ? nombre.trim() || 'Cliente' : pedido.cliente}
        detalles={lineas.map((linea) => ({
          id_producto: linea.id_producto,
          cantidad: linea.cantidad,
        }))}
        obtenerIntencion={
          cobrandoNuevo || !pedido
            ? () =>
                pedidoService.crearIntencionDeLineas(
                  lineas.map((linea) => ({
                    id_producto: linea.id_producto,
                    cantidad: linea.cantidad,
                  })),
                )
            : () => pedidoService.crearIntencion(pedido.id_pedido)
        }
        obtenerClavePublica={pedidoService.obtenerClavePublicaStripe}
        onCerrar={() => {
          if (enviando) return;
          setCobrandoNuevo(false);
          setModalTarjetaAbierto(false);
        }}
        onVentaConfirmada={cobrandoNuevo || !pedido ? guardarConTarjeta : entregarConTarjeta}
      />
    </div>
  );
}

function TarjetaPan({ pan, enPedido, onAgregar }: { pan: Producto; enPedido: number; onAgregar: () => void }) {
  return (
    <button
      type="button"
      onClick={onAgregar}
      aria-label={`Agregar ${pan.nombre}, ${bolivianos(pan.precio_venta)}`}
      className={`relative flex h-full w-full flex-col rounded-2xl border bg-white p-4 text-left transition hover:-translate-y-0.5 hover:shadow-md ${
        enPedido > 0 ? 'border-amber-400 ring-2 ring-amber-200' : 'border-slate-200 hover:border-amber-300'
      }`}
    >
      {enPedido > 0 ? (
        <span className="absolute right-2 top-2 flex h-7 min-w-7 items-center justify-center rounded-full bg-amber-700 px-2 text-xs font-bold text-white">
          {enPedido}
        </span>
      ) : null}
      <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {pan.categoria_nombre || 'Pan'}
      </span>
      <span className="mt-0.5 text-base font-bold text-slate-900">{pan.nombre}</span>
      <span className="mt-3 text-xl font-black tabular-nums text-amber-800">{bolivianos(pan.precio_venta)}</span>
    </button>
  );
}

function LineaPedido({ linea, onCambiar }: { linea: Linea; onCambiar: (cantidad: number) => void }) {
  const subtotal = (Math.round(Number(linea.precio) * 100) * linea.cantidad) / 100;
  return (
    <li className="flex items-center gap-3">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-800">{linea.nombre}</p>
        <p className="text-xs tabular-nums text-slate-500">{bolivianos(linea.precio)} c/u</p>
      </div>
      <div className="flex items-center rounded-xl border border-amber-200 bg-white">
        <button
          type="button"
          onClick={() => onCambiar(linea.cantidad - 1)}
          aria-label={linea.cantidad === 1 ? `Quitar ${linea.nombre}` : `Restar una unidad de ${linea.nombre}`}
          className="flex h-8 w-8 items-center justify-center"
        >
          {linea.cantidad === 1 ? <X className="h-3.5 w-3.5" /> : <Minus className="h-3.5 w-3.5" />}
        </button>
        <span className="w-8 text-center text-sm font-bold tabular-nums">{linea.cantidad}</span>
        <button
          type="button"
          onClick={() => onCambiar(linea.cantidad + 1)}
          aria-label={`Sumar una unidad de ${linea.nombre}`}
          className="flex h-8 w-8 items-center justify-center"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
      </div>
      <span className="text-sm font-bold tabular-nums">{bolivianos(subtotal)}</span>
    </li>
  );
}

function OpcionMetodo({
  activo,
  icono: Icono,
  titulo,
  subtitulo,
  onSeleccionar,
}: {
  activo: boolean;
  icono: ElementType;
  titulo: string;
  subtitulo?: string;
  onSeleccionar: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSeleccionar}
      className={`flex items-center gap-2 rounded-xl border-2 px-3 py-2.5 text-left ${
        activo ? 'border-amber-600 bg-amber-50 text-amber-900' : 'border-slate-200 bg-white text-slate-600'
      }`}
    >
      <Icono className={`h-5 w-5 ${activo ? 'text-amber-700' : 'text-slate-400'}`} aria-hidden="true" />
      <span>
        <span className="block text-sm font-bold">{titulo}</span>
        {subtitulo ? <span className="block text-[11px] text-slate-500">{subtitulo}</span> : null}
      </span>
    </button>
  );
}

function DialogoPedidoGuardado({
  pedido,
  onCerrar,
}: {
  pedido: PedidoRegistrado;
  onCerrar: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4" role="presentation">
      <div role="dialog" aria-modal="true" aria-labelledby="titulo-guardado" className="max-w-md rounded-3xl bg-white p-6 shadow-xl">
        <h3 id="titulo-guardado" className="text-xl font-bold text-slate-900">
          El pedido ha sido guardado
        </h3>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">
          El pedido {pedido.id_pedido} de {pedido.cliente} quedó en pendiente, por {bolivianos(pedido.total)}.
        </p>
        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={onCerrar}
            className="rounded-xl bg-amber-700 px-4 py-2 text-sm font-bold text-white"
          >
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
}

function DialogoPedidoEntregado({
  pedido,
  onCerrar,
}: {
  pedido: PedidoRegistrado;
  onCerrar: () => void;
}) {
  const comprobante = pedido.numero_comprobante ? ` La venta quedó registrada como ${pedido.numero_comprobante}.` : '';
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4" role="presentation">
      <div role="dialog" aria-modal="true" aria-labelledby="titulo-entregado" className="max-w-md rounded-3xl bg-white p-6 shadow-xl">
        <h3 id="titulo-entregado" className="text-xl font-bold text-slate-900">
          El pedido ha sido entregado
        </h3>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">
          El pedido {pedido.id_pedido} de {pedido.cliente} quedó entregado, por {bolivianos(pedido.total)}.
          Se descontó el stock.{comprobante}
        </p>
        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={onCerrar}
            className="min-h-11 rounded-xl bg-amber-700 px-4 text-sm font-bold text-white focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-300/70"
          >
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
}

function DialogoCancelar({
  enviando,
  onVolver,
  onConfirmar,
}: {
  enviando: boolean;
  onVolver: () => void;
  onConfirmar: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4" role="presentation">
      <div role="dialog" aria-modal="true" aria-labelledby="titulo-cancelar" className="max-w-md rounded-3xl bg-white p-6 shadow-xl">
        <h3 id="titulo-cancelar" className="text-xl font-bold text-slate-900">
          ¿Está seguro de cancelar?
        </h3>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">
          Si cancelas, el pedido queda en cancelado. No se cobra, no se crea una venta y no se descuenta el stock.
          Ya no se podrá entregar. Al cancelar el pedido no habrá devolución del dinero.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" onClick={onVolver} className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-600">
            No, volver
          </button>
          <button
            type="button"
            disabled={enviando}
            onClick={onConfirmar}
            className="rounded-xl bg-red-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
          >
            Sí, cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
