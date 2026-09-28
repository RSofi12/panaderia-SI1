/* ------------------------------------------------------------------ *
 * Política de contraseñas evaluada en el navegador
 * ------------------------------------------------------------------ *
 *
 * POR QUÉ VIVE FUERA DE `PasswordRequirements.tsx`
 * Estaba dentro, y el linter lo marcaba con
 * `react-refresh/only-export-components`: un archivo que exporta un
 * componente y además funciones sueltas hace que Vite recargue la página
 * entera en vez de intercambiar el componente. No es un error de estilo,
 * es una regla de Vite sobre cómo se recarga cada módulo.
 *
 * El CU3 reutiliza este módulo tal cual: el modal de alta de cuenta
 * muestra el mismo checklist que el formulario de recuperación del CU2,
 * y las reglas no se escriben dos veces.
 *
 * POR QUÉ ESTO NO ES LA FUENTE DE VERDAD
 * El predicado se escribe acá y no se importa del backend porque son dos
 * lenguajes distintos. Lo que se busca es que la lista sea legible, no
 * que sea autoritativa. La fuente de verdad SIEMPRE es el backend: si
 * estas reglas se desincronizan de `ComplexPasswordValidator` y el
 * servidor termina rechazando una contraseña que acá aparece como válida,
 * lo que se rompe es la experiencia de la persona, pero la cuenta sigue
 * protegida.
 */

/** Regla de la política, ya evaluada contra lo que la persona escribió. */
export interface ReglaContrasena {
  /** Se cumple con la contraseña escrita hasta ahora. */
  cumplida: boolean;
  /** Texto de la regla, tal como lo vería la persona. */
  texto: string;
}

/**
 * Las cuatro reglas que el backend sí deja verificar en el cliente.
 *
 * Reproducen `ComplexPasswordValidator` (ver
 * `users/password_validators.py`): mínimo 8 caracteres, una mayúscula, un
 * número y un símbolo. El conjunto de símbolos sale de la misma expresión
 * regular del backend: `!@#$%^&*(),.?":{}|<>=_+-\\/[]`.
 */
export const evaluarReglas = (contrasena: string): ReglaContrasena[] => [
  { cumplida: contrasena.length >= 8, texto: 'Mínimo 8 caracteres' },
  { cumplida: /[A-Z]/.test(contrasena), texto: 'Al menos una letra mayúscula' },
  { cumplida: /\d/.test(contrasena), texto: 'Al menos un número' },
  {
    cumplida: /[!@#$%^&*(),.?":{}|<>=_+\-\\/[\]]/.test(contrasena),
    texto: 'Al menos un símbolo (!@#$%^&*-_+=)',
  },
];

/** `true` cuando se cumplen las cuatro reglas verificables en el cliente. */
export const cumplePoliticaVisible = (contrasena: string): boolean =>
  evaluarReglas(contrasena).every((regla) => regla.cumplida);
