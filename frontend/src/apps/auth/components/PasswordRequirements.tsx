import React from 'react';
import { Check, X } from 'lucide-react';

/**
 * Regla de la política de contraseñas, evaluada en el navegador.
 *
 * El predicado se escribe acá y no se importa del backend porque son dos
 * lenguajes distintos; lo que se busca es que la lista sea legible, no que sea
 * la fuente de verdad. La fuente de verdad SIEMPRE es el backend: si estas
 * reglas se desincronizan de `ComplexPasswordValidator` y el servidor termina
 * rechazando una contraseña que acá aparece como válida, lo que se rompe es la
 * experiencia de la persona, pero el backend sigue protegiendo la cuenta.
 */
export interface ReglaContrasena {
  /** Se cumple con la contraseña escrita hasta ahora. */
  cumplida: boolean;
  /** Texto de la regla, tal como lo vería la persona. */
  texto: string;
}

/**
 * Evalúa las cuatro reglas que el backend sí deja verificar en el cliente.
 *
 * Reproducen `ComplexPasswordValidator` (ver
 * `users/password_validators.py`): mínimo 8 caracteres, una mayúscula, un
 * número y un símbolo. El conjunto de símbolos sale de la misma expresión
 * regular del backend: `!@#$%^&*(),.?":{}|<>=_+-\\\/[]`.
 */
export const evaluarReglas = (contrasena: string): ReglaContrasena[] => {
  return [
    { cumplida: contrasena.length >= 8, texto: 'Mínimo 8 caracteres' },
    { cumplida: /[A-Z]/.test(contrasena), texto: 'Al menos una letra mayúscula' },
    { cumplida: /\d/.test(contrasena), texto: 'Al menos un número' },
    {
      cumplida: /[!@#$%^&*(),.?":{}|<>=_+\-\\\/[\]]/.test(contrasena),
      texto: 'Al menos un símbolo (!@#$%^&*-_+=)',
    },
  ];
};

/** `true` cuando se cumplen las cuatro reglas verificables en el cliente. */
export const cumplePoliticaVisible = (contrasena: string): boolean =>
  evaluarReglas(contrasena).every((regla) => regla.cumplida);

/**
 * Checklist vivo de la política de contraseñas.
 *
 * POR QUÉ EXISTE
 * `ContrasenaDebilError` devuelve 400 con la lista de reglas incumplidas, o sea
 * que el backend ya explica el error. Pero solo lo hace DESPUÉS de que la
 * persona apretó enviar y esperó la respuesta de la red. Con el checklist, las
 * reglas se leen mientras escribe, y el 400 pasa a ser la confirmación de algo
 * que ya sabía.
 *
 * POR QUÉ DICE QUE NO ES TODA LA POLÍTICA
 * `AUTH_PASSWORD_VALIDATORS` tiene CUATRO validadores, no uno. Además del
 * `ComplexPasswordValidator` están `CommonPasswordValidator` (rechaza unas
 * 20.000 contraseñas filtradas) y `UserAttributeSimilarityValidator` (rechaza
 * contraseñas parecidas al nombre de usuario). Los dos últimos dependen de
 * información que el navegador no tiene: una lista de 20.000 contraseñas o el
 * nombre de usuario del servidor. Presentarlos como "contraseña válida" sería
 * mentir, así que el componente dice explícitamente que el servidor revisa
 * además esas dos cosas.
 */
export const PasswordRequirements: React.FC<{
  contrasena: string;
  /** Muestra el checklist aunque la contraseña esté vacía. */
  visiblePorDefecto?: boolean;
}> = ({ contrasena, visiblePorDefecto = false }) => {
  // Con la contraseña vacía el checklist no aporta nada y asusta de entrada:
  // cuatro rojas antes de que la persona haya escrito una letra. Aparece
  // cuando ya se está escribiendo, o cuando el campo recibió el foco.
  const hayAlgo = contrasena.length > 0;
  if (!hayAlgo && !visiblePorDefecto) return null;

  const reglas = evaluarReglas(contrasena);
  const todasOk = reglas.every((r) => r.cumplida);

  return (
    <div className="mt-2.5 p-3 bg-slate-50 border border-slate-200 rounded-xl">
      <ul className="space-y-1.5">
        {reglas.map((regla) => (
          <li
            key={regla.texto}
            className={`flex items-center gap-2 text-[11px] transition-colors ${
              regla.cumplida ? 'text-emerald-700' : 'text-slate-500'
            }`}
          >
            {regla.cumplida ? (
              <Check className="w-3.5 h-3.5 flex-shrink-0" />
            ) : (
              <X className="w-3.5 h-3.5 flex-shrink-0 text-slate-300" />
            )}
            <span>{regla.texto}</span>
          </li>
        ))}
      </ul>

      {todasOk && (
        <p className="mt-2 pt-2 border-t border-slate-200 text-[10px] leading-relaxed text-slate-500">
          Cumplís las reglas de formato. El servidor además rechaza contraseñas
          muy comunes y las que se parecen a tu nombre de usuario: eso se
          verifica al enviar, no se puede calcular en el navegador.
        </p>
      )}
    </div>
  );
};

export default PasswordRequirements;
