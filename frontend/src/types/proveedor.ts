export interface Proveedor {
  id_proveedor: number;
  nombre: string;
  telefono: string | null;
  direccion: string | null;
  descripcion: string;
  fecha_registro: string;
  activo: boolean;
}

export interface ProveedorPayload {
  nombre: string;
  telefono: string;
  direccion: string;
  descripcion: string;
}

export interface ProveedorFiltros {
  q?: string;
  nombre?: string;
  telefono?: string;
  activo?: 'true' | 'false';
}
