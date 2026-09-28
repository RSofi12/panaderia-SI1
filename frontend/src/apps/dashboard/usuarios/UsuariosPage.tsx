import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Search, X } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import usuariosService from '../../../services/usuariosService';
import { normalizarErrorApi } from '../../../services/erroresApi';
import UsuariosTabla from './components/UsuariosTabla';
import ModalUsuario from './components/ModalUsuario';
import ModalEstado from './components/ModalEstado';
import ModalRestablecerContrasena from './components/ModalRestablecerContrasena';
import type { EditarUsuario, RolSimple, UsuarioFila } from '../../../types/usuarios';

/**
 * Ventana de gestión de usuarios del Administrador (CU3).
 *
 * POR QUÉ ES UN CONTENEDOR Y NO UNA PANTALLA CON JSX DENTRO
 * Esta página no tiene casi appearance visual propio: trae los datos,
 * guarda el estado de los tres modales y del paginado. La tabla y cada
 * modal están aparte. Un componente que mezcla las cinco cosas tiene
 * que releerse entero para cambiar un color de la tabla.
 *
 * POR QUÉ NO HAY UN HOOK `useUsuarios`
 * Habría un hook con el listado, los filtros y el paginado, y con eso
 * la página bajaría a veinte líneas. Se deja así a propósito: el CU4
 * (roles) y el CU26 (bitácora) van a tener listados parecidos pero con
 * filtros distintos, y un hook genérico con cuatro parámetros
 * opcionales termina siendo un `any` con forma de función. Cuando
 * exista el segundo consumidor con el mismo patrón, ahí se extrae.
 *
 * CÓMO SE ACCEDE A ESTA VENTANA
 * `navigation.ts` la publica con el permiso `gestionar_usuarios` y la
 * ruta la declara `AppRoutes.tsx` detrás de `ProtectedRoute` con ese
 * mismo permiso. El filtro del Sidebar esconde el enlace; el
 * `ProtectedRoute` impide la URL directa. Son dos capas distintas:
 * la primera es de navegación, la segunda es de seguridad.
 */

/** Retraso del buscador, en ms. */
const RETRASO_BUSQUEDA = 300;

type ModalAbierto =
  | { tipo: 'usuario'; fila: UsuarioFila | null }
  | { tipo: 'estado'; fila: UsuarioFila }
  | { tipo: 'reset'; fila: UsuarioFila }
  | null;

