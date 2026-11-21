import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle, Loader2, Mic, MicOff, Sparkles } from 'lucide-react';
import { interpretarComandoVoz } from '../../../../services/reporteVozService';
import type { CasoUsoReporte, ComandoVozInterpretado } from '../../../../types/reporteVoz';

interface AsistenteVozReporteProps {
  cuActual?: CasoUsoReporte;
  /** Si devuelve texto, ese mensaje se usa para la voz (p. ej. sin datos en el período). */
  onComando: (comando: ComandoVozInterpretado) => Promise<string | void> | string | void;
  className?: string;
}

interface ReconocimientoVoz extends EventTarget {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: { resultIndex: number; results: { length: number; [i: number]: { isFinal: boolean; 0: { transcript: string } } } }) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
}

type SpeechRecognitionCtor = new () => ReconocimientoVoz;

function obtenerReconocimiento(): SpeechRecognitionCtor | null {
  const w = window as Window & {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

const SUGERENCIAS = [
  'Descarga en PDF el reporte de ventas de este mes',
  'Exporta en Excel las ventas en efectivo de esta semana',
  'Muéstrame el reporte de ventas de hoy',
];

export const AsistenteVozReporte: React.FC<AsistenteVozReporteProps> = ({
  cuActual = 'CU21',
  onComando,
  className = '',
}) => {
  const reconocimientoRef = useRef<ReconocimientoVoz | null>(null);
  const transcripcionRef = useRef('');
  const detenerManualRef = useRef(false);
  const [soportaVoz, setSoportaVoz] = useState(false);
  const [escuchando, setEscuchando] = useState(false);
  const [procesando, setProcesando] = useState(false);
  const [texto, setTexto] = useState('');
  const [transcripcion, setTranscripcion] = useState('');
  const [error, setError] = useState('');
  const [avisoVoz, setAvisoVoz] = useState('');
  const [ultimo, setUltimo] = useState<ComandoVozInterpretado | null>(null);

  useEffect(() => {
    return () => {
      reconocimientoRef.current?.abort();
      reconocimientoRef.current = null;
    };
  }, []);

  useEffect(() => {
    setSoportaVoz(Boolean(obtenerReconocimiento()));
  }, []);

  const hablar = useCallback((mensaje: string) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(mensaje);
    u.lang = 'es-ES';
    window.speechSynthesis.speak(u);
  }, []);

  const ejecutarTexto = useCallback(
    async (entrada: string) => {
      const limpio = entrada.trim();
      if (!limpio) return;
      setError('');
      setProcesando(true);
      try {
        const comando = await interpretarComandoVoz(limpio, cuActual);
        setUltimo(comando);
        const mensajeVoz = (await onComando(comando)) ?? comando.respuesta_voz;
        setUltimo({ ...comando, respuesta_voz: mensajeVoz });
        hablar(mensajeVoz);
      } catch {
        setError('No se pudo interpretar el comando. Verifica tu sesión y el backend.');
      } finally {
        setProcesando(false);
      }
    },
    [cuActual, hablar, onComando],
  );

  const finalizarEscucha = useCallback(
    (interpretar: boolean) => {
      const final = transcripcionRef.current.trim();
      setEscuchando(false);
      setTranscripcion('');
      reconocimientoRef.current = null;
      if (final) {
        setTexto(final);
      }
      if (interpretar && final) {
        void ejecutarTexto(final);
      } else if (!final && interpretar) {
        setError('No se captó ninguna frase. Habla de nuevo y pulsa Detener al terminar.');
      }
      detenerManualRef.current = false;
    },
    [ejecutarTexto],
  );

  const iniciarEscucha = useCallback(() => {
    const Ctor = obtenerReconocimiento();
    if (!Ctor) {
      setError('Tu navegador no soporta reconocimiento de voz. Escribe el comando abajo.');
      return;
    }

    setError('');
    setAvisoVoz('');
    transcripcionRef.current = '';
    setTranscripcion('');
    detenerManualRef.current = false;

    const instancia = new Ctor();
    instancia.lang = 'es-ES';
    instancia.interimResults = true;
    instancia.continuous = true;
    instancia.maxAlternatives = 1;
    reconocimientoRef.current = instancia;

    instancia.onresult = (event) => {
      let acumulado = '';
      for (let i = 0; i < event.results.length; i += 1) {
        acumulado += event.results[i][0].transcript;
      }
      transcripcionRef.current = acumulado;
      setTranscripcion(acumulado);
    };

    instancia.onerror = (event) => {
      const codigo = event?.error ?? '';
      if (codigo === 'aborted') {
        return;
      }
      if (codigo === 'not-allowed' || codigo === 'service-not-allowed') {
        setError('El navegador bloqueó el micrófono. Permite el acceso en la barra de direcciones.');
      } else if (codigo === 'no-speech') {
        setAvisoVoz('No se oyó voz. Sigue hablando o pulsa Detener cuando termines.');
      } else if (codigo === 'network') {
        setError('El reconocimiento de voz necesita conexión a internet en Chrome/Edge.');
      } else {
        setError('No se pudo captar audio. Revisa permisos del micrófono.');
      }
      setEscuchando(false);
    };

    instancia.onend = () => {
      if (detenerManualRef.current) {
        finalizarEscucha(true);
        return;
      }
      const restante = transcripcionRef.current.trim();
      if (restante) {
        setAvisoVoz(
          'La escucha se cortó sola. Revisa el texto abajo y pulsa Interpretar, o vuelve a pulsar Hablar.',
        );
        setTexto(restante);
      }
      setEscuchando(false);
      reconocimientoRef.current = null;
    };

    try {
      instancia.start();
      setEscuchando(true);
      setAvisoVoz('Escuchando… di tu frase completa y pulsa Detener al finalizar.');
    } catch {
      setError('No se pudo iniciar el micrófono. Usa HTTPS o localhost y permite el permiso.');
    }
  }, [finalizarEscucha]);

  const toggleMicrofono = useCallback(() => {
    if (escuchando && reconocimientoRef.current) {
      detenerManualRef.current = true;
      reconocimientoRef.current.stop();
      return;
    }
    iniciarEscucha();
  }, [escuchando, iniciarEscucha]);

  const etiquetaEstado = useMemo(() => {
    if (procesando) return 'Interpretando con Gemini o reglas locales…';
    if (escuchando) return 'Escuchando… pulsa Detener cuando acabes de hablar';
    return 'Pide un reporte por voz o escribe el comando';
  }, [escuchando, procesando]);

  return (
    <section
      className={`rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50/80 to-white p-4 shadow-2xs ${className}`}
      aria-label="Asistente de reportes por voz"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-indigo-800">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            Comando por voz (CU21–CU25)
          </p>
          <p className="mt-1 text-xs text-slate-600">{etiquetaEstado}</p>
        </div>
        <button
          type="button"
          onClick={() => void toggleMicrofono()}
          disabled={procesando}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold text-white shadow-md transition-colors disabled:opacity-60 ${
            escuchando
              ? 'bg-rose-600 hover:bg-rose-700'
              : 'bg-indigo-600 hover:bg-indigo-700'
          }`}
        >
          {procesando ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : escuchando ? (
            <MicOff className="h-4 w-4" aria-hidden="true" />
          ) : (
            <Mic className="h-4 w-4" aria-hidden="true" />
          )}
          {escuchando ? 'Detener' : 'Hablar'}
        </button>
      </div>

      {!soportaVoz ? (
        <p className="mt-2 text-[11px] text-amber-800">
          Sin micrófono en este navegador: usa el campo de texto.
        </p>
      ) : null}

      <form
        className="mt-3 flex flex-col gap-2 sm:flex-row"
        onSubmit={(e) => {
          e.preventDefault();
          void ejecutarTexto(texto);
        }}
      >
        <input
          type="text"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder='Ej. "Descarga en PDF las ventas de octubre en efectivo"'
          className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          maxLength={500}
          aria-label="Comando de reporte por texto"
        />
        <button
          type="submit"
          disabled={procesando || !texto.trim()}
          className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
        >
          Interpretar
        </button>
      </form>

      {transcripcion && escuchando ? (
        <p className="mt-2 text-xs italic text-slate-500">«{transcripcion}»</p>
      ) : null}

      {avisoVoz ? (
        <p className="mt-2 text-xs font-medium text-indigo-800">{avisoVoz}</p>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        {SUGERENCIAS.map((sugerencia) => (
          <button
            key={sugerencia}
            type="button"
            className="rounded-full border border-indigo-200 bg-white px-2.5 py-1 text-[11px] font-medium text-indigo-900 hover:bg-indigo-50"
            onClick={() => {
              setTexto(sugerencia);
              void ejecutarTexto(sugerencia);
            }}
          >
            {sugerencia}
          </button>
        ))}
      </div>

      {ultimo ? (
        <p className="mt-3 text-xs text-slate-700">
          <span className="font-bold">{ultimo.caso_uso}</span> ·{' '}
          {ultimo.requiere_seleccion_formato ? 'elige formato abajo' : ultimo.formato.toUpperCase()} · motor{' '}
          {ultimo.motor}
          {!ultimo.modulo_disponible ? (
            <span className="ml-1 font-semibold text-amber-800">(módulo aún no integrado en pantalla)</span>
          ) : null}
        </p>
      ) : null}

      {error ? (
        <div className="mt-2 flex items-center gap-2 text-xs text-rose-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      ) : null}
    </section>
  );
};

export default AsistenteVozReporte;