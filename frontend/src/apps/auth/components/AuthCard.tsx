import React from 'react';
import circleLogo from '../../../assets/circle-logo-panaderia.svg';

/**
 * Envoltura visual compartida por las pantallas públicas de Usuarios y
 * Seguridad: login (CU1), recuperar contraseña y restablecer contraseña (CU2).
 *
 * Muestra el logo oficial con borde blanco circular limpio y la identidad
 * visual corporativa de la Panadería Santiago.
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
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl shadow-amber-950/5 border border-amber-100/80 overflow-hidden backdrop-blur-sm">
        {/* Cabecera con Logo e Identidad Visual */}
        <div className="pt-8 pb-3 px-8 text-center bg-gradient-to-b from-amber-50/60 to-transparent">
          <div className="inline-block mb-3">
            <div className="w-20 h-20 sm:w-24 sm:h-24 mx-auto rounded-full bg-white shadow-md p-1.5 border-4 border-white flex items-center justify-center transition-transform duration-300 hover:scale-105">
              <img
                src={circleLogo}
                alt="Logo Panadería Santiago"
                className="w-full h-full object-contain rounded-full"
              />
            </div>
          </div>

          <h1 className="font-sugo text-2xl sm:text-3xl text-slate-900 tracking-wide">
            {titulo}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            {subtitulo}
          </p>
        </div>

        {/* Cuerpo: cada pantalla pone aquí su formulario */}
        <div className="px-6 sm:px-8 pb-8 pt-3">{children}</div>

        {/* Pie de Página de la Tarjeta */}
        <div className="py-3 px-6 bg-slate-50 border-t border-slate-100 text-center text-[11px] text-slate-400">
          Panadería Santiago • Santa Cruz de la Sierra, Bolivia
        </div>
      </div>
    </div>
  );
};

export default AuthCard;
