import React, { useState } from 'react';
import { isAxiosError } from 'axios';
import { AlertCircle, AlertTriangle, Calculator, X } from 'lucide-react';
import productoService from '../../../../services/productoService';
import type { CategoriaProducto, Producto, ProductoPayload } from '../../../../types/producto';
import { calcularPrecioSugerido, formatearBs } from '../precios';

interface ProductoFormModalProps {
  /** null = alta de producto; con valor = edición. */
  producto: Producto | null;
  categorias: CategoriaProducto[];
  onClose: () => void;
  onSaved: (producto: Producto) => void;
}

type ErroresCampo = Partial<Record<keyof ProductoPayload | 'general', string>>;

const estadoInicial = (producto: Producto | null): ProductoPayload => ({
  id_categoria: producto?.id_categoria ?? null,
  nombre: producto?.nombre ?? '',
  descripcion: producto?.descripcion ?? '',
  costo_produccion: producto?.costo_produccion ?? '',
  porcentaje_ganancia: producto?.porcentaje_ganancia ?? '',
  precio_venta: producto?.precio_venta ?? '',
});

const validar = (form: ProductoPayload): ErroresCampo => {
  const errores: ErroresCampo = {};
  if (!form.nombre.trim()) errores.nombre = 'El nombre del producto es obligatorio.';
  if (form.id_categoria === null) errores.id_categoria = 'Selecciona una categoría.';

  const costo = Number(form.costo_produccion);
  if (form.costo_produccion.trim() === '' || !Number.isFinite(costo) || costo < 0) {
    errores.costo_produccion = 'Ingresa un costo válido (0 o mayor).';
  }
  const porcentaje = Number(form.porcentaje_ganancia);
  if (form.porcentaje_ganancia.trim() === '' || !Number.isFinite(porcentaje) || porcentaje < 0) {
    errores.porcentaje_ganancia = 'Ingresa un porcentaje válido (0 o mayor).';
  }
  const precio = Number(form.precio_venta);
  if (form.precio_venta.trim() === '' || !Number.isFinite(precio) || precio <= 0) {
    errores.precio_venta = 'El precio de venta debe ser mayor a cero.';
  }
  return errores;
};

