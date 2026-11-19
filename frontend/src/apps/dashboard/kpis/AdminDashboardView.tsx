import React from 'react';
import {
  Users,
  ShieldAlert,
  Activity,
  UserCheck,
  Shield,
  ArrowUpRight,
  Clock,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import type { AdminKpiSummary } from '../../../services/kpiDashboardService';
import KpiCard from './components/KpiCard';

interface AdminDashboardViewProps {
  data: AdminKpiSummary;
}

export const AdminDashboardView: React.FC<AdminDashboardViewProps> = ({ data }) => {
  return (
    <div className="space-y-6 transition-opacity duration-300 ease-out">
      {/* 1. SECCIÓN DE HEADLINE KPIS (Gobernanza y Auditoría) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          titulo="Usuarios Habilitados"
          valor={data.usuariosActivos}
          subtexto={`De un total de ${data.totalUsuarios} registrados`}
          icono={Users}
          variante="amber"
          tendencia={{
            valor: `${data.usuariosInactivos} inactivos`,
            esNeutra: true,
          }}
        />

        <KpiCard
          titulo="Actividad Auditada Hoy"
          valor={data.eventosHoy}
          subtexto="Eventos en bitácora general"
          icono={Activity}
          variante="emerald"
          tendencia={{
            valor: 'Registro activo CU26',
            esPositiva: true,
          }}
        />

        <KpiCard
          titulo="Alertas de Seguridad"
          valor={data.intentosFallidosOSeguridad}
          subtexto="Accesos o cambios sensibles"
          icono={ShieldAlert}
          variante={data.intentosFallidosOSeguridad > 0 ? 'rose' : 'emerald'}
          tendencia={{
            valor: data.intentosFallidosOSeguridad > 0 ? 'Verificar auditoría' : 'Sin anomalías',
            esPositiva: data.intentosFallidosOSeguridad === 0,
          }}
        />

        <KpiCard
          titulo="Roles Configurables"
          valor={data.distribucionRoles.length}
          subtexto="Control RBAC activo"
          icono={Shield}
          variante="indigo"
          tendencia={{
            valor: 'CU04 Asignar roles',
            esNeutra: true,
          }}
        />
      </div>

      {/* 2. ESTRUCTURA: DISTRIBUCIÓN DE USUARIOS Y BITÁCORA EN VIVO */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Distribución por Roles */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-base font-bold text-slate-900">Distribución por Rol</h3>
            <Link
              to="/dashboard/usuarios"
              className="text-xs font-semibold text-amber-700 hover:text-amber-800 transition-colors"
            >
              Gestionar
            </Link>
          </div>

          <div className="space-y-3">
            {data.distribucionRoles.map((item: { rol: string; total: number }) => {
              const porcentaje = data.totalUsuarios > 0 ? Math.round((item.total / data.totalUsuarios) * 100) : 0;
              return (
                <div key={item.rol} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-700">{item.rol}</span>
                    <span className="font-semibold text-slate-900">{item.total} ({porcentaje}%)</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-amber-600 transition-all duration-500 ease-out"
                      style={{ width: `${porcentaje}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6 rounded-xl border border-slate-100 bg-slate-50 p-3.5 text-xs text-slate-600">
            <p className="flex items-center gap-1.5 font-semibold text-slate-800">
              <UserCheck className="h-4 w-4 text-emerald-600" />
              Política de mínimos privilegios:
            </p>
            <p className="mt-1 text-[11px] text-slate-500">
              Cada usuario accede exclusivamente a los módulos explícitamente autorizados mediante la matriz de permisos.
            </p>
          </div>
        </div>

        {/* Últimas acciones en bitácora */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs lg:col-span-2">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-base font-bold text-slate-900">Actividad Reciente del Sistema (Bitácora)</h3>
              <p className="text-xs text-slate-500">Trazabilidad en tiempo real de operaciones críticas (CU26)</p>
            </div>
            <Link
              to="/dashboard/usuarios"
              className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 hover:text-amber-800 transition-colors"
            >
              Abrir bitácora completa
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {data.ultimosEventosBitacora.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No se han registrado eventos recientes.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {data.ultimosEventosBitacora.map((ev: { id: number; usuario: string; accion: string; modulo: string; fecha: string; descripcion: string }) => (
                <div key={ev.id} className="flex items-start justify-between py-2.5 text-xs">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900">{ev.usuario}</span>
                      <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
                        {ev.modulo}
                      </span>
                    </div>
                    <p className="text-slate-600">{ev.accion}: {ev.descripcion || 'Sin detalle adicional'}</p>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] text-slate-400 shrink-0">
                    <Clock className="h-3 w-3" />
                    <span>{ev.fecha ? new Date(ev.fecha).toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' }) : ''}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardView;