export const UsuariosPage: React.FC = () => {
  const { user } = useAuth();

  const [filas, setFilas] = useState<UsuarioFila[]>([]);
  const [roles, setRoles] = useState<RolSimple[]>([]);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [cargando, setCargando] = useState(true);
  const [procesandoId, setProcesandoId] = useState<number | null>(null);
  const [modal, setModal] = useState<ModalAbierto>(null);
  const [aviso, setAviso] = useState<{ texto: string; tono: 'ok' | 'error' } | null>(null);

  // El texto del buscador y el valor que se manda al backend NO son lo
  // mismo. Se escribe en `busqueda` y 300 ms después de dejar de
  // escribir se copia a `busquedaAplicada`, que es la que dispara la
  // petición. Sin esa separación, cada tecla genera un `GET` y el
  // backend recibe trece búsquedas para escribir "administrador".
  const [busqueda, setBusqueda] = useState('');
  const [busquedaAplicada, setBusquedaAplicada] = useState('');
  const [filtroActivo, setFiltroActivo] = useState<'todos' | 'activos' | 'inactivos'>('todos');
  const [filtroRol, setFiltroRol] = useState('');

  // Un `useRef` para saber si ya hubo una respuesta pendiente, en vez de
  // comparar en el `useEffect`: comparar estado contra estado en un
  // efecto es la forma más corta de meterse en un bucle de peticiones.
  const peticionRef = useRef(0);

  // Contador de refresco. Sube solo cuando hay que volver a pedir la
  // página actual, por ejemplo tras un alta. Está en las dependencias del
  // efecto de carga, y eso evita tener un `cargar()` suelto que otro
  // efecto tendría que invocar.
  const [refresco, setRefresco] = useState(0);

  useEffect(() => {
    const temporizador = window.setTimeout(() => {
      setBusquedaAplicada(busqueda.trim());
      // Un filtro nuevo casi siempre invalida la página 5. Volver a la
      // primera evita quedarse en un "vacío" que no es real: la página 5
      // del filtro viejo era la única que tenía cosas.
      setPagina(1);
    }, RETRASO_BUSQUEDA);

    return () => window.clearTimeout(temporizador);
  }, [busqueda]);

  /**
   * La carga vive ENTERA dentro del efecto, sin un `cargar()` aparte.
   *
   * Hay dos razones y ninguna es estética. La primera es que llamar a un
   * `useCallback` desde el efecto sigue siendo un `setState` síncrono en el
   * cuerpo del efecto, que es justo lo que la regla de React 19 marca como
   * re-render en cascada. La segunda es que así se ve de un vistazo que
   * cada cambio de filtro dispara exactamente una petición.
   *
   * `vigente` cancela la respuesta si el efecto se limpió antes de que
   * llegara: sin eso, una búsqueda lenta que llega después de una rápida
   * pisa la tabla con resultados viejos.
   */
  useEffect(() => {
    let vigente = true;
    const numeroPeticion = ++peticionRef.current;

    usuariosService
      .listar({
        search: busquedaAplicada || undefined,
        activo: filtroActivo === 'todos' ? undefined : filtroActivo === 'activos',
        id_rol: filtroRol ? Number(filtroRol) : undefined,
        page: pagina,
        ordering: 'nombre_usuario',
      })
      .then((respuesta) => {
        if (!vigente || numeroPeticion !== peticionRef.current) return;
        setFilas(respuesta.results);
        setTotal(respuesta.count);
      })
      .catch((fallo: unknown) => {
        if (!vigente || numeroPeticion !== peticionRef.current) return;
        const normalizado = normalizarErrorApi(fallo);
        setAviso({
          texto: normalizado.mensaje ?? 'No se pudo cargar el listado de usuarios.',
          tono: 'error',
        });
        setFilas([]);
        setTotal(0);
      })
      .finally(() => {
        if (!vigente || numeroPeticion !== peticionRef.current) return;
        // El esqueleto solo aparece en la PRIMERA carga. Al cambiar un
        // filtro la tabla se reemplaza en el sitio: es más rápido y no
        // hace parpadear toda la pantalla para volver a mostrar lo mismo
        // con dos filas distintas.
        setCargando(false);
      });

    return () => {
      vigente = false;
    };
  }, [busquedaAplicada, filtroActivo, filtroRol, pagina, refresco]);

  // Los roles se piden una vez y no en cada cambio de filtro: son
  // cuatro filas y no cambian mientras la pantalla esté abierta.
  useEffect(() => {
    usuariosService
      .listarRoles()
      .then(setRoles)
      .catch(() => setRoles([]));
  }, []);

  // El aviso de éxito se va solo. El de error no: un error que desaparece
  // solo deja a la persona creyendo que la operación sí se hizo.
  useEffect(() => {
    if (!aviso || aviso.tono !== 'ok') return;
    const temporizador = window.setTimeout(() => setAviso(null), 5000);
    return () => window.clearTimeout(temporizador);
  }, [aviso]);

  const hayFiltros = busquedaAplicada !== '' || filtroActivo !== 'todos' || filtroRol !== '';

  const limpiarFiltros = () => {
    setBusqueda('');
    setBusquedaAplicada('');
    setFiltroActivo('todos');
    setFiltroRol('');
    setPagina(1);
  };

  const totalPaginas = Math.max(1, Math.ceil(total / 10));

  /** Reemplaza la fila editada o devuelve la lista a pedir. */
  const sustituirFila = useCallback((filaNueva: UsuarioFila) => {
    setFilas((previas) =>
      previas.map((fila) => (fila.id_usuario === filaNueva.id_usuario ? filaNueva : fila))
    );
  }, []);

  /**
   * Una alta puede caer en la página 3 si el listado está ordenado por
   * nombre y el nombre nuevo cae alfabéticamente lejos. Pedir la página 1
   * es lo simple; la alternativa es un insert en la posición correcta
   * que casi siempre está en otra página y produce un "no aparece" que
   * parece un fallo del guardado.
   */
  const trasAlta = useCallback(() => {
    setPagina(1);
    setRefresco((n) => n + 1);
  }, []);

  /**
   * Tras una EDICIÓN se vuelve a pedir la página, aunque la fila editada se
   * pueda corregir en el sitio. Es una petición más, a cambio de no mentir.
   *
   * La tentación es la contraria: guardar la fila devuelta con el servidor y
   * listo. El problema es que la edición puede haber movido al usuario fuera
   * de la tabla que se está viendo. Si se filtró por rol "Panadero" y el
   * usuario pasó a "Administrador", esa fila ya no pertenece a la página
   * actual, pero seguiría en pantalla hasta el próximo cambio de página: la
   * tabla contradiciendo al servidor. Con búsqueda activa, lo mismo con el
   * nombre. Y el listado viene ordenado por `nombre_usuario`, así que aunque
   * no haya filtros, corregir la fila en el sitio la dejaría fuera de orden.
   *
   * NO se corrige comprobando en el cliente si la fila sigue cumpliendo el
   * filtro, aunque parecería más barato. El backend busca con `icontains` de
   * Django sobre una collation de PostgreSQL que resuelve los acentos de otra
   * forma que `String.toLowerCase()`: "Ángel" y "angel" coinciden en la base y
   * no en el navegador. Reimplementar el filtro acá garantiza que un día los
   * dos digan cosas distintas. Un GET extra al terminar de guardar es barato;
   * un filtro desincronizado es un bug que no se ve.
   */
  const trasEdicion = useCallback(() => {
    setRefresco((n) => n + 1);
  }, []);

  const cambiarEstado = useCallback(
    async (fila: UsuarioFila, motivo: string) => {
      setProcesandoId(fila.id_usuario);
      try {
        const actualizada = await usuariosService.cambiarEstado(fila.id_usuario, {
          activo: !fila.activo,
          motivo,
        });
        sustituirFila(actualizada);
        return actualizada;
      } finally {
        setProcesandoId(null);
      }
    },
    [sustituirFila]
  );

  const desbloquear = useCallback(
    async (fila: UsuarioFila) => {
      setProcesandoId(fila.id_usuario);
      try {
        const respuesta = await usuariosService.desbloquear(fila.id_usuario);
        // El endpoint devuelve un texto, no la fila. El estado de bloqueo
        // sí cambió en el servidor, así que se corrige acá para que el
        // botón "Desbloquear" desaparezca sin volver a pedir la página.
        sustituirFila({
          ...fila,
          esta_bloqueado: false,
          minutos_bloqueo_restantes: 0,
        });
        return respuesta.message;
      } finally {
        setProcesandoId(null);
      }
    },
    [sustituirFila]
  );

  const esUsuarioActual = useCallback(
    (id: number) => user?.id_usuario === id,
    [user?.id_usuario]
  );

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <header>
        <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
          Gestión de usuarios
        </h1>
        <p className="mt-1 text-xs text-slate-500 sm:text-sm">
          CU3 · Crear cuentas, editarlas y activarlas o inactivarlas. Las cuentas no se borran: se
          inactivan para conservar el historial de ventas y producción.
        </p>
      </header>

      {aviso && (
        <div
          role="status"
          className={`rounded-xl border px-4 py-3 text-xs font-medium ${
            aviso.tono === 'ok'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : 'border-red-200 bg-red-50 text-red-800'
          }`}
        >
          {aviso.texto}
        </div>
      )}

      <Filtros
        busqueda={busqueda}
        onBusqueda={setBusqueda}
        filtroActivo={filtroActivo}
        onFiltroActivo={(valor) => {
          setFiltroActivo(valor);
          setPagina(1);
        }}
        filtroRol={filtroRol}
        onFiltroRol={(valor) => {
          setFiltroRol(valor);
          setPagina(1);
        }}
        roles={roles}
        hayFiltros={hayFiltros}
        onLimpiar={limpiarFiltros}
      />

      <UsuariosTabla
        filas={filas}
        cargando={cargando}
        procesandoId={procesandoId}
        onNuevo={() => setModal({ tipo: 'usuario', fila: null })}
        onEditar={(fila) => setModal({ tipo: 'usuario', fila })}
        onCambiarEstado={(fila) => setModal({ tipo: 'estado', fila })}
        onRestablecer={(fila) => setModal({ tipo: 'reset', fila })}
        onDesbloquear={async (fila) => {
          try {
            const mensaje = await desbloquear(fila);
            setAviso({ texto: mensaje, tono: 'ok' });
          } catch (fallo) {
            setAviso({
              texto: normalizarErrorApi(fallo).mensaje ?? 'No se pudo desbloquear la cuenta.',
              tono: 'error',
            });
          }
        }}
        esUsuarioActual={esUsuarioActual}
      />

      {totalPaginas > 1 && (
        <nav
          aria-label="Paginación del listado"
          className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white px-5 py-3"
        >
          <p className="text-[11px] text-slate-500">
            Página <span className="font-semibold text-slate-700">{pagina}</span> de{' '}
            <span className="font-semibold text-slate-700">{totalPaginas}</span> · {total}{' '}
            {total === 1 ? 'cuenta' : 'cuentas'} en total
          </p>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPagina((p) => Math.max(1, p - 1))}
              disabled={pagina === 1 || cargando}
              className="inline-flex min-h-11 items-center gap-1 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40 cursor-pointer"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              Anterior
            </button>
            <button
              type="button"
              onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
              disabled={pagina === totalPaginas || cargando}
              className="inline-flex min-h-11 items-center gap-1 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40 cursor-pointer"
            >
              Siguiente
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </nav>
      )}

      {modal?.tipo === 'usuario' && (
        <ModalUsuario
          key={`usuario-${modal.fila?.id_usuario ?? 'nuevo'}`}
          usuario={modal.fila}
          roles={roles}
          onCerrar={() => setModal(null)}
          onGuardado={() => (modal.fila ? trasEdicion() : trasAlta())}
          onExito={(texto) => setAviso({ texto, tono: 'ok' })}
          onError={(texto) => setAviso({ texto, tono: 'error' })}
          crear={(datos) => usuariosService.crear(datos)}
          editar={(id, datos: EditarUsuario) => usuariosService.editar(id, datos)}
        />
      )}

      {modal?.tipo === 'estado' && (
        <ModalEstado
          key={`estado-${modal.fila.id_usuario}`}
          usuario={modal.fila}
          onCerrar={() => setModal(null)}
          onConfirmar={(motivo) => cambiarEstado(modal.fila, motivo)}
          onExito={(texto) => setAviso({ texto, tono: 'ok' })}
          onError={(texto) => setAviso({ texto, tono: 'error' })}
        />
      )}

      {modal?.tipo === 'reset' && (
        <ModalRestablecerContrasena
          key={`reset-${modal.fila.id_usuario}`}
          usuario={modal.fila}
          onCerrar={() => setModal(null)}
          onConfirmar={async (nueva, confirmacion) => {
            const respuesta = await usuariosService.restablecerContrasena(modal.fila.id_usuario, {
              nueva_contrasena: nueva,
              confirmar_contrasena: confirmacion,
            });
            return respuesta.message;
          }}
          onExito={(texto) => setAviso({ texto, tono: 'ok' })}
          onError={(texto) => setAviso({ texto, tono: 'error' })}
        />
      )}
    </div>
  );
};

