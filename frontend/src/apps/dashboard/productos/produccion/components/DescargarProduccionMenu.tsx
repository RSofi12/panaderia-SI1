import React from 'react';
import MenuDescarga from '../../../components/MenuDescarga';
import produccionService from '../../../../../services/produccionService';
import type { ProduccionFiltros } from '../../../../../types/produccion';
import { JORNADAS_LABELS } from '../../../../../types/produccion';

interface DescargarProduccionMenuProps {
  filtros: ProduccionFiltros;
  nombreProducto?: string;
  deshabilitado?: boolean;
}

function describirFiltro(filtros: ProduccionFiltros, nombreProducto?: string): string {
  const jornada = filtros.jornada ? JORNADAS_LABELS[filtros.jornada] : 'todas las jornadas';
  let periodo = 'todas las fechas';
  if (filtros.fecha_desde && filtros.fecha_hasta) {
    periodo = `${filtros.fecha_desde} a ${filtros.fecha_hasta}`;
  } else if (filtros.fecha_desde) {
    periodo = `desde ${filtros.fecha_desde}`;
  } else if (filtros.fecha_hasta) {
    periodo = `hasta ${filtros.fecha_hasta}`;
  }
  const producto = nombreProducto || (filtros.id_producto ? `producto ${filtros.id_producto}` : 'todos los productos');
  return `${jornada} · ${periodo} · ${producto}`;
}

export const DescargarProduccionMenu: React.FC<DescargarProduccionMenuProps> = ({
  filtros,
  nombreProducto,
  deshabilitado = false,
}) => (
  <MenuDescarga
    descripcion={describirFiltro(filtros, nombreProducto)}
    deshabilitado={deshabilitado}
    validar={() => (
      filtros.fecha_desde && filtros.fecha_hasta && filtros.fecha_desde > filtros.fecha_hasta
        ? 'La fecha inicial no puede ser mayor que la fecha final.'
        : null
    )}
    onDescargar={(formato) => produccionService.descargarHistorial(formato, filtros)}
  />
);

export default DescargarProduccionMenu;
