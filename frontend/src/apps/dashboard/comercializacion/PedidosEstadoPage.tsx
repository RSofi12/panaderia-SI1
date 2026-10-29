import { ClipboardList, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { pedidoService } from '../../../services/pedidoService';
import type { EstadoPedido, Pedido } from '../../../types/pedido';

const ESTADOS: Array<{ value: EstadoPedido | ''; label: string }> = [
  { value: '', label: 'Todos los estados' },
  { value: 'pendiente', label: 'Pendiente' },
  { value: 'en_preparacion', label: 'En preparación' },
  { value: 'listo', label: 'Listo para entregar' },
  { value: 'entregado', label: 'Entregado' },
  { value: 'cancelado', label: 'Cancelado' },
];

const ETIQUETAS_ESTADO: Record<EstadoPedido, string> = {
  pendiente: 'Pendiente',
  en_preparacion: 'En preparación',
  listo: 'Listo',
  entregado: 'Entregado',
  cancelado: 'Cancelado',
};

function fecha(valor: string | null) {
  return valor ? new Date(valor).toLocaleString('es-BO', { dateStyle: 'short', timeStyle: 'short' }) : 'Sin fecha';
}

export default function PedidosEstadoPage() {
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [estado, setEstado] = useState<EstadoPedido | ''>('');
  const [busqueda, setBusqueda] = useState('');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    pedidoService.listar({ estado, q: busqueda.trim() }).then((datos) => {
      if (vigente) {
        setPedidos(datos);
        setError('');
        setCargando(false);
      }
    }).catch(() => {
      if (vigente) {
        setError('No se pudo cargar el estado de los pedidos.');
        setCargando(false);
      }
    });
    return () => { vigente = false; };
  }, [estado, busqueda]);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header>
        <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900">
          <ClipboardList className="h-7 w-7 text-amber-700" aria-hidden="true" />
          Estado de pedidos
        </h1>
        <p className="mt-1 text-sm text-slate-500">Consulta los pedidos anticipados y su avance de preparación.</p>
      </header>

      <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs sm:flex-row">
        <label className="relative flex-1">
          <span className="sr-only">Buscar pedido</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input value={busqueda} onChange={(event) => setBusqueda(event.target.value)} placeholder="Cliente, teléfono o número de pedido" className="w-full rounded-xl border border-slate-200 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-amber-400 focus:ring-4 focus:ring-amber-100" />
        </label>
        <select value={estado} onChange={(event) => setEstado(event.target.value as EstadoPedido | '')} className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-amber-400">
          {ESTADOS.map((opcion) => <option key={opcion.value} value={opcion.value}>{opcion.label}</option>)}
        </select>
      </section>

      {error ? <p className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p> : null}
      {cargando ? <p className="text-sm text-slate-500">Cargando pedidos…</p> : null}
      {!cargando && !error && pedidos.length === 0 ? <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No hay pedidos que coincidan con la búsqueda.</p> : null}
      <div className="grid gap-4 md:grid-cols-2">
        {pedidos.map((pedido) => (
          <article key={pedido.id_pedido} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-mono text-xs text-slate-400">Pedido #{pedido.id_pedido}</p>
                <h2 className="mt-1 font-bold text-slate-900">{pedido.cliente}</h2>
                <p className="text-xs text-slate-500">Registrado: {fecha(pedido.fecha_registro)}</p>
              </div>
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900">{ETIQUETAS_ESTADO[pedido.estado]}</span>
            </div>
            <div className="mt-4 space-y-1 text-sm text-slate-600">
              {pedido.detalles.map((detalle) => <p key={detalle.id_detalle_pedido}>{detalle.cantidad} × {detalle.nombre_producto}</p>)}
            </div>
            <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-sm">
              <span className="text-slate-500">Entrega: {fecha(pedido.fecha_entrega)}</span>
              <strong className="text-slate-900">Bs {Number(pedido.total).toFixed(2)}</strong>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
