import { ArrowLeft, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import productoService from '../../../../services/productoService';
import type { Producto } from '../../../../types/producto';
import { pedidoService, type PedidoRegistrado } from './pedidoService';

interface Linea {
  id_producto: number;
  nombre: string;
  precio: string;
  cantidad: number;
}

function bolivianos(valor: string | number): string {
  return `Bs ${Number(valor).toFixed(2)}`;
}

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
  const [fechaEntrega, setFechaEntrega] = useState('');
  const [metodo, setMetodo] = useState<'efectivo' | 'stripe'>('efectivo');
  const [lineas, setLineas] = useState<Linea[]>([]);
  const [productoId, setProductoId] = useState('');
  const [cantidad, setCantidad] = useState(1);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [pedido, setPedido] = useState<PedidoRegistrado | null>(null);
  const [abiertos, setAbiertos] = useState<PedidoRegistrado[]>([]);
  const [numeroTarjeta, setNumeroTarjeta] = useState('');
  const [expMes, setExpMes] = useState('');
  const [expAnio, setExpAnio] = useState('');
  const [cvc, setCvc] = useState('');

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

  const totalCentavos = lineas.reduce(
    (suma, linea) => suma + Math.round(Number(linea.precio) * 100) * linea.cantidad,
    0,
  );

  function agregarLinea() {
    const pan = panes.find((item) => String(item.id_producto) === productoId);
    if (!pan || cantidad < 1) return;
    setLineas((actuales) => {
      const yaEsta = actuales.find((linea) => linea.id_producto === pan.id_producto);
      if (yaEsta) {
        return actuales.map((linea) =>
          linea.id_producto === pan.id_producto
            ? { ...linea, cantidad: linea.cantidad + cantidad }
            : linea,
        );
      }
      return [
        ...actuales,
        {
          id_producto: pan.id_producto,
          nombre: pan.nombre,
          precio: pan.precio_venta,
          cantidad,
        },
      ];
    });
  }

  async function guardar() {
    setError('');
    setEnviando(true);
    try {
      const creado = await pedidoService.registrar({
        cliente: {
          nombre: nombre.trim(),
          telefono: telefono.trim(),
          direccion: direccion.trim(),
        },
        fecha_entrega: new Date(fechaEntrega).toISOString(),
        metodo_pago: metodo,
        detalles: lineas.map((linea) => ({
          id_producto: linea.id_producto,
          cantidad: linea.cantidad,
        })),
      });
      setPedido(creado);
      await cargarAbiertos();
    } catch (causa) {
      setError(mensajeDeError(causa));
    } finally {
      setEnviando(false);
    }
  }

  async function mover(estado: string) {
    if (!pedido) return;
    const cobraTarjeta = estado === 'entregado' && pedido.metodo_pago === 'stripe';
    if (cobraTarjeta && (!numeroTarjeta.trim() || !expMes || !expAnio || !cvc.trim())) {
      setError('Para entregar con tarjeta indica número, vencimiento y CVC.');
      return;
    }
    setError('');
    setEnviando(true);
    try {
      const actualizado = await pedidoService.cambiarEstado(
        pedido.id_pedido,
        estado,
        cobraTarjeta
          ? {
              numero: numeroTarjeta.trim(),
              exp_mes: Number(expMes),
              exp_anio: Number(expAnio),
              cvc: cvc.trim(),
              titular: pedido.cliente,
            }
          : undefined,
      );
      setPedido(actualizado);
      await cargarAbiertos();
    } catch (causa) {
      setError(mensajeDeError(causa));
    } finally {
      setEnviando(false);
    }
  }

  const acciones = pedido ? (ACCIONES[pedido.estado] ?? []) : [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Link to="/dashboard/comercializacion" className="inline-flex items-center gap-2 text-sm text-slate-500">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Comercialización
      </Link>
      <h2 className="text-2xl font-bold text-slate-900">Registrar pedido</h2>

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
                  onClick={() => setPedido(item)}
                  className="flex w-full justify-between py-2 text-left"
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
        <section className="space-y-3 rounded-3xl bg-white p-6 shadow-sm">
          <h3 className="text-xl font-bold text-slate-900">Pedido {pedido.id_pedido}</h3>
          <p className="text-sm text-slate-600">
            {pedido.cliente} · {NOMBRE_ESTADO[pedido.estado] ?? pedido.estado} · {bolivianos(pedido.total)}
          </p>
          <p className="text-sm text-slate-500">
            {pedido.estado === 'entregado'
              ? `Se registró la venta${pedido.numero_comprobante ? ` ${pedido.numero_comprobante}` : ''} y se descontó el stock.`
              : pedido.estado === 'listo'
                ? 'Entregar cobra con el método previsto, crea la venta y baja el stock.'
                : pedido.estado === 'cancelado'
                  ? 'El pedido quedó cancelado. No hay venta ni movimiento de stock.'
                  : 'Cambiar el estado no cobra ni descuenta stock.'}
          </p>
          {pedido.estado === 'listo' && pedido.metodo_pago === 'stripe' ? (
            <div className="grid gap-2 sm:grid-cols-4">
              <input
                value={numeroTarjeta}
                onChange={(evento) => setNumeroTarjeta(evento.target.value)}
                placeholder="Número de tarjeta"
                className="rounded-xl border border-slate-200 px-3 py-2 text-sm sm:col-span-2"
              />
              <input
                value={expMes}
                onChange={(evento) => setExpMes(evento.target.value)}
                placeholder="Mes"
                className="rounded-xl border border-slate-200 px-3 py-2 text-sm"
              />
              <input
                value={expAnio}
                onChange={(evento) => setExpAnio(evento.target.value)}
                placeholder="Año"
                className="rounded-xl border border-slate-200 px-3 py-2 text-sm"
              />
              <input
                value={cvc}
                onChange={(evento) => setCvc(evento.target.value)}
                placeholder="CVC"
                className="rounded-xl border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            {acciones.map((accion) => (
              <button
                key={accion.estado}
                type="button"
                disabled={enviando}
                onClick={() => {
                  void mover(accion.estado);
                }}
                className={
                  accion.estado === 'cancelado'
                    ? 'rounded-xl border border-red-200 px-4 py-2 text-sm font-semibold text-red-700 disabled:opacity-50'
                    : 'rounded-xl bg-amber-400 px-4 py-2 text-sm font-bold text-[#2b1a10] disabled:opacity-50'
                }
              >
                {accion.etiqueta}
              </button>
            ))}
          </div>
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
        </section>
      ) : null}

      <form
        className="space-y-4 rounded-3xl bg-white p-6 shadow-sm"
        onSubmit={(evento) => {
          evento.preventDefault();
          void guardar();
        }}
      >
        <label className="block text-sm font-semibold text-slate-700">
          Cliente
          <input
            required
            value={nombre}
            onChange={(evento) => setNombre(evento.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
          />
        </label>
        <label className="block text-sm font-semibold text-slate-700">
          Teléfono
          <input
            value={telefono}
            onChange={(evento) => setTelefono(evento.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
          />
        </label>
        <label className="block text-sm font-semibold text-slate-700">
          Dirección
          <input
            value={direccion}
            onChange={(evento) => setDireccion(evento.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
          />
        </label>
        <label className="block text-sm font-semibold text-slate-700">
          Fecha de entrega
          <input
            required
            type="datetime-local"
            value={fechaEntrega}
            onChange={(evento) => setFechaEntrega(evento.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
          />
        </label>
        <fieldset className="text-sm font-semibold text-slate-700">
          <legend>Cómo va a pagar al retirar</legend>
          <label className="mr-4 font-normal">
            <input
              type="radio"
              name="metodo"
              checked={metodo === 'efectivo'}
              onChange={() => setMetodo('efectivo')}
            />{' '}
            Efectivo
          </label>
          <label className="font-normal">
            <input
              type="radio"
              name="metodo"
              checked={metodo === 'stripe'}
              onChange={() => setMetodo('stripe')}
            />{' '}
            Tarjeta
          </label>
        </fieldset>

        <div className="flex flex-wrap items-end gap-2">
          <label className="text-sm font-semibold text-slate-700">
            Pan
            <select
              value={productoId}
              onChange={(evento) => setProductoId(evento.target.value)}
              className="mt-1 block rounded-xl border border-slate-200 px-3 py-2"
            >
              <option value="">Elegir</option>
              {panes.map((pan) => (
                <option key={pan.id_producto} value={pan.id_producto}>
                  {pan.nombre} · {bolivianos(pan.precio_venta)}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-semibold text-slate-700">
            Cantidad
            <input
              type="number"
              min={1}
              value={cantidad}
              onChange={(evento) => setCantidad(Number(evento.target.value))}
              className="mt-1 block w-24 rounded-xl border border-slate-200 px-3 py-2"
            />
          </label>
          <button
            type="button"
            onClick={agregarLinea}
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          >
            Agregar
          </button>
        </div>

        <ul className="divide-y divide-slate-100 text-sm">
          {lineas.map((linea) => (
            <li key={linea.id_producto} className="flex justify-between py-2">
              <span>
                {linea.nombre} × {linea.cantidad}
              </span>
              <span>{bolivianos((Number(linea.precio) * linea.cantidad).toFixed(2))}</span>
            </li>
          ))}
        </ul>
        <p className="text-lg font-bold text-slate-900">
          Total estimado {bolivianos((totalCentavos / 100).toFixed(2))}
        </p>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button
          type="submit"
          disabled={enviando || lineas.length === 0 || !nombre.trim() || !fechaEntrega}
          className="inline-flex items-center gap-2 rounded-2xl bg-amber-400 px-5 py-3 font-bold text-[#2b1a10] disabled:opacity-50"
        >
          {enviando ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
          Guardar pedido
        </button>
      </form>
    </div>
  );
}
