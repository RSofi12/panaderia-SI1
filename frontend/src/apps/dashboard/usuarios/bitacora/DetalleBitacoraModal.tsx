import React from 'react';
import Modal from '../../components/Modal';
import type { RegistroBitacora } from '../../../../types/bitacora';
import { autorRegistro, clasesAccion, formatearFechaHora, nombreModulo } from './formato';

interface DetalleBitacoraModalProps {
  registro: RegistroBitacora;
  onCerrar: () => void;
}

const Dato: React.FC<{ etiqueta: string; children: React.ReactNode }> = ({ etiqueta, children }) => (
  <div className="grid gap-1 sm:grid-cols-[9rem_1fr] sm:gap-3">
    <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{etiqueta}</dt>
    <dd className="text-sm text-slate-800 break-words">{children}</dd>
  </div>
);

export const DetalleBitacoraModal: React.FC<DetalleBitacoraModalProps> = ({ registro, onCerrar }) => (
  <Modal
    titulo={`Registro de auditoría #${registro.id_bitacora}`}
    subtitulo={formatearFechaHora(registro.fecha_hora)}
    onCerrar={onCerrar}
    ancho="lg"
    pie={
      <div className="flex justify-end">
        <button
          type="button"
          onClick={onCerrar}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
        >
          Cerrar
        </button>
      </div>
    }
  >
    <dl className="space-y-4">
      <Dato etiqueta="Usuario">
        {autorRegistro(registro)}
        {registro.nombre_usuario && <span className="ml-1.5 text-slate-500">@{registro.nombre_usuario}</span>}
      </Dato>
      <Dato etiqueta="Acción">
        <span
          className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${clasesAccion(registro.accion)}`}
        >
          {registro.accion_etiqueta}
        </span>
        <code className="ml-2 text-xs text-slate-400">{registro.accion}</code>
      </Dato>
      <Dato etiqueta="Módulo">
        {nombreModulo(registro.tabla_afectada)}
        {registro.tabla_afectada && (
          <code className="ml-2 text-xs text-slate-400">{registro.tabla_afectada}</code>
        )}
      </Dato>
      <Dato etiqueta="Descripción">
        <p className="whitespace-pre-wrap">{registro.descripcion || 'Sin descripción.'}</p>
      </Dato>
      <Dato etiqueta="Navegador">
        <span className="text-xs text-slate-600">{registro.agente_usuario || 'No registrado.'}</span>
      </Dato>
    </dl>
  </Modal>
);

export default DetalleBitacoraModal;
