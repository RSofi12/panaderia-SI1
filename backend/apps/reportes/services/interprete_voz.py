"""
Intérprete de comandos de voz/texto para reportes CU21–CU25 (Gemini + fallback local).

No persiste datos: solo traduce lenguaje natural a un JSON estructurado que el
frontend (o futuros endpoints) pueden ejecutar.
"""
from __future__ import annotations

import json
import re
from calendar import monthrange
from datetime import date, timedelta
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

CASOS_USO = ('CU21', 'CU22', 'CU23', 'CU24', 'CU25')
FORMATOS = ('pdf', 'csv', 'excel', 'pantalla')
MODULOS_DISPONIBLES = frozenset({'CU21', 'CU22', 'CU25'})

_PROMPT_SISTEMA = """Eres el asistente de reportes de la Panadería Santiago (Bolivia).
Traduce el comando del usuario a JSON estricto.

Casos de uso (prioriza el que mejor encaje; consultas de roles/usuarios siguen siendo CU21 para período pero el análisis puede ser de seguridad):
- CU21: ventas, ingresos, facturación, comprobantes, tickets, roles, usuarios, cajeros
- CU22: producción, jornadas, horneado, pan producido
- CU23: existencias, inventario, stock, materia prima, productos terminados
- CU24: compras, proveedores, gastos, inversiones, egresos
- CU25: resultados económicos, utilidad, margen, balance, ganancias

Formatos: pdf, csv, excel, pantalla (solo ver en pantalla sin descargar).
Si pide descargar/exportar/generar archivo Y menciona el formato → accion=descargar y formato=pdf|csv|excel.
Si pide descargar pero NO dice el formato → accion=descargar, formato=pantalla, requiere_seleccion_formato=true.
Si solo pide ver o consultar → accion=consultar, formato=pantalla, requiere_seleccion_formato=false.

Filtros (solo los que apliquen):
- periodo: dia, semana, mes
- desde, hasta: YYYY-MM-DD (fecha actual de referencia abajo)
- Si menciona un año (ej. 2025 o 20250): desde=AAAA-01-01, hasta=AAAA-12-31 (todo el año)
- metodo_pago: efectivo, stripe o cadena vacía (solo CU21)
- jornada: Mañana, Tarde, Noche, unica o cadena vacía (solo CU22)
- columnas: lista opcional; CU21: comprobante, fecha, metodo, cajero, total; CU22: lote, fecha, jornada, responsable, unidades, costo

Responde SOLO JSON con las claves:
caso_uso, formato, accion, requiere_seleccion_formato (boolean), filtros (objeto),
respuesta_voz (frase corta en español; si falta formato, pregunta: PDF, CSV o Excel).
No afirmes que hay ventas ni que el archivo ya se generó; el sistema verifica los datos después.
"""


def _hoy() -> date:
    return timezone.localdate()


def _rango_mes(anio: int, mes: int) -> tuple[str, str]:
    ultimo = monthrange(anio, mes)[1]
    return (
        f'{anio}-{mes:02d}-01',
        f'{anio}-{mes:02d}-{ultimo:02d}',
    )


def _rango_semana(ref: date) -> tuple[str, str]:
    lunes = ref - timedelta(days=ref.weekday())
    domingo = lunes + timedelta(days=6)
    return lunes.isoformat(), domingo.isoformat()


def _filtros_vacios() -> dict[str, Any]:
    return {
        'periodo': None,
        'desde': None,
        'hasta': None,
        'metodo_pago': '',
        'jornada': '',
        'columnas': None,
    }


def _completar_fechas_filtros(filtros: dict[str, Any], texto: str) -> dict[str, Any]:
    """Gemini a veces omite desde/hasta; el análisis narrativo siempre necesita un rango."""
    filtros = dict(filtros)
    if not filtros.get('desde') or not filtros.get('hasta'):
        detectados = _detectar_fechas(texto)
        if detectados.get('desde') and detectados.get('hasta'):
            filtros['desde'] = detectados['desde']
            filtros['hasta'] = detectados['hasta']
            if detectados.get('periodo'):
                filtros['periodo'] = detectados['periodo']
    if not filtros.get('desde') or not filtros.get('hasta'):
        filtros['periodo'] = filtros.get('periodo') or 'mes'
        filtros['desde'], filtros['hasta'] = _rango_mes(_hoy().year, _hoy().month)
    return filtros


