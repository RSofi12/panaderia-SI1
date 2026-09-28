import React from 'react';
import { ChefHat } from 'lucide-react';
import circleLogo from '../../../assets/circle-logo-panaderia.svg';

/**
 * Envoltura visual compartida por las pantallas públicas de Usuarios y
 * Seguridad: login (CU1), recuperar contraseña y restablecer contraseña (CU2).
 *
 * POR QUÉ EXISTE
 * La cabecera con el logo del panadero, el degradado ámbar y el pie con la
 * ciudad eran cuarenta líneas que vivían dentro de `LoginPage`. Con dos pantallas
 * nuevas para el CU2, copiarlo producía tres copias que divergían con el
 * tiempo: cambiar el color de marca obligaba a editar tres archivos, y en la
 * práctica se olvidaba una.
 *
 * NO es una abstracción preventiva. Las tres pantallas ya existían al momento
 * de sacarla, que es cuando una abstracción se justifica: cuando ya duele.
 *
 * Se conserva la estructura y las clases exactas del `LoginPage` original para
 * que el aspecto no cambie ni un píxel; lo único que se mueve es el `children`
 * del cuerpo, que cada pantalla controla.
 */
export const AuthCard: React.FC<{
  /** Título grande de la tarjeta. */
  titulo: string;
  /** Bajada en tono ámbar, debajo del título. */
  subtitulo: string;
  /** Cuerpo del formulario. */
  children: React.ReactNode;
}> = ({ titulo, subtitulo, children }) => {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-amber-50/60 via-slate-50 to-amber-100/40 p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl shadow-amber-900/5 border border-amber-100/80 overflow-hidden backdrop-blur-sm">
        {/* Cabecera con Logo e Identidad Visual */}
        <div className="pt-8 pb-4 px-8 text-center bg-gradient-to-b from-amber-50/70 to-transparent">
          <div className="relative inline-block mb-3">
            <div className="w-24 h-24 sm:w-28 sm:h-28 mx-auto rounded-full bg-white shadow-md p-1 border-2 border-amber-200/80 flex items-center justify-center transition-transform duration-300 hover:scale-105">
              <img
                src={circleLogo}
                alt="Logo Panadería Santiago"
                className="w-full h-full object-contain rounded-full"
              />
            </div>
            <div className="absolute -bottom-1 -right-1 bg-amber-600 text-white p-1.5 rounded-full shadow-sm">
              <ChefHat className="w-4 h-4" />
            </div>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            {titulo}
          </h1>
          <p className="text-xs sm:text-sm text-amber-800 font-medium mt-1">
            {subtitulo}
          </p>
        </div>

        {/* Cuerpo: cada pantalla pone aquí su formulario */}
        <div className="px-6 sm:px-8 pb-8 pt-2">{children}</div>

        {/* Pie de Página de la Tarjeta */}
        <div className="py-3 px-6 bg-slate-50 border-t border-slate-100 text-center text-[11px] text-slate-400">
          Panadería Santiago • Santa Cruz de la Sierra, Bolivia
        </div>
      </div>
    </div>
  );
};

export default AuthCard;
