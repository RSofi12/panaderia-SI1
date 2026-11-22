"""Filas CSV del asistente (misma lógica que PDF, UTF-8 para Excel)."""
from __future__ import annotations

import csv
from typing import Any


def escribir_tablas_csv(writer: csv.writer, contexto: dict[str, Any]) -> None:
    tipo = contexto.get('tipo', '')
    if tipo == 'roles':
        _roles(writer, contexto)
    elif tipo == 'ventas':
        _ventas(writer, contexto)
    elif tipo == 'produccion':
        _produccion(writer, contexto)
    elif tipo == 'existencias':
        _existencias(writer, contexto)
    elif tipo == 'compras':
        _compras(writer, contexto)


def _bloque(writer: csv.writer, titulo: str, columnas: list[str], filas: list[list], vacio: str) -> None:
    writer.writerow([])
    writer.writerow([titulo])
    writer.writerow(columnas)
    if filas:
        for fila in filas:
            writer.writerow(fila)
    else:
        writer.writerow([vacio])


def _roles(writer: csv.writer, contexto: dict[str, Any]) -> None:
    filas = []
    for r in contexto.get('roles') or []:
        usuarios = ', '.join(r.get('usuarios_activos') or []) or '—'
        filas.append([
            r.get('rol', '—'),
            r.get('cantidad_usuarios', 0),
            usuarios,
            (r.get('descripcion') or '')[:300],
        ])
    _bloque(
        writer,
        'Roles y usuarios activos',
        ['Rol', 'Cantidad', 'Usuarios activos', 'Descripción'],
        filas,
        'Sin roles en el sistema.',
    )


def _produccion(writer: csv.writer, contexto: dict[str, Any]) -> None:
    filas = [
        [
            p.get('nombre', '—'),
            p.get('unidades', p.get('cantidad', 0)),
            p.get('vendidas', p.get('jornadas', 0)),
            p.get('diferencia', 0),
        ]
        for p in contexto.get('productos') or []
    ]
    _bloque(
        writer,
        'Producción vs ventas por producto',
        ['Producto', 'Producidas', 'Vendidas', 'Diferencia'],
        filas,
        'Sin producción en el período.',
    )


def _existencias(writer: csv.writer, contexto: dict[str, Any]) -> None:
    filas = [[p.get('nombre', '—'), p.get('stock', 0)] for p in contexto.get('productos') or []]
    _bloque(
        writer,
        'Existencias actuales',
        ['Producto', 'Stock'],
        filas,
        contexto.get('nota') or 'Sin datos de inventario.',
    )


def _compras(writer: csv.writer, contexto: dict[str, Any]) -> None:
    filas = [
        [m.get('tipo', '—'), m.get('categoria', '—'), m.get('cantidad', 0), m.get('total_bs', 0)]
        for m in contexto.get('movimientos_resumen') or []
    ]
    _bloque(
        writer,
        'Compras y gastos',
        ['Tipo', 'Categoría', 'Movimientos', 'Total (Bs)'],
        filas,
        'Sin movimientos en el período.',
    )


def _ventas(writer: csv.writer, contexto: dict[str, Any]) -> None:
    prod = [
        [p.get('nombre', '—'), p.get('cantidad', 0), p.get('subtotal', 0)]
        for p in (contexto.get('productos') or [])[:40]
    ]
    _bloque(writer, 'Productos vendidos', ['Producto', 'Cantidad', 'Subtotal (Bs)'], prod, 'Sin productos en el período.')

    ventas = []
    for v in (contexto.get('ventas') or [])[:200]:
        metodo = v.get('metodo_pago', '')
        if metodo == 'efectivo':
            metodo_txt = 'Efectivo'
        elif metodo == 'stripe':
            metodo_txt = 'Tarjeta'
        else:
            metodo_txt = metodo or '—'
        ventas.append([
            v.get('numero_comprobante', ''),
            v.get('fecha_hora', v.get('fecha', '')),
            metodo_txt,
            v.get('cajero', '—'),
            v.get('total', 0),
        ])
    _bloque(
        writer,
        'Detalle de ventas',
        ['Nº comprobante', 'Fecha y hora', 'Método', 'Cajero', 'Total (Bs)'],
        ventas,
        'Sin ventas en el período.',
    )