/** Barra de búsqueda y filtros. Se separa para que la página no crezca. */
interface FiltrosProps {
  busqueda: string;
  onBusqueda: (valor: string) => void;
  filtroActivo: 'todos' | 'activos' | 'inactivos';
  onFiltroActivo: (valor: 'todos' | 'activos' | 'inactivos') => void;
  filtroRol: string;
  onFiltroRol: (valor: string) => void;
  roles: RolSimple[];
  hayFiltros: boolean;
  onLimpiar: () => void;
}

const Filtros: React.FC<FiltrosProps> = ({
  busqueda,
  onBusqueda,
  filtroActivo,
  onFiltroActivo,
  filtroRol,
  onFiltroRol,
  roles,
  hayFiltros,
  onLimpiar,
}) => (
  <div className="rounded-2xl border border-slate-200 bg-white p-4">
    <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
      <div className="flex-1">
        <label htmlFor="buscar-usuarios" className="mb-1.5 block text-xs font-semibold text-slate-700">
          Buscar
        </label>
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            aria-hidden="true"
          />
          <input
            id="buscar-usuarios"
            type="search"
            value={busqueda}
            onChange={(e) => onBusqueda(e.target.value)}
            placeholder="Nombre, usuario o correo..."
            aria-describedby="ayuda-buscar"
            className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pl-10 pr-3.5 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:border-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-200"
          />
        </div>
        <p id="ayuda-buscar" className="mt-1.5 text-[11px] text-slate-500">
          La búsqueda distingue mayúsculas y minúsculas en la base de datos.
        </p>
      </div>

      <div className="lg:w-48">
        <label htmlFor="filtro-rol" className="mb-1.5 block text-xs font-semibold text-slate-700">
          Rol
        </label>
        <select
          id="filtro-rol"
          value={filtroRol}
          onChange={(e) => onFiltroRol(e.target.value)}
          className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 transition-colors focus:border-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-200 cursor-pointer"
        >
          <option value="">Todos los roles</option>
          {roles.map((rol) => (
            <option key={rol.id_rol} value={rol.id_rol}>
              {rol.nombre}
            </option>
          ))}
        </select>
      </div>

      <div className="lg:w-auto">
        <span className="mb-1.5 block text-xs font-semibold text-slate-700">Estado</span>
        <div
          role="group"
          aria-label="Filtrar por estado de la cuenta"
          className="flex rounded-xl border border-slate-300 p-1"
        >
          {(
            [
              { valor: 'todos', texto: 'Todos' },
              { valor: 'activos', texto: 'Activos' },
              { valor: 'inactivos', texto: 'Inactivos' },
            ] as const
          ).map((opcion) => (
            <button
              key={opcion.valor}
              type="button"
              onClick={() => onFiltroActivo(opcion.valor)}
              aria-pressed={filtroActivo === opcion.valor}
              className={`min-h-9 flex-1 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 cursor-pointer ${
                filtroActivo === opcion.valor
                  ? 'bg-amber-600 text-white'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              {opcion.texto}
            </button>
          ))}
        </div>
      </div>

      {hayFiltros && (
        <button
          type="button"
          onClick={onLimpiar}
          className="inline-flex min-h-11 items-center justify-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 cursor-pointer"
        >
          <X className="h-3.5 w-3.5" aria-hidden="true" />
          Limpiar
        </button>
      )}
    </div>
  </div>
);

export default UsuariosPage;
