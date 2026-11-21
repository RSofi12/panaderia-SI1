"""
Exportación de archivos del CU25 (Reporte de resultados económicos).

Genera CSV (con delimitador ';' y decimales ',' compatible con Excel)
y documento PDF formal con membrete institucional de la Panadería Santiago.
"""
import csv
import io
from decimal import Decimal

from django.utils import timezone

from apps.reportes.formatos.csv_reporte import dinero_local
from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible


def _dinero_bs(valor) -> str:
    return f'Bs {Decimal(valor):.2f}'


def csv_resultados_economicos(reporte: dict) -> bytes:
    """Genera archivo CSV estructurado del balance económico para abrir en Excel."""
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    resumen = reporte.get('resumen_financiero', {})
    ingresos = reporte.get('ingresos', {})
    costos = reporte.get('costos', {})
    gastos = reporte.get('gastos_operativos', {})
    inversiones = reporte.get('inversiones', {})
    estado_resultados = reporte.get('estado_resultados', [])

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')

    # Encabezado institucional
    writer.writerow(['Panadería Santiago'])
    writer.writerow(['Reporte de Resultados Económicos y Balance Operativo (CU25)'])
    writer.writerow(['Desde', fecha_visible(reporte['desde'])])
    writer.writerow(['Hasta', fecha_visible(reporte['hasta'])])
    writer.writerow(['Generado el', generado])
    writer.writerow([])

    # Resumen Ejecutivo
    writer.writerow(['Resumen Ejecutivo'])
    writer.writerow(['Indicador Financiero', 'Monto (Bs)', '% s/ Ingresos'])
    writer.writerow(['Ingresos Totales por Ventas', dinero_local(resumen.get('total_ingresos', 0)), '100,00%'])
    writer.writerow(['Costos Directos (Compras + Mermas)', dinero_local(costos.get('total_costos_directos', 0)), ''])
    writer.writerow(['Margen / Utilidad Bruta', dinero_local(resumen.get('utilidad_bruta', 0)), f"{resumen.get('margen_bruto_pct', 0)}%"])
    writer.writerow(['Gastos Operativos', dinero_local(gastos.get('total', 0)), ''])
    writer.writerow(['Utilidad Operativa (EBITDA)', dinero_local(resumen.get('utilidad_operativa', 0)), f"{resumen.get('margen_operativo_pct', 0)}%"])
    writer.writerow(['Inversiones de Capital', dinero_local(inversiones.get('total', 0)), ''])
    writer.writerow(['Resultado Económico Neto', dinero_local(resumen.get('utilidad_neta', 0)), f"{resumen.get('margen_neto_pct', 0)}%"])
    writer.writerow([])

    # Estado de Resultados Detallado
    writer.writerow(['Estado de Resultados'])
    writer.writerow(['Concepto', 'Monto (Bs)', '% de Incidencia'])
    for fila in estado_resultados:
        writer.writerow([
            fila['concepto'],
            dinero_local(fila['monto']),
            f"{fila['porcentaje_ingresos']}%",
        ])
    writer.writerow([])

    # Desglose de Gastos Operativos por Categoría
    writer.writerow(['Desglose de Gastos Operativos por Categoría'])
    writer.writerow(['Categoría', 'Cantidad', 'Total (Bs)'])
    desglose_g = gastos.get('desglose', [])
    if desglose_g:
        for g in desglose_g:
            writer.writerow([g['categoria'].capitalize(), g['cantidad'], dinero_local(g['total'])])
    else:
        writer.writerow(['Sin gastos registrados en el período', '0', '0,00'])
    writer.writerow([])

    # Desglose de Inversiones por Categoría
    writer.writerow(['Desglose de Inversiones de Capital'])
    writer.writerow(['Categoría', 'Cantidad', 'Total (Bs)'])
    desglose_i = inversiones.get('desglose', [])
    if desglose_i:
        for i_item in desglose_i:
            writer.writerow([i_item['categoria'].capitalize(), i_item['cantidad'], dinero_local(i_item['total'])])
    else:
        writer.writerow(['Sin inversiones registradas en el período', '0', '0,00'])
    writer.writerow([])

    writer.writerow(['Este documento consolida las operaciones financieras registradas en la Panadería Santiago.'])
    return buffer.getvalue().encode('utf-8-sig')


