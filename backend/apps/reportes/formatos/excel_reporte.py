"""
Módulo de generación de hojas de cálculo Excel (.xlsx) nativas para reportes.
Panadería Santiago (SI-1).

Utiliza openpyxl para crear libros de cálculo con diseño profesional,
tipografía legible, paleta institucional artesanal (ámbar/dorado),
bloque de resumen (KPIs), tablas estructuradas con filtros y anchos de columna automáticos.
"""
import io
from decimal import Decimal
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


# ==============================================================================
# ESTILOS Y PALETA INSTITUCIONAL
# ==============================================================================

COLOR_PRIMARIO = '78350F'      # Ámbar oscuro / panadería
COLOR_ENCABEZADO = '9A3412'    # Ámbar tostado
COLOR_SECCION = 'FDE68A'       # Ámbar claro para subsecciones
COLOR_KPI_FONDO = 'FEF3C7'     # Ámbar suave
COLOR_ZEBRA = 'F8FAFC'         # Gris tenue alternado
COLOR_BORDE = 'CBD5E1'         # Gris claro

FONT_TITULO = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
FONT_SUBTITULO = Font(name='Calibri', size=11, italic=True, color='FDE68A')
FONT_SECCION = Font(name='Calibri', size=12, bold=True, color='78350F')
FONT_TH = Font(name='Calibri', size=10, bold=True, color='FFFFFF')
FONT_BODY = Font(name='Calibri', size=10, color='1E293B')
FONT_BODY_BOLD = Font(name='Calibri', size=10, bold=True, color='1E293B')
FONT_KPI_VALOR = Font(name='Calibri', size=13, bold=True, color='9A3412')
FONT_KPI_LABEL = Font(name='Calibri', size=9, bold=True, color='64748B')

FILL_BANNER = PatternFill(start_color=COLOR_PRIMARIO, end_color=COLOR_PRIMARIO, fill_type='solid')
FILL_TH = PatternFill(start_color=COLOR_ENCABEZADO, end_color=COLOR_ENCABEZADO, fill_type='solid')
FILL_SECCION = PatternFill(start_color=COLOR_SECCION, end_color=COLOR_SECCION, fill_type='solid')
FILL_KPI = PatternFill(start_color=COLOR_KPI_FONDO, end_color=COLOR_KPI_FONDO, fill_type='solid')
FILL_ZEBRA = PatternFill(start_color=COLOR_ZEBRA, end_color=COLOR_ZEBRA, fill_type='solid')

BORDE_FINO = Border(
    left=Side(style='thin', color=COLOR_BORDE),
    right=Side(style='thin', color=COLOR_BORDE),
    top=Side(style='thin', color=COLOR_BORDE),
    bottom=Side(style='thin', color=COLOR_BORDE),
)

ALIGN_LEFT = Alignment(horizontal='left', vertical='center')
ALIGN_CENTER = Alignment(horizontal='center', vertical='center')
ALIGN_RIGHT = Alignment(horizontal='right', vertical='center')


def _ajustar_anchos(ws, min_col=1, max_col=10, min_width=12, max_width=45):
    """Calcula el ancho óptimo de cada columna basándose en el contenido."""
    for col in range(min_col, max_col + 1):
        col_letter = get_column_letter(col)
        max_len = 0
        for cell in ws[col_letter]:
            if cell.row <= 2:  # Omitir banner principal
                continue
            val_str = str(cell.value or '')
            if '\n' in val_str:
                val_str = max(val_str.split('\n'), key=len)
            max_len = max(max_len, len(val_str))
        ancho = min(max(max_len + 3, min_width), max_width)
        ws.column_dimensions[col_letter].width = ancho


def _crear_banner(ws, titulo: str, subtitulo: str, max_cols: int = 6):
    """Crea el encabezado institucional con branding en las primeras filas."""
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_cols)
    cell_t = ws.cell(row=1, column=1, value=f'PANADERÍA SANTIAGO — {titulo.upper()}')
    cell_t.font = FONT_TITULO
    cell_t.fill = FILL_BANNER
    cell_t.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 36

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max_cols)
    cell_s = ws.cell(row=2, column=1, value=subtitulo)
    cell_s.font = FONT_SUBTITULO
    cell_s.fill = FILL_BANNER
    cell_s.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 20

    # Borde inferior del banner
    for col in range(1, max_cols + 1):
        ws.cell(row=1, column=col).fill = FILL_BANNER
        ws.cell(row=2, column=col).fill = FILL_BANNER


