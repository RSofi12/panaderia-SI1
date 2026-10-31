import React, { useEffect, useState } from 'react';
import { AlertCircle, Download, FileText, Loader2, Printer, X } from 'lucide-react';
import type { ComprobanteVenta } from '../../../../types/comprobante';
import { ComprobanteTicketView } from './ComprobanteTicketView';
import { ventaService } from './ventaService';

interface ComprobanteVentaModalProps {
  idVenta: number | null;
  abierto: boolean;
  onCerrar: () => void;
}

export const ComprobanteVentaModal: React.FC<ComprobanteVentaModalProps> = ({
  idVenta,
  abierto,
  onCerrar,
}) => {
  const [comprobante, setComprobante] = useState<ComprobanteVenta | null>(null);
  const [cargando, setCargando] = useState(false);
  const [descargandoPdf, setDescargandoPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!abierto || !idVenta) {
      return;
    }

    let activo = true;

    const cargar = async () => {
      setCargando(true);
      setError(null);
      try {
        const datos = await ventaService.obtenerComprobante(idVenta);
        if (activo) {
          setComprobante(datos);
        }
      } catch (err: unknown) {
        if (activo) {
          const apiError = (err as { response?: { data?: { error?: string } } })?.response?.data?.error;
          const mensaje = apiError || (err instanceof Error ? err.message : 'No se pudo cargar el comprobante');
          setError(mensaje);
        }
      } finally {
        if (activo) {
          setCargando(false);
        }
      }
    };

    void cargar();

    return () => {
      activo = false;
    };
  }, [idVenta, abierto]);

  // Manejo de teclado (Escape para cerrar)
  useEffect(() => {
    if (!abierto) return;
    const alPresionar = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCerrar();
    };
    window.addEventListener('keydown', alPresionar);
    return () => window.removeEventListener('keydown', alPresionar);
  }, [abierto, onCerrar]);

  const handleDescargarPdf = async () => {
    if (!comprobante) return;
    try {
      setDescargandoPdf(true);
      await ventaService.descargarPdfComprobante(
        comprobante.id_venta,
        comprobante.numero_comprobante
      );
    } catch (err: unknown) {
      const mensaje = err instanceof Error ? err.message : 'Error al descargar el PDF';
      alert(mensaje);
    } finally {
      setDescargandoPdf(false);
    }
  };

  const handleImprimir = () => {
    if (!comprobante) return;

    // Crear ventana de impresión limpia para el ticket térmico
    const elemento = document.getElementById('ticket-imprimible-area');
    if (!elemento) {
      window.print();
      return;
    }

    const ventana = window.open('', '_blank', 'width=400,height=600');
    if (!ventana) {
      window.print();
      return;
    }

    const metodoPagoNombre = comprobante.metodo_pago === 'stripe' ? 'TARJETA (STRIPE)' : 'EFECTIVO';

    ventana.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Comprobante #${comprobante.numero_comprobante} - Panadería Santiago</title>
          <style>
            @page {
              margin: 4mm;
              size: 80mm auto;
            }
            body {
              font-family: monospace, 'Courier New', Courier;
              font-size: 11px;
              color: #111;
              margin: 0;
              padding: 6px;
              line-height: 1.3;
            }
            .text-center { text-align: center; }
            .text-right { text-align: right; }
            .text-left { text-align: left; }
            .font-bold { font-weight: bold; }
            .border-b { border-bottom: 1px dashed #666; padding-bottom: 5px; margin-bottom: 5px; }
            .border-t { border-top: 1px dashed #666; padding-top: 5px; margin-top: 5px; }
            table { width: 100%; border-collapse: collapse; font-size: 11px; }
            th { text-align: left; font-size: 10px; border-bottom: 1px solid #999; padding-bottom: 3px; }
            td { padding: 2px 0; }
            .flex-between { display: flex; justify-content: space-between; }
          </style>
        </head>
        <body>
          <div class="text-center border-b">
            <h2 style="margin: 0 0 2px 0; font-size: 14px;">${comprobante.empresa.nombre}</h2>
            <div>${comprobante.empresa.propietario}</div>
            <div style="font-size: 10px;">${comprobante.empresa.direccion}</div>
            <div style="font-size: 10px;">Telf: ${comprobante.empresa.telefono}</div>
          </div>

          <div class="border-b" style="font-size: 11px;">
            <div class="flex-between font-bold">
              <span>COMPROBANTE DE VENTA</span>
              <span>#${comprobante.numero_comprobante}</span>
            </div>
            <div class="flex-between">
              <span>Fecha:</span>
              <span>${new Date(comprobante.fecha_hora).toLocaleString('es-BO')}</span>
            </div>
            <div class="flex-between">
              <span>Cajero:</span>
              <span>${comprobante.cajero}</span>
            </div>
            <div class="flex-between">
              <span>Pago:</span>
              <span>${metodoPagoNombre}</span>
            </div>
            ${
              comprobante.id_transaccion_stripe
                ? `<div class="flex-between" style="font-size: 9px;"><span>Ref:</span><span>${comprobante.id_transaccion_stripe}</span></div>`
                : ''
            }
          </div>

          <table class="border-b">
            <thead>
              <tr>
                <th style="width: 25px; text-align: center;">Cant</th>
                <th>Producto</th>
                <th style="text-align: right; width: 45px;">P.U.</th>
                <th style="text-align: right; width: 50px;">Total</th>
              </tr>
            </thead>
            <tbody>
              ${comprobante.detalles
                .map(
                  (item) => `
                <tr>
                  <td style="text-align: center; font-weight: bold;">${item.cantidad}</td>
                  <td>${item.nombre_producto}</td>
                  <td style="text-align: right;">${Number(item.precio_unitario).toFixed(2)}</td>
                  <td style="text-align: right; font-weight: bold;">${Number(item.subtotal).toFixed(2)}</td>
                </tr>
              `
                )
                .join('')}
            </tbody>
          </table>

          <div class="border-b">
            <div class="flex-between">
              <span>Total articulos:</span>
              <span>${comprobante.total_articulos}</span>
            </div>
            <div class="flex-between font-bold border-t" style="font-size: 13px;">
              <span>TOTAL BS:</span>
              <span>Bs ${Number(comprobante.total).toFixed(2)}</span>
            </div>
          </div>

          <div class="text-center" style="font-size: 10px; margin-top: 8px;">
            <div class="font-bold">¡GRACIAS POR SU COMPRA!</div>
            <div>Panaderia Santiago</div>
            <div style="font-size: 9px; color: #555;">Documento de control interno</div>
          </div>
        </body>
      </html>
    `);

    ventana.document.close();
    ventana.focus();
    setTimeout(() => {
      ventana.print();
      ventana.close();
    }, 250);
  };

  const handleCerrar = () => {
    setComprobante(null);
    setError(null);
    onCerrar();
  };

  if (!abierto) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-modal-comprobante"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm"
      onClick={handleCerrar}
    >
      <div
        className="flex max-h-[92vh] w-full max-w-md flex-col rounded-2xl bg-white shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera del modal */}
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 bg-amber-50/50">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-600 text-white shadow-sm">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h2 id="titulo-modal-comprobante" className="text-base font-bold text-slate-900">
                Comprobante de Venta
              </h2>
              <p className="text-xs text-slate-500">CU16 · Panadería Santiago</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleCerrar}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
            aria-label="Cerrar comprobante"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Cuerpo del modal con el ticket */}
        <div className="flex-1 overflow-y-auto p-5 bg-slate-50">
          {cargando ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-500">
              <Loader2 className="h-9 w-9 animate-spin text-amber-600" />
              <p className="mt-3 text-sm font-medium">Cargando comprobante...</p>
            </div>
          ) : error ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-center">
              <AlertCircle className="mx-auto h-8 w-8 text-rose-600" />
              <p className="mt-2 text-sm font-semibold text-rose-800">{error}</p>
              <button
                type="button"
                onClick={handleCerrar}
                className="mt-3 text-xs font-bold text-rose-700 underline"
              >
                Cerrar
              </button>
            </div>
          ) : comprobante ? (
            <ComprobanteTicketView comprobante={comprobante} />
          ) : null}
        </div>

        {/* Botones de acción inferiores */}
        <div className="border-t border-slate-100 bg-white px-5 py-3.5 flex flex-wrap items-center justify-between gap-2">
          <button
            type="button"
            onClick={handleCerrar}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
          >
            Cerrar
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={!comprobante || cargando || descargandoPdf}
              onClick={handleDescargarPdf}
              className="inline-flex items-center gap-1.5 rounded-xl border border-amber-300 bg-amber-50 px-3.5 py-2.5 text-xs font-bold text-amber-800 hover:bg-amber-100 transition disabled:opacity-50"
              title="Descargar comprobante en PDF oficial"
            >
              {descargandoPdf ? (
                <Loader2 className="h-4 w-4 animate-spin text-amber-700" />
              ) : (
                <Download className="h-4 w-4 text-amber-700" />
              )}
              <span>Descargar PDF</span>
            </button>

            <button
              type="button"
              disabled={!comprobante || cargando}
              onClick={handleImprimir}
              className="inline-flex items-center gap-1.5 rounded-xl bg-amber-700 px-4 py-2.5 text-xs font-bold text-white shadow hover:bg-amber-800 transition disabled:opacity-50"
              title="Imprimir ticket para cliente"
            >
              <Printer className="h-4 w-4" />
              <span>Imprimir Ticket</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
