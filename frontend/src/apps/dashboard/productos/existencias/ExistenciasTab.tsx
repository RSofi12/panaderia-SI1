import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Boxes,
  CheckCircle2,
  Coins,
  History,
  RefreshCw,
  Search,
  Store,
  XCircle,
} from 'lucide-react';
import existenciasService from '../../../../services/existenciasService';
import productoService from '../../../../services/productoService';
import type {
  DetalleKardexProducto,
  ExistenciaProducto,
  FiltrosExistencias,
  NivelStock,
  ResumenExistencias,
} from '../../../../types/existencias';
import type { CategoriaProducto } from '../../../../types/producto';
import KardexProductoModal from './components/KardexProductoModal';

export const ExistenciasTab: React.FC = () => {
  // Estados de datos
  const [existencias, setExistencias] = useState<ExistenciaProducto[]>([]);
  const [resumen, setResumen] = useState<ResumenExistencias | null>(null);
  const [categorias, setCategorias] = useState<CategoriaProducto[]>([]);
  const [cargando, setCargando] = useState(true);
  const [recargando, setRecargando] = useState(false);

  // Filtros de búsqueda
  const [busqueda, setBusqueda] = useState('');
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState('');
  const [estadoStockSeleccionado, setEstadoStockSeleccionado] = useState<'' | NivelStock>('');
  const [ordenSeleccionado, setOrdenSeleccionado] = useState<FiltrosExistencias['ordenar_por']>('nombre_asc');

  // Modal de Kardex
  const [productoKardexSeleccionado, setProductoKardexSeleccionado] = useState<number | null>(null);
  const [detalleKardex, setDetalleKardex] = useState<DetalleKardexProducto | null>(null);
  const [cargandoKardex, setCargandoKardex] = useState(false);

  // Cargar categorías al inicio
  useEffect(() => {
    let activo = true;
    productoService.listarCategorias().then((cats) => {
      if (activo) setCategorias(cats);
    }).catch(() => {
      // Ignora si falla la carga de categorías
    });
    return () => { activo = false; };
  }, []);

  // Efecto reactivo ante cambios en filtros de búsqueda y orden
  useEffect(() => {
    let activo = true;

    existenciasService
      .listar({
        q: busqueda.trim() || undefined,
        categoria: categoriaSeleccionada || undefined,
        estado_stock: estadoStockSeleccionado || undefined,
        ordenar_por: ordenSeleccionado,
      })
      .then((dataExistencias) => {
        if (activo) {
          setExistencias(dataExistencias);
          setCargando(false);
          setRecargando(false);
        }
      })
      .catch(() => {
        if (activo) {
          setCargando(false);
          setRecargando(false);
        }
      });

    existenciasService
      .obtenerResumen()
      .then((dataResumen) => {
        if (activo) setResumen(dataResumen);
      })
      .catch(() => {
        // Fallback manejado
      });

    return () => {
      activo = false;
    };
  }, [busqueda, categoriaSeleccionada, estadoStockSeleccionado, ordenSeleccionado]);

  // Recarga manual forzada por el usuario
  const handleRecargarManual = () => {
    setRecargando(true);
    Promise.all([
      existenciasService.listar({
        q: busqueda.trim() || undefined,
        categoria: categoriaSeleccionada || undefined,
        estado_stock: estadoStockSeleccionado || undefined,
        ordenar_por: ordenSeleccionado,
      }),
      existenciasService.obtenerResumen(),
    ])
      .then(([dataExistencias, dataResumen]) => {
        setExistencias(dataExistencias);
        setResumen(dataResumen);
      })
      .finally(() => {
        setRecargando(false);
      });
  };

  // Manejador para abrir el Kardex de un producto
  const handleVerKardex = async (idProducto: number) => {
    setProductoKardexSeleccionado(idProducto);
    setCargandoKardex(true);
    try {
      const data = await existenciasService.obtenerKardex(idProducto);
      setDetalleKardex(data);
    } catch {
      setDetalleKardex(null);
    } finally {
      setCargandoKardex(false);
    }
  };

  const handleCerrarKardex = () => {
    setProductoKardexSeleccionado(null);
    setDetalleKardex(null);
  };

  // Limpiar filtros activos
  const hayFiltrosActivos = busqueda !== '' || categoriaSeleccionada !== '' || estadoStockSeleccionado !== '';
  const limpiarFiltros = () => {
    setBusqueda('');
    setCategoriaSeleccionada('');
    setEstadoStockSeleccionado('');
    setOrdenSeleccionado('nombre_asc');
  };

  return (
    <div className="space-y-6">
      {/* 1. Tarjetas de Métricas / KPIs Resumen (CU12) */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        {/* KPI 1: Variedad de panes */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Variedad en vitrina
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-700">
              <Boxes className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              {resumen?.total_panes_distintos ?? 0}
            </span>
            <span className="text-xs text-slate-500">tipos de pan</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Catálogo activo horneado</p>
        </div>

        {/* KPI 2: Total unidades disponibles */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Stock total listo
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
              <Store className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-emerald-700">
              {resumen?.total_unidades_stock ?? 0}
            </span>
            <span className="text-xs text-slate-500">unidades</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Listas para despacho en mostrador</p>
        </div>

        {/* KPI 3: Valor monetario estimado en Bs. */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Valor en mostrador
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
              <Coins className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Bs. {resumen?.valor_total_inventario ?? '0.00'}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Valorización a precio de venta</p>
        </div>

        {/* KPI 4: Estado crítico o agotado */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Atención / Alertas
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-50 text-rose-700">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-rose-700">
              {(resumen?.productos_stock_critico ?? 0) + (resumen?.productos_agotados ?? 0)}
            </span>
            <span className="text-xs text-slate-500">panes críticos/0</span>
          </div>
          <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
            <span className="text-amber-700 font-medium">{resumen?.productos_stock_critico ?? 0} bajos</span>
            <span>·</span>
            <span className="text-rose-700 font-medium">{resumen?.productos_agotados ?? 0} agotados</span>
          </div>
        </div>
      </div>

      {/* 2. Barra de Filtros y Búsqueda */}
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs sm:flex-row sm:items-center sm:justify-between">
        {/* Buscador de texto */}
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar por nombre de pan (marraqueta, dulce, chama...)..."
            className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2 pl-10 pr-4 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:border-amber-600 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-amber-600/20"
          />
        </div>

        {/* Controles secundarios */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Selector de Categoría */}
          <select
            value={categoriaSeleccionada}
            onChange={(e) => setCategoriaSeleccionada(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs sm:text-sm font-medium text-slate-700 focus:border-amber-600 focus:outline-hidden"
          >
            <option value="">Todas las categorías</option>
            {categorias.map((cat) => (
              <option key={cat.id_categoria} value={cat.id_categoria}>
                {cat.nombre}
              </option>
            ))}
          </select>

          {/* Selector de Estado de Stock */}
          <select
            value={estadoStockSeleccionado}
            onChange={(e) => setEstadoStockSeleccionado(e.target.value as '' | NivelStock)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs sm:text-sm font-medium text-slate-700 focus:border-amber-600 focus:outline-hidden"
          >
            <option value="">Cualquier stock</option>
            <option value="disponible">Normal (&gt; 20 un)</option>
            <option value="critico">Bajo (1 a 20 un)</option>
            <option value="agotado">Agotado (0 un)</option>
          </select>

          {/* Selector de Orden */}
          <select
            value={ordenSeleccionado}
            onChange={(e) => setOrdenSeleccionado(e.target.value as FiltrosExistencias['ordenar_por'])}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs sm:text-sm font-medium text-slate-700 focus:border-amber-600 focus:outline-hidden"
          >
            <option value="nombre_asc">Nombre: A - Z</option>
            <option value="nombre_desc">Nombre: Z - A</option>
            <option value="stock_desc">Mayor stock</option>
            <option value="stock_asc">Menor stock</option>
            <option value="precio_desc">Mayor precio</option>
            <option value="precio_asc">Menor precio</option>
          </select>

          {/* Botón Refrescar */}
          <button
            type="button"
            onClick={handleRecargarManual}
            disabled={recargando}
            title="Actualizar existencias"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors cursor-pointer"
          >
            <RefreshCw className={`h-4 w-4 ${recargando ? 'animate-spin text-amber-600' : ''}`} />
          </button>

          {/* Limpiar filtros si hay alguno activo */}
          {hayFiltrosActivos && (
            <button
              type="button"
              onClick={limpiarFiltros}
              className="text-xs font-semibold text-amber-800 hover:text-amber-950 px-2 py-1 cursor-pointer"
            >
              Limpiar filtros
            </button>
          )}
        </div>
      </div>

      {/* 3. Tabla Principal de Existencias */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
        {cargando ? (
          <div className="space-y-4 p-8">
            <div className="flex items-center justify-center gap-3 text-slate-400">
              <div className="h-6 w-6 animate-spin rounded-full border-3 border-amber-600 border-t-transparent" />
              <span className="text-sm">Consultando existencias de productos terminados en mostrador...</span>
            </div>
          </div>
        ) : existencias.length === 0 ? (
          <div className="p-12 text-center">
            <Store className="mx-auto h-12 w-12 text-slate-300" />
            <h3 className="mt-3 text-base font-bold text-slate-800">No se encontraron productos</h3>
            <p className="mt-1 text-xs sm:text-sm text-slate-500 max-w-sm mx-auto">
              No hay existencias registradas que coincidan con los criterios de búsqueda aplicados.
            </p>
            {hayFiltrosActivos && (
              <button
                type="button"
                onClick={limpiarFiltros}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-amber-50 px-4 py-2 text-xs sm:text-sm font-semibold text-amber-800 hover:bg-amber-100 transition-colors cursor-pointer"
              >
                Limpiar filtros de búsqueda
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs sm:text-sm">
              <thead className="border-b border-slate-200 bg-slate-50/75 text-slate-600 font-semibold">
                <tr>
                  <th className="py-3 px-4">Producto terminado</th>
                  <th className="py-3 px-4">Categoría</th>
                  <th className="py-3 px-4 text-right">Precio unitario</th>
                  <th className="py-3 px-4 min-w-[200px]">Nivel de existencias</th>
                  <th className="py-3 px-4 text-center">Estado</th>
                  <th className="py-3 px-4 text-right">Valor en vitrina</th>
                  <th className="py-3 px-4 text-center">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {existencias.map((item) => {
                  const stock = item.stock_actual;
                  const porcentajeVisual = Math.min(100, Math.round((stock / 150) * 100));

                  return (
                    <tr key={item.id_inventario} className="hover:bg-slate-50/60 transition-colors">
                      {/* Producto */}
                      <td className="py-3.5 px-4 font-medium text-slate-900">
                        <div className="flex items-center gap-3">
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-100/70 text-amber-800 font-bold text-xs">
                            {item.producto_nombre.substring(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-semibold text-slate-900">{item.producto_nombre}</p>
                            {item.producto_descripcion && (
                              <p className="text-[11px] text-slate-400 line-clamp-1 max-w-xs">
                                {item.producto_descripcion}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Categoría */}
                      <td className="py-3.5 px-4 text-slate-600">
                        <span className="inline-flex items-center rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                          {item.categoria_nombre}
                        </span>
                      </td>

                      {/* Precio de venta */}
                      <td className="py-3.5 px-4 text-right font-semibold text-slate-900 tabular-nums">
                        Bs. {Number(item.precio_venta).toFixed(2)}
                      </td>

                      {/* Nivel de stock con barra visual */}
                      <td className="py-3.5 px-4">
                        <div className="space-y-1.5">
                          <div className="flex justify-between items-center text-xs">
                            <span className="font-bold text-slate-900 tabular-nums">
                              {stock} unidades
                            </span>
                            <span className="text-[11px] text-slate-400">
                              Cap. ~150 un
                            </span>
                          </div>
                          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                item.estado_stock === 'disponible'
                                  ? 'bg-emerald-500'
                                  : item.estado_stock === 'critico'
                                  ? 'bg-amber-500'
                                  : 'bg-rose-500'
                              }`}
                              style={{ width: `${stock === 0 ? 0 : Math.max(8, porcentajeVisual)}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Estado / Badge de disponibilidad */}
                      <td className="py-3.5 px-4 text-center">
                        {item.estado_stock === 'disponible' ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                            Disponible
                          </span>
                        ) : item.estado_stock === 'critico' ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                            <AlertTriangle className="h-3 w-3 text-amber-600" />
                            Stock bajo
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 border border-rose-200 px-2.5 py-0.5 text-xs font-semibold text-rose-800">
                            <XCircle className="h-3 w-3 text-rose-600" />
                            Agotado
                          </span>
                        )}
                      </td>

                      {/* Valor total en vitrina */}
                      <td className="py-3.5 px-4 text-right font-bold text-slate-900 tabular-nums">
                        Bs. {Number(item.valor_total_stock).toFixed(2)}
                      </td>

                      {/* Acciones: Ver Kardex */}
                      <td className="py-3.5 px-4 text-center">
                        <button
                          type="button"
                          onClick={() => handleVerKardex(item.id_producto)}
                          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-900 transition-all cursor-pointer shadow-2xs"
                          title={`Ver historial de movimientos de ${item.producto_nombre}`}
                        >
                          <History className="h-3.5 w-3.5 text-amber-600" />
                          <span>Kardex</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 4. Modal de Kardex del Producto */}
      {productoKardexSeleccionado !== null && (
        <KardexProductoModal
          kardex={detalleKardex}
          cargando={cargandoKardex}
          onClose={handleCerrarKardex}
        />
      )}
    </div>
  );
};

export default ExistenciasTab;
