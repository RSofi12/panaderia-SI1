import React from 'react';
import {
  ShoppingBag,
  ClipboardList,
  Clock,
  Receipt,
  Store,
  Sparkles,
  TrendingUp,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface CasoUsoCard {
  cu: string;
  titulo: string;
  descripcion: string;
  actores: string;
  icono: React.ElementType;
}

const CASOS_USO: CasoUsoCard[] = [
  {
    cu: 'CU13',
    titulo: 'Registrar venta',
    descripcion:
      'Registro ágil de ventas directas por unidad en mostrador, cálculo de total y descuento automático de inventario terminado.',
    actores: 'Personal de Ventas',
    icono: ShoppingBag,
  },
  {
    cu: 'CU14',
    titulo: 'Registrar pedido',
    descripcion:
      'Recepción y registro de pedidos anticipados de pan y pastelería con fecha de entrega, cliente y anticipo.',
    actores: 'Personal de Ventas',
    icono: ClipboardList,
  },
  {
    cu: 'CU15',
    titulo: 'Consultar estado de pedido',
    descripcion:
      'Seguimiento en tiempo real de pedidos (Pendiente, En elaboración, Listo para entrega, Entregado, Cancelado).',
    actores: 'Personal de Ventas, Personal de Producción',
    icono: Clock,
  },
  {
    cu: 'CU16',
    titulo: 'Generar comprobante de venta',
    descripcion:
      'Emisión e impresión de notas de venta o facturas detallando productos, cantidades, método de pago e importe.',
    actores: 'Personal de Ventas',
    icono: Receipt,
  },
  {
    cu: 'CU17',
    titulo: 'Consultar disponibilidad de productos',
    descripcion:
      'Consulta rápida en pantalla de existencias de panes disponibles para la venta al momento de atender a un cliente.',
    actores: 'Personal de Ventas',
    icono: Store,
  },
];

export const ComercializacionPage: React.FC = () => {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Encabezado General */}
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
          Comercialización · Ciclo 3 (CU13–CU17)
        </p>
        <div className="mt-1 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              <TrendingUp className="h-7 w-7 text-amber-700" />
              Comercialización (Ventas y Pedidos)
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Venta de panes en mostrador, control de pedidos anticipados y emisión de comprobantes.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
            <Sparkles className="h-3.5 w-3.5 text-amber-600" />
            Módulo en Progreso · Ciclo 3
          </span>
        </div>
      </div>

      {/* Banner Informativo */}
      <section className="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50 via-orange-50/50 to-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-700 text-white shadow-md shadow-amber-700/20">
              <ShoppingBag className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Paquete de Comercialización en Desarrollo
              </h3>
              <p className="mt-1 text-sm text-slate-600 leading-relaxed max-w-2xl">
                Este módulo se encuentra planificado según el cronograma del PUDS para el{' '}
                <strong className="text-slate-800">Ciclo 3</strong>. Integrará el flujo de caja diario,
                despacho de pedidos y emisión de comprobantes conectado con las existencias de mostrador (CU12).
              </p>
            </div>
          </div>
          <Link
            to="/dashboard/productos?tab=existencias"
            className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-amber-300 bg-white px-4 py-2.5 text-xs font-semibold text-amber-900 shadow-sm hover:bg-amber-50 transition-colors"
          >
            <span>Ver existencias actuales (CU12)</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </section>

      {/* Casos de Uso Planificados */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            Casos de Uso del Paquete (5 Casos de Uso)
          </h3>
          <span className="text-xs text-slate-500 font-medium">Ciclo 3 PUDS</span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CASOS_USO.map((item) => {
            const Icono = item.icono;
            return (
              <div
                key={item.cu}
                className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-xs transition-shadow hover:shadow-md hover:border-amber-200"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="inline-flex items-center rounded-md bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-900">
                      {item.cu}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500">
                      <AlertCircle className="h-3 w-3 text-amber-600" />
                      Planificado
                    </span>
                  </div>

                  <div className="flex items-center gap-2.5 mb-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-800">
                      <Icono className="h-4 w-4" />
                    </div>
                    <h4 className="text-sm font-bold text-slate-900">{item.titulo}</h4>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed mb-4">{item.descripcion}</p>
                </div>

                <div className="border-t border-slate-100 pt-3">
                  <p className="text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-600">Actor:</span> {item.actores}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};

export default ComercializacionPage;