def _enriquecer_resultado(data: dict[str, Any]) -> dict[str, Any]:
    caso = data.get('caso_uso', 'CU21')
    if caso not in CASOS_USO:
        caso = 'CU21'
    formato = str(data.get('formato', 'pantalla')).lower()
    if formato not in FORMATOS:
        formato = 'pantalla'
    accion = data.get('accion', 'consultar')
    if accion not in ('consultar', 'descargar'):
        accion = 'descargar' if formato != 'pantalla' else 'consultar'

    filtros = {**_filtros_vacios(), **(data.get('filtros') or {})}
    metodo = str(filtros.get('metodo_pago') or '').lower()
    if metodo in ('tarjeta', 'stripe', 'card'):
        metodo = 'stripe'
    elif metodo not in ('efectivo', 'stripe'):
        metodo = ''
    filtros['metodo_pago'] = metodo

    jornada = str(filtros.get('jornada') or '').strip()
    jornada_alias = {
        'mañana': 'Mañana',
        'manana': 'Mañana',
        'tarde': 'Tarde',
        'noche': 'Noche',
        'unica': 'unica',
        'única': 'unica',
        'jornada única': 'unica',
        'jornada unica': 'unica',
    }
    filtros['jornada'] = jornada_alias.get(jornada.lower(), jornada if jornada in ('Mañana', 'Tarde', 'Noche', 'unica') else '')

    columnas = filtros.get('columnas')
    if columnas and not isinstance(columnas, list):
        columnas = None
    filtros['columnas'] = columnas

    requiere_formato = bool(data.get('requiere_seleccion_formato', False))
    if accion == 'descargar' and formato == 'pantalla' and not requiere_formato:
        requiere_formato = True
    if accion == 'descargar' and formato in ('pdf', 'csv', 'excel'):
        requiere_formato = False

    if requiere_formato:
        respuesta = (
            data.get('respuesta_voz')
            or 'Entendido. ¿En qué formato quieres el reporte: PDF, CSV o Excel?'
        )
    else:
        respuesta = data.get('respuesta_voz') or _mensaje_por_defecto(caso, formato, accion)

    return {
        'caso_uso': caso,
        'formato': formato,
        'accion': accion,
        'requiere_seleccion_formato': requiere_formato,
        'filtros': filtros,
        'respuesta_voz': respuesta,
        'modulo_disponible': caso in MODULOS_DISPONIBLES,
        'motor': data.get('motor', 'gemini'),
    }


def _mensaje_por_defecto(caso_uso: str, formato: str, accion: str) -> str:
    verbo = 'Descargando' if accion == 'descargar' else 'Consultando'
    return f'{verbo} {caso_uso} en formato {formato.upper()}.'


def _llamar_gemini(texto: str, cu_actual: str | None) -> dict[str, Any] | None:
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    if not api_key.strip():
        return None

    modelo = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
    hoy = _hoy().isoformat()
    contexto = f'Fecha de referencia (Bolivia): {hoy}.'
    if cu_actual:
        contexto += f' Pantalla actual del usuario: {cu_actual}.'

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent'
        f'?key={api_key}'
    )
    payload = {
        'contents': [
            {
                'role': 'user',
                'parts': [{'text': f'{_PROMPT_SISTEMA}\n\n{contexto}\n\nComando: {texto}'}],
            }
        ],
        'generationConfig': {
            'temperature': 0.2,
            'responseMimeType': 'application/json',
        },
    }

    try:
        respuesta = requests.post(url, json=payload, timeout=15)
        respuesta.raise_for_status()
        cuerpo = respuesta.json()
        texto_json = (
            cuerpo.get('candidates', [{}])[0]
            .get('content', {})
            .get('parts', [{}])[0]
            .get('text', '')
        )
        if not texto_json:
            return None
        data = json.loads(texto_json)
        data['motor'] = 'gemini'
        return _enriquecer_resultado(data)
    except (requests.RequestException, json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None


def _detectar_caso_uso(texto: str, cu_actual: str | None) -> str:
    t = texto.lower()
    if any(p in t for p in ('rol', 'roles', 'permiso', 'usuario', 'usuarios', 'matriz de permiso')):
        return 'CU21'
    reglas = (
        ('CU25', ('resultado', 'económico', 'economico', 'utilidad', 'margen', 'ganancia', 'balance')),
        ('CU24', ('compra', 'gasto', 'inversión', 'inversion', 'proveedor', 'egreso')),
        ('CU23', ('existencia', 'inventario', 'stock', 'insumo', 'materia prima')),
        ('CU22', ('producción', 'produccion', 'horneado', 'jornada', 'merma')),
        ('CU21', ('venta', 'ingreso', 'factur', 'comprobante', 'ticket', 'recaud')),
    )
    for cu, palabras in reglas:
        if any(p in t for p in palabras):
            return cu
    if cu_actual in CASOS_USO:
        return cu_actual
    return 'CU21'


def _detectar_formato_explicito(texto: str) -> str | None:
    t = texto.lower()
    if 'pdf' in t:
        return 'pdf'
    if 'csv' in t:
        return 'csv'
    if 'excel' in t or 'xlsx' in t or 'hoja de cálculo' in t or 'hoja de calculo' in t:
        return 'excel'
    return None


def _detectar_intencion_descarga(texto: str) -> bool:
    t = texto.lower()
    return any(
        v in t
        for v in (
            'descarga',
            'descargar',
            'exporta',
            'exportar',
            'genera',
            'generar',
            'archivo',
            'bájalo',
            'bajalo',
            'sácalo',
            'sacalo',
        )
    )


def _detectar_intencion_consulta(texto: str) -> bool:
    t = texto.lower()
    return any(v in t for v in ('muestra', 'muéstrame', 'muestrame', 'mostrar', 'consulta', 'ver el', 'ver '))


def _detectar_jornada(texto: str) -> str:
    t = texto.lower()
    if 'mañana' in t or 'manana' in t:
        return 'Mañana'
    if 'noche' in t:
        return 'Noche'
    if 'tarde' in t:
        return 'Tarde'
    if 'jornada única' in t or 'jornada unica' in t:
        return 'unica'
    return ''


def _detectar_metodo(texto: str) -> str:
    t = texto.lower()
    if 'efectivo' in t or 'caja' in t:
        return 'efectivo'
    if any(v in t for v in ('tarjeta', 'stripe', 'qr')):
        return 'stripe'
    return ''


def _detectar_rango_anual(texto: str) -> tuple[str, str] | None:
    """Si el usuario dice «año 2025» (o 20250), devuelve el 1 ene – 31 dic de ese año."""
    t = texto.lower()
    if not any(v in t for v in ('año', 'anio', 'ano')):
        return None
    match = re.search(r'(\d{4,})', t)
    if not match:
        return None
    anio = int(match.group(1))
    return f'{anio}-01-01', f'{anio}-12-31'


def _aplicar_rango_anual_si_corresponde(texto: str, resultado: dict[str, Any]) -> dict[str, Any]:
    rango = _detectar_rango_anual(texto)
    if not rango:
        return resultado
    filtros = dict(resultado.get('filtros') or {})
    filtros['desde'], filtros['hasta'] = rango
    filtros['periodo'] = None
    resultado['filtros'] = filtros
    return resultado


def _detectar_fechas(texto: str) -> dict[str, Any]:
    hoy = _hoy()
    t = texto.lower()
    desde, hasta = None, None
    periodo = None

    rango_anual = _detectar_rango_anual(texto)
    if rango_anual:
        desde, hasta = rango_anual

    if rango_anual:
        pass
    elif 'hoy' in t:
        periodo = 'dia'
        desde = hasta = hoy.isoformat()
    elif 'ayer' in t:
        periodo = 'dia'
        ayer = hoy - timedelta(days=1)
        desde = hasta = ayer.isoformat()
    elif 'semana' in t:
        periodo = 'semana'
        desde, hasta = _rango_semana(hoy)
    elif 'mes' in t or 'mensual' in t:
        periodo = 'mes'
        desde, hasta = _rango_mes(hoy.year, hoy.month)

    meses = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
    }
    for nombre, numero in meses.items():
        if nombre in t:
            anio = hoy.year
            match = re.search(r'(\d{4})', t)
            if match:
                anio = int(match.group(1))
            periodo = 'mes'
            desde, hasta = _rango_mes(anio, numero)
            break

    return {'periodo': periodo, 'desde': desde, 'hasta': hasta}