def _agregar_kpis(ws, kpis: list[tuple[str, str]], start_row: int, max_cols: int = 6) -> int:
    """Inserta bloque visual de tarjetas resumen tipo KPI."""
    ws.cell(row=start_row, column=1, value='RESUMEN EJECUTIVO DEL PERÍODO').font = FONT_SECCION
    start_row += 1

    col = 1
    row = start_row
    for label, valor in kpis:
        c_label = ws.cell(row=row, column=col, value=label.upper())
        c_label.font = FONT_KPI_LABEL
        c_label.fill = FILL_KPI
        c_label.alignment = ALIGN_CENTER
        c_label.border = BORDE_FINO

        c_val = ws.cell(row=row + 1, column=col, value=valor)
        c_val.font = FONT_KPI_VALOR
        c_val.fill = FILL_KPI
        c_val.alignment = ALIGN_CENTER
        c_val.border = BORDE_FINO

        col += 1
        if col > max_cols:
            col = 1
            row += 2

    return (row + 2) if col == 1 else (row + 3)


def _agregar_tabla(
    ws,
    titulo_seccion: str,
    columnas: list[str],
    filas: list[list],
    start_row: int,
    alineaciones: list[str] | None = None,
) -> int:
    """Inserta una tabla con encabezado estilizado y filas zebra alternadas."""
    ws.cell(row=start_row, column=1, value=titulo_seccion).font = FONT_SECCION
    start_row += 1

    # Encabezados de columna
    for idx, col_nom in enumerate(columnas, start=1):
        c = ws.cell(row=start_row, column=idx, value=col_nom)
        c.font = FONT_TH
        c.fill = FILL_TH
        c.alignment = ALIGN_CENTER
        c.border = BORDE_FINO
    ws.row_dimensions[start_row].height = 24
    start_row += 1

    if not filas:
        ws.cell(row=start_row, column=1, value='Sin registros disponibles para los criterios seleccionados.').font = FONT_BODY
        ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=len(columnas))
        return start_row + 2

    for r_idx, fila in enumerate(filas):
        fill_actual = FILL_ZEBRA if r_idx % 2 == 1 else None
        for c_idx, val in enumerate(fila, start=1):
            c = ws.cell(row=start_row, column=c_idx, value=val)
            c.font = FONT_BODY
            c.border = BORDE_FINO
            if fill_actual:
                c.fill = fill_actual

            # Alineación según columna
            if alineaciones and c_idx - 1 < len(alineaciones):
                align_code = alineaciones[c_idx - 1]
                c.alignment = ALIGN_RIGHT if align_code == 'R' else (ALIGN_CENTER if align_code == 'C' else ALIGN_LEFT)
            else:
                c.alignment = ALIGN_RIGHT if isinstance(val, (int, float, Decimal)) else ALIGN_LEFT
        ws.row_dimensions[start_row].height = 20
        start_row += 1

    return start_row + 1


# ==============================================================================
# EXPORTADORES POR CASO DE USO (CU21 a CU25 + Voz)
# ==============================================================================

