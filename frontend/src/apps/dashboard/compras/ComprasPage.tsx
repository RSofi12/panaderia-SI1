import React, { useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { AlertCircle, CheckCircle2, Eye, Plus, ShoppingCart } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import compraService from '../../../services/compraService';
import type { Compra, CompraResumen } from '../../../types/compra';
import RegistrarCompraModal from './components/RegistrarCompraModal';
import DetalleCompraModal from './components/DetalleCompraModal';

type ModalAbierto = { tipo: 'registrar' } | { tipo: 'detalle'; idCompra: number } | null;

interface Resultado {
  version: number;
  compras: CompraResumen[];
  error: string | null;
}

const formatoFechaHora = new Intl.DateTimeFormat('es-BO', { dateStyle: 'medium', timeStyle: 'short' });

export const ComprasPage: React.FC = () => {
  const { hasPermission } = useAuth();
  const puedeRegistrar = hasPermission('registrar_compras');

  const [version, setVersion] = useState(0);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [modal, setModal] = useState<ModalAbierto>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  const cargando = resultado?.version !== version;

  useEffect(() => {
    let vigente = true;
    compraService
      .listar()
      .then((compras) => {
        if (vigente) setResultado({ version, compras, error: null });
      })
      .catch((err: unknown) => {
        if (!vigente) return;
        const sinPermiso = isAxiosError(err) && err.response?.status === 403;
        setResultado({
          version,
          compras: [],
          error: sinPermiso
            ? 'Tu rol no puede consultar las compras.'
            : 'No se pudieron cargar las compras. Verifica que el backend esté en ejecución.',
        });
      });
    return () => {
      vigente = false;
    };
  }, [version]);

  const compras = resultado?.compras ?? [];
  let totalGeneral = 0;
  for (const compra of compras) totalGeneral += Number(compra.total);

  const mostrarAviso = (mensaje: string) => {
    setAviso(mensaje);
    window.setTimeout(() => setAviso(null), 3500);
  };

  const handleRegistrada = (compra: Compra) => {
    setModal(null);
    setVersion((v) => v + 1);
    mostrarAviso(`Compra #${compra.id_compra} registrada a ${compra.proveedor_nombre} por Bs ${compra.total}.`);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
            Compras y Proveedores · CU7
          </p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Compras de materia prima</h2>
          <p className="mt-1 text-sm text-slate-500">
            Cada compra suma stock al inventario y actualiza el último precio del insumo.
          </p>
        </div>
        {puedeRegistrar && (
          <button
            type="button"
            onClick={() => setModal({ tipo: 'registrar' })}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-amber-600/20 hover:from-amber-700 hover:to-amber-800 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Registrar compra
          </button>
        )}
      </div>

      {aviso && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          {aviso}
        </div>
      )}

      <section className="rounded-2xl border border-slate-200 bg-white">
        {resultado?.error ? (
          <div className="m-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <AlertCircle className="w-5 h-5 shrink-0" />
            {resultado.error}
          </div>
        ) : (
          <div className={`overflow-x-auto transition-opacity ${cargando ? 'opacity-60' : ''}`}>
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">N.º</th>
                  <th className="px-4 py-3">Fecha</th>
                  <th className="px-4 py-3">Proveedor</th>
                  <th className="px-4 py-3">Registrado por</th>
                  <th className="px-4 py-3 text-right">Líneas</th>
                  <th className="px-4 py-3 text-right">Total</th>
                  <th className="px-4 py-3 text-right">Detalle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {compras.map((compra) => (
                  <tr key={compra.id_compra}>
                    <td className="px-4 py-3 font-semibold text-slate-900">#{compra.id_compra}</td>
                    <td className="px-4 py-3 text-slate-500">{formatoFechaHora.format(new Date(compra.fecha_hora))}</td>
                    <td className="px-4 py-3 text-slate-800">{compra.proveedor_nombre}</td>
                    <td className="px-4 py-3 text-slate-600">{compra.registrado_por}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-600">{compra.cantidad_lineas}</td>
                    <td className="px-4 py-3 text-right tabular-nums font-semibold text-slate-900">Bs {compra.total}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => setModal({ tipo: 'detalle', idCompra: compra.id_compra })}
                        title="Ver detalle"
                        aria-label={`Ver detalle de la compra ${compra.id_compra}`}
                        className="rounded-lg p-2 text-slate-500 hover:bg-amber-50 hover:text-amber-700 cursor-pointer"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}

                {!cargando && compras.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center">
                      <ShoppingCart className="mx-auto mb-2 w-8 h-8 text-slate-300" />
                      <p className="text-sm font-medium text-slate-500">Todavía no hay compras registradas.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="border-t border-slate-100 px-4 py-3 text-xs text-slate-500">
          {cargando && !resultado
            ? 'Cargando compras...'
            : `Mostrando ${compras.length} compras · total acumulado Bs ${totalGeneral.toFixed(2)}`}
        </div>
      </section>

      {modal?.tipo === 'registrar' && (
        <RegistrarCompraModal onClose={() => setModal(null)} onSaved={handleRegistrada} />
      )}

      {modal?.tipo === 'detalle' && (
        <DetalleCompraModal idCompra={modal.idCompra} onClose={() => setModal(null)} />
      )}
    </div>
  );
};

export default ComprasPage;
