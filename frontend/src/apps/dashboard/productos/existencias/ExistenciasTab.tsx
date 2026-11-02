import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Boxes,
  CheckCircle2,
  History,
  Layers,
  RefreshCw,
  Search,
  Sparkles,
  TrendingDown,
  XCircle,
  AlertOctagon,
} from 'lucide-react';
import type {
  DetalleKardexProducto,
  ExistenciaProducto,
  FiltrosExistencias,
  NivelStock,
  ResumenExistencias,
  NotaPerdida,
} from '../../../../types/existencias';
import { existenciasService } from '../../../../services/existenciasService';
import { productoService } from '../../../../services/productoService';
import { useAuth } from '../../../../contexts/AuthContext';
import { KardexProductoModal } from './components/KardexProductoModal';
import { RegistrarBajaModal } from './components/RegistrarBajaModal';
import { HistorialMermasModal } from './components/HistorialMermasModal';
import type { CategoriaProducto } from '../../../../types/producto';

export const ExistenciasTab: React.FC = () => {
  const { hasPermission } = useAuth();
  const puedeRegistrarBaja =
    hasPermission('gestionar_inventario') ||
    hasPermission('registrar_produccion') ||
    hasPermission('gestionar_productos');

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

  // Modales y estados para CU18 (Registrar Baja / Merma)
  const [modalBajaAbierto, setModalBajaAbierto] = useState(false);
  const [modalHistorialAbierto, setModalHistorialAbierto] = useState(false);
  const [productoParaBaja, setProductoParaBaja] = useState<ExistenciaProducto | null>(null);
  const [mensajeExito, setMensajeExito] = useState<string | null>(null);

  // Cargar categorías al inicio
  useEffect(() => {
    let activo = true;
    productoService
      .listarCategorias()
      .then((cats) => {
        if (activo) setCategorias(cats);
      })
      .catch(() => {
        // Ignora si falla la carga de categorías
      });
    return () => {
      activo = false;
    };
  }, []);

  // Cargar existencias y resumen con filtros reactivos
  useEffect(() => {
    let activo = true;
    const cargarDatos = async () => {
      try {
        const filtros: FiltrosExistencias = {
          q: busqueda.trim() || undefined,
          categoria: categoriaSeleccionada || undefined,
          estado_stock: estadoStockSeleccionado || undefined,
          ordenar_por: ordenSeleccionado,
          solo_activos: true,
        };

        const [items, stats] = await Promise.all([
          existenciasService.listar(filtros),
          existenciasService.obtenerResumen(),
        ]);

        if (activo) {
          setExistencias(items);
          setResumen(stats);
          setCargando(false);
        }
      } catch {
        if (activo) setCargando(false);
      }
    };

    cargarDatos();
    return () => {
      activo = false;
    };
  }, [busqueda, categoriaSeleccionada, estadoStockSeleccionado, ordenSeleccionado]);

  // Recargar manual
  const handleRecargarManual = async () => {
    setRecargando(true);
    try {
      const filtros: FiltrosExistencias = {
        q: busqueda.trim() || undefined,
        categoria: categoriaSeleccionada || undefined,
        estado_stock: estadoStockSeleccionado || undefined,
        ordenar_por: ordenSeleccionado,
        solo_activos: true,
      };
      const [items, stats] = await Promise.all([
        existenciasService.listar(filtros),
        existenciasService.obtenerResumen(),
      ]);
      setExistencias(items);
      setResumen(stats);
    } finally {
      setRecargando(false);
    }
  };

  // Abrir modal de Kardex
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

  // Cerrar modal de Kardex
  const handleCerrarKardex = () => {
    setProductoKardexSeleccionado(null);
    setDetalleKardex(null);
  };

  // Abrir modal de baja de producto (CU18)
  const handleAbrirBaja = (producto?: ExistenciaProducto) => {
    setProductoParaBaja(producto || null);
    setModalBajaAbierto(true);
  };

  // Handler tras completar baja exitosamente
  const handleBajaRegistrada = (nota: NotaPerdida) => {
    setMensajeExito(
      `Baja registrada exitosamente: ${nota.cantidad} un. de "${nota.producto_nombre}" (Pérdida calculada: Bs. ${Number(
        nota.costo_total
      ).toFixed(2)})`
    );
    setTimeout(() => setMensajeExito(null), 5000);
    handleRecargarManual();
  };

  // Limpiar filtros activos
  const hayFiltrosActivos =
    busqueda !== '' || categoriaSeleccionada !== '' || estadoStockSeleccionado !== '';
  const limpiarFiltros = () => {
    setBusqueda('');
    setCategoriaSeleccionada('');
    setEstadoStockSeleccionado('');
    setOrdenSeleccionado('nombre_asc');
  };

  return (
    <div className="space-y-6">
      {/* Notificación Toast de Éxito para CU18 */}
      {mensajeExito && (
        <div className="flex items-center justify-between p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-medium animate-in fade-in">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
            <span>{mensajeExito}</span>
          </div>
          <button
            type="button"
            onClick={() => setMensajeExito(null)}
            className="text-emerald-700 hover:text-emerald-900 text-xs font-bold underline cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      )}

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

        {/* KPI 2: Unidades totales disponibles */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total unidades listas
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
              <Sparkles className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              {resumen?.total_unidades_stock ?? 0}
            </span>
            <span className="text-xs text-slate-500">unidades</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Listos para despacho o venta</p>
        </div>

        {/* KPI 3: Panes en estado crítico o agotados */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Bajo stock o agotado
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-50 text-rose-700">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              {(resumen?.productos_stock_critico ?? 0) + (resumen?.productos_agotados ?? 0)}
            </span>
            <span className="text-xs text-slate-500">requieren horneado</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {resumen?.productos_agotados ?? 0} agotados / {resumen?.productos_stock_critico ?? 0} críticos
          </p>
        </div>

        {/* KPI 4: Valorización total de vitrina */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Valorización en vitrina
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
              <Layers className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Bs. {Number(resumen?.valor_total_inventario ?? 0).toFixed(2)}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Precio estimado a venta</p>
        </div>
      </div>

      {/* 2. Barra de Herramientas y Filtros (CU12 + Acciones CU18) */}
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs md:flex-row md:items-center md:justify-between">
        {/* Buscador de texto */}
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar por tipo de pan o descripción..."
            className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2 pl-10 pr-4 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:border-amber-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 transition-all"
          />
        </div>

        {/* Filtros desplegables y botones */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Selector de Categoría */}
          <select
            value={categoriaSeleccionada}
            onChange={(e) => setCategoriaSeleccionada(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white py-2 px-3 text-xs sm:text-sm text-slate-700 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
          >
            <option value="">Todas las categorías</option>
            {categorias.map((cat) => (
              <option key={cat.id_categoria} value={cat.id_categoria}>
                {cat.nombre}
              </option>
            ))}
          </select>

          {/* Selector de Nivel de Stock */}
          <select
            value={estadoStockSeleccionado}
            onChange={(e) => setEstadoStockSeleccionado(e.target.value as '' | NivelStock)}
            className="rounded-xl border border-slate-200 bg-white py-2 px-3 text-xs sm:text-sm text-slate-700 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
          >
            <option value="">Todos los estados</option>
            <option value="disponible">Disponible (&gt; 20 un)</option>
            <option value="critico">Bajo stock (1 a 20 un)</option>
            <option value="agotado">Agotado (0 un)</option>
          </select>

          {/* Selector de Ordenamiento */}
          <select
            value={ordenSeleccionado}
            onChange={(e) =>
              setOrdenSeleccionado(e.target.value as FiltrosExistencias['ordenar_por'])
            }
            className="rounded-xl border border-slate-200 bg-white py-2 px-3 text-xs sm:text-sm text-slate-700 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
          >
            <option value="nombre_asc">Nombre: A-Z</option>
            <option value="nombre_desc">Nombre: Z-A</option>
            <option value="stock_desc">Mayor stock</option>
            <option value="stock_asc">Menor stock</option>
            <option value="precio_desc">Mayor precio</option>
            <option value="precio_asc">Menor precio</option>
          </select>

          {/* Botón para refrescar */}
          <button
            type="button"
            onClick={handleRecargarManual}
            disabled={recargando}
            title="Actualizar existencias"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors cursor-pointer"
          >
            <RefreshCw className={`h-4 w-4 ${recargando ? 'animate-spin text-amber-600' : ''}`} />
          </button>

          {/* Botón Historial de Bajas (CU18) */}
          <button
            type="button"
            onClick={() => setModalHistorialAbierto(true)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs sm:text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer shadow-2xs"
            title="Ver auditoría y reporte histórico de mermas"
          >
            <History className="h-4 w-4 text-slate-500" />
            <span>Historial Bajas</span>
          </button>

          {/* Botón Registrar Baja (CU18) */}
          {puedeRegistrarBaja && (
            <button
              type="button"
              onClick={() => handleAbrirBaja()}
              className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-3.5 py-2 text-xs sm:text-sm font-semibold text-white hover:bg-rose-700 shadow-sm transition-all cursor-pointer"
              title="Registrar merma o descarte de panes"
            >
              <AlertOctagon className="h-4 w-4" />
              <span>Registrar Baja</span>
            </button>
          )}

          {/* Limpiar filtros si hay activos */}
          {hayFiltrosActivos && (
            <button
              type="button"
              onClick={limpiarFiltros}
              className="text-xs text-amber-600 hover:text-amber-800 font-medium underline px-1 cursor-pointer"
            >
              Restablecer
            </button>
          )}
        </div>
      </div>

      {/* 3. Tabla Principal de Existencias */}
      <div className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        {cargando ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <RefreshCw className="h-8 w-8 animate-spin text-amber-600 mb-2" />
            <p className="text-xs sm:text-sm font-medium">Consultando existencias en vitrina...</p>
          </div>
        ) : existencias.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center px-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-600 mb-3">
              <Boxes className="h-6 w-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">
              No se encontraron productos en vitrina
            </h3>
            <p className="mt-1 text-xs sm:text-sm text-slate-500 max-w-sm">
              No hay productos terminados que coincidan con los filtros seleccionados o el catálogo
              está vacío.
            </p>
            {hayFiltrosActivos && (
              <button
                type="button"
                onClick={limpiarFiltros}
                className="mt-4 inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
              >
                Limpiar filtros
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

                      {/* Nivel de existencias con barra visual */}
                      <td className="py-3.5 px-4">
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-slate-900 tabular-nums">
                              {stock} unidades
                            </span>
                            <span className="text-[11px] text-slate-400">Capacidad ref. 150</span>
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

                      {/* Badge de Estado */}
                      <td className="py-3.5 px-4 text-center">
                        {item.estado_stock === 'disponible' ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                            Disponible
                          </span>
                        ) : item.estado_stock === 'critico' ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                            <TrendingDown className="h-3 w-3 text-amber-600" />
                            Bajo stock
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

                      {/* Acciones: Ver Kardex y Dar de Baja (CU18) */}
                      <td className="py-3.5 px-4 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleVerKardex(item.id_producto)}
                            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-900 transition-all cursor-pointer shadow-2xs"
                            title={`Ver historial de movimientos de ${item.producto_nombre}`}
                          >
                            <History className="h-3.5 w-3.5 text-amber-600" />
                            <span>Kardex</span>
                          </button>

                          {puedeRegistrarBaja && item.stock_actual > 0 && (
                            <button
                              type="button"
                              onClick={() => handleAbrirBaja(item)}
                              className="inline-flex items-center gap-1 rounded-xl border border-rose-200 bg-rose-50/60 px-2.5 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 hover:text-rose-900 transition-all cursor-pointer shadow-2xs"
                              title={`Registrar baja por merma de ${item.producto_nombre}`}
                            >
                              <AlertOctagon className="h-3.5 w-3.5 text-rose-600" />
                              <span>Baja</span>
                            </button>
                          )}
                        </div>
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

      {/* 5. Modal de Registro de Baja / Merma (CU18) */}
      {modalBajaAbierto && (
        <RegistrarBajaModal
          existencias={existencias}
          productoInicial={productoParaBaja}
          onClose={() => {
            setModalBajaAbierto(false);
            setProductoParaBaja(null);
          }}
          onBajaRegistrada={handleBajaRegistrada}
        />
      )}

      {/* 6. Modal de Historial de Mermas (CU18) */}
      {modalHistorialAbierto && (
        <HistorialMermasModal onClose={() => setModalHistorialAbierto(false)} />
      )}
    </div>
  );
};

export default ExistenciasTab;