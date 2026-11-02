import React from 'react';
import MenuDescarga from '../../components/MenuDescarga';
import compraService from '../../../../services/compraService';
import type { CompraFiltros } from '../../../../types/compra';

interface DescargarComprasMenuProps {
  filtros: CompraFiltros;
  nombreProveedor?: string;
  deshabilitado?: boolean;
}

function describirFiltro(filtros: CompraFiltros, nombreProveedor?: string): string {
  const proveedor = nombreProveedor
    || (filtros.id_proveedor ? `proveedor ${filtros.id_proveedor}` : 'todos los proveedores');
  let periodo = 'todas las fechas';
  if (filtros.fecha_desde && filtros.fecha_hasta) {
    periodo = `${filtros.fecha_desde} a ${filtros.fecha_hasta}`;
  } else if (filtros.fecha_desde) {
    periodo = `desde ${filtros.fecha_desde}`;
  } else if (filtros.fecha_hasta) {
    periodo = `hasta ${filtros.fecha_hasta}`;
  }
  const busqueda = filtros.search?.trim()
    ? `búsqueda «${filtros.search.trim()}»`
    : 'todo el listado';
  return `${proveedor} · ${periodo} · ${busqueda}`;
}

export const DescargarComprasMenu: React.FC<DescargarComprasMenuProps> = ({
  filtros,
  nombreProveedor,
  deshabilitado = false,
}) => (
  <MenuDescarga
    descripcion={describirFiltro(filtros, nombreProveedor)}
    deshabilitado={deshabilitado}
    validar={() => (
      filtros.fecha_desde && filtros.fecha_hasta && filtros.fecha_desde > filtros.fecha_hasta
        ? 'La fecha inicial no puede ser mayor que la fecha final.'
        : null
    )}
    onDescargar={(formato) => compraService.descargar(formato, filtros)}
  />
);

export default DescargarComprasMenu;
