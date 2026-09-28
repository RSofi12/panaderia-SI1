import React from 'react';
import { Check, X } from 'lucide-react';
import { evaluarReglas } from '../politicaContrasena';

/**
 * Checklist vivo de la política de contraseñas.
 *
 * Este archivo exporta SOLO el componente. Los predicados viven en
 * `../politicaContrasena`, porque un archivo que exporta componentes y
 * además funciones sueltas rompe el Fast Refresh de Vite: recarga la
 * página entera en vez de intercambiar el componente.
 *
 * POR QUÉ EXISTE ESTE COMPONENTE
 * `ContrasenaDebilError` devuelve 400 con la lista de reglas incumplidas,
 * o sea que el backend ya explica el error. Pero solo lo hace DESPUÉS de
 * que la persona apretó enviar y esperó la respuesta de la red. Con el
 * checklist, las reglas se leen mientras escribe, y el 400 pasa a ser la
 * confirmación de algo que ya sabía.
 *
 * POR QUÉ DICE QUE NO ES TODA LA POLÍTICA
 * `AUTH_PASSWORD_VALIDATORS` tiene CUATRO validadores, no uno. Además del
 * `ComplexPasswordValidator` están `CommonPasswordValidator` (rechaza unas
 * 20.000 contraseñas filtradas) y `UserAttributeSimilarityValidator`
 * (rechaza contraseñas parecidas al nombre de usuario). Los dos últimos
 * dependen de información que el navegador no tiene: una lista de 20.000
 * contraseñas o el nombre de usuario del servidor. Presentarlos como
 * "contraseña válida" sería mentir, así que el componente dice
 * explícitamente que el servidor revisa además esas dos cosas.
 *
 * Lo usan las tres pantallas que aceptan una contraseña nueva: el
 * restablecimiento del CU2 y, en el CU3, el alta de cuenta y el
 * restablecimiento administrativo.
 */
export const PasswordRequirements: React.FC<{
  contrasena: string;
  /** Muestra el checklist aunque la contraseña esté vacía. */
  visiblePorDefecto?: boolean;
}> = ({ contrasena, visiblePorDefecto = false }) => {
  // Con la contraseña vacía el checklist no aporta nada y asusta de
  // entrada: cuatro rojas antes de que la persona haya escrito una letra.
  // Aparece cuando ya se está escribiendo, o cuando el campo recibió el
  // foco.
  const hayAlgo = contrasena.length > 0;
  if (!hayAlgo && !visiblePorDefecto) return null;

  const reglas = evaluarReglas(contrasena);
  const todasOk = reglas.every((r) => r.cumplida);

  return (
    <div className="mt-2.5 rounded-xl border border-slate-200 bg-slate-50 p-3">
      <ul className="space-y-1.5">
        {reglas.map((regla) => (
          <li
            key={regla.texto}
            className={`flex items-center gap-2 text-[11px] transition-colors ${
              regla.cumplida ? 'text-emerald-700' : 'text-slate-500'
            }`}
          >
            {regla.cumplida ? (
              <Check className="h-3.5 w-3.5 flex-shrink-0" />
            ) : (
              <X className="h-3.5 w-3.5 flex-shrink-0 text-slate-300" />
            )}
            <span>{regla.texto}</span>
          </li>
        ))}
      </ul>

      {todasOk && (
        <p className="mt-2 border-t border-slate-200 pt-2 text-[10px] leading-relaxed text-slate-500">
          Cumplís las reglas de formato. El servidor además rechaza contraseñas
          muy comunes y las que se parecen a tu nombre de usuario: eso se
          verifica al enviar, no se puede calcular en el navegador.
        </p>
      )}
    </div>
  );
};

export default PasswordRequirements;
