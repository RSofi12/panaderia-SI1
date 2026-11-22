import { PackageSearch, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { disponibilidadService } from '../../../services/disponibilidadService';
import type { ProductoDisponible } from '../../../types/disponibilidad';

export default function DisponibilidadPage() {
  const [productos, setProductos] = useState<ProductoDisponible[]>([]);
  const [busqueda, setBusqueda] = useState('');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    disponibilidadService.listar({ q: busqueda.trim() }).then((datos) => {
      if (vigente) { setProductos(datos); setError(''); setCargando(false); }
    }).catch(() => {
      if (vigente) { setError('No se pudo cargar la disponibilidad.'); setCargando(false); }
    });
    return () => { vigente = false; };
  }, [busqueda]);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header>
        <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900"><PackageSearch className="h-7 w-7 text-amber-700" aria-hidden="true" />Disponibilidad de productos</h1>
        <p className="mt-1 text-sm text-slate-500">Consulta rápida de los panes activos disponibles para la venta.</p>
      </header>
      <label className="relative block rounded-2xl border border-slate-200 bg-white shadow-xs">
        <span className="sr-only">Buscar producto</span>
        <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
        <input value={busqueda} onChange={(event) => setBusqueda(event.target.value)} placeholder="Buscar por nombre o descripción" className="w-full rounded-2xl py-3 pl-11 pr-4 text-sm outline-none focus:ring-4 focus:ring-amber-100" />
      </label>
      {error ? <p className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p> : null}
      {cargando ? <p className="text-sm text-slate-500">Cargando disponibilidad…</p> : null}
      {!cargando && !error && productos.length === 0 ? <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No hay productos disponibles.</p> : null}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {productos.map((producto) => (
          <article key={producto.id_producto} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">{producto.categoria}</p>
            <h2 className="mt-1 text-lg font-bold text-slate-900">{producto.nombre}</h2>
            <p className="mt-4 text-3xl font-bold tabular-nums text-slate-900">{producto.stock_actual}</p>
            <p className="text-xs text-slate-500">unidades disponibles</p>
            <div className="mt-4 flex justify-between border-t border-slate-100 pt-3 text-sm"><span>Precio: Bs {Number(producto.precio_venta).toFixed(2)}</span><strong>Bs {Number(producto.valor_disponible).toFixed(2)}</strong></div>
          </article>
        ))}
      </div>
    </div>
  );
}
