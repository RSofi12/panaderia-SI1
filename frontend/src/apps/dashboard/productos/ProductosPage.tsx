import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  AlertCircle,
  CheckCircle2,
  Package,
  Pencil,
  Plus,
  Power,
  Search,
  Wheat,
} from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import productoService from '../../../services/productoService';
import type { CategoriaProducto, Producto, ProductoFiltros } from '../../../types/producto';
import ProductoFormModal from './components/ProductoFormModal';
import ConfirmarEstadoDialog from './components/ConfirmarEstadoDialog';
import { formatearBs } from './precios';
import ProduccionTab from './produccion/ProduccionTab';

type EstadoFiltro = '' | 'true' | 'false';
type PestanaProducto = 'catalogo' | 'produccion';

type ModalAbierto =
  | { tipo: 'formulario'; producto: Producto | null }
  | { tipo: 'estado'; producto: Producto }
  | null;

interface Resultado {
  clave: string;
  productos: Producto[];
  error: string | null;
}

export const ProductosPage: React.FC = () => {
  const { hasPermission } = useAuth();
  const puedeGestionar = hasPermission('gestionar_productos');
  const puedeRegistrarProduccion = hasPermission('registrar_produccion');

  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get('tab') as PestanaProducto | null;

  // Deriva la pestaña activa: si el rol es de producción (no tiene gestión de catálogo), abre producción directamente
  const pestanaActiva: PestanaProducto =
    tabParam === 'produccion' || (!puedeGestionar && puedeRegistrarProduccion)
      ? 'produccion'
      : 'catalogo';

  const cambiarPestana = (nueva: PestanaProducto) => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set('tab', nueva);
        return next;
      },
      { replace: true }
    );
  };

  const [categorias, setCategorias] = useState<CategoriaProducto[]>([]);
  const [busqueda, setBusqueda] = useState('');
  const [categoria, setCategoria] = useState('');
  const [estado, setEstado] = useState<EstadoFiltro>('');
  const [version, setVersion] = useState(0);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [modal, setModal] = useState<ModalAbierto>(null);
  const [procesandoEstado, setProcesandoEstado] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  const claveConsulta = JSON.stringify([busqueda.trim(), categoria, estado, version]);
  const cargando = resultado?.clave !== claveConsulta;

  useEffect(() => {
    let vigente = true;
    productoService
      .listarCategorias()
      .then((data) => {
        if (vigente) setCategorias(data);
      })
      .catch(() => {
        // Sin categorías el filtro queda vacío; el listado muestra su propio error.
      });
    return () => {
      vigente = false;
    };
  }, []);

  useEffect(() => {
    let vigente = true;
    const filtros: ProductoFiltros = {};
    const nombre = busqueda.trim();
    if (nombre) filtros.nombre = nombre;
    if (categoria) filtros.id_categoria = categoria;
    if (estado) filtros.activo = estado;

    const temporizador = window.setTimeout(() => {
      productoService
        .listar(filtros)
        .then((productos) => {
          if (vigente) setResultado({ clave: claveConsulta, productos, error: null });
        })
        .catch(() => {
          if (vigente) {
            setResultado({
              clave: claveConsulta,
              productos: [],
              error: 'No se pudo cargar el catálogo. Verifica que el backend esté en ejecución.',
            });
          }
        });
    }, nombre ? 250 : 0);

    return () => {
      vigente = false;
      window.clearTimeout(temporizador);
    };
  }, [busqueda, categoria, estado, claveConsulta]);

  const productos = resultado?.productos ?? [];
  let activos = 0;
  for (const producto of productos) {
    if (producto.activo) activos += 1;
  }

  const mostrarAviso = (mensaje: string) => {
    setAviso(mensaje);
    window.setTimeout(() => setAviso(null), 3500);
  };

  const handleGuardado = (producto: Producto) => {
    const eraEdicion = modal?.tipo === 'formulario' && modal.producto !== null;
    setModal(null);
    setVersion((v) => v + 1);
    mostrarAviso(eraEdicion ? `${producto.nombre} actualizado.` : `${producto.nombre} agregado al catálogo.`);
  };

  const handleConfirmarEstado = async () => {
    if (modal?.tipo !== 'estado') return;
    setProcesandoEstado(true);
    try {
      const actualizado = await productoService.alternarActivo(modal.producto.id_producto);
      setModal(null);
      setVersion((v) => v + 1);
      mostrarAviso(`${actualizado.nombre} ${actualizado.activo ? 'activado' : 'inactivado'}.`);
    } catch {
      setModal(null);
      mostrarAviso('No se pudo cambiar el estado del producto.');
    } finally {
      setProcesandoEstado(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Encabezado General del Módulo */}
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
          Productos e Inventario · {pestanaActiva === 'catalogo' ? 'CU5' : 'CU10 & CU11'}
        </p>
        <div className="mt-1 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              {pestanaActiva === 'catalogo' ? 'Catálogo de productos' : 'Producción diaria'}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {pestanaActiva === 'catalogo'
                ? 'Panes que elabora la panadería, con su costo, margen y precio de venta.'
                : 'Registro de horneado diario, cálculo MRP de recetas y consumo automático de insumos.'}
            </p>
          </div>

          {pestanaActiva === 'catalogo' && puedeGestionar && (
            <button
              type="button"
              onClick={() => setModal({ tipo: 'formulario', producto: null })}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-amber-600/20 hover:from-amber-700 hover:to-amber-800 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              Nuevo producto
            </button>
          )}
        </div>

        {/* Selector de pestañas */}
        <div
          role="tablist"
          aria-label="Secciones de productos e inventario"
          className="flex border-b border-slate-200 mt-5 gap-6"
        >
          <button
            type="button"
            role="tab"
            aria-selected={pestanaActiva === 'catalogo'}
            onClick={() => cambiarPestana('catalogo')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
              pestanaActiva === 'catalogo'
                ? 'border-amber-600 text-amber-900'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <Package className="h-4 w-4" />
            <span>Catálogo de panes</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={pestanaActiva === 'produccion'}
            onClick={() => cambiarPestana('produccion')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
              pestanaActiva === 'produccion'
                ? 'border-amber-600 text-amber-900'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <Wheat className="h-4 w-4" />
            <span>Producción diaria</span>
          </button>
        </div>
      </div>

      {/* Contenido según pestaña activa */}
      {pestanaActiva === 'produccion' ? (
        <ProduccionTab />
      ) : (
        <>
          {aviso && (
            <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              {aviso}
            </div>
          )}

          {!puedeGestionar && (
            <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500">
              Tu rol puede consultar el catálogo. Crear o modificar productos requiere el permiso{' '}
              <code className="rounded bg-slate-100 px-1 py-0.5 text-slate-700">gestionar_productos</code>.
            </div>
          )}

      <section className="rounded-2xl border border-slate-200 bg-white">
        <div className="flex flex-col gap-3 border-b border-slate-100 p-4 md:flex-row">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 w-4 h-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por nombre..."
              aria-label="Buscar producto por nombre"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder-slate-400 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <select
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
            aria-label="Filtrar por categoría"
            className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500 md:w-56"
          >
            <option value="">Todas las categorías</option>
            {categorias.map((c) => (
              <option key={c.id_categoria} value={c.id_categoria}>
                {c.nombre}
              </option>
            ))}
          </select>
          <select
            value={estado}
            onChange={(e) => setEstado(e.target.value as EstadoFiltro)}
            aria-label="Filtrar por estado"
            className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500 md:w-44"
          >
            <option value="">Todos los estados</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
        </div>

        {resultado?.error ? (
          <div className="m-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <AlertCircle className="w-5 h-5 shrink-0" />
            {resultado.error}
          </div>
        ) : (
          <div className={`overflow-x-auto transition-opacity ${cargando ? 'opacity-60' : ''}`}>
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">Producto</th>
                  <th className="px-4 py-3">Categoría</th>
                  <th className="px-4 py-3 text-right">Costo</th>
                  <th className="px-4 py-3 text-right">Ganancia</th>
                  <th className="px-4 py-3 text-right">Sugerido</th>
                  <th className="px-4 py-3 text-right">Venta</th>
                  <th className="px-4 py-3">Estado</th>
                  {puedeGestionar && <th className="px-4 py-3 text-right">Acciones</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {productos.map((producto) => (
                  <tr key={producto.id_producto} className={producto.activo ? '' : 'bg-slate-50/60 text-slate-400'}>
                    <td className="px-4 py-3">
                      <p className={`font-semibold ${producto.activo ? 'text-slate-900' : 'text-slate-500'}`}>
                        {producto.nombre}
                      </p>
                      {producto.descripcion && (
                        <p className="max-w-xs truncate text-xs text-slate-400">{producto.descripcion}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{producto.categoria_nombre ?? 'Sin categoría'}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatearBs(producto.costo_produccion)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{Number(producto.porcentaje_ganancia)} %</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatearBs(producto.precio_sugerido)}</td>
                    <td className="px-4 py-3 text-right font-semibold tabular-nums text-amber-800">
                      {formatearBs(producto.precio_venta)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                          producto.activo ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${producto.activo ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                        {producto.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    {puedeGestionar && (
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-1">
                          <button
                            type="button"
                            onClick={() => setModal({ tipo: 'formulario', producto })}
                            title="Editar"
                            aria-label={`Editar ${producto.nombre}`}
                            className="rounded-lg p-2 text-slate-500 hover:bg-amber-50 hover:text-amber-700 cursor-pointer"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setModal({ tipo: 'estado', producto })}
                            title={producto.activo ? 'Inactivar' : 'Activar'}
                            aria-label={`${producto.activo ? 'Inactivar' : 'Activar'} ${producto.nombre}`}
                            className={`rounded-lg p-2 cursor-pointer ${
                              producto.activo
                                ? 'text-slate-500 hover:bg-red-50 hover:text-red-600'
                                : 'text-slate-400 hover:bg-emerald-50 hover:text-emerald-600'
                            }`}
                          >
                            <Power className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}

                {!cargando && productos.length === 0 && (
                  <tr>
                    <td colSpan={puedeGestionar ? 8 : 7} className="px-4 py-12 text-center">
                      <Package className="mx-auto mb-2 w-8 h-8 text-slate-300" />
                      <p className="text-sm font-medium text-slate-500">No hay productos con esos filtros.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="border-t border-slate-100 px-4 py-3 text-xs text-slate-500">
          {cargando && !resultado
            ? 'Cargando catálogo...'
            : `Mostrando ${productos.length} productos · ${activos} activos · ${productos.length - activos} inactivos`}
        </div>
      </section>
        </>
      )}

      {modal?.tipo === 'formulario' && (
        <ProductoFormModal
          producto={modal.producto}
          categorias={categorias}
          onClose={() => setModal(null)}
          onSaved={handleGuardado}
        />
      )}

      {modal?.tipo === 'estado' && (
        <ConfirmarEstadoDialog
          producto={modal.producto}
          procesando={procesandoEstado}
          onCancel={() => setModal(null)}
          onConfirm={handleConfirmarEstado}
        />
      )}
    </div>
  );
};

export default ProductosPage;