def pdf_resultados_economicos(reporte: dict) -> bytes:
    """Genera documento PDF formal del balance de resultados económicos."""
    cuando = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    detalle = (
        f'Período: del {fecha_visible(reporte["desde"])} al {fecha_visible(reporte["hasta"])}\n'
        f'Generado: {cuando}   ·   Moneda: Bolivianos (Bs)\n'
        f'Módulo de Reportes Financieros — Caso de Uso CU25'
    )

    pdf = HojaReporte('Reporte de Resultados Económicos')
    pdf.abrir('RESULTADOS ECONÓMICOS', detalle)

    resumen = reporte.get('resumen_financiero', {})
    utilidad_neta = Decimal(resumen.get('utilidad_neta', 0))
    margen_neto = Decimal(resumen.get('margen_neto_pct', 0))

    # 1. Tarjetas Superiores de Indicadores Clave
    pdf.tarjetas([
        ('Ingresos', _dinero_bs(resumen.get('total_ingresos', 0))),
        ('Costos Insumos', _dinero_bs(reporte.get('costos', {}).get('compras_materia_prima', 0))),
        ('Gastos Operat.', _dinero_bs(reporte.get('gastos_operativos', {}).get('total', 0))),
        ('Resultado Neto', _dinero_bs(utilidad_neta)),
    ])

    # 2. Sección: Estado de Resultados Formal
    pdf.seccion('Estado de Resultados del Período')
    cols_er = anchos_de(5, 2, 2)

    def cabecera_er():
        pdf.fila(
            [('Concepto Contable / Operativo', 'izq'), ('Monto (Bs)', 'der'), ('% s/ Ingresos', 'der')],
            cols_er,
            encabezado=True,
        )

    cabecera_er()
    estado = reporte.get('estado_resultados', [])
    for idx, f in enumerate(estado):
        es_subtotal = f.get('tipo') in ('subtotal', 'total_neto')
        signo = '+' if f.get('tipo') == 'ingreso' else ''
        monto_fmt = f"{signo}{_dinero_bs(f['monto'])}" if not es_subtotal else _dinero_bs(f['monto'])
        pct_fmt = f"{Decimal(f.get('porcentaje_ingresos', 0)):.1f}%"
        pdf.fila(
            [(f['concepto'], 'izq'), (monto_fmt, 'der'), (pct_fmt, 'der')],
            cols_er,
            cebra=(idx % 2 == 1 and not es_subtotal),
            al_continuar=cabecera_er,
        )

    # 3. Sección: Desglose de Gastos Operativos e Inversiones
    pdf.y -= 10
    pdf.seccion('Desglose de Gastos Operativos e Inversiones (CU20)')
    cols_desglose = anchos_de(3, 2, 2, 2)

    def cabecera_desglose():
        pdf.fila(
            [('Tipo / Rubro', 'izq'), ('Categoría', 'izq'), ('Registros', 'der'), ('Total (Bs)', 'der')],
            cols_desglose,
            encabezado=True,
        )

    cabecera_desglose()
    desglose_filas = []
    for g in reporte.get('gastos_operativos', {}).get('desglose', []):
        desglose_filas.append(('Gasto operativo', g['categoria'].capitalize(), str(g['cantidad']), _dinero_bs(g['total'])))
    for i_item in reporte.get('inversiones', {}).get('desglose', []):
        desglose_filas.append(('Inversión capital', i_item['categoria'].capitalize(), str(i_item['cantidad']), _dinero_bs(i_item['total'])))

    if desglose_filas:
        for idx, fila in enumerate(desglose_filas):
            pdf.fila(
                [(fila[0], 'izq'), (fila[1], 'izq'), (fila[2], 'der'), (fila[3], 'der')],
                cols_desglose,
                cebra=(idx % 2 == 1),
                al_continuar=cabecera_desglose,
            )
    else:
        pdf.fila(
            [('Sin egresos operativos registrados en el período', 'izq'), ('-', 'izq'), ('0', 'der'), ('Bs 0.00', 'der')],
            cols_desglose,
            al_continuar=cabecera_desglose,
        )

    pdf.nota('Nota: Las cifras corresponden a las transacciones registradas y validadas en el sistema sin incluir movimientos anulados.')
    return pdf.cerrar()
