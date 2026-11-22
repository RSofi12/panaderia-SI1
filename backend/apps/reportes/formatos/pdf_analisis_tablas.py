"""Tablas del PDF del asistente (datos reales, sin Markdown de Gemini)."""
from __future__ import annotations

from typing import Any

from apps.comercializacion.ventas.models import MetodoPago
from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de


def _metodo_etiqueta(valor: str) -> str:
    if valor == MetodoPago.EFECTIVO:
        return 'Efectivo'
    if valor == MetodoPago.STRIPE:
        return 'Tarjeta'
    return str(valor or '—')


def _fila_tabla(
    hoja: HojaReporte,
    celdas: list[tuple[str, str]],
    proporciones: list[int],
    *,
    encabezado: bool = False,
    cebra: bool = False,
    al_continuar=None,
) -> None:
    anchos = anchos_de(*proporciones)
    hoja.fila(celdas, anchos, encabezado=encabezado, cebra=cebra, al_continuar=al_continuar)


def agregar_tablas_por_contexto(hoja: HojaReporte, contexto: dict[str, Any]) -> None:
    tipo = contexto.get('tipo', '')
    if tipo == 'roles':
        _tabla_roles(hoja, contexto)
    elif tipo == 'ventas':
        _tabla_ventas(hoja, contexto)
    elif tipo == 'produccion':
        _tabla_produccion(hoja, contexto)
    elif tipo == 'existencias':
        _tabla_existencias(hoja, contexto)
    elif tipo == 'compras':
        _tabla_compras(hoja, contexto)
    else:
        hoja.nota('Sin tabla estructurada para este tema; revise el resumen narrativo.')


def _tabla_roles(hoja: HojaReporte, contexto: dict[str, Any]) -> None:
    filas = contexto.get('roles') or []
    hoja.seccion('Detalle de roles y usuarios activos')
    proporciones = [18, 8, 30, 44]

    def encabezado():
        _fila_tabla(
            hoja,
            [
                ('Rol', 'izq'),
                ('Cant.', 'der'),
                ('Usuarios activos', 'izq'),
                ('Descripción', 'izq'),
            ],
            proporciones,
            encabezado=True,
        )

    encabezado()
    if not filas:
        hoja.nota('No hay roles registrados.')
        return
    for indice, fila in enumerate(filas):
        usuarios = ', '.join(fila.get('usuarios_activos') or []) or '—'
        desc = (fila.get('descripcion') or '—')[:120]
        _fila_tabla(
            hoja,
            [
                (fila.get('rol', '—'), 'izq'),
                (str(fila.get('cantidad_usuarios', 0)), 'der'),
                (usuarios, 'izq'),
                (desc, 'izq'),
            ],
            proporciones,
            cebra=indice % 2 == 1,
            al_continuar=encabezado,
        )


def _tabla_produccion(hoja: HojaReporte, contexto: dict[str, Any]) -> None:
    hoja.seccion('Producción vs ventas por producto')
    proporciones = [40, 20, 20, 20]

    def encabezado():
        _fila_tabla(
            hoja,
            [
                ('Producto', 'izq'),
                ('Producidas', 'der'),
                ('Vendidas', 'der'),
                ('Diferencia', 'der'),
            ],
            proporciones,
            encabezado=True,
        )

    encabezado()
    productos = contexto.get('productos') or []
    if not productos:
        hoja.nota('No hay producción en el período.')
        return
    for indice, p in enumerate(productos):
        producidas = p.get('unidades', p.get('cantidad', 0))
        vendidas = p.get('vendidas', p.get('jornadas', 0))
        diferencia = p.get('diferencia', producidas - vendidas)
        _fila_tabla(
            hoja,
            [
                (p.get('nombre', '—'), 'izq'),
                (str(producidas), 'der'),
                (str(vendidas), 'der'),
                (str(diferencia), 'der'),
            ],
            proporciones,
            cebra=indice % 2 == 1,
            al_continuar=encabezado,
        )


