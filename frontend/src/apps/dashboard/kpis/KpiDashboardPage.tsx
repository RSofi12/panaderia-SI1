import React, { useEffect, useState, useTransition } from 'react';
import {
  Gauge,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import {
  kpiDashboardService,
  type OwnerKpiSummary,
  type AdminKpiSummary,
} from '../../../services/kpiDashboardService';
import type { PeriodoReporte } from '../../../services/reporteVentasService';
import OwnerDashboardView from './OwnerDashboardView';
import AdminDashboardView from './AdminDashboardView';

export const KpiDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [periodo, setPeriodo] = useState<PeriodoReporte>('mes');
  const [vistaActiva, setVistaActiva] = useState<'propietario' | 'admin'>('propietario');
  const [cargando, setCargando] = useState<boolean>(true);
  const [ownerData, setOwnerData] = useState<OwnerKpiSummary | null>(null);
  const [adminData, setAdminData] = useState<AdminKpiSummary | null>(null);
  const [isPending, startTransition] = useTransition();

  const esAdmin = user?.rol?.toLowerCase().includes('admin') || user?.rol?.toLowerCase().includes('administrador');
  const esPropietario = user?.rol?.toLowerCase().includes('propietario') || user?.rol?.toLowerCase().includes('dueño');

  useEffect(() => {
    // Si es admin exclusivo, arrancar con vista admin
    if (esAdmin && !esPropietario) {
      setVistaActiva('admin');
    } else {
      setVistaActiva('propietario');
    }
  }, [esAdmin, esPropietario]);

  const cargarDatos = async (p = periodo) => {
    setCargando(true);
    try {
      const [ownerRes, adminRes] = await Promise.all([
        kpiDashboardService.obtenerResumenPropietario(p).catch(() => null),
        kpiDashboardService.obtenerResumenAdmin().catch(() => null),
      ]);
      setOwnerData(ownerRes);
      setAdminData(adminRes);
    } catch (err) {
      console.error('Error al cargar KPIs del dashboard:', err);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarDatos(periodo);
  }, [periodo]);

  const cambiarPeriodo = (nuevoPeriodo: PeriodoReporte) => {
    startTransition(() => {
      setPeriodo(nuevoPeriodo);
    });
  };

  return (
    <div className="mostrador-aparecer mx-auto max-w-6xl space-y-6">
      {/* HEADER DEL DASHBOARD CON CONTROLES */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-100 text-amber-800">
              <Gauge className="h-4 w-4" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-amber-800">
              Control y Resultados
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
            Tablero de Indicadores y KPIs
          </h1>
          <p className="mt-0.5 text-xs text-slate-500">
            Métricas estratégicas para la toma de decisiones en Panadería Santiago.
          </p>
        </div>

        {/* CONTROLES Y FILTROS */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Selector de Perspectiva (si tiene acceso a ambas) */}
          {(esAdmin || esPropietario) && (
            <div className="flex items-center rounded-xl bg-slate-100 p-1 text-xs font-semibold text-slate-600">
              <button
                type="button"
                onClick={() => setVistaActiva('propietario')}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all ${
                  vistaActiva === 'propietario'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <TrendingUp className="h-3.5 w-3.5" />
                Negocio
              </button>
              <button
                type="button"
                onClick={() => setVistaActiva('admin')}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all ${
                  vistaActiva === 'admin'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <ShieldCheck className="h-3.5 w-3.5" />
                Seguridad
              </button>
            </div>
          )}

          {/* Selector de Rango de Fechas (Para vista de negocio) */}
          {vistaActiva === 'propietario' && (
            <div className="flex items-center rounded-xl border border-slate-200 bg-white p-1 text-xs font-medium shadow-xs">
              {(['dia', 'semana', 'mes'] as PeriodoReporte[]).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => cambiarPeriodo(p)}
                  className={`rounded-lg px-3 py-1.5 transition-colors ${
                    periodo === p
                      ? 'bg-amber-600 font-bold text-white shadow-2xs'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {p === 'dia' ? 'Hoy' : p === 'semana' ? 'Esta semana' : 'Este mes'}
                </button>
              ))}
            </div>
          )}

          {/* Botón Refrescar */}
          <button
            type="button"
            onClick={() => cargarDatos()}
            disabled={cargando}
            aria-label="Actualizar datos"
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-xs hover:bg-slate-50 hover:text-slate-900 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${cargando ? 'animate-spin text-amber-700' : ''}`} />
          </button>
        </div>
      </div>

      {/* CONTENIDO DEL DASHBOARD CON TRANSICIONES */}
      <div className={`transition-all duration-300 ease-in-out ${cargando || isPending ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
        {vistaActiva === 'propietario' && ownerData && (
          <OwnerDashboardView data={ownerData} />
        )}

        {vistaActiva === 'admin' && adminData && (
          <AdminDashboardView data={adminData} />
        )}
      </div>
    </div>
  );
};

export default KpiDashboardPage;