const erroresDesdeApi = (data: unknown): ErroresCampo => {
  if (!data || typeof data !== 'object') {
    return { general: 'No se pudo guardar el producto.' };
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

export const ProductoFormModal: React.FC<ProductoFormModalProps> = ({
  producto,
  categorias,
  onClose,
  onSaved,
}) => {
  const [form, setForm] = useState<ProductoPayload>(() => estadoInicial(producto));
  const [errores, setErrores] = useState<ErroresCampo>({});
  const [guardando, setGuardando] = useState(false);

  const esEdicion = producto !== null;
  const sugerido = calcularPrecioSugerido(form.costo_produccion, form.porcentaje_ganancia);
  const cambioDePrecio =
    esEdicion && form.precio_venta.trim() !== '' && Number(form.precio_venta) !== Number(producto.precio_venta);

  const actualizar = <K extends keyof ProductoPayload>(campo: K, valor: ProductoPayload[K]) => {
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

    const payload: ProductoPayload = {
      ...form,
      nombre: form.nombre.trim(),
      descripcion: form.descripcion.trim(),
    };

    setGuardando(true);
    try {
      const guardado = esEdicion
        ? await productoService.actualizar(producto.id_producto, payload)
        : await productoService.crear(payload);
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
        aria-labelledby="titulo-producto"
        className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-xl border border-amber-100"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 id="titulo-producto" className="text-base font-bold text-slate-900">
              {esEdicion ? 'Editar producto' : 'Nuevo producto'}
            </h2>
            <p className="text-xs text-slate-500">Catálogo base de la panadería (CU5)</p>
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
              maxLength={100}
              value={form.nombre}
              onChange={(e) => actualizar('nombre', e.target.value)}
              placeholder="ej. Marraqueta"
              className={inputClass(Boolean(errores.nombre))}
            />
            <CampoError mensaje={errores.nombre} />
          </div>

          <div>
            <label htmlFor="id_categoria" className="block text-xs font-semibold text-slate-700 mb-1.5">
              Categoría
            </label>
            <select
              id="id_categoria"
              value={form.id_categoria ?? ''}
              onChange={(e) => actualizar('id_categoria', e.target.value ? Number(e.target.value) : null)}
              className={inputClass(Boolean(errores.id_categoria))}
            >
              <option value="">Selecciona una categoría</option>
              {categorias.map((categoria) => (
                <option key={categoria.id_categoria} value={categoria.id_categoria}>
                  {categoria.nombre}
                </option>
              ))}
            </select>
            <CampoError mensaje={errores.id_categoria} />
          </div>

          <div>
            <label htmlFor="descripcion" className="block text-xs font-semibold text-slate-700 mb-1.5">
              Descripción <span className="font-normal text-slate-400">(opcional)</span>
            </label>
            <textarea
              id="descripcion"
              rows={2}
              value={form.descripcion}
              onChange={(e) => actualizar('descripcion', e.target.value)}
              className={inputClass(false)}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="costo" className="block text-xs font-semibold text-slate-700 mb-1.5">
                Costo de producción (Bs)
              </label>
              <input
                id="costo"
                type="number"
                inputMode="decimal"
                min="0"
                step="0.01"
                value={form.costo_produccion}
                onChange={(e) => actualizar('costo_produccion', e.target.value)}
                placeholder="0.40"
                className={inputClass(Boolean(errores.costo_produccion))}
              />
              <CampoError mensaje={errores.costo_produccion} />
            </div>
            <div>
              <label htmlFor="ganancia" className="block text-xs font-semibold text-slate-700 mb-1.5">
                Ganancia (%)
              </label>
              <input
                id="ganancia"
                type="number"
                inputMode="decimal"
                min="0"
                step="0.01"
                value={form.porcentaje_ganancia}
                onChange={(e) => actualizar('porcentaje_ganancia', e.target.value)}
                placeholder="50"
                className={inputClass(Boolean(errores.porcentaje_ganancia))}
              />
              <CampoError mensaje={errores.porcentaje_ganancia} />
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 rounded-xl border border-amber-100 bg-amber-50/70 px-4 py-3">
            <div className="flex items-center gap-2.5">
              <Calculator className="w-5 h-5 text-amber-700" />
              <div>
                <p className="text-[11px] font-medium text-amber-900">Precio sugerido</p>
                <p className="text-sm font-bold text-amber-900">
                  {sugerido === null ? '—' : formatearBs(sugerido)}
                </p>
              </div>
            </div>
            <button
              type="button"
              disabled={sugerido === null || sugerido <= 0}
              onClick={() => sugerido !== null && actualizar('precio_venta', sugerido.toFixed(2))}
              className="rounded-lg border border-amber-200 bg-white px-3 py-1.5 text-xs font-semibold text-amber-800 hover:bg-amber-100 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              Usar como precio de venta
            </button>
          </div>
          <p className="-mt-2 text-[11px] text-slate-500">
            Costo × (1 + ganancia ÷ 100). Lo recalcula el sistema al guardar.
          </p>

          <div>
            <label htmlFor="precio_venta" className="block text-xs font-semibold text-slate-700 mb-1.5">
              Precio de venta (Bs)
            </label>
            <input
              id="precio_venta"
              type="number"
              inputMode="decimal"
              min="0.01"
              step="0.01"
              value={form.precio_venta}
              onChange={(e) => actualizar('precio_venta', e.target.value)}
              placeholder="0.60"
              className={inputClass(Boolean(errores.precio_venta))}
            />
            <CampoError mensaje={errores.precio_venta} />
          </div>

          {cambioDePrecio && (
            <div className="p-3 bg-amber-50 border border-amber-200 text-amber-900 text-xs rounded-xl flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0 text-amber-600" />
              <span>
                Cambiar el precio de venta de {formatearBs(producto?.precio_venta ?? 0)} a{' '}
                {formatearBs(form.precio_venta)} registrará un nuevo valor en el historial de precios.
              </span>
            </div>
          )}

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
              {guardando ? 'Guardando...' : esEdicion ? 'Guardar cambios' : 'Crear producto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProductoFormModal;