def _tabla_existencias(hoja: HojaReporte, contexto: dict[str, Any]) -> None:
    hoja.seccion('Existencias actuales (productos terminados)')
    proporciones = [70, 30]

    def encabezado():
        _fila_tabla(
            hoja,
            [('Producto', 'izq'), ('Stock', 'der')],
            proporciones,
            encabezado=True,
        )

    encabezado()
    productos = contexto.get('productos') or []
    if not productos:
        hoja.nota(contexto.get('nota') or 'Sin datos de inventario.')
        return
    for indice, p in enumerate(productos):
        _fila_tabla(
            hoja,
            [(p.get('nombre', '—'), 'izq'), (p.get('stock', '0'), 'der')],
            proporciones,
            cebra=indice % 2 == 1,
            al_continuar=encabezado,
        )


def _tabla_compras(hoja: HojaReporte, contexto: dict[str, Any]) -> None:
    hoja.seccion('Resumen de compras y gastos')
    proporciones = [18, 32, 15, 35]

    def encabezado():
        _fila_tabla(
            hoja,
            [('Tipo', 'izq'), ('Categoría', 'izq'), ('Movimientos', 'der'), ('Total (Bs)', 'der')],
            proporciones,
            encabezado=True,
        )

    encabezado()
    movs = contexto.get('movimientos_resumen') or []
    if not movs:
        hoja.nota('No hay movimientos económicos en el período.')
        return
    for indice, m in enumerate(movs):
        _fila_tabla(
            hoja,
            [
                (m.get('tipo', '—'), 'izq'),
                (m.get('categoria', '—'), 'izq'),
                (str(m.get('cantidad', 0)), 'der'),
                (m.get('total_bs', '0'), 'der'),
            ],
            proporciones,
            cebra=indice % 2 == 1,
            al_continuar=encabezado,
        )


def _tabla_ventas(hoja: HojaReporte, contexto: dict[str, Any]) -> None:
    productos = contexto.get('productos') or []
    ventas = contexto.get('ventas') or []

    if productos:
        hoja.seccion('Productos más vendidos')
        proporciones = [55, 20, 25]

        def enc_prod():
            _fila_tabla(
                hoja,
                [('Producto', 'izq'), ('Cantidad', 'der'), ('Subtotal (Bs)', 'der')],
                proporciones,
                encabezado=True,
            )

        enc_prod()
        for indice, p in enumerate(productos[:25]):
            _fila_tabla(
                hoja,
                [
                    (p.get('nombre', '—'), 'izq'),
                    (str(p.get('cantidad', 0)), 'der'),
                    (f"{p.get('subtotal', 0)}", 'der'),
                ],
                proporciones,
                cebra=indice % 2 == 1,
                al_continuar=enc_prod,
            )

    hoja.seccion('Detalle de ventas del período')
    cols = [22, 28, 18, 20, 12]
    claves = ('comprobante', 'fecha', 'metodo', 'cajero', 'total')

    def enc_ventas():
        _fila_tabla(
            hoja,
            [
                ('Nº Comp.', 'izq'),
                ('Fecha y hora', 'izq'),
                ('Método', 'izq'),
                ('Cajero', 'izq'),
                ('Total (Bs)', 'der'),
            ],
            cols,
            encabezado=True,
        )

    enc_ventas()
    if not ventas:
        hoja.nota('Este período no tiene transacciones registradas.')
        return
    for indice, v in enumerate(ventas[:80]):
        _fila_tabla(
            hoja,
            [
                (f"#{v.get('numero_comprobante', '—')}", 'izq'),
                (v.get('fecha_hora', v.get('fecha', '—')), 'izq'),
                (_metodo_etiqueta(v.get('metodo_pago')), 'izq'),
                (v.get('cajero', '—'), 'izq'),
                (f"{v.get('total', 0)}", 'der'),
            ],
            cols,
            cebra=indice % 2 == 1,
            al_continuar=enc_ventas,
        )
    if len(ventas) > 80:
        hoja.nota(f'Se muestran 80 de {len(ventas)} ventas. Exporte CSV desde reportes de ventas para el listado completo.')