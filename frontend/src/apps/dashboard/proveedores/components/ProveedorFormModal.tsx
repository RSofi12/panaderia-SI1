import React, { useState } from 'react';
import { isAxiosError } from 'axios';
import { AlertCircle, X } from 'lucide-react';
import proveedorService from '../../../../services/proveedorService';
import type { Proveedor, ProveedorPayload } from '../../../../types/proveedor';

interface ProveedorFormModalProps {
  proveedor: Proveedor | null;
  onClose: () => void;
  onSaved: (proveedor: Proveedor) => void;
}

type ErroresCampo = Partial<Record<keyof ProveedorPayload | 'general', string>>;

const estadoInicial = (proveedor: Proveedor | null): ProveedorPayload => ({
  nombre: proveedor?.nombre ?? '',
  telefono: proveedor?.telefono ?? '',
  direccion: proveedor?.direccion ?? '',
});

const validar = (form: ProveedorPayload): ErroresCampo => {
  const errores: ErroresCampo = {};
  if (!form.nombre.trim()) errores.nombre = 'El nombre del proveedor es obligatorio.';
  if (!form.telefono.trim()) errores.telefono = 'El teléfono es obligatorio.';
  if (!form.direccion.trim()) errores.direccion = 'La dirección es obligatoria.';
  return errores;
};

const erroresDesdeApi = (data: unknown): ErroresCampo => {
  if (!data || typeof data !== 'object') {
    return { general: 'No se pudo guardar el proveedor.' };
  }
  const errores: ErroresCampo = {};
  for (const [campo, valor] of Object.entries(data as Record<string, unknown>)) {
    const mensaje = Array.isArray(valor) ? String(valor[0]) : String(valor);
    const clave = campo === 'detail' || campo === 'non_field_errors' ? 'general' : campo;
    errores[clave as keyof ErroresCampo] = mensaje;
  }
  return errores;
};

const inputClass = (conError: boolean) =>
  `w-full px-3.5 py-2.5 bg-slate-50 border rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all ${
    conError ? 'border-red-300' : 'border-slate-200'
  }`;

const CampoError: React.FC<{ mensaje?: string }> = ({ mensaje }) =>
  mensaje ? <p className="mt-1 text-[11px] text-red-600">{mensaje}</p> : null;

export const ProveedorFormModal: React.FC<ProveedorFormModalProps> = ({
  proveedor,
  onClose,
  onSaved,
}) => {
  const [form, setForm] = useState<ProveedorPayload>(() => estadoInicial(proveedor));
  const [errores, setErrores] = useState<ErroresCampo>({});
  const [guardando, setGuardando] = useState(false);

  const esEdicion = proveedor !== null;

  const actualizar = <K extends keyof ProveedorPayload>(campo: K, valor: ProveedorPayload[K]) => {
    setForm((actual) => ({ ...actual, [campo]: valor }));
    setErrores((actual) => ({ ...actual, [campo]: undefined, general: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const erroresLocales = validar(form);
    if (Object.keys(erroresLocales).length > 0) {
      setErrores(erroresLocales);
      return;
    }

    const payload: ProveedorPayload = {
      nombre: form.nombre.trim(),
      telefono: form.telefono.trim(),
      direccion: form.direccion.trim(),
    };

    setGuardando(true);
    try {
      const guardado = esEdicion
        ? await proveedorService.actualizar(proveedor.id_proveedor, payload)
        : await proveedorService.crear(payload);
      onSaved(guardado);
    } catch (err) {
      setErrores(
        isAxiosError(err) && err.response
          ? erroresDesdeApi(err.response.data)
          : { general: 'No se pudo conectar con el servidor.' }
      );
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-proveedor"
        className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-xl border border-amber-100"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 id="titulo-proveedor" className="text-base font-bold text-slate-900">
              {esEdicion ? 'Editar proveedor' : 'Nuevo proveedor'}
            </h2>
            <p className="text-xs text-slate-500">Maestro de proveedores de insumos (CU6)</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 px-6 py-5" noValidate>
          {errores.general && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{errores.general}</span>
            </div>
          )}

          <div>
            <label htmlFor="nombre" className="block text-xs font-semibold text-slate-700 mb-1.5">
              Nombre
            </label>
            <input
              id="nombre"
              type="text"
              maxLength={150}
              value={form.nombre}
              onChange={(e) => actualizar('nombre', e.target.value)}
              placeholder="ej. Molinos del Oriente S.R.L."
              className={inputClass(Boolean(errores.nombre))}
            />
            <CampoError mensaje={errores.nombre} />
          </div>

          <div>
            <label htmlFor="telefono" className="block text-xs font-semibold text-slate-700 mb-1.5">
              Teléfono
            </label>
            <input
              id="telefono"
              type="tel"
              maxLength={20}
              value={form.telefono}
              onChange={(e) => actualizar('telefono', e.target.value)}
              placeholder="ej. 33210099 o +591 33210099"
              className={inputClass(Boolean(errores.telefono))}
            />
            <CampoError mensaje={errores.telefono} />
          </div>

          <div>
            <label htmlFor="direccion" className="block text-xs font-semibold text-slate-700 mb-1.5">
              Dirección
            </label>
            <input
              id="direccion"
              type="text"
              maxLength={200}
              value={form.direccion}
              onChange={(e) => actualizar('direccion', e.target.value)}
              placeholder="ej. Parque Industrial, Santa Cruz"
              className={inputClass(Boolean(errores.direccion))}
            />
            <CampoError mensaje={errores.direccion} />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={guardando}
              className="rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-amber-600/20 hover:from-amber-700 hover:to-amber-800 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
            >
              {guardando ? 'Guardando...' : esEdicion ? 'Guardar cambios' : 'Crear proveedor'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProveedorFormModal;