def _interpretar_local(texto: str, cu_actual: str | None) -> dict[str, Any]:
    caso = _detectar_caso_uso(texto, cu_actual)
    formato_explicito = _detectar_formato_explicito(texto)
    quiere_descarga = _detectar_intencion_descarga(texto)
    quiere_consulta = _detectar_intencion_consulta(texto)

    if formato_explicito:
        formato = formato_explicito
        accion = 'descargar'
        requiere_formato = False
    elif quiere_descarga and not quiere_consulta:
        formato = 'pantalla'
        accion = 'descargar'
        requiere_formato = True
    else:
        formato = 'pantalla'
        accion = 'consultar'
        requiere_formato = False

    filtros = _filtros_vacios()
    filtros.update(_detectar_fechas(texto))
    filtros['metodo_pago'] = _detectar_metodo(texto)
    if caso == 'CU22':
        filtros['jornada'] = _detectar_jornada(texto)

    if not filtros['desde']:
        filtros['periodo'] = 'mes'
        filtros['desde'], filtros['hasta'] = _rango_mes(_hoy().year, _hoy().month)

    data = {
        'caso_uso': caso,
        'formato': formato,
        'accion': accion,
        'requiere_seleccion_formato': requiere_formato,
        'filtros': filtros,
        'respuesta_voz': (
            'Entendido. ¿En qué formato quieres el reporte: PDF, CSV o Excel?'
            if requiere_formato
            else _mensaje_por_defecto(caso, formato, accion)
        ),
        'motor': 'local',
    }
    return _enriquecer_resultado(data)


def interpretar_comando_voz(texto: str, cu_actual: str | None = None) -> dict[str, Any]:
    """Punto de entrada: intenta Gemini y cae a reglas locales."""
    limpio = (texto or '').strip()
    if not limpio:
        raise ValueError('El comando de voz no puede estar vacío.')

    cu = cu_actual if cu_actual in CASOS_USO else None
    gemini = _llamar_gemini(limpio, cu)
    if gemini:
        resultado = _aplicar_rango_anual_si_corresponde(limpio, gemini)
    else:
        resultado = _interpretar_local(limpio, cu)
    resultado['filtros'] = _completar_fechas_filtros(resultado.get('filtros') or {}, limpio)
    return resultado