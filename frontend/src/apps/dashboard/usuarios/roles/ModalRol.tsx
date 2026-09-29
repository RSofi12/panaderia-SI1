import React, { useId, useState } from 'react';
import { Lock, Shield } from 'lucide-react';
import { Modal } from '../../components/Modal';
import rolesService from '../../../../services/rolesService';
import { normalizarErrorApi } from '../../../../services/erroresApi';
import type { RolDetalle, RolListado } from '../../../../types/roles';

interface ModalRolProps {
  rol: RolListado | null;
  onCerrar: () => void;
  onGuardado: (rol: RolDetalle) => void;
  onExito: (mensaje: string) => void;
  onError: (mensaje: string) => void;
}

export const ModalRol: React.FC<ModalRolProps> = ({
  rol,
  onCerrar,
  onGuardado,
  onExito,
  onError,
}) => {
  const inputId = useId();
  const esEdicion = !!rol;
  const esProtegido = rol?.es_protegido ?? false;

  const [nombre, setNombre] = useState(rol?.nombre ?? '');
  const [descripcion, setDescripcion] = useState(rol?.descripcion ?? '');
  const [guardando, setGuardando] = useState(false);
  const [errores, setErrores] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrores({});

    const nombreLimpio = nombre.trim();
    if (!esEdicion && !nombreLimpio) {
      setErrores({ nombre: 'El nombre del rol es obligatorio.' });
      return;
    }

    setGuardando(true);
    try {
      let resultado: RolDetalle;
      if (esEdicion && rol) {
        resultado = await rolesService.editarRol(rol.id_rol, {
          ...(esProtegido ? {} : { nombre: nombreLimpio }),
          descripcion: descripcion.trim() || null,
        });
        onExito(`Rol "${resultado.nombre}" actualizado correctamente.`);
      } else {
        resultado = await rolesService.crearRol({
          nombre: nombreLimpio,
          descripcion: descripcion.trim() || null,
        });
        onExito(`Rol "${resultado.nombre}" creado exitosamente.`);
      }

      onGuardado(resultado);
      onCerrar();
    } catch (err: unknown) {
      const normalizado = normalizarErrorApi(err);
      if (normalizado.campos && Object.keys(normalizado.campos).length > 0) {
        const erroresSimples: Record<string, string> = {};
        for (const [campo, lista] of Object.entries(normalizado.campos)) {
          if (lista && lista.length > 0) {
            erroresSimples[campo] = lista[0];
          }
        }
        setErrores(erroresSimples);
      }
      onError(normalizado.mensaje || 'No se pudo guardar la información del rol.');
    } finally {
      setGuardando(false);
    }
  };

  const pieModal = (
    <div className="flex items-center justify-end gap-2 w-full">
      <button
        type="button"
        onClick={onCerrar}
        disabled={guardando}
        className="min-h-10 px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 cursor-pointer disabled:opacity-50"
      >
        Cancelar
      </button>

      <button
        type="button"
        onClick={handleSubmit}
        disabled={guardando}
        className="min-h-10 px-5 py-2 text-xs font-semibold text-white bg-amber-600 rounded-xl shadow-xs hover:bg-amber-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 cursor-pointer disabled:opacity-60 flex items-center justify-center gap-2"
      >
        {guardando && (
          <div
            className="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"
            aria-hidden="true"
          />
        )}
        <span>{guardando ? 'Guardando...' : esEdicion ? 'Actualizar rol' : 'Crear rol'}</span>
      </button>
    </div>
  );

  return (
    <Modal
      titulo={esEdicion ? `Editar rol — ${rol.nombre}` : 'Nuevo rol de personal'}
      subtitulo={
        esEdicion
          ? 'Modifica los datos descriptivos del perfil de usuario.'
          : 'Define un nuevo perfil de acceso para asignar a cuentas del personal.'
      }
      ancho="md"
      onCerrar={onCerrar}
      pie={pieModal}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {esProtegido && (
          <div className="flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900 leading-relaxed shadow-2xs">
            <Lock className="h-4 w-4 text-amber-700 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <strong className="font-semibold">Perfil del sistema:</strong> Este es un rol base
              protegido. Su nombre no se puede modificar para preservar la integridad del sistema,
              pero puedes adaptar su descripción operativa.
            </div>
          </div>
        )}

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label htmlFor={`nombre-${inputId}`} className="block text-xs font-semibold text-slate-800">
              Nombre del rol <span className="text-amber-600">*</span>
            </label>
            <span className="text-[10px] text-slate-400 font-medium">
              {nombre.length} / 50
            </span>
          </div>

          <div className="relative">
            <input
              id={`nombre-${inputId}`}
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              disabled={esProtegido || guardando}
              placeholder="Ej. Cajero Principal, Supervisor..."
              maxLength={50}
              className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-900 transition-colors focus:outline-none focus:ring-2 ${
                errores.nombre
                  ? 'border-red-300 focus:border-red-600 focus:ring-red-100'
                  : 'border-slate-300 focus:border-amber-600 focus:ring-amber-100'
              } disabled:bg-slate-100/80 disabled:text-slate-500 disabled:cursor-not-allowed`}
              aria-invalid={!!errores.nombre}
              aria-describedby={errores.nombre ? `error-nombre-${inputId}` : undefined}
            />
            {esProtegido && (
              <Shield
                className="absolute right-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
                aria-hidden="true"
              />
            )}
          </div>
          {errores.nombre && (
            <p id={`error-nombre-${inputId}`} className="mt-1 text-xs text-red-600 font-medium">
              {errores.nombre}
            </p>
          )}
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label htmlFor={`desc-${inputId}`} className="block text-xs font-semibold text-slate-800">
              Descripción del rol
            </label>
            <span className="text-[10px] text-slate-400 font-medium">
              {descripcion.length} / 255
            </span>
          </div>

          <textarea
            id={`desc-${inputId}`}
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            disabled={guardando}
            rows={3}
            maxLength={255}
            placeholder="Describe las responsabilidades, alcance y actividades permitidas para este rol..."
            className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:border-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-100 resize-none"
          />
        </div>
      </form>
    </Modal>
  );
};

export default ModalRol;
