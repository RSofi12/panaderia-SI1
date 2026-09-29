import React from 'react';
import {
  Flame,
  KeyRound,
  Lock,
  Pencil,
  Receipt,
  ShieldCheck,
  Sparkles,
  UserCheck,
  Users,
} from 'lucide-react';
import type { RolListado } from '../../../../types/roles';
import { estilosRoles } from './estilosRoles';

interface TarjetaRolProps {
  rol: RolListado;
  totalPermisosCatalogo: number;
  onConfigurar: (rol: RolListado) => void;
  onEditar: (rol: RolListado) => void;
}

interface RolVisualInfo {
  icono: React.ElementType;
  colorFondo: string;
  colorIcono: string;
  colorBorde: string;
}

/**
 * Mapeo de identidad visual según el rol del personal de la panadería.
 */
function obtenerVisualRol(nombre: string): RolVisualInfo {
  const normalizado = nombre.toLowerCase().trim();

  if (normalizado.includes('admin')) {
    return {
      icono: ShieldCheck,
      colorFondo: 'bg-amber-100/80',
      colorIcono: 'text-amber-800',
      colorBorde: 'border-amber-200',
    };
  }
  if (normalizado.includes('cajer') || normalizado.includes('vent')) {
    return {
      icono: Receipt,
      colorFondo: 'bg-emerald-100/80',
      colorIcono: 'text-emerald-800',
      colorBorde: 'border-emerald-200',
    };
  }
  if (normalizado.includes('panad')) {
    return {
      icono: Flame,
      colorFondo: 'bg-orange-100/80',
      colorIcono: 'text-orange-800',
      colorBorde: 'border-orange-200',
    };
  }
  if (normalizado.includes('pastel') || normalizado.includes('repost')) {
    return {
      icono: Sparkles,
      colorFondo: 'bg-rose-100/80',
      colorIcono: 'text-rose-800',
      colorBorde: 'border-rose-200',
    };
  }

  return {
    icono: UserCheck,
    colorFondo: 'bg-slate-100',
    colorIcono: 'text-slate-700',
    colorBorde: 'border-slate-200',
  };
}

export const TarjetaRol: React.FC<TarjetaRolProps> = ({
  rol,
  totalPermisosCatalogo,
  onConfigurar,
  onEditar,
}) => {
  const porcentaje =
    totalPermisosCatalogo > 0
      ? Math.round((rol.total_permisos / totalPermisosCatalogo) * 100)
      : 0;

  const visual = obtenerVisualRol(rol.nombre);
  const IconoRol = visual.icono;

  return (
    <article className={estilosRoles.tarjeta} aria-labelledby={`rol-titulo-${rol.id_rol}`}>
      <div>
        {/* Cabecera con Avatar de Rol, Nombre y Badge */}
        <div className={estilosRoles.tarjetaHeader}>
          <div className="flex items-center gap-3 min-w-0">
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${visual.colorFondo} ${visual.colorBorde} shadow-2xs`}
              aria-hidden="true"
            >
              <IconoRol className={`h-5 w-5 ${visual.colorIcono}`} />
            </div>

            <div className="min-w-0">
              <h3 id={`rol-titulo-${rol.id_rol}`} className={estilosRoles.tarjetaTitulo}>
                <span className="truncate">{rol.nombre}</span>
              </h3>
              <p className="text-[11px] text-slate-500 font-medium">
                {rol.es_protegido ? 'Perfil base del sistema' : 'Perfil personalizado'}
              </p>
            </div>
          </div>

          <div className="shrink-0">
            {rol.es_protegido ? (
              <span
                className={estilosRoles.badgeProtegido}
                title="Rol base del sistema: su nombre no puede ser cambiado para salvaguardar la coherencia interna."
              >
                <Lock className="h-3 w-3 text-amber-700" aria-hidden="true" />
                Sistema
              </span>
            ) : (
              <span
                className={estilosRoles.badgePersonalizado}
                title="Rol personalizado creado por la administración"
              >
                Personalizado
              </span>
            )}
          </div>
        </div>

        {/* Descripción del rol */}
        <p className={estilosRoles.tarjetaDesc}>
          {rol.descripcion || 'Sin descripción asignada para este perfil de usuario.'}
        </p>

        {/* Métricas destacadas */}
        <div className="grid grid-cols-2 gap-2 mb-4">
          <div
            className={estilosRoles.badgeMetrica}
            title={`${rol.total_usuarios} usuarios asignados con este rol`}
          >
            <Users className="h-3.5 w-3.5 text-slate-500 shrink-0" aria-hidden="true" />
            <span className="truncate">
              <strong className="font-semibold text-slate-900">{rol.total_usuarios}</strong>{' '}
              {rol.total_usuarios === 1 ? 'cuenta' : 'cuentas'}
            </span>
          </div>

          <div
            className={estilosRoles.badgeMetrica}
            title={`${rol.total_permisos} permisos asignados de un catálogo de ${totalPermisosCatalogo}`}
          >
            <KeyRound className="h-3.5 w-3.5 text-slate-500 shrink-0" aria-hidden="true" />
            <span className="truncate">
              <strong className="font-semibold text-slate-900">{rol.total_permisos}</strong> de{' '}
              {totalPermisosCatalogo}
            </span>
          </div>
        </div>

        {/* Cobertura de permisos */}
        <div className="space-y-1.5 mb-5">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Cobertura de permisos</span>
            <span className="font-semibold text-slate-800">{porcentaje}%</span>
          </div>
          <div
            className={estilosRoles.barraProgresoFondo}
            role="progressbar"
            aria-valuenow={porcentaje}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Cobertura de permisos para ${rol.nombre}: ${porcentaje}%`}
          >
            <div
              className={estilosRoles.barraProgresoRelleno}
              style={{ width: `${Math.min(porcentaje, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Botones de acción */}
      <div className="flex items-center gap-2 pt-3 border-t border-slate-100">
        <button
          type="button"
          onClick={() => onConfigurar(rol)}
          className={estilosRoles.botonConfigurar}
          aria-label={`Configurar matriz de permisos para el rol ${rol.nombre}`}
        >
          <ShieldCheck className="h-4 w-4" aria-hidden="true" />
          <span>Matriz de permisos</span>
        </button>

        <button
          type="button"
          onClick={() => onEditar(rol)}
          className={estilosRoles.botonEditar}
          aria-label={`Editar detalles del rol ${rol.nombre}`}
          title="Editar descripción o nombre del rol"
        >
          <Pencil className="h-3.5 w-3.5 text-slate-600" aria-hidden="true" />
        </button>
      </div>
    </article>
  );
};

export default TarjetaRol;
