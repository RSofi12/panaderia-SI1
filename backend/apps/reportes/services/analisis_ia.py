"""
Análisis narrativo con IA sobre datos reales del sistema (no solo CU21–CU25 estructurados).

Usa Gemini cuando hay API key; si no, genera un resumen local a partir del contexto recolectado.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum

from apps.productos_inventario.produccion.models import DetalleProduccion, Produccion
from apps.reportes.services.interprete_voz import interpretar_comando_voz
from apps.reportes.services.reporte_ventas import reporte_ventas
from apps.usuarios_seguridad.roles.models import Rol

Usuario = get_user_model()

TEMAS = (
    'ventas',
    'produccion',
    'existencias',
    'compras',
    'economico',
    'roles',
    'productos',
    'general',
)


def _detectar_tema(texto: str, caso_uso: str) -> str:
    t = texto.lower()
    if any(
        p in t
        for p in (
            'rol',
            'roles',
            'permiso',
            'permisos',
            'usuario',
            'usuarios',
            'acceso',
            'matriz',
            'cajero',
            'personal',
        )
    ):
        return 'roles'
    if any(p in t for p in ('producción', 'produccion', 'horneado', 'jornada', 'merma')):
        return 'produccion'
    if any(p in t for p in ('existencia', 'inventario', 'stock', 'insumo', 'materia prima')):
        return 'existencias'
    if any(p in t for p in ('compra', 'gasto', 'proveedor', 'inversión', 'inversion')):
        return 'compras'
    if any(p in t for p in ('resultado', 'utilidad', 'margen', 'ganancia', 'balance', 'económico', 'economico')):
        return 'economico'
    if any(p in t for p in ('producto', 'pan', 'catálogo', 'catalogo', 'mas vendido', 'más vendido')):
        return 'productos'
    if any(p in t for p in ('venta', 'ingreso', 'factur', 'comprobante', 'ticket', 'recaud')):
        return 'ventas'
    mapa = {
        'CU21': 'ventas',
        'CU22': 'produccion',
        'CU23': 'existencias',
        'CU24': 'compras',
        'CU25': 'economico',
    }
    return mapa.get(caso_uso, 'general')


def _contexto_roles() -> dict[str, Any]:
    """Solo columnas existentes en BD (evita fallos si falta migración tipo_rol)."""
    filas = []
    try:
        roles = Rol.objects.values('id_rol', 'nombre', 'descripcion').order_by('nombre')
        for rol in roles:
            usuarios = Usuario.objects.filter(id_rol_id=rol['id_rol'], activo=True).values_list(
                'nombre_completo', flat=True
            )
            filas.append(
                {
                    'rol': rol['nombre'],
                    'descripcion': (rol.get('descripcion') or '')[:200],
                    'usuarios_activos': list(usuarios),
                    'cantidad_usuarios': len(usuarios),
                }
            )
    except Exception:
        return {
            'tipo': 'roles',
            'roles': [],
            'nota': 'No se pudieron cargar roles/usuarios; ejecuta migrate en el backend.',
        }
    return {'tipo': 'roles', 'roles': filas}


def _contexto_produccion(desde: date, hasta: date) -> dict[str, Any]:
    jornadas = Produccion.objects.filter(fecha__range=(desde, hasta)).count()
    detalles = (
        DetalleProduccion.objects.filter(id_produccion__fecha__range=(desde, hasta))
        .values('id_producto__nombre')
        .annotate(cantidad=Sum('cantidad'), jornadas=Count('id_produccion', distinct=True))
        .order_by('-cantidad')[:15]
    )
    return {
        'tipo': 'produccion',
        'jornadas': jornadas,
        'productos': [
            {'nombre': d['id_producto__nombre'], 'unidades': d['cantidad'], 'jornadas': d['jornadas']}
            for d in detalles
        ],
    }


def _contexto_ventas(desde: date, hasta: date, metodo: str | None) -> dict[str, Any]:
    datos = reporte_ventas(desde=desde, hasta=hasta, metodo_pago=metodo or None)
    return {'tipo': 'ventas', **datos}


def _recolectar_contexto(tema: str, desde: date, hasta: date, metodo: str) -> dict[str, Any]:
    if tema == 'roles':
        ctx = _contexto_roles()
        ctx['periodo'] = {'desde': desde.isoformat(), 'hasta': hasta.isoformat()}
        return ctx
    if tema == 'produccion':
        return _contexto_produccion(desde, hasta)
    if tema in ('ventas', 'productos', 'economico', 'general'):
        return _contexto_ventas(desde, hasta, metodo)
    if tema == 'existencias':
        try:
            from apps.productos_inventario.productos_terminados.models import InventarioProductoTerminado

            items = (
                InventarioProductoTerminado.objects.select_related('id_producto')
                .filter(id_producto__activo=True)
                .values('id_producto__nombre', 'stock_actual')[:30]
            )
            return {
                'tipo': 'existencias',
                'productos': [{'nombre': i['id_producto__nombre'], 'stock': str(i['stock_actual'])} for i in items],
                'periodo': {'desde': desde.isoformat(), 'hasta': hasta.isoformat()},
            }
        except Exception:
            return {'tipo': 'existencias', 'productos': [], 'nota': 'Sin datos de inventario cargados.'}
    if tema == 'compras':
        try:
            from apps.compras.gastos.models import MovimientoEconomico

            movs = (
                MovimientoEconomico.objects.filter(
                    fecha_hora__date__range=(desde, hasta),
                    anulado=False,
                )
                .values('tipo', 'categoria')
                .annotate(total=Sum('monto'), cantidad=Count('pk'))
            )
            return {
                'tipo': 'compras',
                'movimientos_resumen': [
                    {
                        'tipo': m['tipo'],
                        'categoria': m['categoria'],
                        'total_bs': str(m['total'] or 0),
                        'cantidad': m['cantidad'],
                    }
                    for m in movs
                ],
            }
        except Exception:
            return {'tipo': 'compras', 'movimientos_resumen': []}
    return _contexto_ventas(desde, hasta, metodo)


def recolectar_contexto_analisis(
    tema: str,
    desde: date,
    hasta: date,
    metodo: str = '',
) -> dict[str, Any]:
    """Contexto estructurado para PDF/exports del asistente (misma fuente que la IA)."""
    return _recolectar_contexto(tema, desde, hasta, metodo)


def _analisis_local(consulta: str, tema: str, contexto: dict[str, Any], desde: str, hasta: str) -> str:
    if tema == 'roles' and contexto.get('roles'):
        lineas = [
            f'Roles y usuarios activos en el sistema (consulta: «{consulta}»).',
            f'Período de referencia para ventas relacionadas: {desde} → {hasta}.',
            '',
        ]
        for fila in contexto['roles']:
            nombres = ', '.join(fila['usuarios_activos']) or 'sin usuarios activos'
            lineas.append(
                f"• {fila['rol']}: {fila['cantidad_usuarios']} usuario(s) — {nombres}."
            )
        return '\n'.join(lineas)

    if contexto.get('tipo') == 'ventas':
        if contexto.get('cantidad', 0) == 0:
            return (
                f'No hay ventas registradas entre {desde} y {hasta} para «{consulta}». '
                'Prueba otro período (por ejemplo octubre 2026 si ejecutaste seed_mes_operativo).'
            )
        tops = contexto.get('productos', [])[:5]
        resumen_prod = ', '.join(f"{p['nombre']} ({p['cantidad']})" for p in tops) if tops else '—'
        return (
            f"Ventas del {desde} al {hasta}: {contexto['cantidad']} comprobantes, "
            f"total Bs {contexto['total']} (efectivo Bs {contexto['efectivo']}, tarjeta Bs {contexto['tarjeta']}). "
            f"Productos destacados: {resumen_prod}."
        )

    return (
        f'Consulta «{consulta}» ({tema}) para {desde} → {hasta}. '
        'Configura GEMINI_API_KEY para un análisis más detallado con IA.'
    )


def _llamar_gemini_analisis(consulta: str, tema: str, contexto: dict[str, Any], desde: str, hasta: str) -> str | None:
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    if not api_key.strip():
        return None

    modelo = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent'
        f'?key={api_key}'
    )
    payload = {
        'contents': [
            {
                'role': 'user',
                'parts': [
                    {
                        'text': (
                            'Eres el analista de inteligencia de negocio de la Panadería Santiago (Santa Cruz, Bolivia). '
                            'Responde en español claro, en texto plano (sin Markdown: no uses *, **, # ni listas con asteriscos). '
                            'Usa párrafos cortos; los datos tabulares van en tablas del sistema, no los repitas como lista. '
                            'Basa el análisis SOLO en los datos JSON proporcionados; no inventes cifras. '
                            'Si los datos están vacíos, dilo y sugiere revisar el período o ejecutar seed_all.\n\n'
                            f'Consulta del usuario: {consulta}\n'
                            f'Tema inferido: {tema}\n'
                            f'Período: {desde} a {hasta}\n\n'
                            f'Datos:\n{json.dumps(contexto, ensure_ascii=False, default=str)[:14000]}'
                        )
                    }
                ],
            }
        ],
        'generationConfig': {'temperature': 0.35},
    }
    try:
        respuesta = requests.post(url, json=payload, timeout=25)
        respuesta.raise_for_status()
        cuerpo = respuesta.json()
        texto = (
            cuerpo.get('candidates', [{}])[0]
            .get('content', {})
            .get('parts', [{}])[0]
            .get('text', '')
        )
        return texto.strip() or None
    except (requests.RequestException, KeyError, IndexError, TypeError):
        return None


def analizar_consulta_reporte(texto: str, cu_actual: str | None = None) -> dict[str, Any]:
    """Interpreta fechas/filtros y devuelve análisis narrativo + metadatos para exportación."""
    comando = interpretar_comando_voz(texto, cu_actual=cu_actual)
    filtros = comando.get('filtros') or {}
    desde_s = filtros.get('desde')
    hasta_s = filtros.get('hasta')
    if not desde_s or not hasta_s:
        raise ValueError('No se pudo inferir un rango de fechas para el análisis.')

    desde = date.fromisoformat(str(desde_s))
    hasta = date.fromisoformat(str(hasta_s))
    metodo = str(filtros.get('metodo_pago') or '')
    tema = _detectar_tema(texto, comando.get('caso_uso', 'CU21'))

    contexto = _recolectar_contexto(tema, desde, hasta, metodo)
    motor = 'gemini'
    analisis = _llamar_gemini_analisis(texto, tema, contexto, desde.isoformat(), hasta.isoformat())
    if not analisis:
        motor = 'local'
        analisis = _analisis_local(texto, tema, contexto, desde.isoformat(), hasta.isoformat())

    exportar_ventas = (
        tema in ('ventas', 'productos', 'economico', 'general')
        and contexto.get('tipo') == 'ventas'
        and int(contexto.get('cantidad', 0)) > 0
    )

    return {
        'consulta': texto.strip(),
        'tema': tema,
        'caso_uso': comando['caso_uso'],
        'desde': desde.isoformat(),
        'hasta': hasta.isoformat(),
        'analisis': analisis,
        'motor': motor,
        'comando': comando,
        'exportar_ventas': exportar_ventas,
        'respuesta_voz': analisis.split('\n')[0][:280],
    }