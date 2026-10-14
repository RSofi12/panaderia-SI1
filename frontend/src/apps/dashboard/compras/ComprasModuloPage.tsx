import React from 'react';
import type { ElementType } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ShoppingCart, Truck } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import ProveedoresPage from '../proveedores/ProveedoresPage';
import ComprasPage from './ComprasPage';

type Pestana = 'compras' | 'proveedores';

interface DefinicionPestana {
  id: Pestana;
  etiqueta: string;
  icono: ElementType;
  visible: boolean;
}

export const ComprasModuloPage: React.FC = () => {
  const { hasPermission } = useAuth();
  const puedeComprar = hasPermission('registrar_compras');
  const puedeVerProveedores = puedeComprar || hasPermission('gestionar_proveedores');

  const pestanas: DefinicionPestana[] = [
    { id: 'compras', etiqueta: 'Compras', icono: ShoppingCart, visible: puedeComprar },
    { id: 'proveedores', etiqueta: 'Proveedores', icono: Truck, visible: puedeVerProveedores },
  ];
  const disponibles = pestanas.filter((p) => p.visible);

  // La pestaña vive en la URL (?tab=) para que sobreviva a recargar la página.
  const [params, setParams] = useSearchParams();
  const pedida = params.get('tab');
  const activa: Pestana =
    disponibles.find((p) => p.id === pedida)?.id ?? disponibles[0]?.id ?? 'proveedores';

  return (
    <div className="space-y-6">
      {disponibles.length > 1 && (
        <div role="tablist" aria-label="Secciones de compras" className="mx-auto flex max-w-6xl flex-wrap gap-x-1 gap-y-1 border-b border-slate-200">
          {disponibles.map(({ id, etiqueta, icono: Icono }) => {
            const seleccionada = id === activa;
            return (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={seleccionada}
                onClick={() => setParams({ tab: id })}
                className={`-mb-px inline-flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold transition-colors cursor-pointer ${
                  seleccionada
                    ? 'border-amber-600 text-amber-700'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Icono className="w-4 h-4" />
                {etiqueta}
              </button>
            );
          })}
        </div>
      )}

      <div role="tabpanel">{activa === 'compras' ? <ComprasPage /> : <ProveedoresPage />}</div>
    </div>
  );
};

export default ComprasModuloPage;
