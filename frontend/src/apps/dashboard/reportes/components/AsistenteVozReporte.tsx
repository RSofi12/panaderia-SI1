import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle, Download, Loader2, Mic, MicOff } from 'lucide-react';
import { EncabezadoCasoUso } from './EncabezadoCasoUso';
import { analizarConsultaVoz } from '../../../../services/reporteVozService';
import type {
  AnalisisVozReporte,
  CasoUsoReporte,
  ContextoDescargaAsistente,
} from '../../../../types/reporteVoz';

interface AsistenteVozReporteProps {
  cuActual?: CasoUsoReporte;
  onAnalisis: (resultado: AnalisisVozReporte) => Promise<void>;
  onDescargar: (formato: 'pdf' | 'csv' | 'excel', ctx: ContextoDescargaAsistente) => Promise<void>;
  descargando?: string;
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
  'Reporte de roles y usuarios activos',
  'Analiza las ventas de octubre en efectivo',
  '¿Qué productos se vendieron más esta semana?',
  'Resumen de producción del mes',
];

function sinMarkdown(texto: string): string {
  return texto
    .split('\n')
    .map((linea) => {
      let frag = linea.trim();
      frag = frag.replace(/^#{1,6}\s*/, '');
      frag = frag.replace(/\*\*([^*]+)\*\*/g, '$1');
      frag = frag.replace(/\*([^*]+)\*/g, '$1');
      frag = frag.replace(/^\*\s+/, '• ');
      frag = frag.replace(/^\-\s+/, '• ');
      frag = frag.replace(/\*\*/g, '');
      return frag;
    })
    .join('\n');
}

function parrafosAnalisis(texto: string): string[] {
  return sinMarkdown(texto)
    .split(/\n+/)
    .map((p) => p.trim())
    .filter(Boolean);
}

export const AsistenteVozReporte: React.FC<AsistenteVozReporteProps> = ({
  cuActual = 'CU21',
  onAnalisis,
  onDescargar,
  descargando = '',
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
  const [ultimo, setUltimo] = useState<AnalisisVozReporte | null>(null);
  const [contextoDescarga, setContextoDescarga] = useState<ContextoDescargaAsistente | null>(null);

  useEffect(() => {
    return () => {
      reconocimientoRef.current?.abort();
      reconocimientoRef.current = null;
    };
  }, []);

  useEffect(() => {
    setSoportaVoz(Boolean(obtenerReconocimiento()));
  }, []);

  const subtitulo = useMemo(
    () =>
      'Dictá o escribí una consulta y Gemini analizará los datos del período seleccionado.',
    [],
  );

  const ejecutarTexto = useCallback(
    async (entrada: string) => {
      const limpio = entrada.trim();
      if (!limpio) return;
      setError('');
      setProcesando(true);
      try {
        const resultado = await analizarConsultaVoz(limpio, cuActual);
        setUltimo(resultado);
        const cmd = resultado.comando?.filtros ?? {};
        const metodo = cmd.metodo_pago ?? '';
        setContextoDescarga({
          consulta: resultado.consulta,
          desde: resultado.desde,
          hasta: resultado.hasta,
          metodo,
          jornada: cmd.jornada || undefined,
          columnas: cmd.columnas ?? [],
          exportarVentas: resultado.exportar_ventas,
          exportarProduccion: resultado.exportar_produccion,
          analisis: resultado.analisis,
          tema: resultado.tema,
        });
        await onAnalisis(resultado);
      } catch (err: unknown) {
        const axiosErr = err as {
          response?: { data?: { texto?: string | string[]; detail?: string } };
        };
        const data = axiosErr.response?.data;
        const textoApi = data?.texto;
        const detalle =
          (Array.isArray(textoApi) ? textoApi.join(' ') : textoApi) ||
          data?.detail ||
          'No se pudo analizar la consulta. Verifica tu sesión y el backend.';
        setError(detalle);
      } finally {
        setProcesando(false);
      }
    },
    [cuActual, onAnalisis],
  );

  const finalizarEscucha = useCallback(
    (analizar: boolean) => {
      const final = transcripcionRef.current.trim();
      setEscuchando(false);
      setTranscripcion('');
      reconocimientoRef.current = null;
      if (final) {
        setTexto(final);
      }
      if (analizar && final) {
        void ejecutarTexto(final);
      } else if (!final && analizar) {
        setError('No se captó ninguna frase. Habla de nuevo y pulsa Detener al terminar.');
      }
      detenerManualRef.current = false;
    },
    [ejecutarTexto],
  );

  const iniciarEscucha = useCallback(() => {
    const Ctor = obtenerReconocimiento();
    if (!Ctor) {
      setError('Tu navegador no soporta reconocimiento de voz. Escribe la consulta abajo.');
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
      if (codigo === 'aborted') return;
      if (codigo === 'not-allowed' || codigo === 'service-not-allowed') {
        setError('El navegador bloqueó el micrófono. Permite el acceso en la barra de direcciones.');
      } else if (codigo === 'no-speech') {
        setAvisoVoz('No se oyó voz. Sigue hablando o pulsa Detener cuando termines.');
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
        setAvisoVoz('La escucha se cortó. Revisa el texto y pulsa Analizar, o vuelve a Hablar.');
        setTexto(restante);
      }
      setEscuchando(false);
      reconocimientoRef.current = null;
    };

    try {
      instancia.start();
      setEscuchando(true);
      setAvisoVoz('Escuchando… al terminar pulsa Detener.');
    } catch {
      setError('No se pudo iniciar el micrófono. Usa HTTPS o localhost.');
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

  const motorEtiqueta = ultimo?.motor === 'gemini' ? 'Gemini' : 'Análisis local';

  return (
    <section
      className={`overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xs ${className}`}
      aria-label="CU27 Generar reportes por voz"
    >
      <div className="px-4 py-4 sm:px-5">
        <EncabezadoCasoUso
          cu="CU27"
          titulo="Generar reportes por voz"
          descripcion={subtitulo}
        />
      </div>

      <div className="space-y-3 p-4 sm:p-5">
        <form
          className="flex flex-col gap-2 sm:flex-row sm:items-stretch"
          onSubmit={(e) => {
            e.preventDefault();
            void ejecutarTexto(texto);
          }}
        >
          <div className="flex flex-1 gap-2">
            <button
              type="button"
              onClick={() => void toggleMicrofono()}
              disabled={procesando}
              aria-pressed={escuchando}
              aria-label={escuchando ? 'Detener micrófono' : 'Hablar consulta'}
              className={`inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-xl text-white shadow-md transition-colors disabled:opacity-60 ${
                escuchando ? 'bg-rose-600 hover:bg-rose-700' : 'bg-indigo-600 hover:bg-indigo-700'
              }`}
            >
              {procesando ? (
                <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
              ) : escuchando ? (
                <MicOff className="h-5 w-5" aria-hidden="true" />
              ) : (
                <Mic className="h-5 w-5" aria-hidden="true" />
              )}
            </button>
            <input
              type="text"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Dictá o escribí tu consulta. Ej: ¿Cuánto se vendió este mes?"
              className="min-h-11 flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              maxLength={800}
              aria-label="Consulta de reporte"
            />
          </div>
          <button
            type="submit"
            disabled={procesando || !texto.trim()}
            className="min-h-11 rounded-xl bg-violet-600 px-5 text-sm font-bold text-white hover:bg-violet-700 disabled:opacity-50"
          >
            {procesando ? 'Analizando…' : 'Analizar'}
          </button>
        </form>

        {!soportaVoz ? (
          <p className="text-[11px] text-amber-800">Sin micrófono: escribe la consulta en el campo.</p>
        ) : null}

        {transcripcion && escuchando ? (
          <p className="text-xs italic text-slate-500">«{transcripcion}»</p>
        ) : null}
        {avisoVoz ? <p className="text-xs font-medium text-indigo-800">{avisoVoz}</p> : null}

        <div className="flex flex-wrap gap-2">
          {SUGERENCIAS.map((sugerencia) => (
            <button
              key={sugerencia}
              type="button"
              className="rounded-full border border-indigo-200 bg-indigo-50/50 px-2.5 py-1 text-[11px] font-medium text-indigo-900 hover:bg-indigo-100"
              onClick={() => {
                setTexto(sugerencia);
                void ejecutarTexto(sugerencia);
              }}
            >
              {sugerencia}
            </button>
          ))}
        </div>

        {error ? (
          <div className="flex items-center gap-2 text-xs text-rose-700">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        ) : null}

        {ultimo ? (
          <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-[11px] font-bold uppercase tracking-wider text-indigo-800">
                Análisis de {motorEtiqueta}
              </p>
              <span className="rounded-md bg-white px-2 py-0.5 text-[11px] font-semibold text-slate-700 shadow-2xs">
                {ultimo.desde} → {ultimo.hasta}
              </span>
            </div>
            <div className="mt-3 space-y-2 text-sm leading-relaxed text-slate-800">
              {parrafosAnalisis(ultimo.analisis).map((parrafo) => (
                <p key={parrafo.slice(0, 48)}>{parrafo}</p>
              ))}
            </div>

            {contextoDescarga ? (
              <div className="mt-4 border-t border-slate-200 pt-3">
                <p className="mb-2 flex items-center gap-1 text-[11px] font-bold uppercase tracking-wide text-slate-600">
                  <Download className="h-3.5 w-3.5" aria-hidden="true" />
                  Descargar reporte completo
                </p>
                <div className="flex flex-wrap gap-2">
                  {(['excel', 'pdf', 'csv'] as const).map((formato) => (
                    <button
                      key={formato}
                      type="button"
                      disabled={Boolean(descargando)}
                      onClick={() => void onDescargar(formato, contextoDescarga)}
                      className="min-h-10 rounded-lg border border-slate-300 bg-white px-4 text-xs font-bold uppercase tracking-wide text-slate-800 hover:bg-slate-50 disabled:opacity-50"
                    >
                      {descargando === formato ? '…' : formato}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
};

export default AsistenteVozReporte;