def excel_reporte_ventas(reporte: dict, metodo_pago=None, columnas: list[str] | None = None) -> bytes:
    """Genera archivo XLSX para CU21 (Reporte de ventas)."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Ventas'
    ws.views.sheetView[0].showGridLines = True

    sub = f'Período: {reporte["desde"]} al {reporte["hasta"]} | Método: {metodo_pago or "Todos"}'
    _crear_banner(ws, 'Reporte de Ventas', sub, max_cols=5)

    kpis = [
        ('Tickets Emitidos', str(reporte['cantidad'])),
        ('Total Facturado', f'Bs {Decimal(reporte["total"]):,.2f}'),
        ('Efectivo', f'Bs {Decimal(reporte["efectivo"]):,.2f}'),
        ('Tarjeta / QR', f'Bs {Decimal(reporte["tarjeta"]):,.2f}'),
    ]
    next_row = _agregar_kpis(ws, kpis, start_row=4, max_cols=4)

    # Detalle de ventas
    cols_map = [
        ('comprobante', 'Nº Comprobante', lambda v: f"#{v['numero_comprobante']}", 'C'),
        ('fecha', 'Fecha y Hora', lambda v: v.get('fecha_hora', ''), 'C'),
        ('metodo', 'Método de Pago', lambda v: v.get('metodo_pago_nombre', v.get('metodo_pago', '')), 'C'),
        ('cajero', 'Cajero / Responsable', lambda v: v.get('cajero', 'Sistema'), 'L'),
        ('total', 'Total (Bs)', lambda v: float(Decimal(v['total'])), 'R'),
    ]
    cols_activas = [c for c in cols_map if c[0] in columnas] if columnas else cols_map
    if not cols_activas:
        cols_activas = cols_map

    titulos_th = [c[1] for c in cols_activas]
    alins = [c[3] for c in cols_activas]
    filas_ventas = [[c[2](v) for c in cols_activas] for v in reporte.get('ventas', [])]

    next_row = _agregar_tabla(ws, 'DETALLE DE TICKETS DE VENTA', titulos_th, filas_ventas, next_row, alins)

    # Resumen de productos vendidos
    prods = reporte.get('productos', [])
    filas_prods = [[p['nombre'], p['cantidad'], float(Decimal(p['subtotal']))] for p in prods]
    _agregar_tabla(
        ws,
        'PRODUCTOS VENDIDOS EN EL PERÍODO',
        ['Producto', 'Unidades Vendidas', 'Subtotal (Bs)'],
        filas_prods,
        next_row,
        ['L', 'R', 'R'],
    )

    _ajustar_anchos(ws, min_col=1, max_col=5)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def excel_reporte_produccion(reporte: dict, jornada=None, columnas: list[str] | None = None) -> bytes:
    """Genera archivo XLSX para CU22 (Reporte de producción)."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Producción'
    ws.views.sheetView[0].showGridLines = True

    sub = f'Período: {reporte["desde"]} al {reporte["hasta"]} | Jornada: {jornada or "Todas las jornadas"}'
    _crear_banner(ws, 'Reporte de Producción y Balance', sub, max_cols=6)

    kpis = [
        ('Jornadas de Horno', str(reporte['cantidad'])),
        ('Horneadas (U)', str(reporte['unidades'])),
        ('Vendidas (U)', str(reporte['unidades_vendidas'])),
        ('Mermas CU18 (U)', str(reporte.get('unidades_mermadas', 0))),
        ('Diferencia Neta', str(reporte['diferencia'])),
        ('Costo Insumos', f'Bs {Decimal(reporte["costo"]):,.2f}'),
    ]
    next_row = _agregar_kpis(ws, kpis, start_row=4, max_cols=6)

    # Detalle de jornadas / lotes
    cols_map = [
        ('lote', 'Nº Lote', lambda l: f"#{l['id_produccion']}", 'C'),
        ('fecha', 'Fecha', lambda l: str(l.get('fecha', '')), 'C'),
        ('jornada', 'Jornada', lambda l: str(l.get('jornada', '')), 'C'),
        ('responsable', 'Responsable', lambda l: str(l.get('responsable', 'Sistema')), 'L'),
        ('unidades', 'Unidades', lambda l: l.get('unidades', 0), 'R'),
        ('costo', 'Costo (Bs)', lambda l: float(Decimal(l['costo'])), 'R'),
    ]
    cols_activas = [c for c in cols_map if c[0] in columnas] if columnas else cols_map
    if not cols_activas:
        cols_activas = cols_map

    titulos_th = [c[1] for c in cols_activas]
    alins = [c[3] for c in cols_activas]
    filas_lotes = [[c[2](l) for c in cols_activas] for l in reporte.get('lotes', [])]

    next_row = _agregar_tabla(ws, 'JORNADAS DE PRODUCCIÓN REGISTRADAS', titulos_th, filas_lotes, next_row, alins)

    # Balance por producto
    prods = reporte.get('productos', [])
    filas_prods = [
        [
            p['nombre'],
            p.get('cantidad', 0),
            p.get('vendidas', 0),
            p.get('mermadas', 0),
            p.get('diferencia', 0),
            float(Decimal(p.get('costo', 0))),
        ]
        for p in prods
    ]
    next_row = _agregar_tabla(
        ws,
        'BALANCE DETALLADO POR PRODUCTO (PRODUCIDO vs VENDIDO vs MERMADO)',
        ['Producto', 'Horneado', 'Vendido', 'Mermado (CU18)', 'Diferencia', 'Costo (Bs)'],
        filas_prods,
        next_row,
        ['L', 'R', 'R', 'R', 'R', 'R'],
    )

    # Detalle de mermas si existen
    mermas = reporte.get('mermas', [])
    if mermas:
        filas_mermas = [
            [
                m.get('fecha', ''),
                m.get('producto', ''),
                m.get('cantidad', 0),
                float(Decimal(m.get('costo_unitario', 0))),
                float(Decimal(m.get('costo_total', 0))),
                m.get('motivo', ''),
            ]
            for m in mermas
        ]
        _agregar_tabla(
            ws,
            'DETALLE DE NOTAS DE PÉRDIDA Y MERMAS (CU18)',
            ['Fecha y Hora', 'Producto', 'Cantidad', 'Costo Unit. (Bs)', 'Costo Total (Bs)', 'Motivo'],
            filas_mermas,
            next_row,
            ['C', 'L', 'R', 'R', 'R', 'L'],
        )

    _ajustar_anchos(ws, min_col=1, max_col=6)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def excel_reporte_existencias(reporte: dict, columnas: list[str] | None = None, **filtros) -> bytes:
    """Genera archivo XLSX para CU23 (Reporte de existencias de vitrina e insumos)."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Existencias'
    ws.views.sheetView[0].showGridLines = True

    sub = f'Tipo: {filtros.get("tipo") or "Todos"} | Estado: {filtros.get("estado") or "Todos"}'
    _crear_banner(ws, 'Reporte de Existencias en Mostrador', sub, max_cols=6)

    res = reporte.get('resumen', {})
    kpis = [
        ('Total Ítems', str(res.get('total', 0))),
        ('Stock Bajo (Alerta)', str(res.get('bajo_stock', res.get('bajo', 0)))),
        ('Sin Registro', str(res.get('sin_inventario', res.get('agotado', 0)))),
        ('Terminados', str(res.get('productos_terminados', 0))),
        ('Materias Primas', str(res.get('materias_primas', 0))),
    ]
    next_row = _agregar_kpis(ws, kpis, start_row=4, max_cols=5)

    filas_raw = reporte.get('resultados') or reporte.get('items') or []

    cols_map = [
        ('producto', 'Producto / Insumo', lambda it: it.get('nombre') or it.get('producto_nombre', ''), 'L'),
        ('tipo', 'Tipo', lambda it: ('Materia prima' if it.get('tipo') == 'materia_prima' else 'Producto terminado'), 'C'),
        ('stock', 'Stock Actual', lambda it: float(Decimal(it['stock_actual'])) if it.get('stock_actual') is not None else '—', 'R'),
        ('minimo', 'Stock Mínimo', lambda it: float(Decimal(it['stock_minimo'])) if it.get('stock_minimo') is not None else '—', 'R'),
        ('nivel', 'Nivel de Alerta', lambda it: it.get('estado', '').replace('_', ' ').capitalize(), 'C'),
        ('unidad', 'Unidad', lambda it: str(it.get('unidad_medida', '')), 'C'),
        ('estado', 'Estado', lambda it: ('Activo' if it.get('activo') else 'Inactivo') if 'activo' in it else it.get('estado', ''), 'C'),
    ]

    cols_activas = [c for c in cols_map if c[0] in columnas] if columnas else cols_map
    if not cols_activas:
        cols_activas = cols_map

    titulos_th = [c[1] for c in cols_activas]
    alins = [c[3] for c in cols_activas]
    filas = [[c[2](it) for c in cols_activas] for it in filas_raw]

    _agregar_tabla(
        ws,
        'INVENTARIO ACTUAL DE MATERIAS PRIMAS Y PRODUCTOS TERMINADOS',
        titulos_th,
        filas,
        next_row,
        alins,
    )

    _ajustar_anchos(ws, min_col=1, max_col=max(len(titulos_th), 5))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def excel_reporte_compras(reporte: dict, nombre_prov: str | None = None) -> bytes:
    """Genera archivo XLSX para CU24 (Reporte de compras y gastos)."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Compras'
    ws.views.sheetView[0].showGridLines = True

    sub = f'Período: {reporte["desde"]} al {reporte["hasta"]} | Proveedor: {nombre_prov or "Todos los proveedores"}'
    _crear_banner(ws, 'Reporte de Compras e Insumos', sub, max_cols=4)

    kpis = [
        ('Compras Realizadas', str(reporte['cantidad'])),
        ('Total Invertido', f'Bs {Decimal(reporte["total"]):,.2f}'),
        ('Proveedores Activos', str(len(reporte.get('proveedores', [])))),
        ('Insumos Adquiridos', str(len(reporte.get('materias_primas', [])))),
    ]
    next_row = _agregar_kpis(ws, kpis, start_row=4, max_cols=4)

    # Detalle por materia prima
    mps = reporte.get('materias_primas', [])
    filas_mp = [
        [mp['nombre'], f"{mp['cantidad']} {mp.get('unidad_medida', '')}", float(Decimal(mp['subtotal']))]
        for mp in mps
    ]
    next_row = _agregar_tabla(
        ws,
        'DETALLE DE MATERIA PRIMA ADQUIRIDA',
        ['Materia Prima', 'Cantidad Adquirida', 'Subtotal Invertido (Bs)'],
        filas_mp,
        next_row,
        ['L', 'R', 'R'],
    )

    # Detalle por proveedor
    provs = reporte.get('proveedores', [])
    filas_prov = [
        [
            p.get('nombre', '—'),
            p.get('cantidad_compras', p.get('compras', 0)),
            float(Decimal(str(p.get('total', 0)))),
        ]
        for p in provs
    ]
    _agregar_tabla(
        ws,
        'DESGLOSE POR PROVEEDOR',
        ['Proveedor', 'Nº Compras', 'Total Facturado (Bs)'],
        filas_prov,
        next_row,
        ['L', 'C', 'R'],
    )

    _ajustar_anchos(ws, min_col=1, max_col=4)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def excel_resultados_economicos(reporte: dict) -> bytes:
    """Genera archivo XLSX para CU25 (Resultados económicos / balance contable)."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Resultados Económicos'
    ws.views.sheetView[0].showGridLines = True

    sub = f'Período: {reporte["desde"]} al {reporte["hasta"]} | Estado de Resultados Integral'
    _crear_banner(ws, 'Reporte de Resultados Económicos', sub, max_cols=4)

    kpis = [
        ('Ingresos Totales', f'Bs {Decimal(reporte.get("ingresos", {}).get("total", 0)):,.2f}'),
        ('Costos Producción', f'Bs {Decimal(reporte.get("costos_produccion", {}).get("total", 0)):,.2f}'),
        ('Gastos Operativos', f'Bs {Decimal(reporte.get("gastos_operativos", {}).get("total", 0)):,.2f}'),
        ('Resultado Neto', f'Bs {Decimal(reporte.get("resultado_neto", 0)):,.2f}'),
    ]
    next_row = _agregar_kpis(ws, kpis, start_row=4, max_cols=4)

    # Detalle de líneas contables
    filas_balance = [
        ['(+) Ventas en Mostrador (Efectivo)', float(Decimal(reporte.get('ingresos', {}).get('ventas_mostrador_efectivo', 0)))],
        ['(+) Ventas en Mostrador (Tarjeta / QR)', float(Decimal(reporte.get('ingresos', {}).get('ventas_mostrador_tarjeta', 0)))],
        ['(+) Pedidos Anticipados Entregados', float(Decimal(reporte.get('ingresos', {}).get('pedidos_entregados', 0)))],
        ['TOTAL INGRESOS BRUTOS', float(Decimal(reporte.get('ingresos', {}).get('total', 0)))],
        ['(-) Costo de Insumos / Materias Primas', float(Decimal(reporte.get('costos_produccion', {}).get('costo_materia_prima', 0)))],
        ['(-) Mermas de Producción y Mostrador', float(Decimal(reporte.get('costos_produccion', {}).get('costo_mermas', 0)))],
        ['UTILIDAD BRUTA', float(Decimal(reporte.get('utilidad_bruta', 0)))],
        ['(-) Gastos Operativos Generales', float(Decimal(reporte.get('gastos_operativos', {}).get('total', 0)))],
        ['(=) RESULTADO NETO DEL EJERCICIO', float(Decimal(reporte.get('resultado_neto', 0)))],
    ]
    _agregar_tabla(
        ws,
        'ESTADO DE RESULTADOS DETALLADO',
        ['Concepto Contable', 'Monto (Bs)'],
        filas_balance,
        next_row,
        ['L', 'R'],
    )

    _ajustar_anchos(ws, min_col=1, max_col=3)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def excel_reporte_analisis(consulta: str, tema: str, desde: str, hasta: str, analisis: str, motor: str = 'local') -> bytes:
    """Genera archivo XLSX para CU27 (Reporte por voz / Gemini)."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Análisis por Voz'
    ws.views.sheetView[0].showGridLines = True

    sub = f'Período: {desde} al {hasta} | Motor: {motor.upper()} | Tema: {tema}'
    _crear_banner(ws, 'Análisis de Reporte por Voz', sub, max_cols=3)

    ws.cell(row=4, column=1, value='CONSULTA DEL USUARIO:').font = FONT_SECCION
    ws.cell(row=5, column=1, value=consulta).font = FONT_BODY_BOLD

    ws.cell(row=7, column=1, value='CONCLUSIONES Y ANÁLISIS DE DATOS:').font = FONT_SECCION
    ws.cell(row=8, column=1, value=analisis).font = FONT_BODY

    _ajustar_anchos(ws, min_col=1, max_col=3, min_width=20, max_width=80)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
