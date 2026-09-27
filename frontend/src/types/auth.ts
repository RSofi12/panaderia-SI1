export interface Permiso {
  id_permiso: number;
  nombre: string;
  descripcion?: string;
}

export interface Rol {
  id_rol: number;
  nombre: string;
  descripcion?: string;
  permisos?: Permiso[];
}

export interface Usuario {
  id_usuario: number;
  nombre_usuario: string;
  nombre_completo: string;
  email: string | null;
  activo: boolean;
  id_rol: number | null;
  rol: string;
  permisos: string[];
}

export interface LoginCredentials {
  nombre_usuario: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: Usuario;
}

export interface AuthContextType {
  user: Usuario | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permissionName: string) => boolean;
  hasRole: (roleName: string) => boolean;
}
